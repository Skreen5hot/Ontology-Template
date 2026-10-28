# SPDX-License-Identifier: MIT
"""Exactly one licensing disposition per tracked file.

    python tools/licensing/disposition.py              # summary
    python tools/licensing/disposition.py --list third-party-cited
    python tools/licensing/disposition.py --check      # exit 1 on a finding

Derived from the declared role in the layout contract plus explicit owner
adjudications, never from a list of filenames. A list of filenames decays
in two directions at once: it stops matching what is there, and nothing
notices.

Every rule that matches is collected rather than the first one winning. A
first-match chain silently prefers whichever rule was written earliest,
and a later contradictory rule is never seen. Two matches is a refusal,
and so is none.

THE QUESTION THIS EXISTS TO ANSWER

Not "what licence is this" but "may this be published". Those differ
exactly where it matters. Reference material consulted while building an
ontology is cited, not redistributed, and a repository that contains it
is redistributing it whatever the README says.

There are three third-party answers here, not one. A licensed framework
may not be redistributed at all. A permissive upstream may, on condition
-- and a condition nobody checks is a condition nobody meets, so the
attribution every vendored licence requires is a check below rather than
a notice file somebody remembers to update.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402

CONTENT = "project-content"
SOFTWARE = "project-software"
CITED = "third-party-cited"
#: Third-party, redistributed, and permitted to be. The distinction from
#: CITED is the licence and not the convenience: BFO is CC BY 4.0 and CCO
#: is BSD-3-Clause, and both allow redistribution provided attribution
#: travels with the work. A sister ontology pinned beside them is held to
#: whatever its own licence says.
VENDORED = "third-party-redistributed"

UPSTREAM_SOURCES = "config/upstream-sources.yaml"
NOTICE = "vendor/NOTICE.md"

#: SPDX identifiers this tool can recognise in a LICENSE file. Listed
#: rather than pattern-matched, because "BSD" appears in several licences
#: that are not the same licence -- a lesson from the project this was
#: carried from, which shipped a BSD template and tested only for a
#: phrase every BSD variant contains.
KNOWN_LICENCES = (
    ("MIT License", "MIT"),
    ("Apache License", "Apache-2.0"),
    ("Creative Commons Attribution 4.0", "CC-BY-4.0"),
    ("GNU GENERAL PUBLIC LICENSE", "GPL-3.0-or-later"),
    ("Mozilla Public License", "MPL-2.0"),
)


def project_licence() -> str:
    """What this repository actually offers itself under.

    Read from LICENSE rather than written here. A hardcoded map would
    assert a licence the repository does not declare, which is the same
    class of error as a README claiming a redistribution policy the
    contents contradict.

    A content/software split -- published ontology under one licence and
    tooling under another -- is a reasonable owner decision and is what
    the project this method came from settled on. It is not assumed here:
    right now this repository says one licence for everything, and this
    reports that.
    """
    text = layout.component("licence.project").resolve().read_text(
        encoding="utf-8")
    found = [spdx for needle, spdx in KNOWN_LICENCES if needle in text]
    if len(found) != 1:
        raise Refused(
            "LICENSE names %d recognised licences (%s). Exactly one is "
            "required, because every project-authored file is reported as "
            "carrying it." % (len(found), found or "none"))
    return found[0]


def vendored_sources() -> dict:
    """Pinned upstreams, indexed by every path each produces: its extract
    and its register, both the upstream's content under its licence.

    Read here rather than restated, so the licence this tool reports for
    a vendored file and the licence the vendoring tool wrote into that
    file come from one declaration.
    """
    import yaml

    root = layout.repository_root()
    path = root / UPSTREAM_SOURCES
    if not path.is_file():
        raise Refused(
            UPSTREAM_SOURCES + " is missing, so the licence of every "
            "vendored extract would have to be guessed from its contents.")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    found = {}
    for entry in raw.get("sources") or []:
        for required in ("extract", "licence"):
            if not entry.get(required):
                raise Refused("a source in %s declares no %r"
                              % (UPSTREAM_SOURCES, required))
        for required in ("spdx", "attribution"):
            if not entry["licence"].get(required):
                raise Refused("%s declares no licence.%s for %s"
                              % (UPSTREAM_SOURCES, required,
                                 entry["extract"]))
        found[entry["extract"]] = entry
        for derived in ("register", "disjointness"):
            if entry.get(derived):
                found[entry[derived]] = entry
    return found


def licence_of(disposition: str, relative=None):
    if disposition == CITED:
        return None
    if disposition == VENDORED:
        sources = vendored_sources()
        if relative not in sources:
            raise Refused(
                "%s is declared vendored, and %s pins no source producing "
                "it, so nothing states what licence it carries."
                % (relative, UPSTREAM_SOURCES))
        return sources[relative]["licence"]["spdx"]
    return project_licence()

ADJUDICATIONS = "config/licensing-adjudications.yaml"

#: Roles whose files this repository authored and may publish as content.
#:
#: `specification`: a design document the project is built against. A
#: role of its own rather than `documentation` because it carries a
#: consequence beyond licensing -- the vendoring tool reads it for the
#: upstream terms the design names. A superseded specification is
#: re-roled `documentation` in the commit that supersedes it, so it stops
#: seeding the day it is superseded. The template has none.
#:
#: `historical-draft`: an earlier iteration of the project's own work,
#: preserved byte-for-byte as it was imported. Content under the project
#: licence, code included -- which is why it sits here rather than in
#: SOFTWARE_ROLES. A role of its own so that nothing loads its Turtle as
#: ontology: its defects are not this corpus's defects.
#:
#: `site-source`: a public site's page fragments, curated copy,
#: stylesheet and scripts. Content rather than software, JavaScript
#: included, because the site is a published document: what it says is
#: the point, and the scripts only search and display it.
#:
#: `communication`: messages to and from other teams (communications/).
#: Content under the project licence. Incoming messages are other teams'
#: words, copied verbatim; the teams this template was cut from all have
#: one author. A message from a team with a different owner needs its own
#: role and rule, as cited references do.
CONTENT_ROLES = {"ontology-module", "ontology-module-set",
                 "ontology-validation", "test-fixture", "documentation",
                 "generated-artifact", "specification", "historical-draft",
                 "site-source", "communication", "example-data",
                 "competency-question", "research", "vocabulary-intake",
                 "mapping-set"}

#: Roles that are software rather than published content.
SOFTWARE_ROLES = {"tool", "configuration"}

#: The repository's own terms. Content, and the file every other
#: disposition is derived from.
LICENCE_ROLES = {"project-licence"}

#: Roles this repository may not redistribute at all.
CITED_ROLES = {"third-party-reference"}

#: Roles that are somebody else work, redistributed under their terms.
#: `vendored-register` is the per-source list of every term and its
#: labels: the upstream's words, so the upstream's licence, and a role of
#: its own because it is JSON and must never be parsed as ontology.
VENDORED_ROLES = {"vendored-ontology", "vendored-register"}

#: Suffix rules for files no component claims. Kept small on purpose: the
#: contract is the primary authority and this is the fallback, so a
#: growing list here means the contract is being left behind.
SOFTWARE_SUFFIXES = (".py", ".cfg", ".ini", ".toml", ".yml", ".yaml")
CONTENT_SUFFIXES = (".ttl", ".md", ".html", ".css", ".svg", ".png", ".jsonld",
                    ".cff", ".txt", ".tsv", ".json")

#: Suffixless root files that are repository configuration.
CONFIG_NAMES = (".gitignore", ".gitattributes", ".nvmrc")


class Refused(SystemExit):
    """Raised rather than guessing. Every message names the file."""


class Disposition(NamedTuple):
    path: str
    role: str
    disposition: str
    licence: str | None
    redistributable: bool
    rationale: str


def git(*args: str) -> list[str]:
    root = layout.repository_root()
    result = subprocess.run(["git", *args], cwd=str(root),
                            capture_output=True, text=True)
    if result.returncode:
        raise Refused("git " + " ".join(args) + " failed: "
                      + result.stderr.strip()[-300:])
    return result.stdout.splitlines()


def adjudications() -> dict[str, dict]:
    """Owner rulings, indexed by the single path each names."""
    import yaml

    root = layout.repository_root()
    path = root / ADJUDICATIONS
    if not path.is_file():
        raise Refused(
            ADJUDICATIONS + " is missing. It records the rulings that "
            "override a derived disposition, and without it an override "
            "would be invisible rather than absent.")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    found: dict[str, dict] = {}
    for entry in raw.get("adjudications") or []:
        for required in ("path", "disposition", "why", "decided",
                         "decided_by"):
            if not entry.get(required):
                raise Refused(
                    "an adjudication in %s declares no %r: %r"
                    % (ADJUDICATIONS, required, entry))
        if entry["path"] in found:
            raise Refused("two adjudications name " + entry["path"])
        if entry["disposition"] not in (CONTENT, SOFTWARE, CITED,
                                        VENDORED):
            raise Refused("unknown disposition %r in %s"
                          % (entry["disposition"], ADJUDICATIONS))
        found[entry["path"]] = entry
    return found


def rules(relative: str, owner) -> list[tuple[str, str, str]]:
    """Every rule that matches, so overlap is visible rather than resolved."""
    matched: list[tuple[str, str, str]] = []

    if owner is not None:
        role = owner.role
        if role in CITED_ROLES:
            matched.append((
                CITED, role,
                "third-party reference material, consulted and cited; this "
                "repository grants no rights over it and must not "
                "redistribute it"))
        elif role in VENDORED_ROLES:
            matched.append((
                VENDORED, role,
                "a pinned extract of a third-party ontology, redistributed "
                "under the upstream licence and requiring attribution"))
        elif role in SOFTWARE_ROLES:
            matched.append((SOFTWARE, role, "repository tooling"))
        elif role in LICENCE_ROLES:
            matched.append((CONTENT, role,
                            "the repository's own licence text"))
        elif role in CONTENT_ROLES:
            matched.append((CONTENT, role, "project-authored content"))
        else:
            raise Refused(
                "%s belongs to component %s whose role %r has no licensing "
                "rule. Add one deliberately rather than letting the file "
                "fall through to a suffix guess."
                % (relative, owner.id, role))
        return matched

    # No component claims it. Fall back to suffix, and say so, because a
    # file nothing declares is a file nobody decided about.
    name = Path(relative).name
    suffix = Path(relative).suffix.lower()
    if "/" not in relative and (name in CONFIG_NAMES
                                or name.startswith("requirements")):
        matched.append((SOFTWARE, "(undeclared)",
                        "repository configuration at the root"))
    elif relative.startswith((".github/", "tools/", "tests/", "config/")):
        matched.append((SOFTWARE, "(undeclared)",
                        "under a tooling directory"))
    elif suffix in SOFTWARE_SUFFIXES:
        matched.append((SOFTWARE, "(undeclared)", "software by suffix"))
    elif suffix in CONTENT_SUFFIXES:
        matched.append((CONTENT, "(undeclared)", "content by suffix"))
    return matched


def classify() -> list[Disposition]:
    ruled = adjudications()
    out: list[Disposition] = []
    problems: list[str] = []

    for relative in git("ls-files"):
        if relative in ruled:
            entry = ruled[relative]
            out.append(Disposition(
                relative, "(adjudicated)", entry["disposition"],
                entry.get("licence",
                          licence_of(entry["disposition"], relative)),
                entry["disposition"] != CITED,
                "owner ruling %s: %s" % (entry["decided"], entry["why"])))
            continue

        owner = layout.owning_component(relative)
        matched = rules(relative, owner)
        if len(matched) != 1:
            problems.append(
                "%s matches %d disposition rules%s"
                % (relative, len(matched),
                   "" if matched else " -- nothing declares it and no "
                                     "suffix rule reaches it"))
            continue
        disposition, role, why = matched[0]
        out.append(Disposition(relative, role, disposition,
                               licence_of(disposition, relative),
                               disposition != CITED, why))

    unused = sorted(set(ruled) - {row.path for row in out})
    if unused:
        problems.append(
            "adjudications naming no tracked file: %s -- an exception "
            "granted for nothing reads as coverage" % unused)

    if problems:
        raise Refused("licensing could not be determined:\n  "
                      + "\n  ".join(problems))
    return out


def attribution_findings(rows) -> list:
    """Redistribution on condition, with the condition checked.

    Both vendored licences permit redistribution provided attribution
    travels with the work. `vendor/NOTICE.md` is generated, which makes
    it right on the day it is written and says nothing about the day a
    source is added and the notice is not regenerated. So the pins are
    read here and each declared attribution is required to appear in it.
    """
    out = []
    vendored = [r for r in rows if r.disposition == VENDORED]
    if not vendored:
        return out

    root = layout.repository_root()
    notice = root / NOTICE
    if not notice.is_file():
        return ["%d vendored extract(s) are tracked and %s does not exist. "
                "Both upstream licences permit redistribution on condition "
                "of attribution, and this repository is redistributing "
                "without it." % (len(vendored), NOTICE)]

    flat = " ".join(notice.read_text(encoding="utf-8").split())
    sources = vendored_sources()
    missing = []
    for row in vendored:
        attribution = " ".join(
            sources[row.path]["licence"]["attribution"].split())
        if attribution not in flat:
            missing.append("%s: %s" % (row.path, attribution))
    if missing:
        out.append(
            "%d vendored extract(s) are redistributed without the "
            "attribution their licence requires appearing in %s:"
            % (len(missing), NOTICE)
            + chr(10) + "    " + (chr(10) + "    ").join(missing))
    return out


#: What research/ may hold: the project's own notes, tables and
#: bibliographies. Anything else is likely a source, which belongs in the
#: never-tracked reference component.
RESEARCH_SUFFIXES = (".md", ".txt", ".tsv", ".csv", ".bib", ".yaml", ".yml")


def research_findings(rows) -> list:
    """A source copied into research/ is redistributed like any other
    tracked file. Refused by suffix, and by content: a file whose bytes are
    those of a file in the reference component is a copy whatever its
    name. The content half can only look at reference files present on
    this machine; in CI there are none, and the suffix half stands alone.
    """
    import hashlib

    research = [c for c in layout.components() if c.role == "research"]
    if not research:
        return []
    prefixes = tuple(c.path + "/" for c in research)
    tracked = [r.path for r in rows if r.path.startswith(prefixes)]
    root = layout.repository_root()
    out = []
    odd = [p for p in tracked if Path(p).suffix.lower() not in RESEARCH_SUFFIXES]
    if odd:
        out.append("%d file(s) in research/ are not notes, tables or "
                   "bibliographies, and are likely sources, which belong in "
                   "the never-tracked reference component: %s" % (len(odd),
                                                                  odd[:6]))
    reference = {}
    for entry in layout.components():
        if entry.role in CITED_ROLES and entry.exists():
            for path in entry.members("*"):
                if path.is_file():
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    reference[digest] = path.name
    copies = [p for p in tracked
              if hashlib.sha256((root / p).read_bytes()).hexdigest()
              in reference]
    if copies:
        out.append("%d file(s) in research/ are byte-for-byte copies of "
                   "reference material: %s" % (len(copies), copies[:6]))
    return out


def embedded_text(root=None) -> list[dict]:
    """Declared third-party text inside the authored modules: per module
    and property, how many values and the licence as declared. Listed
    apart from the module's own disposition, which is per file and cannot
    see a quotation (T9). The validator holds each module to its
    declaration; this only classifies."""
    import rdflib

    import third_party

    declarations = third_party.load(root)
    out = []
    if not declarations:
        return out
    base = root or layout.repository_root()
    for path in layout.ontology_files():
        graph = rdflib.Graph()
        graph.parse(path, format="turtle")
        for declaration in declarations:
            count = third_party.values_in(graph, declaration)
            if count:
                out.append({"module": path.relative_to(base).as_posix(),
                            "property": declaration["property"],
                            "values": count,
                            "source": "%s %s" % (declaration["source"],
                                                 declaration["release"]),
                            "licence": declaration["licence"]})
    return out


def findings(rows: list[Disposition]) -> list[str]:
    """What is wrong, as opposed to what is unusual."""
    out = attribution_findings(rows) + research_findings(rows)
    not_publishable = [r for r in rows if not r.redistributable]
    if not_publishable:
        out.append(
            "%d tracked file(s) may not be redistributed but are committed, "
            "and are therefore published wherever this repository is:\n    %s"
            % (len(not_publishable),
               "\n    ".join(r.path for r in not_publishable)))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", default=None, metavar="DISPOSITION")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if anything unpublishable is tracked")
    args = ap.parse_args(argv)

    rows = classify()

    if args.list:
        for row in rows:
            if row.disposition == args.list:
                print("%-18s %s" % (row.licence or "(no rights granted)",
                                    row.path))
        return 0

    print("  %d tracked file(s), each with exactly one disposition"
          % len(rows))
    counts: dict[tuple, int] = {}
    for row in rows:
        key = (row.disposition, row.licence or "(no rights granted)")
        counts[key] = counts.get(key, 0) + 1
    for (disposition, licence), count in sorted(counts.items()):
        print("    %-26s %-14s %4d" % (disposition, licence, count))

    embedded = embedded_text()
    if embedded:
        import third_party

        print()
        print("  third-party text inside modules, as declared in %s:"
              % third_party.DECLARATIONS)
        for row in embedded:
            print("    %-36s %6d value(s) of %s -- from %s, licence as "
                  "declared: %s" % (row["module"], row["values"],
                                    row["property"], row["source"],
                                    row["licence"]))
        print("  " + third_party.STATEMENT)

    problems = findings(rows)
    if problems:
        print()
        for problem in problems:
            print("  FINDING: %s" % problem)
        if any(not row.redistributable for row in rows):
            print()
            print("  Citing a source and shipping it are different acts. A "
                  "README saying the repository does not redistribute "
                  "these is not a licence; the repository's contents are.")
    if args.check:
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
