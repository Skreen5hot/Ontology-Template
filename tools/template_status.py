# SPDX-License-Identifier: MIT
"""Which template-owned files a project has changed, and which the template has.

    python tools/template_status.py                  # report divergence
    python tools/template_status.py --record         # template only: rewrite
                                                     # the manifest
    python tools/template_status.py --check          # exit 1 if the manifest
                                                     # is stale (template) --
                                                     # a project only reports
    python tools/template_status.py --against ../Ontology-Template
                                                     # what a newer template
                                                     # changed, and where that
                                                     # meets a local change

WHY THIS EXISTS

The repositories this template was cut from were each made by copying
the last one's tools. The Business Capability Ontology fixed a defect in
its copy of the vendoring tool -- triples attributed to the wrong
upstream's licence -- and the Application Requirement Ontology, which it
was copied from, still has it. Nothing in either repository could say
so, because neither knew what it had been copied from.

So the template records a digest of every file it owns (components
declared `template: owned` in the layout contract), and a project keeps
that record as it arrived. Comparing the record with the files says what
the project changed; comparing it with a newer template's record says
what the template changed since; a file in both lists is where a merge
needs a person.

This reports. It does not merge, and a project changing an owned file is
not an error -- it is information the next update needs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402
import project  # noqa: E402

FORMAT_VERSION = 1
GENERATOR = "tools/template_status.py"
MANIFEST = "config/template-manifest.json"


class Refused(SystemExit):
    """Raised rather than writing a record that would mislead."""


def candidate_files(root: Path) -> list[str]:
    """Tracked files plus untracked ones git would not ignore.

    Untracked included, because the manifest is recorded before the
    commit that adds a new tool; ignored excluded, because __pycache__
    under tests/ is not something the template ships.
    """
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=str(root), capture_output=True)
    if result.returncode:
        raise Refused("git ls-files failed: "
                      + result.stderr.decode("utf-8", "replace")[-300:])
    names = result.stdout.decode("utf-8").splitlines()
    return sorted({name for name in names
                   if name and (root / name).is_file()})


def owned_components() -> list:
    return [c for c in layout.components() if c.template == "owned"]


def owned_files(root: Path | None = None) -> list[str]:
    """Files whose owning component -- longest match -- is owned.

    By owning component rather than by path prefix, so a template-only
    file inside an owned directory (tests/test_init_project.py inside
    tests/) is not recorded as something every project should have.
    """
    root = root or layout.repository_root()
    if not owned_components():
        raise Refused(
            "no component is declared template: owned, so there is nothing "
            "to record and every comparison would report no divergence")
    out = []
    for name in candidate_files(root):
        owner = layout.owning_component(name)
        if owner is not None and owner.template == "owned":
            out.append(name)
    return out


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def measure(root: Path | None = None) -> dict:
    root = root or layout.repository_root()
    files = {name: sha256_of((root / name).read_bytes())
             for name in owned_files(root)}
    return {"files": files, "digest": digest_of(files)}


def digest_of(files: dict) -> str:
    rows = "\n".join("%s %s" % (name, files[name]) for name in sorted(files))
    return sha256_of(rows.encode("utf-8"))


def head_commit(root: Path) -> str:
    """The commit the record is made on.

    Not the commit that carries the record: that commit does not exist
    yet when the record is written, and its id depends on the record.
    So the manifest names its parent, and the template commit a project
    was made from is the first commit after `template_commit` whose
    manifest has this digest; at a release, the tag names it (T21).
    """
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root),
                            capture_output=True)
    if result.returncode:
        raise Refused("git rev-parse HEAD failed, so the record could not "
                      "name the commit it was made on: "
                      + result.stderr.decode("utf-8", "replace")[-300:])
    return result.stdout.decode("utf-8").strip()


def manifest_of(measured: dict, label: str, commit: str) -> dict:
    return {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "template_repository": project.repository(),
        "template_commit": commit,
        "label": label,
        "digest": measured["digest"],
        "files": measured["files"],
        "note": (
            "The digest of every template-owned file as the template "
            "shipped it. A project keeps this as it arrived: it is the "
            "record of what the project was made from, and "
            "tools/template_status.py compares the project's files, and "
            "a newer template's manifest, against it. template_commit is "
            "the template commit this record was made on; the commit "
            "that carries the record follows it, and a release tag names "
            "that commit."),
    }


def recorded(root: Path | None = None) -> dict:
    root = root or layout.repository_root()
    path = root / MANIFEST
    if not path.is_file():
        raise Refused(MANIFEST + " is missing. Without it nothing can say "
                      "what this repository was made from.")
    return json.loads(path.read_text(encoding="utf-8"))


def compare(was: dict, now: dict) -> dict:
    """Changed, removed and added, between two {path: sha256} maps."""
    return {
        "changed": sorted(p for p in set(was) & set(now)
                          if was[p] != now[p]),
        "removed": sorted(set(was) - set(now)),
        "added": sorted(set(now) - set(was)),
    }


def diverged(difference: dict) -> bool:
    return any(difference[key] for key in ("changed", "removed", "added"))


def against(other_root: Path) -> dict:
    """What a newer template changed since this project's record, and
    where that meets a change made here."""
    mine = recorded()["files"]
    theirs = recorded(other_root)["files"]
    upstream = compare(mine, theirs)
    local = compare(mine, measure()["files"])
    touched_here = set(local["changed"]) | set(local["removed"])
    touched_there = set(upstream["changed"]) | set(upstream["removed"])
    return {"template_changed": upstream, "changed_here": local,
            "both": sorted(touched_here & touched_there)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--record", action="store_true",
                    help="rewrite the manifest (the template only)")
    ap.add_argument("--label", default="unreleased",
                    help="with --record: the template version this is")
    ap.add_argument("--check", action="store_true",
                    help="in the template, exit 1 if the manifest is stale")
    ap.add_argument("--against", default=None, metavar="TEMPLATE_CHECKOUT")
    args = ap.parse_args(argv)

    root = layout.repository_root()
    now = measure(root)

    if args.record:
        if not project.is_template():
            raise Refused(
                "this is a project, not the template. Its manifest is the "
                "record of what it was made from, and rewriting it would "
                "make every local change look like the template's.")
        path = root / MANIFEST
        record = manifest_of(now, args.label, head_commit(root))
        path.write_bytes(json.dumps(record, indent=2,
                                    sort_keys=True).encode("utf-8") + b"\n")
        print("  wrote %s: %d owned file(s), digest %s"
              % (MANIFEST, len(now["files"]), now["digest"][:16]))
        return 0

    if args.against:
        report = against(Path(args.against).resolve())
        upstream = report["template_changed"]
        print("  the template changed %d, removed %d, added %d owned file(s) "
              "since this project's record"
              % (len(upstream["changed"]), len(upstream["removed"]),
                 len(upstream["added"])))
        for key in ("changed", "removed", "added"):
            for name in upstream[key]:
                print("    %-8s %s" % (key, name))
        if report["both"]:
            print("  changed both here and in the template -- merge by "
                  "hand:")
            for name in report["both"]:
                print("    %s" % name)
        return 0

    record = recorded(root)
    difference = compare(record["files"], now["files"])
    template = project.is_template()
    print("  %d owned file(s); recorded %s (%s), now %s"
          % (len(now["files"]), record["digest"][:16], record.get("label"),
             now["digest"][:16]))
    print("  made from %s, recorded on commit %s"
          % (record.get("template_repository"),
             record.get("template_commit") or "(not recorded)"))
    for key in ("changed", "removed", "added"):
        for name in difference[key]:
            print("    %-8s %s" % (key, name))
    if not diverged(difference):
        print("  every owned file is as the manifest records")
        return 0
    if template:
        print()
        print("  STALE: this is the template, and its manifest does not "
              "describe its own files. Run: python %s --record" % GENERATOR)
        return 1 if args.check else 0
    print()
    print("  this project has diverged from the template it was made from "
          "in the files above. That is allowed; it is what the next "
          "template update will have to merge.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
