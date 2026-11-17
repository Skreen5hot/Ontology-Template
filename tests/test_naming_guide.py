# SPDX-License-Identifier: MIT
"""The guide's naming rule that a scheme rule cannot state, run as written.

A scheme rule (config/naming.yaml) relates a local name to a pattern and a
category; it cannot relate a local name to a value the class carries. The
Business Process Ontology's "a class with a pcfID is named P<pcfID>" is
such a rule (P-A4), and the template's answer is a project's own shape set,
shown in docs/DEVELOPMENT.md, "A naming rule that relates a local name to a
value" (decision 54). Nothing in the template runs that example, so these
tests do: they read the shape set, its fixture, its layout entries and its
project test out of the guide, and hold them to what the guide says they
do. If the example stops working, or the two engines stop agreeing on it,
the suite fails.
"""

from __future__ import annotations

import re

import pytest
import yaml

from conftest import load_tool

NS = "https://example.org/my-ontology#"

# By identity: the focus, and the code it is reported for. The guide names
# these five; a count would be satisfied by any five.
EXPECTED = {
    ("P10008", "10009"),
    ("Planning", "10010"),
    ("P10011", "10012"),
    ("P10013", " 10013"),
    ("P10014", "10015"),
}

BLOCKS = ("shapes", "fixture", "layout", "test")


def example_blocks(text: str) -> dict:
    """Each fenced block that directly follows a
    `<!-- naming-guide-example: NAME -->` marker, by NAME."""
    found = {}
    pattern = re.compile(
        r"<!-- naming-guide-example: ([a-z]+) -->\n```[a-z]*\n(.*?)\n```\n",
        re.S)
    for name, body in pattern.findall(text):
        assert name not in found, "the guide marks two %r blocks" % name
        found[name] = body + "\n"
    return found


@pytest.fixture(scope="module")
def blocks(repo):
    return example_blocks((repo / "docs/DEVELOPMENT.md").read_bytes().decode())


@pytest.fixture(scope="module")
def validator():
    return load_tool("t_naming_guide_validate", "tools/ontology/validate.py")


@pytest.fixture(scope="module")
def results(blocks, validator):
    import rdflib

    data = rdflib.Graph().parse(data=blocks["fixture"], format="turtle")
    shapes = rdflib.Graph().parse(data=blocks["shapes"], format="turtle")
    return {engine: validator.run(data, shapes, engine=engine)
            for engine in ("oxigraph", "pyshacl")}


def reported(result) -> set:
    out = set()
    for record in result["violations"]:
        assert record["focus"].startswith(NS), record
        match = re.search(r"carries the code (.*) and is not named P",
                          record["message"] or "")
        assert match, record
        out.add((record["focus"][len(NS):], match.group(1)))
    return out


def test_the_guide_carries_every_block_of_the_example(blocks):
    assert sorted(blocks) == sorted(BLOCKS), sorted(blocks)


def test_the_extraction_finds_a_marked_block_and_only_one():
    """Guards the reader the tests above and below rest on."""
    text = ("<!-- naming-guide-example: shapes -->\n```turtle\na\nb\n```\n"
            "```turtle\nunmarked\n```\n"
            "<!-- naming-guide-example: layout -->\nprose between\n"
            "```yaml\nnot directly after its marker\n```\n")
    assert example_blocks(text) == {"shapes": "a\nb\n"}
    with pytest.raises(AssertionError):
        example_blocks(text + "<!-- naming-guide-example: shapes -->\n"
                              "```turtle\nc\n```\n")


def test_a_finding_is_read_as_its_focus_and_its_code():
    """Guards `reported`: the identity it gives a finding is the focus and
    the code in the message, not the focus alone."""
    record = {"focus": NS + "P1", "severity": "Violation",
              "message": "Class %sP1 carries the code 2 and is not named P2."
                         % NS}
    assert reported({"violations": [record]}) == {("P1", "2")}
    assert reported({"violations": [dict(record, focus=NS + "Q")]}) \
        == {("Q", "2")}


@pytest.mark.parametrize("engine", ["oxigraph", "pyshacl"])
def test_each_engine_reports_exactly_the_cases_built_to_break_it(results,
                                                                 engine):
    """The guide's five cases, each for the code it names, and none of its
    positive controls: the exempt class, the typed and tagged codes that
    match, and the P-name with no code."""
    assert reported(results[engine]) == EXPECTED
    # One record per case: a set would hide a case reported twice.
    assert len(results[engine]["violations"]) == len(EXPECTED)
    assert all(r["severity"] == "Violation"
               for r in results[engine]["violations"])
    assert results[engine]["conforms"] is False


def test_the_two_engines_agree_record_for_record(results):
    """The validator runs SPARQL constraints in Oxigraph; pyshacl is the
    reference (tests/test_scale.py). The guide's example must give the
    same records in both, focus, shape, severity and message."""
    def records(result):
        return sorted(tuple(sorted(r.items())) for r in result["violations"])

    assert records(results["oxigraph"]) == records(results["pyshacl"])


def test_the_layout_entries_are_a_shape_set_and_its_fixture(blocks):
    entries = yaml.safe_load(blocks["layout"])
    assert [e["role"] for e in entries] == ["ontology-validation",
                                            "test-fixture"]
    assert [e["path"] for e in entries] == [
        "shapes/code_names_shapes.ttl", "shapes/code_names_bad_examples.ttl"]
    # The project's own: a template key would report them as divergence,
    # or claim them for the template.
    assert all("template" not in e for e in entries), entries


def test_the_project_test_passes_on_the_example(blocks, tmp_path):
    """The guide's own project test, run on its shape set and fixture
    written where the layout entries put them."""
    (tmp_path / "shapes").mkdir()
    (tmp_path / "shapes/code_names_shapes.ttl").write_bytes(
        blocks["shapes"].encode())
    (tmp_path / "shapes/code_names_bad_examples.ttl").write_bytes(
        blocks["fixture"].encode())
    namespace = {}
    exec(compile(blocks["test"], "docs/DEVELOPMENT.md (test)", "exec"),
         namespace)
    namespace["test_every_code_names_constraint_is_exercised"](tmp_path)


def test_the_project_test_fails_when_the_shape_finds_nothing(blocks,
                                                              tmp_path):
    """Guards the test above: the guide's project test is not vacuous."""
    (tmp_path / "shapes").mkdir()
    (tmp_path / "shapes/code_names_shapes.ttl").write_bytes(
        blocks["shapes"].encode())
    clean = "\n".join(line for line in blocks["fixture"].splitlines()
                      if not line.startswith(("my:P10008", "my:Planning",
                                              "my:P10011", "my:P10013",
                                              "my:P10014")))
    (tmp_path / "shapes/code_names_bad_examples.ttl").write_bytes(
        clean.encode())
    namespace = {}
    exec(compile(blocks["test"], "docs/DEVELOPMENT.md (test)", "exec"),
         namespace)
    with pytest.raises(AssertionError):
        namespace["test_every_code_names_constraint_is_exercised"](tmp_path)
