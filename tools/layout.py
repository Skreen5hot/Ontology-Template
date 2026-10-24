# SPDX-License-Identifier: MIT
"""Resolve logical component ids to paths.

Everything that needs a path asks here, so relocating a file is a change
to `config/repository-layout.yaml` rather than an edit across every module
that mentioned it.

Standalone by design. The equivalent in the project this was carried from
lived inside a package whose `__init__` loaded an entire agent runtime, so
asking where a file lived pulled in 44 modules and most of a second. That
was recorded as a known wart there; there is no reason to inherit it.

The only dependency is PyYAML, and the only thing this module does is read
one file and answer questions about it.
"""

from __future__ import annotations

import functools
from pathlib import Path

CONTRACT = "config/repository-layout.yaml"


class LayoutError(RuntimeError):
    """The contract and the tree disagree.

    Always raised with the component id and what was expected, because
    the usual cause is a file that moved without the contract following,
    and the id is the only thing that identifies which one.
    """


def repository_root(start: Path | None = None) -> Path:
    """The directory containing the layout contract.

    Found by walking up rather than by assuming a depth, so a tool can
    live at any level and a test can import from anywhere.
    """
    here = (start or Path(__file__)).resolve()
    for candidate in (here, *here.parents):
        if (candidate / CONTRACT).is_file():
            return candidate
    raise LayoutError(
        "no %s above %s, so the repository root cannot be identified"
        % (CONTRACT, here))


class Component:
    """One declaration, with the questions worth asking of it."""

    __slots__ = ("id", "path", "role", "description", "redistributable",
                 "tracked", "generator", "orphaned", "template", "format",
                 "_root")

    def __init__(self, raw: dict, root: Path):
        for required in ("id", "path", "role"):
            if not raw.get(required):
                raise LayoutError(
                    "a component in %s declares no %r: %r"
                    % (CONTRACT, required, raw))
        self.id = raw["id"]
        self.path = raw["path"]
        self.role = raw["role"]
        self.description = raw.get("description", "")
        # Absent means "no statement made", which is different from False.
        # Only a third-party reference is expected to say so explicitly.
        self.redistributable = raw.get("redistributable")
        #: Whether this component belongs in the index at all. Defaults
        #: to True because almost everything does; `tracked: false` says
        #: the files may exist locally and must never be committed, which
        #: is a stronger statement than .gitignore makes on its own.
        self.tracked = raw.get("tracked", True)
        #: The component id of the tool that writes this file, when one
        #: exists here. `orphaned` is the other answer: a reason, in
        #: prose, why this artifact cannot be rebuilt. Exactly one of the
        #: two is required of a generated-artifact, and the point of
        #: forcing the choice is that "neither" was the state three
        #: components were in while the contract said they were
        #: regenerated rather than edited.
        self.generator = raw.get("generator")
        self.orphaned = raw.get("orphaned")
        if self.generator and self.orphaned:
            raise LayoutError(
                "%s declares both a generator and a reason it is orphaned; "
                "it is one or the other" % self.id)
        #: The component's relation to the template this repository was
        #: made from. `owned`: the template maintains it, and a project
        #: that changes it has diverged (tools/template_status.py says
        #: where). `only`: it describes the template itself and
        #: tools/init_project.py removes it. Absent: the project's own.
        self.template = raw.get("template")
        if self.template not in (None, "owned", "only"):
            raise LayoutError(
                "%s declares template %r; the values are 'owned' and "
                "'only'" % (self.id, self.template))
        #: `canonical`: the module is kept in canonical Turtle by
        #: tools/ontology/normalize.py -- for a module edited in Protégé,
        #: which rewrites it on save. Absent: written by hand, comments
        #: and all.
        self.format = raw.get("format")
        if self.format not in (None, "canonical"):
            raise LayoutError("%s declares format %r; the value is "
                              "'canonical'" % (self.id, self.format))
        self._root = root

    def resolve(self) -> Path:
        """The path, required to exist.

        A contract naming something that is not there is worse than no
        contract: every consumer believes it.
        """
        target = self._root / self.path
        if not target.exists():
            raise LayoutError(
                "%s declares %s, which does not exist" % (self.id, self.path))
        return target

    def exists(self) -> bool:
        return (self._root / self.path).exists()

    def members(self, pattern: str = "*.ttl") -> list[Path]:
        """Files under a component, sorted.

        Sorted because a build that enumerates in filesystem order is a
        build whose output depends on the filesystem.
        """
        target = self.resolve()
        if target.is_file():
            return [target]
        return sorted(target.rglob(pattern),
                      key=lambda p: p.relative_to(target).as_posix())

    def relative_members(self, pattern: str = "*.ttl") -> list[str]:
        root = self._root
        return [p.relative_to(root).as_posix()
                for p in self.members(pattern)]

    def __repr__(self) -> str:
        return "Component(%r, %r, role=%r)" % (self.id, self.path, self.role)


@functools.lru_cache(maxsize=1)
def _load() -> dict[str, Component]:
    import yaml

    root = repository_root()
    raw = yaml.safe_load((root / CONTRACT).read_text(encoding="utf-8")) or {}
    declared = raw.get("components") or []
    if not declared:
        raise LayoutError(CONTRACT + " declares no components")

    found: dict[str, Component] = {}
    for entry in declared:
        component = Component(entry, root)
        if component.id in found:
            raise LayoutError(
                "two components share the id %r, so a consumer asking for "
                "it would get whichever was parsed last" % component.id)
        found[component.id] = component
    return found


def component(component_id: str) -> Component:
    known = _load()
    if component_id not in known:
        raise LayoutError(
            "no component %r in %s. Declared ids: %s"
            % (component_id, CONTRACT, ", ".join(sorted(known))))
    return known[component_id]


def path(component_id: str) -> Path:
    return component(component_id).resolve()


def components(role: str | None = None) -> list[Component]:
    """Every component, or every one in a role, in declaration order."""
    everything = list(_load().values())
    if role is None:
        return everything
    return [c for c in everything if c.role == role]


def roles() -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in _load().values():
        counts[entry.role] = counts.get(entry.role, 0) + 1
    return dict(sorted(counts.items()))


def ontology_files() -> list[Path]:
    """Every authored ontology file, and nothing else.

    Deliberately excludes generated artifacts, validation shapes and the
    bad-example fixture. A reasoner run that swept the whole tree would
    load reports it had itself produced and a file whose entire purpose
    is to be invalid, and would then report the result as a property of
    the ontology.
    """
    out: list[Path] = []
    for entry in components():
        if entry.role in ("ontology-module", "ontology-module-set"):
            out.extend(entry.members("*.ttl"))
    return out


def orphaned_artifacts() -> list["Component"]:
    """Generated artifacts nothing in this repository can rebuild.

    Kept as a list rather than a comment so it can shrink visibly. Every
    entry is a file that looks derived, is treated as derived by anyone
    reading it, and is in fact frozen at whatever it said when it arrived.
    """
    return [c for c in components() if c.orphaned]


def vendored_files() -> list[Path]:
    """Every vendored upstream extract.

    Separate from `ontology_files` and deliberately so. These belong in
    the *data* graph -- a shape asking whether a class reaches a CCO
    anchor cannot answer without them -- and must be absent from every
    measure of what this repository authored. One combined list would
    make the corpus digest move whenever an upstream pin changed, which
    is a digest of the wrong thing.
    """
    out: list[Path] = []
    for entry in components("vendored-ontology"):
        out.extend(entry.members("*.ttl"))
    return out


def declared_paths() -> set[str]:
    """Every path the contract names, relative to the root."""
    return {entry.path for entry in _load().values()}


def owning_component(relative_path: str) -> Component | None:
    """Which component a repository-relative path belongs to.

    Longest match wins, so a file inside a directory component resolves
    to that component rather than to a shorter prefix that happens to
    match.
    """
    best: Component | None = None
    for entry in _load().values():
        declared = entry.path
        if relative_path == declared or relative_path.startswith(declared + "/"):
            if best is None or len(declared) > len(best.path):
                best = entry
    return best


def main(argv=None) -> int:
    """`python tools/layout.py` prints the contract as resolved."""
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--role", default=None)
    ap.add_argument("--id", default=None)
    args = ap.parse_args(argv)

    if args.id:
        entry = component(args.id)
        print("%s\n  path %s\n  role %s\n  %s"
              % (entry.id, entry.path, entry.role, entry.description.strip()))
        return 0

    print("root %s" % repository_root())
    print()
    for entry in components(args.role):
        if not entry.tracked:
            mark = "local " if entry.exists() else "absent"
        else:
            mark = "ok    " if entry.exists() else "MISSING"
        print("  %-7s %-36s %-22s %s"
              % (mark, entry.id, entry.role, entry.path))
    print()
    print("  roles: %s" % roles())
    print("  never tracked: %s"
          % [e.id for e in components() if not e.tracked])
    orphans = orphaned_artifacts()
    if orphans:
        print("  cannot be regenerated (no generator here): %s"
              % [e.id for e in orphans])
    missing = [e.id for e in components() if e.tracked and not e.exists()]
    if missing:
        print("  MISSING: %s" % missing)
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
