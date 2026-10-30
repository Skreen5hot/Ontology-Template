# SPDX-License-Identifier: MIT
"""The stage check (tools/stages.py, decision 21): config/stages.yaml as
shipped passes, and each refusal is shown on a constructed file that
differs from a passing one in one way."""

from __future__ import annotations

import copy

import pytest
import yaml

from conftest import load_tool


@pytest.fixture()
def stages():
    return load_tool("t_stages", "tools/stages.py")


SKELETON = b"# Standard: (stage id)\n"
COMPONENTS = {"research", "mappings", "docs.charter"}


def passing():
    """Two path stages and a lane, the first stage done under a standard,
    the second started under one, the lane started early."""
    return {
        "version": 1,
        "path": [
            {"id": "charter", "runs": True, "status": "done",
             "standard": "docs/standards/charter.md",
             "where": ["docs.charter"]},
            {"id": "sources", "runs": True, "status": "in-progress",
             "standard": "docs/standards/sources.md", "where": ["research"]},
            {"id": "specification", "runs": False, "status": "not-started",
             "standard": None, "where": []},
        ],
        "lanes": [
            {"id": "thesaurus", "runs": True, "status": "in-progress",
             "standard": "docs/standards/thesaurus.md",
             "where": ["mappings"], "joins": ["sources"]},
        ],
    }


@pytest.fixture()
def root(tmp_path):
    standards = tmp_path / "docs/standards"
    standards.mkdir(parents=True)
    for name in ("charter", "sources", "thesaurus"):
        (standards / (name + ".md")).write_bytes(
            b"# Standard: " + name.encode() + b"\n")
    return tmp_path


def problems(stages, root, raw):
    return stages.problems_of(raw, root, COMPONENTS, SKELETON)


def test_the_constructed_file_passes(stages, root):
    """The positive control the refusals below are measured against."""
    assert problems(stages, root, passing()) == []


def test_the_shipped_file_passes(stages):
    found, problems_found = stages.check()
    assert problems_found == [], problems_found
    assert len(found) >= 9
    assert {s["kind"] for s in found} == {"path", "lanes"}


def changed(edit):
    raw = copy.deepcopy(passing())
    edit(raw)
    assert raw != passing()
    return raw


def stage(raw, name):
    return next(s for s in raw["path"] + raw["lanes"] if s["id"] == name)


REFUSALS = {
    "started without a standard": (
        lambda r: stage(r, "sources").update(standard=None),
        "sources: is in-progress with no standard"),
    "a standard that does not exist": (
        lambda r: stage(r, "sources").update(
            standard="docs/standards/gone.md"),
        "standard docs/standards/gone.md does not exist"),
    "done out of order": (
        lambda r: (stage(r, "charter").update(status="in-progress"),
                   stage(r, "sources").update(status="done")),
        "sources: is done, but charter, before it on the path, is "
        "in-progress"),
    "a lane done before what it joins": (
        lambda r: stage(r, "thesaurus").update(status="done"),
        "thesaurus: is done, but sources, which it joins, is in-progress"),
    "a lane joining no path stage": (
        lambda r: stage(r, "thesaurus").update(joins=["taxonomy"]),
        "thesaurus: joins 'taxonomy', which is not a path stage"),
    "a stage not run, started": (
        lambda r: stage(r, "specification").update(
            status="in-progress", standard="docs/standards/charter.md"),
        "specification: is in-progress, but the project does not run it"),
    "an unknown status": (
        lambda r: stage(r, "charter").update(status="finished"),
        "charter: status 'finished' is not one of"),
    "runs not a boolean": (
        lambda r: stage(r, "charter").update(runs="yes"),
        "charter: runs is 'yes', not true or false"),
    "an undeclared component": (
        lambda r: stage(r, "sources").update(where=["sources.register"]),
        "where names 'sources.register', which the layout contract does "
        "not declare"),
    "listed twice": (
        lambda r: r["lanes"].append(dict(stage(r, "thesaurus"))),
        "thesaurus: listed twice"),
    "a missing field": (
        lambda r: stage(r, "charter").pop("standard"),
        "charter: missing standard"),
    "a lane without joins": (
        lambda r: stage(r, "thesaurus").pop("joins"),
        "thesaurus: missing joins"),
    "no path": (
        lambda r: r.update(path=[]),
        "no path stages"),
    "another version": (
        lambda r: r.update(version=2),
        "version is 2, not 1"),
}


@pytest.mark.parametrize("case", sorted(REFUSALS))
def test_each_refusal(stages, root, case):
    edit, expected = REFUSALS[case]
    found = problems(stages, root, changed(edit))
    assert any(expected in f for f in found), found


def test_the_blank_skeleton_is_not_a_standard(stages, root):
    (root / "docs/standards/sources.md").write_bytes(SKELETON)
    found = problems(stages, root, passing())
    assert found == ["sources: standard docs/standards/sources.md is the "
                     "blank skeleton, not filled in"], found


def test_a_stage_not_run_does_not_hold_the_path(stages, root):
    """specification does not run, so a stage after it may be done while
    it has not started; the same file with it running is refused."""
    raw = passing()
    raw["path"].append({"id": "formalization", "runs": True,
                        "status": "done",
                        "standard": "docs/standards/charter.md",
                        "where": []})
    stage(raw, "sources").update(status="done")
    assert problems(stages, root, raw) == []
    stage(raw, "specification").update(runs=True)
    found = problems(stages, root, raw)
    assert found == ["formalization: is done, but specification, before "
                     "it on the path, is not-started"], found


def test_main_reads_the_file_the_layout_names(stages, repo, monkeypatch,
                                              capsys, tmp_path):
    """main, not only problems_of: a started stage with no standard in the
    file the contract declares fails the command."""
    raw = yaml.safe_load((repo / "config/stages.yaml").read_text(
        encoding="utf-8"))
    raw["path"][0]["status"] = "in-progress"
    path = tmp_path / "stages.yaml"
    path.write_bytes(yaml.safe_dump(raw).encode())
    real = stages.layout.path
    monkeypatch.setattr(stages.layout, "path", lambda cid: path
                        if cid == "config.stages" else real(cid))
    assert stages.main([]) == 1
    out = capsys.readouterr().out
    assert "charter: is in-progress with no standard" in out
    assert "1 finding(s)" in out


def test_the_shipped_skeleton_is_the_one_refused(stages, repo):
    """The skeleton the check compares against is the one docs/standards
    ships, and copying it unchanged is refused."""
    skeleton = (repo / "docs/standards" / stages.SKELETON).read_bytes()
    assert skeleton.startswith(b"# Standard:")
    raw = passing()
    found = stages.problems_of(raw, repo, COMPONENTS, skeleton)
    assert any("does not exist" in f for f in found)
    stage(raw, "charter").update(
        standard="docs/standards/" + stages.SKELETON)
    found = stages.problems_of(raw, repo, COMPONENTS, skeleton)
    assert any("charter: standard docs/standards/stage-standard.md is the "
               "blank skeleton" in f for f in found), found
