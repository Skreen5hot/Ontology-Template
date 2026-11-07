# SPDX-License-Identifier: MIT
"""init turns a copy of the template into a project that describes itself.

Run against throwaway copies of this repository -- every tracked file,
plus anything untracked git would not ignore -- never against the
repository itself. The copy is initialized as `widget-works`, and then
asked the questions its own suite asks: does the layout contract describe
the tree, does the namespace in the shapes agree with the project file,
is every file's licence decided.

What this does not cover: the vendoring rebuild. It needs the network or
a warm cache, so the copy here is initialized with --offline -- every
other generator runs -- and the suites that read the extracts are not run
in it. A full init, rebuild included, is run by hand before a template
release and recorded in docs/template/ROADMAP.md; a CI job doing the same
is roadmap phase 8.

Declared `template: only`: init deletes this file, because in a project
there is no template to initialize. So it asserts it is in the template
rather than skipping when it is not.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest

from conftest import load_tool

ARGS = ["--id", "widget-works", "--title", "Widget Works Ontology",
        "--description", "What widgets are, and the works that make them.",
        "--repository", "owner/Widget-Works"]
NEW_BASE = "https://fandaws.com/ontology/widget-works"


def run(root, *command, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k != "GITHUB_REPOSITORY"}
    env.update(env_extra or {})
    result = subprocess.run([sys.executable, *command], cwd=str(root),
                            capture_output=True, env=env)
    out = (result.stdout + result.stderr).decode("utf-8", "replace")
    return result.returncode, out


def git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@invalid",
                    *args], cwd=str(root), check=True, capture_output=True)


def copy_of(repo, target):
    """The repository's files, in a fresh git repository of their own."""
    names = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=str(repo), check=True, capture_output=True
    ).stdout.decode("utf-8").splitlines()
    copied = 0
    for name in names:
        source = repo / name
        if not source.is_file():
            continue
        (target / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target / name)
        copied += 1
    assert copied > 30, "only %d files were copied" % copied
    git(target, "init", "-q")
    git(target, "add", "-A")
    # Carry the executable bit over from the index, to both places git
    # reads it. "Use this template" copies git objects, modes included. A
    # plain file copy loses the bit: on Windows (core.filemode=false) git
    # takes the mode from the index, so it is set there; on Linux git
    # compares the index with the file on disk, so it is set there too --
    # setting only the index made CI's copy look modified, and init
    # refused it as a dirty tree.
    staged = subprocess.run(["git", "ls-files", "-s"], cwd=str(repo),
                            check=True, capture_output=True
                            ).stdout.decode("utf-8").splitlines()
    for row in staged:
        mode, _blob, _stage, name = row.split(None, 3)
        if mode == "100755":
            path = target / name
            path.chmod(path.stat().st_mode | 0o111)
            git(target, "update-index", "--chmod=+x", name)
    git(target, "commit", "-q", "-m", "copy")
    return target


@pytest.fixture(scope="module", autouse=True)
def in_template(project):
    assert project.is_template(), (
        "this file is template-only and init should have removed it")


@pytest.fixture(scope="module")
def initialized(repo, tmp_path_factory):
    root = copy_of(repo, tmp_path_factory.mktemp("copy") / "r")
    code, out = run(root, "tools/init_project.py", *ARGS, "--offline")
    assert code == 0, out
    # No `git add` here: init stages its own changes, and the suite must
    # pass on what it leaves (T13).
    return root


def read(root, relative):
    return (root / relative).read_bytes().decode("utf-8")


# -------------------------------------------------------- the result


def test_a_project_refuses_to_be_initialized_again(initialized):
    """The copy init has just run in says template: false now."""
    code, out = run(initialized, "tools/init_project.py", *ARGS, "--dry-run",
                    "--allow-dirty")
    assert code != 0 and "already a project" in out, out


def test_the_project_file_says_what_was_asked(initialized):
    import yaml

    values = yaml.safe_load(read(initialized, "config/project.yaml"))
    assert values["template"] is False
    assert values["id"] == "widget-works"
    assert values["code"] == "WIDGETWORKS"
    assert values["prefix"] == "widget_works"
    assert values["namespace"] == NEW_BASE + "#"
    assert values["iri_base"] == NEW_BASE
    assert values["repository"] == "owner/Widget-Works"
    assert values["title"] == "Widget Works Ontology"
    assert values["description"].startswith("What widgets are")
    assert "# The project's own values" in read(initialized,
                                                 "config/project.yaml"), (
        "the comments explaining the fields did not survive")


def test_the_module_is_renamed_and_rewritten(initialized):
    import rdflib

    assert not (initialized / "ontology/example.ttl").exists()
    module = initialized / "ontology/widget-works.ttl"
    graph = rdflib.Graph()
    graph.parse(module, format="turtle")
    headers = list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
    assert [str(h) for h in headers] == [NEW_BASE]
    assert "Widget Works Ontology" in read(initialized,
                                           "ontology/widget-works.ttl")
    assert "path: ontology/widget-works.ttl" in read(
        initialized, "config/repository-layout.yaml")


def test_the_template_namespace_survives_only_where_the_network_is_needed(
        initialized):
    """--offline runs every generator but the vendoring rebuild, so the
    template's IRI base may survive in the vendored files and their
    manifest -- the rebuild's output -- and nowhere else. Anything else
    still naming it is a file a generator should have rewritten and did
    not, or one no generator owns that init missed."""
    allowed = ("vendor/", "config/upstream-extracts.json")
    old = "fandaws.com/ontology/example"
    stray = []
    for path in initialized.rglob("*"):
        relative = path.relative_to(initialized).as_posix()
        if (not path.is_file() or relative.startswith(".git/")
                or relative.startswith(allowed)):
            continue
        text = path.read_bytes().decode("utf-8", "replace")
        # The Protégé files import the vendored files by their ontology
        # IRIs, which only the rebuild changes: there, and only there, the
        # old base may stand in front of /vendor/.
        if relative.startswith("protege/"):
            text = text.replace(old + "/vendor/", "")
        # The manifest records what the project was made from, the
        # template's own values included (`identity`, decision 32): there,
        # and only in that block, the template's base is the record.
        if relative == "config/template-manifest.json":
            data = json.loads(text)
            data.pop("identity", None)
            text = json.dumps(data)
        if old in text:
            stray.append(relative)
    assert stray == [], stray
    edit = read(initialized, "protege/edit.ttl")
    assert "<https://fandaws.com/ontology/widget-works/edit>" in edit, (
        "the Protégé generator did not run under --offline")


def test_the_template_only_parts_are_gone(initialized):
    assert not (initialized / "docs/template").exists()
    contract = read(initialized, "config/repository-layout.yaml")
    assert "template-only" not in contract
    assert "template: only" not in contract
    readme = read(initialized, "README.md")
    assert readme.startswith("# Widget Works Ontology")
    assert "{{" not in readme
    assert "Widget Works Ontology" in read(initialized, "CLAUDE.md")
    assert "Widget Works Ontology" in read(initialized, "docs/HANDOFF.md")
    import yaml

    cff = yaml.safe_load(read(initialized, "CITATION.cff"))
    assert cff["title"] == "Widget Works Ontology"
    assert cff["repository-code"] == "https://github.com/owner/Widget-Works"


def test_the_porting_guide_and_form_survive_init(initialized):
    """The form ships outside docs/template/, which init deletes (T21)."""
    assert (initialized / "docs/PORTING.md").is_file()
    assert (initialized / "docs/porting/port-report.md").is_file()
    assert (initialized / "tests/project/README.md").is_file()


def test_the_readme_names_each_setup_step(repo, initialized):
    """What the BPO port had to find out for itself (T15): the command-line
    route, the git hook, the suite command and its time, Pages through the
    API; and the rendered CLAUDE.md does not forbid the push that the
    last step needs."""
    readme = read(repo, "README.md")
    steps = readme[readme.index("## Starting a project"):
                   readme.index("## Keeping up with the template")]
    for needed in ("gh repo create", "--template Skreen5hot/Ontology-Template",
                   "git config core.hooksPath .githooks",
                   'python -m pytest tests/ -q -p no:randomly -m "not reasoning',
                   "80 s on GitHub's standard runner",
                   "gh api -X POST repos/owner/Widget-Ontology/pages -f "
                   "build_type=workflow",
                   "git diff --staged", "research/", "docs/PORTING.md"):
        assert needed in steps, needed
    claude = read(initialized, "CLAUDE.md")
    assert "Nothing is pushed without the architect's say-so, except the " \
           "first push" in claude.replace("\n", " ")
    project_readme = read(initialized, "README.md")
    assert "git config core.hooksPath .githooks" in project_readme


def test_a_template_tag_skips_the_release_and_a_project_tag_does_not(
        repo, initialized):
    """The Release workflow's first job greps project.yaml for the line
    that marks the template. That line must be in the template's file,
    exactly, and not in a project's after init, or a project's tag would
    publish nothing and pass."""
    import yaml

    workflow = yaml.safe_load(read(repo, ".github/workflows/release.yml"))
    jobs = workflow["jobs"]
    assert jobs["release"]["needs"] == "which"
    assert jobs["release"]["if"] == "needs.which.outputs.template != 'true'"
    flag = "grep -qx 'template: true' config/project.yaml"
    assert any(flag in step.get("run", "") for step in jobs["which"]["steps"])
    assert "template: true" in read(repo, "config/project.yaml").splitlines()
    assert "template: true" not in read(
        initialized, "config/project.yaml").splitlines()


def test_init_ends_by_asking_for_the_pins_then_pages(repo):
    """Decision 16: checking every pin is the first step after init, so
    the message init ends with names it, before Pages and the push, as
    the README's steps do."""
    init = load_tool("t_init_next", "tools/init_project.py")
    pins = [i for i, s in enumerate(init.NEXT_STEPS) if '"Pins"' in s]
    pages = [i for i, s in enumerate(init.NEXT_STEPS) if "Pages" in s]
    assert pins and pages and pins[0] < pages[0], init.NEXT_STEPS
    readme = read(repo, "README.md")
    assert readme.index("**Check every pin.**") < readme.index(
        "Enable GitHub Pages")


def test_the_owned_files_are_untouched(repo, initialized):
    """init must not write a template-owned file: the manifest says what
    the template shipped, and a project should start with no divergence."""
    status = load_tool("t_status_for_init", "tools/template_status.py")
    for name, digest in status.recorded()["files"].items():
        assert status.sha256_of((initialized / name).read_bytes()) == digest, (
            name)


def test_init_stages_everything_it_changed(initialized):
    """Nothing init or its generators did is left unstaged or untracked,
    so `git diff --staged` is the whole of it and `git ls-files` -- which
    the layout and licensing checks read -- describes the project."""
    status = subprocess.run(["git", "status", "--porcelain"],
                            cwd=str(initialized), capture_output=True,
                            check=True).stdout.decode("utf-8")
    loose = [row for row in status.splitlines()
             if row[1] != " " or row.startswith("??")]
    assert loose == [], loose
    staged = subprocess.run(["git", "diff", "--staged", "--name-status",
                             "-M"], cwd=str(initialized),
                            capture_output=True, check=True
                            ).stdout.decode("utf-8").splitlines()
    assert any(row.startswith("R")
               and row.endswith("ontology/widget-works.ttl")
               for row in staged), (
        "the module was not moved with git mv: %s" % staged)


def test_the_suite_passes_straight_after_init(initialized):
    """The copy's own checks, run in the copy straight after init, with
    no staging by hand (T13): the layout contract, the licensing
    classification, the project file, and the whole suite but this file
    -- with GITHUB_REPOSITORY naming the new repository, as Actions
    would. The suite was a list of files once, and a test the list left
    out passed in the template and failed in every project."""
    env = {"GITHUB_REPOSITORY": "owner/Widget-Works"}
    code, out = run(initialized, "tools/project.py", "--check",
                    env_extra=env)
    assert code == 0, out
    code, out = run(initialized, "tools/layout.py")
    assert code == 0, out
    code, out = run(initialized, "tools/licensing/disposition.py", "--check")
    assert code == 0, out
    code, out = run(initialized, "-m", "pytest", "-q", "-p", "no:randomly",
                    "-p", "no:cacheprovider", "tests/",
                    "--ignore=tests/test_init_project.py",
                    # --offline leaves the extracts as the template's,
                    # headers and all; a network init rebuilds them, and
                    # RELEASING.md item 3 runs one before each release.
                    "--deselect", "tests/test_upstream_vendoring.py::"
                    "test_the_extract_headers_name_this_project", "-m", "not reasoning and not scale and not corpus",
                    env_extra=env)
    assert code == 0, out[-3000:]
    code, out = run(initialized, "tools/site/build_site.py",
                    env_extra=env)
    assert code == 0, out[-3000:]
    code, out = run(initialized, "tools/site/check_site.py",
                    env_extra=env)
    assert code == 0, out[-3000:]
    home = (initialized / "_site/index.html").read_text(encoding="utf-8")
    # The site names the new project, from the project file, and nothing
    # of the template's: no step of init touched the site.
    assert "<title>Widget Works Ontology</title>" in home
    assert "github.com/owner/Widget-Works" not in home, (
        "built as private by default, so no link into the repository")
    assert "Example Ontology" not in home
    assert (initialized / "_site/downloads/widget-works-ontology.zip").is_file()


def test_init_records_each_message_it_removes(initialized, repo):
    """Template decision 39: every message of the template's
    correspondence, by path and the digest of its committed bytes."""
    import hashlib

    import yaml

    raw = yaml.safe_load(read(initialized, "communications/removed-at-init.yaml"))
    listed = {(r["path"], r["sha256"]) for r in raw["removed"]}
    names = subprocess.run(["git", "ls-files", "communications/*/*/*.md"],
                           cwd=str(repo), check=True, capture_output=True
                           ).stdout.decode("utf-8").split()
    expected = {(n, hashlib.sha256((repo / n).read_bytes()).hexdigest())
                for n in names}
    assert listed == expected and listed


def test_committing_init_leaves_the_communications_record_clean(
        initialized, tmp_path):
    """The defect decision 39 fixed: a person commits what init did, and
    the communications check refused every message init removed as
    deleted. Run in a copy, so the shared project stays uncommitted for
    the tests above."""
    copy = tmp_path / "committed"
    shutil.copytree(initialized, copy, ignore=shutil.ignore_patterns("_site"))
    git(copy, "add", "-A")
    git(copy, "commit", "-q", "-m", "init")
    code, out = run(copy, "tools/communications.py")
    assert code == 0, out


# -------------------------------------------------------- refusals


def test_a_dry_run_writes_nothing(repo, tmp_path):
    root = copy_of(repo, tmp_path / "r")
    code, out = run(root, "tools/init_project.py", *ARGS, "--dry-run")
    assert code == 0, out
    assert "write   config/project.yaml" in out, out
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(root),
                            capture_output=True).stdout
    assert status == b"", status


@pytest.mark.parametrize("change", ["README.md", "notes.md",
                                    "research-notes/a.md"])
def test_any_other_change_still_blocks_init(repo, tmp_path, change):
    """init rewrites files across the tree; from a dirty checkout its
    changes could not be told from the ones already there. An edit, a
    new file, and a directory merely named like research/: all refused."""
    root = copy_of(repo, tmp_path / "r")
    (root / change).parent.mkdir(parents=True, exist_ok=True)
    (root / change).write_bytes(b"edited\n")
    code, out = run(root, "tools/init_project.py", *ARGS, "--dry-run")
    assert code != 0 and "uncommitted changes" in out, out
    assert change in out, out


def test_research_notes_do_not_block_init(repo, tmp_path):
    """A port report is filled in as the port goes, from before init
    runs; research/ is where it lives, and init never writes there (T14).
    So init runs, and leaves the notes as they were: unstaged."""
    root = copy_of(repo, tmp_path / "r")
    (root / "research/port-report.md").write_bytes(b"# Port report\n")
    with open(root / "research/README.md", "ab") as handle:
        handle.write(b"\nedited\n")
    code, out = run(root, "tools/init_project.py", *ARGS, "--offline",
                    "--no-regenerate")
    assert code == 0, out
    status = subprocess.run(["git", "status", "--porcelain", "--",
                             "research/"], cwd=str(root),
                            capture_output=True, check=True
                            ).stdout.decode("utf-8").splitlines()
    assert sorted(status) == [" M research/README.md",
                              "?? research/port-report.md"], status


def test_the_dirty_check_reads_porcelain_z():
    """-z: a path with a space is one path, and a rename is two."""
    init = load_tool("t_init_dirty", "tools/init_project.py")
    status = ("?? research/a b.md\0 M README.md\0"
              "R  docs/new.md\0research/old.md\0?? researcher.md\0")
    assert init.changes_outside(status) == [
        "README.md", "docs/new.md", "researcher.md"]


@pytest.mark.parametrize("override, expect", [
    (["--id", "Widget"], "is not lowercase"),
    (["--repository", "widget"], "is not owner/name"),
    (["--prefix", "owl"], "already used"),
])
def test_bad_values_are_refused_before_anything_is_written(
        repo, tmp_path, override, expect):
    root = copy_of(repo, tmp_path / "r")
    args = list(ARGS)
    for flag, value in zip(override[::2], override[1::2]):
        if flag in args:
            args[args.index(flag) + 1] = value
        else:
            args += [flag, value]
    code, out = run(root, "tools/init_project.py", *args)
    assert code != 0 and expect in out, out
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(root),
                            capture_output=True).stdout
    assert status == b"", "a refused init wrote %s" % status


def test_init_refuses_to_write_an_owned_file(monkeypatch):
    """If a skeleton were ever rendered over a template-owned file, every
    project would start diverged from the template it was made from."""
    init = load_tool("t_init_owned", "tools/init_project.py")
    monkeypatch.setattr(init, "RENDERED",
                        dict(init.RENDERED, **{"README.md":
                                               "docs/DEVELOPMENT.md"}))
    args = init.argparse.Namespace(
        id="widget-works", title="W", description="D",
        repository="owner/Widget-Works", code=None, prefix=None,
        iri_base=None, licence_holder=None)
    old = dict(init.project.load())
    new = init.values_of(args, old)
    with pytest.raises(SystemExit) as error:
        init.plan(init.layout.repository_root(), old, new)
    assert "which the template owns" in str(error.value)



# ------------------------------------------ seeded files (P-A3, d. 32)
#
# A template copy with history of its own (a commit, then the manifest
# recorded and committed, as a release does), and a project made from it.
# Each test changes copies of the two, never the fixtures themselves.


@pytest.fixture(scope="module")
def template_copy(repo, tmp_path_factory):
    root = copy_of(repo, tmp_path_factory.mktemp("template") / "t")
    code, out = run(root, "tools/template_status.py", "--record")
    assert code == 0, out
    git(root, "add", "-A")
    git(root, "commit", "-q", "-m", "record")
    return root


@pytest.fixture(scope="module")
def made(template_copy, tmp_path_factory):
    root = copy_of(template_copy, tmp_path_factory.mktemp("made") / "p")
    code, out = run(root, "tools/init_project.py", *ARGS, "--offline")
    assert code == 0, out
    return root


def clone(source, target):
    shutil.copytree(source, target)
    return target


def append(root, relative, text="# changed\n"):
    path = root / relative
    path.write_bytes(path.read_bytes() + text.encode("utf-8"))


def record(root, *, before_v030=False):
    path = root / "config/template-manifest.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if before_v030:
        for key in ("seeded", "seeded_digest", "identity", "initialized"):
            data.pop(key, None)
        data["format_version"] = 1
        path.write_bytes(json.dumps(data, indent=2, sort_keys=True)
                         .encode("utf-8") + b"\n")
        # And its layout, which marks no file seeded.
        layout = root / "config/repository-layout.yaml"
        layout.write_bytes(layout.read_bytes().replace(
            b"    template: seeded\n", b""))
    return data


REALIST = "shapes/realist_shapes.ttl"
SKOS = "shapes/skos_shapes.ttl"
NAMING = "config/naming.yaml"


def test_init_records_each_seeded_file_as_it_left_it(made):
    data = record(made)
    status = load_tool("t_status_seeded", "tools/template_status.py")
    seeded = data["initialized"]["seeded"]
    assert seeded and set(seeded) == set(status.seeded_files(made))
    for name, digest in seeded.items():
        assert status.sha256_of((made / name).read_bytes()) == digest, name
    assert data["initialized"]["values"]["iri_base"] == NEW_BASE
    code, out = run(made, "tools/template_status.py")
    assert code == 0, out
    assert "every seeded file is as the template left it" in out


def test_the_template_it_was_made_from_reports_no_change(made,
                                                         template_copy):
    """The round trip: the template's shapes, through init's rewrite,
    are the project's shapes byte for byte. Compared as bytes, every
    shape would be reported changed from the first commit."""
    code, out = run(made, "tools/template_status.py", "--against",
                    str(template_copy))
    assert code == 0, out
    assert "changed 0, removed 0, added 0 seeded" in out, out
    assert "every seeded file is as the template left it" in out
    assert "DEPENDENCY CHANGE" not in out and "NOT COMPARED" not in out


def test_template_change_configuration_and_both_are_told_apart(
        made, template_copy, tmp_path):
    project = clone(made, tmp_path / "p")
    template = clone(template_copy, tmp_path / "t")
    append(project, NAMING)
    append(project, REALIST, "# here\n")
    append(template, REALIST, "# there\n")
    append(template, SKOS)
    code, out = run(template, "tools/template_status.py", "--record")
    assert code == 0, out
    code, out = run(project, "tools/template_status.py", "--against",
                    str(template))
    assert code == 0, out
    assert "changed  %s" % REALIST in out and "changed  %s" % SKOS in out
    assert "configured here (expected): %s, %s" % (NAMING, REALIST) in out
    merge = out[out.index("merge by hand"):]
    assert REALIST in merge and SKOS not in merge and NAMING not in merge


def test_a_pin_the_template_moved_is_a_dependency_change(made, template_copy,
                                                         tmp_path):
    template = clone(template_copy, tmp_path / "t")
    pins = template / "config/upstream-sources.yaml"
    text = pins.read_bytes().decode("utf-8")
    assert "release: v2.0-2024-11-06" in text
    pins.write_bytes(text.replace("release: v2.0-2024-11-06",
                                  "release: v9.9", 1).encode("utf-8"))
    code, out = run(template, "tools/template_status.py", "--record")
    assert code == 0, out
    before = (made / "config/upstream-sources.yaml").read_bytes()
    code, out = run(made, "tools/template_status.py", "--against",
                    str(template))
    assert code == 0, out
    assert "changed  config/upstream-sources.yaml" in out
    assert "DEPENDENCY CHANGE, for review" in out
    assert "cco      here v2.0-2024-11-06, template v9.9" in out
    assert (made / "config/upstream-sources.yaml").read_bytes() == before


def test_a_manifest_from_before_v030_is_compared_through_history(
        made, template_copy, tmp_path):
    """A project made from v0.1.0 or v0.2.0 records no seeded file. On
    its own it says it cannot compare them; with the template checkout
    the base is found in its history, and the comparison is exact."""
    project = clone(made, tmp_path / "p")
    record(project, before_v030=True)
    code, out = run(project, "tools/template_status.py")
    assert code == 0, out
    assert "NOT COMPARED" in out and "predates v0.3.0" in out
    assert "every seeded file is as" not in out

    code, out = run(project, "tools/template_status.py", "--against",
                    str(template_copy))
    assert code == 0, out
    assert "every seeded file is as the template left it" in out
    append(project, REALIST)
    code, out = run(project, "tools/template_status.py", "--against",
                    str(template_copy))
    assert "configured here (expected): %s" % REALIST in out, out


def test_without_the_history_nothing_is_reported_unchanged(
        made, template_copy, tmp_path):
    """Decision 32: a checkout without the history is a comparison not
    made, exit 2, and no seeded file is called unchanged."""
    project = clone(made, tmp_path / "p")
    record(project, before_v030=True)
    files = tmp_path / "files"
    shutil.copytree(template_copy, files,
                    ignore=shutil.ignore_patterns(".git"))
    code, out = run(project, "tools/template_status.py", "--against",
                    str(files))
    assert code == 2, out
    assert "NOT COMPARED" in out and "not a git checkout" in out
    assert "every seeded file is as" not in out


def test_a_change_already_taken_is_not_a_merge(made, template_copy,
                                               tmp_path):
    """A file the template changed, and the project changed to the same
    bytes -- by taking the template's version -- is already taken, not a
    conflict: owned files byte for byte, seeded ones through init's
    rewrite. A file the two changed differently is still a merge."""
    project = clone(made, tmp_path / "p")
    template = clone(template_copy, tmp_path / "t")
    owned = "tools/findings.py"
    for root in (project, template):
        append(root, owned)
        append(root, REALIST)
    append(project, SKOS, "# here\n")
    append(template, SKOS, "# there\n")
    code, out = run(template, "tools/template_status.py", "--record")
    assert code == 0, out
    code, out = run(project, "tools/template_status.py", "--against",
                    str(template))
    assert code == 0, out
    taken, merge, section = [], [], None
    for line in out.splitlines():
        if "already taken" in line:
            section = taken
            taken.extend(n.strip() for n in line.split(
                "nothing to merge:", 1)[1].split(",") if n.strip())
        elif "merge by hand" in line:
            section = merge
        elif line.startswith("    ") and section is not None:
            section.append(line.strip())
        else:
            section = None
    assert owned in taken and REALIST in taken, out
    assert merge == [SKOS], out
