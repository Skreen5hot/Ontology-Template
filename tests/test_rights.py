# SPDX-License-Identifier: MIT
"""Rights and provenance reviews (P8, template decision 40).

Each refusal has a planted case refused by name and a near miss that
passes, on a small project built in a temporary directory with its own
register, reviews, declarations, decision records, modules and git
history. The four safeguards of decision 40 are among them: a review
names its edition and each intended use, and a release of one use, or of
one edition, covers no other; a manual item holds no digest and is never
counted as digest-verified; the stage and release holds ask only that a
decision exists and covers the use; and a decision taken before
required_from stands as written.
"""

from __future__ import annotations

import copy
import hashlib
import http.server
import os
import shutil
import subprocess
import threading
from pathlib import Path

import pytest
import yaml

from conftest import ROOT, load_tool


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_rights", "tools/rights.py")


SOURCE = "SRC-STD-01"
PROPERTY = "https://example.org/vocabulary#sourceText"
MODULE = "ontology/core.ttl"
OTHER = "ontology/extra.ttl"
DECISION = "docs/decisions/2026-11-10-standard-use.md"
DIGEST = "a" * 64
COMMIT = "b" * 40
OWNERS = {MODULE: "ontology.main", OTHER: "ontology.extra"}

TURTLE = """@prefix ex: <https://example.org/vocabulary#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
<https://example.org/onto> a owl:Ontology .
ex:Thing ex:sourceText "Quoted text." .
"""


def evidence(**extra):
    item = {"kind": "url", "url": "https://example.org/licence.html",
            "sha256": DIGEST, "retrieved": "2026-11-07",
            "checked": "The licence notice."}
    item.update(extra)
    return item


def review(**extra):
    entry = {"source": SOURCE, "rightsholder": "Example Body",
             "work": "Example Standard", "edition": "2021",
             "status": "evidence-complete", "terms": "unambiguous",
             "evidence": [evidence()],
             "reviewed_by": "A. Reviewer (rights-reviewer)",
             "uses": [use()]}
    entry.update(extra)
    return entry


def use(state="released", modules=(MODULE,), **extra):
    entry = {"intended": "Definitions quoted, attributed.",
             "modules": list(modules), "use": state}
    if state == "released":
        entry["released_by"] = {"decision": DECISION,
                                "by": "A. Damiano (architect)"}
    entry.update(extra)
    return entry


def declaration(**extra):
    entry = {"property": PROPERTY, "source": "Example Standard",
             "release": "2021", "licence": "unknown",
             "attribution": "Contains text from Example Standard.",
             "rights": SOURCE}
    entry.update(extra)
    return entry


def project(root, reviews=(), declarations=None, settings=None,
            files=None, register=(SOURCE, "SRC-STD-02"), quote_limit=None,
            untracked=(), commit_date=None):
    """A project with this register, these reviews and declarations, a
    module holding the declared property, and a decision record citing
    the source. All tracked but the untracked ones; committed if
    commit_date is given."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "config/review.yaml", root / "config/review.yaml")
    write = {
        "config/rights.yaml": yaml.safe_dump(dict({"version": 1},
                                                  **(settings or {}))),
        "config/sources.yaml": yaml.safe_dump(
            {"version": 1, "max_quote_words": quote_limit}),
        "research/sources.yaml": yaml.safe_dump({
            "format_version": 1, "exceptions": [],
            "entries": [{"id": s, "citation": "A work."} for s in register]}),
        "research/rights.yaml": yaml.safe_dump(
            {"format_version": 1, "reviews": list(reviews)}),
        "config/third-party-text.yaml": yaml.safe_dump({
            "format_version": 1,
            "declarations": [declaration()] if declarations is None
            else list(declarations)}),
        MODULE: TURTLE,
        OTHER: TURTLE,
        DECISION: "# Use of the standard\n\nReleases %s.\n" % SOURCE,
    }
    write.update(files or {})
    for name, text in write.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(text.encode("utf-8"))
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    for name in untracked:
        subprocess.run(["git", "rm", "-q", "--cached", name], cwd=root,
                       check=True)
    if commit_date:
        env = dict(os.environ, GIT_COMMITTER_DATE=commit_date + "T12:00:00",
                   GIT_AUTHOR_DATE=commit_date + "T12:00:00")
        subprocess.run(["git", "-c", "user.name=t", "-c",
                        "user.email=t@invalid", "commit", "-q", "-m", "c"],
                       cwd=root, check=True, env=env)
    return root


def check(tool, root, **kwargs):
    return tool.check(root, modules=[root / MODULE, root / OTHER], **kwargs)


def said(result, text):
    return any(text in p for p in result["problems"])


def held(result):
    return {(r["module"], r["why"]) for r in result["held"]}


def why(result, module=MODULE):
    return [r["why"] for r in result["held"] if r["module"] == module]


# ----------------------------------------------------------- a clean one


def test_a_released_use_with_its_decision_passes_and_holds_nothing(
        tool, tmp_path):
    result = check(tool, project(tmp_path, [review(uses=[
        use(modules=[MODULE, OTHER])])]))
    assert result["problems"] == [] and result["held"] == []
    assert result["reviews"] == 1


def test_the_template_record_is_empty_and_clean(tool):
    result = tool.check(ROOT)
    assert result["problems"] == [] and result["reviews"] == 0


# ----------------------------------------------------------- the schema


@pytest.mark.parametrize("change, message", [
    ({"licence_text": "x"}, "unknown field(s): licence_text"),
    ({"rightsholder": ""}, "has no rightsholder"),
    ({"edition": None}, "has no edition"),
    ({"source": "SRC-STD-09"}, "is not a source of research/sources.yaml"),
    ({"status": "done"}, "status 'done' is not one of"),
    ({"terms": "fine"}, "terms 'fine' is not one of"),
    ({"status": "gap"}, "is gap and gives no gap_reason"),
    ({"status": "deferred"}, "is deferred and gives no gap_reason"),
    ({"gap_reason": "x"}, "is evidence-complete and gives a gap_reason"),
    ({"gap_reason": None, "status": "gap"}, "is gap and gives no gap_reason"),
    ({"terms": "ambiguous"}, "ambiguous and it lists no open question"),
    ({"open_questions": "one"}, "open_questions is not a list"),
    ({"evidence": []}, "evidence-complete and lists no evidence"),
    ({"evidence": "x"}, "evidence is not a list"),
    ({"reviewed_by": "A. Reviewer"}, "is not '<name> (<kind>)'"),
    ({"reviewed_by": "A. Reviewer (architect)"},
     "a rights review is made as rights-reviewer"),
    ({"uses": "x"}, "uses is not a list"),
])
def test_a_malformed_review_is_refused(tool, tmp_path, change, message):
    result = check(tool, project(tmp_path, [review(**change)]))
    assert said(result, message), result["problems"]


@pytest.mark.parametrize("change", [
    {"status": "gap", "gap_reason": "The annex was not found."},
    {"status": "deferred", "gap_reason": "Waiting on the publisher."},
    {"terms": "ambiguous", "open_questions": ["Is the annex covered?"]},
    {"terms": "not-established", "status": "gap", "gap_reason": "x"},
    {"gap_reason": None},
])
def test_the_near_misses_pass(tool, tmp_path, change):
    result = check(tool, project(tmp_path, [review(**change)]))
    assert result["problems"] == []


def test_one_edition_reviewed_twice_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(), review()]))
    assert said(result, "%s is reviewed twice for edition 2021" % SOURCE)


def test_two_editions_are_two_reviews_each_holding_its_own_text(tool,
                                                                 tmp_path):
    """Decision 40, safeguard 1: BCO reviews two editions of one source;
    each is its own review, and releases only its own edition's text."""
    other = "docs/decisions/2026-11-12-other-edition.md"
    result = check(tool, project(tmp_path, [
        review(uses=[use(modules=[MODULE, OTHER])]),
        review(edition="2024", uses=[use(state="withheld",
                                         modules=[MODULE, OTHER])])],
        declarations=[declaration(release="2024")],
        files={other: "# Other\n\nOn %s.\n" % SOURCE}))
    assert result["problems"] == []
    assert why(result) == ["its use (Definitions quoted, attributed.) is "
                           "withheld"]


def test_an_unknown_top_field_is_refused(tool, tmp_path):
    root = project(tmp_path, [review()])
    raw = yaml.safe_load((root / "research/rights.yaml").read_text())
    raw["notes"] = "x"
    (root / "research/rights.yaml").write_text(yaml.safe_dump(raw))
    assert said(check(tool, root), "unknown field(s): notes")


def test_an_unknown_format_cannot_be_read(tool, tmp_path):
    root = project(tmp_path)
    (root / "research/rights.yaml").write_text("format_version: 2\n")
    with pytest.raises(tool.Unreadable, match="format_version"):
        check(tool, root)


def test_an_unknown_setting_cannot_be_read(tool, tmp_path):
    with pytest.raises(tool.Unreadable, match="unknown field"):
        check(tool, project(tmp_path, settings={"release_by": []}))


def test_a_required_from_that_is_no_date_cannot_be_read(tool, tmp_path):
    with pytest.raises(tool.Unreadable, match="not a date"):
        check(tool, project(tmp_path, settings={"required_from": "soon"}))


# ------------------------------------------------------------- evidence


@pytest.mark.parametrize("item, message", [
    ({"kind": "web"}, "kind 'web' is not one of"),
    (evidence(sha256=None), "(url) has no sha256"),
    (evidence(checked=""), "(url) has no checked"),
    (evidence(sha256="A" * 64), "sha256 is not 64 lowercase hex"),
    (evidence(sha256="a" * 63), "sha256 is not 64 lowercase hex"),
    (evidence(retrieved="last week"), "is not a date"),
    (evidence(commit=COMMIT), "unknown field(s) for url evidence: commit"),
    ({"kind": "repository", "repository": "example/repo", "commit": "b" * 39,
      "path": "LICENSE", "sha256": DIGEST, "retrieved": "2026-11-07",
      "checked": "The licence."}, "commit is not 40 lowercase hex"),
    ({"kind": "repository", "repository": "example/repo", "path": "LICENSE",
      "sha256": DIGEST, "retrieved": "2026-11-07", "checked": "x"},
     "(repository) has no commit"),
    ({"kind": "manual", "retrieved": "2026-11-07", "checked": "The page."},
     "(manual) has no why_not_refetched"),
    ("x", "is not a mapping"),
])
def test_malformed_evidence_is_refused(tool, tmp_path, item, message):
    result = check(tool, project(tmp_path, [review(evidence=[item])]))
    assert said(result, message), result["problems"]


def test_manual_evidence_carrying_a_digest_is_refused(tool, tmp_path):
    """Decision 40, safeguard 2: no bytes kept, so nothing is
    digest-verified, and no digest may say otherwise."""
    item = {"kind": "manual", "retrieved": "2026-11-07", "checked": "x",
            "why_not_refetched": "Behind a login.", "sha256": DIGEST}
    result = check(tool, project(tmp_path, [review(evidence=[item])]))
    assert said(result, "is manual and carries a sha256")
    assert not said(result, "unknown field")


def test_manual_and_repository_evidence_pass_and_are_counted_apart(
        tool, tmp_path):
    items = [{"kind": "manual", "url": "https://example.org/terms",
              "retrieved": "2026-11-07", "checked": "The terms page.",
              "why_not_refetched": "It is rendered for a signed-in user."},
             {"kind": "repository", "repository": "example/repo",
              "commit": COMMIT, "path": "LICENSE", "sha256": DIGEST,
              "retrieved": "2026-11-07", "checked": "The licence."}]
    result = check(tool, project(tmp_path, [review(evidence=items)]))
    assert result["problems"] == []
    assert result["evidence"]["pinned"] == 1
    assert result["evidence"]["manual"] == 1
    assert result["evidence"]["manual_only"] == []


def test_a_review_on_manual_evidence_only_is_named(tool, tmp_path):
    item = {"kind": "manual", "retrieved": "2026-11-07", "checked": "x",
            "why_not_refetched": "Behind a login."}
    result = check(tool, project(tmp_path, [review(evidence=[item])]))
    assert result["evidence"]["pinned"] == 0
    assert result["evidence"]["manual_only"] == [SOURCE]


def test_the_report_never_calls_manual_evidence_digest_verified(
        tool, tmp_path, monkeypatch, capsys):
    item = {"kind": "manual", "retrieved": "2026-11-07", "checked": "x",
            "why_not_refetched": "Behind a login."}
    root = project(tmp_path, [review(evidence=[item])])
    monkeypatch.setattr(tool.layout, "repository_root", lambda: root)
    monkeypatch.setattr(tool.layout, "ontology_files",
                        lambda: [root / MODULE, root / OTHER])
    assert tool.main([]) == 0
    out = capsys.readouterr().out
    assert "0 evidence item(s) pinned by digest, 1 manual and not " \
           "digest-verified" in out
    assert "Resting on manual evidence only, with no bytes pinned: " \
           + SOURCE in out


def test_a_quote_over_the_limit_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(evidence=[
        evidence(quote="one two three four")])], quote_limit=3))
    assert said(result, "its quote is 4 words, longer than max_quote_words")


def test_a_quote_within_the_limit_passes(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(evidence=[
        evidence(quote="one two three")])], quote_limit=3))
    assert result["problems"] == []


def test_no_limit_admits_any_quote(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(evidence=[
        evidence(quote="word " * 400)])]))
    assert result["problems"] == []


# ----------------------------------------------------------------- uses


@pytest.mark.parametrize("entry, message", [
    (use(intended=""), "does not say what the text would be used for"),
    (use(modules=[]), "lists no modules it covers"),
    (use(modules=["ontology/*.ttl"]), "not a repository path to one file"),
    (use(modules=["../core.ttl"]), "not a repository path to one file"),
    (use(state="allowed"), "use 'allowed' is not one of"),
    (use(state="withheld", released_by={"decision": DECISION, "by": "x"}),
     "is withheld and names a release"),
    (dict(use(), released_by=None), "is released and names no released_by"),
    (use(released_by={"decision": DECISION, "by": "A. Damiano (architect)",
                      "on": "x"}), "released_by has unknown field(s): on"),
    (use(released_by={"decision": "docs/decisions/2026-11-11-none.md",
                      "by": "A. Damiano (architect)"}),
     "which is not a tracked decision record"),
    (use(released_by={"decision": "research/sources.yaml",
                      "by": "A. Damiano (architect)"}),
     "which is not a tracked decision record"),
    (use(released_by={"decision": DECISION, "by": "A. Damiano"}),
     "released_by.by 'A. Damiano' is not"),
    (use(released_by={"decision": DECISION,
                      "by": "A. Damiano (proxy-domain-expert)"}),
     "a kind config/rights.yaml does not allow to release"),
    ({"intended": "x", "modules": [MODULE], "use": "withheld", "why": "x"},
     "unknown field(s): why"),
])
def test_a_malformed_use_is_refused(tool, tmp_path, entry, message):
    result = check(tool, project(tmp_path, [review(uses=[entry])]))
    assert said(result, message), result["problems"]


def test_a_module_two_uses_cover_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(uses=[
        use(), use(state="withheld")])]))
    assert said(result, "use 2 covers %s, which use 1 covers too" % MODULE)


def test_a_release_by_an_untracked_decision_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, [review()], untracked=[DECISION]))
    assert said(result, "which is not a tracked decision record")


def test_a_decision_not_citing_the_source_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, [review()], files={
        DECISION: "# Use\n\nReleases the standard.\n"}))
    assert said(result, "which does not cite %s" % SOURCE)


def test_a_longer_identifier_is_not_a_citation(tool, tmp_path):
    result = check(tool, project(tmp_path, [review()], files={
        DECISION: "# Use\n\nReleases SRC-STD-010 and XSRC-STD-01.\n"}))
    assert said(result, "which does not cite %s" % SOURCE)


def test_a_decision_taken_before_required_from_stands_as_written(
        tool, tmp_path):
    """Decision 40, safeguard 4: an accepted decision is not reopened to
    cite a review made after it."""
    prior = "docs/decisions/2026-01-05-adr-003.md"
    result = check(tool, project(tmp_path, [review(uses=[use(
        modules=[MODULE, OTHER],
        released_by={"decision": prior, "by": "A. Damiano (architect)"})])],
        settings={"required_from": "2026-11-01"},
        files={prior: "# ADR-003\n\nThe framework's text may be used.\n"}))
    assert result["problems"] == [] and result["held"] == []


def test_a_decision_taken_after_required_from_must_cite(tool, tmp_path):
    result = check(tool, project(tmp_path, [review()],
                                 settings={"required_from": "2026-11-01"},
                                 files={DECISION: "# Use\n\nReleased.\n"}))
    assert said(result, "which does not cite %s" % SOURCE)


def test_an_undated_decision_is_dated_by_the_commit_that_added_it(
        tool, tmp_path):
    adr = "docs/adr/ADR-003.md"
    root = project(tmp_path, [review(uses=[use(released_by={
        "decision": adr, "by": "A. Damiano (architect)"})])],
        settings={"required_from": "2026-11-01",
                  "decisions": ["docs/decisions/*.md", "docs/adr/*.md"]},
        files={adr: "# ADR-003\n\nThe text may be used.\n"},
        commit_date="2026-03-01")
    assert check(tool, root)["problems"] == []


def test_an_uncommitted_undated_decision_must_cite(tool, tmp_path):
    adr = "docs/adr/ADR-003.md"
    result = check(tool, project(tmp_path, [review(uses=[use(released_by={
        "decision": adr, "by": "A. Damiano (architect)"})])],
        settings={"required_from": "2026-11-01",
                  "decisions": ["docs/decisions/*.md", "docs/adr/*.md"]},
        files={adr: "# ADR-003\n\nThe text may be used.\n"}))
    assert said(result, "which does not cite %s" % SOURCE)


def test_a_delegated_kind_may_release_with_its_delegation(tool, tmp_path):
    delegation = "docs/decisions/2026-11-09-delegation.md"
    result = check(tool, project(tmp_path, [review(uses=[use(released_by={
        "decision": DECISION, "by": "B. Reviewer (rights-reviewer)"})])],
        settings={"releasers": [{"kind": "architect"}, {
            "kind": "rights-reviewer", "delegated_by": delegation}]},
        files={delegation: "# Delegation\n"}))
    assert result["problems"] == []


@pytest.mark.parametrize("item, message", [
    ({"kind": "rights-reviewer"}, "only by a recorded delegation"),
    ({"kind": "rights-reviewer", "delegated_by": "docs/decisions/x.md"},
     "only by a recorded delegation"),
    ({"kind": "lawyer"}, "releaser 'lawyer' is not a kind"),
])
def test_a_releaser_without_its_delegation_is_refused(tool, tmp_path, item,
                                                      message):
    result = check(tool, project(tmp_path, [review(uses=[use(released_by={
        "decision": DECISION, "by": "B. Reviewer (rights-reviewer)"})])],
        settings={"releasers": [{"kind": "architect"}, item]}))
    assert said(result, message)
    if item["kind"] == "rights-reviewer":
        assert said(result, "does not allow to release")


# ------------------------------------------------------- where it is held


def test_text_whose_declaration_names_no_review_is_held(tool, tmp_path):
    result = check(tool, project(tmp_path, declarations=[
        {k: v for k, v in declaration().items() if k != "rights"}]))
    assert result["problems"] == []
    assert why(result) == ["its declaration names no rights review "
                           "(rights: SRC-...)"]


def test_text_from_a_source_with_no_review_is_held(tool, tmp_path):
    result = check(tool, project(tmp_path))
    assert result["problems"] == []
    assert why(result) == ["%s has no review in research/rights.yaml"
                           % SOURCE]


def test_text_from_another_edition_is_held(tool, tmp_path):
    """Decision 40, safeguard 1: a review of one edition releases
    nothing of another."""
    result = check(tool, project(tmp_path, [review()], declarations=[
        declaration(release="2024")]))
    assert result["problems"] == []
    assert why(result) == ["%s was reviewed for edition 2021; this text is "
                           "from release 2024" % SOURCE]


def test_a_use_released_for_one_module_does_not_cover_another(tool,
                                                              tmp_path):
    """Decision 40, safeguard 1: permission for one use is not permission
    for another."""
    result = check(tool, project(tmp_path, [review()]))
    assert why(result, MODULE) == []
    assert why(result, OTHER) == ["no intended use of %s in "
                                  "research/rights.yaml covers it" % SOURCE]


def test_a_withheld_use_is_held_and_fails_nothing(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(uses=[
        use(state="withheld", modules=[MODULE, OTHER])])]))
    assert result["problems"] == []
    assert why(result) == ["its use (Definitions quoted, attributed.) is "
                           "withheld"]


def test_a_release_with_a_finding_releases_nothing(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(uses=[
        use(modules=[MODULE, OTHER])])], files={
        DECISION: "# Use\n\nReleased.\n"}))
    assert said(result, "does not cite")
    assert why(result) == ["its release has a finding"]


def test_a_rights_naming_no_register_source_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, declarations=[
        declaration(rights="SRC-STD-77")]))
    assert said(result, "names the review of 'SRC-STD-77', which is not a "
                        "source")


def test_a_module_without_the_property_is_never_held(tool, tmp_path):
    result = check(tool, project(tmp_path, files={
        MODULE: "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
                "<https://example.org/onto> a owl:Ontology .\n",
        OTHER: "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
               "<https://example.org/onto2> a owl:Ontology .\n"}))
    assert result["held"] == []


def test_a_declaration_made_before_required_from_is_unreviewed_not_held(
        tool, tmp_path):
    result = check(tool, project(tmp_path, declarations=[
        {k: v for k, v in declaration().items() if k != "rights"}],
        settings={"required_from": "2026-11-01"}, commit_date="2026-06-01"))
    assert result["held"] == [] and result["problems"] == []
    assert {r["module"] for r in result["unreviewed"]} == {MODULE, OTHER}


def test_a_declaration_made_after_required_from_is_held(tool, tmp_path):
    result = check(tool, project(tmp_path, declarations=[
        {k: v for k, v in declaration().items() if k != "rights"}],
        settings={"required_from": "2026-11-01"}, commit_date="2026-11-05"))
    assert result["unreviewed"] == [] and len(result["held"]) == 2


def test_an_uncommitted_declaration_is_held_under_required_from(tool,
                                                                tmp_path):
    result = check(tool, project(tmp_path, declarations=[
        {k: v for k, v in declaration().items() if k != "rights"}],
        settings={"required_from": "2026-11-01"}))
    assert result["unreviewed"] == [] and len(result["held"]) == 2


def test_an_older_declaration_naming_a_review_is_held_to_it(tool, tmp_path):
    result = check(tool, project(tmp_path, settings={
        "required_from": "2026-11-01"}, commit_date="2026-06-01"))
    assert result["unreviewed"] == [] and len(result["held"]) == 2


# ------------------------------------------------------------ the gates


def stages(status="done", where=("ontology.main",), runs=True):
    return [{"id": "formalization", "runs": runs, "status": status,
             "where": list(where)}]


def test_a_done_stage_is_held_by_a_withheld_module_in_its_scope(tool,
                                                                tmp_path):
    result = check(tool, project(tmp_path, [review()]))
    problems = tool.stage_problems(stages(where=["ontology.extra"]),
                                   result["held"], OWNERS.get)
    assert problems == ["formalization: is done, but %s holds text from %s "
                        "(%s) no decision has released: no intended use of "
                        "%s in research/rights.yaml covers it"
                        % (OTHER, SOURCE, PROPERTY, SOURCE)]


@pytest.mark.parametrize("plan", [
    stages(status="in-progress", where=["ontology.extra"]),
    stages(where=["ontology.main"]),
    stages(runs=False, status="not-started", where=["ontology.extra"]),
])
def test_a_stage_not_done_or_out_of_scope_is_not_held(tool, tmp_path, plan):
    result = check(tool, project(tmp_path, [review()]))
    assert tool.stage_problems(plan, result["held"], OWNERS.get) == []


def test_a_held_module_stops_a_release(tool, tmp_path):
    result = check(tool, project(tmp_path, [review()]))
    assert tool.release_problems(result["held"]) == [
        "%s holds text from %s (%s) no decision has released: no intended "
        "use of %s in research/rights.yaml covers it"
        % (OTHER, SOURCE, PROPERTY, SOURCE)]


def test_nothing_held_releases(tool, tmp_path):
    result = check(tool, project(tmp_path, [review(uses=[
        use(modules=[MODULE, OTHER])])]))
    assert tool.release_problems(result["held"]) == []


def test_stages_check_reaches_the_withholding_gate(monkeypatch, tmp_path):
    stages_tool = load_tool("t_stages_p8", "tools/stages.py")
    import rights as imported

    row = {"module": MODULE, "property": PROPERTY, "source": SOURCE,
           "release": "2021", "why": "its use (x) is withheld"}
    monkeypatch.setattr(imported, "check", lambda root=None: {"held": [row]})
    monkeypatch.setattr(imported, "owner_of", OWNERS.get)
    monkeypatch.setattr(imported, "declarations",
                        lambda root: [declaration()])
    assert stages_tool.withholding(tmp_path, stages()) == [
        "formalization: is done, but %s holds text from %s (%s) no decision "
        "has released: its use (x) is withheld" % (MODULE, SOURCE, PROPERTY)]


def test_with_nothing_declared_the_gate_reads_no_record(monkeypatch,
                                                        tmp_path):
    stages_tool = load_tool("t_stages_p8_empty", "tools/stages.py")
    import rights as imported

    def refuse(root=None):
        raise AssertionError("the record was read")

    monkeypatch.setattr(imported, "check", refuse)
    monkeypatch.setattr(imported, "declarations", lambda root: [])
    assert stages_tool.withholding(tmp_path, stages()) == []


def test_stages_check_reaches_the_withholding_gate_only_when_done(
        monkeypatch, tmp_path):
    """The wiring in tools/stages.py: any stage marked done reaches the
    gate; with none done, nothing is read."""
    stages_tool = load_tool("t_stages_p8_wiring", "tools/stages.py")
    called = []
    monkeypatch.setattr(stages_tool, "withholding",
                        lambda r, s: called.append(r) or ["HELD"])
    monkeypatch.setattr(stages_tool, "propagation", lambda r, s: [])
    monkeypatch.setattr(stages_tool, "problems_of", lambda *a: [])
    path = tmp_path / "stages.yaml"
    monkeypatch.setattr(stages_tool.layout, "path",
                        lambda cid: path if cid == "config.stages"
                        else tmp_path / "docs/standards")
    monkeypatch.setattr(stages_tool.layout, "components", lambda: [])
    path.write_text(yaml.safe_dump({"version": 1, "path": stages()}),
                    encoding="utf-8")
    assert stages_tool.check(tmp_path)[1] == ["HELD"]
    path.write_text(yaml.safe_dump({"version": 1, "path": stages(
        status="in-progress")}), encoding="utf-8")
    called.clear()
    assert stages_tool.check(tmp_path)[1] == [] and called == []


def test_release_build_refuses_before_writing(monkeypatch, tmp_path):
    release = load_tool("t_release_p8", "tools/release.py")
    row = {"module": MODULE, "property": PROPERTY, "source": SOURCE,
           "release": "2021", "why": "its use (x) is withheld"}
    monkeypatch.setattr(release.decisions, "check",
                        lambda root=None: {"owed": []})
    monkeypatch.setattr(release.rights, "check",
                        lambda root=None: {"held": [row]})
    with pytest.raises(release.Refused, match="no decision has released"):
        release.build("1.2.3", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_a_hold_never_fails_the_ordinary_check(tool, tmp_path, monkeypatch,
                                                capsys):
    root = project(tmp_path, [review(uses=[use(state="withheld")])])
    monkeypatch.setattr(tool.layout, "repository_root", lambda: root)
    monkeypatch.setattr(tool.layout, "ontology_files",
                        lambda: [root / MODULE, root / OTHER])
    assert tool.main([]) == 0
    out = capsys.readouterr().out
    assert "withheld  %s <- %s" % (MODULE, SOURCE) in out
    assert "does not judge what a source's terms permit" in out


# -------------------------------------------------------------- confirm


@pytest.fixture
def server(tmp_path):
    """A local server for --confirm, never the network."""
    served = tmp_path / "served"
    served.mkdir()

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(served), **kwargs)

        def log_message(self, *args):
            pass

    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield served, "http://127.0.0.1:%d/" % httpd.server_address[1]
    httpd.shutdown()
    httpd.server_close()


def test_confirm_passes_a_document_whose_digest_holds(tool, tmp_path,
                                                      server):
    served, base = server
    (served / "licence.html").write_bytes(b"The licence.\n")
    digest = hashlib.sha256(b"The licence.\n").hexdigest()
    root = project(tmp_path / "p", [review(evidence=[evidence(
        url=base + "licence.html", sha256=digest)])])
    assert check(tool, root, refetch=True)["problems"] == []


def test_confirm_reports_a_moved_digest_and_never_repins_it(tool, tmp_path,
                                                            server):
    served, base = server
    (served / "licence.html").write_bytes(b"The licence, changed.\n")
    root = project(tmp_path / "p", [review(evidence=[evidence(
        url=base + "licence.html")])])
    before = (root / "research/rights.yaml").read_bytes()
    result = check(tool, root, refetch=True)
    assert said(result, "not the %s pinned on 2026-11-07" % DIGEST)
    assert said(result, "It is not re-pinned")
    assert (root / "research/rights.yaml").read_bytes() == before


def test_confirm_reports_a_document_it_cannot_fetch(tool, tmp_path, server):
    _, base = server
    root = project(tmp_path / "p", [review(evidence=[evidence(
        url=base + "gone.html")])])
    assert said(check(tool, root, refetch=True), "could not be fetched")


def test_confirm_refetches_only_url_items(tool, tmp_path):
    items = [{"kind": "manual", "url": "https://example.org/terms",
              "retrieved": "2026-11-07", "checked": "x",
              "why_not_refetched": "Behind a login."},
             {"kind": "repository", "repository": "example/repo",
              "commit": COMMIT, "path": "LICENSE", "sha256": DIGEST,
              "retrieved": "2026-11-07", "checked": "x"}]
    fetched = []
    root = project(tmp_path, [review(evidence=items)])
    result = check(tool, root, refetch=True,
                   fetcher=lambda url: fetched.append(url) or b"")
    assert fetched == [] and result["problems"] == []


def test_without_confirm_nothing_is_fetched(tool, tmp_path):
    fetched = []
    check(tool, project(tmp_path, [review()]),
          fetcher=lambda url: fetched.append(url) or b"")
    assert fetched == []


# ------------------------------------------------------------- the seeds


def test_the_seeded_files_are_the_defaults(tool):
    settings = tool.configuration(ROOT)
    assert settings == dict(tool.DEFAULTS)
    raw = yaml.safe_load((ROOT / "research/rights.yaml").read_text(
        encoding="utf-8"))
    assert raw == {"format_version": 1, "reviews": []}


def test_the_seeded_example_is_a_review_the_check_accepts(tool, tmp_path):
    """The commented example in research/rights.yaml, uncommented, with a
    digest for its placeholder, is a clean review held as withheld."""
    text = (ROOT / "research/rights.yaml").read_text(encoding="utf-8")
    lines = text.split("Example, not\n# a recommendation:\n#\n", 1)[1]
    lines = lines.split("\n\nformat_version", 1)[0]
    example = "\n".join(line[2:] for line in lines.splitlines())
    example = example.replace("<64 hex digits of the bytes retrieved>",
                              DIGEST)
    example = example.replace("<its id in research/sources.yaml>", SOURCE)
    entry = yaml.safe_load(example)[0]
    result = check(tool, project(tmp_path, [copy.deepcopy(entry)],
                                 declarations=[declaration()]))
    assert result["problems"] == []
    assert why(result) == ["its use (Definitions quoted in ontology/core.ttl, "
                           "attributed.) is withheld"]
