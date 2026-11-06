# SPDX-License-Identifier: MIT
"""The dependency lock (tools/lock.py, P-A1, template decision 32),
offline: the lock as committed, then copies of its inputs changed one way
at a time. Resolving it needs the network and runs in the Install
workflow (`--verify`), on Linux, Windows and macOS."""

from __future__ import annotations

import platform
import shutil

import pytest
import yaml

from conftest import load_tool

FILES = ("requirements-dev.txt", "requirements-pip.txt",
         "requirements-lock.txt", "config/tooling.yaml")


@pytest.fixture()
def lock():
    return load_tool("t_lock", "tools/lock.py")


@pytest.fixture()
def copy(repo, tmp_path):
    """The lock and its three inputs, in a scratch root."""
    (tmp_path / "config").mkdir()
    for name in FILES:
        shutil.copyfile(repo / name, tmp_path / name)
    return tmp_path


def rewrite(path, old, new):
    text = path.read_bytes().decode("utf-8")
    assert text.count(old) >= 1, old
    path.write_bytes(text.replace(old, new, 1).encode("utf-8"))


def test_the_committed_lock_is_current_and_whole(lock, repo):
    assert lock.problems(repo) == []


def test_the_lock_holds_what_p_a1_found_unpinned(lock, repo):
    """owlrl, which pyshacl runs, and the platform marker that makes one
    lock serve every platform."""
    found = {e["name"]: e for e in lock.entries(
        (repo / "requirements-lock.txt").read_text(encoding="utf-8"))}
    assert "owlrl" in found and "pip" in found
    assert found["colorama"]["marker"] == "sys_platform == 'win32'"
    assert all(e["hashes"] for e in found.values())
    direct = lock.pins_in((repo / "requirements-dev.txt").read_text(
        encoding="utf-8"))
    assert set(direct) < set(found), "the lock adds the transitive ones"


def test_an_input_changed_after_the_lock_fails(lock, copy):
    for name in ("requirements-dev.txt", "requirements-pip.txt",
                 "config/tooling.yaml"):
        path = copy / name
        before = path.read_bytes()
        path.write_bytes(before + b"# changed\n")
        [problem] = lock.problems(copy)
        assert "is stale" in problem and "python tools/lock.py --write" \
            in problem, problem
        path.write_bytes(before)
    assert lock.problems(copy) == []


def test_a_lock_with_no_digest_fails(lock, copy):
    rewrite(copy / "requirements-lock.txt", "# inputs-sha256: ",
            "# inputs: ")
    assert any("records no inputs digest" in p for p in lock.problems(copy))


def test_a_direct_pin_the_lock_does_not_list_fails(lock, copy, monkeypatch):
    rewrite(copy / "requirements-dev.txt", "pytest==",
            "newpackage==1.0\npytest==")
    monkeypatch.setattr(lock, "inputs_digest", lambda root: lock.DIGEST_LINE
                        .search((root / lock.LOCK).read_text()).group(1))
    assert lock.problems(copy) == [
        "requirements-dev.txt pins newpackage==1.0, and "
        "requirements-lock.txt does not list it"]


def test_a_direct_pin_at_another_version_fails(lock, copy):
    rewrite(copy / "requirements-lock.txt", "pyshacl==0.40.2",
            "pyshacl==0.40.1")
    assert lock.problems(copy) == [
        "requirements-dev.txt pins pyshacl==0.40.2, and "
        "requirements-lock.txt has 0.40.1"]


def test_the_pip_pin_is_held_to_the_lock_too(lock, copy):
    rewrite(copy / "requirements-lock.txt", "\npip==", "\nnotpip==")
    assert any(p.startswith("requirements-pip.txt pins pip==")
               and "does not list it" in p for p in lock.problems(copy))


def test_an_entry_without_a_hash_fails(lock, copy):
    path = copy / "requirements-lock.txt"
    lines = path.read_bytes().decode("utf-8").split("\n")
    start = next(i for i, line in enumerate(lines)
                 if line.startswith("owlrl=="))
    end = next(i for i in range(start + 1, len(lines))
               if not lines[i].startswith("    --hash"))
    lines[start:end] = [lines[start].rstrip(" \\")]
    path.write_bytes("\n".join(lines).encode("utf-8"))
    assert lock.problems(copy) == [
        "requirements-lock.txt: owlrl==7.6.2 has no hash, so pip's "
        "hash-checking mode refuses the whole lock"]


def test_an_entry_not_pinned_exactly_fails(lock, copy):
    path = copy / "requirements-lock.txt"
    path.write_bytes(path.read_bytes() + b"rdflib>=7 \\\n"
                     b"    --hash=sha256:" + b"0" * 64 + b"\n")
    assert lock.problems(copy) == [
        "requirements-lock.txt: 'rdflib>=7' is not pinned with =="]


def test_uv_is_pinned_by_version_and_checksums(lock, repo, copy):
    uv = lock.tooling(repo)
    assert uv["python"] == "3.12", "3.12 stays the declared baseline"
    assert uv["sha256"] and all(len(v) == 64 for v in uv["sha256"].values())
    rewrite(copy / "config/tooling.yaml", sorted(uv["sha256"].values())[0],
            "not-a-checksum")
    with pytest.raises(lock.Refused, match="not a sha256 for"):
        lock.tooling(copy)


@pytest.fixture()
def installs(lock, monkeypatch):
    """Record each pip call the bootstrap makes, and what it was given,
    instead of installing; `versions` is what pip reports, in turn."""
    calls, versions = [], []

    def run(command, cwd=None):
        requirement = command[command.index("-r") + 1]
        calls.append((list(map(str, command)),
                      open(requirement, encoding="utf-8").read()))
    monkeypatch.setattr(lock, "run", run)
    monkeypatch.setattr(lock, "pip_version",
                        lambda python: versions.pop(0))
    return calls, versions


def test_the_bootstrap_installs_only_the_pinned_pip_by_its_hashes(
        lock, repo, installs, capsys):
    calls, versions = installs
    pinned = lock.pins_in((repo / "requirements-pip.txt").read_text(
        encoding="utf-8"))["pip"]
    versions[:] = ["25.0.1", pinned]
    assert lock.bootstrap(repo, python="python") == 0
    [(command, requirement)] = calls
    assert {"--require-hashes", "--no-deps"} <= set(command)
    [entry] = [e for e in lock.entries((repo / "requirements-lock.txt")
               .read_text(encoding="utf-8")) if e["name"] == "pip"]
    assert requirement.startswith("pip==%s " % pinned)
    assert requirement.count("--hash=sha256:") == len(entry["hashes"])
    out = capsys.readouterr().out
    assert "interpreter %s" % platform.python_version() in out
    assert "pip 25.0.1 installed pip %s" % pinned in out


def test_a_bootstrap_that_does_not_end_on_the_pinned_pip_fails(
        lock, repo, installs, capsys):
    calls, versions = installs
    versions[:] = ["25.0.1", "25.0.1"]
    assert lock.bootstrap(repo, python="python") == 1
    assert "FAIL: pip is 25.0.1" in capsys.readouterr().out


def test_a_lock_without_the_pinned_pip_refuses_the_bootstrap(
        lock, copy, installs):
    rewrite(copy / "requirements-lock.txt", "\npip==", "\nnotpip==")
    with pytest.raises(lock.Refused, match="no hashed pip=="):
        lock.bootstrap(copy, python="python")
    assert installs[0] == [], "nothing is installed unchecked"


def test_every_workflow_installs_from_the_lock(repo):
    """No workflow installs from the direct pins, or upgrades pip to
    whatever is newest: each bootstraps the pinned pip, then installs the
    lock in hash-checking mode."""
    for path in sorted((repo / ".github/workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        assert "-r requirements-dev.txt" not in text, path.name
        assert "--upgrade pip" not in text, path.name
        if "actions/setup-python" in text:
            assert "python tools/lock.py --bootstrap" in text, path.name
            assert "--require-hashes -r requirements-lock.txt" in text, \
                path.name


def test_the_install_workflow_covers_three_platforms(repo):
    """Decision 32's first safeguard: one lock, installed fresh on each
    platform, and resolved again there."""
    workflow = yaml.safe_load((repo / ".github/workflows/install.yml")
                              .read_text(encoding="utf-8"))
    job = workflow["jobs"]["install"]
    systems = job["strategy"]["matrix"]["os"]
    assert {s.split("-")[0] for s in systems} == {"ubuntu", "windows",
                                                  "macos"}
    assert not any(s.endswith("latest") for s in systems)
    runs = "\n".join(step.get("run", "") for step in job["steps"])
    for command in ("tools/lock.py --bootstrap", "--require-hashes",
                    "pip check", "tools/lock.py --verify",
                    "validate.py --gate"):
        assert command in runs, command


def test_the_release_workflow_runs_on_a_pinned_runner(repo):
    """Decision 32: Release on ubuntu-24.04, not ubuntu-latest."""
    text = (repo / ".github/workflows/release.yml").read_text(
        encoding="utf-8")
    assert "ubuntu-latest" not in text
    assert text.count("runs-on: ubuntu-24.04") == 2


def test_no_workflow_runs_on_a_moving_runner(repo):
    """Every workflow names the image it runs on, as Release does, so
    the files say what runs and GitHub moving `-latest` changes
    nothing unannounced."""
    for path in sorted((repo / ".github/workflows").glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        assert "-latest" not in text, path.name


def test_a_pip_line_without_hashes_refuses_the_bootstrap(lock, copy,
                                                         installs):
    """The bootstrap installs pip only by its hashes: a pip line with
    none is refused, not installed on trust."""
    path = copy / "requirements-lock.txt"
    lines = path.read_bytes().decode("utf-8").split("\n")
    start = next(i for i, line in enumerate(lines) if line.startswith("pip=="))
    end = next(i for i in range(start + 1, len(lines))
               if not lines[i].startswith("    --hash"))
    lines[start:end] = [lines[start].rstrip(" \\")]
    path.write_bytes("\n".join(lines).encode("utf-8"))
    with pytest.raises(lock.Refused, match="no hashed pip=="):
        lock.bootstrap(copy, python="python")
    assert installs[0] == []
