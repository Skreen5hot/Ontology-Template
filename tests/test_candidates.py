# SPDX-License-Identifier: MIT
"""Review candidates (backlog item 12, template decisions 34 and 35).

Each rule has a planted case it must report and a near miss it must not,
built on the vendored BFO and CCO, so the upstream half of every chain is
the real one. The four WP6 defects (analysis section 3.3) are the
positives, rewritten as synthetic terms: no BPO text is here.
"""

from __future__ import annotations

import socket

import pytest

from conftest import load_tool

CCO = "https://www.commoncoreontologies.org/"
OBO = "http://purl.obolibrary.org/obo/"
MATERIAL_ARTIFACT = CCO + "ont00000995"
INFORMATION_CONTENT = CCO + "ont00000958"
PARTICIPATES_IN = OBO + "BFO_0000056"
PROCESS = OBO + "BFO_0000015"


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_candidates", "tools/ontology/candidates.py")


@pytest.fixture(scope="module")
def upstream(tool, repo):
    return tool.upstream(repo)


@pytest.fixture(scope="module")
def ns(project):
    return project.namespace()


def turtle(ns: str, body: str) -> str:
    return """@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl:  <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix cco:  <%s> .
@prefix obo:  <%s> .
@prefix ex:   <%s> .
""" % (CCO, OBO, ns) + body


def build(tool, upstream, ns, *modules):
    import rdflib

    graphs = []
    for i, body in enumerate(modules):
        graph = rdflib.Graph()
        graph.parse(data=turtle(ns, body), format="turtle")
        graphs.append(("m%d.ttl" % (i + 1), graph))
    labels, parents, disjoint = upstream
    return tool.Corpus(graphs, ns, labels, parents, disjoint)


def found(tool, upstream, ns, *modules, rule=None, **settings):
    corpus = build(tool, upstream, ns, *modules)
    out = tool.generate(corpus, dict(tool.DEFAULTS, **settings))
    return [c for c in out if rule is None or c["rule"] == rule]


SOFTWARE = """
ex:Software a owl:Class ; rdfs:label "software"@en ;
    rdfs:subClassOf cco:ont00000958 ;
    skos:definition "An information content entity that prescribes a computation."@en .
"""


# ------------------------------------------------------- over-claiming


def test_necessity_without_an_axiom_is_a_candidate(tool, upstream, ns):
    got = found(tool, upstream, ns, """
ex:Pump a owl:Class ; rdfs:label "pump"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that requires a power source."@en .
""", rule="necessity-without-axiom")
    assert [c["about"] for c in got] == [[ns + "Pump"]]
    assert got[0]["evidence"]["words"] == ["requires"]


def test_necessity_with_an_existential_axiom_is_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:Pump a owl:Class ; rdfs:label "pump"@en ;
    rdfs:subClassOf cco:ont00000995 , [ a owl:Restriction ;
        owl:onProperty obo:BFO_0000056 ; owl:someValuesFrom obo:BFO_0000015 ] ;
    skos:definition "A material artifact that requires a power source."@en .
""", rule="necessity-without-axiom")


def test_a_definition_without_necessity_wording_is_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:Pump a owl:Class ; rdfs:label "pump"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact designed to move fluid."@en .
""", rule="necessity-without-axiom")


def test_the_word_list_is_the_projects(tool, upstream, ns):
    body = """
ex:Pump a owl:Class ; rdfs:label "pump"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that needs a power source."@en .
"""
    assert not found(tool, upstream, ns, body, rule="necessity-without-axiom")
    assert found(tool, upstream, ns, body, rule="necessity-without-axiom",
                 necessity_words=["needs"])


def test_necessity_words_are_whole_words(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:Sauce a owl:Class ; rdfs:label "sauce"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact made with mustard and everyday spices."@en .
""", rule="necessity-without-axiom")


def test_an_inverse_with_necessity_wording_is_a_candidate(tool, upstream,
                                                          ns):
    got = found(tool, upstream, ns, """
ex:dispatches a owl:ObjectProperty ; rdfs:label "dispatches"@en ;
    owl:inverseOf ex:isDispatchedBy ;
    skos:definition "A relation in which every capability must be dispatched."@en .
ex:isDispatchedBy a owl:ObjectProperty ; rdfs:label "is dispatched by"@en ;
    skos:definition "The inverse of dispatches."@en .
""", rule="inverse-necessity")
    assert [c["about"] for c in got] == [[ns + "dispatches"]]
    assert got[0]["evidence"]["inverse_of"] == [ns + "isDispatchedBy"]


def test_an_inverse_declared_from_the_other_side_counts(tool, upstream, ns):
    got = found(tool, upstream, ns, """
ex:dispatches a owl:ObjectProperty ; rdfs:label "dispatches"@en ;
    skos:definition "A relation in which every capability must be dispatched."@en .
ex:isDispatchedBy a owl:ObjectProperty ; rdfs:label "is dispatched by"@en ;
    owl:inverseOf ex:dispatches ;
    skos:definition "The inverse of dispatches."@en .
""", rule="inverse-necessity")
    assert [c["about"] for c in got] == [[ns + "dispatches"]]


def test_a_property_without_an_inverse_is_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:dispatches a owl:ObjectProperty ; rdfs:label "dispatches"@en ;
    skos:definition "A relation in which every capability must be dispatched."@en .
""", rule="inverse-necessity")


# ------------------------------------------------------------- homonym


def test_one_iri_with_two_genera_across_modules(tool, upstream, ns):
    got = found(tool, upstream, ns, """
ex:Unit a owl:Class ; rdfs:label "unit"@en ;
    skos:definition "An agent that performs work for an organization."@en .
""", """
ex:Unit a owl:Class ;
    skos:definition "A process that delivers a measured amount of work."@en .
""", rule="genus-differs")
    assert [c["about"] for c in got] == [[ns + "Unit"]]
    genera = sorted(r["genus"] for r in got[0]["evidence"]["definitions"])
    assert genera == ["agent", "process"]
    assert {r["module"] for r in got[0]["evidence"]["definitions"]} == {
        "m1.ttl", "m2.ttl"}


def test_one_iri_with_one_genus_twice_is_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:Unit a owl:Class ; rdfs:label "unit"@en ;
    skos:definition "An agent that performs work for an organization."@en .
""", """
ex:Unit a owl:Class ;
    skos:definition "An agent that acts on behalf of an organization."@en .
""", rule="genus-differs")


def test_one_iri_edited_in_one_module_is_a_candidate(tool, upstream, ns):
    """The commonest drift: a term copied into two modules keeps its genus
    and changes its meaning."""
    body = """
ex:Profile a owl:Class ; rdfs:label "profile"@en ;
    skos:definition "An agent that describes a group of customers."@en .
"""
    got = found(tool, upstream, ns, body, body.replace(
        "a group of customers", "one customer's service requirements"),
        rule="definitions-differ")
    assert [c["about"] for c in got] == [[ns + "Profile"]]
    assert not found(tool, upstream, ns, body, body,
                     rule="definitions-differ"), "the same text twice"


def test_two_genera_are_genus_differs_not_definitions_differ(tool,
                                                             upstream, ns):
    got = found(tool, upstream, ns, """
ex:Unit a owl:Class ; rdfs:label "unit"@en ;
    skos:definition "An agent that performs work for an organization."@en .
""", """
ex:Unit a owl:Class ;
    skos:definition "A process that delivers a measured amount of work."@en .
""")
    assert {c["rule"] for c in got} == {"genus-differs"}


def test_an_unknown_genus_is_read_up_to_its_differentia(tool, upstream, ns):
    corpus = build(tool, upstream, ns, "")
    assert tool.genus(corpus, "A widget housing, which holds parts.")[0] \
        == "widget housing"
    assert tool.genus(corpus, "An agent that acts.")[0] == "agent"
    assert tool.genus(corpus, "A material artifact used for pumping water.")[
        0] == "material artifact", "a known label, not the words up to 'that'"


# ----------------------------------------------------------- duplicate


def test_two_classes_with_one_label_are_a_candidate(tool, upstream, ns):
    got = found(tool, upstream, ns, """
ex:Invoice a owl:Class ; rdfs:label "invoice"@en ;
    skos:definition "A document that requests payment."@en .
ex:Bill a owl:Class ; rdfs:label "Invoice (billing)"@en ;
    skos:definition "A statement of charges owed."@en .
""", rule="near-duplicate")
    assert [c["about"] for c in got] == [sorted([ns + "Bill",
                                                 ns + "Invoice"])]
    assert got[0]["evidence"]["same_label"] == "invoice"


def test_two_definitions_that_mostly_coincide_are_a_candidate(tool,
                                                              upstream, ns):
    got = found(tool, upstream, ns, """
ex:Invoice a owl:Class ; rdfs:label "invoice"@en ;
    skos:definition "A document issued by a seller requesting payment for goods delivered."@en .
ex:Bill a owl:Class ; rdfs:label "bill"@en ;
    skos:definition "A document issued by a seller requesting payment for goods delivered to a buyer."@en .
""", rule="near-duplicate")
    assert len(got) == 1 and got[0]["evidence"]["overlap"] >= 0.8


def test_different_definitions_are_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:Invoice a owl:Class ; rdfs:label "invoice"@en ;
    skos:definition "A document issued by a seller requesting payment for goods delivered."@en .
ex:Receipt a owl:Class ; rdfs:label "receipt"@en ;
    skos:definition "A document acknowledging that a payment has been received in full."@en .
""", rule="near-duplicate")


def test_a_class_with_an_upstream_label_is_a_candidate(tool, upstream,
                                                       ns):
    got = found(tool, upstream, ns, """
ex:Facility a owl:Class ; rdfs:label "Facility"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that houses operations."@en .
""", rule="near-duplicate")
    assert [c["about"] for c in got] == [sorted([ns + "Facility",
                                                 CCO + "ont00000192"])]
    assert got[0]["evidence"]["upstream"] == CCO + "ont00000192"
    assert not found(tool, upstream, ns, """
ex:Depot a owl:Class ; rdfs:label "storage depot"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that houses stock."@en .
""", rule="near-duplicate")


def test_short_definitions_are_not_compared(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:A a owl:Class ; rdfs:label "a thing"@en ; skos:definition "A pump."@en .
ex:B a owl:Class ; rdfs:label "b thing"@en ; skos:definition "A pump."@en .
""", rule="near-duplicate")


# ---------------------------------------------------- misclassification


def test_a_disjoint_category_in_the_differentia_is_a_candidate(tool,
                                                               upstream, ns):
    """WP6's case: a material artifact defined to include software, an
    information content entity, which BFO puts under a category disjoint
    from material entity's."""
    got = found(tool, upstream, ns, SOFTWARE + """
ex:Terminal a owl:Class ; rdfs:label "terminal"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that includes software for taking orders."@en .
""", rule="category-in-differentia")
    assert [c["about"] for c in got] == [sorted([ns + "Software",
                                                 ns + "Terminal"])]
    evidence = got[0]["evidence"]
    assert evidence["mention"] == "software"
    assert evidence["disjoint_with"] == OBO + "BFO_0000031"


def test_a_relation_to_a_disjoint_category_is_not(tool, upstream, ns):
    """'Used in software development' relates the class to software; it
    does not say the class is or includes software."""
    assert not found(tool, upstream, ns, SOFTWARE + """
ex:Bench a owl:Class ; rdfs:label "bench"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact used in testing software."@en .
""", rule="category-in-differentia")


def test_a_constitution_from_a_compatible_category_is_not(tool, upstream,
                                                          ns):
    assert not found(tool, upstream, ns, """
ex:Campus a owl:Class ; rdfs:label "campus"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that includes a facility and grounds."@en .
""", rule="category-in-differentia")


def test_an_unread_genus_does_not_hide_a_constitution(tool, upstream, ns):
    """With no known label opening it, the genus is read as the first few
    words, which here run into the differentia."""
    got = found(tool, upstream, ns, SOFTWARE + """
ex:Kiosk a owl:Class ; rdfs:label "kiosk"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A self service unit comprising software for orders."@en .
""", rule="category-in-differentia")
    assert [c["about"] for c in got] == [sorted([ns + "Kiosk",
                                                 ns + "Software"])]


def test_is_also_is_a_constitution(tool, upstream, ns):
    got = found(tool, upstream, ns, SOFTWARE + """
ex:Appliance a owl:Class ; rdfs:label "appliance"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that is also a software for billing."@en .
""", rule="category-in-differentia")
    assert [c["about"] for c in got] == [sorted([ns + "Appliance",
                                                 ns + "Software"])]


def test_a_wrong_genus_is_left_to_the_genus_check(tool, upstream, ns):
    """A definition whose genus is a disjoint class is already a genus
    warning; this rule reads the differentia only, so it is not listed
    twice."""
    assert not found(tool, upstream, ns, SOFTWARE + """
ex:Terminal a owl:Class ; rdfs:label "terminal"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "Software that takes orders at a counter."@en .
""", rule="category-in-differentia")


def test_a_mention_an_axiom_accounts_for_is_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, SOFTWARE + """
ex:Terminal a owl:Class ; rdfs:label "terminal"@en ;
    rdfs:subClassOf cco:ont00000995 , [ a owl:Restriction ;
        owl:onProperty ex:bears ; owl:someValuesFrom ex:Software ] ;
    skos:definition "A material artifact that includes software for taking orders."@en .
""", rule="category-in-differentia")


def test_a_process_with_its_participation_axiom_is_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:Pump a owl:Class ; rdfs:label "pump"@en ;
    rdfs:subClassOf cco:ont00000995 , [ a owl:Restriction ;
        owl:onProperty obo:BFO_0000056 ; owl:someValuesFrom obo:BFO_0000015 ] ;
    skos:definition "A material artifact that participates in a process of pumping."@en .
""", rule="category-in-differentia")


def test_a_mention_from_a_compatible_category_is_not(tool, upstream, ns):
    assert not found(tool, upstream, ns, """
ex:Rack a owl:Class ; rdfs:label "rack"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that holds another material artifact in a facility."@en .
""", rule="category-in-differentia")


# ------------------------------------------------------ the whole tool


def test_identity_is_the_rule_and_the_iris_never_the_message(tool):
    one = tool.candidate("near-duplicate", ["urn:b", "urn:a"], "first",
                         {})
    two = dict(one, message="reworded entirely")
    assert tool.identity(one) == tool.identity(two) == (
        "near-duplicate", ("urn:a", "urn:b"))


def test_the_same_corpus_gives_the_same_candidates(tool, upstream, ns):
    body = SOFTWARE + """
ex:Terminal a owl:Class ; rdfs:label "terminal"@en ;
    rdfs:subClassOf cco:ont00000995 ;
    skos:definition "A material artifact that requires software."@en .
"""
    assert found(tool, upstream, ns, body) == found(tool, upstream, ns, body)


def test_it_reads_the_repository_offline(tool, repo, monkeypatch, capsys):
    """CI runs it with no network and no credentials: every input is a
    file in the repository."""
    def refuse(*args, **kwargs):
        raise AssertionError("candidates.py opened a network connection")
    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
    assert tool.main([]) == 0
    assert "candidate(s)" in capsys.readouterr().out


def test_the_settings_are_checked(tool, tmp_path):
    (tmp_path / "config").mkdir()
    path = tmp_path / "config/candidates.yaml"
    path.write_text("version: 1\nduplicate_overlap: 1.5\n", encoding="utf-8")
    with pytest.raises(tool.Unreadable, match="duplicate_overlap"):
        tool.configuration(tmp_path)
    path.write_text("version: 1\nloosen: true\n", encoding="utf-8")
    with pytest.raises(tool.Unreadable, match="unknown setting"):
        tool.configuration(tmp_path)


def test_the_shipped_settings_are_the_defaults(tool, repo):
    assert tool.configuration(repo) == tool.DEFAULTS
