# SPDX-License-Identifier: MIT
"""The source register and source adequacy (P4, template decision 36).

Each rule has a planted case refused by name and a near miss that passes,
on a small project built in a temporary directory: its own register, its
own decision files, its own git history for the reference scan. The
regressions decision 36 names -- stable claim ids, a whole-source
citation with no claims, stale exceptions, mentions -- are among them.
"""

from __future__ import annotations

import shutil
import subprocess

import pytest
import yaml

from conftest import load_tool


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_sources", "tools/sources.py")


ENTRY = {"id": "SRC-STD-01", "citation": "Example Body, Example Standard, 2021",
         "claims": [{"id": "C1", "status": "V", "scope": "clauses 1 to 5"},
                    {"id": "C2", "status": "L", "scope": "annex B"}]}
READ = {"id": "SRC-STD-02", "citation": "Example Body, Another Standard, 2022",
        "claims": [{"id": "C1", "status": "V", "scope": "all of it"},
                   {"id": "C2", "status": "P", "scope": "chapters 1 to 3"}]}
UNCLAIMED = {"id": "SRC-STD-03", "citation": "Example Body, Unread, 2023"}
EXCEPTION = {"citation": "SRC-STD-01-C2",
             "in": "docs/decisions/2026-11-10-placement.md",
             "scope": "the annex's title only",
             "reason": "named, not relied on for content",
             "approved_by": "A. Damiano (architect)"}


def project(tool, repo, root, decisions=None, entries=(ENTRY, READ),
            exceptions=(), settings=None, write=True):
    """A project with this register and these decision files, committed so
    the reference scan sees them."""
    for name in ("config/review.yaml",):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / name, root / name)
    (root / "config/sources.yaml").write_text(yaml.safe_dump(
        dict({"version": 1}, **(settings or {}))), encoding="utf-8")
    (root / "research").mkdir(exist_ok=True)
    raw = {"format_version": 1, "entries": [dict(e) for e in entries],
           "exceptions": [dict(x) for x in exceptions]}
    (root / "research/sources.yaml").write_text(yaml.safe_dump(raw),
                                                encoding="utf-8")
    for name, text in (decisions or {}).items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    if write:
        (root / "research/sources.md").write_bytes(
            tool.markdown(raw).encode("utf-8"))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    return root


def check(tool, root):
    return tool.check(root)


def said(result, text):
    return any(text in p for p in result["problems"])


DECISION = "docs/decisions/2026-11-10-placement.md"


# ------------------------------------------------------------- adequacy


def test_a_v_claim_is_adequate(tool, repo, tmp_path):
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Placed under X, per SRC-STD-01-C1.\n"}))
    assert result["problems"] == []
    assert [r["verdict"] for r in result["rows"]] == ["adequate"]


def test_an_l_claim_is_refused(tool, repo, tmp_path):
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Placed under X, per SRC-STD-01-C2.\n"}))
    assert said(result, "%s: cites SRC-STD-01-C2, which is not graded V or P"
                % DECISION), result["problems"]


def test_a_whole_source_needs_every_claim_read(tool, repo, tmp_path):
    """One V claim beside an L claim does not make the source adequate."""
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Per SRC-STD-01 and SRC-STD-02.\n"}))
    verdicts = {r["citation"]: r["verdict"] for r in result["rows"]}
    assert verdicts == {"SRC-STD-01": "inadequate", "SRC-STD-02": "adequate"}
    assert said(result, "in every claim")


def test_a_whole_source_with_no_claim_is_refused(tool, repo, tmp_path):
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Per SRC-STD-03.\n"}, entries=(ENTRY, READ, UNCLAIMED)))
    assert said(result, "cites SRC-STD-03, which is not graded V or P in "
                "every claim (or has no claim)"), result["problems"]


def test_a_mention_is_not_evaluated(tool, repo, tmp_path):
    """Decision 36 C: a source named as background is not evidence."""
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "An annex exists (mention:SRC-STD-01-C2); see also "
                  "mention:SRC-STD-03.\n"}, entries=(ENTRY, READ, UNCLAIMED)))
    assert result["problems"] == []
    assert {r["verdict"] for r in result["rows"]} == {"mention"}


def test_a_mention_must_still_resolve(tool, repo, tmp_path):
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "mention:SRC-STD-09\n"}))
    assert said(result, "SRC-STD-09 names nothing"), result["problems"]


def test_an_exception_excuses_one_citation_in_one_file(tool, repo,
                                                      tmp_path):
    other = "docs/decisions/2026-11-11-other.md"
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Per SRC-STD-01-C2.\n", other: "Per SRC-STD-01-C2.\n"},
        exceptions=(EXCEPTION,)))
    verdicts = {r["file"]: r["verdict"] for r in result["rows"]}
    assert verdicts == {DECISION: "excused", other: "inadequate"}
    assert said(result, "%s: cites SRC-STD-01-C2" % other)
    assert not said(result, "%s: cites" % DECISION)


def test_an_exception_never_changes_the_grade(tool, repo, tmp_path):
    root = project(tool, repo, tmp_path, {DECISION: "Per SRC-STD-01-C2.\n"},
                   exceptions=(EXCEPTION,))
    raw = tool.register(root)
    assert tool.index(raw)["SRC-STD-01"]["claims"]["C2"] == "L"
    assert "| SRC-STD-01-C2 | L |" in tool.markdown(raw)


def test_an_exception_whose_citation_is_gone_is_stale(tool, repo, tmp_path):
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Per SRC-STD-01-C1.\n"}, exceptions=(EXCEPTION,)))
    assert said(result, "is stale: %s no longer cites SRC-STD-01-C2"
                % DECISION), result["problems"]


def test_an_exception_whose_claim_is_now_read_is_stale(tool, repo,
                                                       tmp_path):
    read = dict(ENTRY, claims=[ENTRY["claims"][0],
                               {"id": "C2", "status": "V",
                                "scope": "annex B"}])
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Per SRC-STD-01-C2.\n"}, entries=(read, READ),
        exceptions=(EXCEPTION,)))
    assert said(result, "is stale: SRC-STD-01-C2 is now adequate")


@pytest.mark.parametrize("change, text", [
    ({"approved_by": "A. Damiano (proxy-domain-expert)"},
     "approved as proxy-domain-expert, which may not approve"),
    ({"approved_by": "A. Damiano"}, "is not '<name> (<kind>)'"),
    ({"scope": None}, "has no scope"),
    ({"in": "docs/notes.md"}, "is not a decision file"),
    ({"colour": "red"}, "unknown field colour"),
])
def test_an_exception_is_complete_and_approved_by_an_allowed_role(
        tool, repo, tmp_path, change, text):
    item = {k: v for k, v in dict(EXCEPTION, **change).items()
            if v is not None}
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Per SRC-STD-01-C2.\n"}, exceptions=(item,)))
    assert said(result, text), result["problems"]


def test_a_delegated_kind_needs_its_recorded_delegation(tool, repo,
                                                        tmp_path):
    """Decision 36: adding a kind confers no authority by itself."""
    item = dict(EXCEPTION, approved_by="O. Logist (ontologist)")
    delegation = "docs/decisions/2026-11-09-delegation.md"
    base = {DECISION: "Per SRC-STD-01-C2.\n"}
    loose = check(tool, project(tool, repo, tmp_path / "a", base,
                                exceptions=(item,), settings={
        "exception_approvers": [{"kind": "architect"},
                                {"kind": "ontologist"}]}))
    assert said(loose, "ontologist may approve exceptions only by a "
                "recorded delegation"), loose["problems"]
    recorded = check(tool, project(tool, repo, tmp_path / "b", dict(
        base, **{delegation: "The architect delegates.\n"}),
        exceptions=(item,), settings={"exception_approvers": [
            {"kind": "architect"},
            {"kind": "ontologist", "delegated_by": delegation}]}))
    assert recorded["problems"] == []


def test_no_citation_passes_and_says_it_proves_nothing(tool, repo, tmp_path,
                                                       monkeypatch, capsys):
    root = project(tool, repo, tmp_path, {DECISION: "No source here.\n"})
    monkeypatch.setattr(tool.layout, "repository_root", lambda: root)
    assert tool.main([]) == 0
    out = capsys.readouterr().out
    assert "0 citation(s) evaluated" in out
    assert "not evidence that the decisions are well sourced" in out


def test_only_decision_files_are_held(tool, repo, tmp_path):
    result = check(tool, project(tool, repo, tmp_path, {
        "research/notes.md": "Read SRC-STD-01-C2 next.\n"}))
    assert result["problems"] == [] and result["rows"] == []


# -------------------------------------------------------- the register


def problems(tool, *entries, limit=None):
    settings = dict(tool.DEFAULTS, max_quote_words=limit)
    return tool.register_problems({"format_version": 1,
                                   "entries": list(entries)}, settings)


@pytest.mark.parametrize("entry, text", [
    (dict(ENTRY, claims=[{"status": "V", "scope": "all"}]),
     "id None is not C<n>; a claim's id is explicit and stable"),
    (dict(ENTRY, claims=[{"id": "C1", "status": "V", "scope": "a"},
                         {"id": "C1", "status": "S"}]), "id C1 is repeated"),
    (dict(ENTRY, claims=[{"id": "C1", "status": "V/P", "scope": "a"}]),
     "is not exactly one of V, P, S, K, L"),
    (dict(ENTRY, claims=[{"id": "C1", "status": "P"}]),
     "a P claim states its scope"),
    (dict(ENTRY, id="SRC-std-1"), "id is not SRC-<FAMILY>-<NN>"),
    (dict(ENTRY, citation=None), "has no citation"),
    (dict(ENTRY, authority="A1"), "unknown field authority"),
    (dict(ENTRY, summary='Defines the "category" of things.'),
     "summary has a typed quotation mark"),
    (dict(ENTRY, summary="As it says, {Q2}."),
     "has the placeholder {Q2}, which names no quote"),
    (dict(ENTRY, quotes=[{"key": "SRC-STD-02-Q1", "text": "x"}]),
     "quote key 'SRC-STD-02-Q1' is not SRC-STD-01-Q<n>"),
])
def test_each_register_rule_is_refused_by_name(tool, entry, text):
    got = problems(tool, entry)
    assert any(text in p for p in got), got


def test_a_well_formed_entry_with_a_quote_and_a_mention_passes(tool):
    entry = dict(ENTRY, quotes=[{"key": "SRC-STD-01-Q1",
                                 "text": "a category is a kind"}],
                 summary="Its {mention:Categories} clause says {Q1}.")
    assert problems(tool, entry) == []
    assert "“a category is a kind”" in tool.markdown(
        {"entries": [entry]})


def test_a_repeated_entry_is_refused(tool):
    assert any("is listed twice" in p for p in problems(tool, ENTRY, ENTRY))


def test_the_quote_limit_is_the_projects(tool):
    entry = dict(ENTRY, quotes=[{"key": "SRC-STD-01-Q1",
                                 "text": "one two three four five six"}])
    assert problems(tool, entry) == []
    assert any("has 6 words; this project's limit is 5" in p
               for p in problems(tool, entry, limit=5))


def test_a_claim_keeps_its_id_when_the_list_is_reordered(tool, repo,
                                                         tmp_path):
    """Decision 36 A: a citation never depends on a claim's position."""
    swapped = dict(ENTRY, claims=list(reversed(ENTRY["claims"])))
    result = check(tool, project(tool, repo, tmp_path, {
        DECISION: "Per SRC-STD-01-C1.\n"}, entries=(swapped, READ)))
    assert result["problems"] == []
    assert [r["verdict"] for r in result["rows"]] == ["adequate"]


# ------------------------------------------------- references, the output


def test_every_reference_in_a_tracked_file_resolves(tool, repo, tmp_path):
    result = check(tool, project(tool, repo, tmp_path, {
        "research/notes.md": "See SRC-STD-01-C9, SRC-STD-07 and "
                             "SRC-STD-01-Q1.\n"}))
    for missing in ("SRC-STD-01-C9", "SRC-STD-07", "SRC-STD-01-Q1"):
        assert said(result, "%s names nothing" % missing), missing


def test_shorthand_continuations_are_expanded(tool):
    assert tool.references("SRC-FO-01, -02 and SRC-OG-01/03") == [
        "SRC-FO-01", "SRC-FO-02", "SRC-OG-01", "SRC-OG-03"]
    assert tool.references("mention:SRC-FO-01") == []


def test_a_stale_markdown_register_is_refused(tool, repo, tmp_path):
    root = project(tool, repo, tmp_path, write=False)
    (root / "research/sources.md").write_text("old\n", encoding="utf-8")
    assert said(check(tool, root), "is not what research/sources.yaml "
                "generates")


def test_the_template_passes(tool, repo):
    result = tool.check(repo)
    assert result["problems"] == [], result["problems"]
    assert result["entries"] == 0


def test_the_settings_are_checked(tool, tmp_path):
    (tmp_path / "config").mkdir()
    path = tmp_path / "config/sources.yaml"
    path.write_text("version: 1\nmax_quote_words: 0\n", encoding="utf-8")
    with pytest.raises(tool.Unreadable, match="max_quote_words"):
        tool.configuration(tmp_path)
    path.write_text("version: 1\nstrict: false\n", encoding="utf-8")
    with pytest.raises(tool.Unreadable, match="unknown setting"):
        tool.configuration(tmp_path)
