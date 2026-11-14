# SPDX-License-Identifier: MIT
"""Upgrade a project to this template release: plan, take what the
project never changed, and adopt the release's record.

Run from the checkout of the release a project moves to, against the
project, so that a project made from any earlier release runs it without
first changing itself to get it (P-A2, template decision 45, safeguard 1):

    python ../Ontology-Template/tools/upgrade.py --project .            # plan
    python ../Ontology-Template/tools/upgrade.py --project . --out DIR  # and
                                    # write merge bases into DIR
    python ../Ontology-Template/tools/upgrade.py --project . --take
    python ../Ontology-Template/tools/upgrade.py --project . --adopt \\
        [--retain PATH ...]

WHAT THE PLAN SAYS

Every template-owned and template-seeded file, compared three ways: as
the project received it (its record's base), as the project has it, and
as this release ships it -- seeded files on both template sides through
init's own rewrite with the project's values, so an unchanged shape
matches exactly. Each falls in one class:

  take             the release changed it, the project did not
  merge            both changed it, differently: a person merges, with
                   the base and the release's version written by --out
                   for `git merge-file`. Nothing merges automatically
  already taken    the project has the release's bytes
  added            new in the release, nothing in the project's way
  collision        new in the release, and a file is already at its path
  removed          removed in the release, unchanged here: a person
                   removes it
  removed, changed here
                   removed in the release, changed here: a person decides
  deleted here     the release changed it, and the project removed it
  kept             changed here only
  pins             config/upstream-sources.yaml changed in the release:
                   a BFO or CCO pin is the ontology's dependency, and moves
                   only by explicit acceptance (safeguard 2)

and beside them: the layout entries the release adds, changes or removes
(config/repository-layout.yaml is the project's, and is never written
here); the skeletons the project's README.md, CLAUDE.md, docs/HANDOFF.md
and CITATION.cff were rendered from, where the release changed them, as
diffs; the generators to run after taking; and the release notes of
every release since the project's, read from this checkout's ROADMAP.

A comparison that cannot be made -- the project's base commit is not in
this checkout's history -- is reported as not made, never as a file to
take.

--take copies the take and added files, and nothing else. It refuses to
run on a project with uncommitted changes, so a mistake is one checkout
away; on a checkout that is not the release its manifest records; and,
without --allow-unreleased, on a checkout whose manifest is not a
release. Before each write it reads the file again, and writes only if
it is still the base (take) or still absent (added), never through a
symbolic link, and never from one (safeguard 4). With --accept-pins it
also takes config/upstream-sources.yaml, if the project never changed it;
the extracts are then rebuilt by the project.

--adopt writes the project's manifest as this release's record. It keeps
the original init's block (`initialized`) and the first record the
project was made from (`made_from`) as they were, adds `adopted`: the
release's seeded files through init's rewrite, the values used, the
label and the exact commit; and appends to `upgrades` the move from one
record to the other with what remains (safeguard 3):

  retained     files that differ from the release because the project
               keeps its own version, each named with --retain; and the
               upstream pins, when not accepted
  unresolved   files that differ and were not named, files the release
               removed that are still here, layout entries the release
               adds that the contract does not declare
  review       rendered files whose skeleton changed, for a person

It refuses a checkout whose release is not newer than the project's
record, and a project whose own layout check fails. It never edits a
file but the manifest.

It is never an ontology migration: modules, vocabulary, research,
decisions and communications are the project's, and no class touches
them.

Exit codes: 0 done (a plan with work in it is still 0); 1 refused;
2 a comparison could not be made.
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402
import project  # noqa: E402
import template_status as status  # noqa: E402

UPSTREAMS = status.UPSTREAMS
CONTRACT = "config/repository-layout.yaml"
ROADMAP = "docs/template/ROADMAP.md"
SKELETONS = "docs/template/skeletons"
#: Each skeleton, and the file init renders from it in a project.
RENDERED = {"README.md": "README.md", "CLAUDE.md": "CLAUDE.md",
            "HANDOFF.md": "docs/HANDOFF.md", "CITATION.cff": "CITATION.cff"}
VERSION = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
LAYOUT_FIELDS = ("path", "role", "template", "generator")
WRITES = ("take", "added")
NOT_COMPARED = 2


class Refused(SystemExit):
    """Raised rather than writing something that would mislead or harm."""


# --------------------------------------------------------------- reading


def version(label) -> tuple | None:
    match = VERSION.match(str(label or ""))
    return tuple(int(g) for g in match.groups()) if match else None


def values_of(root: Path) -> dict:
    raw = status.yaml_of(status.read_file(root, status.PROJECT))
    return {key: raw.get(key) for key in project.IDENTITY}


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(root), capture_output=True)


def contract_of(data: bytes | None) -> dict:
    """{component id: its entry}, from a layout contract's bytes."""
    raw = status.yaml_of(data)
    return {str(c.get("id")): c for c in raw.get("components") or []
            if isinstance(c, dict) and c.get("id")}


def sha(data: bytes | None) -> str | None:
    return status.sha256_of(data) if data is not None else None


def unsafe(root: Path, relative: str) -> str | None:
    """Why writing this path would be unsafe, or None: outside the root,
    or through a symbolic link at the file or any directory above it."""
    if relative.startswith("/") or ".." in Path(relative).parts:
        return "is not a path inside the project"
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            return "goes through the symbolic link %s" % \
                current.relative_to(root).as_posix()
    return None


# ----------------------------------------------------------------- the plan


class Upgrade:
    """The comparison between a project and this release, computed once."""

    def __init__(self, project_root: Path, template_root: Path | None = None):
        self.project = project_root.resolve()
        self.template = (template_root or layout.repository_root()).resolve()
        if self.project == self.template:
            raise Refused("--project names this checkout; run it from the "
                          "release's checkout against the project")
        self.record = status.recorded(self.project)
        self.release = status.recorded(self.template)
        self.mine = values_of(self.project)
        self.theirs_values = values_of(self.template)
        commit = git(self.template, "rev-parse", "HEAD")
        self.head = commit.stdout.decode().strip() if not commit.returncode \
            else None
        self.base, self.why_no_base = status.base_commit(self.template,
                                                         self.record)
        self.base_values = (values_of_at(self.template, self.base)
                            if self.base else {})
        self.not_compared: list[str] = []
        if self.base is None:
            self.not_compared.append(
                "%s: the skeletons, the layout entries the release removed "
                "and the merge bases need the base commit, and are not "
                "compared; the files are, from the project's record. "
                "--take and --adopt refuse until the whole plan is known"
                % self.why_no_base)
        self.rows = self.classify()

    # -- the three sides of each file

    def base_bytes(self, name: str, seeded: bool) -> bytes | None:
        if self.base is None:
            return None
        data = status.git_bytes(self.template, "show",
                                "%s:%s" % (self.base, name))
        if data is None or not seeded:
            return data
        return status.as_received(name, data, self.base_values, self.mine)

    def theirs_bytes(self, name: str, seeded: bool) -> bytes | None:
        data = status.read_file(self.template, name)
        if data is None or not seeded:
            return data
        return status.as_received(name, data, self.theirs_values, self.mine)

    def base_digests(self) -> tuple[dict, dict | None]:
        """(owned {name: digest}, seeded {name: digest} or None): the
        project's record, in the project's form."""
        owned = dict(self.record.get("files") or {})
        block = self.record.get("adopted") or self.record.get("initialized")
        if block and block.get("seeded") is not None:
            return owned, dict(block["seeded"])
        if self.base is None:
            return owned, None
        names = set(self.record.get("seeded") or {}) or set(
            (self.release.get("seeded") or {}))
        seeded = {}
        for name in names:
            data = self.base_bytes(name, True)
            if data is not None:
                seeded[name] = sha(data)
        return owned, seeded

    def classify(self) -> list[dict]:
        owned_base, seeded_base = self.base_digests()
        release_owned = self.release.get("files") or {}
        release_seeded = self.release.get("seeded") or {}
        rows = []
        if seeded_base is None:
            self.not_compared.append(
                "seeded files: the project's record holds no seeded base "
                "and its base commit is not in this checkout")
            seeded_base = {}
            seeded_names = set()
        else:
            seeded_names = set(seeded_base) | set(release_seeded)
        owned_names = (set(owned_base) | set(release_owned)) - seeded_names
        for name in sorted(owned_names | seeded_names):
            seeded = name in seeded_names
            base = (seeded_base if seeded else owned_base).get(name)
            in_release = name in (release_seeded if seeded else release_owned)
            theirs = self.theirs_bytes(name, seeded) if in_release else None
            here = status.read_file(self.project, name)
            row = {"path": name, "kind": "seeded" if seeded else "owned",
                   "class": classify(base, sha(theirs), sha(here),
                                     in_release)}
            if name == UPSTREAMS and row["class"] in ("take", "merge"):
                row["changed_here"] = row["class"] == "merge"
                row["class"] = "pins"
                row["pins"] = status.dependency_changes(
                    here, status.read_file(self.template, name))
            if row["class"] is not None:
                rows.append(row)
        return rows

    def by_class(self, name: str) -> list[dict]:
        return [r for r in self.rows if r["class"] == name]

    # -- beside the files

    def layout_changes(self) -> dict:
        here = contract_of(status.read_file(self.project, CONTRACT))
        release = {k: v for k, v in contract_of(
            status.read_file(self.template, CONTRACT)).items()
            if v.get("template") != "only"}
        base = (contract_of(status.git_bytes(
            self.template, "show", "%s:%s" % (self.base, CONTRACT)))
            if self.base else None)
        module = "ontology/%s.ttl" % status.yaml_of(status.read_file(
            self.project, status.PROJECT)).get("id")
        out = {"added": [], "changed": [], "removed": []}
        everything = contract_of(status.read_file(self.template, CONTRACT))
        for ident, entry in sorted(release.items()):
            entry = dict(entry)
            if ident == "ontology.main":
                entry["path"] = module
            if ident not in here:
                out["added"].append({"id": ident, "entry": entry,
                                     "state": self.state_of(entry,
                                                            everything)})
                continue
            differs = [f for f in LAYOUT_FIELDS
                       if here[ident].get(f) != entry.get(f)]
            if differs:
                out["changed"].append({"id": ident, "fields": differs,
                                       "here": {f: here[ident].get(f)
                                                for f in differs},
                                       "release": {f: entry.get(f)
                                                   for f in differs}})
        if base is not None:
            for ident in sorted(set(base) - set(release)):
                if ident in here and base[ident].get("template") != "only":
                    out["removed"].append({"id": ident})
        return out

    def state_of(self, entry: dict, contract: dict) -> str:
        """What a person does for a layout entry the release adds, once its
        declaration is in: nothing if its file is here; else take it (an
        owned or seeded file --take writes), run the generator that writes
        it, or copy the release's starting file, which is the project's
        from then on."""
        path = str(entry.get("path") or "")
        if path and (self.project / path).exists():
            return "present"
        if entry.get("template") in ("owned", "seeded"):
            return "taken by --take"
        tool = contract.get(str(entry.get("generator")))
        if tool:
            return "generated by %s" % tool.get("path")
        if path and (self.template / path).exists():
            return ("absent: copy it from the release (%s); it is the "
                    "project's from then on" % path)
        return "absent: the release has no file there either"

    def skeleton_changes(self) -> list[dict]:
        if self.base is None:
            return []
        out = []
        for skeleton, target in RENDERED.items():
            name = "%s/%s" % (SKELETONS, skeleton)
            before = status.git_bytes(self.template, "show",
                                      "%s:%s" % (self.base, name))
            after = status.read_file(self.template, name)
            if before == after or after is None:
                continue
            diff = "".join(difflib.unified_diff(
                (before or b"").decode("utf-8").splitlines(True),
                after.decode("utf-8").splitlines(True),
                fromfile="%s (%s)" % (name, self.base[:12]),
                tofile="%s (this release)" % name))
            out.append({"skeleton": name, "rendered": target, "diff": diff})
        return out

    def generators(self) -> list[str]:
        """What init runs to regenerate every generated file, the same
        commands, in the same order. The vendoring rebuild needs the
        network, and is needed when the pins, the vendoring tool or its
        outputs changed: a release adding an output (the hierarchies in
        v0.4.0) needs it with the pins unmoved."""
        import init_project

        return [" ".join(command) for command in init_project.GENERATORS]

    def notes(self) -> list[dict]:
        """Each release's "What changes for a project" notes, after the
        project's and up to this one."""
        text = (status.read_file(self.template, ROADMAP) or b"").decode(
            "utf-8")
        start = version(self.record.get("label"))
        end = version(self.release.get("label"))
        out = []
        for match in re.finditer(r"^### Release (v\d+\.\d+\.\d+)[^\n]*\n"
                                 r"(.*?)(?=^### |\Z)", text, re.S | re.M):
            number = version(match.group(1))
            if start and number <= start:
                continue
            if end and number > end:
                continue
            body = match.group(2)
            found = re.search(r"^\*\*What changes for a project.*?(?=^\| |"
                              r"\Z)", body, re.S | re.M)
            out.append({"release": match.group(1),
                        "notes": (found.group(0) if found
                                  else body.split("\n\n")[0]).strip()})
        return out

    def plan(self) -> dict:
        return {"project": str(self.project), "template": str(self.template),
                "from": {"label": self.record.get("label"),
                         "template_commit": self.record.get(
                             "template_commit"), "base": self.base},
                "to": {"label": self.release.get("label"),
                       "template_commit": self.release.get(
                           "template_commit"), "commit": self.head},
                "files": self.rows, "layout": self.layout_changes(),
                "skeletons": self.skeleton_changes(),
                "generators": self.generators(), "notes": self.notes(),
                "not_compared": self.not_compared}

    # -- writing

    def merge_bases(self, out: Path) -> list[str]:
        """For each file both sides changed, its base and the release's
        version, for `git merge-file <project file> <.base> <.release>`."""
        if out.exists() and any(out.iterdir()):
            raise Refused("%s exists and is not empty" % out)
        written = []
        for row in self.by_class("merge") + self.by_class("pins"):
            seeded = row["kind"] == "seeded"
            for suffix, data in (
                    ("base", self.base_bytes(row["path"], seeded)),
                    ("release", self.theirs_bytes(row["path"], seeded))):
                if data is None:
                    continue
                target = out / ("%s.%s" % (row["path"], suffix))
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                written.append(target.as_posix())
        return written

    def ready(self, allow_unreleased: bool) -> None:
        """What --take and --adopt both require of the checkout."""
        if self.base is None:
            raise Refused("cannot compare: %s" % self.why_no_base)
        if version(self.release.get("label")) is None and \
                not allow_unreleased:
            raise Refused("this checkout's manifest is %r, not a release; "
                          "check out a release tag, or pass "
                          "--allow-unreleased" % self.release.get("label"))
        clean = git(self.template, "status", "--porcelain")
        if clean.returncode or clean.stdout.strip():
            raise Refused("this checkout has uncommitted changes, so no "
                          "commit carries the record it would adopt; check "
                          "out the release cleanly")
        measured = status.measure(self.template)
        if measured["digest"] != self.release.get("digest") or \
                measured["seeded_digest"] != self.release.get(
                    "seeded_digest"):
            raise Refused("this checkout's files are not the release its "
                          "manifest records; it has local changes")

    def take(self, accept_pins: bool = False,
             allow_unreleased: bool = False) -> list[str]:
        self.ready(allow_unreleased)
        dirty = git(self.project, "status", "--porcelain")
        if dirty.returncode or dirty.stdout.strip():
            raise Refused("the project has uncommitted changes; commit or "
                          "stash them first, so the upgrade is one diff")
        _owned, seeded_base = self.base_digests()
        owned_base = self.record.get("files") or {}
        written = []
        for row in self.rows:
            if row["class"] == "pins":
                if not accept_pins:
                    continue
                if row["changed_here"]:
                    row["skipped"] = ("the project changed its pins too; "
                                      "merge them by hand")
                    continue
            elif row["class"] not in WRITES:
                continue
            name, seeded = row["path"], row["kind"] == "seeded"
            why = unsafe(self.project, name)
            source = self.template / name
            if why is None and source.is_symlink():
                why = "is a symbolic link in the release"
            if why:
                row["skipped"] = why
                continue
            here = status.read_file(self.project, name)
            target = self.project / name
            if row["class"] == "added":
                if target.exists() or target.is_symlink():
                    row["skipped"] = "a file appeared at its path"
                    continue
            else:
                base = (seeded_base or {}).get(name) if seeded \
                    else owned_base.get(name)
                if sha(here) != base:
                    row["skipped"] = "it changed since the plan was made"
                    continue
            data = self.theirs_bytes(name, seeded)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            written.append(name)
        return written

    def adopt(self, retain: list[str], allow_unreleased: bool = False,
              today: datetime.date | None = None) -> dict:
        self.ready(allow_unreleased)
        here, there = version(self.record.get("label")), version(
            self.release.get("label"))
        if here and there and there <= here:
            raise Refused("this checkout is %s, not newer than the "
                          "project's record, %s"
                          % (self.release.get("label"),
                             self.record.get("label")))
        check = subprocess.run([sys.executable, "tools/layout.py"],
                               cwd=str(self.project), capture_output=True)
        if check.returncode:
            raise Refused("the project's layout check fails, so the record "
                          "would describe files its contract does not "
                          "declare:\n" + check.stdout.decode(
                              "utf-8", "replace")[-1500:])
        missing = undeclared(self.project)
        if missing:
            raise Refused("%d tracked file(s) belong to no component of the "
                          "project's %s, so the record would describe files "
                          "its contract does not declare: %s; the plan lists "
                          "the entries the release adds"
                          % (len(missing), CONTRACT, ", ".join(missing[:8])))
        unknown = sorted(set(retain) - {r["path"] for r in self.rows})
        if unknown:
            raise Refused("--retain names %s, which the plan does not list"
                          % ", ".join(unknown))
        retained, unresolved, review = [], [], []
        release_owned = self.release.get("files") or {}
        release_seeded = self.release.get("seeded") or {}
        adopted_seeded = {}
        for name in sorted(release_seeded):
            data = self.theirs_bytes(name, True)
            adopted_seeded[name] = sha(data)
        for name in sorted(set(release_owned) | set(release_seeded)):
            expected = adopted_seeded.get(name) or release_owned.get(name)
            if sha(status.read_file(self.project, name)) == expected:
                continue
            if name == UPSTREAMS:
                retained.append({"path": name, "why": "upstream pins not "
                                 "accepted: BFO and CCO stay as the "
                                 "project pins them"})
            elif name in retain:
                retained.append({"path": name, "why": "kept on purpose "
                                 "(--retain)"})
            else:
                unresolved.append({"path": name, "why": "differs from the "
                                   "release, and --retain does not name it"})
        for row in self.rows:
            if row["class"] in ("removed", "removed, changed here") and \
                    (self.project / row["path"]).exists():
                unresolved.append({"path": row["path"], "why": "removed in "
                                   "the release, still here"})
        for entry in self.layout_changes()["added"]:
            unresolved.append({"path": CONTRACT, "why": "the release's "
                               "layout entry %s is not declared"
                               % entry["id"]})
        for change in self.skeleton_changes():
            review.append({"path": change["rendered"], "why": "rendered "
                           "from %s, which the release changed"
                           % change["skeleton"]})
        record = dict(self.release)
        record.pop("initialized", None)
        if "initialized" in self.record:
            record["initialized"] = self.record["initialized"]
        record["made_from"] = self.record.get("made_from") or {
            "label": self.record.get("label"),
            "template_commit": self.record.get("template_commit"),
            "digest": self.record.get("digest")}
        record["adopted"] = {"label": self.release.get("label"),
                             "template_commit": self.release.get(
                                 "template_commit"),
                             "commit": self.head, "values": self.mine,
                             "seeded": adopted_seeded}
        entry = {"date": (today or datetime.date.today()).isoformat(),
                 "from": {"label": self.record.get("label"),
                          "template_commit": self.record.get(
                              "template_commit"),
                          "digest": self.record.get("digest")},
                 "to": {"label": self.release.get("label"),
                        "template_commit": self.release.get(
                            "template_commit"),
                        "commit": self.head,
                        "digest": self.release.get("digest")},
                 "retained": retained, "unresolved": unresolved,
                 "review": review}
        record["upgrades"] = list(self.record.get("upgrades") or []) + [entry]
        status.write_manifest(self.project, record)
        return entry


def undeclared(root: Path) -> list[str]:
    """Tracked files no component of the project's contract owns: the
    rule tests/test_repository_layout.py holds, read from the project's
    own contract, so it works on a project from any release."""
    paths = [str(c.get("path")).rstrip("/") for c in contract_of(
        status.read_file(root, CONTRACT)).values() if c.get("path")]
    listed = git(root, "ls-files")
    names = listed.stdout.decode("utf-8").splitlines() \
        if not listed.returncode else []
    return [name for name in names
            if not any(name == p or name.startswith(p + "/") for p in paths)]


def values_of_at(template: Path, commit: str) -> dict:
    raw = status.yaml_of(status.git_bytes(template, "show",
                                          "%s:%s" % (commit, status.PROJECT)))
    return {key: raw.get(key) for key in project.IDENTITY}


def classify(base, theirs, here, in_release: bool) -> str | None:
    """One file's class (the module docstring), from its three digests.
    None when there is nothing to say."""
    if not in_release:
        if base is None:
            return None
        if here is None:
            return None
        return "removed" if here == base else "removed, changed here"
    if base is None:
        if here is None:
            return "added"
        return "already taken" if here == theirs else "collision"
    if base == theirs:
        return None if here == base else (
            "deleted here" if here is None else "kept")
    if here == theirs:
        return "already taken"
    if here == base:
        return "take"
    if here is None:
        return "deleted here"
    return "merge"


# ----------------------------------------------------------------- main


ORDER = ("take", "added", "pins", "merge", "collision", "deleted here",
         "removed", "removed, changed here", "kept", "already taken")


def print_plan(plan: dict) -> None:
    print("  from %s (%s) to %s (%s)" % (
        plan["from"]["label"], (plan["from"]["base"] or "?")[:12],
        plan["to"]["label"], (plan["to"]["commit"] or "?")[:12]))
    for reason in plan["not_compared"]:
        print("  NOT COMPARED  %s" % reason)
    for name in ORDER:
        rows = [r for r in plan["files"] if r["class"] == name]
        if rows:
            print("\n  %s (%d)" % (name, len(rows)))
            for row in rows:
                print("    %s%s" % (row["path"], "  [seeded]"
                                    if row["kind"] == "seeded" else ""))
                for pin in row.get("pins") or []:
                    print("      %s: here %s, release %s" % (
                        pin["source"], pin["here"], pin["template"]))
    changes = plan["layout"]
    if any(changes.values()):
        print("\n  layout entries (config/repository-layout.yaml is yours; "
              "nothing here writes it)")
        for item in changes["added"]:
            print("    add      %s  (%s)" % (item["id"], item["state"]))
            for field in LAYOUT_FIELDS + ("description",):
                if item["entry"].get(field) is not None:
                    print("               %s: %s" % (
                        field, " ".join(str(item["entry"][field]).split())))
        for item in changes["changed"]:
            print("    changed  %s: %s" % (item["id"], ", ".join(
                "%s %r -> %r" % (f, item["here"][f], item["release"][f])
                for f in item["fields"])))
        for item in changes["removed"]:
            print("    removed  %s (the release no longer declares it)"
                  % item["id"])
    for change in plan["skeletons"]:
        print("\n  skeleton changed: %s, from which %s was rendered; carry "
              "what you want by hand\n" % (change["skeleton"],
                                           change["rendered"]))
        print("\n".join("    " + line
                        for line in change["diff"].splitlines()))
    if plan["generators"]:
        print("\n  after taking, regenerate: " + ", ".join(
            "python " + g for g in plan["generators"]))
    if plan["notes"] and version(plan["from"]["label"]) is None:
        print("\n  The project's record is %r, not a release, so the notes "
              "of every release up to this one follow." % plan["from"]["label"])
    for note in plan["notes"]:
        print("\n  release notes, %s\n" % note["release"])
        print("\n".join("    " + line for line in note["notes"].splitlines()))
    print("\n  Nothing merges automatically, and nothing here touches the "
          "ontology. --take copies only the take and added files.")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--project", type=Path, required=True)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", type=Path,
                    help="write the base and the release's version of each "
                         "file to merge into this directory")
    action = ap.add_mutually_exclusive_group()
    action.add_argument("--take", action="store_true")
    action.add_argument("--adopt", action="store_true")
    ap.add_argument("--accept-pins", action="store_true",
                    help="with --take: also take the release's upstream "
                         "pins, if the project never changed them")
    ap.add_argument("--retain", action="append", default=[],
                    metavar="PATH", help="with --adopt: a file the project "
                                         "keeps its own version of")
    ap.add_argument("--allow-unreleased", action="store_true")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        upgrade = Upgrade(args.project)
        if args.take:
            written = upgrade.take(args.accept_pins, args.allow_unreleased)
            for name in written:
                print("  took     %s" % name)
            for row in upgrade.rows:
                if row.get("skipped"):
                    print("  skipped  %s: %s" % (row["path"], row["skipped"]))
            print("\n  %d file(s) taken. Merge, declare the layout entries "
                  "and regenerate as the plan says, then --adopt."
                  % len(written))
            return 0
        if args.adopt:
            entry = upgrade.adopt(args.retain, args.allow_unreleased)
            print("  adopted %s at %s" % (entry["to"]["label"],
                                          (entry["to"]["commit"] or "")[:12]))
            for key in ("retained", "unresolved", "review"):
                for item in entry[key]:
                    print("  %-10s %s: %s" % (key, item["path"], item["why"]))
            return 0
        plan = upgrade.plan()
        if args.out:
            for name in upgrade.merge_bases(args.out):
                print("  wrote %s" % name)
        if args.json:
            print(json.dumps(plan, indent=1, default=str))
        else:
            print_plan(plan)
        return NOT_COMPARED if plan["not_compared"] else 0
    except Refused as exc:
        print("  refused: %s" % exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
