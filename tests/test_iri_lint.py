# SPDX-License-Identifier: MIT
"""The IRI linter: each rule fires where it should, and nowhere else.

The fixtures are in tests/fixtures/iri_lint/. dirty.ttl marks every line
that must be reported with a trailing `# expect:` comment, and the test
reads those comments as the expected result -- so the expectation sits
beside the case, and a line nobody marked that gets reported is a false
positive, which fails exactly as a missed finding does. clean.ttl and
module2.ttl are the positive controls.

Three of the controls are the defects found in IRI_Linter on 2026-10-23,
each now a case: a BFO parent reported as dangling, a CCO v2.0 term
reported as unverified because the register was from another release,
and an unparseable file reported clean. A fourth is the line number: every
occurrence is reported on its own line.

The fixtures carry `{{namespace}}` where the project namespace goes, and
are written to a temporary directory with it filled in, because they are
template-owned and must name no project.
"""

from __future__ import annotations

import json
import re

import pytest

from conftest import load_tool

FIXTURES = "tests/fixtures/iri_lint"


@pytest.fixture(scope="module")
def linter():
    return load_tool("t_iri_lint", "tools/ontology/iri_lint.py")


@pytest.fixture(scope="module")
def written(repo, project, tmp_path_factory):
    """The fixtures with the project namespace filled in."""
    target = tmp_path_factory.mktemp("iri_lint")
    out = {}
    for source in sorted((repo / FIXTURES).glob("*.ttl")):
        text = source.read_bytes().decode("utf-8")
        assert "{{namespace}}" in text, source.name
        path = target / source.name
        path.write_bytes(text.replace("{{namespace}}",
                                      project.namespace()).encode("utf-8"))
        out[source.stem] = path
    assert {"clean", "module2", "dirty", "broken"} <= set(out), sorted(out)
    return out


def expectations(path, linter, project):
    """{(line, rule): suggestion-or-marker} read from `# expect:` comments."""
    sources = linter.upstreams()
    prefixes = {s.prefix: s.namespace for s in sources}
    prefixes["p"] = project.namespace()
    found = {}
    for number, line in enumerate(path.read_text(encoding="utf-8")
                                  .split("\n"), 1):
        match = re.search(r"#\s*expect:\s*(\w+)(?:\s*->\s*(\S+)|\s+(candidates))?\s*$",
                          line)
        if not match:
            continue
        rule, suggested, candidates = match.groups()
        if suggested:
            prefix, local = suggested.split(":", 1)
            suggested = prefixes[prefix] + local
        found[(number, rule)] = suggested or candidates
    return found


def results_of(findings):
    out = {}
    for record in findings:
        key = (record["line"], record["type"])
        assert key not in out, "two findings on one line for one rule: %s" % (
            key,)
        out[key] = (record.get("suggestion")
                    or ("candidates" if "candidates" in record else None))
    return out


# ---------------------------------------------------------- the live corpus


def test_the_authored_turtle_lints_clean(linter, layout):
    """Guarded: the scope is the modules and the shapes, and must not be
    empty -- an empty scope lints clean and says nothing."""
    paths = linter.default_paths()
    module = layout.component("ontology.main").resolve()
    assert module in paths
    assert not [p for p in paths if "bad_examples" in p.name], (
        "a fixture built to be invalid is in the lint scope")
    assert linter.lint(paths) == []


def test_the_main_entry_point_exits_0_on_the_corpus(linter, capsys):
    assert linter.main([]) == 0


# ------------------------------------------------------------- the rules


def test_the_positive_controls_report_nothing(linter, written):
    findings = linter.lint([written["clean"], written["module2"]])
    assert findings == [], findings


def test_the_dirty_fixture_reports_exactly_what_it_marks(linter, written,
                                                         project):
    want = expectations(written["dirty"], linter, project)
    assert len(want) >= 16, (
        "the fixture marks %d expectations; the markers are not being "
        "read" % len(want))
    findings = [f for f in linter.lint([written["dirty"], written["module2"]])
                if f["file"] == written["dirty"].as_posix()]
    got = results_of(findings)
    missing = {k: v for k, v in want.items() if k not in got}
    unexpected = {k: v for k, v in got.items() if k not in want}
    wrong = {k: (want[k], got[k]) for k in want.keys() & got.keys()
             if want[k] != got[k]}
    assert not missing and not unexpected and not wrong, (
        "missing %s; unexpected %s; wrong suggestion (want, got) %s"
        % (missing, unexpected, wrong))


def test_every_rule_is_exercised(linter, written, project):
    """Named, not counted: a rule no fixture line expects is a rule
    nothing shows can fire. deprecated_upstream is exercised below on a
    constructed register, because neither pinned upstream deprecates
    anything."""
    rules = {rule for _line, rule in expectations(written["dirty"], linter,
                                                  project)}
    assert rules | {"deprecated_upstream"} == set(linter.RULES), rules


def test_a_reference_resolves_across_the_files_linted_together(
        linter, written, project):
    """dirty.ttl points at p:FromTheOtherModule, which only module2.ttl
    declares. Linted alone it dangles; linted together it does not."""
    target = project.namespace() + "FromTheOtherModule"
    alone = [f for f in linter.lint([written["dirty"]])
             if f["subject"] == target]
    together = [f for f in linter.lint([written["dirty"], written["module2"]])
                if f["subject"] == target]
    assert alone and all(f["type"] == "dangling_ref" for f in alone)
    assert together == []


def test_a_deprecated_upstream_term_is_reported(linter, written,
                                                monkeypatch):
    """Neither pinned upstream marks a term owl:deprecated, so the rule is
    exercised by marking one in the loaded register."""
    real = linter.upstreams

    def with_deprecation(root=None):
        sources = real(root)
        for source in sources:
            if "https://www.commoncoreontologies.org/ont00000326" in \
                    source.terms:
                source.terms = dict(source.terms)
                source.terms[
                    "https://www.commoncoreontologies.org/ont00000326"] = \
                    dict(source.terms[
                        "https://www.commoncoreontologies.org/ont00000326"],
                        deprecated=True)
        return sources

    monkeypatch.setattr(linter, "upstreams", with_deprecation)
    findings = linter.lint([written["clean"], written["module2"]])
    assert [f["type"] for f in findings] == ["deprecated_upstream"], findings


# ------------------------------------------- IRI_Linter's defects, as cases


def test_a_bfo_parent_is_not_a_dangling_reference(linter, written):
    findings = linter.lint([written["clean"], written["module2"]])
    assert not [f for f in findings
                if f["subject"].startswith("http://purl.obolibrary.org/obo/")]
    clean = written["clean"].read_text(encoding="utf-8")
    assert "obo:BFO_0000040" in clean, "the case is no longer in the fixture"


def test_a_cco_v2_term_is_verified_against_the_pinned_release(linter,
                                                              written):
    """UPC Barcode is in CCO v2.0 and not in IRI_Linter's register."""
    sources = {s.id: s for s in linter.upstreams()}
    assert ("https://www.commoncoreontologies.org/ont00000326"
            in sources["cco"].terms)
    assert "cco:ont00000326" in written["clean"].read_text(encoding="utf-8")


def test_a_file_that_does_not_parse_is_not_clean(linter, written, capsys):
    with pytest.raises(linter.Unrunnable) as error:
        linter.lint([written["broken"]])
    assert "does not parse" in str(error.value)
    assert linter.main([str(written["broken"])]) == 2
    assert "broken.ttl" in capsys.readouterr().err


def test_a_file_that_cannot_be_read_is_not_clean(linter, tmp_path):
    assert linter.main([str(tmp_path / "absent.ttl")]) == 2


def test_a_missing_register_stops_the_lint(linter, tmp_path, written):
    (tmp_path / "config").mkdir()
    (tmp_path / "config/upstream-sources.yaml").write_text(
        "sources:\n  - id: x\n    register: vendor/x.json\n",
        encoding="utf-8")
    with pytest.raises(linter.Unrunnable) as error:
        linter.lint([written["clean"]], root=tmp_path)
    assert "vendor/x.json is missing" in str(error.value)


def test_every_occurrence_is_reported_on_its_own_line(linter, written,
                                                      project):
    """IRI_Linter reported the first line an IRI appeared on, for every
    occurrence, and then deduplicated them into one."""
    target = project.namespace() + "AlsoUndeclared"
    lines = sorted(f["line"] for f in linter.lint(
        [written["dirty"], written["module2"]]) if f["subject"] == target)
    text = written["dirty"].read_text(encoding="utf-8").split("\n")
    want = [n for n, line in enumerate(text, 1)
            if "p:AlsoUndeclared" in line.split("#")[0]]
    assert len(want) == 2 and lines == want, (lines, want)


# ------------------------------------------------------------ the scanner


def test_comments_and_strings_are_not_occurrences(linter):
    """The line finder blanks comments and literals -- triple-quoted ones
    across lines -- and keeps <...> whole, so a # inside an IRI is not a
    comment."""
    text = ('p:a p:b """first line\nsecond cco:X line""" . # cco:Y\n'
            "p:c <https://h.invalid/x#y> 'cco:Z' .\n")
    code = linter.code_only(text)
    assert code.count("\n") == text.count("\n")
    assert "cco:X" not in code and "cco:Y" not in code and "cco:Z" not in code
    assert "<https://h.invalid/x#y>" in code


def test_a_quote_inside_a_triple_quoted_literal_does_not_end_it(linter):
    """The case that tells a triple-quote scanner from a single-quote one.

    The test above passed with triple quotes read as single ones, because
    its literal held no quote of its own: `""` then `"..."` blanked the
    same span. A definition with an inch mark does not -- read one quote
    at a time, the text after the mark is code, and an IRI in the prose
    becomes an occurrence. Found by mutating the scanner.
    """
    text = 'p:a p:b """a bolt 5" long,\nsee cco:X""" .\n'
    code = linter.code_only(text)
    assert "cco:X" not in code, code
    assert "long" not in code, code


@pytest.mark.parametrize("name, label", [
    ("has_output", "has output"), ("hasOutput", "has output"),
    ("has-output", "has output"), ("Organization", "organization"),
    ("UPCBarcode", "upc barcode"),
])
def test_names_and_labels_meet_in_one_form(linter, name, label):
    assert linter.normalized(name) == linter.normalized(label) == label


# --------------------------------------------------------------- output


def test_the_json_output_keeps_iri_linters_shape(linter, written, capsys):
    """format_version, metadata, statistics, violations with file, line,
    type, subject and an optional suggestion -- IRI_Linter's schema, so a
    consumer of one reads the other."""
    code = linter.main([str(written["dirty"]), str(written["module2"]),
                        "--output", "json"])
    assert code == 1
    record = json.loads(capsys.readouterr().out)
    assert set(record) >= {"format_version", "metadata", "statistics",
                           "violations"}
    assert record["statistics"]["total_violations"] == len(
        record["violations"]) > 0
    for violation in record["violations"]:
        assert {"file", "line", "type", "subject"} <= set(violation)
    assert any("suggestion" in v for v in record["violations"])


def test_the_text_output_names_the_suggestion(linter, written, capsys):
    linter.main([str(written["dirty"]), str(written["module2"])])
    out = capsys.readouterr().out
    assert "readable_label cco:Organization -> cco:ont00001180" in out, out


# ---------------------------------------------------------------- hooks


@pytest.fixture(scope="module")
def hook():
    return load_tool("t_claude_hook", "tools/hooks/claude_ttl_lint.py")


def test_the_claude_hook_is_registered_for_edits(repo):
    """The settings file names the hook script that exists, on the tools
    an agent writes files with. A hook pointing at a moved script fails
    silently in every session."""
    settings = json.loads((repo / ".claude/settings.json").read_text(
        encoding="utf-8"))
    entries = settings["hooks"]["PostToolUse"]
    commands = [(entry["matcher"], hook_["command"]) for entry in entries
                for hook_ in entry["hooks"]]
    assert any("Write" in m and "Edit" in m and
               "tools/hooks/claude_ttl_lint.py" in c for m, c in commands), (
        commands)
    assert (repo / "tools/hooks/claude_ttl_lint.py").is_file()


def test_the_claude_hook_passes_what_is_not_turtle_here(hook, repo):
    def never(_root):
        raise AssertionError("the lint ran for a file it should ignore")

    assert hook.decide({"tool_input": {"file_path": str(repo / "README.md")}},
                       repo, run=never) == (0, "")
    assert hook.decide({"tool_input": {"file_path": "/elsewhere/x.ttl"}},
                       repo, run=never) == (0, "")
    assert hook.decide({}, repo, run=never) == (0, "")


def test_the_claude_hook_hands_findings_back(hook, repo):
    """Exit 2 is how a PostToolUse hook returns stderr to the agent; a
    finding (lint exit 1) and an unrunnable lint (exit 2) both use it."""
    edited = {"tool_input": {"file_path": str(repo / "ontology/x.ttl")}}
    assert hook.decide(edited, repo, run=lambda _r: (0, "")) == (0, "")
    code, message = hook.decide(
        edited, repo, run=lambda _r: (1, "x.ttl:3 readable_label cco:Organization"
                                         " -> cco:ont00001180"))
    assert code == 2 and "cco:ont00001180" in message
    code, message = hook.decide(edited, repo,
                                run=lambda _r: (2, "does not parse"))
    assert code == 2 and "could not run" in message


def test_the_claude_hook_runs_the_real_lint(hook, repo):
    """End to end, on the live corpus: clean, so the hook stays silent."""
    edited = {"tool_input": {"file_path": str(repo / "ontology/x.ttl")}}
    assert hook.decide(edited, repo) == (0, "")


def test_the_git_hook_runs_the_linter_and_is_executable(repo):
    import subprocess

    text = (repo / ".githooks/pre-commit").read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh")
    assert "tools/ontology/iri_lint.py" in text
    mode = subprocess.run(["git", "ls-files", "-s", ".githooks/pre-commit"],
                          cwd=str(repo), capture_output=True
                          ).stdout.decode().split()[0]
    assert mode == "100755", "the hook is not executable in the index: %s" % mode
