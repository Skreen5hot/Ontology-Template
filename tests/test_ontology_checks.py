# SPDX-License-Identifier: MIT
"""The corpus measures, and the honesty of the validation ladder.

Carried from the Application Requirement Ontology. There, these tests
were written against 62,000 triples of APQC corpus and two shape sets
that had been reporting a missing vocabulary as 213 defects. A project
made from the template starts against one empty module header and one
shape set, which makes the falsification half of every rung the only
evidence that anything is being checked at all: a corpus with no classes
conforms to every shape whether the shapes work or not.

So the assertions that matter on day one are the ones about the fixture,
and the corpus-size guards are set to what a fresh project has -- one
module, header only. They are floors, so a growing corpus passes them;
a project may raise them as its modules fill.
"""

from __future__ import annotations

import pytest

from conftest import load_tool


@pytest.fixture(scope="module")
def digest_tool():
    return load_tool("t_digest", "tools/ontology/corpus_digest.py")


@pytest.fixture(scope="module")
def digest(digest_tool):
    return digest_tool.measure()


@pytest.fixture(scope="module")
def validator():
    return load_tool("t_validate", "tools/ontology/validate.py")


@pytest.fixture(scope="module")
def validation(validator):
    """Measured once.

    Each call runs every shape set against the whole corpus and against
    the fixture. Cheap today; in ARO, three tests asking for it
    separately over 62,000 triples outran a ten-minute timeout, and this
    corpus is meant to grow.
    """
    return validator.measure()


# ------------------------------------------------------------- digests


def test_the_two_measures_cover_every_triple(digest):
    """Ground triples and blank-node-touching triples partition the
    graph. If they did not, a change could land in the gap between them
    and move neither number."""
    merged = digest["merged"]
    assert (merged["ground_triples"] + merged["blank_nodes"]["triples_touching"]
            == merged["triples"]), merged


def test_the_corpus_is_not_empty(digest):
    """Guards every digest below: a digest of nothing is stable, and
    means nothing. One module header of five triples is what a fresh
    project authors."""
    assert digest["merged"]["triples"] >= 4, digest["merged"]["triples"]
    assert digest["scope"]["files"] >= 1, digest["scope"]


def test_the_scope_is_the_authored_ontology(digest):
    """Not a directory walk. A walk would include the reasoner's own
    output and the fixture built to be invalid."""
    paths = digest["scope"]["paths"]
    assert not [p for p in paths if p.startswith("drafts/")], paths
    assert not [p for p in paths if "bad_examples" in p], paths
    assert not [p for p in paths if "shapes" in p], paths


def test_the_ground_digest_moves_when_a_named_term_changes(digest_tool):
    """Falsifies the measure: a digest that ignored content would be
    perfectly stable and perfectly useless."""
    import rdflib

    graph = rdflib.Graph()
    graph.parse(data='<https://ex.invalid/a> <https://ex.invalid/p> "one" .',
                format="turtle")
    before = digest_tool.digest_of(digest_tool.ground(graph))
    graph.add((rdflib.URIRef("https://ex.invalid/a"),
               rdflib.URIRef("https://ex.invalid/p"),
               rdflib.Literal("two")))
    assert digest_tool.digest_of(digest_tool.ground(graph)) != before


def test_the_blank_node_shape_survives_reparsing(digest_tool):
    """The reason blank nodes get a shape rather than a digest.

    rdflib renames them on every parse, so a naive comparison reports
    every restriction as both added and removed -- which is exactly what
    the first namespace check in this repository did.
    """
    import rdflib

    turtle = ("@prefix ex: <https://ex.invalid/> ." + chr(10)
              + "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> ."
              + chr(10)
              + "ex:A rdfs:subClassOf [ a ex:R ; ex:on ex:p ] ." + chr(10)
              + "ex:B rdfs:subClassOf [ a ex:R ; ex:on ex:q ] ." + chr(10))
    first, second = rdflib.Graph(), rdflib.Graph()
    first.parse(data=turtle, format="turtle")
    second.parse(data=turtle, format="turtle")

    raw_first = {(str(s), str(p), str(o)) for s, p, o in first}
    raw_second = {(str(s), str(p), str(o)) for s, p, o in second}
    assert raw_first != raw_second, (
        "blank node names were stable across parses, so the problem this "
        "measure exists for did not occur and it is not being tested")

    assert (digest_tool.bnode_shape(first)["shape_sha256"]
            == digest_tool.bnode_shape(second)["shape_sha256"])


# ------------------------------------------------------- the ladder


def test_the_upstream_vocabulary_the_shapes_walk_is_in_scope(validation):
    """The inverse of what this test used to assert.

    Shapes requiring a class to reach a CCO anchor via subClassOf+ have
    no chain to walk when CCO is absent. They report every subject as
    violating, and that report is indistinguishable from a real defect
    unless the tool separates the two. It did separate them, and then the
    vocabulary was vendored, so now every referenced term resolves.
    """
    record = validation
    assert record["unresolved"] == [], (
        "%s is referenced and not described, so any rung that walks "
        "through it is reporting the scope again" % record["unresolved"])
    for name, info in record["upstream_vocabularies"].items():
        assert info["resolvable"], (name, info)

    for name, rung in record["rungs"].items():
        assert rung["evaluable"], (
            "%s is blocked on %s" % (name,
                                     rung["blocked_by_missing_vocabulary"]))


def test_a_resolvable_vocabulary_is_not_a_complete_one(validation):
    """What "resolvable" does and does not mean.

    Every referenced term is described. That is true of a partial extract
    by construction -- the extract was built from the references -- and
    it is not the same claim as "BFO and CCO are present". The report has
    to carry the difference, or a reader takes the first for the second.
    """
    vendoring = validation["vendoring"]
    assert vendoring["available"], vendoring
    assert vendoring["partial_extracts"] is True
    assert vendoring["not_covered"]
    assert sum(entry["axioms_dropped"]
               for entry in vendoring["sources"].values()) > 0


def test_the_violations_are_attributed_to_whose_terms_they_are(validation):
    """Loading somebody else ontology into the data graph creates the
    mirror of the problem it solved: a defect in the extract reported as
    a defect here."""
    for name, rung in validation["rungs"].items():
        corpus = rung["corpus"]
        assert (corpus["against_authored_terms"]
                + corpus["warnings_against_authored_terms"]
                + corpus["against_vendored_terms"]
                == corpus["violations"]), (name, corpus)
        assert corpus["against_vendored_terms"] == 0, (
            "%d violation(s) are against vendored upstream terms, which "
            "are findings about the extract" % corpus["against_vendored_terms"])


def test_the_baseline_describes_reality(validation, validator):
    """The gate, run as a test.

    The count of open findings used to be written into this file as
    `== 10`. It now lives in config/validation-baseline.json, so the team
    inheriting this can see what is owed without reading test code, and
    so there is one source of truth rather than a number here and another
    in a report.
    """
    problems = validator.compare(validation, validator.baseline())
    assert problems == [], problems


def test_every_rung_is_recorded(validation, validator):
    """Both directions. A rung with no baseline entry would be adopted
    silently; an entry for a rung that no longer exists is coverage for
    nothing."""
    recorded = set((validator.baseline().get("rungs") or {}))
    assert recorded == set(validation["rungs"]), (
        "recorded but gone: %s; present but unrecorded: %s"
        % (sorted(recorded - set(validation["rungs"])),
           sorted(set(validation["rungs"]) - recorded)))



# ------------------------------------------------------- the gate


def rung(findings=0, evaluable=True, exercised=True, vendored=0):
    return {"evaluable": evaluable, "can_still_fail": exercised,
            "blocked_by_missing_vocabulary": [] if evaluable else ["CCO"],
            "corpus": {"against_authored_terms": findings,
                       "against_vendored_terms": vendored}}


def test_the_gate_accepts_only_a_baseline_that_matches(validator):
    """Falsifies the gate, one disagreement at a time.

    Run against constructed records rather than the live ladder, because
    several of these states -- a rung that has vanished, a vocabulary
    that has gone missing, a finding at all -- cannot be reached from
    this repository today. A branch that cannot be reached is a branch
    nobody has executed.
    """
    baseline = {"rungs": {"a": {"authored_findings": 10}}}

    assert validator.compare({"rungs": {"a": rung(10)}}, baseline) == []

    got = validator.compare({"rungs": {"a": rung(11)}}, baseline)
    assert got and "1 new finding." in got[0], got

    got = validator.compare({"rungs": {"a": rung(13)}}, baseline)
    assert got and "3 new findings." in got[0], got

    got = validator.compare({"rungs": {"a": rung(9)}}, baseline)
    assert got and "re-record" in got[0], got

    got = validator.compare({"rungs": {"a": rung(10), "b": rung(0)}}, baseline)
    assert got and "no entry" in got[0], got

    got = validator.compare({"rungs": {}}, baseline)
    assert got and "no longer exists" in got[0], got

    got = validator.compare({"rungs": {"a": rung(10, evaluable=False)}},
                            baseline)
    assert got and "cannot be evaluated" in got[0], got

    got = validator.compare({"rungs": {"a": rung(10, exercised=False)}},
                            baseline)
    assert got and "did not fire on the fixture" in got[0], got

    got = validator.compare({"rungs": {"a": rung(10, vendored=3)}}, baseline)
    assert got and "vendored upstream terms" in got[0], got


def test_recording_refuses_to_raise_a_count_without_a_reason(validator,
                                                             tmp_path,
                                                             monkeypatch):
    """Without this, a regression certifies itself on the one run that
    introduces it and the baseline becomes a transcript of whatever
    happened rather than a commitment."""
    import json

    monkeypatch.setattr(validator.layout, "repository_root",
                        lambda: tmp_path)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "validation-baseline.json").write_text(
        json.dumps({"rungs": {"a": {"authored_findings": 10}}}),
        encoding="utf-8")

    raised = {"rungs": {"a": rung(11)}}
    assert validator.record_baseline(raised, None) == 1, (
        "recording accepted a raised count with no reason given")

    assert validator.record_baseline(raised, "deliberate, see ADR-9") == 0
    after = json.loads(
        (tmp_path / "config" / "validation-baseline.json").read_text(
            encoding="utf-8"))
    assert after["rungs"]["a"]["authored_findings"] == 11
    assert after["rungs"]["a"]["why"] == "deliberate, see ADR-9", (
        "the reason was not recorded beside the number it excuses")

    # Lowering never needs a reason.
    assert validator.record_baseline({"rungs": {"a": rung(4)}}, None) == 0


# --------------------------------------------- the wellformedness set


WELLFORMEDNESS_CONSTRAINTS = [
    "Class has no rdfs:label.",
    "Class has no skos:definition.",
    "Concept has no skos:prefLabel.",
]


def test_every_wellformedness_constraint_is_exercised(validation):
    """Named, not counted.

    None of these finds anything in the corpus today, because nothing is
    authored. A constraint that finds nothing and is never exercised is
    indistinguishable from one that selects nothing, and these exist for
    modules that are not written yet, so the fixture is the only evidence
    they work at all.
    """
    rung = validation["rungs"]["validation.wellformedness"]
    fired = sorted({v["message"] for v in rung["fixture"]["detail"]})
    missing = [m for m in WELLFORMEDNESS_CONSTRAINTS if m not in fired]
    assert not missing, (
        "%d presence constraint(s) did not fire against the fixture: %s"
        % (len(missing), missing))

    drift = [m for m in fired if "in the same language" in m]
    assert drift, (
        "no drift constraint fired against the fixture, so a zero against "
        "the corpus rests on nothing")


def test_the_wellformedness_fixture_does_not_flag_what_is_legitimate(
        validation):
    """The false positives sh:maxCount 1 would have produced.

    A multilingual label pair is correct and must not be reported, and a
    catalog concept carrying no rdfs:label is correct because a concept
    is labelled with skos:prefLabel. The second of those was the first
    draft of this shape set, and it reported 3,842 findings that were the
    catalog being told to look like a class.
    """
    rung = validation["rungs"]["validation.wellformedness"]
    flagged = {v["focus"] for v in rung["fixture"]["detail"]}
    for good in ("FixtureMultilingual", "FixtureWellFormed",
                 "FixtureRepeatedValue", "FixtureConceptWellFormed"):
        assert not [f for f in flagged if f and f.endswith("#" + good)], (
            "%s was built to conform and did not" % good)


def test_the_fixtures_come_from_the_contract(validator, layout):
    """In ARO, `measure` named one fixture component, and a second shape
    set then had nowhere to put its cases. Every new shape set brings
    a fixture; this is what makes adding one a declaration rather than
    an edit to the tool."""
    declared = {c.path for c in layout.components("test-fixture")}
    found = {p.relative_to(layout.repository_root()).as_posix()
             for p in validator.fixtures()}
    assert found == declared, (declared, found)
    assert found, "no fixture is loaded, so no shape set can be falsified"


def test_a_ladder_that_evaluated_nothing_does_not_pass(validator):
    """`all()` over an empty sequence is True, so the first version of
    this tool reported success having evaluated no rung at all.

    That state cannot be reached from this repository any more, which is
    exactly why the guard is tested against a constructed record rather
    than against the live one -- otherwise it would be a branch nobody
    executes, sitting in a tool whose whole subject is checks that do not
    fire.
    """
    assert validator.passed_of({}) is False

    blocked = {"one": {"evaluable": False,
                       "corpus": {"conforms": True}, "can_still_fail": True}}
    assert validator.passed_of(blocked) is False

    evaluated = {"one": {"evaluable": True,
                         "corpus": {"conforms": True},
                         "can_still_fail": True}}
    assert validator.passed_of(evaluated) is True


def test_the_shapes_are_still_wired_to_a_fixture(validation):
    """The bad-examples fixture must break at least one shape set.

    A fixture that breaks nothing is not a falsification, and a shape set
    with no fixture behind it has a green result that cannot be
    distinguished from a constraint selecting nothing.
    """
    record = validation
    exercised = [name for name, rung in record["rungs"].items()
                 if rung["fixture_exercises_these_shapes"]]
    assert exercised, (
        "the bad-examples fixture produced no violations against any shape "
        "set, so nothing is falsifying the shapes")

    unexercised = sorted(set(record["rungs"]) - set(exercised))
    assert unexercised == [], (
        "%s has no negative fixture behind it, so its result cannot be "
        "distinguished from a constraint that selects nothing" % unexercised)




# ------------------------------------------- the committed measurement


def test_the_committed_digest_is_the_one_the_tool_produces(digest, repo):
    """An artifact in the tree that nothing compares is a claim, not a
    measurement. This is the comparison."""
    import json

    recorded = json.loads(
        (repo / "config/corpus-digest.json").read_text(encoding="utf-8"))
    assert (recorded["merged"]["ground_sha256"]
            == digest["merged"]["ground_sha256"]), (
        "config/corpus-digest.json describes a different corpus; "
        "regenerate it in the commit that changed the ontology")
    assert (recorded["merged"]["blank_nodes"]["shape_sha256"]
            == digest["merged"]["blank_nodes"]["shape_sha256"])
    assert recorded["scope"]["paths"] == digest["scope"]["paths"]


# -------------------------------------------------- the realist library


#: Every realist constraint, by the start of its message, and the fixture
#: class built to trip it. Named, not counted.
REALIST_CASES = {
    "Class reaches no BFO category": ("Unanchored", "Violation"),
    "Class asserts more than one named parent": ("TwoParents", "Warning"),
    "falls under": ("ContinuantAndOccurrent", "Violation"),
    "does not name its parent": ("VagueDefinition", "Warning"),
    "which is disjoint with the property's range": ("RangeDisjoint",
                                                    "Violation"),
    "which is not known to fall under the property's range": (
        "RangeUnknown", "Warning"),
    "it is disjoint with": ("DomainDisjoint", "Violation"),
    "it is not known to fall under": ("DomainUnknown", "Warning"),
    "Deprecated term names neither": ("DeprecatedNoWayForward",
                                      "Violation"),
    "Ontology header has no dcterms:license": (
        "realist-incomplete-header", "Violation"),
    "Ontology header has no dcterms:creator": (
        "realist-incomplete-header", "Violation"),
    "Ontology header has no owl:versionIRI": (
        "realist-incomplete-header", "Violation"),
    "Ontology header has no owl:versionInfo": (
        "realist-incomplete-header", "Violation"),
}

REALIST_CONTROLS = ("RealistGood", "RealistGoodChild",
                    "RealistGoodRestriction",
                    "RealistDeprecatedWithReplacement",
                    "realist-complete-header")


def results_for(validation, rung, focus_name):
    out = []
    for v in validation["rungs"][rung]["fixture"]["detail"]:
        focus = v["focus"] or ""
        if focus.endswith("#" + focus_name) or focus.endswith("/" + focus_name):
            out.append(v)
    return out


def test_every_realist_constraint_fires_on_its_case(validation):
    detail = validation["rungs"]["validation.realist"]["fixture"]["detail"]
    assert len(detail) < 300, (
        "the fixture detail is at its cap; a constraint could be hidden")
    for message, (case, severity) in REALIST_CASES.items():
        hits = [v for v in results_for(validation, "validation.realist", case)
                if message in v["message"]]
        assert hits, "%r did not fire on %s" % (message, case)
        assert {v["severity"] for v in hits} == {severity}, (
            message, case, {v["severity"] for v in hits})


def test_the_realist_positive_controls_are_not_reported(validation):
    for case in REALIST_CONTROLS:
        for rung in ("validation.realist", "validation.annotation-profile",
                     "validation.wellformedness"):
            assert results_for(validation, rung, case) == [], (rung, case)


def test_a_warning_is_reported_and_not_gated(validator):
    """The constructed case: a rung whose corpus has only warnings is not
    a regression against a baseline of zero."""
    record = {"rungs": {"a": {
        "evaluable": True, "can_still_fail": True,
        "blocked_by_missing_vocabulary": [],
        "corpus": {"against_authored_terms": 0,
                   "warnings_against_authored_terms": 5,
                   "against_vendored_terms": 0}}}}
    assert validator.compare(record,
                             {"rungs": {"a": {"authored_findings": 0}}}) == []


def test_independent_and_dependent_is_caught_only_through_derived_disjointness(
        validator, layout):
    """BFO says independent and specifically dependent continuant are
    disjoint only in an owl:AllDisjointClasses axiom, which the extract
    drops. The derived disjointness file is what lets a shape see it:
    run without that file, the case passes; with it, it fails on exactly
    that pair."""
    from pyshacl import validate as shacl
    import rdflib

    derived = layout.path("vendor.bfo-disjointness")
    fixture = layout.path("fixture.realist-bad-examples")
    shapes = validator.load([layout.path("validation.realist")])
    others = [p for p in layout.vendored_files() if p != derived]

    def disjoint_findings(paths):
        data = validator.load([fixture] + paths)
        report = validator.run(data, shapes)
        return [v for v in report["violations"]
                if (v["focus"] or "").endswith("#IndependentAndDependent")
                and "falls under" in v["message"]]

    without = disjoint_findings(others)
    with_it = disjoint_findings(others + [derived])
    assert without == [], without
    assert len(with_it) == 1, with_it
    assert ("BFO_0000004" in with_it[0]["message"]
            and "BFO_0000020" in with_it[0]["message"]), with_it[0]["message"]


def test_the_profile_shapes_are_what_the_profile_generates(repo):
    tool = load_tool("t_profile", "tools/ontology/profile_shapes.py")
    assert tool.main(["--check"]) == 0


def test_the_profile_refuses_a_property_nobody_defines(tmp_path, monkeypatch):
    tool = load_tool("t_profile_refuse", "tools/ontology/profile_shapes.py")
    real = tool.upstream_terms
    (tmp_path / "config").mkdir()
    for text, expect in (
        ("annotations:\n  - property: https://www.commoncoreontologies.org/"
         "ont99999999\n    label: x\n    severity: warning\n    why: y\n",
         "not a term of any pinned upstream"),
        ("annotations: []\n", "lists no annotation"),
        ("annotations:\n  - property: http://purl.org/dc/terms/source\n"
         "    label: x\n    severity: fatal\n    why: y\n",
         "is not violation or warning"),
    ):
        (tmp_path / "config/annotation-profile.yaml").write_text(
            text, encoding="utf-8")
        monkeypatch.setattr(tool, "upstream_terms", lambda root: real(
            tool.layout.repository_root()))
        with pytest.raises(SystemExit) as error:
            tool.profile(tmp_path)
        assert expect in str(error.value), (expect, str(error.value))


def test_every_profile_annotation_fires_on_the_fixture(validation):
    hits = results_for(validation, "validation.annotation-profile",
                       "NoDefinitionSource")
    assert hits and all(v["severity"] == "Warning" for v in hits), hits


def test_warnings_and_violations_are_split_on_a_real_report(validation,
                                                           validator):
    """The split the gate depends on, run on the realist fixture's own
    results: the vague definition is a warning, the unanchored class a
    violation, and the warning is not among what the gate would count."""
    detail = validation["rungs"]["validation.realist"]["fixture"]["detail"]
    violations, warnings, _upstream = validator.partition(detail)
    def foci(rows):
        return {(r["focus"] or "").rsplit("#", 1)[-1] for r in rows}
    assert "Unanchored" in foci(violations)
    assert "VagueDefinition" in foci(warnings)
    assert "VagueDefinition" not in foci(violations)


# ------------------------------------------------------- concept schemes


SKOS_CASES = {
    "Concept is in no declared concept scheme": "SkosOrphan",
    "is its own broader concept": "SkosCycleA",
    "in a scheme it is not in": "SkosAcrossSchemes",
    "as both its prefLabel and an altLabel": "SkosRepeatedLabel",
    "Concept is also an owl:Class": "SkosAlsoClass",
    "Concept scheme has no top concept": "SkosTopless",
}

SKOS_CONTROLS = ("SkosGoodScheme", "SkosGoodTop", "SkosGoodChild",
                 "SkosOtherScheme", "SkosOtherTop")


def test_every_skos_constraint_fires_on_its_case(validation):
    for message, case in SKOS_CASES.items():
        hits = [v for v in results_for(validation, "validation.skos", case)
                if message in v["message"]]
        assert hits, "%r did not fire on %s" % (message, case)


def test_the_skos_positive_controls_are_not_reported(validation):
    for case in SKOS_CONTROLS:
        assert results_for(validation, "validation.skos", case) == [], case
