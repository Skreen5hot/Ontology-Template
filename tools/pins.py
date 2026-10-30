# SPDX-License-Identifier: MIT
"""Check every pin against its upstream, with output that can be cited.

    python tools/pins.py            # the report; exit 1 if any pin fails
    python tools/pins.py --json     # the same, as JSON

WHY THIS EXISTS

Nothing updates this repository's pins by itself (template decision
16), so checking them is a person's job: the first thing a project does,
and the first item of a template release. Done from a paragraph in the
docs, "every pin checked" is a claim. The BPO Testing Team asked for a
command whose output is the evidence (decision 20): it names the commit
it ran on and when, and every pin with what it found.

What it reads is what docs/DEVELOPMENT.md, "Pins", lists:

  - each GitHub Action in .github/workflows/*.yml, by commit SHA, with
    the release tag in its trailing comment;
  - each Python package in requirements-dev.txt;
  - each upstream in config/upstream-sources.yaml, by release and commit;
  - ROBOT in config/reasoning.yaml, by version and tag commit.

For each it reports the latest release upstream. A pin behind it is
reported, not failed: keeping a pin can be a decision (CCO, decision
18). It fails, and exits 1, on what no decision makes right:

  - a published advisory against a Python pin (osv.dev);
  - a pinned commit that is not what its tag names upstream -- the tag
    moved, or the comment or the commit is wrong;
  - a pin it could not check. An unchecked pin is not a checked one.

It needs the network. GITHUB_TOKEN, if set, is sent to the GitHub API
to raise its rate limit; nothing else is sent anywhere but the names and
versions being checked.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402

WORKFLOWS = ".github/workflows"
REQUIREMENTS = "requirements-dev.txt"
UPSTREAMS = "config/upstream-sources.yaml"
REASONING = "config/reasoning.yaml"

GITHUB = "https://api.github.com"
PYPI = "https://pypi.org/pypi/%s/json"
OSV = "https://api.osv.dev/v1/querybatch"

USES = re.compile(r"uses:\s*([\w.-]+/[\w.-]+)@([0-9a-f]{40})\s*#\s*(\S+)")
REQUIREMENT = re.compile(r"^([A-Za-z0-9_.-]+)==(\S+)$")
RAW = re.compile(r"^https://raw\.githubusercontent\.com/([\w.-]+/[\w.-]+)/")


def fetch_json(url: str, data: dict | None = None):
    """GET, or POST `data` as JSON. The one place this tool touches the
    network, so a test can replace it."""
    headers = {"Accept": "application/json",
               "User-Agent": "ontology-template-pins"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith(GITHUB):
        headers["Authorization"] = "Bearer " + token
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


# ---------------------------------------------------------------- read


def collect(root: Path) -> list[dict]:
    """Every pin, from the files the Pins section names. An action used
    in several workflows is one pin, with every place it is used."""
    import yaml

    pins: list[dict] = []
    actions: dict[tuple, dict] = {}
    for path in sorted((root / WORKFLOWS).glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        for number, line in enumerate(text.splitlines(), 1):
            match = USES.search(line)
            if not match:
                continue
            repo, sha, tag = match.groups()
            where = "%s/%s:%d" % (WORKFLOWS, path.name, number)
            pin = actions.setdefault((repo, sha, tag), {
                "kind": "action", "name": repo, "pinned": tag,
                "commit": sha, "where": []})
            pin["where"].append(where)
    pins.extend(actions.values())

    for number, line in enumerate(
            (root / REQUIREMENTS).read_text(encoding="utf-8").splitlines(),
            1):
        match = REQUIREMENT.match(line.strip())
        if match:
            pins.append({"kind": "python", "name": match.group(1),
                         "pinned": match.group(2),
                         "where": ["%s:%d" % (REQUIREMENTS, number)]})

    upstreams = yaml.safe_load(
        (root / UPSTREAMS).read_text(encoding="utf-8")) or {}
    for source in upstreams.get("sources") or []:
        urls = [source.get("url")] + [f.get("url") for f in
                                      source.get("files") or []]
        repos = {RAW.match(u).group(1) for u in urls if u and RAW.match(u)}
        pins.append({"kind": "upstream", "name": source["id"],
                     "pinned": source.get("release"),
                     "commit": source.get("commit"),
                     "repo": sorted(repos)[0] if len(repos) == 1 else None,
                     "where": [UPSTREAMS]})

    robot = (yaml.safe_load((root / REASONING).read_text(encoding="utf-8"))
             or {}).get("robot") or {}
    if robot:
        pins.append({"kind": "reasoner", "name": "robot",
                     "pinned": "v%s" % robot.get("version"),
                     "commit": robot.get("tag_commit"),
                     "repo": "ontodev/robot", "where": [REASONING]})
    return pins


# --------------------------------------------------------------- check


def tag_commit(repo: str, tag: str) -> str:
    return fetch_json("%s/repos/%s/commits/%s" % (GITHUB, repo, tag))["sha"]


def latest_release(repo: str) -> str:
    return fetch_json("%s/repos/%s/releases/latest"
                      % (GITHUB, repo))["tag_name"]


def check_tagged(pin: dict, repo: str | None) -> None:
    """An action, an upstream or the reasoner: its commit must be what
    its tag names, and the latest release is reported."""
    if not repo:
        pin["problems"].append("no single repository to check it against")
        return
    named = tag_commit(repo, pin["pinned"])
    if named != pin["commit"]:
        pin["problems"].append(
            "pinned commit %s is not what %s names upstream (%s)"
            % (pin["commit"][:12], pin["pinned"], named[:12]))
    pin["latest"] = latest_release(repo)


def check(pins: list[dict]) -> list[dict]:
    for pin in pins:
        pin.setdefault("problems", [])
        pin["latest"] = None
        pin["advisories"] = []
        try:
            if pin["kind"] == "action":
                check_tagged(pin, pin["name"])
            elif pin["kind"] == "python":
                pin["latest"] = fetch_json(PYPI % pin["name"])["info"][
                    "version"]
            else:
                check_tagged(pin, pin.get("repo"))
        except Exception as exc:  # urllib and json raise several types
            pin["problems"].append("not checked: %s" % exc)

    python = [p for p in pins if p["kind"] == "python"]
    if python:
        try:
            answer = fetch_json(OSV, {"queries": [
                {"package": {"name": p["name"], "ecosystem": "PyPI"},
                 "version": p["pinned"]} for p in python]})
            for pin, result in zip(python, answer["results"]):
                pin["advisories"] = sorted(v["id"] for v in
                                           result.get("vulns") or [])
                if pin["advisories"]:
                    pin["problems"].append(
                        "published advisories: "
                        + ", ".join(pin["advisories"]))
        except Exception as exc:
            for pin in python:
                pin["problems"].append("advisories not checked: %s" % exc)
    return pins


# -------------------------------------------------------------- report


def head(root: Path) -> str:
    """HEAD, and whether the files read differ from it: a report on a
    commit is only evidence about that commit if they do not."""
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root),
                            capture_output=True)
    if result.returncode:
        return "(not a git checkout)"
    commit = result.stdout.decode("ascii").strip()
    changed = subprocess.run(
        ["git", "status", "--porcelain", "--", WORKFLOWS, REQUIREMENTS,
         UPSTREAMS, REASONING], cwd=str(root), capture_output=True)
    if changed.stdout.strip():
        commit += " (with uncommitted changes to the pin files)"
    return commit


def status_of(pin: dict) -> str:
    if pin["problems"]:
        return "FAIL"
    if pin["latest"] and pin["latest"] != pin["pinned"]:
        return "newer: %s" % pin["latest"]
    return "current"


def report(pins: list[dict], commit: str, when: str) -> str:
    lines = ["Pins at %s, checked %s" % (commit, when), ""]
    width = max(len(p["name"]) for p in pins)
    for pin in pins:
        lines.append("  %-8s  %-*s  %-20s  %s" % (
            pin["kind"], width, pin["name"], pin["pinned"], status_of(pin)))
        lines.extend("            %s" % p for p in pin["problems"])
    failed = sum(1 for p in pins if p["problems"])
    newer = sum(1 for p in pins
                if not p["problems"] and status_of(p) != "current")
    lines += ["", "  %d pin(s): %d current, %d with a newer release, %d "
              "failed" % (len(pins), len(pins) - failed - newer, newer,
                          failed)]
    if newer:
        lines.append("  A newer release is reported, not failed: take it, "
                     "or keep the pin and say why (docs/DEVELOPMENT.md, "
                     "\"Pins\").")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--json", action="store_true",
                    help="print the result as JSON")
    args = ap.parse_args(argv)

    root = layout.repository_root()
    pins = check(collect(root))
    commit = head(root)
    when = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.json:
        print(json.dumps({"commit": commit, "checked": when, "pins": pins},
                         indent=2, sort_keys=True))
    else:
        sys.stdout.write(report(pins, commit, when))
    return 1 if any(p["problems"] for p in pins) else 0


if __name__ == "__main__":
    sys.exit(main())
