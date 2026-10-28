# SPDX-License-Identifier: MIT
"""One term contract: what the site publishes is what the validator checks.

The BPO port found the two apart. The site refused a property with no
definition, or a term with two English labels, which the shapes -- written
for classes -- passed, so the ontology passed every check and failed at
deploy (T6). And the site read a term's text from the module declaring
it, so a definition that differed in another module was never shown, and
the conflict was hidden (T7).

So the site refuses nothing about the ontology's content. It publishes
each term with every variant of its text, notes what is wrong, and lists
the notes on the status page; the validator reports the same thing, and
a finding can be accepted in the register. These tests put one planted
corpus through both and require them to agree, in both directions.
"""

from __future__ import annotations

import ast
import json

import pytest

from conftest import load_tool

OBO = "http://purl.obolibrary.org/obo/"

PREFIXES = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
@prefix : <{ns}> .
"""

#: Four planted modules. Every term is in the project's namespace, as the
#: shapes' targets require; none is BPO's.
CORPUS = {
    "m_a.ttl": """
<urn:planted:a> a owl:Ontology ; dcterms:title "Planted A" .
:WellFormed a owl:Class ; rdfs:label "Well formed" ;
    skos:definition "A process that is well formed." ;
    rdfs:subClassOf obo:BFO_0000015 .
:NoDefinition a owl:Class ; rdfs:label "No definition" ;
    rdfs:subClassOf obo:BFO_0000015 .
:Unlabelled a owl:Class ; skos:definition "A process with no label." ;
    rdfs:subClassOf obo:BFO_0000015 .
:TwoEnglishLabels a owl:Class ; rdfs:label "First"@en, "Second"@en ;
    skos:definition "A process with two English labels."@en ;
    rdfs:subClassOf obo:BFO_0000015 .
:IriLabel a owl:Class ; rdfs:label :WellFormed ;
    skos:definition "A process labelled with a reference." ;
    rdfs:subClassOf obo:BFO_0000015 .
:IriDefinition a owl:Class ; rdfs:label "IRI definition" ;
    skos:definition :WellFormed ; rdfs:subClassOf obo:BFO_0000015 .
:undefinedProperty a owl:ObjectProperty ; rdfs:label "undefined property" .
:unlabelledProperty a owl:DatatypeProperty ;
    skos:definition "A property with no label." .
:twoLabelProperty a owl:AnnotationProperty ;
    rdfs:label "one"@en, "two"@en ; skos:definition "Two labels."@en .
:Drifted a owl:Class ; rdfs:label "Drifted" ;
    skos:definition "A process as module A defines it." ;
    rdfs:subClassOf obo:BFO_0000015 .
:Twice a owl:Class ; rdfs:label "Twice" ;
    skos:definition "A process declared in two modules." ;
    rdfs:subClassOf obo:BFO_0000015 .
:BothKinds a owl:Class ; rdfs:label "Both kinds" ;
    skos:definition "A process that is also a material entity." ;
    rdfs:subClassOf obo:BFO_0000015, obo:BFO_0000040 .
:Scheme a skos:ConceptScheme ; skos:prefLabel "Scheme" ;
    skos:hasTopConcept :TwoPrefLabels .
:TwoPrefLabels a skos:Concept ; skos:inScheme :Scheme ;
    skos:prefLabel "One"@en, "Other"@en .
""",
    # Not a declaration of :Drifted: an inlined copy of its text, as the
    # BPO port's slices carry their shared genera.
    "m_b.ttl": """
<urn:planted:b> a owl:Ontology ;
    dcterms:title "Planted B"@en, "Planted Bee"@en .
:Drifted skos:definition "A process as module B defines it." .
:Twice a owl:Class .
""",
    "m_c.ttl": """
:InHeaderless a owl:Class ; rdfs:label "In a headerless module" ;
    skos:definition "A process in a module with no header." ;
    rdfs:subClassOf obo:BFO_0000015 .
""",
    "m_d.ttl": """
<urn:planted:d1> a owl:Ontology ; dcterms:title "D one" .
<urn:planted:d2> a owl:Ontology ; dcterms:title "D two" .
""",
}

#: (term, what the site notes: kind and about, what the validator says).
TERM_CASES = [
    ("NoDefinition", ("missing", "skos:definition"),
     "Class has no skos:definition."),
    ("Unlabelled", ("missing", "rdfs:label"), "Class has no rdfs:label."),
    ("TwoEnglishLabels", ("conflict", "rdfs:label"),
     "carries two different"),
    ("IriLabel", ("not-literal", "rdfs:label"),
     "Class has an rdfs:label that is not a literal."),
    ("IriDefinition", ("not-literal", "skos:definition"),
     "Class has a skos:definition that is not a literal."),
    ("undefinedProperty", ("missing", "skos:definition"),
     "Property has no skos:definition."),
    ("unlabelledProperty", ("missing", "rdfs:label"),
     "Property has no rdfs:label."),
    ("twoLabelProperty", ("conflict", "rdfs:label"),
     "carries two different"),
    ("Drifted", ("conflict", "skos:definition"), "carries two different"),
    ("Twice", ("declared-twice", "declaration"), "is declared in 2 modules"),
    ("BothKinds", ("categories", "category"), "which are declared disjoint"),
]

#: (concept, what the vocabulary page shows, what the validator says).
CONCEPT_CASES = [
    ("TwoPrefLabels", "One / Other (conflicting labels)",
     "carries two different skos:prefLabel values"),
]

#: (focus, the validator's module rule). The site lists these from the
#: validator's own module check.
MODULE_CASES = [
    ("urn:planted:b", "module:header-drift"),
    ("m_c.ttl", "module:one-header"),
    ("m_d.ttl", "module:one-header"),
]

#: What, of the validator's findings, is the term contract: the rest
#: (genus wording, definition sources, two parents) the site does not
#: depend on.
CONTRACT_RUNGS = ("validation.wellformedness", "modules")
CONTRACT_REALIST = "which are declared disjoint"


@pytest.fixture(scope="module")
def builder():
    return load_tool("tc_build_site", "tools/site/build_site.py")


@pytest.fixture(scope="module")
def validator():
    return load_tool("tc_validate", "tools/ontology/validate.py")


@pytest.fixture(scope="module")
def planted(tmp_path_factory, project):
    root = tmp_path_factory.mktemp("planted")
    header = PREFIXES.replace("{ns}", project.namespace())
    paths = []
    for name, body in CORPUS.items():
        path = root / name
        path.write_bytes((header + body).encode("utf-8"))
        paths.append(path)
    return paths


@pytest.fixture(scope="module")
def ladder(validator, planted):
    """The validator's findings on the planted corpus, as the register
    identifies them."""
    mp = pytest.MonkeyPatch()
    mp.setattr(validator.layout, "ontology_files", lambda: list(planted))
    try:
        record = validator.measure()
    finally:
        mp.undo()
    return record, validator.register_findings(record)


@pytest.fixture(scope="module")
def site(builder, validator, planted, layout):
    """What the site would publish from the planted corpus: its term
    records, its module headers, and its status-page table."""
    import rdflib

    sources = []
    for path in planted:
        graph = rdflib.Graph()
        graph.parse(path, format="turtle")
        sources.append({"key": path.stem, "path": "ontology/" + path.name,
                        "graph": graph, "origin": "authored", "file": path})
    merged = rdflib.Graph()
    for path in layout.vendored_files():
        merged.parse(path, format="turtle")
    for source in sources:
        for triple in source["graph"]:
            merged.add(triple)
    known = builder.prefixes()
    records = builder.term_records(sources, merged, known)
    headers = {s["key"]: builder.ontology_header(s["graph"], s["path"])
               for s in sources}
    modules = validator.module_findings(
        [(s["file"], s["graph"]) for s in sources])
    table = builder.published_findings_section(records, modules, known)
    authored = rdflib.Graph()
    for source in sources:
        for triple in source["graph"]:
            authored.add(triple)
    return {"records": {r["iri"]: r for r in records}, "headers": headers,
            "modules": modules, "table": table,
            "schemes": builder.scheme_trees(authored, known)}


def found_on(findings, focus):
    return [f for f in findings if f["focus"] == focus]


def message_of(finding, record):
    """The finding's message, which the register stores as a digest."""
    for rung in record["rungs"].values():
        corpus = rung["corpus"]
        for result in (corpus["detail"] + corpus["warning_detail"]):
            if (result["focus"], result["shape"]) == (finding["focus"],
                                                      finding["rule"]):
                yield result["message"]
    for result in record["modules"]["detail"]:
        if (result["focus"], result["shape"]) == (finding["focus"],
                                                  finding["rule"]):
            yield result["message"]


# ------------------------------------------------------------- T6


#: Every function in the site build that may refuse, and what stops its
#: input before a deploy. None of them reads the ontology's content.
SITE_REFUSALS = {
    "git": "the Checks step that builds the site (full history)",
    "source_bytes": "test_the_index_is_lf_throughout, and the site step",
    "fill": "test_an_unfilled_placeholder_stops_the_build, and the site step",
    "gather": "vendor_upstream.py (a vendored file no pin produces); one "
              "specification in the layout contract",
    "build": "test_a_fragment_no_navigation_names_stops_the_build and "
             "test_an_asset_with_no_rule_stops_the_build, and the site step",
    "clear_output": "the output directory, not the repository",
}

#: The functions that read the ontology for the term index and the
#: module pages. They must not refuse.
TERM_INDEX = ("text_variants", "published_text", "category_of",
              "term_records", "ontology_header",
              "published_findings_section", "scheme_trees")


def test_every_site_refusal_is_a_ladder_finding(site, ladder, project):
    """T6. One planted case per rule the site once refused on -- a
    definition missing, two values in one language, a label or
    definition that is not text, a term declared twice, two unrelated
    categories, a module with no header or two -- each run through the
    site and the validator. The site publishes it, noted; the validator
    finds it. A property without a definition and a class with two
    English labels are among them."""
    record, findings = ladder
    ns = project.namespace()
    for name, (kind, about), says in TERM_CASES:
        published = site["records"].get(ns + name)
        assert published, "%s was not published" % name
        assert [n for n in published["notes"]
                if (n["kind"], n["about"]) == (kind, about)], (
            "the site published %s without noting %s %s: %s"
            % (name, kind, about, published["notes"]))
        messages = [m for f in found_on(findings, ns + name)
                    for m in message_of(f, record)]
        assert [m for m in messages if says in m], (
            "the validator did not find %s on %s: %s" % (says, name, messages))
        assert published["id"] in site["table"], name

    for name, shown, says in CONCEPT_CASES:
        assert shown in site["schemes"], (name, site["schemes"][:400])
        messages = [m for f in found_on(findings, ns + name)
                    for m in message_of(f, record)]
        assert [m for m in messages if says in m], (name, messages)

    for focus, rule in MODULE_CASES:
        matched = [f for f in findings if f["rule"] == rule
                   and f["focus"].endswith(focus)]
        assert matched, (focus, rule)
        assert focus in site["table"], focus
    assert site["headers"]["m_c"]["iri"] == ""
    assert site["headers"]["m_d"]["iri"] == "urn:planted:d1 / urn:planted:d2"
    assert site["headers"]["m_b"]["title"] == "Planted B / Planted Bee"


def test_what_the_validator_finds_the_site_marks(site, ladder, project):
    """The reverse: every term-contract finding the validator makes on
    the planted corpus is noted on the published term, or listed as a
    module finding. A site that marked a subset would pass the test
    above."""
    record, findings = ladder
    ns = project.namespace()
    contract = []
    for finding in findings:
        messages = list(message_of(finding, record))
        if finding["where"] in CONTRACT_RUNGS or any(
                CONTRACT_REALIST in m for m in messages):
            contract.append(finding)
    assert len(contract) >= len(TERM_CASES) + len(MODULE_CASES)
    module_foci = {m["focus"] for m in site["modules"]}
    for finding in contract:
        focus = finding["focus"]
        if focus in site["records"]:
            assert site["records"][focus]["notes"], focus
        elif focus.startswith(ns):
            # A concept: published on the vocabulary page, marked there.
            assert "(conflicting labels)" in site["schemes"], focus
        else:
            assert focus in module_foci, focus


def test_a_well_formed_term_is_neither_noted_nor_found(site, ladder,
                                                       project):
    """Guards both tests above: a site that noted every term, or a
    validator that found every term, would pass them."""
    record, findings = ladder
    iri = project.namespace() + "WellFormed"
    assert site["records"][iri]["notes"] == []
    assert not [f for f in found_on(findings, iri)
                if f["where"] in CONTRACT_RUNGS]


def test_the_site_refuses_only_its_own_inputs(repo):
    """Read from the build's source: the functions that may refuse are
    the listed ones, each with what stops its input before a deploy, and
    none of the term index's functions is among them."""
    tree = ast.parse((repo / "tools/site/build_site.py")
                     .read_text(encoding="utf-8"))
    refusing = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Raise) and inner.exc is not None
                        and isinstance(inner.exc, ast.Call)
                        and getattr(inner.exc.func, "id", "") == "Refused"):
                    refusing.add(node.name)
    assert refusing == set(SITE_REFUSALS), refusing ^ set(SITE_REFUSALS)
    assert not refusing & set(TERM_INDEX)


def test_the_checks_job_builds_the_site(repo):
    """What the build refuses fails in Checks, before the Pages job."""
    import yaml

    workflow = yaml.safe_load((repo / ".github/workflows/checks.yml")
                              .read_text(encoding="utf-8"))
    steps = workflow["jobs"]["checks"]["steps"]
    [step] = [s for s in steps if s.get("id") == "site"]
    assert "tools/site/build_site.py -o" in step["run"]
    assert "tools/site/check_site.py" in step["run"]
    assert step.get("continue-on-error") is True


# ------------------------------------------------------------- T7


def test_a_drifted_term_shows_every_variant(site, project):
    """T7, on a planted two-module drift: both definitions, each with
    its module, both in the published text, and a note."""
    drifted = site["records"][project.namespace() + "Drifted"]
    variants = drifted["variants"]["definition"]
    assert [(v["value"], v["modules"]) for v in variants] == [
        ("A process as module A defines it.", ["m_a"]),
        ("A process as module B defines it.", ["m_b"])]
    for variant in variants:
        assert variant["value"] in drifted["definition"]
    [note] = [n for n in drifted["notes"] if n["kind"] == "conflict"]
    assert "m_a, m_b" in note["text"]
    assert drifted["declared_in"] == ["m_a"]


def concealing_site(tmp_path, records, status):
    out = tmp_path / "_site"
    (out / "status").mkdir(parents=True)
    (out / "status/index.html").write_text(status, encoding="utf-8")
    return out, records


def test_the_checker_refuses_a_concealed_conflict(site, project, tmp_path):
    """The site checker holds the published index to it: a conflict
    shown as one of its variants, or with no note, or missing from the
    status page, each fails."""
    import copy

    checker = load_tool("tc_check_site", "tools/site/check_site.py")
    drifted = site["records"][project.namespace() + "Drifted"]
    out, _ = concealing_site(tmp_path, None, site["table"])
    assert checker.check_nothing_concealed(out, [drifted]) == []

    picked = copy.deepcopy(drifted)
    picked["definition"] = picked["variants"]["definition"][0]["value"]
    unnoted = copy.deepcopy(drifted)
    unnoted["notes"] = [n for n in unnoted["notes"]
                        if n["kind"] != "conflict"]
    for damaged, says in ((picked, "not all of them"),
                          (unnoted, "no note says so")):
        problems = checker.check_nothing_concealed(out, [damaged])
        assert [p for p in problems if says in p], problems
    (out / "status/index.html").write_text("<p>nothing</p>",
                                           encoding="utf-8")
    problems = checker.check_nothing_concealed(out, [drifted])
    assert [p for p in problems if "status page does not list" in p]


def test_accepted_findings_are_published_with_the_term(builder):
    """A finding the register accepts is shown on its term with the
    reason, owner and review date: accepting a finding does not hide it."""
    entry = {"check": "validate", "where": "validation.wellformedness",
             "focus": "urn:x", "rule": "urn:shape", "digest": "0" * 16,
             "severity": "Violation", "text": "Class has no definition.",
             "reason": "planted", "owner": "nobody",
             "review": "2099-01-01"}
    records = [{"iri": "urn:x"}, {"iri": "urn:y"}]
    builder.attach_accepted(records, [entry])
    assert records[0]["accepted"][0]["reason"] == "planted"
    assert records[0]["accepted"][0]["text"] == "Class has no definition."
    assert "digest" not in records[0]["accepted"][0]
    assert records[1]["accepted"] == []


def test_the_explorer_shows_variants_notes_and_accepted_findings(repo):
    """The explorer is where a reader meets a term; the index fields the
    tests above check are only worth anything if it renders them."""
    script = (repo / "site/src/assets/js/explorer.js").read_text(
        encoding="utf-8")
    for field in ("record.variants[field].forEach", "record.notes.forEach",
                  "record.accepted.forEach", "record.declared_in.join"):
        assert field in script, field

