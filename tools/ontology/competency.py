# SPDX-License-Identifier: MIT
"""Competency questions: what the ontology must be able to answer, checked.

    python tools/ontology/competency.py          # run every answerable question
    python tools/ontology/competency.py --list   # every question and its status

A shape says what must never be true. A competency question says what the
ontology must be able to answer -- "which processes have an organization
as participant?" -- written as SPARQL with the answer it must give. One
YAML file per question in competency-questions/ (format in its README).

WHAT RUNS, AGAINST WHAT

Only `status: answerable`. A `draft` question is written down and not yet
expected to pass; a `deferred` one is out of scope for now. Each
answerable question runs over the authored modules, the vendored
extracts, and the example files it names (examples/, instance data in its
own namespace) -- only those, so one scenario's individuals cannot answer
another's question.

WHAT IS REFUSED, NOT PASSED

  an expectation nothing can fail -- `rows: []`, `includes: []`,
  `count: 0`, `ask: false` -- because a query that matches nothing meets
  it, and "the ontology answers nothing" is not an answer;
  a result with no rows where rows were expected, reported as such;
  a `depends_on` term no pinned upstream describes and no authored module
  declares;
  an example file that does not exist, or lies outside examples/;
  a file whose id is not its filename, or that lacks a field.

Exit codes: 0 every answerable question gives its answer (or there are
none, which is said); 1 anything above.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

QUESTION_ROLE = "competency-question"
EXAMPLE_ROLE = "example-data"
STATUSES = ("draft", "answerable", "deferred")
EXPECTATIONS = ("rows", "includes", "count", "ask")
REQUIRED = ("id", "question", "status", "depends_on", "examples", "query",
            "expect")
ID = re.compile(r"^CQ-\d{3,}$")

W3C = {
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}
DECLARING = {W3C["owl"] + k for k in ("Class", "ObjectProperty",
                                      "DatatypeProperty", "AnnotationProperty",
                                      "NamedIndividual")}


def examples_namespace() -> str:
    """Where example individuals are minted: under the project, apart
    from its terms, so they are never counted as the ontology's."""
    return project.iri_base() + "/examples/"


def prefixes() -> dict[str, str]:
    import yaml

    root = layout.repository_root()
    pins = yaml.safe_load((root / "config/upstream-sources.yaml").read_text(
        encoding="utf-8")) or {}
    out = dict(W3C)
    for entry in pins.get("sources") or []:
        out[entry["prefix"]] = entry["namespace"]
    out[project.prefix()] = project.namespace()
    out["eg"] = examples_namespace()
    return out


def expand(value, known: dict) -> str:
    """An expected value as the string a result is compared with: a full
    IRI for `prefix:local` or `<iri>`, the lexical form otherwise."""
    text = str(value)
    if text.startswith("<") and text.endswith(">"):
        return text[1:-1]
    match = re.match(r"^([A-Za-z][\w\-]*):(\S*)$", text)
    if match and match.group(1) in known:
        return known[match.group(1)] + match.group(2)
    return text


def as_text(term) -> str:
    return str(term)


# --------------------------------------------------------------- reading


def read(path: Path) -> tuple[dict | None, list[str]]:
    import yaml

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as error:  # yaml raises several types
        return None, ["is not YAML: %s" % " ".join(str(error).split())[:200]]
    if not isinstance(raw, dict):
        return None, ["is not a mapping"]
    problems = ["lacks %s" % key for key in REQUIRED if key not in raw]
    if problems:
        return raw, problems
    if not ID.match(str(raw["id"])):
        problems.append("id %r is not CQ-<number>" % raw["id"])
    if raw["id"] != path.stem:
        problems.append("id %s is not its filename %s" % (raw["id"], path.name))
    if raw["status"] not in STATUSES:
        problems.append("status %r is not one of %s"
                        % (raw["status"], ", ".join(STATUSES)))
    if not isinstance(raw["question"], str) or not raw["question"].strip():
        problems.append("question is empty")
    for key in ("depends_on", "examples"):
        if not isinstance(raw[key], list):
            problems.append("%s must be a list (empty if there are none)" % key)
    expect = raw["expect"]
    if not isinstance(expect, dict) or len(expect) != 1 \
            or next(iter(expect)) not in EXPECTATIONS:
        problems.append("expect must be exactly one of %s"
                        % ", ".join(EXPECTATIONS))
    else:
        kind, value = next(iter(expect.items()))
        if kind in ("rows", "includes"):
            if not isinstance(value, list) or not value:
                problems.append(
                    "expect %s is empty. A query that matches nothing meets "
                    "an empty expectation, so it shows nothing; refused"
                    % kind)
            elif not all(isinstance(row, list) and row for row in value):
                problems.append("expect %s must be a list of non-empty rows"
                                % kind)
        elif kind == "count":
            if not isinstance(value, int) or value < 1:
                problems.append("expect count must be a positive number; "
                                "count 0 is met by a query that matches "
                                "nothing, and is refused")
        elif kind == "ask" and value is not True:
            problems.append(
                "expect ask must be true. `ask: false` is met by a query that "
                "matches nothing; a property that must never hold is a shape")
    return raw, problems


def questions(root: Path) -> list[Path]:
    out = []
    for entry in layout.components(QUESTION_ROLE):
        out.extend(entry.members("*.yaml"))
    return out


# ---------------------------------------------------------------- terms


def known_terms(root: Path) -> set[str]:
    """Every term a question may depend on: a pinned upstream's, or one an
    authored module declares."""
    import json

    import rdflib
    import yaml

    pins = yaml.safe_load((root / "config/upstream-sources.yaml").read_text(
        encoding="utf-8")) or {}
    found = set()
    for entry in pins.get("sources") or []:
        path = root / entry["register"]
        if path.is_file():
            found |= set(json.loads(path.read_text(encoding="utf-8"))["terms"])
    graph = rdflib.Graph()
    for path in layout.ontology_files():
        graph.parse(path, format="turtle")
    for subject, kind in graph.subject_objects(rdflib.RDF.type):
        if str(kind) in DECLARING:
            found.add(str(subject))
    return found


# ------------------------------------------------------------- running


def graph_for(example_paths: list[Path]):
    import rdflib

    graph = rdflib.Graph()
    for path in layout.ontology_files() + layout.vendored_files():
        graph.parse(path, format="turtle")
    for path in example_paths:
        graph.parse(path, format="turtle")
    return graph


def answer(record: dict, base: Path, known: dict, terms: set,
           inside: Path | None) -> tuple[str, str]:
    """(verdict, detail) for one well-formed answerable question.
    verdict is pass, fail or refused."""
    missing = [t for t in record["depends_on"]
               if expand(t, known) not in terms]
    if missing:
        return "refused", ("depends on %s, which no pinned upstream "
                           "describes and no module declares" % missing)
    paths = []
    for relative in record["examples"]:
        path = (base / relative).resolve()
        if not path.is_file():
            return "refused", "names example %s, which does not exist" % relative
        if inside is not None:
            try:
                path.relative_to(inside.resolve())
            except ValueError:
                return "refused", ("names example %s, which is outside %s"
                                   % (relative, inside))
        paths.append(path)

    header = "".join("PREFIX %s: <%s>\n" % (p, ns)
                     for p, ns in sorted(known.items()))
    try:
        result = graph_for(paths).query(header + record["query"])
    except Exception as error:  # rdflib raises several types
        return "fail", "the query does not run: %s" % " ".join(
            str(error).split())[:300]

    kind, want = next(iter(record["expect"].items()))
    if kind == "ask":
        if result.type != "ASK":
            return "fail", "expects an ASK answer and the query is a %s" \
                % result.type
        return (("pass", "ask true") if result.askAnswer is True
                else ("fail", "answered false"))
    if result.type != "SELECT":
        return "fail", "expects rows and the query is a %s" % result.type
    rows = {tuple(as_text(v) for v in row) for row in result}
    if not rows:
        return "fail", "returned nothing"
    if kind == "count":
        return (("pass", "%d rows" % len(rows)) if len(rows) == want
                else ("fail", "%d rows, expected %d" % (len(rows), want)))
    expected = {tuple(expand(v, known) for v in row) for row in want}
    if kind == "rows":
        if rows == expected:
            return "pass", "%d rows" % len(rows)
        return "fail", "missing %s; unexpected %s" % (
            sorted(expected - rows)[:4], sorted(rows - expected)[:4])
    missing_rows = expected - rows
    if not missing_rows:
        return "pass", "includes %d expected row(s)" % len(expected)
    return "fail", "missing %s" % sorted(missing_rows)[:4]


def check(paths: list[Path], base: Path | None = None,
          inside: Path | None = None) -> dict:
    """Read and run. `base` resolves example paths; `inside`, when given,
    is where every example must live."""
    root = layout.repository_root()
    base = base or root
    known = prefixes()
    terms = known_terms(root)
    results, seen = [], {}
    for path in sorted(paths):
        record, problems = read(path)
        qid = (record or {}).get("id", path.stem)
        if problems:
            results.append({"id": qid, "file": path.name, "status":
                            (record or {}).get("status"), "verdict": "refused",
                            "detail": "; ".join(problems)})
            continue
        if qid in seen:
            results.append({"id": qid, "file": path.name,
                            "status": record["status"], "verdict": "refused",
                            "detail": "id also used by %s" % seen[qid]})
            continue
        seen[qid] = path.name
        if record["status"] != "answerable":
            results.append({"id": qid, "file": path.name,
                            "status": record["status"], "verdict": "not run",
                            "detail": record["question"]})
            continue
        verdict, detail = answer(record, base, known, terms, inside)
        results.append({"id": qid, "file": path.name,
                        "status": record["status"], "verdict": verdict,
                        "detail": detail, "question": record["question"]})
    failing = [r for r in results if r["verdict"] in ("fail", "refused")]
    return {"results": results,
            "answerable": sum(1 for r in results
                              if r["status"] == "answerable"),
            "failing": failing, "ok": not failing}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)

    root = layout.repository_root()
    inside = None
    for entry in layout.components(EXAMPLE_ROLE):
        inside = entry.resolve()
    record = check(questions(root), root, inside)
    for row in record["results"]:
        if args.list or row["verdict"] != "pass":
            print("  %-8s %-10s %-8s %s" % (row["id"], row["status"] or "?",
                                            row["verdict"], row["detail"]))
    passed = sum(1 for r in record["results"] if r["verdict"] == "pass")
    if not record["results"]:
        print("  no competency questions yet")
    else:
        print("  %d question(s), %d answerable, %d answered as expected"
              % (len(record["results"]), record["answerable"], passed))
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
