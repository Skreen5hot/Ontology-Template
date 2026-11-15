# SPDX-License-Identifier: MIT
"""The findings register, the checks that read it, and a Checks job that
runs every check.

The register replaced a count per shape set. Under the count, the
Business Process Ontology port found, fixing one of 57 findings and
introducing an unrelated one passed; a warning was never gated; and the
IRI linter, with no record at all, kept the Checks job red for one
accepted finding while the seven steps after it never ran. Each of those
is a test here, on planted cases rather than BPO's: a swap, a new
warning, a stale entry, an accepted lint finding, and a workflow step
that would stop the job.
"""

from __future__ import annotations

import datetime

import pytest
import yaml

from conftest import load_tool

TODAY = datetime.date(2026, 10, 28)


@pytest.fixture(scope="module")
def register():
    return load_tool("t_findings", "tools/findings.py")


@pytest.fixture(scope="module")
def validator():
    return load_tool("t_findings_validate", "tools/ontology/validate.py")


@pytest.fixture(scope="module")
def linter():
    return load_tool("t_findings_lint", "tools/ontology/iri_lint.py")


def entry_for(register, record, **extra):
    entry = {key: record[key] for key in register.IDENTITY}
    entry.update(reason="planted", owner="the suite", review="2027-01-01")
    entry.update(extra)
    return entry


def found(register, focus, rule="urn:shape:a", severity="Violation",
          message="m", check="validate", where="validation.a"):
    return register.finding(check, where, focus, rule, message, severity)


# ------------------------------------------------------- the entries


def test_an_entry_needs_reason_owner_and_review_date(register, project):
    good = entry_for(register, found(register, "urn:x"))
    assert register.problems_of([good]) == []
    for key in ("reason", "owner", "review", "check", "where", "focus",
                "rule", "digest", "severity"):
        bad = dict(good)
        del bad[key]
        got = register.problems_of([bad])
        assert any("has no %s" % key in p for p in got), (key, got)
    cases = {
        "review": ("2027-13-01", "is not a date"),
        "severity": ("Severe", "is not one of"),
        "check": ("spelling", "is not one of"),
    }
    for key, (value, said) in cases.items():
        got = register.problems_of([dict(good, **{key: value})])
        assert any(said in p for p in got), (key, got)
    got = register.problems_of([dict(good, reason="TODO why")])
    assert any("placeholder" in p for p in got), got
    got = register.problems_of([dict(good, colour="red")])
    assert any("unknown field" in p for p in got), got
    got = register.problems_of([good, dict(good)])
    assert any("repeats entry 1" in p for p in got), got


def test_an_upstream_focus_needs_an_entry_naming_the_upstream(register):
    sources = register.upstream_ids()
    cco = sources["CCO"]
    on_cco = entry_for(register, found(register, cco + "ont00001180"))
    got = register.problems_of([on_cco])
    assert any("must name the upstream" in p for p in got), got
    named = dict(on_cco, upstream="CCO %sont00001180" % cco)
    assert register.problems_of([named]) == []
    for wrong in ("CCO", "XYZ %sont00001180" % cco,
                  "CCO http://example.org/elsewhere"):
        got = register.problems_of([dict(on_cco, upstream=wrong)])
        assert any("is not '<SOURCE> <IRI>'" in p for p in got), (wrong, got)


def test_the_live_register_can_be_used(register):
    register.load()
    assert register.main([]) == 0


def test_a_proposal_is_refused_until_a_person_fills_it(register):
    records = [found(register, "urn:x"), found(register, "urn:x")]
    entries = yaml.safe_load(register.propose(records))
    assert len(entries) == 1, "a repeated finding was proposed twice"
    got = register.problems_of(entries)
    assert sum("placeholder" in p for p in got) == 7, got
    for key in ("reason", "owner", "review") + register.CLASSIFICATION:
        assert any(key in p for p in got if "placeholder" in p
                   or "not a date" in p), key
    filled = yaml.safe_load(register.propose(records, "r", "o",
                                             "2027-01-01"))
    left = register.problems_of(filled)
    assert sorted(p.split(":")[1].split()[0] for p in left) == sorted(
        register.CLASSIFICATION), "only the judgement is left to a person"
    for entry in filled:
        for key in register.CLASSIFICATION:
            del entry[key]
    assert register.problems_of(filled) == [], (
        "a version 1 entry may leave the classification out")


# ------------------------------------------------------- the policy


def test_swapping_one_finding_for_another_fails(register):
    """The defect the count could not see: one fixed, one introduced."""
    a, b, c = (found(register, "urn:" + n) for n in "abc")
    entries = [entry_for(register, a), entry_for(register, b)]
    assert register.judge("validate", [a, b], entries, TODAY)["passed"]
    verdict = register.judge("validate", [a, c], entries, TODAY)
    assert not verdict["passed"]
    assert verdict["new"] == [c] and verdict["failing"] == [c]
    assert [e["focus"] for e in verdict["stale"]] == ["urn:b"]


def test_a_changed_message_is_a_different_finding(register):
    a = found(register, "urn:a", message="one")
    moved = found(register, "urn:a", message="another")
    verdict = register.judge("validate", [moved], [entry_for(register, a)],
                             TODAY)
    assert not verdict["passed"] and verdict["new"] == [moved]


def test_a_new_warning_fails_unless_recorded(register):
    warning = found(register, "urn:w", severity="Warning")
    verdict = register.judge("validate", [warning], [], TODAY)
    assert not verdict["passed"] and verdict["failing"] == [warning]
    assert register.judge("validate", [warning],
                          [entry_for(register, warning)], TODAY)["passed"]


def test_a_new_info_is_reported_and_does_not_fail(register):
    info = found(register, "urn:i", severity="Info")
    verdict = register.judge("validate", [info], [], TODAY)
    assert verdict["passed"] and verdict["new"] == [info]


def test_a_stale_entry_fails(register):
    gone = entry_for(register, found(register, "urn:fixed"))
    verdict = register.judge("validate", [], [gone], TODAY)
    assert not verdict["passed"] and verdict["stale"] == [gone]
    partial = register.judge("validate", [], [gone], TODAY, complete=False)
    assert partial["passed"], "a run over part of the scope judged staleness"


def test_an_expired_review_is_reported_not_failed(register):
    a = found(register, "urn:a")
    due = entry_for(register, a, review="2026-01-01")
    verdict = register.judge("validate", [a], [due], TODAY)
    assert verdict["passed"] and verdict["expired"] == [due]


def test_entries_are_per_check(register):
    a = found(register, "urn:a")
    lint_entry = entry_for(register, dict(a, check="iri_lint"))
    verdict = register.judge("validate", [a], [lint_entry], TODAY)
    assert verdict["new"] == [a] and verdict["stale"] == []


# ------------------------------------------------------- the validator


def ladder_of(validator, data, path):
    """A record shaped as measure() makes it, for one shape set run over
    `data`, so the gate is exercised on real findings."""
    results = validator.run(data, validator.load([path]))["violations"]
    authored, warnings, upstream = validator.partition(results)
    return {"rungs": {"validation.realist": {
        "evaluable": True, "can_still_fail": True,
        "blocked_by_missing_vocabulary": [],
        "corpus": {"detail": authored, "warning_detail": warnings,
                   "vendored_detail": upstream}}}}


@pytest.fixture(scope="module")
def realist_record(validator, layout):
    data = validator.load([layout.path("fixture.realist-bad-examples")]
                          + list(layout.vendored_files()))
    return ladder_of(validator, data, layout.path("validation.realist"))


def test_the_validator_gate_fails_a_swap_of_real_findings(validator,
                                                          register,
                                                          realist_record):
    """On the realist fixture's own findings, violations and warnings
    both: all accepted passes; one replaced by an entry for something
    else fails, naming both."""
    real = validator.register_findings(realist_record)
    severities = {r["severity"] for r in real}
    assert {"Violation", "Warning"} <= severities, severities
    entries = [entry_for(register, r) for r in real]
    problems, verdict = validator.gate(realist_record, entries, TODAY)
    assert problems == [] and verdict["passed"], verdict["new"][:3]

    swapped = entries[1:] + [entry_for(register, dict(
        real[0], focus=real[0]["focus"] + "Elsewhere"))]
    _, verdict = validator.gate(realist_record, swapped, TODAY)
    assert not verdict["passed"]
    assert [r["focus"] for r in verdict["new"]] == [real[0]["focus"]]
    assert [e["focus"] for e in verdict["stale"]] == [
        real[0]["focus"] + "Elsewhere"]

    warning = next(r for r in real if r["severity"] == "Warning")
    _, verdict = validator.gate(
        realist_record, [e for e in entries
                         if e["digest"] != warning["digest"]
                         or e["focus"] != warning["focus"]], TODAY)
    assert verdict["failing"] == [warning], "an unrecorded warning passed"


def test_a_rung_that_cannot_fail_fails_the_gate_whatever_the_register(
        validator):
    record = {"rungs": {"a": {
        "evaluable": True, "can_still_fail": False,
        "blocked_by_missing_vocabulary": [],
        "corpus": {"detail": [], "warning_detail": [],
                   "vendored_detail": []}}}}
    problems, _ = validator.gate(record, [], TODAY)
    assert problems and "did not fire on the fixture" in problems[0]
    record["rungs"]["a"].update(evaluable=False,
                                blocked_by_missing_vocabulary=["CCO"])
    problems, _ = validator.gate(record, [], TODAY)
    assert problems and "cannot be evaluated" in problems[0]


def test_a_blocked_rung_exits_2_whatever_else_it_found(validator):
    """P-B2: a run that could not evaluate a rung exited 1, as a run with
    findings does, and so could not be told from one. 2 wins over 1,
    because a count that misses a rung is not the ontology's."""
    def record(evaluable, blocked):
        return {"evaluable_rungs": evaluable, "blocked_rungs": blocked}

    assert validator.exit_code(record(["a"], []), failed=False) == 0
    assert validator.exit_code(record(["a"], []), failed=True) == 1
    assert validator.exit_code(record(["a"], ["b"]), failed=True) == 2
    assert validator.exit_code(record(["a"], ["b"]), failed=False) == 2
    assert validator.exit_code(record([], []), failed=False) == 2


def test_a_blocked_rung_is_never_counted_as_zero_findings(validator):
    """The blocked rung's results stay out of the count, and the total is
    null rather than the evaluable rungs' count passed off as the whole."""
    def rung(evaluable, focus):
        return {"evaluable": evaluable, "can_still_fail": True,
                "blocked_by_missing_vocabulary": [] if evaluable else ["CCO"],
                "corpus": {"detail": [{"focus": focus, "shape": "urn:s",
                                       "message": "m",
                                       "severity": "Violation"}],
                           "warning_detail": [], "vendored_detail": []}}

    record = {"rungs": {"a": rung(True, "urn:a"), "b": rung(False, "urn:b")},
              "evaluable_rungs": ["a"], "blocked_rungs": ["b"]}
    assert validator.finding_count(record) == {
        "total": None, "from_evaluable_rungs": 1, "not_counted_from": ["b"]}
    record["rungs"]["b"] = rung(True, "urn:b")
    record.update(evaluable_rungs=["a", "b"], blocked_rungs=[])
    assert validator.finding_count(record) == {
        "total": 2, "from_evaluable_rungs": 2, "not_counted_from": []}


def test_a_run_without_its_vocabulary_says_so_and_exits_2(
        validator, tmp_path, monkeypatch, capsys):
    """The WP6 case, reproduced: a corpus naming CCO, measured with no
    extract in scope. The gate, the report and --propose all exit 2, the
    summary names the blocked rungs, and the JSON's total is null."""
    import json

    corpus = tmp_path / "corpus.ttl"
    corpus.write_bytes((DIRTY % "https://example.org/blocked#").encode())
    monkeypatch.setattr(validator.layout, "ontology_files", lambda: [corpus])
    monkeypatch.setattr(validator.layout, "vendored_files", lambda: [])

    assert validator.main(["--gate"]) == 2
    out = capsys.readouterr().out
    out_json = tmp_path / "report.json"
    assert validator.main(["-o", str(out_json)]) == 2
    report_out = capsys.readouterr().out
    record = json.loads(out_json.read_text(encoding="utf-8"))

    blocked = record["blocked_rungs"]
    assert blocked, "nothing was blocked without the extracts"
    for text in (out, report_out):
        line = next(l for l in text.splitlines() if "INCOMPLETE" in l)
        for name in blocked:
            assert name in line, (name, line)
    assert record["findings"]["total"] is None
    assert record["findings"]["not_counted_from"] == blocked

    # Proposed entries would miss the blocked rung's findings too.
    assert validator.main(["--propose"]) == 2
    assert "INCOMPLETE" in capsys.readouterr().err
    # A selection refused on such a run says that the rung did not run:
    # its value may be one of the findings that are missing (P-A6).
    assert validator.main(["--propose", "--rule", "urn:not:run"]) == 2
    err = capsys.readouterr().err
    assert "CANNOT PROPOSE" in err and "INCOMPLETE" in err, err


def test_the_report_holds_every_finding(validator, benchmark_module,
                                        tmp_path, monkeypatch):
    """T20: the JSON once kept 20 warnings of BPO's hundreds. On a
    200-class benchmark the annotation profile alone gives one warning a
    class; every one is in the report, and so is every planted defect."""
    import json

    corpus = tmp_path / "benchmark.ttl"
    corpus.write_bytes(benchmark_module.generate(200, 280).serialize(
        format="turtle", encoding="utf-8"))
    monkeypatch.setattr(validator.layout, "ontology_files",
                        lambda: [corpus])
    out = tmp_path / "report.json"
    validator.main(["-o", str(out)])
    record = json.loads(out.read_text(encoding="utf-8"))
    total = 0
    for name, rung in record["rungs"].items():
        corpus_part = rung["corpus"]
        assert len(corpus_part["detail"]) == \
            corpus_part["against_authored_terms"], name
        assert len(corpus_part["warning_detail"]) == \
            corpus_part["warnings_against_authored_terms"], name
        total += len(corpus_part["warning_detail"])
    assert total > 200, "the benchmark gave %d warnings" % total
    focused = {(name, (v["focus"] or "").rsplit("#", 1)[-1])
               for name, rung in record["rungs"].items()
               for v in rung["corpus"]["detail"]
               + rung["corpus"]["warning_detail"]}
    for planted, expected in benchmark_module.PLANTED.items():
        assert (expected, planted) in focused, planted


def test_the_validator_reports_progress_on_stderr(validator, capsys,
                                                  monkeypatch):
    """Over the fixtures alone: the ladder on a project's corpus is
    minutes, and what is tested is where the progress goes."""
    monkeypatch.setattr(validator.layout, "ontology_files", lambda: [])
    validator.main([])
    captured = capsys.readouterr()
    for name in validator.shape_sets():
        assert "%s: the corpus" % name in captured.err, name
    assert "... " not in captured.out


@pytest.fixture(scope="module")
def benchmark_module():
    return load_tool("t_findings_benchmark", "tools/ontology/benchmark.py")


# ------------------------------------------------------- the linter


DIRTY = """@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix cco: <https://www.commoncoreontologies.org/> .
@prefix : <%s> .

:Thing a owl:Class ;
    rdfs:subClassOf cco:Organization ;
    rdfs:subClassOf :NothingDeclaresThis .
"""


def test_an_accepted_lint_finding_passes(linter, project, tmp_path,
                                         monkeypatch, capsys):
    """T5: with its entries, a file with lint findings exits 0; take one
    away and it exits 1, naming only the unaccepted one."""
    path = tmp_path / "dirty.ttl"
    path.write_bytes((DIRTY % project.namespace()).encode("utf-8"))
    records = linter.lint([path])
    assert {r["type"] for r in records} >= {"readable_label",
                                            "dangling_ref"}, records
    root = linter.layout.repository_root()
    new = linter.verdict_of(records, root, complete=False)["new"]
    entries = yaml.safe_load(linter.findings.propose(
        new, "planted", "the suite", "2027-01-01"))
    monkeypatch.setattr(linter.findings, "load", lambda root=None: entries)
    assert linter.main([str(path)]) == 0
    capsys.readouterr()

    kept = [e for e in entries if e["rule"] != "dangling_ref"]
    monkeypatch.setattr(linter.findings, "load", lambda root=None: kept)
    assert linter.main([str(path)]) == 1
    out = capsys.readouterr().out
    assert "dangling_ref" in out and "readable_label" not in out, out


def test_a_lint_finding_keeps_its_identity_when_its_line_moves(
        linter, project, tmp_path):
    path = tmp_path / "dirty.ttl"
    path.write_bytes((DIRTY % project.namespace()).encode("utf-8"))
    root = linter.layout.repository_root()
    before = linter.register_findings(linter.lint([path]), root)
    path.write_bytes(("\n\n# moved\n" + DIRTY % project.namespace())
                     .encode("utf-8"))
    after = linter.register_findings(linter.lint([path]), root)
    assert {f["digest"] for f in before} == {f["digest"] for f in after}
    assert [r["record"]["line"] for r in before] != \
        [r["record"]["line"] for r in after]


def test_a_stale_lint_entry_fails_over_the_whole_scope(linter, register,
                                                       monkeypatch):
    gone = entry_for(register, register.finding(
        "iri_lint", "ontology/gone.ttl", "urn:gone", "dangling_ref",
        "dangling_ref urn:gone", "Violation"))
    monkeypatch.setattr(linter.findings, "load", lambda root=None: [gone])
    assert linter.main([]) == 1


# ------------------------------------------------------- the workflow


def test_checks_runs_every_step(repo):
    """T5: every check step continues on error and has an id, and the
    last step runs always and fails on any step that did not succeed."""
    workflow = yaml.safe_load((repo / ".github/workflows/checks.yml")
                              .read_text(encoding="utf-8"))
    steps = workflow["jobs"]["checks"]["steps"]
    setup = [s for s in steps if "uses" in s
             or s.get("name") == "Install the pinned dependencies"]
    *checks, verdict = [s for s in steps if s not in setup]
    assert len(checks) >= 15, [s.get("name") for s in checks]
    for step in checks:
        assert step.get("continue-on-error") is True, step["name"]
        assert step.get("id"), step["name"]
    assert len({s["id"] for s in checks}) == len(checks)
    assert verdict["if"] == "always()"
    assert "toJSON(steps)" in verdict["env"]["STEPS"]
    assert 'outcome"] != "success"' in verdict["run"]
    assert "sys.exit(1)" in verdict["run"]
    names = " ".join(s["run"] for s in checks)
    for tool in ("tools/findings.py", "tools/ontology/validate.py --gate",
                 "tools/ontology/iri_lint.py"):
        assert tool in names, tool


def test_the_verdict_step_fails_on_any_failed_step(repo, tmp_path):
    """The verdict step's script, run on the outcomes GitHub would pass
    it: one failure among passes fails it and names the step."""
    import os
    import subprocess
    import sys

    workflow = yaml.safe_load((repo / ".github/workflows/checks.yml")
                              .read_text(encoding="utf-8"))
    script = workflow["jobs"]["checks"]["steps"][-1]["run"]
    body = script.split("<<'PY'\n", 1)[1].rsplit("PY", 1)[0]
    import textwrap
    path = tmp_path / "verdict.py"
    path.write_bytes(textwrap.dedent(body).encode("utf-8"))

    def outcome(steps):
        import json
        return subprocess.run(
            [sys.executable, str(path)], capture_output=True,
            env=dict(os.environ, STEPS=json.dumps(steps)))

    ok = {"layout": {"outcome": "success"}, "tests": {"outcome": "success"}}
    assert outcome(ok).returncode == 0
    bad = dict(ok, layout={"outcome": "failure"})
    result = outcome(bad)
    assert result.returncode == 1
    assert b"layout (failure)" in result.stdout
    skipped = dict(ok, tests={"outcome": "skipped"})
    assert outcome(skipped).returncode == 1


def test_a_proposal_is_yaml_and_nothing_else(validator, linter, capsys,
                                             monkeypatch):
    """--propose's stdout is pasted under `entries:`, so the report goes
    elsewhere. With every finding of a planted case new, the output
    parses as a list of entries."""
    monkeypatch.setattr(validator, "measure", lambda: {"rungs": {}})
    monkeypatch.setattr(validator, "register_findings", lambda record: [
        validator.findings.finding("validate", "validation.a", "urn:x",
                                   "urn:shape", "m", "Warning")])
    assert validator.main(["--propose"]) == 0
    out = capsys.readouterr().out
    entries = yaml.safe_load(out)
    assert isinstance(entries, list) and entries[0]["focus"] == "urn:x", out
    monkeypatch.setattr(linter, "lint", lambda paths, root=None: [])
    assert linter.main(["--propose"]) == 0
    assert yaml.safe_load(capsys.readouterr().out) is None


def test_a_lint_run_on_one_file_calls_no_entry_stale(linter, register,
                                                    project, tmp_path,
                                                    monkeypatch):
    """The Claude hook and the pre-commit hook lint what they are given;
    an entry for a file outside that run matches nothing there and is
    not stale."""
    path = tmp_path / "clean.ttl"
    path.write_bytes(("@prefix : <%s> .\n" % project.namespace())
                     .encode("utf-8"))
    elsewhere = entry_for(register, register.finding(
        "iri_lint", "ontology/other.ttl", "urn:other", "dangling_ref",
        "dangling_ref urn:other", "Violation"))
    monkeypatch.setattr(linter.findings, "load",
                        lambda root=None: [elsewhere])
    assert linter.main([str(path)]) == 0


# --------------------------------- --propose class by class (P-A6)
#
# Decision 50. BPO's port disposed of its findings in 17 classes, each
# with one reason, owner and classification, and had to call
# findings.propose() once per class because --propose took every new
# finding. A selection narrows it; a classification typed once by a named
# person is copied into the selected entries, checked by the register's
# own rules before anything is printed.

import argparse  # noqa: E402

PERSON = "Jane Doe (domain-expert)"
FILLED = ["--reason", "one class", "--owner", "the suite",
          "--review", "2027-01-01"]
JUDGED = ["--validity", "real", "--origin", "project",
          "--resolution", "accepted", "--classified-by", PERSON]


def parsed(register, *argv):
    ap = argparse.ArgumentParser()
    register.add_proposal_arguments(ap)
    return ap.parse_args(["--propose", *argv])


def planted(register):
    """Six new findings across two rules, two shape sets and four terms;
    one of them repeated, as a check can report it."""
    return [
        found(register, "urn:a", rule="urn:shape:label", message="a1"),
        found(register, "urn:a", rule="urn:shape:label", message="a1"),
        found(register, "urn:a", rule="urn:shape:genus", message="a2"),
        found(register, "urn:b", rule="urn:shape:label", message="b1",
              where="validation.b"),
        found(register, "urn:c", rule="urn:shape:genus", message="c1",
              severity="Warning"),
        found(register, "urn:d", rule="urn:shape:genus", message="d1",
              where="validation.b"),
    ]


def proposed(register, new, *argv, accepted=(), err=None):
    import io

    err = err if err is not None else io.StringIO()
    text = register.proposal(new, list(accepted), parsed(register, *argv),
                             err=err)
    return yaml.safe_load(text) or [], err


def refused(register, new, *argv, accepted=()):
    with pytest.raises(register.ProposalError) as caught:
        proposed(register, new, *argv, accepted=accepted)
    return str(caught.value)


def test_with_no_selector_a_proposal_is_as_before(register):
    """Decision 50, 1: with no new option the behaviour is unchanged --
    the same entries, byte for byte, and nothing more on stderr."""
    import io

    new = planted(register)
    for argv, before in (([], register.propose(new)),
                         (FILLED, register.propose(
                             new, "one class", "the suite", "2027-01-01"))):
        err = io.StringIO()
        text = register.proposal(new, [], parsed(register, *argv), err=err)
        assert text == before, argv
        assert err.getvalue() == "", err.getvalue()


def test_each_selector_selects_what_it_names(register):
    new = planted(register)
    cases = {
        ("--rule", "urn:shape:label"): {"a1", "b1"},
        ("--where", "validation.b"): {"b1", "d1"},
        ("--focus", "urn:a"): {"a1", "a2"},
    }
    for argv, expected in cases.items():
        entries, _ = proposed(register, new, *argv)
        assert {e["text"] for e in entries} == expected, (argv, entries)


def test_values_of_one_selector_widen_and_selectors_narrow(register):
    new = planted(register)
    entries, _ = proposed(register, new, "--focus", "urn:a",
                          "--focus", "urn:c")
    assert {e["text"] for e in entries} == {"a1", "a2", "c1"}
    entries, _ = proposed(register, new, "--focus", "urn:a",
                          "--focus", "urn:c", "--rule", "urn:shape:genus")
    assert {e["text"] for e in entries} == {"a2", "c1"}
    entries, _ = proposed(register, new, "--rule", "urn:shape:genus",
                          "--where", "validation.b")
    assert {e["text"] for e in entries} == {"d1"}


def test_the_counts_say_what_was_left_out(register):
    new = planted(register)
    _, err = proposed(register, new, "--rule", "urn:shape:genus")
    assert ("3 of 5 distinct new finding(s) selected; 2 not selected, "
            "still new"
            in err.getvalue()), err.getvalue()


def test_a_value_matching_nothing_is_refused(register):
    new = planted(register)
    said = refused(register, new, "--rule", "urn:shape:label",
                   "--rule", "urn:shape:typo")
    assert "--rule urn:shape:typo matches no new finding" in said, said
    assert "urn:shape:label" not in said, "a value that matches is named"
    said = refused(register, new, "--focus", "urn:entered",
                   accepted=[found(register, "urn:entered")])
    assert "--focus urn:entered matches only findings already in the " \
           "register" in said, said


def test_an_empty_selection_is_refused(register):
    """Each value matches some finding; together they match none."""
    new = planted(register)
    said = refused(register, new, "--focus", "urn:b",
                   "--rule", "urn:shape:genus")
    assert "no new finding matches --rule urn:shape:genus and --focus " \
           "urn:b together" in said, said


def test_a_focus_file_lists_terms(register, tmp_path):
    new = planted(register)
    path = tmp_path / "class.txt"
    path.write_bytes(b"# the unsure ones\n\nurn:b\n  urn:d  \n")
    entries, _ = proposed(register, new, "--focus-file", str(path),
                          "--focus", "urn:b")
    assert {e["text"] for e in entries} == {"b1", "d1"}
    for content, said in ((b"urn:b\nnot an iri\n", "line 2, 'not an iri'"),
                          (b"# only a comment\n", "lists no IRI"),
                          (b"\xff\xfe", "cannot be read")):
        path.write_bytes(content)
        got = refused(register, new, "--focus-file", str(path))
        assert said in got, (content, got)
    got = refused(register, new, "--focus-file", str(tmp_path / "absent"))
    assert "cannot be read" in got, got


def test_selected_entries_accept_exactly_the_selection(register):
    """Pasted in, the selected entries are accepted; every other finding
    is still new, and a Warning among them still fails the gate."""
    new = planted(register)
    entries, _ = proposed(register, new, "--rule", "urn:shape:label",
                          *FILLED, *JUDGED)
    assert register.problems_of(entries, version=2) == []
    verdict = register.judge("validate", new, entries, today=TODAY)
    assert {r["message"] for r in verdict["new"]} == {"a2", "c1", "d1"}
    assert not verdict["passed"]
    assert {r["message"] for r in verdict["failing"]} == {"a2", "c1", "d1"}


def test_class_by_class_the_register_fills_and_the_gate_passes(register):
    """Three classes, each proposed once and pasted in: the gate passes
    at the end, and no finding is entered twice."""
    new = planted(register)
    classes = [
        ["--rule", "urn:shape:label", *FILLED, *JUDGED],
        ["--focus", "urn:a", "--rule", "urn:shape:genus", *FILLED,
         "--validity", "false-alarm", "--origin", "template",
         "--resolution", "reported", "--reference", "issue 7",
         "--classified-by", "A. Person (ontologist)"],
        ["--focus", "urn:c", "--focus", "urn:d", *FILLED,
         "--validity", "unsure", "--origin", "unknown",
         "--resolution", "deferred", "--classified-by", PERSON],
    ]
    entries = []
    for argv in classes:
        accepted = register.judge("validate", new, entries,
                                  today=TODAY)["accepted"]
        still = [r for r in new if r not in accepted]
        got, _ = proposed(register, still, *argv, accepted=accepted)
        entries.extend(got)
    assert register.problems_of(entries, version=2) == []
    verdict = register.judge("validate", new, entries, today=TODAY)
    assert verdict["passed"] and not verdict["new"], verdict
    assert len(entries) == 5


def test_without_a_classification_the_placeholders_stay(register):
    new = planted(register)
    entries, _ = proposed(register, new, "--rule", "urn:shape:label",
                          *FILLED)
    got = register.problems_of(entries)
    assert sum("placeholder" in p for p in got) == 4 * len(entries), got


def test_a_given_classification_is_recorded_and_counted(register):
    new = planted(register)
    entries, err = proposed(register, new, "--rule", "urn:shape:genus",
                            *FILLED, *JUDGED)
    for entry in entries:
        assert {k: entry[k] for k in register.CLASSIFICATION} == {
            "validity": "real", "origin": "project",
            "resolution": "accepted", "classified_by": PERSON}
        assert "reference" not in entry
    assert ("3 entries given the classification validity real, origin "
            "project, resolution accepted, by " + PERSON) in err.getvalue()


def test_a_classification_is_given_whole(register):
    new = planted(register)
    for drop in register.CLASSIFICATION:
        flag = "--" + drop.replace("_", "-")
        argv = list(JUDGED)
        index = argv.index(flag)
        del argv[index:index + 2]
        said = refused(register, new, *FILLED, *argv)
        assert "given whole or not at all: %s is missing" % flag in said, \
            said
    said = refused(register, new, *FILLED, "--reference", "issue 7")
    assert "are missing" in said, said


def test_a_classified_entry_needs_its_reason_owner_and_review(register):
    new = planted(register)
    for key in ("reason", "owner", "review"):
        argv = list(FILLED)
        index = argv.index("--" + key)
        del argv[index:index + 2]
        said = refused(register, new, *argv, *JUDGED)
        assert "--%s also required with a classification" % key in said, said


def test_origin_upstream_is_not_given_for_a_group(register):
    new = planted(register)
    argv = [v if v != "project" else "upstream" for v in JUDGED]
    said = refused(register, new, *FILLED, *argv)
    assert "origin upstream is not given for a group" in said, said


def test_the_register_rules_hold_before_anything_is_printed(register):
    """Every refusal is the register's own message, and no entry is
    printed when any would be refused."""
    new = planted(register)
    cco = register.upstream_ids()["CCO"]

    def judged(validity, origin, resolution, by=PERSON, *more):
        return [*FILLED, "--validity", validity, "--origin", origin,
                "--resolution", resolution, "--classified-by", by, *more]

    cases = [
        (judged("false-alarm", "project", "accepted"),
         "accepted requires validity real"),
        (judged("real", "project", "not-a-defect"),
         "not-a-defect requires validity false-alarm"),
        (judged("unsure", "project", "accepted"),
         "unsure requires resolution deferred"),
        (judged("real", "unknown", "accepted"),
         "origin unknown requires validity unsure"),
        (judged("false-alarm", "template", "reported"),
         "reported requires a reference"),
        (judged("right", "project", "accepted"),
         "validity 'right' is not one of"),
        (judged("real", "project", "accepted", "Jane Doe (oracle)"),
         "names the kind 'oracle'"),
        (judged("real", "project", "accepted", "Jane Doe"),
         "is not '<name> (<kind>)'"),
        (judged("real", "project", "accepted", "TODO <name> (<kind>)"),
         "still a placeholder"),
    ]
    for argv, said in cases:
        got = refused(register, new, "--rule", "urn:shape:label", *argv)
        assert said in got and "no entry is printed" in got, (said, got)
        assert "the finding urn:shape:label urn:a" in got, got
    argv = list(FILLED)
    argv[argv.index("2027-01-01")] = "2027-02-30"
    got = refused(register, new, *argv, *JUDGED)
    assert "is not a date" in got, got
    on_cco = [found(register, cco + "ont00001180", message="u1")]
    got = refused(register, on_cco, *FILLED, *JUDGED)
    assert "must name the upstream" in got, got


def test_the_validator_selects_on_the_command_line(validator, capsys,
                                                   monkeypatch):
    """The wiring: the validator's --propose passes its new and accepted
    findings, prints the entries, and exits 2 on a refusal with nothing
    on stdout."""
    register = validator.findings
    new = planted(register)
    entered = entry_for(register, found(register, "urn:old", rule="urn:x"))
    monkeypatch.setattr(validator, "measure", lambda: {"rungs": {}})
    monkeypatch.setattr(validator, "register_findings",
                        lambda record: new + [found(register, "urn:old",
                                                    rule="urn:x")])
    monkeypatch.setattr(register, "load", lambda root=None: [entered])
    assert validator.main(["--propose", "--rule", "urn:shape:label",
                           *FILLED, *JUDGED]) == 0
    out, err = capsys.readouterr()
    assert {e["text"] for e in yaml.safe_load(out)} == {"a1", "b1"}
    assert "2 of 5 distinct new finding(s) selected" in err, err
    assert "2 entries given the classification" in err, err
    assert validator.main(["--propose", "--focus", "urn:old"]) == 2
    out, err = capsys.readouterr()
    assert out == "" and "CANNOT PROPOSE: --focus urn:old matches only " \
        "findings already in the register" in err, (out, err)
    assert validator.main(["--propose"]) == 0
    out, _ = capsys.readouterr()
    assert out == register.propose(new) + "\n", "unchanged with no option"


def test_the_linter_selects_on_the_command_line(linter, capsys,
                                                monkeypatch):
    register = linter.findings
    new = [register.finding("iri_lint", "ontology/a.ttl", "urn:a",
                            "dangling_ref", "dangling_ref urn:a", "Violation"),
           register.finding("iri_lint", "ontology/a.ttl", "urn:b",
                            "readable_label", "readable_label urn:b",
                            "Warning")]
    monkeypatch.setattr(linter, "lint", lambda paths, root=None: [])
    monkeypatch.setattr(linter, "register_findings",
                        lambda records, root=None: new)
    monkeypatch.setattr(register, "load", lambda root=None: [])
    assert linter.main(["--propose", "--rule", "readable_label"]) == 0
    out, err = capsys.readouterr()
    assert [e["focus"] for e in yaml.safe_load(out)] == ["urn:b"], out
    assert "1 of 2 distinct new finding(s) selected" in err, err
    assert linter.main(["--propose", "--where", "ontology/b.ttl"]) == 2
    out, err = capsys.readouterr()
    assert out == "" and "CANNOT PROPOSE" in err, (out, err)
    assert linter.main(["--propose"]) == 0
    out, _ = capsys.readouterr()
    assert out == register.propose(new) + "\n", "unchanged with no option"
