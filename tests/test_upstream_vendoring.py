# SPDX-License-Identifier: MIT
"""The vendored extracts, and whether they earn their place.

Two questions, and the second is the one worth asking.

  Is the vendoring correct?   Every upstream term this repository names is
                              described, nothing dangles, the digests
                              match, and every triple sits in the extract
                              of the file it came from.

  Is it load-bearing?         BFO is vendored whole so that a shape can
                              ask a realist question -- does this class
                              reach entity, does it sit under two disjoint
                              categories -- of a term no module names. If
                              the BFO extract stopped carrying the whole
                              hierarchy, those questions would answer "no"
                              for the scope rather than for the ontology.

None of these tests need the network. Rebuilding from upstream does, and
that is a separate mode of the tool -- see `--confirm`, which is what
shows these files are derived from the pins rather than hand-edited.

Owned by the ontology template. A project that pins a sister ontology
beside BFO and CCO keeps passing: the tests derive the set of sources
from the pins, and require only that BFO and CCO are among them.
"""

from __future__ import annotations

import pytest

from conftest import load_tool

OBO = "http://purl.obolibrary.org/obo/"
ENTITY = OBO + "BFO_0000001"
CONTINUANT = OBO + "BFO_0000002"
OCCURRENT = OBO + "BFO_0000003"
PROCESS = OBO + "BFO_0000015"
MATERIAL_ENTITY = OBO + "BFO_0000040"
ORGANIZATION = "https://www.commoncoreontologies.org/ont00001180"

RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"


@pytest.fixture(scope="module")
def vendoring():
    return load_tool("t_vendor", "tools/ontology/vendor_upstream.py")


@pytest.fixture(scope="module")
def report(vendoring):
    return vendoring.verify()


@pytest.fixture(scope="module")
def manifest(vendoring):
    import json

    root = vendoring.layout.repository_root()
    return json.loads((root / vendoring.MANIFEST).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def extracts(layout):
    """The vendored extracts as one graph."""
    import rdflib

    graph = rdflib.Graph()
    for path in layout.vendored_files():
        graph.parse(path, format="turtle")
    return graph


def extract(layout, component_id):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(layout.path(component_id), format="turtle")
    return graph


def constructed_upstreams(vendoring, monkeypatch, upstreams, seeds):
    """Pins and bytes built here, so `build` runs without the network.

    `upstreams` is [(id, namespace, select, turtle)]. Afterwards
    `vendoring.build(tmp)` builds from these.
    """
    licence = "<http://purl.org/dc/terms/license>"
    pins = []
    for key, namespace, select, text in upstreams:
        # The licence statement's subject is outside every pinned
        # namespace, so it is never selected as one of the source's terms.
        text += "<https://licence.invalid/%s> %s \"licence-%s\" .\n" % (
            key, licence, key.upper())
        pins.append({
            "id": key, "project": key.upper(), "release": "r",
            "commit": "c0ffee", "url": "https://u.invalid/c0ffee/" + key,
            "sha256": key, "namespace": namespace, "prefix": key,
            "select": select,
            "extract": "vendor/%s.ttl" % key, "_text": text,
            "licence": {"spdx": "MIT", "url": "https://l.invalid/",
                        "licence_statement_contains": "licence-" + key.upper(),
                        "attribution": key}})
    monkeypatch.setattr(vendoring, "sources", lambda: pins)
    monkeypatch.setattr(vendoring, "fetch",
                        lambda source, cache: source["_text"].encode("utf-8"))
    monkeypatch.setattr(vendoring, "seed_terms", lambda namespaces: set(seeds))
    monkeypatch.setattr(vendoring, "spec_terms", lambda: set())


def parsed(text):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(data=text, format="turtle")
    return graph


# ------------------------------------------------------------- pinning


def test_every_url_names_the_commit_it_pins(vendoring):
    """A tag can be moved to a different commit; a commit cannot.

    Includes any licence statement url, which is read for the licence
    and would otherwise be read from whatever that url serves today.
    """
    for entry in vendoring.sources():
        assert entry["commit"] in entry["url"], entry["id"]
        statement = entry["licence"].get("statement_url")
        if statement:
            assert entry["commit"] in statement, entry["id"]


def test_a_licence_statement_off_the_pinned_commit_is_refused(
        vendoring, monkeypatch):
    """Falsifies the check above in the tool rather than in this file.

    The template pins no source with a separate licence statement, so
    one is constructed: the first pin, given a statement url on `main`."""
    real = vendoring.sources()
    tampered = [dict(entry, licence=dict(entry["licence"]))
                for entry in real]
    first = tampered[0]
    first["licence"]["statement_url"] = (
        "https://raw.githubusercontent.com/o/r/main/LICENSE")
    first["licence"]["statement_sha256"] = "0" * 64
    assert first["commit"] not in first["licence"]["statement_url"]

    import yaml

    monkeypatch.setattr(yaml, "safe_load", lambda _text: {"sources": tampered})
    with pytest.raises(SystemExit) as error:
        vendoring.sources()
    assert "does not name the pinned commit" in str(error.value)


def test_an_unknown_select_mode_is_refused(vendoring, monkeypatch):
    real = vendoring.sources()
    tampered = [dict(entry) for entry in real]
    tampered[0]["select"] = "everything"

    import yaml

    monkeypatch.setattr(yaml, "safe_load", lambda _text: {"sources": tampered})
    with pytest.raises(SystemExit) as error:
        vendoring.sources()
    assert "the modes are" in str(error.value)


def test_the_recorded_digest_is_what_the_extract_digests_to(report):
    assert report["ok"], report["findings"]


def test_the_manifest_records_a_source_digest_for_every_extract(vendoring,
                                                                manifest):
    pinned = {entry["id"]: entry for entry in vendoring.sources()}
    assert set(manifest["extracts"]) == set(pinned)
    assert {"bfo", "cco"} <= set(pinned), (
        "BFO and CCO are the foundation every project made from the "
        "template is aligned to; one of them is no longer pinned")
    for key, record in manifest["extracts"].items():
        assert record["source_sha256"] == pinned[key]["sha256"], key
        assert record["commit"] == pinned[key]["commit"], key
        assert record["select"] == pinned[key]["select"], key


def test_the_extract_headers_name_this_project(layout, project):
    """The extracts' owl:Ontology IRIs live under the project, which is
    why init regenerates them. One left under another project's IRI base
    would be a file claiming to be somebody else's extract -- and exactly
    one header, because the upstream's own is not a term and is left out.
    """
    import rdflib

    for path in layout.vendored_files():
        graph = rdflib.Graph()
        graph.parse(path, format="turtle")
        headers = [str(s) for s in graph.subjects(
            rdflib.RDF.type, rdflib.URIRef(OWL + "Ontology"))]
        assert headers == [project.iri_base() + "/vendor/" + path.stem], (
            path.name, headers)


# ------------------------------------------------------- completeness


def test_every_upstream_term_named_here_is_described(report):
    """The check that catches the corpus growing past the extract. A new
    cco: reference lands as a term nothing describes, and a shape
    walking through it silently answers "no" for every subject."""
    assert report["unresolved_seeds"] == [], report["unresolved_seeds"]


def test_the_extracts_reference_nothing_they_do_not_describe(report):
    """Closure. An extract that mentions an upstream term it does not
    carry has the same defect as the corpus would, one level down."""
    assert report["dangling_references"] == [], report["dangling_references"]


def test_a_term_that_is_not_vendored_is_reported_rather_than_ignored(
        vendoring, monkeypatch):
    """Falsifies the completeness check.

    Both assertions above pass when nothing is missing and would also
    pass if the check looked at the wrong thing. Adding one term nobody
    vendored has to produce a finding.
    """
    real = vendoring.seed_terms
    invented = "https://www.commoncoreontologies.org/ont00000000"

    monkeypatch.setattr(vendoring, "seed_terms",
                        lambda namespaces: real(namespaces) | {invented})
    record = vendoring.verify()
    assert invented in record["unresolved_seeds"], record
    assert not record["ok"]


def test_a_readable_cco_name_is_a_term_nothing_describes(vendoring,
                                                         monkeypatch):
    """The mistake an author -- or an agent -- makes most: CCO v2 IRIs
    are opaque, and `cco:Organization` parses as an IRI and names
    nothing. Until the IRI linter exists, this is what catches it."""
    real = vendoring.seed_terms
    readable = "https://www.commoncoreontologies.org/Organization"

    monkeypatch.setattr(vendoring, "seed_terms",
                        lambda namespaces: real(namespaces) | {readable})
    record = vendoring.verify()
    assert readable in record["unresolved_seeds"], record


def test_a_new_spec_term_fails_until_the_extracts_are_rebuilt(
        vendoring, monkeypatch):
    """A specification is a seed source, so one naming a new CCO class
    must fail offline verification -- that failure is the moment
    somebody rebuilds and looks at what the new term is. Only the terms
    the last build recorded as unresolvable are excused."""
    real = vendoring.spec_terms
    invented = "https://www.commoncoreontologies.org/ont00000001"
    assert invented not in vendoring.recorded_unresolvable_spec_terms()

    monkeypatch.setattr(vendoring, "spec_terms",
                        lambda: real() | {invented})
    record = vendoring.verify()
    assert invented in record["unresolved_seeds"], record
    assert not record["ok"]


def test_a_specification_is_read_for_upstream_terms(
        vendoring, monkeypatch, tmp_path):
    """The template has no specification component, so the reader is
    exercised on a constructed one: prefixed names with prefixes from
    the pins, and full IRIs under a pinned namespace."""
    spec = tmp_path / "spec.md"
    spec.write_text("A `cco:ont00001180` bears it; the act is an "
                    "obo:BFO_0000015, see " + ENTITY + ".",
                    encoding="utf-8")

    class Spec:
        @staticmethod
        def resolve():
            return spec

    monkeypatch.setattr(vendoring.layout, "components",
                        lambda role=None: [Spec()])
    found = vendoring.spec_terms()
    assert {ORGANIZATION, PROCESS, ENTITY} <= found, found


def test_a_markdown_escaped_underscore_does_not_truncate_a_term(
        vendoring, monkeypatch, tmp_path):
    """Markdown writes `obo:BFO\\_0000015` for obo:BFO_0000015. Read
    naively that is obo:BFO, a different term -- and an invented one
    that would then be recorded as named by the spec."""
    spec = tmp_path / "spec.md"
    spec.write_text("The act " + "`obo:BFO" + chr(92) + "_0000015`" + ".",
                    encoding="utf-8")

    class Spec:
        @staticmethod
        def resolve():
            return spec

    monkeypatch.setattr(vendoring.layout, "components",
                        lambda role=None: [Spec()])
    found = vendoring.spec_terms()
    assert PROCESS in found, found
    assert OBO + "BFO" not in found, found


def test_the_extracts_carry_no_blank_nodes(extracts):
    """By construction, and the reason the digest means anything.

    rdflib renames blank nodes on every parse. An extract containing one
    would digest differently every time it was rebuilt from identical
    upstream bytes, and `--confirm` would report a difference that is not
    there.
    """
    import rdflib

    blank = [t for triple in extracts for t in triple
             if isinstance(t, rdflib.BNode)]
    assert not blank, "%d blank node(s) in the extracts" % len(blank)


# ------------------------------------------------- select: all / named


def test_select_all_takes_what_nobody_names_and_named_does_not(
        vendoring, monkeypatch, tmp_path):
    """The difference between the two modes, measured on constructed
    upstreams: A is vendored whole, B by reference. A's `lonely` term is
    named by nothing and must be in A's extract; B's is named by nothing
    and must not be in B's."""
    a_ns, b_ns = "https://a.invalid/", "https://b.invalid/"
    rdfs_label = "<%slabel>" % RDFS
    constructed_upstreams(vendoring, monkeypatch, [
        ("a", a_ns, "all",
         "<%slonely> %s \"lonely A\" .\n" % (a_ns, rdfs_label)),
        ("b", b_ns, "named",
         "<%slonely> %s \"lonely B\" .\n"
         "<%snamed> %s \"named B\" .\n" % (b_ns, rdfs_label,
                                          b_ns, rdfs_label)),
    ], seeds={b_ns + "named"})

    built = vendoring.build(tmp_path)
    a_subjects = {str(s) for s in parsed(built["a"]["text"]).subjects()}
    b_subjects = {str(s) for s in parsed(built["b"]["text"]).subjects()}
    assert a_ns + "lonely" in a_subjects
    assert b_ns + "named" in b_subjects
    assert b_ns + "lonely" not in b_subjects


def test_select_all_leaves_the_upstream_ontology_header_out(
        vendoring, monkeypatch, tmp_path):
    """BFO's own owl:Ontology (obo:bfo.owl) is in BFO's namespace.
    Selecting it put a second ontology header into the extract, with an
    owl:versionIRI nothing describes -- which the offline check reported
    as a dangling reference on the first build of the template."""
    import rdflib

    a_ns = "https://a.invalid/"
    constructed_upstreams(vendoring, monkeypatch, [
        ("a", a_ns, "all",
         "<%shead> <%stype> <%sOntology> .\n"
         "<%shead> <%sversionIRI> <%shead/1.0> .\n"
         "<%sterm> <%slabel> \"a term\" .\n"
         % (a_ns, "http://www.w3.org/1999/02/22-rdf-syntax-ns#", OWL,
            a_ns, OWL, a_ns, a_ns, RDFS)),
    ], seeds=set())

    built = vendoring.build(tmp_path)
    graph = parsed(built["a"]["text"])
    assert rdflib.URIRef(a_ns + "term") in set(graph.subjects())
    assert rdflib.URIRef(a_ns + "head") not in set(graph.subjects())


def test_a_select_all_source_that_describes_nothing_is_refused(
        vendoring, monkeypatch, tmp_path):
    """A namespace typed wrong in the pins would otherwise vendor an
    empty BFO, and every reachability question would answer for that."""
    constructed_upstreams(vendoring, monkeypatch, [
        ("a", "https://a.invalid/", "all",
         "<https://elsewhere.invalid/x> <%slabel> \"x\" .\n" % RDFS),
    ], seeds=set())
    with pytest.raises(SystemExit) as error:
        vendoring.build(tmp_path)
    assert "describes no term" in str(error.value)


# ---------------------------------------------------------- attribution


def test_a_triple_is_vendored_under_the_file_it_came_from(
        vendoring, monkeypatch, tmp_path):
    """The defect fixed in the BCO's copy of the tool.

    ARO partitioned selected triples by subject namespace alone. CCO's
    merged file carries its own annotations on BFO terms, so triples that
    exist only in CCO were written into the BFO extract under BFO's
    licence, with a header naming bfo-core.ttl as their source. Built
    here from two constructed upstreams so the case is exercised without
    the network: B annotates a term in A's namespace, and that triple has
    to land in B's extract.
    """
    import rdflib

    a_ns, b_ns = "https://a.invalid/", "https://b.invalid/"
    constructed_upstreams(vendoring, monkeypatch, [
        ("a", a_ns, "named",
         "<%sx> <%slabel> \"x\" .\n" % (a_ns, RDFS)),
        ("b", b_ns, "named",
         "<%sx> <http://www.w3.org/2004/02/skos/core#scopeNote> "
         "\"said by B\" .\n"
         "<%sy> <%ssubClassOf> <%sx> .\n" % (a_ns, b_ns, RDFS, a_ns)),
    ], seeds={b_ns + "y"})

    built = vendoring.build(tmp_path)
    graph_a, graph_b = parsed(built["a"]["text"]), parsed(built["b"]["text"])

    note = (rdflib.URIRef(a_ns + "x"),
            rdflib.URIRef("http://www.w3.org/2004/02/skos/core#scopeNote"),
            rdflib.Literal("said by B"))
    assert note in graph_b, "B's annotation on A's term left B's extract"
    assert note not in graph_a, (
        "B's annotation on A's term was vendored under A's licence")
    assert (rdflib.URIRef(a_ns + "x"), rdflib.RDFS.label,
            rdflib.Literal("x")) in graph_a


def test_ccos_annotations_on_bfo_terms_are_in_the_cco_extract(layout):
    """The same rule, measured on the real pins: CCO v2.0's merged file
    adds skos:scopeNote to BFO's temporal relations. Those are CCO's
    words and must be under CCO's licence, not BFO's."""
    import rdflib

    scope_note = rdflib.URIRef("http://www.w3.org/2004/02/skos/core#scopeNote")
    bfo, cco = extract(layout, "vendor.bfo"), extract(layout, "vendor.cco")
    in_cco = [(s, o) for s, o in cco.subject_objects(scope_note)
              if str(s).startswith(OBO)]
    assert in_cco, ("no CCO annotation on a BFO term is vendored, so "
                    "this test is not watching the case it is for")
    for subject, note in in_cco:
        assert (subject, scope_note, note) not in bfo, subject


# ------------------------------------------------------- load-bearing


def test_bfo_is_vendored_whole(layout, manifest):
    """Every BFO 2020 class and relation, not the ones named so far.

    36 classes and 40 object properties at release-2024-01-29, measured
    when the template was built. Pinned as a floor rather than an
    equality, so a re-pin to a BFO that adds terms passes and one that
    loses most of them does not.
    """
    import rdflib

    assert manifest["extracts"]["bfo"]["select"] == "all"
    graph = extract(layout, "vendor.bfo")
    classes = {s for s in graph.subjects(rdflib.RDF.type, rdflib.OWL.Class)
               if str(s).startswith(OBO + "BFO_")}
    relations = {s for s in graph.subjects(rdflib.RDF.type,
                                           rdflib.OWL.ObjectProperty)
                 if str(s).startswith(OBO + "BFO_")}
    assert len(classes) >= 36, len(classes)
    assert len(relations) >= 40, len(relations)


def test_every_bfo_class_reaches_entity(layout):
    """The chain a "reaches a BFO root" shape will walk. With the BFO
    extract alone, every BFO class must get to entity through named
    subClassOf edges -- if one did not, a class placed under it would be
    reported as unanchored, and the report would describe the extract."""
    graph = extract(layout, "vendor.bfo")
    rows = graph.query("""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?c WHERE {
          ?c a owl:Class .
          FILTER(STRSTARTS(STR(?c), "%s"))
          FILTER NOT EXISTS { ?c rdfs:subClassOf* <%s> }
        }""" % (OBO + "BFO_", ENTITY))
    unanchored = sorted(str(row[0]) for row in rows)
    assert unanchored == [], unanchored


def test_the_extract_carries_the_disjointness_a_realist_check_needs(
        layout):
    """Continuant and occurrent are disjoint in BFO, asserted between
    named classes, so the extract keeps it even though it drops every
    anonymous class expression. A shape refusing a class under both
    reads this triple; if a re-pin moved it into an anonymous
    owl:AllDisjointClasses, the extract would lose it and this is where
    that would show."""
    import rdflib

    graph = extract(layout, "vendor.bfo")
    assert (rdflib.URIRef(CONTINUANT), rdflib.OWL.disjointWith,
            rdflib.URIRef(OCCURRENT)) in graph
    assert graph.query(
        "ASK { <%s> <%ssubClassOf>* <%s> }" % (PROCESS, RDFS,
                                               OCCURRENT)).askAnswer
    assert graph.query(
        "ASK { <%s> <%ssubClassOf>* <%s> }" % (MATERIAL_ENTITY, RDFS,
                                               CONTINUANT)).askAnswer


# ---------------------------------------------------------- licensing


def test_the_extracts_are_third_party_and_redistributable(disposition):
    rows = {row.path: row for row in disposition.classify()}
    pinned = disposition.vendored_sources()
    vendored = [row for row in rows.values()
                if row.disposition == disposition.VENDORED]
    assert {row.path for row in vendored} == set(pinned)
    assert {row.licence for row in vendored} == {
        entry["licence"]["spdx"] for entry in pinned.values()}
    assert {"CC-BY-4.0", "BSD-3-Clause"} <= {row.licence for row in vendored}
    for row in vendored:
        assert row.redistributable, row.path


def test_the_licence_comes_from_the_pins_not_from_this_repository(
        disposition, monkeypatch):
    """A vendored file does not carry this repository's licence.

    The classifier is asked with the project licence replaced by a
    sentinel. A vendored row that reported the sentinel took its licence
    from the wrong place.
    """
    monkeypatch.setattr(disposition, "project_licence",
                        lambda: "SENTINEL-PROJECT-LICENCE")
    pinned = {path: entry["licence"]["spdx"]
              for path, entry in disposition.vendored_sources().items()}
    rows = [row for row in disposition.classify()
            if row.disposition == disposition.VENDORED]
    assert rows
    for row in rows:
        assert row.licence == pinned[row.path], row


def test_attribution_is_checked_rather_than_assumed(disposition,
                                                    monkeypatch):
    """Falsifies the attribution check.

    Every licence here permits redistribution on condition of
    attribution. Pointing the check at a file that does not contain the
    attribution has to produce a finding, or the condition is being
    reported as met by a check that never looks.
    """
    rows = disposition.classify()
    assert disposition.attribution_findings(rows) == []

    monkeypatch.setattr(disposition, "NOTICE", "LICENSE")
    problems = disposition.attribution_findings(rows)
    assert problems, (
        "the attribution check passed against a file containing no "
        "attribution")
    for extract_path in disposition.vendored_sources():
        assert extract_path in problems[0], extract_path


# -------------------------------------------------- what was not done


def test_the_manifest_states_what_the_extracts_leave_out(manifest):
    """A partial extract that does not say it is partial is the defect
    this whole method is about."""
    assert manifest["not_covered"], manifest.keys()
    assert any("anonymous class expression" in line
               for line in manifest["not_covered"])
    assert any("consistent" in line for line in manifest["not_covered"])

    dropped = sum(entry["axioms_dropped_anonymous_object"]
                  for entry in manifest["extracts"].values())
    assert dropped > 0, (
        "no axioms were dropped, so either the upstream has no anonymous "
        "class expressions -- it does -- or the count is not being taken")


def test_each_extract_says_in_its_own_header_that_it_is_partial(
        layout, vendoring):
    """The manifest is a file somebody has to go and read. The extract is
    the file they already have open."""
    paths = layout.vendored_files()
    assert len(paths) == len(vendoring.sources()), paths
    for path in paths:
        head = path.read_text(encoding="utf-8")[:3000]
        assert "partial extract" in head.lower(), path.name
        assert "cannot be" in head and "consistency" in head, path.name
        assert "axioms about the selected terms were dropped" in head, \
            path.name


# --------------------------------------------------------- serialising


def test_the_serialiser_round_trips_awkward_literals(vendoring):
    """Falsifies the escaping.

    Definitions in CCO run to several lines and contain quotation marks.
    A serialiser that got either wrong would emit a file that parses to a
    different graph, and the digest recorded for it would be a digest of
    the damage.
    """
    import rdflib

    subject = rdflib.URIRef("https://ex.invalid/a")
    awkward = ('line one' + chr(10) + 'line "two"' + chr(9) + 'tabbed'
               + chr(92) + ' backslash')
    triples = [
        (subject, rdflib.URIRef("https://ex.invalid/p"),
         rdflib.Literal(awkward, lang="en")),
        (subject, rdflib.URIRef("http://www.w3.org/2000/01/rdf-schema#label"),
         rdflib.Literal("plain")),
        (subject, rdflib.URIRef("https://ex.invalid/n"),
         rdflib.Literal("3", datatype=rdflib.URIRef(
             "http://www.w3.org/2001/XMLSchema#integer"))),
    ]
    text = vendoring.serialise(triples, ["a test"])
    assert chr(10) not in text.split('"')[1], (
        "the literal was emitted across lines, so a newline inside it is "
        "no longer distinguishable from formatting")

    back = rdflib.Graph()
    back.parse(data=text, format="turtle")
    assert set(back) == set(triples)


def test_the_same_inputs_serialise_to_the_same_bytes(vendoring):
    """Sorted, deduplicated, and independent of the order given."""
    import rdflib

    triples = [
        (rdflib.URIRef("https://ex.invalid/b"),
         rdflib.URIRef("https://ex.invalid/p"), rdflib.Literal("two")),
        (rdflib.URIRef("https://ex.invalid/a"),
         rdflib.URIRef("https://ex.invalid/p"), rdflib.Literal("one")),
    ]
    first = vendoring.serialise(triples, ["h"])
    second = vendoring.serialise(list(reversed(triples)) + triples, ["h"])
    assert first == second


def test_a_blank_node_reaching_the_serialiser_is_refused(vendoring):
    """It cannot happen by construction, which is exactly why the guard
    is here: the construction is what would change."""
    import rdflib

    with pytest.raises(SystemExit):
        vendoring.serialise(
            [(rdflib.URIRef("https://ex.invalid/a"),
              rdflib.URIRef("https://ex.invalid/p"), rdflib.BNode())], ["h"])


def test_the_serialiser_prefixes_come_from_the_pins(vendoring):
    """Every pinned namespace is abbreviated in the extracts. A prefix
    list kept by hand would write a newly pinned source's IRIs out
    longhand the day it was added, and nothing would say so."""
    declared = dict(vendoring.prefixes())
    for entry in vendoring.sources():
        assert declared[entry["prefix"]] == entry["namespace"], entry["id"]


# ------------------------------------------------------------- scope


def test_the_extracts_are_not_counted_as_this_repository_ontology(layout):
    """A vendored file in `ontology_files()` would put third-party triples
    into the corpus digest, and the digest would then move whenever an
    upstream pin changed."""
    authored = {p.as_posix() for p in layout.ontology_files()}
    vendored = {p.as_posix() for p in layout.vendored_files()}
    assert vendored
    assert not (authored & vendored)


def test_the_corpus_digest_does_not_measure_the_vendored_extracts():
    digest = load_tool("t_digest_scope",
                       "tools/ontology/corpus_digest.py").measure()
    assert not [p for p in digest["scope"]["paths"] if p.startswith("vendor/")]
