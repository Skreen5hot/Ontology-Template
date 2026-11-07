# SPDX-License-Identifier: MIT
"""Decision propagation: what each decision says it changes, and whether
each of those files cites it.

    python tools/decisions.py          # check; exit 1 on a finding
    python tools/decisions.py --json   # the findings and every target

METHOD section 6 (P7, template decision 38): a decision taken in the
course of the work often changes documents downstream of it; say which,
and carry it into each by name, so that a decision nobody has carried is
visible rather than remembered. BCO's conceptual model decided two
foundational questions and its specification still owed them; the debt
was found by reading. This makes it a list.

A DECISION NAMES WHAT IT CHANGES

Each record (config/decisions.yaml, `records`: docs/decisions/*.md by
default, never the README) begins with a front matter block:

    ---                                   ---
    carries_into:                         carries_into: []
      - docs/charter.md                   carries_nothing: Records that
      - ontology/core.ttl                   the pin stays.
    ---                                   ---

A decision's identifier is its file name without .md
(2026-11-10-placement), which the record's name, YYYY-MM-DD-<slug>.md,
makes unique. A target is a file, by its repository path.

EACH OF THOSE CITES IT

A target carries a decision when its text contains the decision's
identifier exactly: not as part of a longer one (2026-11-10-placement-b
does not cite 2026-11-10-placement), in prose, a comment or an
annotation. A record is never its own target. A target that does not
carry it is owed, and says why: not yet created, created but not
tracked, or tracked without citing it.

What a finding here refuses, each naming the record or the file:

- a record whose name is not YYYY-MM-DD-<slug>.md;
- a record without the block, unless it is dated before `required_from`
  (a project adopting this sets the date; its older records are listed as
  not declaring, never refused);
- a block that cannot be read, has an unknown field, lists a target
  twice, has `carries_into: []` without `carries_nothing`, or both;
- a target that is not a repository path to a file: absolute, with a ..
  or a glob, a directory, or the record itself;
- a citation, in a tracked text file, written as a path to a record
  (decisions/2026-11-10-placement, with or without .md) that names no
  record;
- an `unscoped` entry in config/decisions.yaml that is malformed, names
  no owed target, or is stale.

What it reports and never refuses: each owed target, oldest decision
first. An owed target is the normal state between recording a decision
and carrying it.

WHERE THE DEBT IS HELD

- tools/stages.py refuses a stage marked done while a decision owes a
  target in its `where` components, or one assigned to it.
- tools/release.py refuses to build while a decision owes a target that
  no running stage's `where` holds, unless config/decisions.yaml's
  `unscoped` assigns it to a stage (`stage:`) or accounts for it
  (`reason:`).

It does not check that a decision is carried faithfully: a citation shows
that a file refers to the decision, not that it says what the decision
decided. That judgement is a person's. It does not find a file a decision
changes but does not list, and does not read where in a file the
citation sits.

Exit codes: 0 no findings; 1 findings.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402

CONFIG = "config/decisions.yaml"
NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$")
#: A character that may continue an identifier: one next to a match means
#: the match is part of a longer identifier, not a citation of this one.
EDGE = "A-Za-z0-9_-"
IDENTIFIER = r"\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*"
FIELDS = {"carries_into", "carries_nothing"}
UNSCOPED_FIELDS = {"decision", "target", "stage", "reason"}
#: The suffixes the citation scan reads: text a person writes.
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".ttl", ".tsv", ".csv", ".txt"}
WHY = {"missing": "not yet created", "untracked": "not tracked",
       "uncited": "does not cite it"}

DEFAULTS = {
    "records": ["docs/decisions/*.md"],
    "exclude": ["docs/decisions/README.md"],
    "required_from": None,
    "scan_exclude": ["docs/template/**", "communications/**"],
    "unscoped": [],
}


class Unreadable(SystemExit):
    """A file this reads cannot be read as what it should be."""


def configuration(root: Path) -> dict:
    import yaml

    path = root / CONFIG
    raw = {}
    if path.is_file():
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise Unreadable("%s cannot be read: %s" % (CONFIG, exc))
    if not isinstance(raw, dict):
        raise Unreadable("%s is not a mapping" % CONFIG)
    unknown = sorted(set(raw) - set(DEFAULTS) - {"version"})
    if unknown:
        raise Unreadable("%s has unknown field(s): %s"
                         % (CONFIG, ", ".join(unknown)))
    settings = dict(DEFAULTS)
    settings.update({k: v for k, v in raw.items() if k != "version"})
    start = settings["required_from"]
    if start is not None and not isinstance(start, datetime.date):
        try:
            settings["required_from"] = datetime.date.fromisoformat(
                str(start))
        except ValueError:
            raise Unreadable("%s: required_from %r is not a date "
                             "(YYYY-MM-DD)" % (CONFIG, start))
    return settings


def cites(text: str, identifier: str) -> bool:
    """Whether text cites this identifier exactly, not as part of another."""
    return re.search(r"(?<![%s])%s(?![%s])" % (EDGE, re.escape(identifier),
                                                EDGE), text) is not None


def front_matter(text: str):
    """(the block's mapping or None, a problem or None). A record without
    a block is (None, None)."""
    import yaml

    lines = text.split("\n")
    if not lines or lines[0].rstrip("\r") != "---":
        return None, None
    for end in range(1, len(lines)):
        if lines[end].rstrip("\r") == "---":
            break
    else:
        return None, "its front matter has no closing ---"
    try:
        block = yaml.safe_load("\n".join(lines[1:end]))
    except yaml.YAMLError as exc:
        return None, "its front matter cannot be read: %s" % exc
    if not isinstance(block, dict):
        return None, "its front matter is not a mapping"
    return block, None


def target_problem(target, record: str, root: Path) -> str | None:
    if not isinstance(target, str) or not target.strip():
        return "lists a target that is not a path: %r" % (target,)
    if (target.startswith(("/", "./")) or "\\" in target or ":" in target
            or ".." in target.split("/") or any(c in target for c in "*?[")):
        return ("lists %s, which is not a repository path to one file"
                % target)
    if target == record:
        return "lists itself; a record does not carry its own decision"
    if (root / target).is_dir():
        return "lists %s, a directory; a target is a file" % target
    return None


def records(root: Path, settings: dict) -> list[str]:
    out = set()
    for pattern in settings["records"]:
        for path in root.glob(pattern):
            name = path.relative_to(root).as_posix()
            if path.is_file() and not any(fnmatch.fnmatch(name, x)
                                          for x in settings["exclude"]):
                out.add(name)
    return sorted(out, key=lambda n: (Path(n).stem, n))


def tracked(root: Path) -> set[str]:
    result = subprocess.run(["git", "ls-files"], cwd=str(root),
                            capture_output=True, text=True)
    return set(result.stdout.split()) if result.returncode == 0 else set()


def declarations(root: Path, settings: dict, names: list[str],
                 known: set[str]) -> dict:
    """Each record's identifier and targets, each target's state; the
    records that predate required_from; and the problems."""
    problems, decided, predating = [], [], []
    seen: dict = {}
    for name in names:
        identifier = Path(name).stem
        match = NAME.match(identifier)
        if not match:
            problems.append("%s: is not named YYYY-MM-DD-<slug>.md, so it "
                            "has no identifier to cite" % name)
            continue
        if identifier in seen:
            problems.append("%s: has the identifier of %s"
                            % (name, seen[identifier]))
            continue
        seen[identifier] = name
        text = (root / name).read_text(encoding="utf-8", errors="replace")
        block, problem = front_matter(text)
        if problem:
            problems.append("%s: %s" % (name, problem))
            continue
        if block is None:
            start = settings["required_from"]
            if start is not None and datetime.date.fromisoformat(
                    match.group(1)) < start:
                predating.append(name)
            else:
                problems.append(
                    "%s: declares neither carries_into nor carries_nothing "
                    "in a front matter block" % name)
            continue
        unknown = sorted(set(block) - FIELDS)
        if unknown:
            problems.append("%s: its front matter has unknown field(s): %s"
                            % (name, ", ".join(map(str, unknown))))
        targets = block.get("carries_into")
        nothing = block.get("carries_nothing")
        if not isinstance(targets, list):
            problems.append("%s: carries_into is not a list of paths" % name)
            continue
        if not targets and not (isinstance(nothing, str) and nothing.strip()):
            problems.append("%s: carries_into is empty and carries_nothing "
                            "gives no reason" % name)
        if targets and nothing is not None:
            problems.append("%s: lists targets and says it carries nothing"
                            % name)
        rows = []
        for target in targets:
            problem = target_problem(target, name, root)
            if problem:
                problems.append("%s: %s" % (name, problem))
                continue
            if target in (r["target"] for r in rows):
                problems.append("%s: lists %s twice" % (name, target))
                continue
            path = root / target
            if not path.is_file():
                state = "missing"
            elif target not in known:
                state = "untracked"
            elif cites(path.read_text(encoding="utf-8", errors="replace"),
                       identifier):
                state = "carried"
            else:
                state = "uncited"
            rows.append({"target": target, "state": state})
        decided.append({"record": name, "decision": identifier,
                        "targets": rows})
    return {"decided": decided, "predating": predating,
            "problems": problems}


def unresolved(root: Path, settings: dict, known: set[str],
               identifiers: set[str]) -> list[str]:
    """Citations written as a path to a record, in tracked text files,
    that name no record. Only the path form is read: a bare dated name is
    as often an evaluation's or a message's file as a decision's."""
    folders = sorted({Path(p).parent.name for p in settings["records"]
                      if Path(p).parent.name})
    if not folders:
        return []
    pattern = re.compile(r"(?<![%s])(?:%s)/(%s)(?:\.md)?(?![%s])" % (
        EDGE, "|".join(map(re.escape, folders)), IDENTIFIER, EDGE))
    out = set()
    for name in sorted(known):
        if (Path(name).suffix not in TEXT_SUFFIXES
                or any(fnmatch.fnmatch(name, g)
                       for g in settings["scan_exclude"])):
            continue
        path = root / name
        if not path.is_file():
            continue
        for match in pattern.finditer(
                path.read_text(encoding="utf-8", errors="replace")):
            if match.group(1) not in identifiers:
                out.add("%s: cites %s, which names no decision record"
                        % (name, match.group(0)))
    return sorted(out)


# ----------------------------------------------------------- where held


def owed(decided: list[dict]) -> list[dict]:
    """Every owed target, oldest decision first."""
    return [dict(row, decision=d["decision"], record=d["record"])
            for d in decided for row in d["targets"]
            if row["state"] != "carried"]


def scopes(stages: list[dict]) -> dict:
    """{component id: [running stage ids whose where names it]}."""
    out: dict = {}
    for stage in stages:
        if stage.get("runs") is not True:
            continue
        for component in stage.get("where") or []:
            out.setdefault(component, []).append(stage.get("id"))
    return out


def placed(debts: list[dict], stages: list[dict], owner,
           unscoped: list[dict]) -> list[dict]:
    """Each owed target with the stages that hold it, and how: in a
    stage's scope, assigned to one, accounted for, or nowhere."""
    held = scopes(stages)
    entries = {(e.get("decision"), e.get("target")): e for e in unscoped
               if isinstance(e, dict)}
    out = []
    for debt in debts:
        stage_ids = held.get(owner(debt["target"]), [])
        entry = entries.get((debt["decision"], debt["target"]))
        if stage_ids:
            how = "scope"
        elif entry and entry.get("stage"):
            how, stage_ids = "assigned", [entry["stage"]]
        elif entry and entry.get("reason"):
            how = "accounted"
        else:
            how = "nowhere"
        out.append(dict(debt, stages=stage_ids, held=how))
    return out


def unscoped_problems(unscoped, decided: list[dict], rows: list[dict],
                      stages: list[dict]) -> list[str]:
    """What is wrong with config/decisions.yaml's unscoped entries."""
    if not isinstance(unscoped, list):
        return ["%s: unscoped is not a list" % CONFIG]
    running = {s.get("id") for s in stages if s.get("runs") is True}
    listed = {(d["decision"], t["target"]) for d in decided
              for t in d["targets"]}
    state = {(r["decision"], r["target"]): r for r in rows}
    out, seen = [], set()
    for index, entry in enumerate(unscoped):
        where = "%s: unscoped entry %d" % (CONFIG, index + 1)
        if not isinstance(entry, dict):
            out.append("%s is not a mapping" % where)
            continue
        unknown = sorted(set(entry) - UNSCOPED_FIELDS)
        if unknown:
            out.append("%s has unknown field(s): %s"
                       % (where, ", ".join(map(str, unknown))))
        pair = (entry.get("decision"), entry.get("target"))
        if not all(isinstance(x, str) and x for x in pair):
            out.append("%s needs a decision and a target" % where)
            continue
        if pair in seen:
            out.append("%s repeats %s %s" % ((where,) + pair))
            continue
        seen.add(pair)
        if bool(entry.get("stage")) == bool(entry.get("reason")):
            out.append("%s needs exactly one of stage (assigned to it) and "
                       "reason (accounted for)" % where)
            continue
        if entry.get("stage") and entry["stage"] not in running:
            out.append("%s assigns %s to %r, which is not a stage the "
                       "project runs" % (where, pair[1], entry["stage"]))
            continue
        if pair not in listed:
            out.append("%s: %s does not list %s" % ((where,) + pair))
        elif pair not in state:
            out.append("%s is stale: %s now carries %s; remove the entry"
                       % (where, pair[1], pair[0]))
        elif state[pair]["held"] == "scope":
            out.append("%s is stale: %s is now in the scope of %s; remove "
                       "the entry" % (where, pair[1],
                                      ", ".join(state[pair]["stages"])))
    return out


def stage_problems(stages: list[dict], rows: list[dict]) -> list[str]:
    """The stage gate: a stage marked done holds every target owed in its
    scope or assigned to it."""
    out = []
    for stage in stages:
        if stage.get("status") != "done":
            continue
        for row in rows:
            if stage.get("id") in row["stages"]:
                out.append("%s: is done, but %s owes %s (%s)%s" % (
                    stage["id"], row["decision"], row["target"],
                    WHY[row["state"]],
                    "; assigned to it in %s" % CONFIG
                    if row["held"] == "assigned" else ""))
    return out


def release_problems(rows: list[dict]) -> list[str]:
    """Owed targets no stage holds and nothing accounts for: refused at
    release (decision 38, safeguard 2)."""
    return ["%s owes %s (%s), which is in no stage's scope; assign it to a "
            "stage or account for it in %s" % (
                r["decision"], r["target"], WHY[r["state"]], CONFIG)
            for r in rows if r["held"] == "nowhere"]


# ----------------------------------------------------------------- main


def owner_of(relative_path: str):
    component = layout.owning_component(relative_path)
    return component.id if component else None


def stages_in(root: Path) -> list[dict]:
    import yaml

    path = root / "config/stages.yaml"
    raw = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}
           if path.is_file() else {})
    return [dict(s or {}) for kind in ("path", "lanes")
            for s in raw.get(kind) or []]


def check(root: Path | None = None, stages: list[dict] | None = None,
          owner=None) -> dict:
    root = root or layout.repository_root()
    settings = configuration(root)
    stages = stages if stages is not None else stages_in(root)
    owner = owner or owner_of
    known = tracked(root)
    names = records(root, settings)
    result = declarations(root, settings, names, known)
    identifiers = {Path(n).stem for n in names}
    problems = result["problems"] + unresolved(root, settings, known,
                                               identifiers)
    rows = placed(owed(result["decided"]), stages, owner,
                  settings["unscoped"] if isinstance(settings["unscoped"],
                                                     list) else [])
    problems += unscoped_problems(settings["unscoped"], result["decided"],
                                  rows, stages)
    targets = sum(len(d["targets"]) for d in result["decided"])
    return {"problems": problems, "owed": rows, "records": names,
            "decided": result["decided"], "predating": result["predating"],
            "targets": targets}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    result = check()
    if args.json:
        print(json.dumps(result, indent=1))
        return 1 if result["problems"] else 0
    for problem in result["problems"]:
        print("  finding  " + problem)
    for name in result["predating"]:
        print("  undeclared  %s (dated before required_from)" % name)
    labels = {"scope": "held by %s", "assigned": "assigned to %s",
              "accounted": "accounted for", "nowhere": "in no stage"}
    for row in result["owed"]:
        held = labels[row["held"]]
        if "%s" in held:
            held %= ", ".join(row["stages"])
        print("  owed     %s -> %s: %s; %s" % (
            row["decision"], row["target"], WHY[row["state"]], held))
    owing = len(result["owed"])
    print("\n  %d record(s), %d declaring, %d dated before required_from; "
          "%d target(s): %d carried, %d owed (%d in no stage)" % (
              len(result["records"]), len(result["decided"]),
              len(result["predating"]), result["targets"],
              result["targets"] - owing, owing,
              sum(1 for r in result["owed"] if r["held"] == "nowhere")))
    if not result["records"]:
        print("  No decision record was read. That is not evidence that "
              "decisions are carried: there were none to carry.")
    print("  Carried means the target cites the decision, not that it "
          "says what the decision decided; that is a person's judgement.")
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
