# SPDX-License-Identifier: MIT
"""WP4: the detection gaps the BPO port found, each closed and held.

For each gap the tests show four things on planted input that is not
BPO's: the defect is found; it is reported with the severity and words
a reader can act on; it can be dispositioned, by an entry in the findings
register; and once corrected it is not found, while reintroducing it is,
so a correction is held rather than hoped for.

  T8   drift in any annotation the profile lists, comments included
  T9   third-party text in a module without the declared attribution
  T10  an object property between classes; an annotation property
       restricted on
  T11  a trailing "(...)" in a parent's label: one qualifier finding,
       not a genus warning on every child
  T12  scheme rules: a local-name pattern that must, or must not, sit
       under a category
  T23  third-party text in a module whose header does not name the
       source's release
"""

from __future__ import annotations

import datetime
import sys

import pytest

from conftest import ROOT, load_tool

sys.path.insert(0, str(ROOT / "tools/licensing"))

PREFIXES = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix cco: <https://www.commoncoreontologies.org/> .
@prefix : <{ns}> .
"""


@pytest.fixture(scope="module")
def validator():
    return load_tool("dg_validate", "tools/ontology/validate.py")


@pytest.fixture(scope="module")
def findings_tool():
    return load_tool("dg_findings", "tools/findings.py")


@pytest.fixture(scope="module")
def vendored(validator, layout):
    return validator.load(layout.vendored_files())


def graph_of(text, project):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(data=PREFIXES.replace("{ns}", project.namespace()) + text,
                format="turtle")
    return graph


def run(validator, vendored, layout, text, project, shape_set):
    """The named shape set over the planted text plus the vendored
    extracts, as the ladder runs it."""
    data = graph_of(text, project)
    for triple in vendored:
        data.add(triple)
    shapes = validator.load([layout.component(shape_set).resolve()])
    return validator.run(data, shapes)["violations"]


def on(results, project, name, says):
    return [r for r in results
            if r["focus"] == project.namespace() + name and says in r["message"]]


def accepted_then_fixed(findings_tool, before, after):
    """The disposition and the correction, through the register: an
    entry with a reason accepts the finding, and when the defect is
    corrected the entry no longer matches anything and the gate fails
    until it is removed -- so the fix is recorded, not silent."""
    import yaml

    today = datetime.date(2026, 10, 28)
    entries = yaml.safe_load(findings_tool.propose(
        before, "planted for the test", "the test", "2099-01-01"))
    accepted = findings_tool.judge("validate", before, entries, today=today)
    assert accepted["passed"] and not accepted["new"], accepted
    fixed = findings_tool.judge("validate", after, entries, today=today)
    assert not fixed["passed"] and fixed["stale"], fixed
    return entries


def as_findings(validator, findings_tool, where, results):
    return [findings_tool.finding("validate", where, r["focus"], r["shape"],
                                  r["message"], r["severity"])
            for r in results]


# ------------------------------------------------------------- T8


DRIFTED = """
:Drifted a owl:Class ; rdfs:label "Drifted" ;
    skos:definition "A process whose comment differs between modules." ;
    rdfs:subClassOf obo:BFO_0000015 ;
    rdfs:comment "As module A says it.", "As module B says it." .
:driftedProperty a owl:ObjectProperty ; rdfs:label "drifted property" ;
    skos:definition "A property whose comment differs between modules." ;
    rdfs:comment "One.", "Two." .
"""
AGREED = """
:Drifted a owl:Class ; rdfs:label "Drifted" ;
    skos:definition "A process whose comment differs between modules." ;
    rdfs:subClassOf obo:BFO_0000015 ;
    rdfs:comment "As the modules agree to say it." .
:driftedProperty a owl:ObjectProperty ; rdfs:label "drifted property" ;
    skos:definition "A property whose comment differs between modules." ;
    rdfs:comment "One." .
"""


def test_comment_drift_is_found(validator, findings_tool, vendored, layout,
                                project):
    """T8: two comments in one language, on a class and on a property --
    BPO's designatesProcessType had seven -- are each a finding, by
    identity; agreed comments are not; the fix is recorded."""
    says = "carries two different rdfs:comment values in the same language"
    before = run(validator, vendored, layout, DRIFTED, project,
                 "validation.annotation-profile")
    for name in ("Drifted", "driftedProperty"):
        [hit] = on(before, project, name, says)
        assert hit["severity"] == "Warning"
    after = run(validator, vendored, layout, AGREED, project,
                "validation.annotation-profile")
    assert not [r for r in after if says in r["message"]]
    pick = [r for r in before if says in r["message"]]
    accepted_then_fixed(
        findings_tool,
        as_findings(validator, findings_tool, "validation.annotation-profile",
                    pick), [])


def test_the_list_is_configurable(tmp_path, monkeypatch):
    """T8: the properties that must agree are the profile's list. Adding
    dcterms:description adds its constraint; the term contract's two
    must be listed, as violations, and generate nothing twice."""
    tool = load_tool("dg_profile", "tools/ontology/profile_shapes.py")
    real = tool.upstream_terms
    monkeypatch.setattr(tool, "upstream_terms", lambda root: real(
        tool.layout.repository_root()))
    (tmp_path / "config").mkdir()
    contract = (
        "  - property: http://www.w3.org/2000/01/rdf-schema#label\n"
        "    label: rdfs:label\n    severity: violation\n    why: c\n"
        "  - property: http://www.w3.org/2004/02/skos/core#definition\n"
        "    label: skos:definition\n    severity: violation\n    why: c\n")
    description = (
        "  - property: http://purl.org/dc/terms/description\n"
        "    label: dcterms:description\n    severity: warning\n    why: d\n")

    def with_list(body):
        (tmp_path / "config/annotation-profile.yaml").write_text(
            "agree_across_modules:\n" + body, encoding="utf-8")
        return tool.agreement(tmp_path)

    text = tool.shapes_text([{"property": "http://purl.org/dc/terms/source",
                              "label": "source", "severity": "warning",
                              "why": "w"}], with_list(contract + description))
    assert "<http://purl.org/dc/terms/description> ?a, ?b" in text
    assert "rdf-schema#comment> ?a" not in text
    assert "rdf-schema#label> ?a" not in text
    for body, expect in (
            (description, "must name"),
            (contract.replace("severity: violation", "severity: warning", 1)
             + description, "cannot be made a warning")):
        with pytest.raises(SystemExit) as error:
            with_list(body)
        assert expect in str(error.value), (expect, str(error.value))


def test_the_committed_list_is_the_default(repo):
    """The response's default: label, definition and comment."""
    tool = load_tool("dg_profile_live", "tools/ontology/profile_shapes.py")
    listed = [e["property"] for e in tool.agreement(repo)]
    assert listed == ["http://www.w3.org/2000/01/rdf-schema#label",
                      "http://www.w3.org/2004/02/skos/core#definition",
                      "http://www.w3.org/2000/01/rdf-schema#comment"]


# ------------------------------------------------------- T9, T23


DECLARATION = {"property": "https://example.org/vocabulary#sourceText",
               "source": "Example Framework", "release": "v1.0",
               "licence": "CC-BY-SA-4.0",
               "attribution": "Contains text from Example Framework v1.0, "
                              "CC BY-SA 4.0."}

QUOTING = """
@prefix ext: <https://example.org/vocabulary#> .
<urn:planted:module> a owl:Ontology ; dcterms:title "Planted" {header} .
:Quoted a owl:Class ; rdfs:label "Quoted" ;
    skos:definition "A process described in another framework." ;
    rdfs:subClassOf obo:BFO_0000015 ;
    ext:sourceText "Text taken verbatim from Example Framework." .
:AlsoQuoted a owl:Class ; rdfs:label "Also quoted" ;
    skos:definition "Another process described there." ;
    rdfs:subClassOf obo:BFO_0000015 ;
    ext:sourceText "More text taken from it." .
"""


def module(project, tmp_path, header):
    path = tmp_path / "quoting.ttl"
    text = (PREFIXES.replace("{ns}", project.namespace())
            + QUOTING.replace("{header}", header))
    path.write_bytes(text.encode("utf-8"))
    return path, graph_of(QUOTING.replace("{header}", header), project)


def module_results(validator, project, tmp_path, header, rule):
    path, graph = module(project, tmp_path, header)
    return [r for r in validator.module_findings(
        [(path, graph)], tmp_path, [DECLARATION])
        if r["shape"] == "module:" + rule]


RIGHTS = '; dcterms:rights "%s"' % DECLARATION["attribution"]
SOURCE = '; dcterms:source "Example Framework v1.0"'


def test_unattributed_third_party_text_fails(validator, findings_tool,
                                             project, tmp_path):
    """T9: a module holding declared third-party text, whose header does
    not carry the declared attribution, is a violation; with it, none;
    the fix is recorded."""
    [hit] = module_results(validator, project, tmp_path, SOURCE,
                           "third-party-attribution")
    assert hit["severity"] == "Violation"
    assert "holds 2 value(s)" in hit["message"]
    assert not module_results(validator, project, tmp_path, SOURCE + RIGHTS,
                              "third-party-attribution")
    accepted_then_fixed(findings_tool, as_findings(
        validator, findings_tool, "modules", [hit]), [])


def test_external_text_without_release_is_found(validator, project,
                                                tmp_path):
    """T23: the header names the source but not the release the text was
    taken from -- 17 of BPO's 18 original slice files -- and is found;
    naming both is not."""
    [hit] = module_results(validator, project, tmp_path,
                           '; dcterms:source "Example Framework"' + RIGHTS,
                           "third-party-source")
    assert "Example Framework v1.0" in hit["message"]
    assert not module_results(validator, project, tmp_path, SOURCE + RIGHTS,
                              "third-party-source")


def test_third_party_text_in_a_module_is_classified(project, tmp_path,
                                                    monkeypatch):
    """T9: the disposition report lists the text apart from the module's
    own licence, with the licence as declared and the statement that it
    judges nothing -- which is pending Legal, and says so."""
    disposition = load_tool("dg_disposition", "tools/licensing/disposition.py")
    import third_party

    path, _graph = module(project, tmp_path, SOURCE)
    monkeypatch.setattr(third_party, "load", lambda root=None: [DECLARATION])
    monkeypatch.setattr(disposition.layout, "ontology_files", lambda: [path])
    [row] = disposition.embedded_text(tmp_path)
    assert row == {"module": "quoting.ttl", "property": DECLARATION["property"],
                   "values": 2, "source": "Example Framework v1.0",
                   "licence": "CC-BY-SA-4.0"}
    assert third_party.STATEMENT.startswith("PENDING LEGAL")
    assert "does not judge whether" in third_party.STATEMENT


def test_the_statement_is_the_proposed_wording():
    """The one sentence that bounds what the check means is the wording
    sent to Legal for its answer, held exactly: a change to it is a
    change in what the template claims, and is made when Legal answers,
    in a diff, not in passing (decision 14)."""
    import third_party

    assert third_party.STATEMENT == (
        "PENDING LEGAL (EXAMPLE-LEGAL-2026-10-28-t9-third-party-text): "
        "proposed wording, not yet Legal's. This report records what the "
        "project declares about third-party text and checks that the "
        "declared source, release and attribution are present. It does not "
        "judge whether the text may be redistributed.")


def test_a_declaration_needs_every_field(tmp_path):
    import third_party

    (tmp_path / "config").mkdir()
    for body, expect in (
            ("declarations:\n  - property: urn:p\n    source: s\n",
             "has no release, licence, attribution"),
            ("declarations:\n  - property: urn:p\n    source: s\n"
             "    release: r\n    licence: some licence\n    attribution: a\n",
             "neither an SPDX identifier")):
        (tmp_path / third_party.DECLARATIONS).write_text(body,
                                                         encoding="utf-8")
        with pytest.raises(SystemExit) as error:
            third_party.load(tmp_path)
        assert expect in str(error.value), str(error.value)


def test_the_template_declares_no_third_party_text(repo, project):
    """No legal interpretation ships with the template: no declaration,
    licence or attribution of its own (decision 14). A project's own
    declarations are its to make; there, they must at least load."""
    import third_party

    declarations = third_party.load(repo)
    if project.is_template():
        assert declarations == []


# ------------------------------------------------------------- T10


PUNNED = """
:requiresThing a owl:ObjectProperty ; rdfs:label "requires thing" ;
    skos:definition "An object property the planted case misuses." .
:note a owl:AnnotationProperty ; rdfs:label "note" ;
    skos:definition "An annotation property the planted case restricts on." .
:Thing a owl:Class ; rdfs:label "Thing" ;
    skos:definition "A material entity the planted case points at." ;
    rdfs:subClassOf obo:BFO_0000040 .
:Punning a owl:Class ; rdfs:label "Punning" ;
    skos:definition "A process related to a class by an object property." ;
    rdfs:subClassOf obo:BFO_0000015 ; :requiresThing :Thing .
:Annotated a owl:Class ; rdfs:label "Annotated" ;
    skos:definition "A process restricted on an annotation property." ;
    rdfs:subClassOf obo:BFO_0000015 ,
        [ a owl:Restriction ; owl:onProperty :note ;
          owl:someValuesFrom :Thing ] .
"""
CORRECTED = PUNNED.replace(
    "rdfs:subClassOf obo:BFO_0000015 ; :requiresThing :Thing .",
    "rdfs:subClassOf obo:BFO_0000015 , [ a owl:Restriction ; "
    "owl:onProperty :requiresThing ; owl:someValuesFrom :Thing ] .").replace(
    "owl:onProperty :note ;", "owl:onProperty :requiresThing ;")


def test_class_level_object_property_use_is_found(validator, findings_tool,
                                                  vendored, layout, project):
    """T10: an object property asserted from class to class, and a
    restriction on an annotation property, are violations; the same
    relations written as restrictions on an object property are not."""
    before = run(validator, vendored, layout, PUNNED, project,
                 "validation.realist")
    [punned] = on(before, project, "Punning", "by the object property")
    [restricted] = on(before, project, "Annotated",
                      "which is an annotation property")
    assert {punned["severity"], restricted["severity"]} == {"Violation"}
    assert project.namespace() + "requiresThing" in punned["message"]
    after = run(validator, vendored, layout, CORRECTED, project,
                "validation.realist")
    assert not on(after, project, "Punning", "by the object property")
    assert not on(after, project, "Annotated",
                  "which is an annotation property")
    accepted_then_fixed(findings_tool, as_findings(
        validator, findings_tool, "validation.realist",
        [punned, restricted]), [])


# ------------------------------------------------------------- T11


QUALIFIED = """
:Anchor a owl:Class ; rdfs:label "planning act (shared anchor)" ;
    skos:definition "A process the planted case labels with a qualifier." ;
    rdfs:subClassOf obo:BFO_0000015 .
:Child a owl:Class ; rdfs:label "child" ;
    skos:definition "A planning act that the planted case places under it." ;
    rdfs:subClassOf :Anchor .
:OtherChild a owl:Class ; rdfs:label "other child" ;
    skos:definition "A planning act placed beside the first." ;
    rdfs:subClassOf :Anchor .
"""


def test_genus_ignores_a_trailing_qualifier(validator, vendored, layout,
                                            project):
    """T11: a child whose definition names the parent without its
    qualifier is not reported; one whose definition names something else
    still is."""
    results = run(validator, vendored, layout, QUALIFIED, project,
                  "validation.realist")
    for child in ("Child", "OtherChild"):
        assert not on(results, project, child, "does not name its parent")
    vague = QUALIFIED.replace("A planning act that", "A process that")
    results = run(validator, vendored, layout, vague, project,
                  "validation.realist")
    assert on(results, project, "Child", "does not name its parent")


def test_the_qualifier_is_still_reported(validator, findings_tool, vendored,
                                         layout, project):
    """T11: the qualifier is the defect (BPO's B10), reported once, on
    the class whose label carries it, as a warning; moving it out of the
    label clears it."""
    results = run(validator, vendored, layout, QUALIFIED, project,
                  "validation.realist")
    [hit] = on(results, project, "Anchor", "ends in a parenthetical qualifier")
    assert hit["severity"] == "Warning"
    assert not [r for r in results
                if "parenthetical qualifier" in r["message"]
                and r is not hit]
    moved = QUALIFIED.replace('"planning act (shared anchor)"',
                              '"planning act" ; skos:altLabel '
                              '"planning act (shared anchor)"')
    results = run(validator, vendored, layout, moved, project,
                  "validation.realist")
    assert not [r for r in results if "parenthetical qualifier" in r["message"]]
    assert not on(results, project, "Child", "does not name its parent")
    accepted_then_fixed(findings_tool, as_findings(
        validator, findings_tool, "validation.realist", [hit]), [])


# ------------------------------------------------------------- T12


SCHEMED = """
:ShipmentProcess a owl:Class ; rdfs:label "Shipment process" ;
    skos:definition "A material entity misnamed as a process." ;
    rdfs:subClassOf obo:BFO_0000040 .
:DeliveryProcess a owl:Class ; rdfs:label "Delivery process" ;
    skos:definition "A process named as one." ;
    rdfs:subClassOf obo:BFO_0000015 .
:Q12 a owl:Class ; rdfs:label "Q twelve" ;
    skos:definition "A material entity carrying a code reserved for acts." ;
    rdfs:subClassOf obo:BFO_0000040 .
:Q13 a owl:Class ; rdfs:label "Q thirteen" ;
    skos:definition "A process carrying the reserved code." ;
    rdfs:subClassOf obo:BFO_0000015 .
"""
RULES = [
    {"id": "process-names", "pattern": "[A-Za-z]+Process",
     "must_sit_under": "http://purl.obolibrary.org/obo/BFO_0000015",
     "severity": "violation", "why": "A name ending Process names one."},
    {"id": "q-codes-are-not-material", "pattern": "Q[0-9]+",
     "must_not_sit_under": "http://purl.obolibrary.org/obo/BFO_0000040",
     "severity": "warning", "why": "A Q code names an act."},
]


def scheme_results(validator, vendored, text, project, rules=RULES):
    data = graph_of(text, project)
    for triple in vendored:
        data.add(triple)
    return validator.scheme_findings(data, rules)


def test_a_scheme_rule_finds_a_misplaced_term(validator, findings_tool,
                                              vendored, project):
    """T12: a must rule and a must-not rule, each finding the one term
    that breaks it and not the one that keeps it -- through the vendored
    hierarchy, so a class under a BFO category is placed by BFO."""
    results = scheme_results(validator, vendored, SCHEMED, project)
    by_rule = {(r["shape"], r["focus"].rsplit("#", 1)[-1], r["severity"])
               for r in results}
    assert by_rule == {("scheme:process-names", "ShipmentProcess",
                        "Violation"),
                       ("scheme:q-codes-are-not-material", "Q12", "Warning")}
    corrected = SCHEMED.replace(
        "misnamed as a process.\" ;\n    rdfs:subClassOf obo:BFO_0000040",
        "misnamed as a process.\" ;\n    rdfs:subClassOf obo:BFO_0000015"
    ).replace("reserved for acts.\" ;\n    rdfs:subClassOf obo:BFO_0000040",
              "reserved for acts.\" ;\n    rdfs:subClassOf obo:BFO_0000015")
    assert scheme_results(validator, vendored, corrected, project) == []
    accepted_then_fixed(findings_tool, as_findings(
        validator, findings_tool, "naming", results), [])


def test_no_scheme_rule_ships_enabled(validator, repo, project):
    """The template ships the mechanism, not BPO's rule. A project's own
    rules are its to write; there, they must at least load."""
    rules = validator.scheme_rules(repo)
    if project.is_template():
        assert rules == []


def test_a_scheme_rule_needs_exactly_one_side(validator, tmp_path):
    """Neither side, or both: a rule that says nothing, or contradicts
    itself, is refused rather than run."""
    (tmp_path / "config").mkdir()
    rule = ("scheme_rules:\n  - id: r\n    pattern: X\n    severity: warning\n"
            "    why: w\n")
    for sides in ("", "    must_sit_under: urn:a\n"
                      "    must_not_sit_under: urn:b\n"):
        (tmp_path / "config/naming.yaml").write_text(rule + sides,
                                                     encoding="utf-8")
        with pytest.raises(SystemExit) as error:
            validator.scheme_rules(tmp_path)
        assert "exactly one of" in str(error.value)


def test_scheme_findings_reach_the_register(validator, findings_tool):
    """Gated like every other finding, under `where: naming`."""
    record = {"rungs": {}, "modules": {"detail": []},
              "naming": {"detail": [{"focus": "urn:x", "shape": "scheme:r",
                                     "severity": "Violation",
                                     "message": "m"}]}}
    [finding] = validator.register_findings(record)
    assert (finding["where"], finding["rule"]) == ("naming", "scheme:r")
