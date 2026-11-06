# SPDX-License-Identifier: MIT
"""The pin check (tools/pins.py, decision 20), offline: the one function
that touches the network is replaced by answers built from the pins
themselves, then changed one way at a time."""

from __future__ import annotations

import pytest

from conftest import load_tool


@pytest.fixture()
def pins():
    return load_tool("t_pins", "tools/pins.py")


def upstream_answering(found, *, latest=None, moved=None, vulns=None,
                       down=None, published=None):
    """A fake upstream that agrees with every pin, except where told:
    `latest` gives a pin's name a newer release, `moved` makes a tag name
    another commit, `vulns` gives a Python distribution advisories, `down`
    fails every lookup whose URL contains it, `published` replaces the
    files PyPI lists for uv's release ({file name: sha256})."""
    latest, moved, vulns = latest or {}, moved or {}, vulns or {}
    by_repo = {}
    for pin in found:
        if pin["kind"] == "action":
            by_repo[pin["name"]] = pin
        elif pin.get("repo"):
            by_repo[pin["repo"]] = pin

    def fetch(url, data=None):
        if down and down in url:
            raise OSError("unreachable")
        if url == "https://api.osv.dev/v1/querybatch":
            return {"results": [
                {"vulns": [{"id": v} for v in vulns.get(
                    q["package"]["name"], [])]} for q in data["queries"]]}
        if url.startswith("https://pypi.org/pypi/"):
            name = url.split("/")[4]
            pin = next(p for p in found if p["name"] == name)
            if url.count("/") == 6:
                files = (published if published is not None
                         else pin["sha256"])
                return {"urls": [{"filename": n, "digests": {"sha256": h}}
                                 for n, h in files.items()]}
            return {"info": {"version": latest.get(name, pin["pinned"])}}
        repo = "/".join(url.split("/")[4:6])
        pin = by_repo[repo]
        if url.endswith("/releases/latest"):
            return {"tag_name": latest.get(pin["name"], pin["pinned"])}
        return {"sha": moved.get(pin["name"], pin["commit"])}
    return fetch


def test_every_place_the_pins_section_names_is_read(pins, repo):
    """The places test_the_pins_section_names_every_pin_file holds
    DEVELOPMENT.md to, and every `uses:` line in the workflows."""
    found = pins.collect(repo)
    kinds = {p["kind"] for p in found}
    assert kinds == {"action", "python", "locked", "tool", "upstream",
                     "reasoner"}, kinds
    uses = sum(text.count("uses:") for text in (
        p.read_text(encoding="utf-8")
        for p in (repo / ".github/workflows").glob("*.yml")))
    assert sum(len(p["where"]) for p in found
               if p["kind"] == "action") == uses
    lines = [line for name in ("requirements-dev.txt",
                               "requirements-pip.txt")
             for line in (repo / name).read_text(
                 encoding="utf-8").splitlines() if "==" in line]
    assert len([p for p in found if p["kind"] == "python"]) == len(lines)
    lock = load_tool("t_pins_lock", "tools/lock.py")
    locked = lock.entries((repo / "requirements-lock.txt").read_text(
        encoding="utf-8"))
    assert (len([p for p in found if p["kind"] in ("python", "locked")])
            == len(locked)), "every locked distribution is a pin, once"
    assert any(p["name"] == "owlrl" and p["kind"] == "locked"
               for p in found), "P-A1's own example"
    assert {p["name"] for p in found if p["kind"] == "upstream"} >= {
        "bfo", "cco"}
    assert all(p.get("repo") for p in found
               if p["kind"] in ("upstream", "reasoner"))


def test_all_current_passes_and_names_the_commit(pins, repo, monkeypatch,
                                                 capsys):
    found = pins.collect(repo)
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(found))
    assert pins.main([]) == 0
    out = capsys.readouterr().out
    assert out.startswith("Pins at ")
    assert pins.head(repo).split()[0] in out
    assert "0 failed" in out and "0 with a newer release" in out


def test_a_newer_release_is_reported_not_failed(pins, repo, monkeypatch,
                                                capsys):
    found = pins.collect(repo)
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(
        found, latest={"cco": "v9.9", "pytest": "99.0"}))
    assert pins.main([]) == 0
    out = capsys.readouterr().out
    assert "newer: v9.9" in out and "newer: 99.0" in out
    assert "2 with a newer release" in out


def test_a_commit_its_tag_does_not_name_fails(pins, repo, monkeypatch,
                                              capsys):
    found = pins.collect(repo)
    action = next(p["name"] for p in found if p["kind"] == "action")
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(
        found, moved={action: "f" * 40, "robot": "e" * 40}))
    assert pins.main([]) == 1
    out = capsys.readouterr().out
    assert out.count("is not what") == 2, out


def test_a_published_advisory_fails(pins, repo, monkeypatch, capsys):
    found = pins.collect(repo)
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(
        found, vulns={"rdflib": ["GHSA-test-0001"]}))
    assert pins.main([]) == 1
    assert "published advisories: GHSA-test-0001" in capsys.readouterr().out


@pytest.mark.parametrize("down", ["pypi.org", "api.osv.dev",
                                  "api.github.com"])
def test_a_pin_that_could_not_be_checked_fails(pins, repo, monkeypatch,
                                               capsys, down):
    found = pins.collect(repo)
    monkeypatch.setattr(pins, "fetch_json",
                        upstream_answering(found, down=down))
    assert pins.main([]) == 1
    assert "not checked" in capsys.readouterr().out


def test_the_docs_point_to_the_command(repo):
    """A project's first step and a release's first item name it. The
    release checklist and the skeletons are the template's own, and init
    removes them."""
    project = load_tool("t_project_for_pins", "tools/project.py")
    paths = ["docs/DEVELOPMENT.md", "README.md"]
    if project.is_template():
        paths += ["docs/template/RELEASING.md",
                  "docs/template/skeletons/README.md"]
    for path in paths:
        text = (repo / path).read_text(encoding="utf-8")
        assert "tools/pins.py" in text, path


def test_an_advisory_against_a_locked_distribution_fails(pins, repo,
                                                         monkeypatch, capsys):
    """P-A1: the transitive distributions are installed, so they are
    scanned like the direct ones."""
    found = pins.collect(repo)
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(
        found, vulns={"owlrl": ["GHSA-test-0002"]}))
    assert pins.main([]) == 1
    out = capsys.readouterr().out
    assert "published advisories: GHSA-test-0002" in out
    assert "owlrl have advisories" in out


def test_a_clean_scan_says_how_much_it_scanned(pins, repo, monkeypatch,
                                               capsys):
    found = pins.collect(repo)
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(found))
    assert pins.main([]) == 0
    scanned = len([p for p in found if p["kind"] in pins.SCANNED])
    assert ("Advisories: osv.dev scanned all %d Python distribution(s); "
            "none has one." % scanned) in capsys.readouterr().out


def test_a_scan_that_could_not_run_is_never_read_as_clean(pins, repo,
                                                          monkeypatch,
                                                          capsys):
    """Decision 32's third safeguard: no advisories and no scan are
    different results, in the text and in the JSON."""
    found = pins.collect(repo)
    monkeypatch.setattr(pins, "fetch_json",
                        upstream_answering(found, down="api.osv.dev"))
    assert pins.main([]) == 1
    out = capsys.readouterr().out
    assert "Advisories: NOT SCANNED" in out
    assert "none has one" not in out
    monkeypatch.setattr(pins, "fetch_json",
                        upstream_answering(found, down="api.osv.dev"))
    assert pins.main(["--json"]) == 1
    import json
    report = json.loads(capsys.readouterr().out)
    assert report["advisory_scan"]["ran"] is False


def test_a_partial_scan_is_not_a_scan(pins, repo, monkeypatch, capsys):
    """osv.dev answering fewer queries than were asked is a scan that did
    not run, not a clean answer for the ones it skipped."""
    found = pins.collect(repo)
    honest = upstream_answering(found)

    def short(url, data=None):
        answer = honest(url, data)
        if url == "https://api.osv.dev/v1/querybatch":
            answer["results"] = answer["results"][:-1]
        return answer
    monkeypatch.setattr(pins, "fetch_json", short)
    assert pins.main([]) == 1
    assert "Advisories: NOT SCANNED" in capsys.readouterr().out


def test_uv_checksums_must_be_the_ones_pypi_publishes(pins, repo,
                                                      monkeypatch, capsys):
    """Decision 32's second safeguard, checked against PyPI: a recorded
    checksum PyPI does not publish fails, and so does a published file
    with no checksum recorded, which pip could pick and then refuse."""
    found = pins.collect(repo)
    uv = next(p for p in found if p["kind"] == "tool")
    name = sorted(uv["sha256"])[0]
    tampered = dict(uv["sha256"], **{name: "0" * 64})
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(
        found, published=tampered))
    assert pins.main([]) == 1
    assert "not as published: %s" % name in capsys.readouterr().out

    extra = dict(uv["sha256"], **{"uv-new-platform.whl": "1" * 64})
    monkeypatch.setattr(pins, "fetch_json", upstream_answering(
        found, published=extra))
    assert pins.main([]) == 1
    assert "not recorded: uv-new-platform.whl" in capsys.readouterr().out
