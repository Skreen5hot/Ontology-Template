# SPDX-License-Identifier: MIT
"""Crosswalks: an SSSOM mapping set that holds passes, and each rule breaks.

tests/fixtures/mappings/good.sssom.tsv must pass; bad.sssom.tsv breaks one
rule per row, numbered in its comment column, and the test names the
finding each row must produce. `{{namespace}}` is filled in on the way to a
temporary directory, so the fixtures name no project.
"""

from __future__ import annotations

import pytest

from conftest import load_tool

FIXTURES = "tests/fixtures/mappings"

#: Row of bad.sssom.tsv -> a phrase its finding must contain.
BAD_ROWS = {
    1: "is not a term an authored module declares",
    2: "is this project's own term",
    3: "is a term of a pinned upstream",
    4: "whose prefix the curie_map does not declare",
    5: "is not a SKOS mapping property",
    6: "is not a semapv: term",
    7: "needs object_type",
    8: "between a owl class and a skos concept",
    9: "owl:equivalentClass from a skos concept",
    11: "repeats row 10",
}


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_mappings", "tools/ontology/mappings.py")


@pytest.fixture(scope="module")
def written(repo, project, tmp_path_factory):
    target = tmp_path_factory.mktemp("mappings")
    out = {}
    for source in sorted((repo / FIXTURES).glob("*")):
        path = target / source.name
        path.write_bytes(source.read_bytes().decode("utf-8").replace(
            "{{namespace}}", project.namespace()).encode("utf-8"))
        out[source.name.split(".")[0]] = path
    return out


def test_a_mapping_set_that_holds_passes(tool, written):
    record = tool.check([written["good"]], modules=[written["terms"]])
    assert record["ok"], record["findings"]
    assert record["rows"] == 5


def test_each_bad_row_gets_its_finding(tool, written):
    record = tool.check([written["bad"]], modules=[written["terms"]])
    findings = record["findings"]
    for number, phrase in BAD_ROWS.items():
        hits = [f for f in findings
                if ("row %d:" % number) in f and phrase in f]
        assert hits, "row %d: %r not found in %s" % (number, phrase, findings)
    assert not [f for f in findings if "row 10:" in f], (
        "the control row 10 was reported")


def test_metadata_that_names_nothing_is_refused(tool, tmp_path, written):
    path = tmp_path / "bare.sssom.tsv"
    path.write_text("# curie_map:\n#   p: https://x.invalid/\n"
                    "subject_id\tpredicate_id\tobject_id\n", encoding="utf-8")
    record = tool.check([path], modules=[written["terms"]])
    for phrase in ("names no mapping_set_id", "names no license",
                   "no creator_id or creator_label", "semapv",
                   "no mapping_justification column"):
        assert any(phrase in f for f in record["findings"]), (phrase,
                                                              record)


def test_a_file_that_is_not_sssom_exits_2(tool, written):
    assert tool.main([str(written["unreadable"])]) == 2


def test_the_live_record_is_clean_and_never_in_the_ontology(tool, layout,
                                                            repo):
    """A fresh project has no mapping sets and says so; and whatever
    mapping sets there are, they are in no scope a check loads as
    ontology."""
    assert tool.main([]) == 0
    scope = {p.resolve() for p in layout.ontology_files()
             + layout.vendored_files()}
    for path in tool.mapping_files():
        assert path.resolve() not in scope
    component = layout.component("mappings")
    assert component.role == "mapping-set"
