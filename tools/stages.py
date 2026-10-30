# SPDX-License-Identifier: MIT
"""Check the stages this project declares it runs (config/stages.yaml).

    python tools/stages.py          # findings, then where each stage stands
    python tools/stages.py --json   # the same, as one JSON object

The method is docs/process/METHOD.md: one decision path in strict order,
terminology lanes beside it that join the path at named gates, and a
standard for every stage before it starts. This is the part of it a tool
can hold:

- a stage that has started, or is done, names a standard, the standard
  exists, and it is not the blank skeleton copied unchanged;
- a path stage is done only when every earlier stage the project runs is;
- a lane is done only when every path stage it joins is;
- a stage the project does not run has not started;
- every status, layout component and joined stage is one that exists, and
  no stage is listed twice.

It never reads what a standard says, and never judges whether a gate's
conditions were met: those are for the person who holds the gate. A
standard that exists is evidence that one was written, nothing more.

Exit codes: 0 no findings; 1 findings.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402

STATUSES = ("not-started", "in-progress", "done")
STARTED = ("in-progress", "done")
FIELDS = ("id", "runs", "status", "standard", "where")
#: The blank skeleton in docs/standards/, which is not a standard until
#: it has been filled in.
SKELETON = "stage-standard.md"


def stages_of(raw: dict) -> list[dict]:
    """Every entry, path first, each tagged with the list it came from."""
    out = []
    for kind in ("path", "lanes"):
        for entry in raw.get(kind) or []:
            out.append(dict(entry or {}, kind=kind))
    return out


def problems_of(raw: dict, root: Path, components: set[str],
                skeleton: bytes | None) -> list[str]:
    """What is wrong with a stages file, as sentences naming the stage.
    Pure but for reading the standards it names, so a test can hand it a
    constructed file."""
    if raw.get("version") != 1:
        return ["version is %r, not 1" % raw.get("version")]
    if not raw.get("path"):
        return ["no path stages: the decision path is not optional"]
    found: list[str] = []
    stages = stages_of(raw)
    seen: set[str] = set()
    for stage in stages:
        name = stage.get("id") or "(no id)"
        missing = [f for f in FIELDS if f not in stage]
        if stage["kind"] == "lanes" and "joins" not in stage:
            missing.append("joins")
        if missing:
            found.append("%s: missing %s" % (name, ", ".join(missing)))
            continue
        if name in seen:
            found.append("%s: listed twice" % name)
        seen.add(name)
        if not isinstance(stage["runs"], bool):
            found.append("%s: runs is %r, not true or false"
                         % (name, stage["runs"]))
        if stage["status"] not in STATUSES:
            found.append("%s: status %r is not one of %s"
                         % (name, stage["status"], ", ".join(STATUSES)))
        for component in stage["where"] or []:
            if component not in components:
                found.append("%s: where names %r, which the layout "
                             "contract does not declare" % (name, component))
        if stage["runs"] is False and stage["status"] != "not-started":
            found.append("%s: is %s, but the project does not run it"
                         % (name, stage["status"]))
        standard = stage["standard"]
        if stage["status"] in STARTED and not standard:
            found.append("%s: is %s with no standard; a stage's standard "
                         "is written before it starts" % (name, stage["status"]))
        if standard:
            path = root / standard
            if not path.is_file():
                found.append("%s: standard %s does not exist"
                             % (name, standard))
            elif skeleton is not None and path.read_bytes() == skeleton:
                found.append("%s: standard %s is the blank skeleton, not "
                             "filled in" % (name, standard))

    path_stages = [s for s in stages if s["kind"] == "path" and "id" in s]
    status = {s.get("id"): s.get("status") for s in stages}
    runs = {s.get("id"): s.get("runs") for s in stages}
    for i, stage in enumerate(path_stages):
        if stage.get("status") != "done":
            continue
        for earlier in path_stages[:i]:
            if earlier.get("runs") and earlier.get("status") != "done":
                found.append("%s: is done, but %s, before it on the path, "
                             "is %s" % (stage["id"], earlier["id"],
                                        earlier.get("status")))
    path_ids = {s["id"] for s in path_stages}
    for lane in (s for s in stages if s["kind"] == "lanes"):
        for joined in lane.get("joins") or []:
            if joined not in path_ids:
                found.append("%s: joins %r, which is not a path stage"
                             % (lane.get("id"), joined))
            elif (lane.get("status") == "done" and runs[joined]
                  and status[joined] != "done"):
                found.append("%s: is done, but %s, which it joins, is %s"
                             % (lane["id"], joined, status[joined]))
    return found


def check(root: Path | None = None) -> tuple[list[dict], list[str]]:
    import yaml

    root = root or layout.repository_root()
    raw = yaml.safe_load(layout.path("config.stages").read_text(
        encoding="utf-8")) or {}
    skeleton_path = layout.path("docs.standards") / SKELETON
    skeleton = skeleton_path.read_bytes() if skeleton_path.is_file() else None
    components = {c.id for c in layout.components()}
    return stages_of(raw), problems_of(raw, root, components, skeleton)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    stages, found = check()
    if args.json:
        print(json.dumps({"findings": found, "stages": [
            {k: s.get(k) for k in ("id", "kind", "runs", "status", "standard")}
            for s in stages]}, indent=2))
        return 1 if found else 0
    for problem in found:
        print("  finding  " + problem)
    for stage in stages:
        print("  %-6s %-18s %-12s %s" % (
            "path" if stage["kind"] == "path" else "lane",
            stage.get("id"),
            stage.get("status") if stage.get("runs") else "not run",
            stage.get("standard") or "(no standard)"))
    print("\n  %d stage(s), %d finding(s)" % (len(stages), len(found)))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
