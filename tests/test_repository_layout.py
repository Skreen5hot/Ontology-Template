# SPDX-License-Identifier: MIT
"""The layout contract describes the repository, or it fails.

A contract nobody checks is a set of paths that used to be true. Both
directions are asserted: every component resolves, and every tracked file
belongs to a component or falls under a rule that was written on purpose.
"""

from __future__ import annotations

import subprocess


def tracked(repo) -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=str(repo),
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-400:]
    return [line for line in result.stdout.splitlines() if line]


def test_every_tracked_component_resolves(layout):
    """A contract naming something absent is worse than no contract:
    every consumer believes it."""
    missing = [c.id for c in layout.components()
               if c.tracked and not c.exists()]
    assert not missing, missing


def test_never_tracked_components_are_absent_from_the_index(layout, repo):
    """The invariant, asserted rather than remembered.

    `tracked: false` says a component's files may exist on disk and must
    never be committed. That is a stronger statement than .gitignore
    makes: ignoring a path and a path being absent from the index are
    different facts, and only the second one keeps something off a public
    URL. A file already tracked stays tracked however the ignore rules
    change.

    In ARO this exists because four PDFs -- one of them a paid ISO
    standard -- were committed and served publicly while the README said
    they were not redistributed.
    """
    never = [c for c in layout.components() if not c.tracked]
    assert never, (
        "no component is marked tracked: false, so this test is watching "
        "nothing")

    indexed = set(tracked(repo))
    for entry in never:
        leaked = sorted(p for p in indexed
                        if p == entry.path or p.startswith(entry.path + "/"))
        assert not leaked, (
            "%s is declared never-tracked but these files are in the "
            "index: %s" % (entry.id, leaked))


def test_the_never_tracked_check_would_catch_a_committed_file(layout, repo):
    """Guards the test above. It passes trivially if the component's path
    never appears, so a typo in the declared path would silence it."""
    never = [c for c in layout.components() if not c.tracked]
    for entry in never:
        pretend_indexed = {entry.path + "/something.pdf"}
        leaked = sorted(p for p in pretend_indexed
                        if p == entry.path or p.startswith(entry.path + "/"))
        assert leaked, (
            "a file under %s would not be recognised as belonging to it, "
            "so the check cannot fire" % entry.path)


def test_no_two_components_share_an_id(layout):
    """Guarded in the loader, asserted here so the guard is exercised
    rather than assumed."""
    ids = [c.id for c in layout.components()]
    assert len(ids) == len(set(ids)), sorted(
        i for i in ids if ids.count(i) > 1)


def test_every_component_declares_a_role_with_a_meaning(layout,
                                                       disposition):
    """A role is not a label. Each one carries a licensing consequence,
    so an unrecognised role would be classified by accident.

    The known set is read from the licensing tool rather than listed
    here. It was listed here, and adding `vendored-ontology` failed this
    test for the right reason and then invited the wrong fix: paste the
    new name into the list and move on, leaving a role that the
    classifier still had no rule for. Asking the classifier what it knows
    makes the two impossible to disagree.
    """
    known = (disposition.CONTENT_ROLES | disposition.SOFTWARE_ROLES
             | disposition.LICENCE_ROLES | disposition.CITED_ROLES
             | disposition.VENDORED_ROLES)
    assert "invented-role" not in known, (
        "the known set accepts anything, so this test would pass for a "
        "role with no licensing rule")

    unknown = sorted({c.role for c in layout.components()} - known)
    assert not unknown, (
        "roles with no licensing rule: %s. Add one deliberately rather "
        "than letting a file inherit a guess." % unknown)


#: The artifacts nothing here can rebuild, named rather than counted.
#:
#: Empty, and the point is that it stays that way unless a commit says
#: otherwise. ARO started with two entries inherited from an earlier tree;
#: this repository starts with every generated file's generator present.
#:
#: Pinned so the list can only change deliberately. A new entry is a
#: failure -- somebody committed a derived file without its generator --
#: and removing one is a visible change in a diff, which is what
#: discharging the debt should look like.
ORPHANED_ARTIFACTS: list[str] = []


def test_a_generated_artifact_names_its_generator_or_admits_it_has_none(
        layout):
    """The rule that would have caught this repository lying to itself.

    Three components declared `generated-artifact`, whose stated meaning
    is "regenerated, not edited", while the tools that wrote them were
    not here. They could not be regenerated, and they were edited -- by
    text substitution, during the namespace migration, because there was
    no other way to move them.

    Nothing detected that, because the contract had no way to express the
    difference between an artifact with a generator and one without.
    """
    for entry in layout.components("generated-artifact"):
        declared = [name for name, value in
                    (("generator", entry.generator),
                     ("orphaned", entry.orphaned)) if value]
        assert len(declared) == 1, (
            "%s declares %s; a generated artifact names the tool that "
            "writes it, or states why nothing can" % (entry.id, declared))

        if entry.generator:
            tool = layout.component(entry.generator)
            assert tool.exists(), (
                "%s names generator %s, which the contract declares at %s "
                "-- and that path does not exist"
                % (entry.id, tool.id, tool.path))
        else:
            assert len(entry.orphaned.split()) >= 20, (
                "%s is orphaned with a reason too short to be one: %r"
                % (entry.id, entry.orphaned))


def test_the_orphaned_artifacts_are_the_ones_recorded(layout):
    """A debt register only works if adding to it is harder than paying
    it off."""
    found = sorted(c.id for c in layout.orphaned_artifacts())
    assert found == ORPHANED_ARTIFACTS, (
        "the set of artifacts nothing can rebuild changed: %s. If a "
        "generator landed, remove the entry here in the same commit; if "
        "a new derived file was committed without one, that is the "
        "finding." % found)


def test_no_orphaned_artifact_is_loaded_as_if_it_were_measured(layout):
    """The reason the register is not merely documentation.

    None of these may reach the reasoner scope or the corpus digest. An
    18.9 MB tree of reasoner output from a different tree, swept into the
    scope, would be reported as a property of this ontology.
    """
    orphans = {c.path for c in layout.orphaned_artifacts()}
    scope = {p.relative_to(layout.repository_root()).as_posix()
             for p in layout.ontology_files() + layout.vendored_files()}
    for path in scope:
        for orphan in orphans:
            assert not (path == orphan or path.startswith(orphan + "/")), (
                "%s is inside orphaned component %s and is in the scope"
                % (path, orphan))


def test_the_ontology_scope_excludes_what_it_must(layout, repo):
    """The reasoner scope is the authored ontology and nothing else.

    Sweeping the tree would load the reports the reasoner itself wrote
    and a fixture whose entire purpose is to be invalid, then report the
    result as a property of the ontology.
    """
    scope = {p.relative_to(repo).as_posix() for p in layout.ontology_files()}
    assert scope, "the ontology scope is empty"

    for excluded in ("shapes/wellformedness_bad_examples.ttl",
                     "shapes/wellformedness_shapes.ttl"):
        assert excluded not in scope, (
            "%s is in the reasoner scope; it is a %s"
            % (excluded, layout.owning_component(excluded).role))

    for path in scope:
        assert not path.startswith("vendor/"), path
        assert not path.startswith("drafts/"), path


def test_the_ontology_scope_is_not_empty_by_accident(layout):
    """Guards the test above: an empty scope excludes everything and
    would satisfy every assertion in it. A fresh project has one module."""
    assert len(layout.ontology_files()) >= 1, len(layout.ontology_files())


def test_every_tracked_file_has_an_owning_component_or_a_stated_rule(
        layout, repo, disposition):
    """The inverse direction. A file nothing declares is a file nobody
    decided about, and it will be classified by a suffix guess.

    No exemptions. This test once excused every file at the root and
    everything under .github/, tools/, tests/ and config/; a CI rehearsal
    planted an undeclared file at the root, and every check passed."""
    undeclared = [relative for relative in tracked(repo)
                  if layout.owning_component(relative) is None]
    assert not undeclared, (
        "%d tracked file(s) belong to no component: %s"
        % (len(undeclared), undeclared[:8]))


def test_an_undeclared_file_anywhere_is_caught(layout):
    """Guards the test above, at the places it once exempted. (.github/
    and tests/ are declared whole, so a file there is declared.)"""
    for path in ("planted.txt", "tools/planted.py",
                 "config/planted.yaml"):
        assert layout.owning_component(path) is None, path


def test_a_component_pointing_nowhere_is_caught(layout, repo, tmp_path):
    """Falsifies the resolver: a contract that returned paths without
    checking them would pass the first test in this file trivially."""
    import pytest

    entry = layout.component("docs.readme")
    original = entry.path
    try:
        entry.path = "docs/this-does-not-exist.md"
        with pytest.raises(layout.LayoutError) as error:
            entry.resolve()
        assert "docs.readme" in str(error.value)
    finally:
        entry.path = original
    assert entry.resolve().is_file()


def test_the_index_is_lf_throughout(repo):
    """The rule in .gitattributes, checked rather than trusted.

    A CRLF inside a Turtle literal is part of that literal's value, so
    two checkouts with different core.autocrlf settings would disagree
    about the corpus while both looked correct locally. The same applies
    to any digest recorded over a file git is free to re-encode: a byte
    digest over such a file is not a byte digest.

    The floor on blobs examined is set below what the template ships,
    so a fresh project passes it and a check that read nothing does not.
    """
    import subprocess

    nul = chr(0).encode()
    crlf = (chr(13) + chr(10)).encode()
    files = subprocess.run(["git", "ls-files"], cwd=str(repo),
                           capture_output=True, text=True).stdout.split(chr(10))
    offenders, checked = [], 0
    for name in filter(None, files):
        blob = subprocess.run(["git", "cat-file", "blob", ":" + name],
                              cwd=str(repo), capture_output=True).stdout
        if nul in blob[:8000]:
            continue
        checked += 1
        if crlf in blob:
            offenders.append(name)

    assert checked > 30, (
        "only %d text blobs were examined; this test is watching less "
        "than it should" % checked)
    assert not offenders, (
        "%d blob(s) carry CRLF in the index: %s"
        % (len(offenders), offenders[:8]))


def test_the_line_ending_rule_is_repository_wide(repo):
    """Narrowing it to *.ttl would leave every recorded digest describing
    the machine that measured it."""
    rule = (repo / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in rule, (
        "the repository-wide rule is gone; a corpus-only rule protects "
        "the corpus and nothing that records a checksum of anything else")
