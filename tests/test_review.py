# SPDX-License-Identifier: MIT
"""The review register and imported candidates (backlog item 12, template
decisions 34 and 35): a person's answer to each candidate, by rule and
IRIs, under rules each refused by name."""

from __future__ import annotations

import datetime
import shutil

import pytest
import yaml

from conftest import load_tool

TODAY = datetime.date(2026, 11, 6)


@pytest.fixture(scope="module")
def review():
    return load_tool("t_review", "tools/review.py")


def entry(**fields):
    out = {"rule": "near-duplicate", "about": ["urn:a", "urn:b"],
           "validity": "real", "resolution": "fixed",
           "classified_by": "A. Damiano (proxy-domain-expert)",
           "reason": "merged"}
    out.update(fields)
    return {k: v for k, v in out.items() if v is not None}


def problems(review, *entries):
    kinds = ("ontologist", "domain-expert", "proxy-domain-expert",
             "architect", "rights-reviewer")
    return review.problems_of(list(entries), kinds)


def cand(rule="near-duplicate", about=("urn:b", "urn:a"), message="m"):
    return {"rule": rule, "about": sorted(about), "message": message,
            "evidence": {}}


def test_an_answer_passes(review):
    assert problems(review, entry()) == []


@pytest.mark.parametrize("fields, said", [
    ({"resolution": "fixed", "validity": "false-alarm"},
     "fixed requires validity real"),
    ({"resolution": "accepted", "validity": "unsure"},
     "accepted requires validity real"),
    ({"resolution": "not-a-defect", "validity": "real"},
     "not-a-defect requires validity false-alarm"),
    ({"validity": "false-alarm", "resolution": "deferred",
      "review": "2027-01-01"}, "a false-alarm is not-a-defect, or reported"),
    ({"validity": "unsure", "resolution": "fixed"},
     "unsure requires resolution deferred"),
    ({"validity": "unsure", "resolution": "deferred"},
     "deferred requires a review date"),
    ({"validity": "real", "resolution": "reported"},
     "reported requires a reference"),
    ({"review": "next week"}, "is not a date"),
    ({"review": "20270101"}, "is not a date (YYYY-MM-DD)"),
    ({"classified_by": "A. Damiano"}, "is not '<name> (<kind>)'"),
    ({"classified_by": "A. Damiano (stakeholder)"},
     "names the kind 'stakeholder'"),
    ({"validity": "maybe"}, "validity 'maybe' is not one of"),
    ({"resolution": "ignored"}, "resolution 'ignored' is not one of"),
    ({"about": "urn:a"}, "about is not a list of IRIs"),
    ({"reason": None}, "has no reason"),
    ({"colour": "red"}, "unknown field(s): colour"),
    ({"reason": "TODO why"}, "reason is still a placeholder"),
])
def test_each_rule_is_refused_by_name(review, fields, said):
    got = problems(review, entry(**fields))
    assert any(said in p for p in got), got


def test_a_repeated_answer_is_refused(review):
    got = problems(review, entry(), entry(about=["urn:b", "urn:a"]))
    assert any("repeats entry 1" in p for p in got), got


def test_answers_match_by_rule_and_iris_never_text(review):
    verdict = review.judge([cand(message="worded one way")],
                           [entry(text="worded another way")], TODAY)
    assert len(verdict["answered"]) == 1 and not verdict["unanswered"]
    verdict = review.judge([cand(rule="genus-differs")], [entry()], TODAY)
    assert len(verdict["unanswered"]) == 1


def test_an_answer_whose_candidate_is_gone_is_stale_unless_fixed(review):
    accepted = entry(resolution="accepted")
    verdict = review.judge([], [accepted, entry()], TODAY)
    assert verdict["stale"] == [accepted], "a fixed one is expected to go"


def test_a_deferred_answer_past_its_date_is_overdue(review):
    late = entry(validity="unsure", resolution="deferred",
                 review="2026-11-01")
    soon = entry(validity="unsure", resolution="deferred",
                 review="2026-12-01", about=["urn:c"])
    assert review.judge([], [late, soon], TODAY)["overdue"] == [late]


def test_a_proposal_is_refused_until_a_person_answers(review):
    rows = yaml.safe_load(review.propose([cand()]))
    assert rows[0]["about"] == ["urn:a", "urn:b"]
    got = problems(review, *rows)
    for key in ("validity", "resolution", "classified_by", "reason"):
        assert any("%s is still a placeholder" % key in p for p in got), key


def write(root, name, data):
    path = root / "review/candidates" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")


PROVENANCE = {"source": "model-review", "produced_by": "a person",
              "date": "2026-11-06", "corpus": "abc123"}


def test_an_import_is_read_with_its_provenance(review, tmp_path):
    write(tmp_path, "run.yaml", {"provenance": PROVENANCE, "candidates": [
        {"rule": "external:model-review", "about": ["urn:z", "urn:y"],
         "message": "look here"}]})
    [got] = review.imported(tmp_path)
    assert got["about"] == ["urn:y", "urn:z"]
    assert got["file"] == "review/candidates/run.yaml"
    assert got["corpus"] == "abc123"
    assert review.older([got], "abc123") == {}
    assert review.older([got], "def456") == {
        "review/candidates/run.yaml": "abc123"}


@pytest.mark.parametrize("change, said", [
    ({"corpus": None}, "provenance lacks corpus"),
    ({"produced_by": None}, "provenance lacks produced_by"),
    ({"model": "some-model"}, "provenance lacks prompt_sha256"),
])
def test_an_import_without_its_provenance_is_refused(review, tmp_path,
                                                     change, said):
    header = {k: v for k, v in dict(PROVENANCE, **change).items()
              if v is not None}
    write(tmp_path, "run.yaml", {"provenance": header, "candidates": []})
    with pytest.raises(review.RegisterError, match=said):
        review.imported(tmp_path)


def test_an_imported_rule_is_named_external(review, tmp_path):
    write(tmp_path, "run.yaml", {"provenance": PROVENANCE, "candidates": [
        {"rule": "near-duplicate", "about": ["urn:a"]}]})
    with pytest.raises(review.RegisterError, match="external:<source>"):
        review.imported(tmp_path)


def test_the_live_register_and_imports_are_usable(review, repo):
    assert review.load(repo) == []
    assert review.imported(repo) == []


def test_an_unknown_format_is_refused(review, repo, tmp_path):
    for name in ("config/review-register.yaml", "config/review.yaml"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / name, tmp_path / name)
    path = tmp_path / "config/review-register.yaml"
    path.write_bytes(path.read_bytes().replace(b"format_version: 1",
                                               b"format_version: 9"))
    with pytest.raises(review.RegisterError, match="format_version 9"):
        review.load(tmp_path)


def test_the_generator_proposes_through_the_register(repo, capsys):
    tool = load_tool("t_candidates_propose", "tools/ontology/candidates.py")
    assert tool.main(["--propose"]) == 0
    assert capsys.readouterr().out == "", "nothing to answer in the template"
