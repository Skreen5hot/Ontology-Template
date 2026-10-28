# SPDX-License-Identifier: MIT
"""Run the SHACL shapes, and check that they can still fail.

    python tools/ontology/validate.py            # report
    python tools/ontology/validate.py -o r.json  # and every finding, as JSON
    python tools/ontology/validate.py --gate     # exit 1 on a finding the
                                                 # register does not accept,
                                                 # or an entry that matches
                                                 # nothing
    python tools/ontology/validate.py --propose  # register entries for the
                                                 # new findings

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

SEVERITY AND THE REGISTER

The realist library uses warnings for what a reviewer should look at (two
asserted parents, a definition that does not name its genus) and
violations for what is wrong. Both are gated through the findings
register (tools/findings.py, which states the policy): each finding is
accepted by an entry naming it, or it is new, and a new violation or
warning fails. This replaced a count per shape set, under which fixing
one finding and introducing another passed, and a warning was never
gated at all.

MODULES

The shapes see one merged graph, and some of what the site publishes is
per module: the header it shows a module under, and which module a term
is declared in. Those are read module by module here (`module_findings`)
and gated through the same register, under `where: modules`, so that
nothing the site depends on goes unchecked until a deploy. The same
reading holds a module carrying declared third-party text to its
declaration (config/third-party-text.yaml): the header names the source
and its release, and carries the declared attribution (T9, T23).

SCHEME RULES

config/naming.yaml may hold `scheme_rules`: a local-name pattern that
must, or must not, sit under a category through rdfs:subClassOf (T12).
They are a project's IRI scheme, not realist rules, so the template ships
none; a project's are gated under `where: naming`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import findings  # noqa: E402
import layout  # noqa: E402
import project  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "licensing"))
import third_party  # noqa: E402

FORMAT_VERSION = 2
GENERATOR = "tools/ontology/validate.py"
CHECK = "validate"


def load(paths) -> "rdflib.Graph":
    import rdflib

    graph = rdflib.Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


OWL = "http://www.w3.org/2002/07/owl#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

#: The header annotations the site shows for a module, which must each be
#: one literal per language for the site to show one.
HEADER_TEXT = (("http://purl.org/dc/terms/title", "dcterms:title"),
               (OWL + "versionInfo", "owl:versionInfo"),
               ("http://www.w3.org/2000/01/rdf-schema#comment",
                "rdfs:comment"))

#: The declarations that make a subject a term, for the site and here.
TERM_TYPES = (OWL + "Class", OWL + "ObjectProperty", OWL + "DatatypeProperty",
              OWL + "AnnotationProperty")

#: `where` for the module findings in the register.
MODULES = "modules"
#: `where` for the scheme-rule findings.
NAMING = "naming"
DCTERMS = "http://purl.org/dc/terms/"
RDFS_SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"


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


def run(data, shapes, engine: str = "oxigraph") -> dict:
    """Every shape in `shapes` over `data`, as one record.

    engine "oxigraph": the SPARQL constraints run set-based in Oxigraph
    (tools/ontology/sparql_constraints.py, which says why), the core
    constraints in pyshacl. engine "pyshacl": everything in pyshacl, per
    focus node -- the reference the first is held to, record for record,
    in tests/test_ontology_checks.py, and quadratic at a real ontology's
    size.
    """
    from pyshacl import validate as shacl

    sparql_records = []
    core = shapes
    if engine == "oxigraph":
        import sparql_constraints

        core, sparql_shapes = sparql_constraints.split(shapes)
        if sparql_shapes:
            for record in sparql_constraints.run(data, shapes,
                                                 sparql_shapes):
                source = record.pop("source")
                record["shape"] = stable_shape(source, record["message"])
                record["message"] = (record["message"][:600]
                                     if record["message"] else None)
                sparql_records.append(record)
    elif engine != "pyshacl":
        raise ValueError("unknown engine %r" % engine)

    conforms, results_graph, results_text = shacl(
        data_graph=data, shacl_graph=core, inference="none",
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
    violations.extend(sparql_records)
    if any(r["severity"] == "Violation" for r in sparql_records):
        conforms = False
    violations.sort(key=lambda v: (v["shape"] or "", v["focus"] or "",
                                   v["message"] or ""))
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


def progress(text: str) -> None:
    """One line per step, to stderr, so a run that takes minutes says
    where it is and stdout stays the report."""
    print("  ... " + text, file=sys.stderr, flush=True)


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

    progress("loading %d data file(s), %d extract(s), %d fixture(s)"
             % (len(scope), len(vendored), len(fixture_paths)))
    # Each module parsed once, alone, for the module findings, and the
    # same graphs merged for the shapes.
    modules = [(path, load([path])) for path in scope]
    data = load(list(vendored))
    for _path, graph in modules:
        for triple in graph:
            data.add(triple)
    bad = load(list(fixture_paths) + list(vendored))
    vocabularies = unresolved_vocabularies(data)
    missing = sorted(name for name, info in vocabularies.items()
                     if not info["resolvable"])

    rungs = {}
    for name, path in sorted(sets.items()):
        shapes = load([path])
        depends = shapes_depend_on(path)
        blocked = sorted(set(depends) & set(missing))
        progress("%s: the corpus" % name)
        corpus = run(data, shapes)
        progress("%s: the fixtures" % name)
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
                # Every one, not a sample: the register is matched
                # against this list, and a person fixing findings works
                # from it.
                "detail": authored_focus,
                "warning_detail": authored_warnings,
                "vendored_detail": upstream_focus,
            },
            "fixture": {
                "conforms": against_fixture["conforms"],
                "violations": len(against_fixture["violations"]),
                # The evidence that each constraint fires; a cap would
                # make the falsification report a subset of itself.
                "detail": against_fixture["violations"],
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

    module_results = module_findings(modules, root)
    naming_results = scheme_findings(data, scheme_rules(root))
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
        "modules": {"files": len(modules), "detail": module_results},
        "naming": {"rules": len(scheme_rules(root)),
                   "detail": naming_results},
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
        "passed": passed_of(rungs) and not any(
            r["severity"] == "Violation"
            for r in module_results + naming_results),
    }


# ------------------------------------------------------------ modules


def module_findings(modules, root=None, declarations=None) -> list[dict]:
    """What only a module-by-module reading can find, for (path, graph)
    pairs: a module without exactly one ontology header, header text that
    is not one literal per language, an authored term declared in more
    than one module, and declared third-party text whose header does not
    name its source and release or carry its attribution. Records in the
    shape of a shape result, with `shape` naming the rule."""
    import rdflib

    root = root or layout.repository_root()
    if declarations is None:
        declarations = third_party.load(root)
    out, declared = [], {}

    def found(focus, rule, severity, message):
        out.append({"focus": focus, "shape": "module:" + rule,
                    "severity": severity, "message": message})

    for path, graph in modules:
        path = Path(path).resolve()
        where = (path.relative_to(root).as_posix()
                 if path.is_relative_to(root) else path.as_posix())
        headers = sorted(str(s) for s in graph.subjects(
            rdflib.URIRef(RDF_TYPE), rdflib.URIRef(OWL + "Ontology")))
        if len(headers) != 1:
            found(where, "one-header", "Violation",
                  "Module %s has %d ontology headers%s. A module is "
                  "published under its one header: with none it has no "
                  "title, version or licence, and with two the site would "
                  "have to choose." % (where, len(headers), (
                      ": " + ", ".join(headers)) if headers else ""))
        for header in headers:
            for iri, name in HEADER_TEXT:
                values = list(graph.objects(rdflib.URIRef(header),
                                            rdflib.URIRef(iri)))
                if [v for v in values if not isinstance(v, rdflib.Literal)]:
                    found(header, "header-literal", "Violation",
                          "Ontology header %s has a %s that is not a "
                          "literal." % (header, name))
                langs = [v.language or "" for v in values
                         if isinstance(v, rdflib.Literal)]
                if any(langs.count(lang) > 1 for lang in set(langs)):
                    found(header, "header-drift", "Violation",
                          "Ontology header %s carries two different %s "
                          "values in the same language." % (header, name))
        for declaration in declarations:
            count = third_party.values_in(graph, declaration)
            if not count:
                continue
            sources = [str(v) for h in headers for v in graph.objects(
                rdflib.URIRef(h), rdflib.URIRef(DCTERMS + "source"))]
            rights = [str(v) for h in headers for v in graph.objects(
                rdflib.URIRef(h), rdflib.URIRef(DCTERMS + "rights"))]
            if not [s for s in sources if declaration["source"] in s
                    and declaration["release"] in s]:
                found(where, "third-party-source", "Violation",
                      "Module %s holds %d value(s) of %s, declared as text "
                      "from %s %s, and its header names that source and "
                      "release in no dcterms:source. A reader cannot tell "
                      "which release the text was taken from."
                      % (where, count, declaration["property"],
                         declaration["source"], declaration["release"]))
            if not [r for r in rights
                    if declaration["attribution"].strip() in r]:
                found(where, "third-party-attribution", "Violation",
                      "Module %s holds %d value(s) of %s, declared as text "
                      "from %s, and its header does not carry the declared "
                      "attribution in dcterms:rights."
                      % (where, count, declaration["property"],
                         declaration["source"]))
        for type_iri in TERM_TYPES:
            for subject in graph.subjects(rdflib.URIRef(RDF_TYPE),
                                          rdflib.URIRef(type_iri)):
                if isinstance(subject, rdflib.URIRef) and str(
                        subject).startswith(AUTHORED_NAMESPACE):
                    declared.setdefault(str(subject), set()).add(where)
    for iri, wheres in sorted(declared.items()):
        if len(wheres) > 1:
            found(iri, "declared-once", "Warning",
                  "Term %s is declared in %d modules: %s. A term declared "
                  "in two modules is an inlined copy, and inlined copies "
                  "drift; declare it once and let the others use it."
                  % (iri, len(wheres), ", ".join(sorted(wheres))))
    out.sort(key=lambda r: (r["shape"], r["focus"], r["message"]))
    return out


# -------------------------------------------------------- scheme rules


def scheme_rules(root=None) -> list[dict]:
    """`scheme_rules` from config/naming.yaml, checked. Each: id, pattern
    (a regular expression matched against the whole local name), exactly
    one of must_sit_under and must_not_sit_under (a class IRI), severity
    (violation | warning) and why."""
    import re

    import yaml

    path = (root or layout.repository_root()) / "config/naming.yaml"
    if not path.is_file():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rules = raw.get("scheme_rules") or []
    seen = set()
    for number, rule in enumerate(rules, 1):
        where = "config/naming.yaml: scheme rule %d" % number
        for key in ("id", "pattern", "severity", "why"):
            if not rule.get(key):
                raise SystemExit("%s declares no %r" % (where, key))
        sides = [k for k in ("must_sit_under", "must_not_sit_under")
                 if rule.get(k)]
        if len(sides) != 1:
            raise SystemExit("%s needs exactly one of must_sit_under and "
                             "must_not_sit_under" % where)
        if rule["severity"] not in ("violation", "warning"):
            raise SystemExit("%s severity %r is not violation or warning"
                             % (where, rule["severity"]))
        if rule["id"] in seen:
            raise SystemExit("%s repeats the id %r" % (where, rule["id"]))
        seen.add(rule["id"])
        re.compile(rule["pattern"])
    return rules


def scheme_findings(data, rules) -> list[dict]:
    """Every authored class whose local name matches a rule's pattern and
    which sits, or does not sit, under the rule's category -- read through
    rdfs:subClassOf in the merged graph, vendored extracts included."""
    import re

    import rdflib

    out = []
    if not rules:
        return out
    subclass = rdflib.URIRef(RDFS_SUBCLASS)
    classes = sorted(str(s) for s in data.subjects(
        rdflib.URIRef(RDF_TYPE), rdflib.URIRef(OWL + "Class"))
        if isinstance(s, rdflib.URIRef)
        and str(s).startswith(AUTHORED_NAMESPACE))
    for rule in rules:
        pattern = re.compile(rule["pattern"])
        category = rule.get("must_sit_under") or rule["must_not_sit_under"]
        required = bool(rule.get("must_sit_under"))
        for iri in classes:
            local = iri[len(AUTHORED_NAMESPACE):]
            if not pattern.fullmatch(local):
                continue
            under = category in {str(a) for a in data.transitive_objects(
                rdflib.URIRef(iri), subclass) if str(a) != iri}
            if under == required:
                continue
            out.append({
                "focus": iri, "shape": "scheme:" + rule["id"],
                "severity": rule["severity"].capitalize(),
                "message": "Class %s has a local name matching scheme rule "
                           "%s (%s) and %s %s. %s" % (
                               iri, rule["id"], rule["pattern"],
                               "does not sit under" if required
                               else "sits under", category,
                               " ".join(rule["why"].split()))})
    return out


# ---------------------------------------------------------- the gate


def register_findings(record: dict) -> list[dict]:
    """Every corpus result of every evaluable rung, as the register
    identifies findings. Against vendored terms too: those are accepted
    only by an entry that names the upstream."""
    out = []
    for name, rung in sorted(record["rungs"].items()):
        if not rung["evaluable"]:
            continue
        corpus = rung["corpus"]
        for result in (corpus["detail"] + corpus["warning_detail"]
                       + corpus["vendored_detail"]):
            out.append(findings.finding(
                CHECK, name, result["focus"], result["shape"],
                result["message"], result["severity"]))
    for where in (MODULES, NAMING):
        for result in (record.get(where) or {}).get("detail", []):
            out.append(findings.finding(
                CHECK, where, result["focus"], result["shape"],
                result["message"], result["severity"]))
    return out


def structural(record: dict) -> list[str]:
    """What makes the ladder's result mean nothing, whatever the
    register says: a rung that cannot be evaluated, or shapes that do not
    fire on the fixture built to break them."""
    problems = []
    for name, rung in sorted(record["rungs"].items()):
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
    return problems


def gate(record: dict, entries: list, today=None) -> tuple[list, dict]:
    """(structural problems, the register's verdict). The gate passes
    when there are no problems and the verdict passed."""
    return structural(record), findings.judge(
        CHECK, register_findings(record), entries, today=today)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 on a finding the register does not "
                         "accept, or an entry that matches nothing")
    ap.add_argument("--propose", action="store_true",
                    help="print register entries for the new findings")
    ap.add_argument("--reason", help="with --propose: the reason to write")
    ap.add_argument("--owner", help="with --propose: the owner to write")
    ap.add_argument("--review", help="with --propose: the review date")
    args = ap.parse_args(argv)

    record = measure()
    if args.propose:
        # Before the report, which would otherwise precede the YAML on
        # stdout and make it something that cannot be pasted.
        verdict = findings.judge(CHECK, register_findings(record),
                                 findings.load())
        print("  %d new finding(s); entries on stdout" % len(verdict["new"]),
              file=sys.stderr)
        print(findings.propose(verdict["new"], args.reason, args.owner,
                               args.review)
              or "# no new findings: nothing to propose")
        return 0
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
    module_results = record["modules"]["detail"]
    print("  %s" % MODULES)
    print("    corpus  %-9s %d result(s) across %d module(s)"
          % ("conforms" if not module_results else "FINDINGS",
             len(module_results), record["modules"]["files"]))
    naming_results = record["naming"]["detail"]
    print("  %s" % NAMING)
    print("    corpus  %-9s %d result(s) from %d scheme rule(s)"
          % ("conforms" if not naming_results else "FINDINGS",
             len(naming_results), record["naming"]["rules"]))
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

    if args.gate:
        problems, verdict = gate(record, findings.load())
        print("  ladder: %d finding(s) across %d of %d evaluable rung(s)"
              % (len(register_findings(record)),
                 len(record["evaluable_rungs"]), len(record["rungs"])))
        findings.report(CHECK, verdict)
        print()
        for problem in problems:
            print("  GATE: %s" % problem)
        if problems or not verdict["passed"]:
            return 1
        print("  gate:   every finding is accepted by an entry in %s, and "
              "every entry for this check matches one."
              % findings.REGISTER)
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
