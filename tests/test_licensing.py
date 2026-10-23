# SPDX-License-Identifier: MIT
"""What this repository may publish, decided before it publishes.

Carried from the Application Requirement Ontology, where they were
written while that repository was redistributing a paid ISO standard
from a public URL, with a README on the same commit saying it did not.
In a project made from the template they are in place before anything
licensed has been added: the standards and frameworks an ontology is
built against are usually somebody else's, and docs/Reference is where
they would go.

Two of them test the rule rather than the current corpus. Nothing here
is classified third-party-cited, so a test asserting on the classified
set would pass by finding nothing, and would go on passing if the rule
broke.
"""

from __future__ import annotations

import subprocess


def test_every_tracked_file_has_exactly_one_disposition(disposition):
    """`classify` refuses rather than guessing, so reaching this point at
    all is most of the assertion."""
    rows = disposition.classify()
    assert rows, "nothing was classified"
    paths = [row.path for row in rows]
    assert len(paths) == len(set(paths)), "a file was classified twice"

    tracked = subprocess.run(
        ["git", "ls-files"], cwd=str(disposition.layout.repository_root()),
        capture_output=True, text=True).stdout.splitlines()
    assert set(paths) == {p for p in tracked if p}, (
        "classified set and tracked set differ: "
        + str(sorted(set(paths) ^ {p for p in tracked if p})[:8]))


def test_the_project_licence_is_read_not_assumed(disposition):
    """A hardcoded licence map would assert terms the repository does not
    declare -- the same error as a README describing a policy its own
    contents contradict."""
    assert disposition.project_licence() == "MIT", (
        "LICENSE no longer says MIT; every project-authored file is "
        "reported as carrying whatever it says, so this is a deliberate "
        "change rather than a passing detail")


def test_an_ambiguous_licence_file_is_refused(disposition, monkeypatch):
    """Falsifies the reader: naming two licences must refuse, not pick."""
    import pytest

    class Fake:
        @staticmethod
        def read_text(encoding=None):
            return "MIT License ... Apache License ..."

    class FakeComponent:
        @staticmethod
        def resolve():
            return Fake()

    monkeypatch.setattr(disposition.layout, "component",
                        lambda _id: FakeComponent())
    disposition.project_licence.__wrapped__ if hasattr(
        disposition.project_licence, "__wrapped__") else None
    with pytest.raises(SystemExit) as error:
        disposition.project_licence()
    assert "Exactly one is required" in str(error.value)


def test_an_adjudication_matching_no_file_is_refused(disposition,
                                                     monkeypatch):
    """An exception granted for nothing reads as coverage."""
    import pytest

    monkeypatch.setattr(disposition, "adjudications", lambda: {
        "docs/no-such-file.md": {
            "path": "docs/no-such-file.md",
            "disposition": disposition.CONTENT,
            "why": "invented for this test",
            "decided": "2026-09-10",
            "decided_by": "test",
        }})
    with pytest.raises(SystemExit) as error:
        disposition.classify()
    assert "naming no tracked file" in str(error.value)


def test_the_cited_rule_makes_reference_material_unpublishable(
        disposition, layout):
    """Tests the rule, not the corpus.

    Nothing is classified third-party-cited any more, because the files
    are no longer tracked. Asserting on the classified set would
    therefore pass vacuously and stop meaning anything the moment the
    rule broke, so the rule is exercised directly against a path the
    reference component owns.
    """
    owner = layout.component("reference.third-party")
    matched = disposition.rules(owner.path + "/some-standard.pdf", owner)
    assert len(matched) == 1, matched
    kind, role, why = matched[0]
    assert kind == disposition.CITED, matched
    assert role == "third-party-reference"
    assert "must not" in why and "redistribute" in why
    assert disposition.licence_of(kind) is None, (
        "a cited work reports a licence; this repository grants no rights "
        "over it")


def test_the_reference_material_is_present_locally_but_not_committed(
        disposition, layout, repo):
    """Both halves. Absent from the index is the part that matters; still
    on disk is what makes the arrangement usable rather than a deletion.
    """
    import subprocess

    owner = layout.component("reference.third-party")
    indexed = subprocess.run(["git", "ls-files", owner.path],
                             cwd=str(repo), capture_output=True,
                             text=True).stdout.split()
    assert not indexed, (
        "reference material is tracked again: %s" % indexed[:4])

    if owner.exists():
        assert any((repo / owner.path).iterdir()), (
            "%s exists but is empty; the work needs these files even "
            "though the repository must not publish them" % owner.path)


def test_nothing_unpublishable_is_tracked(disposition):
    """The finding ARO had, kept as the check that it never happens here.

    ISO/IEC/IEEE 29148:2018 is a paid standard and was committed there,
    served from a public GitHub URL, while README.md said this repository
    does not redistribute it. Deleting the files would not have been
    enough: they stayed fetchable from the commits that added them, and
    those turned out to be two commits rather than one -- the files began
    at the repository root and were moved into docs/Reference later, so
    the first rewrite removed the destination and left the origin.
    """
    rows = disposition.classify()
    unpublishable = [row.path for row in rows if not row.redistributable]
    assert not unpublishable, (
        "%d file(s) this repository may not redistribute are committed, "
        "and are therefore published wherever it is:\n    %s\n\n"
        "Cite them in README.md instead. Removing them needs a history "
        "rewrite, because they stay fetchable from the commit that added "
        "them."
        % (len(unpublishable), "\n    ".join(unpublishable)))
