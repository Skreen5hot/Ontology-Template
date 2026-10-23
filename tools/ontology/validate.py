# SPDX-License-Identifier: MIT
"""Run the SHACL shapes, and check that they can still fail.

    python tools/ontology/validate.py            # report
    python tools/ontology/validate.py --gate     # exit 1 unless reality
                                                 # matches the baseline
    python tools/ontology/validate.py --record   # rewrite the baseline

Two rungs, and the second is the one that makes the first mean anything.

  conformance   the authored ontology validated against every shape set.
                Violations are findings.

  falsification the bad-examples fixture validated against the same
                shapes. It is built to break them, so violations here are
                the expected result and their *absence* is the finding.

A shape set that reports no violations is ambiguous on its own: the data
might be clean, or the constraint might be selecting nothing. That
happens more easily than it sounds -- a SPARQL constraint filtering on a
namespace prefix string still runs when the string is stale, matches
nothing, and reports success. This repository moved namespaces recently
and had exactly that construct in it, which is why the second rung is
not optional.

SCOPE

The data graph is the authored ontology *plus* the vendored upstream
extracts. Both are needed: a shape asking whether a class reaches
cco:ont00001379 through subClassOf has nothing to walk without CCO, and
answers "no" for every subject. That report is indistinguishable from a
real defect, and in the Application Requirement Ontology, where this
tool was written, it produced exactly that -- 202 violations that were a
property of the scope.

Loading the extracts creates the opposite risk, so violations are split
by whose term the focus node is. A violation against an upstream IRI is a
finding about the extract; only violations against terms this repository
authored are findings about this ontology.

The fixtures are validated with the extracts in scope too. A realist
shape asks whether a class reaches a BFO category, or sits under two
disjoint ones; a fixture loaded alone has no BFO to reach, and every case
would fail for the wrong reason -- the positive controls included.

SEVERITY

A result of severity sh:Warning or sh:Info is reported, and is not a
finding the gate counts. A warning that blocks a commit is a violation
with a softer name; the realist library uses warnings for what a
reviewer should look at (two asserted parents, a definition that does
not name its genus) and violations for what is wrong.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

FORMAT_VERSION = 1
GENERATOR = "tools/ontology/validate.py"
BASELINE = "config/validation-baseline.json"


def load(paths) -> "rdflib.Graph":
    import rdflib

    graph = rdflib.Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def shape_sets() -> dict[str, Path]:
    return {c.id: c.resolve()
            for c in layout.components("ontology-validation")}


def fixtures() -> list[Path]:
    """Every deliberately-invalid graph the contract declares.

    This was one component id written into `measure`. That was fine while
    there was one fixture and quietly wrong the moment a second shape set
    needed its own: the new cases had to be appended to a file named for
    a corpus they had nothing to do with, or go unexercised. Asking the
    contract mirrors how `shape_sets` already works.
    """
    out: list[Path] = []
    for entry in layout.components("test-fixture"):
        out.extend(entry.members("*.ttl"))
    return out


def stable_shape(source, message) -> str:
    import rdflib

    if not isinstance(source, rdflib.BNode):
        return str(source)
    digest = hashlib.sha256(str(message or "").encode("utf-8")).hexdigest()
    return "_:constraint-" + digest[:12]


def run(data, shapes) -> dict:
    from pyshacl import validate as shacl

    conforms, results_graph, results_text = shacl(
        data_graph=data, shacl_graph=shapes, inference="none",
        abort_on_first=False, meta_shacl=False, advanced=True,
        allow_warnings=True, debug=False)

    import rdflib

    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    violations = []
    for result in results_graph.subjects(rdflib.RDF.type, SH.ValidationResult):
        focus = results_graph.value(result, SH.focusNode)
        source = results_graph.value(result, SH.sourceShape)
        message = results_graph.value(result, SH.resultMessage)
        severity = results_graph.value(result, SH.resultSeverity)
        violations.append({
            "focus": str(focus) if focus else None,
            # Named shapes keep their IRI. An inline constraint is a
            # blank node, and rdflib renames blank nodes on every parse,
            # so using its label here would give the report an identifier
            # that changes when nothing has. The message is what
            # identifies the constraint, so the digest is taken of that.
            "shape": (stable_shape(source, message) if source else None),
            "severity": str(severity).rsplit("#", 1)[-1] if severity else None,
            # 600, not the 200 this was: a message with two or three full
            # IRIs substituted in ran past 200 before the words saying
            # which constraint it was, and the realist test could not find
            # the range check in its own report.
            "message": (str(message)[:600] if message else None),
        })
    violations.sort(key=lambda v: (v["shape"] or "", v["focus"] or ""))
    return {"conforms": bool(conforms), "violations": violations,
            "text": results_text[:4000]}


PINS = "config/upstream-sources.yaml"

#: The namespace this repository mints terms in, read from
#: config/project.yaml. It is also the string the wellformedness shapes
#: filter on, written there by tools/init_project.py, and
#: tests/test_namespace.py requires the two to agree -- a SPARQL filter on
#: a stale namespace string selects nothing and reports success.
AUTHORED_NAMESPACE = project.namespace()


def _upstream() -> dict:
    """Namespaces the corpus builds on but does not contain.

    Read from the pins. ARO wrote this as a two-entry dict, which was
    right while CCO and BFO were the only upstreams; the BCO added a
    third on day one, and a hand-kept copy would have classified every
    violation against the third as one against an authored term. A constraint that walks
    subClassOf+ into any of these cannot be evaluated without it, and
    will report every subject as violating.
    """
    import yaml

    path = layout.repository_root() / PINS
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    found = {entry["namespace"]: entry["id"].upper()
             for entry in raw.get("sources") or []}
    if not found:
        raise SystemExit(
            PINS + " declares no upstream, so every violation would be "
            "attributed to this repository whoever's term it is against")
    if AUTHORED_NAMESPACE in found:
        raise SystemExit(
            "%s is pinned as an upstream namespace and is also the one this "
            "repository authors in; the two cannot be told apart"
            % AUTHORED_NAMESPACE)
    return found


UPSTREAM = _upstream()


def unresolved_vocabularies(data) -> dict:
    """Upstream terms referenced but not described in scope.

    This is the difference between "the ontology is wrong" and "the
    question was asked without the vocabulary needed to answer it". A
    shape requiring a class to reach a CCO anchor via subClassOf+ has no
    chain to walk when CCO is absent, so it reports every subject as
    violating -- and the report looks exactly like a real defect.
    """
    import rdflib

    out = {}
    for prefix, name in UPSTREAM.items():
        referenced = {str(t) for triple in data for t in triple
                      if isinstance(t, rdflib.URIRef)
                      and str(t).startswith(prefix)}
        described = {iri for iri in referenced
                     if list(data.predicate_objects(rdflib.URIRef(iri)))}
        out[name] = {
            "prefix": prefix,
            "referenced": len(referenced),
            "described_in_scope": len(described),
            "resolvable": len(referenced) == len(described),
        }
    return out


def shapes_depend_on(path: Path) -> list[str]:
    """Which upstream vocabularies a shape set reasons over.

    Read from the shapes' own text, including the SPARQL inside them,
    because a constraint naming a CCO class in a query depends on CCO
    just as much as one naming it as an IRI.
    """
    text = path.read_text(encoding="utf-8")
    return sorted(name for prefix, name in UPSTREAM.items()
                  if prefix in text)


def vendoring() -> dict:
    """What the vendored extracts contain, and what they left behind.

    Carried into this report rather than left in a separate file, because
    the reader who needs it is the one reading a green result. "Every
    referenced term is described" is true of a partial extract and does
    not mean the upstream is present; the dropped-axiom counts are the
    difference, and they belong next to the conclusion they qualify.
    """
    path = layout.repository_root() / "config/upstream-extracts.json"
    if not path.is_file():
        return {"available": False}
    record = json.loads(path.read_text(encoding="utf-8"))
    return {
        "available": True,
        "partial_extracts": True,
        "sources": {key: {"release": entry["release"],
                          "commit": entry["commit"],
                          "licence": entry["licence_spdx"],
                          "terms": entry["terms_described_in_full"],
                          "stubs": entry["terms_declared_as_stubs"],
                          "axioms_dropped": entry[
                              "axioms_dropped_anonymous_object"]}
                    for key, entry in record["extracts"].items()},
        "not_covered": record["not_covered"],
    }


def authored_namespace() -> str:
    return AUTHORED_NAMESPACE


def passed_of(rungs: dict) -> bool:
    """Whether the ladder passed, as a function of the rungs alone.

    Lifted out of `measure` so the empty case can be tested. `all()` over
    an empty sequence is True, and the first version of this tool
    reported success having evaluated no rung at all -- a check that
    certified the ontology while doing nothing. That branch cannot be
    reached from this repository any more, which is exactly why it needs
    a test that does not depend on reaching it.
    """
    return (any(r["evaluable"] for r in rungs.values())
            and all(r["corpus"]["conforms"] and r["can_still_fail"]
                    for r in rungs.values() if r["evaluable"]))


def partition(results: list) -> tuple[list, list, list]:
    """(authored violations, authored warnings, against vendored terms).

    A result whose focus node is an upstream term is a finding about the
    vendored extract, not about this ontology; counting the two together
    would let a defect in the extract be reported as a defect in the
    corpus, and the reverse. Of the rest, only sh:Violation is a finding
    the gate counts. Lifted out of `measure` so the split can be tested on
    a real report rather than only on a constructed record.
    """
    upstream = [v for v in results
                if v["focus"] and v["focus"].startswith(tuple(UPSTREAM))]
    authored = [v for v in results if v not in upstream]
    return ([v for v in authored if v["severity"] == "Violation"],
            [v for v in authored if v["severity"] != "Violation"],
            upstream)


def measure() -> dict:
    root = layout.repository_root()
    scope = layout.ontology_files()
    vendored = layout.vendored_files()
    fixture_paths = fixtures()
    sets = shape_sets()
    if not sets:
        raise SystemExit("no ontology-validation component is declared")
    if not fixture_paths:
        raise SystemExit(
            "no test-fixture component is declared, so every shape set "
            "below would report a green result with nothing behind it")

    data = load(list(scope) + list(vendored))
    bad = load(list(fixture_paths) + list(vendored))
    vocabularies = unresolved_vocabularies(data)
    missing = sorted(name for name, info in vocabularies.items()
                     if not info["resolvable"])

    rungs = {}
    for name, path in sorted(sets.items()):
        shapes = load([path])
        depends = shapes_depend_on(path)
        blocked = sorted(set(depends) & set(missing))
        corpus = run(data, shapes)
        against_fixture = run(bad, shapes)
        authored_focus, authored_warnings, upstream_focus = partition(
            corpus["violations"])
        rungs[name] = {
            "shapes": path.relative_to(root).as_posix(),
            "depends_on": depends,
            "blocked_by_missing_vocabulary": blocked,
            # Violations from a shape set that cannot resolve the
            # vocabulary it reasons over are not findings about the
            # ontology, and counting them as such would be a measurement
            # of the harness.
            "evaluable": not blocked,
            "corpus": {
                "conforms": corpus["conforms"],
                "violations": len(corpus["violations"]),
                "against_authored_terms": len(authored_focus),
                "warnings_against_authored_terms": len(authored_warnings),
                "against_vendored_terms": len(upstream_focus),
                "detail": authored_focus[:20],
                "warning_detail": authored_warnings[:20],
                "vendored_detail": upstream_focus[:10],
            },
            "fixture": {
                "conforms": against_fixture["conforms"],
                "violations": len(against_fixture["violations"]),
                # Not truncated as tightly as the corpus detail above.
                # This list is the evidence that each constraint fires,
                # and a cap short enough to hide one of them would make
                # the falsification report a subset of itself.
                "detail": against_fixture["violations"][:300],
            },
            # No result against the fixture means the shapes did not fire
            # on data built to break them, which is a broken check
            # reporting success. Counted as results rather than read from
            # `conforms`, which allow_warnings makes true for a set whose
            # fixture raises only warnings.
            "can_still_fail": len(against_fixture["violations"]) > 0,
            "fixture_exercises_these_shapes":
                len(against_fixture["violations"]) > 0,
        }

    return {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "scope": {
            "data_files": len(scope),
            "vendored_files": [p.relative_to(root).as_posix()
                               for p in vendored],
            "fixtures": [p.relative_to(root).as_posix()
                         for p in fixture_paths],
            "shape_sets": sorted(sets),
        },
        "vendoring": vendoring(),
        "upstream_vocabularies": vocabularies,
        "unresolved": missing,
        "rungs": rungs,
        "note": (
            "A shape set reporting no violations is ambiguous by itself: "
            "clean data and a constraint selecting nothing look the same. "
            "can_still_fail is that ambiguity resolved -- the same shapes "
            "run against data built to break them."),
        # Only evaluable rungs can pass or fail. A rung blocked on a
        # missing vocabulary is neither, and saying so is the whole
        # point -- its violation count describes the scope, not the
        # ontology.
        "evaluable_rungs": sorted(n for n, r in rungs.items()
                                  if r["evaluable"]),
        "blocked_rungs": sorted(n for n, r in rungs.items()
                                if not r["evaluable"]),
        "passed": passed_of(rungs),
    }


# ---------------------------------------------------------- baseline


def baseline() -> dict:
    """What this repository currently owes, per rung.

    Kept as an artifact rather than as numbers inside test assertions,
    for one reason: a team taking this over needs to see the debt without
    reading test code, and needs it to be a thing that visibly shrinks.
    """
    path = layout.repository_root() / BASELINE
    if not path.is_file():
        raise SystemExit(
            BASELINE + " is missing. It records the findings this "
            "repository is known to carry; without it the gate below "
            "would have nothing to compare against and would pass.")
    return json.loads(path.read_text(encoding="utf-8"))


def compare(record: dict, recorded: dict) -> list[str]:
    """Every way the ladder and the baseline can disagree.

    The rule is one sentence: the baseline must describe reality. More
    findings than recorded is a regression. Fewer is debt paid and has to
    be re-recorded in the same commit, so that it shows up in a diff
    rather than as a number quietly drifting away from the file.
    """
    problems = []
    rungs = record["rungs"]
    want = recorded.get("rungs") or {}

    for name in sorted(set(rungs) | set(want)):
        if name not in want:
            problems.append(
                "%s has no entry in %s. A new shape set is recorded "
                "deliberately, not adopted silently." % (name, BASELINE))
            continue
        if name not in rungs:
            problems.append(
                "%s is recorded in %s and no longer exists. A baseline "
                "describing a rung that is gone is coverage for nothing."
                % (name, BASELINE))
            continue

        rung = rungs[name]
        if not rung["evaluable"]:
            problems.append(
                "%s cannot be evaluated -- it reasons over %s, which is "
                "not in scope. Its violation count describes the scope, "
                "not the ontology."
                % (name, ", ".join(rung["blocked_by_missing_vocabulary"])))
            continue
        if not rung["can_still_fail"]:
            problems.append(
                "%s did not fire on the fixture built to break it, so its "
                "result against the corpus cannot be distinguished from a "
                "constraint that selects nothing." % name)

        vendored = rung["corpus"]["against_vendored_terms"]
        if vendored:
            problems.append(
                "%s reports %d violation(s) against vendored upstream "
                "terms, which are findings about the extract."
                % (name, vendored))

        got = rung["corpus"]["against_authored_terms"]
        allowed = want[name].get("authored_findings")
        if allowed is None:
            problems.append("%s: %s records no authored_findings"
                            % (name, BASELINE))
        elif got > allowed:
            problems.append(
                "%s: %d finding(s) against authored terms, and %s records "
                "%d. That is %d new %s."
                % (name, got, BASELINE, allowed, got - allowed,
                   "finding" if got - allowed == 1 else "findings"))
        elif got < allowed:
            problems.append(
                "%s: %d finding(s) against authored terms, and %s records "
                "%d. %d have been fixed -- re-record the baseline in this "
                "commit so the reduction is visible: python %s --record"
                % (name, got, BASELINE, allowed, allowed - got, GENERATOR))
    return problems


def as_baseline(record: dict, reasons: dict) -> dict:
    return {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "note": (
            "Findings this repository is known to carry. The gate requires "
            "reality to match: more is a regression, fewer means re-record "
            "so the reduction appears in a diff. These are defects in the "
            "ontology, not in the tools."),
        "rungs": {
            name: dict({"authored_findings":
                        rung["corpus"]["against_authored_terms"]},
                       **({"why": reasons[name]} if name in reasons else {}))
            for name, rung in sorted(record["rungs"].items())},
    }


def record_baseline(record: dict, accept: str | None) -> int:
    """Rewrite the baseline, refusing to raise a count without a reason.

    Without that refusal a regression certifies itself on the one run
    that introduces it, and the file becomes a transcript of whatever
    happened rather than a commitment.
    """
    root = layout.repository_root()
    path = root / BASELINE
    existing = (json.loads(path.read_text(encoding="utf-8")).get("rungs") or {}
                if path.is_file() else {})

    raised = []
    for name, rung in sorted(record["rungs"].items()):
        was = (existing.get(name) or {}).get("authored_findings")
        now = rung["corpus"]["against_authored_terms"]
        if was is not None and now > was:
            raised.append("%s %d -> %d" % (name, was, now))

    if raised and not accept:
        print("  REFUSED: this would raise %d rung(s): %s"
              % (len(raised), "; ".join(raised)))
        print("  Recording a higher number is accepting a regression. If "
              "that is the intent, say so:")
        print("    python %s --record --accept-regression \"why\"" % GENERATOR)
        return 1

    reasons = {name: (existing.get(name) or {}).get("why")
               for name in record["rungs"]
               if (existing.get(name) or {}).get("why")}
    for line in raised:
        reasons[line.split()[0]] = accept

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json.dumps(as_baseline(record, reasons), indent=2,
                                sort_keys=True, ensure_ascii=False)
                     .encode("utf-8") + b"\n")
    print("  wrote %s" % BASELINE)
    for name, rung in sorted(record["rungs"].items()):
        print("    %-40s %4d" % (name,
                                 rung["corpus"]["against_authored_terms"]))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 unless the baseline describes reality")
    ap.add_argument("--record", action="store_true",
                    help="rewrite the baseline from what the ladder found")
    ap.add_argument("--accept-regression", default=None, metavar="WHY",
                    help="required by --record to raise any count")
    args = ap.parse_args(argv)

    record = measure()
    print("  %d data file(s) + %d vendored extract(s), %d shape set(s)"
          % (record["scope"]["data_files"],
             len(record["scope"]["vendored_files"]), len(record["rungs"])))
    vendored = record["vendoring"]
    if vendored.get("available"):
        for key, entry in sorted(vendored["sources"].items()):
            print("    %-4s %-20s %s  %d term(s), %d axiom(s) dropped"
                  % (key, entry["release"], entry["licence"], entry["terms"],
                     entry["axioms_dropped"]))
    print()
    if record["unresolved"]:
        print("  upstream vocabulary not in scope: %s"
              % ", ".join(record["unresolved"]))
        for name, info in sorted(record["upstream_vocabularies"].items()):
            print("    %-8s %d referenced, %d described in scope"
                  % (name, info["referenced"], info["described_in_scope"]))
        print()

    for name, rung in sorted(record["rungs"].items()):
        corpus, fixture = rung["corpus"], rung["fixture"]
        print("  %s" % name)
        if not rung["evaluable"]:
            print("    NOT EVALUABLE -- reasons over %s, which is not in "
                  "scope" % ", ".join(rung["blocked_by_missing_vocabulary"]))
            print("    %d reported violation(s) describe the scope, not the "
                  "ontology" % corpus["violations"])
            continue
        print("    corpus  %-9s %d result(s)  (%d authored, %d warning(s), "
              "%d vendored)"
              % ("conforms" if corpus["conforms"] else "VIOLATIONS",
                 corpus["violations"], corpus["against_authored_terms"],
                 corpus["warnings_against_authored_terms"],
                 corpus["against_vendored_terms"]))
        print("    fixture %-9s %d result(s)  %s"
              % ("rejected" if rung["can_still_fail"] else "conforms",
                 fixture["violations"],
                 "" if rung["can_still_fail"]
                 else "<- the shapes did not fire on data built to break "
                      "them"))
    print()
    if args.gate:
        pass
    elif not record["evaluable_rungs"]:
        print("  passed: %s -- nothing could be evaluated, so this is not "
              "a result" % record["passed"])
    else:
        print("  passed: %s  (%d of %d rung(s) evaluable)"
              % (record["passed"], len(record["evaluable_rungs"]),
                 len(record["rungs"])))

    if args.record:
        return record_baseline(record, args.accept_regression)

    if args.gate:
        problems = compare(record, baseline())
        total = sum(r["corpus"]["against_authored_terms"]
                    for r in record["rungs"].values())
        print("  ladder: %d finding(s) against authored terms across %d of "
              "%d evaluable rung(s)"
              % (total, len(record["evaluable_rungs"]), len(record["rungs"])))
        print()
        if problems:
            for problem in problems:
                print("  GATE: %s" % problem)
            return 1
        print("  gate:   the baseline describes reality. No new findings, "
              "and none of the %d recorded ones has been fixed without "
              "being re-recorded." % total)
        return 0

    if args.out:
        target = Path(args.out)
        target = target if target.is_absolute() else (
            layout.repository_root() / target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(json.dumps(record, indent=2, sort_keys=True,
                                      ensure_ascii=False).encode("utf-8")
                           + b"\n")
        print("  wrote %s" % args.out)
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
