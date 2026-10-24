# SPDX-License-Identifier: MIT
"""Build the public site into _site/, deterministically.

    python tools/site/build_site.py              # into _site/
    python tools/site/build_site.py -o DIR       # somewhere else

The site is for people who will read the ontology, look terms up and
download the files without cloning anything. So it has to be easy to read
and it has to be right, and the second is the harder one: every name,
count, version, digest and licence on it is read from the repository at
build time -- config/project.yaml, the pins, the modules, the manifests --
never typed into a page. site/content/site.json holds only the words a
person has to choose.

Carried from the Business Capability Ontology's builder, which carried
the method from BFO-Aligned ValueNet, and generalized: nothing here names
a project. What carries over unchanged:

DETERMINISM

The site is deployed from an Actions artifact, not a committed tree, so
the only way to tell a deployment matches a commit is to rebuild it and
compare. Every input is enumerated in sorted order; the only timestamp is
the source commit's (or SOURCE_DATE_EPOCH), never now(); the output is
emptied and rewritten; downloads are copied as bytes, never re-serialised.
The Pages workflow builds twice and requires the two trees identical.

RELATIVE PATHS

A project site is served from a subpath (/<repository>/). A root-absolute
/assets/... works in local preview and 404s in production, so every
internal URL is relative, and tools/site/check_site.py resolves every one.

ONTOLOGY TEXT IS NEVER MARKUP

Every value read from a Turtle file, a pin, a question or a mapping set
reaches a page through html.escape here, or through textContent in the
explorer. Markdown documents are rendered with raw HTML shown, not run.

REFUSALS

An authored term with no label or definition, or two in one language,
stops the build: which one is published would otherwise be decided by
traversal order. So does a placeholder nothing fills, a page fragment no
navigation entry names, and an asset with a suffix no rule covers.

A PRIVATE REPOSITORY, A PUBLIC SITE

The ontology is published; how it was made need not be. A Pages site is
public even when its repository is private, and every link into a
private repository -- a source file, the commit, the issues, a release --
is a 404 for the reader the site is for. So the build is told the
repository's visibility (SITE_REPOSITORY_PRIVATE, which the Pages
workflow sets from the event) and, for a private one, writes no link
into it: paths and the commit are shown as text, releases as tags, and
findings go to the `contact` in site.json if there is one. Unset, the
build assumes private, so a local preview never shows links a reader
could not follow. tools/site/check_site.py refuses a link into the
repository on a site built that way.

WHAT IS OPTIONAL

The specification and review pages are built when a component with the
role `specification` or `review` exists, and left out of the navigation
when none does -- `when` on the navigation entry in site.json.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

_here = Path(__file__).resolve()
_root = next(p for p in (_here, *_here.parents)
             if (p / "config/repository-layout.yaml").is_file())
sys.path.insert(0, str(_root / "tools"))

import layout  # noqa: E402
import project  # noqa: E402

OUTPUT = "_site"
PAGES = "site/pages"
ASSETS = "site/src"
CONTENT = "site/content/site.json"
PINS = "config/upstream-sources.yaml"
EXTRACTS = "config/upstream-extracts.json"
BASELINE = "config/validation-baseline.json"

#: Assets copied verbatim. Anything else under site/src/ is refused rather
#: than shipped or skipped: an artifact that deploys whatever it finds
#: cannot say what it deployed.
ALLOWED_ASSET_SUFFIXES = {".css", ".js"}

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
DCTERMS = "http://purl.org/dc/terms/"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
OBO = "http://purl.obolibrary.org/obo/"
CCO = "https://www.commoncoreontologies.org/"

TERM_TYPES = {
    OWL + "Class": "class",
    OWL + "ObjectProperty": "property",
    OWL + "DatatypeProperty": "property",
    OWL + "AnnotationProperty": "property",
}

#: The category a class is shown under: the most specific of these BFO
#: (and one CCO) categories its subClassOf chain reaches. Read from the
#: hierarchy, never from a name. IRIs read from the vendored registers
#: when this was written. A class reaching two unrelated categories is
#: refused -- the realist shapes would already have said so.
CATEGORY_ROOTS = {
    OBO + "BFO_0000040": "material entity",
    OBO + "BFO_0000141": "immaterial entity",
    OBO + "BFO_0000019": "quality",
    OBO + "BFO_0000016": "disposition",
    OBO + "BFO_0000023": "role",
    OBO + "BFO_0000034": "function",
    OBO + "BFO_0000017": "realizable entity",
    OBO + "BFO_0000031": "generically dependent continuant",
    CCO + "ont00000958": "information content entity",
    OBO + "BFO_0000015": "process",
    OBO + "BFO_0000035": "process boundary",
    OBO + "BFO_0000008": "temporal region",
    OBO + "BFO_0000006": "spatial region",
    OBO + "BFO_0000011": "spatiotemporal region",
    OBO + "BFO_0000029": "site",
}

esc = html.escape


class Refused(SystemExit):
    """A question for whoever wrote the input, not for this build."""


# ------------------------------------------------------------- inputs


def git(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=str(_root),
                            capture_output=True)
    if result.returncode:
        raise Refused("git %s failed: %s" % (
            " ".join(args),
            result.stderr.decode("utf-8", "replace").strip()[-300:]))
    # Decoded explicitly: text=True would use cp1252 on Windows.
    return result.stdout.decode("utf-8").strip()


def stamp() -> tuple[str, int]:
    """The commit, and its own timestamp. Never now()."""
    commit = git("rev-parse", "HEAD")
    epoch = os.environ.get("SOURCE_DATE_EPOCH") or git(
        "log", "-1", "--format=%ct", commit)
    return commit, int(epoch)


def load_tool(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, _root / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(relative_path: str) -> dict:
    return json.loads((_root / relative_path).read_text(encoding="utf-8"))


def pins() -> list[dict]:
    import yaml

    raw = yaml.safe_load((_root / PINS).read_text(encoding="utf-8")) or {}
    return raw.get("sources") or []


def source_bytes(path: Path) -> bytes:
    """A file's bytes, refused if they carry CRLF.

    Every download is these bytes, so they have to be the bytes git
    publishes. .gitattributes pins LF in the index, but a checkout made
    with core.autocrlf=true writes CRLF into the working tree, and a build
    there would publish different files from CI's under the same commit.
    That happened to the BCO's first deployment, in 6 of 21 files.
    """
    data = path.read_bytes()
    if b"\r\n" in data:
        name = relative(path) if path.is_relative_to(_root) else str(path)
        raise Refused(
            "%s has CRLF line endings in the working tree, so this build "
            "would publish different bytes from CI's. Rewrite it from the "
            "index (with no uncommitted change to it): delete it, then "
            "git checkout -- %s" % (name, name))
    return data


def relative(path: Path) -> str:
    return path.resolve().relative_to(_root.resolve()).as_posix()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse(path: Path):
    """One Turtle file under a stable base -- never the filesystem path, or
    a relative IRI would describe the machine that built the site."""
    import rdflib

    graph = rdflib.Graph()
    graph.parse(data=path.read_text(encoding="utf-8"), format="turtle",
                publicID=project.iri_base() + "/base/" + path.name)
    return graph


# --------------------------------------------------------- term index


def literal(graph, subject, predicate: str, what: str, required: bool) -> str:
    """At most one value per language, preferring English then untagged."""
    import rdflib

    values = list(graph.objects(subject, rdflib.URIRef(predicate)))
    wrong = [v for v in values if not isinstance(v, rdflib.Literal)]
    if wrong:
        raise Refused("%s has a %s that is not a literal: %r"
                      % (subject, what, [str(w)[:60] for w in wrong]))
    for lang in ("en", None):
        chosen = sorted({str(v) for v in values if v.language == lang})
        if len(chosen) > 1:
            raise Refused(
                "%s has %d %s values tagged %s: %s. Which is published "
                "would depend on traversal order; this is a question for "
                "the ontology." % (subject, len(chosen), what,
                                   lang or "untagged",
                                   [c[:40] for c in chosen]))
        if chosen:
            return chosen[0]
    if required:
        raise Refused("%s has no %s. The site publishes what the ontology "
                      "asserts, with no fallback." % (subject, what))
    return ""


def prefixes() -> list[tuple[str, str]]:
    found = [(entry["prefix"], entry["namespace"]) for entry in pins()]
    found.append((project.prefix(), project.namespace()))
    return sorted(found, key=lambda pair: -len(pair[1]))


def short_id(iri: str, known: list[tuple[str, str]]) -> str:
    for prefix, namespace in known:
        if iri.startswith(namespace):
            return prefix + ":" + iri[len(namespace):]
    return iri


def category_of(iri: str, kind: str, merged) -> str:
    import rdflib

    if kind == "property":
        return "property"
    sub = rdflib.URIRef(RDFS + "subClassOf")
    ancestors = {str(a) for a in merged.transitive_objects(
        rdflib.URIRef(iri), sub)}
    reached = [root for root in CATEGORY_ROOTS if root in ancestors]
    specific = [root for root in reached
                if not any(other != root and root in {
                    str(a) for a in merged.transitive_objects(
                        rdflib.URIRef(other), sub)}
                    for other in reached)]
    if len(specific) > 1:
        raise Refused(
            "%s reaches unrelated categories %s. A class that is two kinds "
            "of thing is a question for the ontology."
            % (iri, [CATEGORY_ROOTS[r] for r in specific]))
    return CATEGORY_ROOTS[specific[0]] if specific else "other"


def term_records(sources: list[dict], merged,
                 known: list[tuple[str, str]]) -> list[dict]:
    """One record per term, authored and upstream. Authored terms must
    carry a label and a definition; an upstream stub may lack the latter."""
    import rdflib

    namespace = project.namespace()
    records, seen = [], {}
    for source in sources:
        graph = source["graph"]
        for type_iri, kind in sorted(TERM_TYPES.items()):
            for subject in graph.subjects(rdflib.URIRef(RDF_TYPE),
                                          rdflib.URIRef(type_iri)):
                if not isinstance(subject, rdflib.URIRef):
                    continue
                iri = str(subject)
                authored = source["origin"] == "authored"
                if authored and not iri.startswith(namespace):
                    continue
                if not authored and not list(graph.objects(
                        subject, rdflib.URIRef(RDFS + "label"))):
                    continue
                if iri in seen:
                    if seen[iri] == source["key"]:
                        continue
                    raise Refused("%s is declared by both %s and %s"
                                  % (iri, seen[iri], source["key"]))
                seen[iri] = source["key"]
                parent_predicate = (RDFS + "subClassOf" if kind == "class"
                                    else RDFS + "subPropertyOf")
                records.append({
                    "id": short_id(iri, known),
                    "iri": iri,
                    "label": literal(graph, subject, RDFS + "label",
                                     "rdfs:label", required=True),
                    "definition": literal(graph, subject,
                                          SKOS + "definition",
                                          "skos:definition",
                                          required=authored),
                    "kind": kind,
                    "category": category_of(iri, kind, merged),
                    "module": source["key"],
                    "origin": source["origin"],
                    "source": source["path"],
                    "parents": sorted(
                        str(o) for o in merged.objects(
                            subject, rdflib.URIRef(parent_predicate))
                        if isinstance(o, rdflib.URIRef)),
                    "synonyms": sorted(
                        str(o) for o in graph.objects(
                            subject, rdflib.URIRef(SKOS + "altLabel"))),
                })
    records.sort(key=lambda r: (r["label"].lower(), r["iri"]))
    return records


def ontology_header(graph, source: str) -> dict:
    import rdflib

    headers = sorted(str(s) for s in graph.subjects(
        rdflib.URIRef(RDF_TYPE), rdflib.URIRef(OWL + "Ontology")))
    if len(headers) != 1:
        raise Refused("%s has %d ontology headers: %s"
                      % (source, len(headers), headers))
    subject = rdflib.URIRef(headers[0])
    return {
        "iri": headers[0],
        "title": literal(graph, subject, DCTERMS + "title", "dcterms:title",
                         required=False),
        "version": literal(graph, subject, OWL + "versionInfo",
                           "owl:versionInfo", required=False),
        "comment": literal(graph, subject, RDFS + "comment", "rdfs:comment",
                           required=False),
    }


# ----------------------------------------------------------- markdown


def render_markdown(text: str) -> tuple[str, str]:
    """(body, table of contents), with raw HTML shown rather than run."""
    import markdown

    md = markdown.Markdown(
        extensions=["tables", "toc", "fenced_code", "sane_lists"],
        extension_configs={"toc": {"permalink": False, "baselevel": 2}})
    md.preprocessors.deregister("html_block")
    md.inlinePatterns.deregister("html")
    body = md.convert(text)
    body = body.replace("<table>", '<div class="scroll-x"><table>')
    body = body.replace("</table>", "</table></div>")
    return body, md.toc


# --------------------------------------------------------- downloads


def deterministic_zip(members: list[tuple[str, bytes]], epoch: int) -> bytes:
    """Same members, same bytes, on any machine."""
    import time

    stamp_tuple = time.gmtime(epoch - (epoch % 2))[:6]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in sorted(members):
            info = zipfile.ZipInfo(name, date_time=stamp_tuple)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    return buffer.getvalue()


# -------------------------------------------------------------- pages


def fill(fragment: str, values: dict, name: str) -> str:
    wanted = set(re.findall(r"\{\{([a-z_]+)\}\}", fragment))
    missing = sorted(wanted - set(values))
    if missing:
        raise Refused("page %s has placeholders nothing fills: %s"
                      % (name, missing))
    for key in sorted(wanted):
        fragment = fragment.replace("{{%s}}" % key, values[key])
    leftover = re.findall(r"\{\{[^}]*\}\}", fragment)
    if leftover:
        raise Refused("page %s has malformed placeholders: %s"
                      % (name, leftover))
    return fragment


def definition_list(rows: list[tuple[str, str]]) -> str:
    """Rows of (term, already-escaped html)."""
    out = ['<dl class="facts">']
    for term, value in rows:
        out.append("  <dt>%s</dt><dd>%s</dd>" % (esc(term), value))
    out.append("</dl>")
    return "\n".join(out)


def code(text: str) -> str:
    return "<code>%s</code>" % esc(text)


def repository_private() -> bool:
    """Whether the repository is private: from the workflow, else assumed.

    Anything but an explicit "false" is private. Assuming public would
    put links on a local preview that a reader of a private project's
    site could not follow."""
    return os.environ.get("SITE_REPOSITORY_PRIVATE", "true").strip() \
        .lower() != "false"


def source_link(ctx: dict, path: str, label: str | None = None) -> str:
    if ctx["private"]:
        return esc(label) if label else code(path)
    url = "%s/blob/%s/%s" % (ctx["repository"], ctx["commit"], path)
    return '<a href="%s">%s</a>' % (esc(url, quote=True),
                                    esc(label or path))


def commit_link(ctx: dict) -> str:
    stamp_html = '<code data-build="commit">%s</code>' % ctx["commit"][:12]
    if ctx["private"]:
        return stamp_html
    return '<a href="%s/tree/%s">%s</a>' % (
        esc(ctx["repository"], quote=True), ctx["commit"], stamp_html)


def contact_href(contact: str) -> str:
    return contact if re.match(r"^(https|mailto):", contact) \
        else "mailto:" + contact


def report_route(ctx: dict) -> str:
    """Where a reader sends a finding: the issues of a public repository,
    else the contact in site.json, else nowhere -- never a private
    repository's issues, which a reader cannot open."""
    if not ctx["private"]:
        return '<a href="%s">Report an issue</a>' % esc(
            ctx["repository"] + "/issues", quote=True)
    contact = (ctx["site"].get("contact") or "").strip()
    if contact:
        return '<a href="%s">Report an issue</a>' % esc(
            contact_href(contact), quote=True)
    return ""


def notice_block(text: str) -> str:
    return ('<section class="notice-block" aria-label="Status">\n'
            "  <p><strong>%s</strong></p>\n</section>" % esc(text))


def footer_notices(ctx: dict) -> list[str]:
    """The notices every page carries, composed from the project file,
    the pins and the licence -- the curated file says only whether IRIs
    resolve, whether the site is a draft, and who else to credit."""
    notices = ctx["site"]["notices"]
    out = []
    if notices["draft"].get("show"):
        out.append("<p class=\"notice\"><strong>%s</strong></p>"
                   % esc(notices["draft"]["text"]))
    if not notices["iri_resolution"].get("resolve"):
        out.append("<p class=\"notice\">%s</p>" % esc(
            "IRIs under %s identify terms and do not resolve over HTTP. Use "
            "the explorer or the downloads to inspect a term."
            % project.namespace()))
    upstream = ", ".join("%s %s" % (p["project"], p["licence"]["spdx"])
                         for p in pins())
    out.append("<p class=\"notice\">%s</p>" % esc(
        "Project-authored ontology, documentation and site content are "
        "offered under the %s licence. The vendored extracts carry their "
        "own licences (%s) and attribution, listed on the Modules and "
        "Downloads pages." % (ctx["licence"], upstream)))
    credit = "Developed by %s." % project.load()["licence_holder"]
    if notices["acknowledgment"].get("text"):
        credit += " " + notices["acknowledgment"]["text"]
    out.append("<p class=\"credit\">%s</p>" % esc(credit))
    return out


def shell(ctx: dict, key: str, title: str, body: str, depth: int) -> str:
    site = ctx["site"]
    prefix = "../" * depth
    nav = []
    for item in ctx["navigation"]:
        href = (prefix + item["path"]) or "./"
        current = ' aria-current="page"' if item["key"] == key else ""
        nav.append('      <a href="%s"%s>%s</a>'
                   % (esc(href, quote=True), current, esc(item["label"])))
    scripts = ""
    if key == "explore":
        scripts = ('\n  <script src="%sassets/js/ranking.js"></script>'
                   '\n  <script src="%sassets/js/explorer.js"></script>'
                   % (prefix, prefix))
    name = esc(ctx["name"])
    page_title = name if key == "home" else "%s &middot; %s" % (esc(title),
                                                                name)
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<link rel="stylesheet" href="%(prefix)sassets/css/site.css">
</head>
<body>
  <a class="skip" href="#main">Skip to content</a>
  <header class="masthead">
    <p class="wordmark"><a href="%(home)s">%(name)s</a></p>
    <nav aria-label="Primary">
%(nav)s
    </nav>
  </header>
  <main id="main" tabindex="-1" class="page-%(key)s">
%(body)s
  </main>
  <footer class="footer">
    %(notices)s
    <p class="build">Built from commit %(commit_link)s &middot;
      <span data-build="label">%(label)s</span>%(issues)s</p>
  </footer>%(scripts)s
</body>
</html>
""" % {
        "title": page_title,
        "prefix": prefix,
        "home": prefix or "./",
        "name": name,
        "nav": "\n".join(nav),
        "key": esc(key),
        "body": body,
        "notices": "\n    ".join(footer_notices(ctx)),
        "commit_link": commit_link(ctx),
        "label": esc(site["notices"]["build_label"]["text"]),
        "issues": (" &middot;\n      %s" % report_route(ctx)
                   if report_route(ctx) else ""),
        "scripts": scripts,
    }


# ------------------------------------------------------------- gather


def gather() -> dict:
    """Everything the pages are made from, read once."""
    import rdflib

    known = prefixes()
    authored = []
    for path in layout.ontology_files():
        authored.append({"key": path.stem, "path": relative(path),
                         "graph": parse(path), "origin": "authored",
                         "file": path})
    by_path = {}
    for pin in pins():
        for key in ("extract", "disjointness"):
            if pin.get(key):
                by_path[pin[key]] = pin
    upstream = []
    for path in layout.vendored_files():
        pin = by_path.get(relative(path))
        if pin is None:
            raise Refused("%s is vendored and no pin produces it"
                          % relative(path))
        upstream.append({"key": pin["id"], "path": relative(path),
                         "graph": parse(path), "origin": "upstream",
                         "file": path, "pin": pin,
                         "derived": relative(path) == pin.get("disjointness")})

    merged = rdflib.Graph()
    for source in authored + upstream:
        for triple in source["graph"]:
            merged.add(triple)
    authored_graph = rdflib.Graph()
    for source in authored:
        for triple in source["graph"]:
            authored_graph.add(triple)

    specs = [c.resolve() for c in layout.components("specification")]
    if len(specs) > 1:
        raise Refused("%d specifications are in force; the site renders one"
                      % len(specs))
    reviews = []
    for entry in layout.components("review"):
        reviews.extend(entry.members("*.md"))

    competency = load_tool("site_competency", "tools/ontology/competency.py")
    inside = None
    for entry in layout.components("example-data"):
        inside = entry.resolve()
    questions = competency.questions(_root)
    verdicts = competency.check(questions, _root, inside)
    texts = {}
    for path in questions:
        record, _problems = competency.read(path)
        texts[path.name] = record or {}

    mapping_tool = load_tool("site_mappings", "tools/ontology/mappings.py")
    mapping_files = mapping_tool.mapping_files()
    mapping_record = mapping_tool.check(mapping_files)
    mapping_sets = []
    for path in mapping_files:
        meta, rows, _columns = mapping_tool.read(path)
        mapping_sets.append({"path": path, "meta": meta, "rows": rows})

    linter = load_tool("site_lint", "tools/ontology/iri_lint.py")
    lint_findings = linter.lint(linter.default_paths())

    tags = [t for t in git("tag", "--merged", "HEAD", "--list", "v*")
            .splitlines() if t]

    def version_key(tag):
        return [int(p) if p.isdigit() else p
                for p in re.split(r"[.\-]", tag[1:])]

    tags.sort(key=version_key, reverse=True)
    releases = [{"tag": t, "commit": git("rev-list", "-n", "1", t)}
                for t in tags]

    return {
        "known": known,
        "authored": authored,
        "upstream": upstream,
        "merged": merged,
        "authored_graph": authored_graph,
        "records": term_records(authored + [u for u in upstream
                                            if not u["derived"]],
                                merged, known),
        "spec_path": specs[0] if specs else None,
        "reviews": reviews,
        "shapes": [e.resolve() for e in layout.components(
            "ontology-validation")],
        "extracts": read_json(EXTRACTS),
        "baseline": read_json(BASELINE),
        "decisions": sorted((p for p in layout.component("docs.decisions")
                             .members("*.md") if p.name != "README.md"),
                            key=lambda p: p.name),
        "questions": verdicts["results"],
        "question_texts": texts,
        "mapping_sets": mapping_sets,
        "mapping_findings": mapping_record["findings"],
        "lint_findings": lint_findings,
        "releases": releases,
    }


# ------------------------------------------------------------ sections


def scheme_trees(graph, known) -> str:
    """Every authored concept scheme, as the tree its top concepts and
    skos:broader make."""
    import rdflib

    namespace = project.namespace()
    skos = rdflib.Namespace(SKOS)
    schemes = sorted(s for s in graph.subjects(rdflib.RDF.type,
                                               skos.ConceptScheme)
                     if str(s).startswith(namespace))
    if not schemes:
        return ("<p>No concept scheme is authored yet. A vocabulary about "
                "terms -- a catalogue, a code list -- goes in a module of its "
                "own, as a skos:ConceptScheme.</p>")

    def label(node):
        return literal(graph, node, SKOS + "prefLabel", "skos:prefLabel",
                       required=False) or short_id(str(node), known)

    def branch(node, scheme, seen):
        children = sorted(
            (c for c in graph.subjects(skos.broader, node)
             if (c, skos.inScheme, scheme) in graph and c not in seen),
            key=lambda c: (label(c).lower(), str(c)))
        if not children:
            return ""
        items = []
        for child in children:
            items.append("<li>%s %s%s</li>" % (
                esc(label(child)), code(short_id(str(child), known)),
                branch(child, scheme, seen | {child})))
        return "<ul>%s</ul>" % "".join(items)

    out = []
    for scheme in schemes:
        tops = set(graph.objects(scheme, skos.hasTopConcept)) | set(
            graph.subjects(skos.topConceptOf, scheme))
        items = []
        for top in sorted(tops, key=lambda c: (label(c).lower(), str(c))):
            items.append("<li>%s %s%s</li>" % (
                esc(label(top)), code(short_id(str(top), known)),
                branch(top, scheme, {top})))
        out.append("<h2>%s</h2>\n<p>%s</p>\n<ul class=\"tree\">\n%s\n</ul>"
                   % (esc(label(scheme)), code(str(scheme)),
                      "\n".join(items) or "<li>no top concept</li>"))
    return "\n".join(out)


def question_sections(data: dict, known) -> tuple[str, str]:
    """(summary, sections) for the competency questions."""
    results = data["questions"]
    if not results:
        none = ("<p>No competency question is written yet. Each goes in "
                "competency-questions/ as a query with the answer it must "
                "give.</p>")
        return none, ""
    counted = {}
    for row in results:
        counted[row["verdict"]] = counted.get(row["verdict"], 0) + 1
    summary = definition_list([
        ("Questions", "%d" % len(results)),
        ("Answerable", "%d" % sum(1 for r in results
                                  if r["status"] == "answerable")),
    ] + [("Verdict: %s" % verdict, "%d" % n)
         for verdict, n in sorted(counted.items())])
    sections = []
    for row in sorted(results, key=lambda r: r["id"]):
        record = data["question_texts"].get(row["file"], {})
        anchor = re.sub(r"[^a-z0-9-]", "-", str(row["id"]).lower())
        sections.append(
            '<section id="%s">\n<h2>%s</h2>\n<p>%s</p>\n%s\n'
            '<pre class="query"><code>%s</code></pre>\n</section>' % (
                esc(anchor, quote=True), esc(str(row["id"])),
                esc(str(record.get("question", ""))),
                definition_list([
                    ("Status", esc(str(row["status"]))),
                    ("Verdict", '<span class="verdict verdict-%s">%s</span>'
                     " &mdash; %s" % (esc(row["verdict"].replace(" ", "-"),
                                          quote=True),
                                      esc(row["verdict"]),
                                      esc(str(row["detail"])))),
                    ("Depends on", " ".join(code(str(t)) for t in
                                            record.get("depends_on") or [])
                     or "&mdash;"),
                    ("Examples", " ".join(code(str(e)) for e in
                                          record.get("examples") or [])
                     or "none: the classes alone"),
                ]), esc(str(record.get("query", "")).rstrip())))
    return summary, "\n".join(sections)


def mapping_sections(data: dict, ctx: dict) -> str:
    if not data["mapping_sets"]:
        return ("<p>No mapping set is written yet. Each goes in mappings/ "
                "as an SSSOM file, one per target vocabulary.</p>")
    out = []
    for entry in data["mapping_sets"]:
        meta, rows = entry["meta"], entry["rows"]
        body = "\n".join(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                code(r.get("subject_id", "")), code(r.get("predicate_id", "")),
                code(r.get("object_id", "")),
                code(r.get("mapping_justification", "")))
            for r in rows)
        out.append(
            "<h2>%s</h2>\n%s\n<div class=\"scroll-x\"><table>\n<thead><tr>"
            "<th>Subject</th><th>Predicate</th><th>Object</th>"
            "<th>Justification</th></tr></thead>\n<tbody>\n%s\n</tbody>"
            "</table></div>" % (
                esc(entry["path"].name), definition_list([
                    ("Mapping set", code(str(meta.get("mapping_set_id", "")))),
                    ("Licence", code(str(meta.get("license", "")))),
                    ("Mappings", "%d" % len(rows)),
                    ("Source", source_link(ctx, relative(entry["path"]))),
                ]), body))
    findings = data["mapping_findings"]
    out.append("<p>%s</p>" % (
        "Every mapping set passes tools/ontology/mappings.py."
        if not findings else
        "%d finding(s) from tools/ontology/mappings.py at this commit."
        % len(findings)))
    return "\n".join(out)


def release_list(data: dict, ctx: dict) -> str:
    if not data["releases"]:
        return ("<p>No release yet. Tagging a commit v&lt;MAJOR&gt;.&lt;MINOR&gt;"
                ".&lt;PATCH&gt; runs every check and the reasoner on it, "
                "builds the artefacts twice, and publishes them.</p>")
    def tag(name):
        if ctx["private"]:
            return esc(name)
        return '<a href="%s">%s</a>' % (esc("%s/releases/tag/%s" % (
            ctx["repository"], name), quote=True), esc(name))

    rows = "\n".join(
        "<tr><td>%s</td><td>%s</td></tr>" % (tag(r["tag"]),
                                            code(r["commit"][:12]))
        for r in data["releases"])
    return ('<div class="scroll-x"><table>\n<thead><tr><th>Version</th>'
            "<th>Commit</th></tr></thead>\n<tbody>\n%s\n</tbody></table>"
            "</div>" % rows)


# --------------------------------------------------------------- build


def build(out: Path) -> list[tuple[str, str]]:
    site = read_json(CONTENT)
    commit, epoch = stamp()
    data = gather()
    disposition = load_tool("site_disposition",
                            "tools/licensing/disposition.py")
    roles = {c.role for c in layout.components()}
    navigation = [item for item in site["navigation"]
                  if not item.get("when") or item["when"] in roles]
    ctx = {"site": site, "commit": commit, "navigation": navigation,
           "name": project.load()["title"],
           "repository": "https://github.com/" + project.repository(),
           "private": repository_private(),
           "licence": disposition.project_licence()}
    files: dict[str, bytes] = {}
    known = data["known"]
    pid = project.project_id()

    authored_terms = [r for r in data["records"] if r["origin"] == "authored"]
    upstream_terms = [r for r in data["records"] if r["origin"] == "upstream"]
    findings = sum(r.get("authored_findings", 0)
                   for r in data["baseline"]["rungs"].values())

    # ---- data
    modules = ([{"key": s["key"], "title": ontology_header(
                    s["graph"], s["path"])["title"] or s["key"],
                 "origin": "authored"} for s in data["authored"]]
               + [{"key": s["key"], "title": "%s %s" % (
                    s["pin"]["project"], s["pin"]["release"]),
                   "origin": "upstream"}
                  for s in data["upstream"] if not s["derived"]])
    modules = sorted({m["key"]: m for m in modules}.values(),
                     key=lambda m: (m["origin"], m["key"]))
    terms = {
        "format_version": 1,
        "generated_by": "tools/site/build_site.py",
        "source_commit": commit,
        "authored_namespace": project.namespace(),
        "modules": modules,
        "counts": {"authored": len(authored_terms),
                   "upstream": len(upstream_terms)},
        "classes": data["records"],
        "note": "`classes` holds every term, properties included; the name "
                "is the explorer's. Upstream terms are vendored, not "
                "authored here; `origin` says which.",
    }
    files["data/terms.json"] = (json.dumps(terms, indent=2, sort_keys=True,
                                           ensure_ascii=False)
                                .encode("utf-8") + b"\n")

    # ---- downloads
    authored_files = [s["file"] for s in data["authored"]] + data["shapes"]
    download_rows, bundle_members, sums = [], [], []
    for path in authored_files:
        raw = source_bytes(path)
        files["downloads/" + path.name] = raw
        download_rows.append({"file": path.name, "path": relative(path),
                              "bytes": len(raw), "sha256": sha256(raw),
                              "origin": "authored"})
        bundle_members.append((pid + "/" + path.name, raw))
        sums.append("%s  %s" % (sha256(raw), path.name))
    licence = source_bytes(_root / "LICENSE")
    bundle_members.append((pid + "/LICENSE", licence))
    sums.append("%s  %s" % (sha256(licence), "LICENSE"))
    sums_bytes = ("\n".join(sorted(sums, key=lambda s: s[66:])) + "\n"
                  ).encode("utf-8")
    bundle_members.append((pid + "/SHA256SUMS", sums_bytes))
    bundle_name = "%s-ontology.zip" % pid
    bundle = deterministic_zip(bundle_members, epoch)
    files["downloads/" + bundle_name] = bundle

    spec = None
    if data["spec_path"] is not None:
        spec_bytes = source_bytes(data["spec_path"])
        files["downloads/" + data["spec_path"].name] = spec_bytes
        spec = {"file": data["spec_path"].name,
                "path": relative(data["spec_path"]),
                "bytes": len(spec_bytes), "sha256": sha256(spec_bytes)}
    upstream_rows = []
    for source in data["upstream"]:
        raw = source_bytes(source["file"])
        files["downloads/upstream/" + source["file"].name] = raw
        upstream_rows.append({"file": source["file"].name,
                              "path": source["path"], "bytes": len(raw),
                              "sha256": sha256(raw), "origin": "upstream",
                              "licence": source["pin"]["licence"]["spdx"]})
    files["downloads/upstream/NOTICE.md"] = source_bytes(
        layout.path("docs.vendor-notice"))

    manifest = {
        "format_version": 1,
        "generated_by": "tools/site/build_site.py",
        "source_commit": commit,
        "repository": ctx["repository"],
        "repository_linked": not ctx["private"],
        "bundle": {"filename": bundle_name, "bytes": len(bundle),
                   "sha256": sha256(bundle), "root": pid + "/",
                   "members": sorted(name for name, _ in bundle_members)},
        "authored": download_rows,
        "specification": spec,
        "upstream": upstream_rows,
    }
    files["data/downloads.json"] = (json.dumps(manifest, indent=2,
                                               sort_keys=True)
                                    .encode("utf-8") + b"\n")

    # ---- page values
    competency_summary, question_html = question_sections(data, known)
    answered = sum(1 for r in data["questions"] if r["verdict"] == "pass")
    answerable = sum(1 for r in data["questions"]
                     if r["status"] == "answerable")
    latest = data["releases"][0]["tag"] if data["releases"] else "none yet"
    status_summary = definition_list([
        ("Authored terms", "%d" % len(authored_terms)),
        ("Upstream terms in use", "%d, from %d pinned sources" % (
            len(upstream_terms), len(pins()))),
        ("Open validation findings", "%d" % findings),
        ("IRI lint findings", "%d" % len(data["lint_findings"])),
        ("Competency questions answered", "%d of %d answerable" % (
            answered, answerable)),
        ("Latest release", '<a href="releases/">%s</a>' % esc(latest)),
    ])
    reviewer_items = ["  <li>%s</li>" % esc(item)
                      for item in site["home"]["for_reviewers"]]
    if report_route(ctx):
        reviewer_items.append(
            "  <li>%s for anything you find. A finding with the term it "
            "concerns is the most useful kind.</li>" % report_route(ctx))
    for_reviewers = "<ol>\n%s\n</ol>" % "\n".join(reviewer_items)
    related = "".join(
        ' Related: <a href="%s">%s</a>.' % (esc(r["url"], quote=True),
                                            esc(r["label"]))
        for r in site.get("related") or [])

    authored_modules = []
    for source in data["authored"]:
        header = ontology_header(source["graph"], source["path"])
        count = sum(1 for r in authored_terms if r["module"] == source["key"])
        authored_modules.append("<h3>%s</h3>\n%s\n%s" % (
            esc(header["title"] or source["key"]),
            "<p>%s</p>" % esc(header["comment"]) if header["comment"] else "",
            definition_list([
                ("Terms", "%d" % count),
                ("Version", esc(header["version"] or "none stated")),
                ("Ontology IRI", code(header["iri"])),
                ("Namespace", code(project.namespace())),
                ("Source", source_link(ctx, source["path"])),
                ("Download", '<a href="../downloads/%s">%s</a>' % (
                    esc(source["file"].name, quote=True),
                    esc(source["file"].name))),
            ])))
    shape_rows = []
    for path in data["shapes"]:
        rung = None
        for name, entry in data["baseline"]["rungs"].items():
            if layout.component(name).resolve() == path:
                rung = entry
        shape_rows.append("<li>%s &mdash; %s recorded finding(s)</li>" % (
            source_link(ctx, relative(path)),
            esc(str(rung["authored_findings"])) if rung else "no baseline"))
    upstream_sources = []
    for pin in pins():
        record = data["extracts"]["extracts"][pin["id"]]
        rows = [
            ("Commit", code(pin["commit"])),
            ("Licence", '<a href="%s">%s</a>' % (
                esc(pin["licence"]["url"], quote=True),
                esc(pin["licence"]["spdx"]))),
            ("Attribution", esc(" ".join(
                pin["licence"]["attribution"].split()))),
            ("Selected", esc(pin.get("select", "named"))),
            ("Terms", "%d in full, %d declared as stubs; %d in the register"
             % (record["terms_described_in_full"],
                record["terms_declared_as_stubs"],
                record.get("register_terms", 0))),
            ("Axioms dropped", "%d (anonymous class expressions)"
             % record["axioms_dropped_anonymous_object"]),
            ("Extract", source_link(ctx, pin["extract"])),
        ]
        if pin.get("disjointness"):
            rows.append(("Derived disjointness", "%d pairs from %d "
                         "AllDisjointClasses axioms &mdash; %s" % (
                             record.get("disjointness_pairs", 0),
                             record.get("disjointness_axioms", 0),
                             source_link(ctx, pin["disjointness"]))))
        upstream_sources.append("<h3>%s %s</h3>\n%s" % (
            esc(pin["project"]), esc(pin["release"]), definition_list(rows)))

    decision_rows = []
    for path in data["decisions"]:
        first = path.read_text(encoding="utf-8").splitlines()[0]
        decision_rows.append("<li>%s</li>" % source_link(
            ctx, relative(path), first.lstrip("# ").strip()))
    decisions = ("<ul>\n%s\n</ul>" % "\n".join(decision_rows)
                 if decision_rows else "<p>None recorded yet.</p>")

    validation = definition_list(
        [("Authored terms checked", "%d" % len(authored_terms))]
        + [(name, "%d recorded finding(s)" % entry["authored_findings"])
           for name, entry in sorted(data["baseline"]["rungs"].items())]) + (
        "<p>With no authored term written, every shape set conforms "
        "vacuously. What shows the shapes work is the fixture built to break "
        "them, which they reject.</p>" if not authored_terms else "")

    unresolved_parts = []
    for key, record in sorted(data["extracts"]["extracts"].items()):
        names = record.get(
            "named_by_specification_described_by_no_pinned_file") or []
        if names:
            unresolved_parts.append(
                "<h3>%s (%d)</h3>\n<ul class=\"term-list\">\n%s\n</ul>"
                % (esc(key.upper()), len(names), "\n".join(
                    "  <li>%s</li>" % code(short_id(iri, known))
                    for iri in names)))
    unresolved = "\n".join(unresolved_parts) or "<p>None.</p>"

    def file_table(rows: list[dict], href_prefix: str, show_licence: bool):
        head = "<th>File</th><th>Bytes</th><th>SHA-256</th>" + (
            "<th>Licence</th>" if show_licence else "")
        body = "\n".join(
            "<tr><td><a href=\"%s%s\">%s</a></td><td>%s</td><td>%s</td>%s"
            "</tr>" % (href_prefix, esc(r["file"], quote=True),
                       esc(r["file"]), "{:,}".format(r["bytes"]),
                       code(r["sha256"]),
                       "<td>%s</td>" % esc(r["licence"]) if show_licence
                       else "")
            for r in rows)
        return ('<div class="scroll-x"><table>\n<thead><tr>%s</tr></thead>'
                "\n<tbody>\n%s\n</tbody></table></div>" % (head, body))

    bundle_html = (
        "<p>Every authored module and shape set, the licence, and a "
        "SHA256SUMS file, in one archive. Upstream extracts are not "
        "included.</p>\n<p><a href=\"%s\">Download %s</a> (%s bytes)</p>\n%s"
        "\n<p>The archive is byte-reproducible: member order, timestamps, "
        "permissions and creating system are fixed.</p>"
        % (esc(bundle_name, quote=True), esc(bundle_name),
           "{:,}".format(len(bundle)), definition_list([
               ("SHA-256", code(sha256(bundle))),
               ("Members", "%d" % len(bundle_members)),
           ])))

    values = {
        "site_name": esc(ctx["name"]),
        "tagline": esc(site["tagline"]),
        "summary": esc(project.load()["description"]),
        "draft_notice": (notice_block(site["notices"]["draft"]["text"])
                         if site["notices"]["draft"].get("show") else ""),
        "status_summary": status_summary,
        "for_reviewers": for_reviewers,
        "foundations": " and ".join(esc("%s %s" % (p["project"],
                                                   p["release"]))
                                    for p in pins()),
        "related": related,
        "authored_modules": "\n".join(authored_modules),
        "shape_sets": "<ul>\n%s\n</ul>" % "\n".join(shape_rows),
        "upstream_sources": "\n".join(upstream_sources),
        "schemes": scheme_trees(data["authored_graph"], known),
        "competency_summary": competency_summary,
        "questions": question_html,
        "mapping_sets": mapping_sections(data, ctx),
        "decisions": decisions,
        "validation": validation,
        "unresolved": unresolved,
        "releases": release_list(data, ctx),
        "bundle": bundle_html,
        "authored_files": file_table(download_rows, "", False),
        "upstream_files": file_table(upstream_rows, "upstream/", True)
        + '\n<p>Attribution for all of them: <a href="upstream/NOTICE.md">'
          "NOTICE.md</a>.</p>",
        "explore_notice": notice_block(
            "No authored term is written yet. Everything listed below is "
            "upstream: the BFO and CCO terms this ontology builds on. Authored "
            "terms will appear beside them, marked as authored.")
        if not authored_terms else "",
    }
    if data["spec_path"] is not None:
        spec_text = data["spec_path"].read_text(encoding="utf-8")
        spec_body, spec_toc = render_markdown(spec_text)
        values.update({
            "spec_facts": definition_list([
                ("Source", source_link(ctx, spec["path"])),
                ("SHA-256", code(spec["sha256"])),
                ("Download", '<a href="../downloads/%s">%s</a> (%s bytes)' % (
                    esc(spec["file"], quote=True), esc(spec["file"]),
                    "{:,}".format(spec["bytes"]))),
            ]),
            "spec_toc": spec_toc, "spec_body": spec_body})
    if data["reviews"]:
        parts = []
        for path in data["reviews"]:
            raw = source_bytes(path)
            body, _toc = render_markdown(raw.decode("utf-8"))
            parts.append("%s\n<article class=\"doc\">\n%s\n</article>" % (
                definition_list([("Source", source_link(ctx, relative(path))),
                                 ("SHA-256", code(sha256(raw)))]), body))
        values["reviews"] = "\n".join(parts)

    labels = {item["key"]: item["label"] for item in navigation}
    declared = {item["key"] for item in site["navigation"]}
    for item in navigation:
        key = item["key"]
        fragment_path = _root / PAGES / (key + ".html")
        if not fragment_path.is_file():
            raise Refused("navigation names %s and %s does not exist"
                          % (key, relative(fragment_path)))
        body = fill(fragment_path.read_text(encoding="utf-8"), values, key)
        depth = 0 if not item["path"] else item["path"].count("/")
        files[(item["path"] or "") + "index.html"] = shell(
            ctx, key, labels[key], body, depth).encode("utf-8")
    unused = sorted(p.stem for p in (_root / PAGES).glob("*.html")
                    if p.stem not in declared)
    if unused:
        raise Refused("page fragments no navigation entry names: %s"
                      % unused)

    # ---- assets
    assets = _root / ASSETS
    refused = []
    for path in sorted(assets.rglob("*"), key=lambda p: p.as_posix()):
        if path.is_dir():
            continue
        if path.name.startswith(".") or path.suffix not in \
                ALLOWED_ASSET_SUFFIXES:
            refused.append(path.relative_to(assets).as_posix())
            continue
        files[path.relative_to(assets).as_posix()] = source_bytes(path)
    if refused:
        raise Refused("%s holds files this build has no rule for: %s"
                      % (ASSETS, refused))

    # ---- write
    clear_output(out)
    written = []
    for name in sorted(files):
        dest = out / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(files[name])
        os.utime(dest, (epoch, epoch))
        written.append((name, sha256(files[name])))
    return written


def clear_output(out: Path) -> None:
    """Empty the artifact so no file from a previous build survives."""
    if not out.exists():
        out.mkdir(parents=True)
        return
    for path in sorted(out.rglob("*"), key=lambda q: len(q.parts),
                       reverse=True):
        try:
            path.rmdir() if path.is_dir() else path.unlink()
        except OSError as exc:
            if not path.is_dir():
                raise Refused("cannot remove %s from the previous build: %s"
                              % (path, exc))


def tree_digest(written: list[tuple[str, str]]) -> str:
    return sha256("\n".join("%s %s" % row for row in written)
                  .encode("utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=OUTPUT)
    args = ap.parse_args(argv)
    out = Path(args.out)
    out = out if out.is_absolute() else _root / out
    written = build(out)
    for name, digest in written:
        print("    %-52s %s" % (name, digest[:16]))
    print()
    print("  %d file(s) -> %s" % (len(written), args.out))
    print("  tree digest %s" % tree_digest(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
