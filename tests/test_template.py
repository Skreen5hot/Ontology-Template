# SPDX-License-Identifier: MIT
"""What the template owns, and the record of it.

Components declared `template: owned` are the template's: every project
made from it gets them unchanged, and tools/template_status.py reports
where a project has diverged. Two things have to hold for that to work.

The owned files must not name a project. init does not rewrite them --
it refuses to -- so a namespace or a repository written into one would
arrive in every project still pointing at whichever project wrote it.
That is exactly how the BCO's tools came to carry its namespace, its
sender code and its extract base as constants.

And the manifest must describe them. In the template a stale manifest
fails; in a project the manifest is the record of what it was made from,
and divergence is reported, not refused.
"""

from __future__ import annotations

import json

import pytest

from conftest import load_tool

#: Project values that must not appear in an owned file, beyond this
#: project's own. Assembled from parts so this file does not contain them.
FOREIGN = (
    "fandaws.com/ontology/" + "bco",
    "example.org/" + "apqc",
    "Business-and-Agent-" + "Capabilities-Ontology",
)


@pytest.fixture(scope="module")
def status():
    return load_tool("t_template_status", "tools/template_status.py")


def named_values(text: str, project) -> list[str]:
    """Which project values a text contains."""
    values = (project.iri_base(), project.namespace()) + FOREIGN
    return [value for value in values if value in text]


def test_the_owned_set_covers_the_tools_and_the_suite(status):
    """Guards the two tests below: an owned set that lost the tools would
    satisfy both by examining nothing."""
    owned = status.owned_files()
    for required in ("tools/project.py", "tools/layout.py",
                     "tools/ontology/validate.py", "tests/conftest.py",
                     ".github/workflows/checks.yml",
                     "docs/process/PROCESS.md"):
        assert required in owned, required


def test_no_owned_file_names_a_project(status, project, repo):
    offenders = {}
    for name in status.owned_files():
        found = named_values((repo / name).read_bytes().decode(
            "utf-8", "replace"), project)
        if found:
            offenders[name] = found
    assert not offenders, (
        "template-owned files name a project, and init will copy them into "
        "every new one unchanged: %s" % offenders)


def test_the_scan_finds_a_project_value(project):
    """Falsifies the test above on a constructed text."""
    planted = "AUTHORED_NAMESPACE = %r" % project.namespace()
    assert named_values(planted, project), planted
    assert named_values("x = 'https://" + FOREIGN[0] + "#'", project)
    assert not named_values("x = 'https://fandaws.com/ontology/%s'", project)


def test_in_the_template_every_tool_is_owned(layout, project, repo):
    """A tool added to the template without `template: owned` would not
    be in the manifest, and a project could never see that it changed.
    A project's own tools are its own, so this binds the template only."""
    tools = sorted(p.relative_to(repo).as_posix()
                   for p in (repo / "tools").rglob("*.py"))
    assert tools, "no tools found"
    unowned = [t for t in tools
               if (layout.owning_component(t) is None
                   or layout.owning_component(t).template != "owned")]
    if project.is_template():
        assert unowned == [], unowned
    else:
        template_tools = set(json.loads(
            (repo / "config/template-manifest.json").read_text(
                encoding="utf-8"))["files"])
        assert not (set(unowned) & template_tools), (
            "a tool the template shipped as owned is no longer declared "
            "owned: %s" % sorted(set(unowned) & template_tools))


def test_the_manifest_describes_the_owned_files(status, project):
    """In the template: current, or the suite fails until --record runs.
    In a project: present and well formed, and whatever has diverged is
    reported by the tool rather than refused here."""
    record = status.recorded()
    now = status.measure()
    assert record["files"], "the manifest records no files"
    assert record["digest"] == status.digest_of(record["files"]), (
        "the manifest's digest is not the digest of the files it lists, so "
        "it has been edited by hand")
    if project.is_template():
        difference = status.compare(record["files"], now["files"])
        assert not status.diverged(difference), (
            "the template's manifest is stale -- run python "
            "tools/template_status.py --record: %s" % difference)


def test_a_changed_owned_file_is_reported(status, monkeypatch):
    """Falsifies the comparison: one owned file with a different digest
    has to come back as changed, and only that one."""
    record = status.recorded()
    name = sorted(record["files"])[0]
    altered = dict(record["files"], **{name: "0" * 64})
    assert altered != record["files"]
    difference = status.compare(record["files"], altered)
    assert difference == {"changed": [name], "removed": [], "added": []}
    assert status.diverged(difference)


def test_a_project_may_not_rewrite_the_record(status, monkeypatch):
    """--record in a project would make every local change look like the
    template's, and the next update would overwrite them silently."""
    monkeypatch.setattr(status.project, "is_template", lambda: False)
    with pytest.raises(SystemExit) as error:
        status.main(["--record"])
    assert "this is a project" in str(error.value)


def test_against_names_what_both_sides_changed(status, monkeypatch,
                                               tmp_path):
    """The update report: a file the template changed and the project
    also changed is the one a person has to merge."""
    record = status.recorded()
    names = sorted(record["files"])
    both, theirs_only = names[0], names[1]

    newer = dict(record, files=dict(record["files"],
                                    **{both: "1" * 64,
                                       theirs_only: "2" * 64}))
    (tmp_path / "config").mkdir()
    (tmp_path / "config/template-manifest.json").write_text(
        json.dumps(newer), encoding="utf-8")

    real_measure = status.measure
    monkeypatch.setattr(status, "measure", lambda root=None: {
        "files": dict(real_measure()["files"], **{both: "3" * 64}),
        "digest": "x"})
    report = status.against(tmp_path)
    assert report["both"] == [both], report
    assert theirs_only in report["template_changed"]["changed"]


def test_the_dependabot_workflow_rerecords_the_manifest_and_nothing_else(repo):
    """The guards that make it safe to give a Dependabot-triggered job
    write permission, read from the workflow itself: it runs only when
    both the author and the actor are Dependabot, only in the template,
    refuses to push anything but the manifest, and re-runs the real
    checks on the new commit rather than declaring it green."""
    import yaml

    workflow = yaml.safe_load((repo / ".github/workflows/"
                               "dependabot-manifest.yml").read_text(
        encoding="utf-8"))
    job = workflow["jobs"]["rerecord"]
    condition = " ".join(job["if"].split())
    assert "github.event.pull_request.user.login == 'dependabot[bot]'" \
        in condition
    assert "github.actor == 'dependabot[bot]'" in condition
    assert workflow["permissions"] == {"contents": "read"}
    assert job["permissions"] == {"contents": "write", "actions": "write"}

    steps = {step["name"]: step for step in job["steps"]}
    record = steps["Re-record, and refuse anything but the manifest"]
    assert "steps.state.outputs.template == 'true'" in record["if"]
    assert '!= "config/template-manifest.json"' in record["run"]
    push = steps["Push the one-file commit"]["run"]
    assert "git add config/template-manifest.json" in push
    assert "git add -A" not in push and "git add ." not in push
    rerun = steps["Run Checks, Reasoning and Pages on the new commit"]["run"]
    for workflow_file in ("checks.yml", "reasoning.yml", "pages.yml"):
        assert workflow_file in rerun, workflow_file
    text = (repo / ".github/workflows/dependabot-manifest.yml").read_text(
        encoding="utf-8")
    for forbidden in ("gh pr merge", "gh pr review", "--admin"):
        assert forbidden not in text, forbidden
