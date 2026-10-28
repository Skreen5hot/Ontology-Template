# SPDX-License-Identifier: MIT
"""Verify before assert: every upstream IRI is a real term, every authored one is declared.

    python tools/ontology/iri_lint.py                   # the authored Turtle
    python tools/ontology/iri_lint.py a.ttl b.ttl       # these files, as one corpus
    python tools/ontology/iri_lint.py --output json
    python tools/ontology/iri_lint.py --propose         # register entries for
                                                        # the new findings

Exit codes: 0 no findings but accepted ones; 1 a new finding, or (over
the whole authored scope) an entry that matches nothing; 2 the lint could
not be run -- a file that does not parse, a file that cannot be read, a
register that is missing. A file that cannot be read is never a file with
no findings.

ACCEPTED FINDINGS

A finding a project accepts rather than fixes -- an IRI kept for a
reason, as the Business Process Ontology's port kept one -- is an entry in
config/findings-register.yaml (tools/findings.py), naming the file, the
rule and the term. Without one, an accepted finding kept the Checks job
red for good, and every step after this one stopped running. Line numbers
are not part of the identity: an edit above a finding moves it, and does
not make it a different finding.

THE RULES

  readable_label      an upstream IRI whose local name is a readable name
                      (cco:Organization) where the upstream mints opaque
                      ids. Parses, names nothing. The suggestion is the id
                      whose label matches -- in the same upstream, or in
                      another (cco:Process -> obo:BFO_0000015).
  case_mismatch       an id-shaped local name in the wrong case
                      (cco:ONT00001180). Suggests the real one.
  unverified          an id-shaped upstream IRI no pinned file describes
                      (cco:ont99999999): a typo, a term from another
                      release, or one written from memory.
  deprecated_upstream an upstream term its own release marks deprecated.
  redeclared_upstream an authored file typing an upstream term
                      (cco:ont00001180 a owl:Class). The term is CCO's;
                      declaring it here makes this file a second, divergent
                      source for it.
  annotated_upstream  an authored file saying anything else about one --
                      a comment, a label, a parent. Same reason.
  naming_convention   an authored term whose local name breaks the
                      convention config/naming.yaml sets for its kind
                      (UpperCamelCase classes, lowerCamelCase properties).
  dangling_ref        an IRI in this project's namespace that nothing in the
                      linted files declares -- in any position, including a
                      restriction filler.

WHERE IT CAME FROM, AND WHAT IS DIFFERENT

The rules are IRI_Linter's (https://github.com/Skreen5hot/IRI_Linter, MIT,
the same author), and so are most of the test cases, rewritten. The code
is not: assessed 2026-10-23 against BFO/CCO projects, IRI_Linter

  - treated every declared namespace that was neither CCO nor a W3C
    vocabulary as project-minted, so `rdfs:subClassOf obo:BFO_0000040`
    was a dangling reference -- in a realist ontology, every class;
  - skipped a file it could not parse and reported it clean, exit 0;
  - checked against a hand-kept register built from a 2026-04-04 CCO, so
    114 terms of the CCO v2.0 this template pins were "unverified" and
    34 it accepted do not exist in v2.0;
  - reported the first line an IRI appears on, for every occurrence.

Here the upstream namespaces and their terms come from the pins and the
registers the vendoring tool generates from the same pinned bytes the
extracts come from; the project namespace comes from config/project.yaml;
a parse failure exits 2; and every occurrence is reported on its own line.
Each of those four is a test.

WHAT A "TERM" IS

An upstream IRI is checked against its source's register, which lists
every term the pinned files describe -- not only the vendored ones. An
IRI in no pinned namespace and not in the project's (a licence URL, a
dcterms:source) is not a term reference and is not checked.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import findings  # noqa: E402
import layout  # noqa: E402
import project  # noqa: E402

CHECK = "iri_lint"

FORMAT_VERSION = "1.0"
GENERATOR = "tools/ontology/iri_lint.py"
PINS = "config/upstream-sources.yaml"

RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"

#: Types whose subject is thereby declared.
DECLARING = {OWL + "Class", OWL + "ObjectProperty", OWL + "DatatypeProperty",
             OWL + "AnnotationProperty", OWL + "NamedIndividual",
             "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property",
             SKOS + "Concept", SKOS + "ConceptScheme"}

#: The roles linted when no file is named: what this project authors,
#: example instance data included -- an example individual typed with a
#: class nothing declares is a dangling reference like any other. Not the
#: fixtures, which are invalid on purpose.
SCOPE_ROLES = ("ontology-module", "ontology-module-set",
               "ontology-validation", "example-data")

RULES = ("readable_label", "case_mismatch", "unverified",
         "deprecated_upstream", "redeclared_upstream", "annotated_upstream",
         "dangling_ref", "naming_convention")

#: A source is "opaque" -- mints ids, not names -- when this share of its
#: register's local names contains a run of four or more digits. BFO and
#: CCO are both 1.0. A source with readable IRIs gets `unverified` for an
#: unknown term, never `readable_label`, because there a readable name is
#: the convention rather than the mistake.
OPAQUE_SHARE = 0.9


class Unrunnable(Exception):
    """The lint cannot be run. Exit 2, naming the cause."""


# --------------------------------------------------------- upstream


class Upstream:
    """One pinned source, as its register describes it."""

    def __init__(self, entry: dict, register: dict):
        self.id = entry["id"]
        self.prefix = entry["prefix"]
        self.namespace = entry["namespace"]
        self.terms = register["terms"]
        locals_ = [iri[len(self.namespace):] for iri in self.terms]
        digits = sum(bool(re.search(r"\d{4,}", name)) for name in locals_)
        self.opaque = bool(locals_) and digits / len(locals_) >= OPAQUE_SHARE
        self.shapes = {shape_of(name) for name in locals_}
        self.by_lower = {}
        for name in locals_:
            self.by_lower.setdefault(name.lower(), []).append(name)
        self.by_label: dict[str, list[str]] = {}
        for iri, record in self.terms.items():
            for label in record["labels"]:
                key = normalized(label["value"])
                if iri not in self.by_label.setdefault(key, []):
                    self.by_label[key].append(iri)

    def local(self, iri: str) -> str:
        return iri[len(self.namespace):]


def shape_of(name: str) -> str:
    return re.sub(r"\d", "9", name)


def normalized(text: str) -> str:
    """A name or a label, compared without case, separators or camelCase.

    `has_output`, `has-output`, `hasOutput` and the label "has output"
    all come to "has output".
    """
    text = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ",
                  text)
    return " ".join(re.sub(r"[_\-]", " ", text).lower().split())


def upstreams(root: Path | None = None) -> list[Upstream]:
    import yaml

    root = root or layout.repository_root()
    raw = yaml.safe_load((root / PINS).read_text(encoding="utf-8")) or {}
    found = []
    for entry in raw.get("sources") or []:
        path = root / entry["register"]
        if not path.is_file():
            raise Unrunnable(
                "%s is missing, so %s terms cannot be checked. Run python "
                "tools/ontology/vendor_upstream.py --rebuild"
                % (entry["register"], entry["id"]))
        found.append(Upstream(entry, json.loads(
            path.read_text(encoding="utf-8"))))
    if not found:
        raise Unrunnable(PINS + " pins no upstream")
    return found


# ------------------------------------------------------- the files


def code_only(text: str) -> str:
    """The Turtle with comments and string literals blanked out.

    Newlines are kept, so a position here is a line there. Triple-quoted
    literals span lines and are handled as such; IRI_Linter blanked
    strings one line at a time, so an IRI on the second line of a long
    definition was a reference.
    """
    out, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "<":
            end = text.find(">", i)
            if end != -1 and "\n" not in text[i:end]:
                out.append(text[i:end + 1])
                i = end + 1
                continue
        if ch in "\"'":
            quote = text[i:i + 3] if text[i:i + 3] in ('"""', "'''") else ch
            j = i + len(quote)
            while j < n and not text.startswith(quote, j):
                j += 2 if text[j] == "\\" else 1
            j = min(n, j + len(quote))
            out.append("".join(c if c == "\n" else " " for c in text[i:j]))
            i = j
            continue
        if ch == "#":
            end = text.find("\n", i)
            end = n if end == -1 else end
            out.append(" " * (end - i))
            i = end
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def prefixes_in(text: str) -> dict[str, str]:
    found = {}
    for match in re.finditer(r"(?im)^\s*(?:@prefix|prefix)\s+([A-Za-z][\w\-]*|)"
                             r"\s*:\s*<([^>]*)>", text):
        found[match.group(1)] = match.group(2)
    return found


def spelled(prefixes: dict, iri: str) -> str:
    """A regex matching the IRI written in full or as a prefixed name."""
    spellings = [re.escape("<%s>" % iri)]
    for prefix, namespace in prefixes.items():
        if iri.startswith(namespace) and len(iri) > len(namespace):
            spellings.append(
                r"(?<![\w:\-])" + re.escape(prefix + ":" + iri[len(namespace):])
                + r"(?![\w\-])")
    return "(?:%s)" % "|".join(spellings)


def lines_of(code: str, prefixes: dict, iri: str,
             followed_by: str = "") -> list[int]:
    """Every line the IRI is written on, as a full IRI or a prefixed name
    -- or, with `followed_by`, only where that comes next.

    Prefix declarations are not occurrences.
    """
    pattern = re.compile(spelled(prefixes, iri) + followed_by)
    found = []
    for number, line in enumerate(code.split("\n"), 1):
        if re.match(r"(?i)\s*(@prefix|prefix|@base|base)\b", line):
            continue
        if pattern.search(line):
            found.append(number)
    return found


def load(paths: list[Path]):
    """{path: (graph, text)}. Unreadable or unparseable is Unrunnable."""
    import rdflib

    loaded = {}
    for path in paths:
        try:
            text = path.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise Unrunnable("%s cannot be read: %s" % (path, error))
        graph = rdflib.Graph()
        try:
            graph.parse(data=text, format="turtle")
        except Exception as error:  # rdflib raises several types
            detail = " ".join(str(error).split())[:300]
            raise Unrunnable("%s does not parse as Turtle: %s"
                             % (path, detail))
        loaded[path] = (graph, text)
    return loaded


# ---------------------------------------------------------- the lint


def judge(iri: str, sources: list[Upstream]) -> tuple[str, list[str]] | None:
    """(rule, suggestions) for an upstream IRI, or None if it is fine."""
    source = next(s for s in sources if iri.startswith(s.namespace))
    if iri in source.terms:
        if source.terms[iri]["deprecated"]:
            return "deprecated_upstream", []
        return None
    name = source.local(iri)
    if not source.opaque:
        return "unverified", suggestions(name, sources, source)
    if name.lower() in source.by_lower:
        return "case_mismatch", [source.namespace + real
                                 for real in source.by_lower[name.lower()]]
    if shape_of(name) in source.shapes:
        return "unverified", []
    return "readable_label", suggestions(name, sources, source)


def suggestions(name: str, sources: list[Upstream], first: Upstream) -> list:
    """Terms whose label is this name: the IRI's own source first, then
    the others. More than one is returned as candidates, not a choice."""
    key = normalized(name)
    ordered = [first] + [s for s in sources if s is not first]
    for source in ordered:
        if key in source.by_label:
            return sorted(source.by_label[key])
    return []


def lint(paths: list[Path], root: Path | None = None) -> list[dict]:
    import rdflib

    sources = upstreams(root)
    upstream_ns = tuple(s.namespace for s in sources)
    authored_ns = project.namespace()
    loaded = load(paths)

    declared = set()
    for graph, _text in loaded.values():
        for subject, _p, kind in graph.triples(
                (None, rdflib.URIRef(RDF_TYPE), None)):
            if (isinstance(subject, rdflib.URIRef)
                    and str(kind) in DECLARING
                    and str(subject).startswith(authored_ns)):
                declared.add(str(subject))

    findings = []
    for path, (graph, text) in loaded.items():
        code = code_only(text)
        prefixes = prefixes_in(text)
        judged = {}
        for triple in graph:
            for term in triple:
                if not isinstance(term, rdflib.URIRef):
                    continue
                iri = str(term)
                if iri in judged:
                    continue
                if iri.startswith(upstream_ns):
                    judged[iri] = judge(iri, sources)
                elif iri.startswith(authored_ns) and iri != authored_ns:
                    judged[iri] = (None if iri in declared
                                   else ("dangling_ref", []))
        findings.extend(redeclarations(path, graph, code, prefixes,
                                       upstream_ns, judged))
        findings.extend(naming(path, graph, code, prefixes, authored_ns,
                               conventions(root)))

        for iri, verdict in judged.items():
            if verdict is None:
                continue
            rule, suggested = verdict
            for line in lines_of(code, prefixes, iri) or [0]:
                record = {"file": path.as_posix(), "line": line,
                          "type": rule, "subject": iri}
                if len(suggested) == 1:
                    record["suggestion"] = suggested[0]
                elif suggested:
                    record["candidates"] = suggested
                findings.append(record)
    findings.sort(key=lambda r: (r["file"], r["line"], r["type"],
                                 r["subject"]))
    return findings


#: The kinds config/naming.yaml names, and the types that make a term one.
NAMING_KINDS = {
    "classes": {OWL + "Class"},
    "properties": {OWL + "ObjectProperty", OWL + "DatatypeProperty",
                   OWL + "AnnotationProperty"},
    "concepts": {SKOS + "Concept", SKOS + "ConceptScheme"},
    "individuals": {OWL + "NamedIndividual"},
}


def conventions(root: Path | None = None) -> dict:
    """{kind: compiled pattern} from config/naming.yaml; a kind set to
    null is not checked, and a project without the file checks nothing."""
    import yaml

    path = (root or layout.repository_root()) / "config/naming.yaml"
    if not path.is_file():
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {kind: re.compile(raw[kind]) for kind in NAMING_KINDS
            if raw.get(kind)}


def naming(path, graph, code, prefixes, authored_ns, patterns) -> list:
    """An authored term whose local name breaks the convention for its
    kind, reported where it is declared."""
    import rdflib

    out = []
    for kind, pattern in sorted(patterns.items()):
        types = NAMING_KINDS[kind]
        for subject, kind_iri in graph.subject_objects(
                rdflib.URIRef(RDF_TYPE)):
            iri = str(subject)
            if (not isinstance(subject, rdflib.URIRef)
                    or str(kind_iri) not in types
                    or not iri.startswith(authored_ns)):
                continue
            if pattern.match(iri[len(authored_ns):]):
                continue
            lines = lines_of(code, prefixes, iri,
                             r"\s+(?:a|rdf:type|<%s>)(?=\s)"
                             % re.escape(RDF_TYPE)) or [0]
            for line in lines:
                record = {"file": path.as_posix(), "line": line,
                          "type": "naming_convention", "subject": iri,
                          "convention": "%s %s" % (kind, pattern.pattern)}
                if record not in out:
                    out.append(record)
    return out


def redeclarations(path, graph, code, prefixes, upstream_ns, judged) -> list:
    """An authored file typing a real upstream term, reported where the
    typing is written -- not at every later reference to the term, which
    is a legitimate use of it. The first version reported every
    occurrence, and the dirty fixture's own positive control caught it.

    The line is the one where the IRI is followed by `a` or `rdf:type`;
    a declaration whose subject and `a` sit on different lines falls back
    to the lines where the IRI begins the line.
    """
    import rdflib

    out = []
    for subject, _p, kind in graph.triples(
            (None, rdflib.URIRef(RDF_TYPE), None)):
        iri = str(subject)
        if not (isinstance(subject, rdflib.URIRef)
                and iri.startswith(upstream_ns)
                and str(kind) in DECLARING
                and judged.get(iri) is None):
            continue
        rows = code.split("\n")
        typed = lines_of(code, prefixes, iri,
                         r"\s+(?:a|rdf:type|<%s>)(?=\s)" % re.escape(RDF_TYPE))
        leading = [n for n in lines_of(code, prefixes, iri)
                   if re.match(spelled(prefixes, iri), rows[n - 1])]
        for line in sorted(set(typed or leading)) or [0]:
            record = {"file": path.as_posix(), "line": line,
                      "type": "redeclared_upstream", "subject": iri}
            if record not in out:
                out.append(record)

    # Anything else said about an upstream term: a comment, a label, a
    # subClassOf. Phase 4's plan had this as a shape; a shape cannot see
    # which file a triple came from, because the validation graph merges
    # the authored modules with the extracts, so it is checked here, where
    # each file is its own graph. A term already reported as redeclared is
    # not reported again for the triples of the same declaration.
    redeclared = {r["subject"] for r in out}
    rows = code.split("\n")
    for subject in sorted({s for s in graph.subjects()
                           if isinstance(s, rdflib.URIRef)}, key=str):
        iri = str(subject)
        if (not iri.startswith(upstream_ns) or iri in redeclared
                or judged.get(iri) is not None):
            continue
        leading = [n for n in lines_of(code, prefixes, iri)
                   if re.match(r"\s*" + spelled(prefixes, iri), rows[n - 1])]
        for line in leading or [0]:
            out.append({"file": path.as_posix(), "line": line,
                        "type": "annotated_upstream", "subject": iri})
    return out


def default_paths(root: Path | None = None) -> list[Path]:
    paths = []
    for role in SCOPE_ROLES:
        for entry in layout.components(role):
            paths.extend(entry.members("*.ttl"))
    if not paths:
        raise Unrunnable("no authored Turtle is declared, so there is "
                         "nothing to lint and a clean result would mean "
                         "nothing")
    return paths


# ----------------------------------------------------------- report


def prefixed(iri: str, sources: list[Upstream]) -> str:
    for source in sources:
        if iri.startswith(source.namespace):
            return "%s:%s" % (source.prefix, source.local(iri))
    if iri.startswith(project.namespace()):
        return "%s:%s" % (project.prefix(), iri[len(project.namespace()):])
    return "<%s>" % iri


def text_of(findings: list[dict], sources: list[Upstream], root: Path) -> str:
    rows = []
    for record in findings:
        name = record["file"]
        try:
            name = Path(name).resolve().relative_to(root).as_posix()
        except ValueError:
            pass
        row = "%s:%d %s %s" % (name, record["line"], record["type"],
                               prefixed(record["subject"], sources))
        if "suggestion" in record:
            row += " -> " + prefixed(record["suggestion"], sources)
        elif "candidates" in record:
            row += " -> one of " + ", ".join(
                prefixed(c, sources) for c in record["candidates"])
        rows.append(row)
    return "\n".join(rows)


def json_of(findings: list[dict], paths: list[Path], error: str | None):
    by_type: dict[str, int] = {}
    for record in findings:
        by_type[record["type"]] = by_type.get(record["type"], 0) + 1
    return {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "metadata": {"input": {"files": [p.as_posix() for p in paths]}},
        "statistics": {"total_violations": len(findings),
                       "by_type": dict(sorted(by_type.items()))},
        "violations": findings,
        "error": error,
    }


def register_findings(records: list[dict], root: Path) -> list[dict]:
    """Each lint record as the register identifies it: the file relative
    to the repository, the rule, the term. No line, no suggestion."""
    out = []
    for record in records:
        name = record["file"]
        try:
            name = Path(name).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            pass
        out.append(dict(findings.finding(
            CHECK, name, record["subject"], record["type"],
            "%s %s" % (record["type"], record["subject"]), "Violation"),
            record=record))
    return out


def verdict_of(records: list[dict], root: Path, complete: bool) -> dict:
    return findings.judge(CHECK, register_findings(records, root),
                          findings.load(root), complete=complete)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--output", choices=("text", "json"), default="text")
    ap.add_argument("--propose", action="store_true",
                    help="print register entries for the new findings")
    ap.add_argument("--reason", help="with --propose: the reason to write")
    ap.add_argument("--owner", help="with --propose: the owner to write")
    ap.add_argument("--review", help="with --propose: the review date")
    args = ap.parse_args(argv)

    root = layout.repository_root()
    paths = [Path(f) for f in args.files]
    # Stale entries can only be judged over the whole scope: run on one
    # file, an entry for another matches nothing and is not stale.
    complete = not paths
    try:
        paths = paths or default_paths(root)
        sources = upstreams(root)
        records = lint(paths, root)
        verdict = verdict_of(records, root, complete)
    except Unrunnable as error:
        if args.output == "json":
            print(json.dumps(json_of([], paths, str(error)), indent=2))
        print("  CANNOT LINT: %s" % error, file=sys.stderr)
        return 2

    if args.propose:
        print(findings.propose(verdict["new"], args.reason, args.owner,
                               args.review)
              or "# no new findings: nothing to propose")
        return 0
    new = [f["record"] for f in verdict["new"]]
    if args.output == "json":
        out = json_of(records, paths, None)
        accepted = {id(f["record"]) for f in verdict["accepted"]}
        for record in out["violations"]:
            record["accepted"] = id(record) in accepted
        out["register"] = {key: len(verdict[key]) for key in
                           ("accepted", "new", "stale", "expired")}
        print(json.dumps(out, indent=2))
    else:
        if new:
            print(text_of(new, sources, root))
        print("  %d file(s), %d finding(s), %d accepted by the register"
              % (len(paths), len(records), len(verdict["accepted"])),
              file=sys.stderr)
        if verdict["stale"] or verdict["expired"]:
            findings.report(CHECK, dict(verdict, new=[]), out=sys.stderr)
    return 0 if verdict["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
