# SPDX-License-Identifier: MIT
"""init turns a copy of the template into a project that describes itself.

Run against throwaway copies of this repository -- every tracked file,
plus anything untracked git would not ignore -- never against the
repository itself. The copy is initialized as `widget-works`, and then
asked the questions its own suite asks: does the layout contract describe
the tree, does the namespace in the shapes agree with the project file,
is every file's licence decided.

What this does not cover: the generators. init regenerates the extracts,
which needs the network or a warm cache, so the copy here is initialized
with --no-regenerate and the suites that read the extracts are not run in
it. A full init, regeneration included, is run by hand before a template
release and recorded in docs/template/ROADMAP.md; a CI job doing the same
is roadmap phase 8.

Declared `template: only`: init deletes this file, because in a project
there is no template to initialize. So it asserts it is in the template
rather than skipping when it is not.
"""

from __future__ import annotations

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
    # Carry the executable bit over from the index. "Use this template"
    # copies git objects, modes included; a file copy on a filesystem git
    # does not trust for modes (Windows, core.filemode=false) loses it,
    # and the copy would then fail a check the real one passes.
    staged = subprocess.run(["git", "ls-files", "-s"], cwd=str(repo),
                            check=True, capture_output=True
                            ).stdout.decode("utf-8").splitlines()
    for row in staged:
        mode, _blob, _stage, name = row.split(None, 3)
        if mode == "100755":
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
    code, out = run(root, "tools/init_project.py", *ARGS, "--no-regenerate")
    assert code == 0, out
    git(root, "add", "-A")
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


def test_the_template_namespace_survives_nowhere_but_generated_files(
        initialized):
    """The generated files still carry it -- --no-regenerate -- and are
    the only ones that may."""
    generated = ("vendor/", "config/upstream-extracts.json")
    stray = []
    for path in initialized.rglob("*"):
        relative = path.relative_to(initialized).as_posix()
        if (not path.is_file() or relative.startswith(".git/")
                or relative.startswith(generated)):
            continue
        if "fandaws.com/ontology/example" in path.read_bytes().decode(
                "utf-8", "replace"):
            stray.append(relative)
    assert stray == [], stray


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


def test_the_owned_files_are_untouched(repo, initialized):
    """init must not write a template-owned file: the manifest says what
    the template shipped, and a project should start with no divergence."""
    status = load_tool("t_status_for_init", "tools/template_status.py")
    for name, digest in status.recorded()["files"].items():
        assert status.sha256_of((initialized / name).read_bytes()) == digest, (
            name)


def test_the_copy_passes_its_own_suite(initialized):
    """The copy's own checks, run in the copy: the layout contract, the
    namespace agreement between the shapes and the project file, the
    licensing classification, the project file, the communications
    record, and the uninitialized-copy refusal -- with GITHUB_REPOSITORY
    naming the new repository, as Actions would."""
    env = {"GITHUB_REPOSITORY": "owner/Widget-Works"}
    code, out = run(initialized, "tools/project.py", "--check",
                    env_extra=env)
    assert code == 0, out
    code, out = run(initialized, "tools/layout.py")
    assert code == 0, out
    code, out = run(initialized, "tools/licensing/disposition.py", "--check")
    assert code == 0, out
    code, out = run(initialized, "-m", "pytest", "-q", "-p", "no:randomly",
                    "-p", "no:cacheprovider",
                    "tests/test_namespace.py",
                    "tests/test_repository_layout.py",
                    "tests/test_licensing.py", "tests/test_project.py",
                    "tests/test_communications.py",
                    "tests/test_iri_lint.py",
                    env_extra=env)
    assert code == 0, out[-3000:]


# -------------------------------------------------------- refusals


def test_a_dry_run_writes_nothing(repo, tmp_path):
    root = copy_of(repo, tmp_path / "r")
    code, out = run(root, "tools/init_project.py", *ARGS, "--dry-run")
    assert code == 0, out
    assert "write   config/project.yaml" in out, out
    status = subprocess.run(["git", "status", "--porcelain"], cwd=str(root),
                            capture_output=True).stdout
    assert status == b"", status


def test_a_dirty_tree_is_refused(repo, tmp_path):
    """init rewrites files across the tree; from a dirty checkout its
    changes could not be told from the ones already there."""
    root = copy_of(repo, tmp_path / "r")
    (root / "README.md").write_bytes(b"edited\n")
    code, out = run(root, "tools/init_project.py", *ARGS, "--dry-run")
    assert code != 0 and "uncommitted changes" in out, out


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
