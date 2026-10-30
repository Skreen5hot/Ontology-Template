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
                       down=None):
    """A fake upstream that agrees with every pin, except where told:
    `latest` gives a pin's name a newer release, `moved` makes a tag name
    another commit, `vulns` gives a Python pin advisories, `down` fails
    every lookup whose URL contains it."""
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
            return {"info": {"version": latest.get(name, pin["pinned"])}}
        repo = "/".join(url.split("/")[4:6])
        pin = by_repo[repo]
        if url.endswith("/releases/latest"):
            return {"tag_name": latest.get(pin["name"], pin["pinned"])}
        return {"sha": moved.get(pin["name"], pin["commit"])}
    return fetch


def test_every_place_the_pins_section_names_is_read(pins, repo):
    """The same four places test_the_pins_section_names_every_pin_file
    holds DEVELOPMENT.md to, and every `uses:` line in the workflows."""
    found = pins.collect(repo)
    kinds = {p["kind"] for p in found}
    assert kinds == {"action", "python", "upstream", "reasoner"}, kinds
    uses = sum(text.count("uses:") for text in (
        p.read_text(encoding="utf-8")
        for p in (repo / ".github/workflows").glob("*.yml")))
    assert sum(len(p["where"]) for p in found
               if p["kind"] == "action") == uses
    lines = [line for line in (repo / "requirements-dev.txt").read_text(
        encoding="utf-8").splitlines() if "==" in line]
    assert len([p for p in found if p["kind"] == "python"]) == len(lines)
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
