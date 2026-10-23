# SPDX-License-Identifier: MIT
"""Competency questions: a right answer passes, a wrong one fails, and an
expectation nothing can fail is refused rather than passed.

The fixtures are in tests/fixtures/competency/: questions CQ-001 to CQ-004
are positive controls (three answerable, one draft that would fail if
run), CQ-101 onwards are built to fail or be refused, each for one
reason. They carry `{{iri_base}}` where the examples namespace goes and
are written to a temporary directory with it filled in, because they are
template-owned and must name no project.
"""

from __future__ import annotations

import pytest

from conftest import load_tool

FIXTURES = "tests/fixtures/competency"

#: The verdict each fixture question must get, and a phrase its detail
#: must contain. Named, not counted.
EXPECTED = {
    "CQ-001": ("pass", "1 rows"),
    "CQ-002": ("pass", "ask true"),
    "CQ-003": ("pass", "includes 1"),
    "CQ-004": ("not run", "draft"),
    "CQ-101": ("fail", "missing"),
    "CQ-102": ("fail", "returned nothing"),
    "CQ-103": ("refused", "expect rows is empty"),
    "CQ-104": ("refused", "expect ask must be true"),
    "CQ-105": ("refused", "lacks query"),
    "CQ-106": ("refused", "depends on"),
    "CQ-107": ("refused", "is not its filename"),
    "CQ-108": ("refused", "does not exist"),
}


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_competency", "tools/ontology/competency.py")


@pytest.fixture(scope="module")
def written(repo, project, tmp_path_factory):
    target = tmp_path_factory.mktemp("competency")
    for source in sorted((repo / FIXTURES).rglob("*")):
        if not source.is_file():
            continue
        path = target / source.relative_to(repo / FIXTURES)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source.read_bytes().decode("utf-8").replace(
            "{{iri_base}}", project.iri_base()).encode("utf-8"))
    return target


@pytest.fixture(scope="module")
def record(tool, written):
    paths = sorted((written / "questions").glob("*.yaml"))
    assert len(paths) == len(EXPECTED), sorted(p.name for p in paths)
    return tool.check(paths, base=written, inside=written / "examples")


def verdicts(record):
    out = {}
    for row in record["results"]:
        key = row["file"].rsplit(".", 1)[0]
        out[key] = (row["verdict"], row["detail"] if row["verdict"] != "not run"
                    else row["status"])
    return out


def test_each_fixture_question_gets_its_verdict(record):
    got = verdicts(record)
    wrong = {}
    for qid, (verdict, phrase) in EXPECTED.items():
        if qid not in got or got[qid][0] != verdict or phrase not in got[qid][1]:
            wrong[qid] = (verdict, phrase, got.get(qid))
    assert not wrong, wrong


def test_the_record_fails_while_anything_fails(record):
    assert record["ok"] is False
    assert {r["file"] for r in record["failing"]} == {
        "%s.yaml" % q for q, (v, _p) in EXPECTED.items()
        if v in ("fail", "refused")}


def test_the_positive_controls_alone_pass(tool, written):
    paths = [written / "questions" / ("%s.yaml" % q)
             for q in ("CQ-001", "CQ-002", "CQ-003", "CQ-004")]
    record = tool.check(paths, base=written, inside=written / "examples")
    assert record["ok"], record["failing"]
    assert record["answerable"] == 3


def test_an_example_outside_examples_is_refused(tool, written):
    """`examples:` names files under examples/, nowhere else, so a question
    cannot be answered by a file nobody reviews as example data."""
    path = written / "questions" / "CQ-001.yaml"
    record = tool.check([path], base=written, inside=written / "questions")
    assert record["results"][0]["verdict"] == "refused"
    assert "outside" in record["results"][0]["detail"]


def test_one_scenario_cannot_answer_anothers_question(tool, written):
    """Only the example files a question names are loaded. CQ-001 with its
    scenario passes; the same question naming none returns nothing."""
    import yaml

    source = yaml.safe_load((written / "questions" / "CQ-001.yaml").read_text(
        encoding="utf-8"))
    source["examples"] = []
    path = written / "isolated" / "CQ-001.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(yaml.safe_dump(source), encoding="utf-8")
    record = tool.check([path], base=written, inside=written / "examples")
    assert record["results"][0]["verdict"] == "fail"
    assert "returned nothing" in record["results"][0]["detail"]


def test_the_live_record_is_clean(tool, capsys):
    """A fresh project has no questions and says so; it does not fail."""
    assert tool.main([]) == 0
    out = capsys.readouterr().out
    assert "no competency questions yet" in out or "answered as expected" in out


def test_an_example_typed_with_an_undeclared_class_is_a_lint_finding(
        project, tmp_path):
    """The rule examples are held to: every type they assert is a declared
    authored class or a real upstream term. The IRI linter enforces it,
    because the examples are in its scope."""
    linter = load_tool("t_lint_examples", "tools/ontology/iri_lint.py")
    path = tmp_path / "scenario.ttl"
    path.write_text(
        "@prefix p: <%s> .\n@prefix eg: <%s/examples/> .\n"
        "eg:thing-1 a p:NoSuchClass .\n" % (project.namespace(),
                                           project.iri_base()),
        encoding="utf-8")
    findings = linter.lint([path])
    assert [(f["type"], f["subject"]) for f in findings] == [
        ("dangling_ref", project.namespace() + "NoSuchClass")], findings
    assert "example-data" in linter.SCOPE_ROLES


def test_a_question_seeds_vendoring(project, monkeypatch, tmp_path, layout):
    """A CCO term named only in a question's SPARQL must be vendored, or
    the question asks about a term the data graph does not describe."""
    vendoring = load_tool("t_vendor_cq", "tools/ontology/vendor_upstream.py")
    found = vendoring.named_in_text(
        "query: |\n  SELECT ?x WHERE { ?x a cco:ont00001180 ; "
        "obo:BFO_0000057 ?y }\n")
    assert "https://www.commoncoreontologies.org/ont00001180" in found
    assert "http://purl.obolibrary.org/obo/BFO_0000057" in found
