# SPDX-License-Identifier: MIT
"""Decision propagation (P7, template decision 38).

Each refusal has a planted case refused by name and a near miss that
passes, on a small project built in a temporary directory with its own
records, targets and git index. The three safeguards of decision 38 are
among them: a target not yet created is owed, not refused, and holds its
stage until it is created, tracked and cites the decision; an owed target
no stage holds stops a release until it is assigned or accounted for;
and a citation is the identifier exactly, never a longer one, never the
record itself.
"""

from __future__ import annotations

import subprocess

import pytest
import yaml

from conftest import load_tool


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_decisions", "tools/decisions.py")


ID = "2026-11-10-placement"
RECORD = "docs/decisions/%s.md" % ID
LATER = "docs/decisions/2026-11-12-scope.md"
CHARTER = "docs/charter.md"
MODULE = "ontology/core.ttl"
#: Which component each test file belongs to, as the layout would say.
OWNERS = {CHARTER: "docs.charter", MODULE: "ontology.main",
          "notes/loose.md": None}


def owner(path):
    return OWNERS.get(path)


def stages(charter="in-progress", formalization="in-progress",
           formalization_runs=True):
    return [{"id": "charter", "runs": True, "status": charter,
             "where": ["docs.charter"]},
            {"id": "formalization", "runs": formalization_runs,
             "status": formalization, "where": ["ontology.main"]}]


def block(targets=(), nothing=None, **extra):
    fields = {"carries_into": list(targets)}
    if nothing is not None:
        fields["carries_nothing"] = nothing
    fields.update(extra)
    return "---\n%s---\n# %s\n\nThe act.\n" % (yaml.safe_dump(fields), ID)


def project(root, files, settings=None, untracked=()):
    """A project with these files, all tracked but the untracked ones."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config/decisions.yaml").write_text(yaml.safe_dump(
        dict({"version": 1}, **(settings or {}))), encoding="utf-8")
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    for name in untracked:
        subprocess.run(["git", "rm", "-q", "--cached", name], cwd=root,
                       check=True)
    return root


def check(tool, root, plan=None):
    return tool.check(root, plan if plan is not None else stages(), owner)


def said(result, text):
    return any(text in p for p in result["problems"])


def states(result):
    return {(r["decision"], r["target"]): r["state"]
            for r in result["owed"]}


# ------------------------------------------------------------ carrying


def test_a_target_citing_the_decision_carries_it(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]),
        CHARTER: "Placed as %s decided.\n" % ID}))
    assert result["problems"] == [] and result["owed"] == []
    assert result["decided"][0]["targets"] == [
        {"target": CHARTER, "state": "carried"}]


def test_a_target_citing_the_record_by_path_carries_it(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]),
        CHARTER: "See [the decision](%s).\n" % RECORD}))
    assert result["problems"] == [] and result["owed"] == []


def test_a_turtle_comment_carries_it(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([MODULE]),
        MODULE: "# decision %s\n@prefix ex: <http://example.org/> .\n" % ID}))
    assert result["owed"] == []


def test_a_tracked_target_not_citing_it_is_owed_not_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]), CHARTER: "Nothing yet.\n"}))
    assert result["problems"] == []
    assert states(result) == {(ID, CHARTER): "uncited"}


def test_a_target_not_yet_created_is_owed_not_refused(tool, tmp_path):
    """Decision 38, safeguard 1."""
    result = check(tool, project(tmp_path, {RECORD: block([MODULE])}))
    assert result["problems"] == []
    assert states(result) == {(ID, MODULE): "missing"}


def test_a_target_created_but_not_tracked_is_owed(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]), CHARTER: "Per %s.\n" % ID},
        untracked=[CHARTER]))
    assert result["problems"] == []
    assert states(result) == {(ID, CHARTER): "untracked"}


@pytest.mark.parametrize("text", [
    "Per %s-b.\n" % ID,            # a longer identifier
    "Per x%s.\n" % ID,             # the identifier inside a word
    "Per %s_v2.\n" % ID,
    "Per 2026-11-10-placemen.\n",  # a shorter one
])
def test_only_the_exact_identifier_carries_it(tool, tmp_path, text):
    """Decision 38, safeguard 3: no false matches."""
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]), CHARTER: text}))
    assert states(result) == {(ID, CHARTER): "uncited"}


@pytest.mark.parametrize("text", [
    "Per %s.\n" % ID, "(%s)\n" % ID, "`%s`\n" % ID, "%s.md\n" % ID,
    "decisions/%s.md\n" % ID])
def test_the_identifier_at_a_boundary_carries_it(tool, tmp_path, text):
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]), CHARTER: text}))
    assert result["owed"] == []


def test_a_record_is_never_its_own_target(tool, tmp_path):
    """Decision 38, safeguard 3: no self-satisfaction. The record holds
    its own identifier, so listing itself would always be carried."""
    result = check(tool, project(tmp_path, {RECORD: block([RECORD])}))
    assert said(result, "%s: lists itself" % RECORD)
    assert result["owed"] == []


def test_another_record_may_be_a_target(tool, tmp_path):
    later = block([RECORD]).replace("# %s" % ID, "# later")
    result = check(tool, project(tmp_path, {
        RECORD: block([], nothing="Records only."),
        LATER: later}))
    assert result["problems"] == []
    assert states(result) == {("2026-11-12-scope", RECORD): "uncited"}


def test_owed_targets_are_listed_oldest_decision_first(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        LATER: block([MODULE]), RECORD: block([CHARTER]),
        CHARTER: "x\n"}))
    assert [r["decision"] for r in result["owed"]] == [
        ID, "2026-11-12-scope"]


# ------------------------------------------------------------- refusals


def test_a_record_without_the_block_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, {RECORD: "# %s\n" % ID}))
    assert said(result, "%s: declares neither carries_into nor "
                        "carries_nothing" % RECORD)


def test_a_record_before_required_from_is_listed_not_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, {RECORD: "# %s\n" % ID},
                                 {"required_from": "2026-11-11"}))
    assert result["problems"] == [] and result["predating"] == [RECORD]


def test_a_record_on_or_after_required_from_must_declare(tool, tmp_path):
    result = check(tool, project(tmp_path, {RECORD: "# %s\n" % ID},
                                 {"required_from": "2026-11-10"}))
    assert said(result, "declares neither") and result["predating"] == []


def test_a_record_before_required_from_with_a_block_is_still_checked(
        tool, tmp_path):
    result = check(tool, project(tmp_path, {RECORD: block([CHARTER])},
                                 {"required_from": "2026-12-01"}))
    assert states(result) == {(ID, CHARTER): "missing"}


def test_required_from_that_is_not_a_date_is_refused(tool, tmp_path):
    with pytest.raises(tool.Unreadable, match="not a date"):
        check(tool, project(tmp_path, {}, {"required_from": "soon"}))


def test_an_unknown_setting_is_refused(tool, tmp_path):
    with pytest.raises(tool.Unreadable, match="unknown field"):
        check(tool, project(tmp_path, {}, {"record": ["x"]}))


def test_a_record_not_named_by_date_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        "docs/decisions/placement.md": block([], nothing="x")}))
    assert said(result, "docs/decisions/placement.md: is not named "
                        "YYYY-MM-DD-<slug>.md")


def test_the_readme_is_not_a_record(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        "docs/decisions/README.md": "# Decisions\n"}))
    assert result["problems"] == [] and result["records"] == []


@pytest.mark.parametrize("text, message", [
    ("---\ncarries_into: []\n# no end\n", "no closing ---"),
    ("---\ncarries_into: [\n---\n", "cannot be read"),
    ("---\n- a list\n---\n", "is not a mapping"),
    ("---\ncarries_into: []\ncarries_nothing: x\nnote: y\n---\n",
     "unknown field(s): note"),
    ("---\ncarries_into: docs/charter.md\n---\n",
     "carries_into is not a list"),
    ("---\ncarries_nothing: x\n---\n", "carries_into is not a list"),
    ("---\ncarries_into: []\n---\n", "carries_nothing gives no reason"),
    ("---\ncarries_into: []\ncarries_nothing: '  '\n---\n",
     "carries_nothing gives no reason"),
    ("---\ncarries_into: [docs/charter.md]\ncarries_nothing: x\n---\n",
     "lists targets and says it carries nothing"),
    ("---\ncarries_into: [docs/charter.md, docs/charter.md]\n---\n",
     "lists docs/charter.md twice"),
])
def test_a_malformed_block_is_refused(tool, tmp_path, text, message):
    result = check(tool, project(tmp_path, {RECORD: text}))
    assert said(result, RECORD + ": ") and said(result, message), result


def test_carries_nothing_with_a_reason_passes(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([], nothing="Records that the pin stays.")}))
    assert result["problems"] == [] and result["owed"] == []


@pytest.mark.parametrize("target", [
    "/docs/charter.md", "./docs/charter.md", "docs/../docs/charter.md",
    "docs\\charter.md", "docs/*.md", "docs/charter?.md", "C:/x.md", "",
    7])
def test_a_target_that_is_not_a_repository_file_path_is_refused(
        tool, tmp_path, target):
    result = check(tool, project(tmp_path, {RECORD: block([target])}))
    assert said(result, RECORD + ": lists"), result
    assert result["owed"] == []


def test_a_directory_target_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block(["docs"]), CHARTER: "x\n"}))
    assert said(result, "lists docs, a directory")


def test_a_citation_of_a_record_that_does_not_exist_is_refused(tool,
                                                               tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([], nothing="x"),
        CHARTER: "See docs/decisions/2026-11-10-placment.md.\n"}))
    assert said(result, "%s: cites decisions/2026-11-10-placment.md, which "
                        "names no decision record" % CHARTER)


def test_a_citation_of_a_record_that_exists_passes(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([], nothing="x"),
        CHARTER: "See ../decisions/%s.md and decisions/%s.\n" % (ID, ID)}))
    assert result["problems"] == []


def test_a_bare_dated_name_is_not_read_as_a_citation(tool, tmp_path):
    """A dated file name is as often an evaluation's or a message's: only
    a path to a record is checked to resolve."""
    result = check(tool, project(tmp_path, {
        CHARTER: "See evaluations/2026-11-06-p7-design.md and "
                 "2026-11-06-t9-policy-adopted.\n"}))
    assert result["problems"] == []


def test_citations_in_excluded_or_unread_files_are_not_checked(tool,
                                                               tmp_path):
    missing = "docs/decisions/2026-01-01-gone.md"
    result = check(tool, project(tmp_path, {
        "docs/template/DECISIONS.md": missing + "\n",
        "communications/bco/incoming/m.md": missing + "\n",
        "tests/test_x.py": "# %s\n" % missing,
        CHARTER: "x\n"}))
    assert result["problems"] == []


def test_an_untracked_file_is_not_scanned_for_citations(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        CHARTER: "docs/decisions/2026-01-01-gone.md\n"},
        untracked=[CHARTER]))
    assert result["problems"] == []


# ------------------------------------------------------- the stage gate


def test_a_done_stage_is_held_by_a_target_owed_in_its_scope(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]), CHARTER: "x\n"}))
    assert tool.stage_problems(stages(charter="done"), result["owed"]) == [
        "charter: is done, but %s owes %s (does not cite it)"
        % (ID, CHARTER)]


def test_a_stage_in_progress_is_not_held(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([CHARTER]), CHARTER: "x\n"}))
    assert tool.stage_problems(stages(), result["owed"]) == []


def test_a_done_stage_is_not_held_by_a_target_outside_its_scope(tool,
                                                                tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block([MODULE]), MODULE: "x\n"}))
    assert tool.stage_problems(stages(charter="done"), result["owed"]) == []


def test_a_missing_target_holds_its_stage_until_created_tracked_and_cited(
        tool, tmp_path):
    """Decision 38, safeguard 1, through every state of the target."""
    plan = stages(formalization="done")
    root = project(tmp_path, {RECORD: block([MODULE])})
    held = tool.stage_problems(plan, check(tool, root, plan)["owed"])
    assert held == ["formalization: is done, but %s owes %s (not yet "
                    "created)" % (ID, MODULE)]
    (root / "ontology").mkdir()
    (root / MODULE).write_text("# decision %s\n" % ID, encoding="utf-8")
    held = tool.stage_problems(plan, check(tool, root, plan)["owed"])
    assert held == ["formalization: is done, but %s owes %s (not tracked)"
                    % (ID, MODULE)]
    (root / MODULE).write_text("# nothing\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    held = tool.stage_problems(plan, check(tool, root, plan)["owed"])
    assert held == ["formalization: is done, but %s owes %s (does not "
                    "cite it)" % (ID, MODULE)]
    (root / MODULE).write_text("# decision %s\n" % ID, encoding="utf-8")
    assert tool.stage_problems(plan, check(tool, root, plan)["owed"]) == []


def test_a_target_assigned_to_a_stage_holds_it(tool, tmp_path):
    result = check(tool, project(tmp_path, {RECORD: block(["notes/loose.md"])},
                                 {"unscoped": [{"decision": ID,
                                                "target": "notes/loose.md",
                                                "stage": "charter"}]}),
                   stages(charter="done"))
    assert result["problems"] == []
    assert tool.stage_problems(stages(charter="done"), result["owed"]) == [
        "charter: is done, but %s owes notes/loose.md (not yet created); "
        "assigned to it in config/decisions.yaml" % ID]


def test_stages_check_reaches_the_propagation_gate_for_a_done_stage(
        monkeypatch, tmp_path):
    """The wiring in tools/stages.py: any stage marked done reaches the
    gate; with none done, decision records are not read."""
    stages_tool = load_tool("t_stages_p7", "tools/stages.py")
    called = []
    monkeypatch.setattr(stages_tool, "propagation",
                        lambda r, s: called.append(r) or ["HELD"])
    monkeypatch.setattr(stages_tool, "withholding", lambda r, s: [])
    monkeypatch.setattr(stages_tool, "problems_of", lambda *a: [])
    path = tmp_path / "stages.yaml"
    monkeypatch.setattr(stages_tool.layout, "path",
                        lambda cid: path if cid == "config.stages"
                        else tmp_path / "docs/standards")
    monkeypatch.setattr(stages_tool.layout, "components", lambda: [])
    path.write_text(yaml.safe_dump({"version": 1, "path": stages(
        charter="done")}), encoding="utf-8")
    assert stages_tool.check(tmp_path)[1] == ["HELD"]
    path.write_text(yaml.safe_dump({"version": 1, "path": stages()}),
                    encoding="utf-8")
    called.clear()
    assert stages_tool.check(tmp_path)[1] == [] and called == []


# ------------------------------------------------------ the release gate


def test_an_owed_target_no_stage_holds_stops_a_release(tool, tmp_path):
    """Decision 38, safeguard 2: visible, and held at release."""
    result = check(tool, project(tmp_path, {
        RECORD: block(["notes/loose.md"])}))
    assert result["problems"] == []
    assert result["owed"][0]["held"] == "nowhere"
    assert tool.release_problems(result["owed"]) == [
        "%s owes notes/loose.md (not yet created), which is in no stage's "
        "scope; assign it to a stage or account for it in "
        "config/decisions.yaml" % ID]


def test_an_owed_target_in_a_stage_not_run_is_in_no_stage(tool, tmp_path):
    plan = stages(formalization_runs=False, formalization="not-started")
    result = check(tool, project(tmp_path, {RECORD: block([MODULE])}), plan)
    assert result["owed"][0]["held"] == "nowhere"
    assert len(tool.release_problems(result["owed"])) == 1


@pytest.mark.parametrize("entry", [
    {"stage": "charter"},
    {"reason": "outstanding until the next specification; released "
               "with it owed"}])
def test_an_assigned_or_accounted_target_does_not_stop_a_release(
        tool, tmp_path, entry):
    result = check(tool, project(tmp_path, {
        RECORD: block(["notes/loose.md"])}, {"unscoped": [dict(
            {"decision": ID, "target": "notes/loose.md"}, **entry)]}))
    assert result["problems"] == []
    assert tool.release_problems(result["owed"]) == []


def test_an_owed_target_in_a_stage_scope_does_not_stop_a_release(tool,
                                                                 tmp_path):
    result = check(tool, project(tmp_path, {RECORD: block([CHARTER])}))
    assert result["owed"][0]["held"] == "scope"
    assert tool.release_problems(result["owed"]) == []


def test_release_build_refuses_before_writing(monkeypatch, tmp_path):
    release = load_tool("t_release_p7", "tools/release.py")
    row = {"decision": ID, "target": "notes/loose.md", "state": "missing",
           "held": "nowhere", "stages": []}
    monkeypatch.setattr(release.decisions, "check",
                        lambda root=None: {"owed": [row]})
    with pytest.raises(release.Refused, match="notes/loose.md"):
        release.build("1.2.3", tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("entry, message", [
    ("x", "is not a mapping"),
    ({"decision": ID}, "needs a decision and a target"),
    ({"decision": ID, "target": "notes/loose.md"}, "exactly one of stage"),
    ({"decision": ID, "target": "notes/loose.md", "stage": "charter",
      "reason": "r"}, "exactly one of stage"),
    ({"decision": ID, "target": "notes/loose.md", "stage": "nope"},
     "not a stage the project runs"),
    ({"decision": ID, "target": "notes/other.md", "reason": "r"},
     "does not list notes/other.md"),
    ({"decision": ID, "target": "notes/loose.md", "reason": "r",
      "by": "me"}, "unknown field(s): by"),
])
def test_a_malformed_unscoped_entry_is_refused(tool, tmp_path, entry,
                                               message):
    result = check(tool, project(tmp_path, {
        RECORD: block(["notes/loose.md"])}, {"unscoped": [entry]}))
    assert said(result, "unscoped entry 1") and said(result, message), result


def test_a_repeated_unscoped_entry_is_refused(tool, tmp_path):
    entry = {"decision": ID, "target": "notes/loose.md", "reason": "r"}
    result = check(tool, project(tmp_path, {
        RECORD: block(["notes/loose.md"])}, {"unscoped": [entry, entry]}))
    assert said(result, "unscoped entry 2 repeats")


def test_an_unscoped_entry_for_a_carried_target_is_stale(tool, tmp_path):
    result = check(tool, project(tmp_path, {
        RECORD: block(["notes/loose.md"]),
        "notes/loose.md": "Per %s.\n" % ID},
        {"unscoped": [{"decision": ID, "target": "notes/loose.md",
                       "reason": "r"}]}))
    assert said(result, "is stale: notes/loose.md now carries %s" % ID)


def test_an_unscoped_entry_for_a_target_now_in_scope_is_stale(tool,
                                                              tmp_path):
    result = check(tool, project(tmp_path, {RECORD: block([CHARTER])},
                                 {"unscoped": [{"decision": ID,
                                                "target": CHARTER,
                                                "reason": "r"}]}))
    assert said(result, "is stale: %s is now in the scope of charter"
                % CHARTER)


# ------------------------------------------------------- what is shipped


def test_the_shipped_settings_are_the_defaults(tool, repo):
    settings = tool.configuration(repo)
    assert settings == tool.DEFAULTS


def test_the_shipped_project_passes(tool, repo):
    result = tool.check(repo)
    assert result["problems"] == []


def test_the_report_says_carried_is_not_faithful(tool, repo, capsys):
    assert tool.main([]) == 0
    assert "not that it says what the decision decided" in (
        capsys.readouterr().out)


@pytest.mark.parametrize("text, title", [
    (block([CHARTER]), ID),
    ("# Placement\n\nThe act.\n", "Placement"),
    ("---\ncarries_into: []\ncarries_nothing: x\n---\n\n# Kept\n", "Kept"),
])
def test_the_site_titles_a_record_after_its_front_matter(tmp_path, text,
                                                         title):
    site = load_tool("t_site_p7", "tools/site/build_site.py")
    path = tmp_path / (ID + ".md")
    path.write_text(text, encoding="utf-8")
    assert site.decision_title(path) == title
