# SPDX-License-Identifier: MIT
"""A finding's classification in the register (P-A7, template decision 32).

Three questions kept apart -- is the finding true (validity), where is its
cause (origin), why is it in the register (resolution) -- and who answered
them, in what capacity (classified_by, with config/review.yaml's kinds,
P5's shared half). In WP6 the BPO Testing Team kept this in a document
beside the register; here each of decision 32's rules is a planted case,
and the line it draws -- a person's conclusion never decides what the
gate passes -- is a test of its own.
"""

from __future__ import annotations

import datetime
import shutil

import pytest
import yaml

from conftest import load_tool

TODAY = datetime.date(2026, 11, 6)


@pytest.fixture(scope="module")
def register():
    return load_tool("t_classification", "tools/findings.py")


def finding(register, focus="urn:x", severity="Warning"):
    return register.finding("validate", "validation.a", focus,
                            "urn:shape:a", "m", severity)


def entry(register, record=None, **fields):
    record = record or finding(register)
    out = {key: record[key] for key in register.IDENTITY}
    out.update(reason="planted", owner="the suite", review="2027-01-01",
               validity="real", origin="project", resolution="accepted",
               classified_by="A. Reviewer (ontologist)")
    out.update(fields)
    return {k: v for k, v in out.items() if v is not None}


def problems(register, *entries, version=2):
    return register.problems_of(list(entries), version=version)


def test_a_classified_entry_passes_in_both_versions(register):
    assert problems(register, entry(register)) == []
    assert problems(register, entry(register), version=1) == []


@pytest.mark.parametrize("fields, said", [
    ({"resolution": "accepted", "validity": "false-alarm"},
     "accepted requires validity real"),
    ({"resolution": "accepted", "validity": "unsure"},
     "accepted requires validity real"),
    ({"resolution": "not-a-defect", "validity": "real"},
     "not-a-defect requires validity false-alarm"),
    ({"validity": "false-alarm", "resolution": "deferred"},
     "a false-alarm is not-a-defect, or reported"),
    ({"validity": "unsure", "resolution": "reported", "reference": "#1"},
     "unsure requires resolution deferred"),
    ({"origin": "unknown", "validity": "real", "resolution": "deferred"},
     "origin unknown requires validity unsure and resolution deferred"),
    ({"origin": "unknown", "validity": "unsure", "resolution": "reported",
      "reference": "#1"},
     "origin unknown requires validity unsure and resolution deferred"),
    ({"origin": "upstream"}, "origin upstream requires the upstream field"),
    ({"resolution": "reported", "validity": "real"},
     "reported requires a reference"),
    ({"classified_by": "A. Reviewer"}, "is not '<name> (<kind>)'"),
    ({"classified_by": "A. Reviewer (lawyer)"},
     "names the kind 'lawyer', which config/review.yaml does not declare"),
    ({"validity": "maybe"}, "validity 'maybe' is not one of"),
    ({"origin": "elsewhere"}, "origin 'elsewhere' is not one of"),
    ({"resolution": "ignored"}, "resolution 'ignored' is not one of"),
])
def test_each_rule_of_decision_32_is_refused_by_name(register, fields, said):
    got = problems(register, entry(register, **fields))
    assert any(said in p for p in got), got
    got = problems(register, entry(register, **fields), version=1)
    assert any(said in p for p in got), (
        "a field given is checked in version 1 as well: %s" % got)


@pytest.mark.parametrize("fields", [
    {"validity": "real", "resolution": "deferred"},
    {"validity": "real", "resolution": "reported", "reference": "#12"},
    {"validity": "false-alarm", "resolution": "not-a-defect",
     "origin": "template"},
    {"validity": "false-alarm", "resolution": "reported",
     "origin": "template", "reference": "https://example.invalid/issue/3"},
    {"validity": "unsure", "resolution": "deferred", "origin": "unknown"},
    {"classified_by": "Jane Doe (domain-expert)"},
    {"classified_by": "Jane Doe (proxy-domain-expert)"},
    {"classified_by": "Jane Doe (architect)"},
])
def test_what_the_rules_allow_passes(register, fields):
    assert problems(register, entry(register, **fields)) == []


def test_upstream_origin_needs_the_field_and_not_the_reverse(register):
    """Decision 32: citing an upstream IRI does not make the upstream the
    cause. An upstream focus still needs `upstream`, and may be the
    project's defect."""
    sources = register.upstream_ids()
    iri = sources["CCO"] + "ont00001180"
    on_cco = finding(register, focus=iri)
    named = entry(register, on_cco, upstream="CCO " + iri)
    assert problems(register, dict(named, origin="upstream")) == []
    assert problems(register, dict(named, origin="project")) == []


def test_version_2_requires_every_field_and_version_1_counts_the_gap(
        register):
    bare = entry(register, validity=None, origin=None, resolution=None,
                 classified_by=None)
    assert problems(register, bare, version=1) == []
    got = problems(register, bare, version=2)
    for key in register.CLASSIFICATION:
        assert any("has no %s (format_version 2" % key in p for p in got), key
    tally = register.counts([bare, entry(register)])
    assert tally["unclassified"] == 1
    assert tally["validity"] == {"real": 1, "unclassified": 1}


def test_a_placeholder_is_never_a_judgement(register):
    for key in register.CLASSIFICATION:
        got = problems(register, entry(register, **{key: "TODO x"}),
                       version=1)
        assert any("%s is still a placeholder" % key in p for p in got), key


def test_the_gate_does_not_read_the_classification(register):
    """The line decision 32 draws: the same findings, accepted by the same
    identities, give the same verdict whatever a person concluded."""
    a = finding(register, "urn:a")
    b = finding(register, "urn:b")
    c = finding(register, "urn:c", severity="Violation")
    verdicts = []
    for fields in ({}, {"validity": "false-alarm", "resolution":
                        "not-a-defect", "origin": "template"},
                   {"validity": "unsure", "resolution": "deferred",
                    "origin": "unknown"},
                   {"validity": None, "origin": None, "resolution": None,
                    "classified_by": None}):
        entries = [entry(register, a, **fields), entry(register, b, **fields)]
        verdict = register.judge("validate", [a, c], entries, TODAY)
        verdicts.append((verdict["passed"],
                         [r["focus"] for r in verdict["accepted"]],
                         [r["focus"] for r in verdict["failing"]],
                         [e["focus"] for e in verdict["stale"]]))
    assert len(set(map(repr, verdicts))) == 1, verdicts
    assert verdicts[0] == (False, ["urn:a"], ["urn:c"], ["urn:b"])


def test_classify_lists_the_unclassified_and_judges_nothing(register):
    bare = entry(register, validity=None, origin=None, resolution=None,
                 classified_by=None)
    half = entry(register, finding(register, "urn:h"), validity="real",
                 origin=None, resolution=None, classified_by=None)
    done = entry(register, finding(register, "urn:d"))
    rows = yaml.safe_load(register.classify([bare, half, done]))
    assert [r["focus"] for r in rows] == ["urn:x", "urn:h"]
    assert rows[1]["validity"] == "real", "what a person gave is kept"
    for row in rows:
        for key in register.CLASSIFICATION:
            value = str(row[key])
            assert value.startswith("TODO") or (row is rows[1]
                                                and key == "validity")
    assert register.problems_of(rows, version=1), (
        "the listing is refused until a person answers it")


def test_the_report_counts_by_field_check_rung_and_rule(register,
                                                        monkeypatch, capsys):
    entries = [entry(register),
               entry(register, finding(register, "urn:f"),
                     validity="false-alarm", resolution="not-a-defect",
                     origin="template"),
               entry(register, finding(register, "urn:u"), validity=None,
                     origin=None, resolution=None, classified_by=None)]
    monkeypatch.setattr(register, "load", lambda root=None: entries)
    assert register.main([]) == 0
    out = capsys.readouterr().out
    assert "validity   false-alarm 1, real 1, unclassified 1" in out
    assert "resolution accepted 1, not-a-defect 1, unclassified 1" in out
    assert "1 unclassified: no judgement is recorded" in out
    assert ("validity  validate validation.a: false-alarm 1, real 1, "
            "unclassified 1") in out
    assert "validity  validate rule urn:shape:a:" in out


def test_the_live_register_is_version_2(register, repo):
    raw = yaml.safe_load((repo / "config/findings-register.yaml").read_text(
        encoding="utf-8"))
    assert raw["format_version"] == 2


def test_an_unknown_format_is_refused(register, repo, tmp_path):
    for name in ("config/findings-register.yaml", "config/review.yaml",
                 "config/upstream-sources.yaml"):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / name, tmp_path / name)
    path = tmp_path / "config/findings-register.yaml"
    path.write_bytes(path.read_bytes().replace(b"format_version: 2",
                                               b"format_version: 3"))
    with pytest.raises(register.RegisterError, match="format_version 3"):
        register.load(tmp_path)


def test_the_review_kinds_keep_the_template_four(register, repo, tmp_path):
    """Decision 32: a project may extend the kinds, not remove these; and
    a rights reviewer is said to imply no legal approval."""
    text = (repo / "config/review.yaml").read_text(encoding="utf-8")
    assert set(register.review_kinds(repo)) >= set(register.KINDS)
    kinds = yaml.safe_load(text)["kinds"]
    assert "no legal approval" in " ".join(kinds["rights-reviewer"].split())
    (tmp_path / "config").mkdir()
    (tmp_path / "config/review.yaml").write_text(
        text.replace("  architect: >-", "  steward: >-"), encoding="utf-8")
    with pytest.raises(register.RegisterError, match="lacks the kind"):
        register.review_kinds(tmp_path)
    (tmp_path / "config/review.yaml").write_text(
        text + "  steward: >-\n    Keeps the vocabulary.\n", encoding="utf-8")
    assert "steward" in register.review_kinds(tmp_path)


def test_the_renamed_kind_is_named_in_the_refusal(register, repo,
                                                   tmp_path):
    """Decision 35: domain-practitioner became domain-expert. A project's
    older review.yaml, or an entry still naming the old kind, is refused
    with the rename in the message."""
    text = (repo / "config/review.yaml").read_text(encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "config/review.yaml").write_text(
        text.replace("  domain-expert: >-", "  domain-practitioner: >-"),
        encoding="utf-8")
    with pytest.raises(register.RegisterError,
                       match="domain-practitioner is now domain-expert"):
        register.review_kinds(tmp_path)
    got = problems(register, entry(
        register, classified_by="Jane Doe (domain-practitioner)"))
    assert any("renamed domain-expert" in p for p in got), got


def test_the_review_roles_are_decision_35s(register, repo):
    kinds = register.review_kinds(repo)
    for kind in ("domain-expert", "proxy-domain-expert", "ontologist"):
        assert kind in kinds, kind
    assert "domain-practitioner" not in kinds


def test_the_site_shows_the_classification(register):
    """The status page carries the counts, and the explorer's record of a
    term carries each entry's fields (ACCEPTED_FIELDS)."""
    site = load_tool("t_classification_site", "tools/site/build_site.py")
    for key in register.CLASSIFICATION + ("reference",):
        assert key in site.ACCEPTED_FIELDS, key
    entries = [entry(register),
               entry(register, finding(register, "urn:u"), validity=None,
                     origin=None, resolution=None, classified_by=None)]
    html = site.register_section(entries)
    assert "Classified by a person: validity real 1, unclassified 1" in html
    assert "1 entry is unclassified" in html
    assert "Every entry is classified." in site.register_section(
        entries[:1])
