# SPDX-License-Identifier: MIT
"""Upgrading a project to a new template release (P-A2, template
decision 45).

One world per module: a copy of the template recorded as release v9.8.0,
a project made from it by init, and a release v9.9.0 with a planted case
for every class of the plan -- a file the project never changed, one both
changed, one only the project changed, one both changed the same way, a
seeded shape through init's rewrite, the upstream pins, a new file, one
in the project's way, one removed -- with a layout entry added and one
removed, a skeleton changed, and its release notes. Each test works on
its own copy of the project.

Decision 45's safeguards are among them: the planner runs from the
release's checkout on a project that has never heard of it; a pin moves
only with --accept-pins; --adopt keeps the original init's block, records
the exact release and commit, and lists what is retained, unresolved and
for review; nothing writes over a project's change, a file in the way or
a symbolic link, and removals and layout changes are reported only.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from conftest import ROOT, load_tool

EXAMPLE = "https://fandaws.com/ontology/example#"
WIDGET = "https://fandaws.com/ontology/widget#"
ENV = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@invalid",
           GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@invalid")

TAKE = "tools/pins.py"
MERGE = "docs/DEVELOPMENT.md"
KEPT = "docs/process/METHOD.md"
SAME = "docs/process/PROCESS.md"
SHAPE = "shapes/realist_shapes.ttl"
PINS = "config/upstream-sources.yaml"
ADDED = "tools/newtool.py"
COLLIDE = "tools/collide.py"
REMOVED = "tools/ontology/normalize.py"
SKELETON = "docs/template/skeletons/CLAUDE.md"


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_upgrade", "tools/upgrade.py")


def run(cwd, *args, check=True):
    return subprocess.run(list(args), cwd=str(cwd), env=ENV, check=check,
                          capture_output=True, text=True)


def commit(root, message):
    run(root, "git", "add", "-A")
    run(root, "git", "commit", "-q", "--no-verify", "-m", message)
    return run(root, "git", "rev-parse", "HEAD").stdout.strip()


def append(path: Path, text: str):
    path.write_bytes(path.read_bytes() + text.encode("utf-8"))


def record(root, label):
    run(root, sys.executable, "tools/template_status.py", "--record",
        "--label", label)


def entry(ident, path, template="owned"):
    return ("  - id: %s\n    path: %s\n    role: tool\n    template: %s\n"
            "    description: >-\n      Planted for the upgrade tests.\n\n"
            % (ident, path, template))


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    """(template checkout at v9.9.0, project made at v9.8.0, the commit of
    v9.8.0, the commit of v9.9.0)."""
    base = tmp_path_factory.mktemp("upgrade")
    template = base / "template"
    listed = run(ROOT, "git", "ls-files", "--cached", "--others",
                 "--exclude-standard").stdout.splitlines()
    for name in listed:
        source = ROOT / name
        if source.is_file():
            target = template / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    run(template, "git", "init", "-q")
    run(template, "git", "config", "core.autocrlf", "false")
    commit(template, "the template")
    record(template, "v9.8.0")
    old = commit(template, "Template v9.8.0")

    project = base / "project"
    run(base, "git", "clone", "-q", str(template), str(project))
    run(project, "git", "config", "core.autocrlf", "false")
    run(project, sys.executable, "tools/init_project.py", "--id", "widget",
        "--title", "Widget Ontology", "--description", "What widgets are.",
        "--repository", "owner/Widget-Ontology", "--no-regenerate")
    commit(project, "Initialize")
    append(project / MERGE, "\nA line the project wrote.\n")
    append(project / KEPT, "\nThe project's own note.\n")
    append(project / SAME, "\nThe same line on both sides.\n")
    (project / COLLIDE).write_bytes(b"# the project's own collide.py\n")
    commit(project, "The project's changes")

    append(template / TAKE, "\n# changed in v9.9.0\n")
    append(template / MERGE, "\nA line the release wrote.\n")
    append(template / SAME, "\nThe same line on both sides.\n")
    append(template / SHAPE, "\n# v9.9.0: %sAnything\n" % EXAMPLE)
    append(template / PINS, "\n# v9.9.0 note\n")
    pins = template / PINS
    pins.write_bytes(pins.read_bytes().replace(
        b"release: v2.0-2024-11-06", b"release: v2.2-planted"))
    (template / ADDED).write_bytes(b"# new in v9.9.0\n")
    (template / COLLIDE).write_bytes(b"# the release's collide.py\n")
    (template / REMOVED).unlink()
    contract = template / "config/repository-layout.yaml"
    text = contract.read_bytes().decode("utf-8")
    start = text.index("  - id: tool.normalize\n")
    end = text.index("\n  - id: ", start + 1) + 1
    text = text[:start] + text[end:]
    text = text.replace("  - id: tool.pins\n", entry("tool.newtool", ADDED)
                        + entry("tool.collide", COLLIDE) + "  - id: tool.pins\n")
    contract.write_bytes(text.encode("utf-8"))
    append(template / SKELETON, "\nA line added to the skeleton.\n")
    roadmap = template / "docs/template/ROADMAP.md"
    text = roadmap.read_bytes().decode("utf-8")
    text = text.replace(
        "### After WP6: the prioritized backlog (decision 29)",
        "### Release v9.9.0 (2099-01-01)\n\nThe planted release.\n\n"
        "**What changes for a project made from v9.8.0.**\n\n"
        "- A planted change.\n\n| What | Why | Tests |\n|---|---|---|\n\n"
        "### After WP6: the prioritized backlog (decision 29)")
    roadmap.write_bytes(text.encode("utf-8"))
    commit(template, "v9.9.0 changes")
    record(template, "v9.9.0")
    new = commit(template, "Template v9.9.0")
    return template, project, old, new


@pytest.fixture
def mine(world, tmp_path):
    """A copy of the project, with its history, for one test."""
    copy = tmp_path / "project"
    shutil.copytree(world[1], copy)
    return copy


def upgrade_cmd(world, project, *args):
    """The release's own tool, run from its checkout against the project:
    safeguard 1, a project that has never had tools/upgrade.py."""
    return run(world[0], sys.executable, "tools/upgrade.py", "--project",
               str(project), *args, check=False)


def plan_of(world, project):
    result = upgrade_cmd(world, project, "--json")
    assert result.returncode in (0, 2), result.stderr
    return json.loads(result.stdout)


def classes(plan):
    return {r["path"]: r["class"] for r in plan["files"]}


# ----------------------------------------------------------- the plan


def test_the_planner_runs_on_a_project_that_does_not_have_it(world, mine):
    (mine / "tools/upgrade.py").unlink()
    commit(mine, "a project made before P-A2")
    plan = plan_of(world, mine)
    assert plan["from"]["label"] == "v9.8.0"
    assert plan["to"]["label"] == "v9.9.0" and plan["to"]["commit"] == world[3]
    # The base is the first commit carrying the project's record (the
    # rule template_status.base_commit has always had): its manifest's
    # digest is the project's.
    shown = run(world[0], "git", "show",
                "%s:config/template-manifest.json" % plan["from"]["base"])
    recorded = json.loads((mine / "config/template-manifest.json").read_text(
        encoding="utf-8"))
    assert json.loads(shown.stdout)["digest"] == recorded["digest"]


def test_every_class_is_found(world, mine):
    found = classes(plan_of(world, mine))
    assert found[TAKE] == "take"
    assert found[MERGE] == "merge"
    assert found[KEPT] == "kept"
    assert found[SAME] == "already taken"
    assert found[SHAPE] == "take"
    assert found[PINS] == "pins"
    assert found[ADDED] == "added"
    assert found[COLLIDE] == "collision"
    assert found[REMOVED] == "removed"
    assert "tools/fidelity.py" not in found          # unchanged: no row


def test_the_layout_changes_are_listed(world, mine):
    changes = plan_of(world, mine)["layout"]
    assert {a["id"] for a in changes["added"]} == {"tool.newtool",
                                                    "tool.collide"}
    assert [r["id"] for r in changes["removed"]] == ["tool.normalize"]
    assert changes["changed"] == []                  # ontology.main matched


def test_the_skeleton_change_is_a_diff(world, mine):
    [change] = plan_of(world, mine)["skeletons"]
    assert change["rendered"] == "CLAUDE.md"
    assert "+A line added to the skeleton." in change["diff"]


def test_the_release_notes_are_those_since_the_project(world, mine):
    notes = plan_of(world, mine)["notes"]
    assert [n["release"] for n in notes] == ["v9.9.0"]
    assert "A planted change." in notes[0]["notes"]
    assert "| What |" not in notes[0]["notes"]


def test_the_pin_change_names_both_releases(world, mine):
    [row] = [r for r in plan_of(world, mine)["files"] if r["path"] == PINS]
    assert {"source": "cco", "here": "v2.0-2024-11-06",
            "template": "v2.2-planted"} in row["pins"]


def test_the_plan_writes_nothing(world, mine):
    before = run(mine, "git", "status", "--porcelain").stdout
    assert upgrade_cmd(world, mine).returncode == 0
    assert run(mine, "git", "status", "--porcelain").stdout == before


def test_merge_bases_are_written_for_git_merge_file(world, mine, tmp_path):
    out = tmp_path / "bases"
    result = upgrade_cmd(world, mine, "--out", str(out))
    assert result.returncode == 0, result.stderr
    base = (out / (MERGE + ".base")).read_text(encoding="utf-8")
    theirs = (out / (MERGE + ".release")).read_text(encoding="utf-8")
    assert "A line the release wrote." in theirs
    assert "A line the release wrote." not in base
    assert "A line the project wrote." not in base
    merged = subprocess.run(["git", "merge-file", "-p", str(mine / MERGE),
                             str(out / (MERGE + ".base")),
                             str(out / (MERGE + ".release"))],
                            capture_output=True, text=True)
    assert "A line the project wrote." in merged.stdout
    assert "A line the release wrote." in merged.stdout


def test_merge_bases_refuse_a_directory_in_use(world, mine, tmp_path):
    out = tmp_path / "bases"
    out.mkdir()
    (out / "x").write_text("x")
    assert upgrade_cmd(world, mine, "--out", str(out)).returncode == 1


def test_a_project_whose_base_is_not_in_the_history_is_not_compared(
        world, mine):
    manifest = mine / "config/template-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["template_commit"] = "e" * 40
    manifest.write_bytes(json.dumps(data, indent=2).encode() + b"\n")
    commit(mine, "a record from elsewhere")
    result = upgrade_cmd(world, mine, "--json")
    assert result.returncode == 2
    plan = json.loads(result.stdout)
    [reason] = plan["not_compared"]
    assert "the skeletons, the layout entries the release removed and the " \
           "merge bases need the base commit, and are not compared" in reason
    assert plan["skeletons"] == [] and plan["layout"]["removed"] == []
    before = (mine / TAKE).read_bytes()
    taken = upgrade_cmd(world, mine, "--take")
    assert taken.returncode == 1 and "cannot compare" in taken.stderr
    assert (mine / TAKE).read_bytes() == before


def test_a_record_from_before_v030_is_compared_from_history(world, mine):
    """No `initialized` block: the seeded base comes from the release's
    history, through init's rewrite, and the classes are the same."""
    manifest = mine / "config/template-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data.pop("initialized")
    manifest.write_bytes(json.dumps(data, indent=2).encode() + b"\n")
    commit(mine, "an older record")
    found = classes(plan_of(world, mine))
    assert found[SHAPE] == "take" and found[TAKE] == "take"


# ----------------------------------------------------------------- take


def test_take_copies_only_what_the_project_never_changed(world, mine):
    merge_before = (mine / MERGE).read_bytes()
    collide_before = (mine / COLLIDE).read_bytes()
    pins_before = (mine / PINS).read_bytes()
    result = upgrade_cmd(world, mine, "--take")
    assert result.returncode == 0, result.stderr
    assert (mine / TAKE).read_bytes() == (world[0] / TAKE).read_bytes()
    assert (mine / ADDED).read_bytes() == (world[0] / ADDED).read_bytes()
    assert (mine / MERGE).read_bytes() == merge_before
    assert (mine / COLLIDE).read_bytes() == collide_before
    assert (mine / PINS).read_bytes() == pins_before   # safeguard 2
    assert (mine / REMOVED).is_file()                  # reported, not removed


def test_a_seeded_shape_is_taken_through_inits_rewrite(world, mine):
    upgrade_cmd(world, mine, "--take")
    text = (mine / SHAPE).read_text(encoding="utf-8")
    assert "# v9.9.0: %sAnything" % WIDGET in text
    assert EXAMPLE not in text


def test_pins_move_only_with_accept_pins(world, mine):
    upgrade_cmd(world, mine, "--take", "--accept-pins")
    assert (mine / PINS).read_bytes() == (world[0] / PINS).read_bytes()


def test_pins_changed_here_are_never_taken(world, mine):
    append(mine / PINS, "\n# the project's own note\n")
    commit(mine, "the project's pins")
    before = (mine / PINS).read_bytes()
    result = upgrade_cmd(world, mine, "--take", "--accept-pins")
    assert (mine / PINS).read_bytes() == before
    assert "merge them by hand" in result.stdout


def test_take_twice_takes_nothing_the_second_time(world, mine):
    upgrade_cmd(world, mine, "--take")
    commit(mine, "taken")
    result = upgrade_cmd(world, mine, "--take")
    assert result.returncode == 0
    assert "0 file(s) taken" in result.stdout


def test_take_refuses_a_project_with_uncommitted_changes(world, mine):
    (mine / "stray.txt").write_text("x")
    result = upgrade_cmd(world, mine, "--take")
    assert result.returncode == 1 and "uncommitted" in result.stderr
    assert (mine / TAKE).read_bytes() != (world[0] / TAKE).read_bytes()


def test_take_refuses_a_dirty_checkout(world, mine):
    stray = world[0] / "stray.txt"
    stray.write_text("x")
    try:
        result = upgrade_cmd(world, mine, "--take")
    finally:
        stray.unlink()
    assert result.returncode == 1 and "uncommitted" in result.stderr


def test_take_refuses_a_checkout_its_manifest_does_not_describe(world,
                                                                mine):
    template = world[0]
    append(template / TAKE, "# unrecorded\n")
    commit(template, "an unrecorded change")
    try:
        result = upgrade_cmd(world, mine, "--take")
    finally:
        run(template, "git", "reset", "-q", "--hard", world[3])
    assert result.returncode == 1
    assert "not the release its manifest records" in result.stderr


def test_take_writes_nothing_over_a_file_that_moved(tool, world, mine,
                                                    monkeypatch):
    """Between the plan and the write, the file changed: skipped."""
    upgrade = tool.Upgrade(mine, world[0])
    monkeypatch.setattr(upgrade, "ready", lambda allow: None)
    append(mine / TAKE, "# moved after the plan\n")
    moved = (mine / TAKE).read_bytes()
    commit(mine, "moved")
    written = upgrade.take()
    assert TAKE not in written and (mine / TAKE).read_bytes() == moved
    [row] = [r for r in upgrade.rows if r["path"] == TAKE]
    assert row["skipped"] == "it changed since the plan was made"


def test_take_writes_nothing_where_a_file_appeared(tool, world, mine,
                                                   monkeypatch):
    upgrade = tool.Upgrade(mine, world[0])
    monkeypatch.setattr(upgrade, "ready", lambda allow: None)
    (mine / ADDED).write_bytes(b"# appeared\n")
    commit(mine, "appeared")
    upgrade.take()
    assert (mine / ADDED).read_bytes() == b"# appeared\n"
    [row] = [r for r in upgrade.rows if r["path"] == ADDED]
    assert row["skipped"] == "a file appeared at its path"


def test_take_never_writes_through_a_symbolic_link(tool, world, mine,
                                                   monkeypatch):
    upgrade = tool.Upgrade(mine, world[0])
    monkeypatch.setattr(upgrade, "ready", lambda allow: None)
    linked = (mine / "tools").resolve()
    real = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: (
        self.resolve() == linked or real(self)))
    before = (mine / TAKE).read_bytes()
    upgrade.take()
    assert (mine / TAKE).read_bytes() == before
    [row] = [r for r in upgrade.rows if r["path"] == TAKE]
    assert row["skipped"] == "goes through the symbolic link tools"


@pytest.mark.parametrize("relative, why", [
    ("../outside.txt", "is not a path inside the project"),
    ("/etc/passwd", "is not a path inside the project"),
])
def test_a_path_outside_the_project_is_unsafe(tool, tmp_path, relative, why):
    assert tool.unsafe(tmp_path, relative) == why


def test_take_refuses_an_unreleased_checkout_unless_allowed(tool, world,
                                                            mine):
    upgrade = tool.Upgrade(mine, world[0])
    upgrade.release = dict(upgrade.release, label="unreleased")
    with pytest.raises(tool.Refused, match="not a release"):
        upgrade.ready(False)


# ---------------------------------------------------------------- adopt


def declared(world, project):
    """The person's step 4: the two entries the plan lists, copied in."""
    contract = project / "config/repository-layout.yaml"
    append(contract, "\n" + entry("tool.newtool", ADDED)
           + entry("tool.collide", COLLIDE))
    commit(project, "declared")


def adopted(world, project, *extra):
    upgrade_cmd(world, project, "--take")
    commit(project, "taken")
    declared(world, project)
    result = upgrade_cmd(world, project, "--adopt", *extra)
    assert result.returncode == 0, result.stderr
    data = json.loads((project / "config/template-manifest.json").read_text(
        encoding="utf-8"))
    return data, result


def test_adopt_refuses_files_the_contract_does_not_declare(world, mine):
    upgrade_cmd(world, mine, "--take")
    commit(mine, "taken")
    result = upgrade_cmd(world, mine, "--adopt")
    assert result.returncode == 1
    assert "belong to no component" in result.stderr
    assert ADDED in result.stderr


def test_adopt_keeps_the_original_init_and_records_the_release(world, mine):
    original = json.loads((mine / "config/template-manifest.json").read_text(
        encoding="utf-8"))
    data, _ = adopted(world, mine)
    assert data["initialized"] == original["initialized"]
    assert data["made_from"] == {"label": "v9.8.0",
                                 "template_commit": original[
                                     "template_commit"],
                                 "digest": original["digest"]}
    assert data["label"] == "v9.9.0"
    assert data["adopted"]["commit"] == world[3]
    assert data["adopted"]["label"] == "v9.9.0"
    [move] = data["upgrades"]
    assert move["from"]["label"] == "v9.8.0"
    assert move["to"] == {"label": "v9.9.0",
                          "template_commit": data["template_commit"],
                          "commit": world[3], "digest": data["digest"]}


def test_adopt_shows_what_is_retained_unresolved_and_for_review(world, mine):
    data, result = adopted(world, mine)
    move = data["upgrades"][-1]
    unresolved = {(u["path"], u["why"]) for u in move["unresolved"]}
    assert (MERGE, "differs from the release, and --retain does not name "
                   "it") in unresolved
    assert (COLLIDE, "differs from the release, and --retain does not name "
                     "it") in unresolved
    assert (REMOVED, "removed in the release, still here") in unresolved
    retained = {(r["path"], r["why"]) for r in move["retained"]}
    assert (PINS, "upstream pins not accepted: BFO and CCO stay as the "
                  "project pins them") in retained
    assert [r["path"] for r in move["review"]] == ["CLAUDE.md"]
    assert "unresolved docs/DEVELOPMENT.md" in " ".join(result.stdout.split())


def test_a_retained_file_is_named_as_kept_on_purpose(world, mine):
    data, _ = adopted(world, mine, "--retain", MERGE)
    move = data["upgrades"][-1]
    assert {"path": MERGE, "why": "kept on purpose (--retain)"} in \
        move["retained"]
    assert MERGE not in {u["path"] for u in move["unresolved"]}


def test_retaining_a_file_the_plan_does_not_list_is_refused(world, mine):
    upgrade_cmd(world, mine, "--take")
    commit(mine, "taken")
    declared(world, mine)
    result = upgrade_cmd(world, mine, "--adopt", "--retain", "README.md")
    assert result.returncode == 1 and "does not list" in result.stderr


def test_adopting_the_same_release_twice_is_refused(world, mine):
    adopted(world, mine)
    commit(mine, "adopted")
    result = upgrade_cmd(world, mine, "--adopt")
    assert result.returncode == 1 and "not newer" in result.stderr


def test_after_adopting_the_reports_start_from_the_release(world, mine):
    adopted(world, mine)
    commit(mine, "adopted")
    found = classes(plan_of(world, mine))
    assert "take" not in found.values() and "added" not in found.values()
    report = run(mine, sys.executable, "tools/template_status.py",
                 "--against", str(world[0]), check=False).stdout
    assert "changed 0, removed 0, added 0 seeded" in report


def test_after_adopting_a_change_here_is_kept_not_merged(world, mine):
    """The next plan's base is the release adopted: a shape changed after
    adopting is the project's own change (kept), not a conflict with the
    release, as it would be against the original init's base."""
    adopted(world, mine)
    commit(mine, "adopted")
    append(mine / SHAPE, "\n# the project's own shape note\n")
    commit(mine, "a shape changed after adopting")
    assert classes(plan_of(world, mine))[SHAPE] == "kept"


def test_after_adopting_the_plain_report_counts_from_the_release(world,
                                                                 mine):
    """template_status.py reads the adopted block: the shape taken is as
    the release left it, and only the pins kept are configured here."""
    adopted(world, mine)
    commit(mine, "adopted")
    report = run(mine, sys.executable, "tools/template_status.py",
                 check=False).stdout
    [line] = [l for l in report.splitlines() if "configured here" in l]
    assert PINS in line and SHAPE not in line


def test_a_second_adoption_keeps_the_first_record(world, mine):
    """made_from is the record the project was first made from, kept
    across every adoption after it."""
    first, _ = adopted(world, mine)
    commit(mine, "adopted")
    manifest = mine / "config/template-manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["label"] = "v9.8.5"
    manifest.write_bytes(json.dumps(data, indent=2).encode() + b"\n")
    commit(mine, "an intermediate release, as if adopted")
    result = upgrade_cmd(world, mine, "--adopt")
    assert result.returncode == 0, result.stderr
    second = json.loads(manifest.read_text(encoding="utf-8"))
    assert second["made_from"] == first["made_from"]
    assert second["made_from"]["label"] == "v9.8.0"
    assert [u["from"]["label"] for u in second["upgrades"]] == ["v9.8.0",
                                                               "v9.8.5"]


def test_take_never_touches_a_merge_or_a_collision(world, mine):
    """Neither is written, and neither is even tried: nothing in the
    take's output names them."""
    result = upgrade_cmd(world, mine, "--take")
    assert result.returncode == 0, result.stderr
    assert MERGE not in result.stdout and COLLIDE not in result.stdout


def test_adopt_writes_only_the_manifest(world, mine):
    upgrade_cmd(world, mine, "--take")
    commit(mine, "taken")
    declared(world, mine)
    upgrade_cmd(world, mine, "--adopt")
    changed = run(mine, "git", "status", "--porcelain").stdout.split("\n")
    assert [line[3:] for line in changed if line] == [
        "config/template-manifest.json"]


# ---------------------------------------------------------- classify


@pytest.mark.parametrize("base, theirs, here, in_release, expected", [
    ("a", "b", "a", True, "take"),
    ("a", "b", "c", True, "merge"),
    ("a", "b", "b", True, "already taken"),
    ("a", "b", None, True, "deleted here"),
    ("a", "a", "c", True, "kept"),
    ("a", "a", "a", True, None),
    ("a", "a", None, True, "deleted here"),
    (None, "b", None, True, "added"),
    (None, "b", "b", True, "already taken"),
    (None, "b", "c", True, "collision"),
    ("a", None, "a", False, "removed"),
    ("a", None, "c", False, "removed, changed here"),
    ("a", None, None, False, None),
    (None, None, "c", False, None),
])
def test_each_file_falls_in_one_class(tool, base, theirs, here, in_release,
                                      expected):
    assert tool.classify(base, theirs, here, in_release) == expected


# ------------------------------------------- what an added entry needs


@pytest.mark.parametrize("entry, expected", [
    ({"path": "tools/pins.py"}, "present"),
    ({"path": "tools/not-here.py", "template": "owned"}, "taken by --take"),
    ({"path": "research/out.md", "generator": "tool.pins"},
     "generated: run python tools/pins.py"),
    ({"path": "docs/template/ROADMAP.md"},
     "absent: copy it from the release (docs/template/ROADMAP.md); it is "
     "the project's from then on"),
    ({"path": "docs/nowhere.md"},
     "absent: the release has no file there either"),
])
def test_an_added_entry_says_what_its_file_needs(tool, world, mine, entry,
                                                 expected):
    """Found upgrading a project made at v0.1.0: the release adds entries
    for files neither owned nor seeded -- a stage config, a charter, a
    generated register -- and the plan said nothing of their absence, so
    --adopt refused on the layout check with no step that led there."""
    upgrade = tool.Upgrade(mine, world[0])
    contract = tool.contract_of((world[0] / tool.CONTRACT).read_bytes())
    assert upgrade.state_of(entry, contract) == expected


def test_the_plan_says_each_added_entrys_state(world, mine):
    added = {a["id"]: a["state"] for a in plan_of(world, mine)["layout"][
        "added"]}
    assert added == {"tool.newtool": "taken by --take",
                     "tool.collide": "present"}
