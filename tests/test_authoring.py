# SPDX-License-Identifier: MIT
"""The authoring aids: the Protégé entry point, canonical form, the GitHub
forms and Dependabot, the citation file, and the research record's rule.

The one check that needs Java -- ROBOT, through the OWL API Protégé uses,
loading the edit file and resolving every import through the catalog,
offline -- is marked `reasoning`. It is how the catalog's first defect was
found: a `--` inside an XML comment, which the catalog parser refuses.
"""

from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from conftest import load_tool

CATALOG_NS = "{urn:oasis:names:tc:entity:xmlns:xml:catalog}"


@pytest.fixture(scope="module")
def protege():
    return load_tool("t_protege", "tools/ontology/protege.py")


@pytest.fixture(scope="module")
def normalize():
    return load_tool("t_normalize", "tools/ontology/normalize.py")


# --------------------------------------------------------------- Protégé


def test_the_protege_files_are_current(protege):
    assert protege.main(["--check"]) == 0


@pytest.mark.parametrize("which", ["committed", "generated now"])
def test_the_catalog_maps_every_import_to_a_file_that_exists(
        protege, repo, layout, which):
    """Both the committed catalog and the one the generator writes now:
    a falsification of the generator left the committed file intact and
    passed this test until it read the generator's output too."""
    data = ((repo / protege.CATALOG).read_bytes() if which == "committed"
            else protege.generated(repo)[protege.CATALOG])
    root = ET.fromstring(data)
    entries = {u.get("name"): u.get("uri")
               for u in root.iter(CATALOG_NS + "uri")}
    wanted = {protege.ontology_iri(p): p
              for p in layout.ontology_files() + layout.vendored_files()}
    assert set(entries) == set(wanted), (set(entries) ^ set(wanted))
    for iri, relative in entries.items():
        target = (repo / "protege" / relative).resolve()
        assert target == wanted[iri].resolve(), (iri, relative)
        assert target.is_file(), relative


def test_the_edit_file_imports_them_and_declares_nothing(protege, repo):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(repo / protege.EDIT, format="turtle")
    imports = {str(o) for o in graph.objects(None, rdflib.OWL.imports)}
    catalog = ET.parse(repo / protege.CATALOG).getroot()
    assert imports == {u.get("name") for u in catalog.iter(CATALOG_NS + "uri")}
    assert len(set(graph.subjects())) == 1, "the edit file declares terms"


def test_a_module_with_two_headers_is_refused(protege, tmp_path):
    path = tmp_path / "m.ttl"
    path.write_text("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
                    "<https://x.invalid/a> a owl:Ontology .\n"
                    "<https://x.invalid/b> a owl:Ontology .\n",
                    encoding="utf-8")
    with pytest.raises(SystemExit) as error:
        protege.ontology_iri(path)
    assert "2 owl:Ontology headers" in str(error.value)


@pytest.mark.reasoning
def test_robot_loads_the_edit_file_through_the_catalog_offline(repo,
                                                               tmp_path):
    reason = load_tool("t_reason_for_protege", "tools/ontology/reason.py")
    jar = reason.fetch_jar(reason.config()["robot"], repo / ".tool-cache")
    out = tmp_path / "merged.ttl"
    result = subprocess.run(
        [reason.java(), "-jar", str(jar), "--catalog",
         str(repo / "protege/catalog-v001.xml"), "merge", "--input",
         str(repo / "protege/edit.ttl"), "--output", str(out)],
        capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    merged = out.read_text(encoding="utf-8")
    assert "BFO_0000015" in merged, "BFO was not loaded through the catalog"


# ------------------------------------------------------- canonical form


def test_canonical_form_keeps_the_graph_and_is_a_fixed_point(normalize,
                                                             layout):
    import rdflib
    from rdflib.compare import isomorphic

    text = layout.path("fixture.realist-bad-examples").read_text(
        encoding="utf-8")
    once = normalize.canonical_text(text)
    twice = normalize.canonical_text(once.decode("utf-8"))
    assert once == twice, "canonical form is not a fixed point"
    a, b = rdflib.Graph(), rdflib.Graph()
    a.parse(data=text, format="turtle")
    b.parse(data=once.decode("utf-8"), format="turtle")
    assert isomorphic(a, b)


def test_canonical_form_is_the_same_bytes_in_another_process(repo, layout):
    fixture = layout.path("fixture.realist-bad-examples")
    script = (
        "import sys, importlib.util; sys.path.insert(0, %r)\n"
        "spec = importlib.util.spec_from_file_location('n', %r)\n"
        "n = importlib.util.module_from_spec(spec); spec.loader.exec_module(n)\n"
        "sys.stdout.buffer.write(n.canonical_text(open(%r, encoding='utf-8')"
        ".read()))\n" % (str(repo / "tools"),
                         str(repo / "tools/ontology/normalize.py"),
                         str(fixture)))
    outputs = []
    for seed in ("1", "9"):
        result = subprocess.run([sys.executable, "-c", script],
                                capture_output=True, cwd=str(repo),
                                env={**os.environ, "PYTHONHASHSEED": seed})
        assert result.returncode == 0, result.stderr
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1] and outputs[0]


def test_a_module_not_in_canonical_form_fails_the_check(normalize,
                                                        monkeypatch,
                                                        tmp_path):
    module = tmp_path / "m.ttl"
    module.write_text("@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
                      "# a comment canonical form will not keep\n"
                      "<https://x.invalid/a> a owl:Class .\n",
                      encoding="utf-8")
    monkeypatch.setattr(normalize, "opted_in", lambda: [module])
    assert normalize.main(["--check"]) == 1
    assert normalize.main([]) == 0
    assert normalize.main(["--check"]) == 0
    assert "# a comment" not in module.read_text(encoding="utf-8")


def test_an_unknown_format_is_refused(layout, repo):
    with pytest.raises(layout.LayoutError):
        layout.Component({"id": "x", "path": "x", "role": "tool",
                          "format": "pretty"}, repo)


# --------------------------------------------------------- GitHub files


def test_dependabot_watches_the_actions_and_the_python_pins(repo):
    import yaml

    config = yaml.safe_load((repo / ".github/dependabot.yml").read_text(
        encoding="utf-8"))
    assert {u["package-ecosystem"] for u in config["updates"]} == {
        "github-actions", "pip"}


def test_the_term_request_form_asks_for_what_placing_a_term_needs(repo):
    import yaml

    form = yaml.safe_load((repo / ".github/ISSUE_TEMPLATE/term-request.yml")
                          .read_text(encoding="utf-8"))
    required = {item["id"] for item in form["body"]
                if item.get("validations", {}).get("required")}
    assert {"label", "definition", "parent", "why"} <= required, required


def test_the_pull_request_checklist_names_the_checks(repo):
    text = (repo / ".github/pull_request_template.md").read_text(
        encoding="utf-8")
    for needle in ("iri_lint.py", "--rebuild", "corpus_digest.py",
                   "negative fixture", "answerable"):
        assert needle in text, needle


def test_the_citation_file_is_valid_cff(repo):
    import yaml

    cff = yaml.safe_load((repo / "CITATION.cff").read_text(encoding="utf-8"))
    for key in ("cff-version", "message", "title", "authors", "license"):
        assert cff.get(key), key
    assert all(author.get("name") for author in cff["authors"])


# --------------------------------------------------------------- research


def test_research_holds_notes_not_sources(disposition, monkeypatch, tmp_path):
    """A PDF in research/ is refused by suffix; a note whose bytes are a
    reference file's is refused as a copy, whatever it is called."""
    rows = disposition.classify()
    assert disposition.research_findings(rows) == []

    Row = disposition.Disposition
    fake = [Row("research/standard.pdf", "research",
                disposition.CONTENT, "MIT", True, "")]
    root = tmp_path / "r"
    (root / "research").mkdir(parents=True)
    (root / "docs/Reference").mkdir(parents=True)
    (root / "research/standard.pdf").write_bytes(b"%PDF")
    (root / "research/notes.md").write_bytes(b"a paid standard's text")
    (root / "docs/Reference/iso.txt").write_bytes(b"a paid standard's text")
    fake.append(Row("research/notes.md", "research", disposition.CONTENT,
                    "MIT", True, ""))
    monkeypatch.setattr(disposition.layout, "repository_root", lambda: root)

    class Ref:
        role = "third-party-reference"
        path = "docs/Reference"

        @staticmethod
        def exists():
            return True

        @staticmethod
        def members(_pattern="*"):
            return [root / "docs/Reference/iso.txt"]

    class Research:
        role = "research"
        path = "research"

    monkeypatch.setattr(disposition.layout, "components",
                        lambda role=None: [Ref(), Research()])
    found = disposition.research_findings(fake)
    assert any("not notes, tables" in f and "standard.pdf" in f
               for f in found), found
    assert any("copies of reference material" in f and "notes.md" in f
               for f in found), found
