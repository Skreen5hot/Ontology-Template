# SPDX-License-Identifier: MIT
"""The vocabulary intake, and the term diff that reports what it changed.

The intake: an accepted, signed row becomes a placed class; a proposed or
rejected one does not; a row that cannot be placed is refused with its
line. Run on constructed intake text against the live profile, naming
convention and modules.

The term diff: a throwaway git repository whose module gains, loses,
relabels, reparents and deprecates terms between two commits, each side
read through its own layout contract.
"""

from __future__ import annotations

import subprocess

import pytest

from conftest import load_tool

OBO = "http://purl.obolibrary.org/obo/"
HEADER = ("local_name\tlabel\tdefinition\tparent\tsynonyms\tstatus\t"
          "requested_by\treviewed_by\tnotes\tdefinition_source\n")


def row(name, status="accepted", label="widget",
        definition="A material entity that is a widget.",
        parent="obo:BFO_0000040", synonyms="", requested="R", reviewed="V",
        source="a standard"):
    return "\t".join([name, label, definition, parent, synonyms, status,
                      requested, reviewed, "", source]) + "\n"


@pytest.fixture(scope="module")
def vocabulary():
    return load_tool("t_vocabulary", "tools/ontology/vocabulary.py")


def check(vocabulary, repo, text):
    return vocabulary.check(text, repo, repo / vocabulary.OUTPUT)


# ----------------------------------------------------------- the intake


def test_the_committed_module_is_what_the_intake_generates(vocabulary):
    assert vocabulary.main(["--check"]) == 0


def test_an_accepted_row_becomes_a_placed_class(vocabulary, repo, project):
    import rdflib

    text = HEADER + row("Widget", synonyms="gadget | gizmo") \
        + row("Pending", status="proposed") + row("Refused",
                                                  status="rejected")
    accepted, problems = check(vocabulary, repo, text)
    assert problems == [], problems
    assert [r["local_name"] for r in accepted] == ["Widget"]
    graph = rdflib.Graph()
    graph.parse(data=vocabulary.module_text(accepted, repo), format="turtle")
    widget = rdflib.URIRef(project.namespace() + "Widget")
    assert (widget, rdflib.RDFS.subClassOf, rdflib.URIRef(OBO + "BFO_0000040")) \
        in graph
    alt = {str(o) for o in graph.objects(widget, rdflib.SKOS.altLabel)}
    assert alt == {"gadget", "gizmo"}
    source = rdflib.URIRef("https://www.commoncoreontologies.org/ont00001754")
    assert str(graph.value(widget, source)) == "a standard", (
        "the profile's column did not become its annotation")
    assert rdflib.URIRef(project.namespace() + "Pending") not in set(
        graph.subjects())


@pytest.mark.parametrize("text, expect", [
    ("local_name\tlabel\n", "lacks the column 'definition'"),
    (HEADER + row("Widget", status="maybe"), "is not one of"),
    (HEADER + row("Widget", reviewed=""), "has no reviewed_by"),
    (HEADER + row("Widget", parent=""), "has no parent"),
    (HEADER + row("widget"), "does not follow the class naming"),
    (HEADER + row("Widget") + row("Widget"), "is also line 2"),
    (HEADER + row("Widget", parent="nope:Thing"), "has no known prefix"),
])
def test_a_row_that_cannot_be_placed_is_refused(vocabulary, repo, text,
                                                expect):
    _accepted, problems = check(vocabulary, repo, text)
    assert any(expect in p for p in problems), problems


def test_a_term_another_module_declares_is_refused(vocabulary, repo,
                                                   monkeypatch, project):
    monkeypatch.setattr(vocabulary, "declared_elsewhere",
                        lambda output: {project.namespace() + "Widget"})
    _accepted, problems = check(vocabulary, repo, HEADER + row("Widget"))
    assert any("already declared in another module" in p for p in problems)


def test_the_generated_module_passes_the_linter_and_its_parent_is_checked(
        vocabulary, repo, tmp_path):
    """Whether the parent exists is the linter's question, asked of the
    generated module: a real BFO parent is clean, a made-up CCO id is not."""
    linter = load_tool("t_lint_vocab", "tools/ontology/iri_lint.py")
    good = tmp_path / "good.ttl"
    accepted, _ = check(vocabulary, repo, HEADER + row("Widget"))
    good.write_text(vocabulary.module_text(accepted, repo), encoding="utf-8")
    assert linter.lint([good]) == []
    bad = tmp_path / "bad.ttl"
    accepted, _ = check(vocabulary, repo,
                        HEADER + row("Widget", parent="cco:ont99999999"))
    bad.write_text(vocabulary.module_text(accepted, repo), encoding="utf-8")
    assert [f["type"] for f in linter.lint([bad])] == ["unverified"]


# ------------------------------------------------------------- term diff


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@invalid",
                    *args], cwd=str(root), check=True, capture_output=True)


CONTRACT = ("version: 1\ncomponents:\n"
            "  - id: ontology.main\n    path: ontology/m.ttl\n"
            "    role: ontology-module\n")


def module(ns, body):
    return ("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
            "@prefix dcterms: <http://purl.org/dc/terms/> .\n"
            "@prefix obo: <%s> .\n@prefix p: <%s> .\n%s" % (OBO, ns, body))


@pytest.fixture(scope="module")
def history(tmp_path_factory, project):
    root = tmp_path_factory.mktemp("history")
    (root / "config").mkdir()
    (root / "ontology").mkdir()
    (root / "config/repository-layout.yaml").write_text(CONTRACT,
                                                        encoding="utf-8")
    ns = project.namespace()
    (root / "ontology/m.ttl").write_text(module(ns, (
        'p:Kept a owl:Class ; rdfs:label "kept" ; rdfs:subClassOf obo:BFO_0000040 .\n'
        'p:Relabelled a owl:Class ; rdfs:label "old name" .\n'
        'p:Gone a owl:Class ; rdfs:label "gone" .\n'
        'p:Retired a owl:Class ; rdfs:label "retired" .\n')), encoding="utf-8")
    git(root, "init", "-q")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "one")
    git(root, "tag", "v1.0.0")
    (root / "ontology/m.ttl").write_text(module(ns, (
        'p:Kept a owl:Class ; rdfs:label "kept" ; rdfs:subClassOf obo:BFO_0000040 .\n'
        'p:Relabelled a owl:Class ; rdfs:label "new name" .\n'
        'p:Retired a owl:Class ; rdfs:label "retired" ; owl:deprecated true ;\n'
        '    dcterms:isReplacedBy p:Kept .\n'
        'p:Added a owl:Class ; rdfs:label "added" ; rdfs:subClassOf p:Kept .\n')),
        encoding="utf-8")
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "two")
    git(root, "tag", "v1.1.0")
    return root


@pytest.fixture(scope="module")
def term_diff():
    return load_tool("t_term_diff", "tools/ontology/term_diff.py")


def test_the_diff_names_every_kind_of_change(term_diff, history, project):
    ns = project.namespace()
    result, before, after = term_diff.run("v1.0.0", "v1.1.0", root=history)
    assert result["added"] == [ns + "Added"]
    assert result["removed"] == [ns + "Gone"]
    assert result["deprecated"] == [ns + "Retired"]
    changed = {c["term"]: c["fields"] for c in result["changed"]}
    assert changed[ns + "Relabelled"]["labels"] == {"was": ["old name"],
                                                    "now": ["new name"]}
    assert changed[ns + "Retired"]["replaced_by"]["now"] == [ns + "Kept"]
    assert ns + "Kept" not in changed, "an unchanged term was reported"


def test_the_markdown_says_it(term_diff, history):
    result, before, after = term_diff.run("v1.0.0", "v1.1.0", root=history)
    text = term_diff.markdown(result, before, after, "v1.0.0", "v1.1.0")
    assert text.startswith("## Terms: 1 added, 1 removed, 2 changed, "
                           "1 deprecated"), text.splitlines()[0]
    for section in ("### Added", "### Removed", "### Deprecated",
                    "### Changed"):
        assert section in text, section


def test_with_no_base_every_term_is_added(term_diff, history):
    result, _before, after = term_diff.run(None, "v1.0.0", root=history)
    assert len(result["added"]) == 4 == len(after)


def test_a_ref_that_is_not_a_commit_is_refused(term_diff, history):
    with pytest.raises(SystemExit) as error:
        term_diff.run("v9.9.9", "v1.0.0", root=history)
    assert "is not a commit" in str(error.value)


def test_a_release_ships_the_diff_inside_its_checksums(tmp_path, project,
                                                      layout):
    """Built from a stand-in module, not the live corpus: where CHANGES.md
    goes does not depend on the ontology's size, and on a 3,000-class
    project a release build of the corpus is minutes."""
    release = load_tool("t_release_changes", "tools/release.py")
    changes = tmp_path / "CHANGES.md"
    changes.write_text("## Terms: 0 added\n", encoding="utf-8")
    names = release.build(
        "1.0.0", tmp_path / "out", changes=changes,
        modules=[layout.path("fixture.realist-bad-examples")])
    assert "CHANGES.md" in names
    sums = (tmp_path / "out" / ("%s-1.0.0" % project.project_id())
            / "SHA256SUMS").read_text(encoding="utf-8")
    assert "  CHANGES.md" in sums
