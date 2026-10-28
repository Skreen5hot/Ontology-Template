# SPDX-License-Identifier: MIT
"""Check the built site before it is published.

    python tools/site/check_site.py            # checks _site/
    python tools/site/check_site.py DIR

Runs on the artifact, not the source, because the artifact is what gets
deployed: a page that is right in site/pages/ and wrong after the build
is wrong on the public site. Standard library only.

What it refuses, and why each one:

  * a page with no <title>, no lang, no <main id="main">, or other than
    exactly one <h1> -- the structure a screen reader navigates by;
  * a resource (script, stylesheet, image) loaded from another origin --
    the site makes no external request, so it renders the same offline,
    behind a proxy, and in ten years;
  * any inline script or on* event attribute -- ontology text reaches the
    page as text, and the one way that rule could be broken quietly is a
    script nobody meant to ship;
  * an internal link or resource that does not resolve to a file in the
    artifact, or a #fragment with no matching id on its target page --
    the site is served from a subpath, and a root-absolute URL that works
    in preview 404s in production;
  * a link to an insecure http: or a javascript: URL;
  * a build stamp still reading "unknown";
  * on a site built for a private repository, any link into it -- the
    reader the site is for cannot follow one;
  * a download whose bytes do not match the manifest's SHA-256, a bundle
    whose SHA256SUMS disagrees with its own members, or a term index whose
    counts disagree with its records.

Carried in spirit from BFO-Aligned ValueNet's check_site.py; rewritten
for this site's pages and data.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())

RESOURCE_ATTRS = {("script", "src"), ("link", "href"), ("img", "src"),
                  ("source", "src"), ("iframe", "src")}


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.lang = None
        self.title = 0
        self.h1 = 0
        self.main = False
        self.ids = set()
        self.links = []        # (tag, attr, value)
        self.inline_scripts = 0
        self.handlers = []
        self.stamp = None
        self._in_stamp = False
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        if tag == "title":
            self.title += 1
        if tag == "h1":
            self.h1 += 1
        if tag == "main" and attrs.get("id") == "main":
            self.main = True
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for name in attrs:
            if name.lower().startswith("on"):
                self.handlers.append((tag, name))
        for attr in ("href", "src"):
            if attrs.get(attr) is not None:
                self.links.append((tag, attr, attrs[attr]))
        if tag == "script":
            self._in_script = True
            if not attrs.get("src"):
                self.inline_scripts += 1
        if tag == "code" and attrs.get("data-build") == "commit":
            self._in_stamp = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False
        if tag == "code":
            self._in_stamp = False

    def handle_data(self, data):
        if self._in_stamp:
            self.stamp = (self.stamp or "") + data


def parse(path: Path) -> Page:
    page = Page()
    page.feed(path.read_text(encoding="utf-8"))
    return page


def resolve(site: Path, page: Path, url: str) -> Path:
    target = (page.parent / unquote(url)).resolve()
    if target.is_dir() or url.endswith("/") or url in ("", "./"):
        target = target / "index.html"
    return target


def check(site: Path) -> list[str]:
    problems = []
    pages = sorted(site.rglob("*.html"), key=lambda p: p.as_posix())
    if not pages:
        return ["no page was built, so nothing below was checked"]
    parsed = {p.resolve(): parse(p) for p in pages}

    for path, page in parsed.items():
        name = path.relative_to(site.resolve()).as_posix()
        if page.lang != "en":
            problems.append("%s: <html lang> is %r" % (name, page.lang))
        if page.title != 1:
            problems.append("%s: %d <title> elements" % (name, page.title))
        if page.h1 != 1:
            problems.append("%s: %d <h1> elements; a page has exactly one"
                            % (name, page.h1))
        if not page.main:
            problems.append("%s: no <main id=\"main\">" % name)
        if page.inline_scripts:
            problems.append("%s: %d inline script(s)"
                            % (name, page.inline_scripts))
        if page.handlers:
            problems.append("%s: event handler attributes %s"
                            % (name, page.handlers[:3]))
        if not page.stamp or page.stamp.strip() == "unknown":
            problems.append("%s: build stamp is %r" % (name, page.stamp))

        for tag, attr, url in page.links:
            parts = urlsplit(url)
            scheme = parts.scheme.lower()
            if scheme in ("javascript", "data", "http"):
                problems.append("%s: <%s %s=%r> uses %s:"
                                % (name, tag, attr, url, scheme))
                continue
            if (tag, attr) in RESOURCE_ATTRS and (scheme or parts.netloc):
                problems.append("%s: <%s> loads %s from another origin"
                                % (name, tag, url))
                continue
            if scheme or parts.netloc:
                continue                    # an outbound https link
            if url.startswith("/"):
                problems.append(
                    "%s: %r is root-absolute; the site is served from a "
                    "subpath, so this works in preview and 404s on Pages"
                    % (name, url))
                continue
            target = path if not parts.path else resolve(site, path,
                                                         parts.path)
            if not target.is_file():
                problems.append("%s: %r resolves to nothing in the artifact"
                                % (name, url))
                continue
            if parts.fragment:
                if target.suffix != ".html":
                    continue
                ids = parsed.get(target.resolve(), Page()).ids
                if unquote(parts.fragment) not in ids:
                    problems.append("%s: %r names a fragment its target "
                                    "does not have" % (name, url))

    problems.extend(check_data(site))
    return problems


def check_data(site: Path) -> list[str]:
    problems = []
    try:
        manifest = json.loads((site / "data/downloads.json")
                              .read_text(encoding="utf-8"))
        terms = json.loads((site / "data/terms.json")
                           .read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ["the site data could not be read: %s" % exc]

    def digest(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    rows = ([(site / "downloads" / r["file"], r["sha256"])
             for r in manifest["authored"]]
            + [(site / "downloads/upstream" / r["file"], r["sha256"])
               for r in manifest["upstream"]]
            + [(site / "downloads" / manifest["bundle"]["filename"],
                manifest["bundle"]["sha256"])])
    # The specification is optional: a project without one has none.
    if manifest.get("specification"):
        rows.append((site / "downloads" / manifest["specification"]["file"],
                     manifest["specification"]["sha256"]))
    for path, want in rows:
        if not path.is_file():
            problems.append("download %s is missing" % path.name)
        elif digest(path) != want:
            problems.append("download %s does not match its manifest "
                            "checksum" % path.name)

    bundle = site / "downloads" / manifest["bundle"]["filename"]
    if bundle.is_file():
        with zipfile.ZipFile(io.BytesIO(bundle.read_bytes())) as archive:
            names = sorted(archive.namelist())
            if names != manifest["bundle"]["members"]:
                problems.append("the bundle's members are not the "
                                "manifest's")
            sums_name = manifest["bundle"]["root"] + "SHA256SUMS"
            listed = {}
            for line in archive.read(sums_name).decode("utf-8").splitlines():
                value, member = line.split(None, 1)
                listed[member.strip()] = value
            for member, value in sorted(listed.items()):
                data = archive.read(manifest["bundle"]["root"] + member)
                if hashlib.sha256(data).hexdigest() != value:
                    problems.append("bundle SHA256SUMS is wrong for %s"
                                    % member)
            covered = {manifest["bundle"]["root"] + m for m in listed}
            missing = sorted(set(names) - covered - {sums_name})
            if missing:
                problems.append("bundle SHA256SUMS omits %s" % missing)

    # A site built for a private repository links nowhere into it: every
    # such link is a 404 for the public reader the site is for.
    if manifest.get("repository_linked") is False and manifest.get(
            "repository"):
        private = manifest["repository"].rstrip("/")
        for page in sorted(site.rglob("*.html")):
            text = page.read_text(encoding="utf-8")
            if 'href="%s/' % private in text or \
                    'href="%s"' % private in text:
                problems.append("%s links into the private repository %s"
                                % (page.relative_to(site).as_posix(),
                                   manifest["repository"]))

    records = terms.get("classes") or []
    if not records:
        problems.append("the term index is empty")
    counted = {"authored": 0, "upstream": 0}
    for record in records:
        counted[record["origin"]] = counted.get(record["origin"], 0) + 1
    if counted != terms["counts"]:
        problems.append("the term index counts %s and holds %s"
                        % (terms["counts"], counted))
    problems.extend(check_nothing_concealed(site, records))
    return problems


def check_nothing_concealed(site: Path, records: list) -> list[str]:
    """A term whose text differs within a language is published with
    every variant and a note, never as one of them; and every noted term
    is on the status page, so the explorer is not the only place it is
    said (BPO evaluation, T7)."""
    problems = []
    status = (site / "status/index.html").read_text(encoding="utf-8") \
        if (site / "status/index.html").is_file() else ""
    for record in records:
        for field, what in (("label", "rdfs:label"),
                            ("definition", "skos:definition")):
            variants = [v for v in record["variants"][field] if v["literal"]]
            shown_lang = "en" if [v for v in variants
                                  if v["lang"] == "en"] else ""
            for lang in sorted({v["lang"] for v in variants}):
                same = [v["value"] for v in variants if v["lang"] == lang]
                if len(same) < 2:
                    continue
                if not [n for n in record["notes"] if n["kind"] == "conflict"
                        and n["about"] == what and n["lang"] == lang]:
                    problems.append("%s has %d %s values in one language "
                                    "and no note says so"
                                    % (record["id"], len(same), what))
                shown = record[field]
                if lang == shown_lang and not all(v in shown for v in same):
                    problems.append("%s is published with one of its %d "
                                    "%s values, not all of them"
                                    % (record["id"], len(same), what))
        if record["notes"] and html.escape(record["id"]) not in status:
            problems.append("%s is published with findings the status "
                            "page does not list" % record["id"])
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?", default="_site")
    args = ap.parse_args(argv)
    site = Path(args.site)
    site = site if site.is_absolute() else _root / site
    problems = check(site)
    pages = len(list(site.rglob("*.html")))
    if problems:
        for problem in problems:
            print("  FINDING: %s" % problem)
        print("  %d finding(s) across %d page(s)" % (len(problems), pages))
        return 1
    print("  %d page(s) checked: structure, origins, links, fragments, "
          "downloads, bundle, term index" % pages)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
