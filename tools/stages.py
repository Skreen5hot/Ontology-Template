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

THE REVIEW GATE (backlog item 12, template decisions 34 and 35)

A stage may name, in `review`, groups of review-candidate rules and the
roles that may answer each (Domain Expert, Proxy Domain Expert,
Ontologist: config/review.yaml). Such a stage is refused as done while

- a current candidate from one of its rules has no answer in
  config/review-register.yaml;
- an answer is by a role the group does not allow: an ontologist's
  answer does not pass a question for a domain expert;
- the person an answer names is not named in the charter in that role
  (docs/charter.md, "Who holds which gate": one line per role, such as
  "- Proxy domain expert: Jane Doe");
- the charter names no one in any of a group's roles;
- an answer deferred is past its review date;
- candidates imported from elsewhere were run on another corpus.

A candidate is a place to look, never a defect: nothing fails because one
exists. The gate checks that each has an answer from the right role on
the current corpus. It cannot check that the person is what the role
says; the charter says it, and the answer is signed.

It never reads what a standard says, and never judges whether a gate's
conditions were met, or whether an answer is right: those are for the
person who holds the gate. A standard that exists is evidence that one
was written, nothing more.

Exit codes: 0 no findings; 1 findings.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402

STATUSES = ("not-started", "in-progress", "done")
CHARTER = "docs/charter.md"
#: The charter's line for each review role: "- Domain expert: <names>".
ROLE_LINES = {"domain expert": "domain-expert",
              "proxy domain expert": "proxy-domain-expert",
              "ontologist": "ontologist"}
ROLE_LINE = re.compile(
    r"^\s*[-*]\s*(proxy domain experts?|domain experts?|ontologists?)\s*:"
    r"\s*(.*?)\s*$", re.I)
#: A charter line that names no one.
NOBODY = re.compile(r"^(none\b.*|)$", re.I)
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
        for problem in review_block_problems(stage.get("review")):
            found.append("%s: review %s" % (name, problem))
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


def review_block_problems(block) -> list[str]:
    """What is wrong with a stage's `review` block, if it has one."""
    if block is None:
        return []
    if not isinstance(block, list) or not block:
        return ["is not a list of {rules, roles} groups"]
    out = []
    for index, group in enumerate(block):
        if (not isinstance(group, dict) or not group.get("rules")
                or not group.get("roles")):
            out.append("group %d needs rules and roles" % (index + 1))
            continue
        unknown = sorted(set(group) - {"rules", "roles"})
        if unknown:
            out.append("group %d has unknown field(s): %s"
                       % (index + 1, ", ".join(unknown)))
    return out


def charter_roles(text: str) -> dict:
    """{role: [names]} from the charter's role lines. A line saying
    "none" names no one; a role with no line is absent."""
    out: dict = {}
    for line in text.splitlines():
        match = ROLE_LINE.match(line)
        if not match:
            continue
        label = match.group(1).lower().rstrip("s")
        role = ROLE_LINES[label]
        value = match.group(2)
        names = [] if NOBODY.match(value) else [
            n.strip() for n in value.split(";") if n.strip()]
        out.setdefault(role, []).extend(names)
    return out


def in_group(rule: str, group: dict) -> bool:
    return any(fnmatch.fnmatchcase(rule, pattern)
               for pattern in group.get("rules") or [])


def review_problems(stages: list[dict], candidates: list[dict],
                    entries: list[dict], roles: dict, older: dict,
                    today: datetime.date) -> list[str]:
    """The review gate, for each stage marked done that names one. Pure:
    the candidates, the register, the charter's roles and the imports run
    on another corpus are given."""
    import review

    found = []
    answers = {review.key(e): e for e in entries}
    for stage in stages:
        groups = stage.get("review")
        if stage.get("status") != "done" or not groups:
            continue
        name = stage.get("id")
        for group in groups:
            allowed = list(group["roles"])
            if not any(roles.get(r) for r in allowed):
                found.append("%s: is done, but the charter names no one as "
                             "%s, the role(s) that answer %s" % (
                                 name, " or ".join(allowed),
                                 ", ".join(group["rules"])))
        for record in candidates:
            group = next((g for g in groups if in_group(record["rule"], g)),
                         None)
            if group is None:
                continue
            what = "%s %s" % (record["rule"], " ".join(record["about"]))
            entry = answers.get(review.key(record))
            if entry is None:
                found.append("%s: is done, but candidate %s has no answer "
                             "in %s" % (name, what, review.REGISTER))
                continue
            kind = review.kind_of(entry)
            person = str(entry["classified_by"]).rsplit(" (", 1)[0]
            if kind not in group["roles"]:
                found.append("%s: candidate %s was answered as %s; this "
                             "stage needs %s" % (name, what, kind,
                                                 " or ".join(group["roles"])))
            elif person not in roles.get(kind, []):
                found.append("%s: candidate %s was answered by %s as %s, "
                             "whom the charter does not name in that role"
                             % (name, what, person, kind))
            if (entry["resolution"] == "deferred" and
                    datetime.date.fromisoformat(entry["review"]) < today):
                found.append("%s: candidate %s was deferred to %s, which "
                             "has passed" % (name, what, entry["review"]))
        for path, corpus in sorted(older.items()):
            found.append("%s: is done, but %s was run on another corpus "
                         "(%s); run it again, or remove it"
                         % (name, path, corpus[:12]))
    return found


def check(root: Path | None = None) -> tuple[list[dict], list[str]]:
    import yaml

    root = root or layout.repository_root()
    raw = yaml.safe_load(layout.path("config.stages").read_text(
        encoding="utf-8")) or {}
    skeleton_path = layout.path("docs.standards") / SKELETON
    skeleton = skeleton_path.read_bytes() if skeleton_path.is_file() else None
    components = {c.id for c in layout.components()}
    stages = stages_of(raw)
    found = problems_of(raw, root, components, skeleton)
    if any(s.get("status") == "done" and s.get("review") for s in stages):
        found.extend(gate(root, stages))
    return stages, found


def gate(root: Path, stages: list[dict]) -> list[str]:
    """The review gate's inputs, read from the repository, then the gate.
    Only run when a stage marked done names a review: generating the
    candidates reads the whole corpus."""
    import review

    candidates, digest = review.current(root)
    charter = root / CHARTER
    roles = charter_roles(charter.read_text(encoding="utf-8")
                          if charter.is_file() else "")
    return review_problems(stages, candidates, review.load(root), roles,
                           review.older(candidates, digest),
                           datetime.date.today())


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
