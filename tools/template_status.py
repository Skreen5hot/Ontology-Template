# SPDX-License-Identifier: MIT
"""Which template files a project has changed, and which the template has.

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

SEEDED FILES (P-A3, template decision 32)

The shapes, their fixtures, and the defaults in config -- annotation
profile, naming, reasoning, the upstream pins -- are `template: seeded`:
the template keeps improving them, and a project is expected to change
them. Until v0.3.0 they were not compared at all, so a project made from
v0.1.0 heard nothing from --against about v0.2.0's new checks.

They cannot be compared as bytes: init rewrites the namespace and prefix
in every shape and fixture, because SPARQL in a shape cannot read the
project file. So the template's copy is put through init's own rewrite
(project.rewrite_turtle) with the project's values, and the result is
compared with the project's file; an unchanged shape then matches
exactly. YAML is not rewritten by init, and is compared as bytes.

The base is the template's file as the project received it. init records
the digest of each seeded file as it left it, in the manifest's
`initialized` block, so the plain report works offline. A project made
before v0.3.0 has no such block; --against then finds the template
commit it was made from in the checkout's history, and takes the files
from there. A comparison that cannot be made is reported as not made,
and --against exits 2 -- never as unchanged.

A change to the upstream pins is reported as a dependency change for a
person to review, with both sides' releases. Nothing here upgrades
anything: the project's pin holds until the project adopts another.

This reports. It does not merge, and a project changing a template file
is not an error -- it is information the next update needs.
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

FORMAT_VERSION = 2
GENERATOR = "tools/template_status.py"
MANIFEST = "config/template-manifest.json"
UPSTREAMS = "config/upstream-sources.yaml"
NOT_COMPARED = 2


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


def files_of(kind: str, root: Path | None = None) -> list[str]:
    """Files whose owning component -- longest match -- is `kind`.

    By owning component rather than by path prefix, so a template-only
    file inside an owned directory (tests/test_init_project.py inside
    tests/) is not recorded as something every project should have.
    """
    root = root or layout.repository_root()
    out = []
    for name in candidate_files(root):
        owner = layout.owning_component(name)
        if owner is not None and owner.template == kind:
            out.append(name)
    return out


def owned_files(root: Path | None = None) -> list[str]:
    if not owned_components():
        raise Refused(
            "no component is declared template: owned, so there is nothing "
            "to record and every comparison would report no divergence")
    return files_of("owned", root)


def seeded_files(root: Path | None = None) -> list[str]:
    return files_of("seeded", root)


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digests(root: Path, names: list[str]) -> dict:
    return {name: sha256_of((root / name).read_bytes()) for name in names}


def measure(root: Path | None = None) -> dict:
    root = root or layout.repository_root()
    files = digests(root, owned_files(root))
    seeded = digests(root, seeded_files(root))
    return {"files": files, "digest": digest_of(files),
            "seeded": seeded, "seeded_digest": digest_of(seeded)}


def digest_of(files: dict) -> str:
    rows = "\n".join("%s %s" % (name, files[name]) for name in sorted(files))
    return sha256_of(rows.encode("utf-8"))


def identity() -> dict:
    """The values init rewrites Turtle with, as this repository has them."""
    values = project.load()
    return {key: values[key] for key in project.IDENTITY}


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
        "seeded_digest": measured["seeded_digest"],
        "seeded": measured["seeded"],
        "identity": identity(),
        "note": (
            "The digest of every template-owned and template-seeded file "
            "as the template shipped it, and the values init rewrites "
            "Turtle from (identity). A project keeps this as it arrived, "
            "with the block init adds (initialized): it is the record of "
            "what the project was made from, and "
            "tools/template_status.py compares the project's files, and "
            "a newer template's manifest, against it. template_commit is "
            "the template commit this record was made on; the commit "
            "that carries the record follows it, and a release tag names "
            "that commit."),
    }


def write_manifest(root: Path, record: dict) -> None:
    (root / MANIFEST).write_bytes(json.dumps(
        record, indent=2, sort_keys=True).encode("utf-8") + b"\n")


def recorded(root: Path | None = None) -> dict:
    root = root or layout.repository_root()
    path = root / MANIFEST
    if not path.is_file():
        raise Refused(MANIFEST + " is missing. Without it nothing can say "
                      "what this repository was made from.")
    return json.loads(path.read_text(encoding="utf-8"))


def initialize(root: Path, values: dict) -> dict:
    """init's own entry in the manifest, written after its rewrite: the
    values it used and each seeded file as it left it. The plain report
    compares against this, offline."""
    record = recorded(root)
    record["initialized"] = {
        "values": {key: values[key] for key in project.IDENTITY},
        "seeded": digests(root, seeded_files(root)),
    }
    write_manifest(root, record)
    return record


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


def touched(difference: dict) -> set:
    return set(difference["changed"]) | set(difference["removed"])


def against(other_root: Path) -> dict:
    """What a newer template changed since this project's record, and
    where that meets a change made here."""
    mine = recorded()["files"]
    theirs = recorded(other_root)["files"]
    upstream = compare(mine, theirs)
    local = compare(mine, measure()["files"])
    return {"template_changed": upstream, "changed_here": local,
            "both": sorted(touched(local) & touched(upstream))}


# --------------------------------------------------------- seeded files


def git_bytes(root: Path, *args: str) -> bytes | None:
    result = subprocess.run(["git", *args], cwd=str(root),
                            capture_output=True)
    return None if result.returncode else result.stdout


def base_commit(template: Path, record: dict) -> tuple[str | None, str]:
    """The template commit carrying this project's record, found in the
    checkout's history: the first commit from `template_commit` on whose
    manifest has the recorded digest (head_commit says why it is not
    `template_commit` itself). (None, why) when it cannot be found."""
    start = record.get("template_commit")
    if not start:
        return None, "this project's manifest names no template commit"
    if git_bytes(template, "cat-file", "-e", start + "^{commit}") is None:
        return None, ("%s is not a git checkout holding template commit %s"
                      % (template, start[:12]))
    listed = git_bytes(template, "log", "--reverse", "--format=%H",
                       start + "..HEAD", "--", MANIFEST) or b""
    for commit in [start] + listed.decode("ascii").split():
        shown = git_bytes(template, "show", "%s:%s" % (commit, MANIFEST))
        try:
            if shown and json.loads(shown)["digest"] == record["digest"]:
                return commit, ""
        except (ValueError, KeyError):
            continue
    return None, ("no commit from %s on in %s carries this project's "
                  "manifest" % (start[:12], template))


def yaml_of(data: bytes | None) -> dict:
    import yaml

    return (yaml.safe_load(data.decode("utf-8")) or {}) if data else {}


def as_received(name: str, data: bytes, template_values: dict,
                project_values: dict) -> bytes:
    """The template's copy of a seeded file as init would have left it in
    this project: Turtle through init's rewrite, anything else as is."""
    if not name.endswith(".ttl"):
        return data
    return project.rewrite_turtle(data.decode("utf-8"), template_values,
                                  project_values).encode("utf-8")


def pins_of(data: bytes | None) -> dict:
    return {s.get("id"): s.get("release")
            for s in yaml_of(data).get("sources") or []}


def dependency_changes(mine: bytes | None, theirs: bytes | None) -> list:
    """Each upstream whose release differs between this project and the
    template, both sides named."""
    here, there = pins_of(mine), pins_of(theirs)
    return [{"source": source, "here": here.get(source),
             "template": there.get(source)}
            for source in sorted(set(here) | set(there), key=str)
            if here.get(source) != there.get(source)]


def from_history(template: Path, record: dict) -> tuple[dict | None, dict,
                                                        str]:
    """The template's seeded files at the commit this project was made
    from, in the template's own form, and the values init rewrote them
    from: for a manifest from before v0.3.0, which records neither."""
    commit, why = base_commit(template, record)
    if commit is None:
        return None, {}, why
    values = yaml_of(git_bytes(template, "show",
                               commit + ":config/project.yaml"))
    listed = (git_bytes(template, "ls-tree", "-r", "--name-only", commit)
              or b"").decode("utf-8").splitlines()
    seeded = set(recorded(template).get("seeded") or {})
    files = {name: git_bytes(template, "show", "%s:%s" % (commit, name))
             for name in listed if name in seeded}
    return files, {key: values.get(key) for key in project.IDENTITY}, ""


def seeded_report(root: Path, template: Path | None = None) -> dict:
    """Seeded files, three ways: what the template changed since this
    project's record, what was configured here, what was changed on both
    sides; and what could not be compared, with why."""
    record = recorded(root)
    current = digests(root, seeded_files(root))
    out = {"template_changed": None, "configured_here": None, "both": [],
           "not_compared": [], "dependencies": []}
    initialized = record.get("initialized")

    base = record.get("seeded")           # template-form digests
    if initialized:
        out["configured_here"] = compare(initialized.get("seeded") or {},
                                         current)
    elif template is not None:
        files, values, why = from_history(template, record)
        if files is None:
            out["not_compared"].append(why)
        else:
            mine = identity()
            out["configured_here"] = compare(
                {name: sha256_of(as_received(name, data, values, mine))
                 for name, data in files.items()}, current)
            base = {name: sha256_of(data) for name, data in files.items()}
    else:
        out["not_compared"].append(
            "this project's manifest predates v0.3.0 and records none, so "
            "what was configured here can be found only from the "
            "template's history: run --against <template checkout>")

    if template is None:
        return out
    theirs = recorded(template).get("seeded")
    if theirs is None:
        out["not_compared"].append(
            "the template at %s records no seeded files (a manifest from "
            "before v0.3.0)" % template)
        return out
    if base is None:
        return out
    out["template_changed"] = compare(base, theirs)
    if out["configured_here"] is not None:
        out["both"] = sorted(touched(out["configured_here"])
                             & touched(out["template_changed"]))

    def read(where: Path) -> bytes | None:
        path = where / UPSTREAMS
        return path.read_bytes() if path.is_file() else None
    out["dependencies"] = dependency_changes(read(root), read(template))
    return out


def print_seeded(report: dict) -> None:
    changed = report["template_changed"]
    if changed is not None:
        print("  the template changed %d, removed %d, added %d seeded "
              "file(s) since this project's record"
              % (len(changed["changed"]), len(changed["removed"]),
                 len(changed["added"])))
        for key in ("changed", "removed", "added"):
            for name in changed[key]:
                print("    %-8s %s" % (key, name))
    here = report["configured_here"]
    if here is not None:
        names = here["changed"] + here["removed"] + here["added"]
        if names:
            print("  configured here (expected): %s" % ", ".join(names))
        else:
            print("  every seeded file is as the template left it")
    if report["both"]:
        print("  changed both here and in the template -- merge by hand:")
        for name in report["both"]:
            print("    %s" % name)
    if report["dependencies"]:
        print("  DEPENDENCY CHANGE, for review: the template pins an "
              "upstream differently from this project. This project's pin "
              "holds until the project adopts another; a move can change "
              "what the ontology means, and is a decision, not an upgrade:")
        for row in report["dependencies"]:
            print("    %-8s here %s, template %s"
                  % (row["source"], row["here"], row["template"]))
    for why in report["not_compared"]:
        print("  NOT COMPARED: the seeded files -- %s. They are not "
              "reported as unchanged." % why)


# ----------------------------------------------------------------- main


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
        write_manifest(root, manifest_of(now, args.label, head_commit(root)))
        print("  wrote %s: %d owned and %d seeded file(s), digest %s"
              % (MANIFEST, len(now["files"]), len(now["seeded"]),
                 now["digest"][:16]))
        return 0

    if args.against:
        other = Path(args.against).resolve()
        report = against(other)
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
        seeded = seeded_report(root, other)
        print_seeded(seeded)
        return NOT_COMPARED if seeded["not_compared"] else 0

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

    if template:
        seeded = compare(record.get("seeded") or {}, now["seeded"])
        for key in ("changed", "removed", "added"):
            for name in seeded[key]:
                print("    %-8s %s (seeded)" % (key, name))
        stale = (diverged(difference) or diverged(seeded)
                 or record.get("seeded") is None
                 or record.get("identity") != identity())
        if not stale:
            print("  every owned and seeded file is as the manifest records")
            return 0
        print()
        print("  STALE: this is the template, and its manifest does not "
              "describe its own files. Run: python %s --record" % GENERATOR)
        return 1 if args.check else 0

    if not diverged(difference):
        print("  every owned file is as the manifest records")
    else:
        print()
        print("  this project has diverged from the template it was made "
              "from in the files above. That is allowed; it is what the "
              "next template update will have to merge.")
    print_seeded(seeded_report(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
