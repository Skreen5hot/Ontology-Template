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
    assert sum("placeholder" in p for p in got) == 3, got
    filled = yaml.safe_load(register.propose(records, "r", "o",
                                             "2027-01-01"))
    assert register.problems_of(filled) == []


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
