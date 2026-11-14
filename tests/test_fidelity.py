# SPDX-License-Identifier: MIT
"""Conceptual fidelity (P6, template decisions 42 and 43).

Each refusal has a planted case refused by name and a near miss that
passes, on a small project built in a temporary directory with its own
model, module, shapes, competency questions, decision records and git
history. Decision 42's amendments are among them: an anchor resolves to
one place or is refused until qualified, and declared anchors are never
reported as read from the file; a departure cites a decision that
references every element; a `preserves` row is signed in a kind
config/review.yaml declares (decision 43); the axiom digest is blind to
serialization order and moves with any asserted axiom; the upstream
context is pinned; a prohibiting element names a guard that runs, or
why it has none; debt is held only at the stage and the release; an
adoption baseline is reproducible, and a term whose age cannot be told
is held, never exempted; and with no approved model the report says so,
never that fidelity passed.

The BCO's three expected changes are fixtures: a basis formalized with
has material basis, a change in meaning that needs its decision; a
conditional designation traced to a shape, with no OWL term; a
closed-world question traced to a competency question.
"""

from __future__ import annotations

import copy
import os
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from conftest import ROOT, load_tool


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_fidelity", "tools/fidelity.py")


NS = "https://example.org/onto#"
MODULE = "ontology/core.ttl"
OTHER = "ontology/extra.ttl"
SHAPES = "shapes/core_shapes.ttl"
MODEL = "docs/models/CM-01.md"
APPROVAL = "docs/decisions/2026-11-10-cm01-approved.md"
DECISION = "docs/decisions/2026-11-12-departures.md"

HEAD = """@prefix ex: <https://example.org/onto#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix obo: <http://purl.obolibrary.org/obo/> .
"""

TURTLE = HEAD + """<https://example.org/onto> a owl:Ontology .
ex:Organization a owl:Class ;
    rdfs:label "organization" ;
    skos:definition "An organized group of agents." ;
    rdfs:subClassOf obo:BFO_0000040 .
ex:BusinessCapability a owl:Class ;
    rdfs:label "business capability" ;
    rdfs:subClassOf [ a owl:Restriction ;
                      owl:onProperty ex:bornBy ;
                      owl:someValuesFrom ex:Organization ] .
ex:bears a owl:ObjectProperty ;
    rdfs:domain ex:Organization ;
    rdfs:range ex:BusinessCapability ;
    owl:inverseOf ex:bornBy .
ex:bornBy a owl:ObjectProperty .
"""

EXTRA = HEAD + "<https://example.org/onto/extra> a owl:Ontology .\n"

SHAPE_TEXT = """@prefix ex: <https://example.org/onto#> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
ex:DesignationShape a sh:NodeShape ;
    sh:targetClass ex:BusinessCapability .
ex:AdequacyGuard a sh:NodeShape ;
    sh:targetClass ex:Organization .
"""

MODEL_TEXT = """# CM-01 — Example model

## 3. Patterns

### P1 — Capability and bearer

The bearer pattern.

```mermaid
flowchart LR
### P9 — not a heading
```

### P2 — Realization

## 4. Concept descriptions

### Organization

- **Description.** An organized group.

### Business Capability

- **Description.** What an organization can do.

## 5. Relationship descriptions

| Id | Name | From | To |
| --- | --- | --- | --- |
| RL-01 | bears | Organization | Business Capability |
| RL-02 | designated | Business Capability | Function |

## 6. Conceptual boundaries

| Distinction | Kept apart |
| --- | --- |
| Able / permitted | Capacity is not permission. |
| Capacity / exercise | Adequacy is never inferred from components. |

## 7. Decision points

### DP-1 — The grounding

#### Options

- **A-01** One option.

### DP-2 — Admission

#### Options

- **A-02** Another.
"""

QUESTION = {"id": "CQ-001", "question": "Which capabilities?",
            "status": "answerable", "depends_on": [], "examples": [],
            "query": "SELECT ?x WHERE { ?x ?p ?o }",
            "expect": {"rows": []}}

UPSTREAM = {"version": 1, "sources": [{"id": "bfo", "commit": "a" * 40}]}

COVER = ["heading:§3/P*", "heading:§4/*", "row:§5/RL-*"]


def model(**extra):
    entry = {"id": "CM-01", "file": MODEL, "approved_by": APPROVAL,
             "cover": list(COVER)}
    entry.update(extra)
    return entry


def rows():
    """A trace covering every covered element and every term."""
    return [
        {"elements": ["CM-01#RL-01"],
         "formalized_as": {"terms": ["ex:bears", "ex:bornBy"]},
         "fidelity": "preserves", "reviewed_by": "A. Onto (ontologist)"},
        {"elements": ["CM-01#Organization"],
         "formalized_as": {"terms": ["ex:Organization"]},
         "fidelity": "preserves",
         "reviewed_by": "A. Damiano (proxy-domain-expert)"},
        {"elements": ["CM-01#Business Capability"],
         "formalized_as": {"terms": [NS + "BusinessCapability"]},
         "fidelity": "preserves", "reviewed_by": "A. Onto (ontologist)"},
        {"elements": ["CM-01#RL-02"],
         "formalized_as": {"shapes": ["ex:DesignationShape"]},
         "fidelity": "not-formalized", "decision": DECISION},
        {"elements": ["CM-01#P1", "CM-01#P2"],
         "formalized_as": {"questions": ["CQ-001"]},
         "fidelity": "preserves", "reviewed_by": "A. Onto (ontologist)"},
    ]


def project(root, trace_rows=None, settings=None, files=None, pin=True,
            untracked=(), commit_date=None):
    """A project with this model registered, this trace, a module, shapes,
    questions and decision records; every digest pinned to the files as
    written unless pin is False. All tracked but the untracked ones;
    committed if commit_date is given."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "config/review.yaml", root / "config/review.yaml")
    config = {"version": 1, "models": [model()]}
    config.update(settings or {})
    write = {
        "config/fidelity.yaml": yaml.safe_dump(config, allow_unicode=True),
        "config/upstream-sources.yaml": yaml.safe_dump(UPSTREAM),
        MODULE: TURTLE,
        OTHER: EXTRA,
        SHAPES: SHAPE_TEXT,
        MODEL: MODEL_TEXT,
        "competency-questions/CQ-001.yaml": yaml.safe_dump(QUESTION),
        "competency-questions/CQ-002.yaml": yaml.safe_dump(
            dict(QUESTION, id="CQ-002", status="draft")),
        APPROVAL: "# CM-01 approved\n\nApproves CM-01.\n",
        DECISION: "# Departures\n\nCM-01#RL-02 is a shape, not OWL.\n"
                  "CM-01#RL-01 changes, as recorded.\n",
    }
    write.update(files or {})
    for name, text in write.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(text.encode("utf-8"))
    trace_rows = copy.deepcopy(rows() if trace_rows is None else trace_rows)
    write_trace(root, trace_rows, pin)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    for name in untracked:
        subprocess.run(["git", "rm", "-q", "--cached", name], cwd=root,
                       check=True)
    if commit_date:
        commit(root, commit_date)
    return root


def write_trace(root, trace_rows, pin=True, tool_=None):
    tool_ = tool_ or load_tool("t_fidelity_pin", "tools/fidelity.py")
    data = {"format_version": 1, "models": {}, "upstream_sha256": None,
            "rows": trace_rows}
    if pin:
        graph = tool_.merged([root / MODULE, root / OTHER])
        for row in trace_rows:
            terms = (row.get("formalized_as") or {}).get("terms") or []
            if terms and "axioms_sha256" not in row:
                row["axioms_sha256"] = tool_.axiom_digest(
                    graph, [tool_.expand(t, NS, "ex") for t in terms])
        data["models"] = {"CM-01": tool_.sha256_of(root / MODEL)}
        data["upstream_sha256"] = tool_.upstream_digest(root)
    (root / "ontology").mkdir(parents=True, exist_ok=True)
    (root / "ontology/trace.yaml").write_bytes(
        yaml.safe_dump(data, allow_unicode=True).encode("utf-8"))


def commit(root, date):
    env = dict(os.environ, GIT_COMMITTER_DATE=date + "T12:00:00",
               GIT_AUTHOR_DATE=date + "T12:00:00")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@invalid",
                    "commit", "-q", "-m", "c"], cwd=root, check=True, env=env)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                          capture_output=True, text=True).stdout.strip()


def check(tool, root):
    return tool.check(root, modules=[root / MODULE, root / OTHER],
                      shapes=[root / SHAPES], namespace=NS, prefix="ex")


def said(result, text):
    return any(text in p for p in result["problems"])


def debt(result):
    return {(d["kind"], d["item"]) for d in result["debt"]}


def edit_row(number, **change):
    trace_rows = rows()
    trace_rows[number].update(change)
    return trace_rows


# ----------------------------------------------------------- a clean one


def test_a_complete_trace_passes_and_owes_nothing(tool, tmp_path):
    result = check(tool, project(tmp_path))
    assert result["problems"] == [] and result["debt"] == []
    assert result["status"] == "applicable"
    counts = result["counts"]
    assert counts["covered"] == 6          # P1, P2, two concepts, two RLs
    assert counts["untraced_covered"] == 0
    assert counts["preserves"] == 5 and counts["not_formalized"] == 1
    assert counts["changes"] == 0 and counts["terms"] == 4


def test_the_template_record_is_not_yet_established(tool):
    result = tool.check(ROOT)
    assert result["problems"] == [] and result["debt"] == []
    assert result["status"] == "not-established"


def test_two_runs_give_the_same_result(tool, tmp_path):
    root = project(tmp_path)
    assert check(tool, root) == check(tool, root)


# -------------------------------------------------------- applicability


def test_with_no_model_nothing_is_owed_and_nothing_passes(tool, tmp_path,
                                                          monkeypatch,
                                                          capsys):
    root = project(tmp_path, trace_rows=[], settings={"models": []},
                   pin=False)
    result = check(tool, root)
    assert result["status"] == "not-established" and result["debt"] == []
    monkeypatch.setattr(tool.layout, "repository_root", lambda: root)
    assert tool.main([]) == 0
    out = capsys.readouterr().out
    assert "not yet established" in out and "nothing was traced" in out


def test_not_applicable_needs_its_decision(tool, tmp_path):
    root = project(tmp_path, trace_rows=[], pin=False, settings={
        "models": [], "applicable": False, "decided_by": APPROVAL})
    result = check(tool, root)
    assert result["status"] == "not-applicable" and result["problems"] == []
    root = project(tmp_path / "b", trace_rows=[], pin=False, settings={
        "models": [], "applicable": False})
    assert said(check(tool, root), "applicable is false, and decided_by "
                                   "None is not a tracked decision record")


def test_not_applicable_with_models_is_refused(tool, tmp_path):
    root = project(tmp_path, settings={"applicable": False,
                                       "decided_by": APPROVAL})
    assert said(check(tool, root), "applicable is false and models are "
                                   "registered")


def test_decided_by_without_applicable_false_is_refused(tool, tmp_path):
    root = project(tmp_path, settings={"decided_by": APPROVAL})
    assert said(check(tool, root), "decided_by is set and applicable is "
                                   "not false")


def test_rows_with_no_model_are_refused(tool, tmp_path):
    root = project(tmp_path, settings={"models": []}, pin=False)
    assert said(check(tool, root), "has rows and no approved model is "
                                   "registered")


# --------------------------------------------------------------- anchors


def names(tool, text=MODEL_TEXT):
    return [(a.kind, a.names[0], a.line) for a in tool.markdown_anchors(text)]


def test_markdown_anchors_are_headings_rows_and_bold_items(tool):
    found = names(tool)
    kinds = {(k, n) for k, n, _ in found}
    assert ("heading", "P1") in kinds and ("heading", "Organization") in kinds
    assert ("row", "RL-01") in kinds and ("row", "Able / permitted") in kinds
    assert ("item", "Description") in kinds and ("item", "A-01") in kinds
    assert ("heading", "3. Patterns") in kinds


def test_fenced_code_and_header_rows_are_not_anchors(tool):
    kinds = {(k, n) for k, n, _ in names(tool)}
    assert ("heading", "P9") not in kinds
    assert ("row", "Id") not in kinds and ("row", "Distinction") not in kinds


def test_a_numbered_section_answers_to_its_number(tool):
    anchors = tool.markdown_anchors(MODEL_TEXT)
    [found] = tool.resolve(anchors, "§6")
    assert found.names == ["6. Conceptual boundaries", "§6"]


@pytest.mark.parametrize("reference", [
    "§7/DP-1/Options", "DP-1/Options", "§7/DP-2/Options",
    "Able / permitted", "§6/Able / permitted", "A-01"])
def test_a_qualified_or_unique_anchor_resolves_once(tool, reference):
    anchors = tool.markdown_anchors(MODEL_TEXT)
    assert len(tool.resolve(anchors, reference)) == 1


@pytest.mark.parametrize("reference, count", [
    ("Options", 2), ("Description", 2), ("§7/Options", 2),
    ("§5/Options", 0), ("P9", 0), ("DP-3", 0),
    ("DP-2/DP-1/Options", 0), ("DP-1/§7/Options", 0)])
def test_an_ambiguous_or_absent_anchor_does_not_resolve_once(tool,
                                                             reference,
                                                             count):
    anchors = tool.markdown_anchors(MODEL_TEXT)
    assert len(tool.resolve(anchors, reference)) == count


def test_an_ambiguous_reference_is_refused_until_qualified(tool, tmp_path):
    trace_rows = rows() + [{"elements": ["CM-01#Options"],
                            "formalized_as": {"questions": ["CQ-001"]},
                            "fidelity": "preserves",
                            "reviewed_by": "A. Onto (ontologist)"}]
    result = check(tool, project(tmp_path, trace_rows))
    assert said(result, "row 6: CM-01#Options names 2 places in %s" % MODEL)
    trace_rows[-1]["elements"] = ["CM-01#§7/DP-1/Options"]
    assert check(tool, project(tmp_path / "b", trace_rows))["problems"] == []


@pytest.mark.parametrize("reference, message", [
    ("CM-01#P9", "CM-01#P9 names nothing in %s" % MODEL),
    ("CM-02#P1", "names model CM-02, which config/fidelity.yaml does not "
                 "register"),
    ("P1", "P1 is not <model id>#<anchor>"),
    ("CM-01#", "CM-01# is not <model id>#<anchor>"),
])
def test_a_bad_reference_is_refused(tool, tmp_path, reference, message):
    trace_rows = edit_row(4, elements=["CM-01#P1", "CM-01#P2", reference])
    assert said(check(tool, project(tmp_path, trace_rows)), message)


def test_declared_anchors_resolve_and_are_reported_as_declared(tool,
                                                               tmp_path):
    root = project(tmp_path, files={"docs/models/CM-01.txt": "plain\n"},
                   settings={"models": [model(
                       file="docs/models/CM-01.txt",
                       anchors=["P1", "P2", "Organization",
                                "Business Capability", "RL-01", "RL-02"],
                       cover=["P*"])]}, pin=False)
    write_trace(root, rows(), pin=True)
    result = check(tool, root)
    assert said(result, "models.CM-01") is False
    assert result["counts"]["declared_models"] == ["CM-01"]


def test_a_model_not_in_markdown_without_anchors_is_refused(tool, tmp_path):
    root = project(tmp_path, files={"docs/models/CM-01.txt": "plain\n"},
                   settings={"models": [model(file="docs/models/CM-01.txt")]})
    assert said(check(tool, root), "is not Markdown and declares no anchors")


def test_a_declared_anchor_twice_is_refused(tool, tmp_path):
    root = project(tmp_path, settings={"models": [model(
        anchors=["P1", "P1", "P2"])]})
    assert said(check(tool, root), "declares the anchor P1 twice")


# ---------------------------------------------------------------- models


@pytest.mark.parametrize("change, message", [
    ({"file": "docs/models/none.md"}, "its file 'docs/models/none.md' does "
                                      "not exist"),
    ({"approved_by": "docs/models/CM-01.md"}, "approved_by "
                                              "'docs/models/CM-01.md' is "
                                              "not a tracked decision"),
    ({"approved_by": DECISION}, "%s, its approval, does not cite CM-01"
                                % DECISION),
    ({"id": "CM#01"}, "is not a model identifier"),
    ({"version": 2}, "unknown field(s): version"),
    ({"cover": "P*"}, "cover is not a list"),
])
def test_a_bad_model_entry_is_refused(tool, tmp_path, change, message):
    files = {DECISION: "# Departures\n\nNothing cited.\n"} \
        if change.get("approved_by") == DECISION else None
    root = project(tmp_path, settings={"models": [model(**change)]},
                   files=files)
    assert said(check(tool, root), message)


def test_an_untracked_approval_is_refused(tool, tmp_path):
    root = project(tmp_path, untracked=[APPROVAL])
    assert said(check(tool, root), "approved_by %r is not a tracked "
                                   "decision record" % APPROVAL)


def test_a_model_registered_twice_is_refused(tool, tmp_path):
    root = project(tmp_path, settings={"models": [model(), model()]})
    assert said(check(tool, root), "model CM-01 is registered twice")


# --------------------------------------------------------------- targets


@pytest.mark.parametrize("field, value, message", [
    ("terms", "obo:BFO_0000040", "obo:BFO_0000040 is not in the authored "
                                 "namespace"),
    ("terms", "ex:Nowhere", "ex:Nowhere is declared in no authored module"),
    ("shapes", "ex:NoShape", "ex:NoShape is not a shape any shape set "
                             "declares"),
    ("questions", "CQ-009", "CQ-009 is not a competency question"),
])
def test_a_target_that_is_not_there_is_refused(tool, tmp_path, field, value,
                                               message):
    trace_rows = rows()
    trace_rows[2]["formalized_as"].setdefault(field, []).append(value)
    trace_rows[2]["axioms_sha256"] = "c" * 64
    assert said(check(tool, project(tmp_path, trace_rows)), message)


def test_an_unknown_target_field_is_refused(tool, tmp_path):
    trace_rows = edit_row(4, formalized_as={"questions": ["CQ-001"],
                                            "axioms": ["x"]})
    assert said(check(tool, project(tmp_path, trace_rows)),
                "formalized_as has unknown field(s): axioms")


# -------------------------------------------------------------- fidelity


def test_a_change_in_meaning_with_its_decision_passes(tool, tmp_path):
    """BCO's first expected change: a basis formalized with has material
    basis, which entails Disposition, a commitment the model does not
    make. A change, decided."""
    trace_rows = edit_row(0, fidelity="changes", decision=DECISION)
    result = check(tool, project(tmp_path, trace_rows))
    assert result["problems"] == [] and result["counts"]["changes"] == 1


@pytest.mark.parametrize("number, value", [(0, "changes"),
                                           (3, "not-formalized")])
def test_a_departure_without_a_decision_is_refused(tool, tmp_path, number,
                                                   value):
    trace_rows = edit_row(number, fidelity=value, decision=None)
    assert said(check(tool, project(tmp_path, trace_rows)),
                "row %d is %s and names no decision" % (number + 1, value))


def test_a_decision_must_cite_every_element(tool, tmp_path):
    trace_rows = edit_row(3, elements=["CM-01#RL-02", "CM-01#P2"])
    result = check(tool, project(tmp_path, trace_rows))
    assert said(result, "decision %s does not cite CM-01#P2" % DECISION)


def test_a_longer_reference_is_not_a_citation(tool, tmp_path):
    root = project(tmp_path, files={
        DECISION: "# Departures\n\nCM-01#RL-020 is something else.\n"})
    assert said(check(tool, root), "does not cite CM-01#RL-02")


def test_an_untracked_decision_is_refused(tool, tmp_path):
    root = project(tmp_path, untracked=[DECISION])
    assert said(check(tool, root), "decision %s is not a tracked decision "
                                   "record" % DECISION)


def test_not_formalized_names_no_term(tool, tmp_path):
    trace_rows = edit_row(3, formalized_as={"terms": ["ex:bornBy"]},
                          axioms_sha256="c" * 64)
    assert said(check(tool, project(tmp_path, trace_rows)),
                "row 4 is not-formalized and names terms")


def test_not_formalized_may_name_nothing(tool, tmp_path):
    """Deliberately not represented anywhere: the decision says so."""
    trace_rows = edit_row(3, formalized_as={})
    assert check(tool, project(tmp_path, trace_rows))["problems"] == []


def test_a_closed_world_question_formalizes_an_element(tool, tmp_path):
    """BCO's third expected change: a question about a capability never
    exercised needs a closed-world check, a competency question."""
    trace_rows = rows()
    assert trace_rows[4]["formalized_as"] == {"questions": ["CQ-001"]}
    assert check(tool, project(tmp_path, trace_rows))["problems"] == []


def test_preserving_with_nothing_formalizing_it_is_refused(tool, tmp_path):
    trace_rows = edit_row(4, formalized_as={})
    assert said(check(tool, project(tmp_path, trace_rows)),
                "row 5 is preserves and names nothing that formalizes it")


@pytest.mark.parametrize("value, message", [
    ("keeps", "fidelity 'keeps' is not one of"),
    (None, "fidelity None is not one of"),
])
def test_an_unknown_fidelity_is_refused(tool, tmp_path, value, message):
    assert said(check(tool, project(tmp_path, edit_row(4, fidelity=value))),
                message)


# ------------------------------------------------------------- reviewers


@pytest.mark.parametrize("reviewer, message", [
    (None, "row 5 is preserves and names no reviewer"),
    ("A. Onto", "reviewed_by 'A. Onto' is not '<name> (<kind>)'"),
    ("A. Onto (domain-practitioner)", "names the kind domain-practitioner"),
    ("A. Damiano (architect)", "names the kind architect"),
    ("A. Damiano (rights-reviewer)", "names the kind rights-reviewer"),
])
def test_a_preserving_row_is_signed_by_an_allowed_kind(tool, tmp_path,
                                                       reviewer, message):
    trace_rows = edit_row(4, reviewed_by=reviewer)
    assert said(check(tool, project(tmp_path, trace_rows)), message)


@pytest.mark.parametrize("kind", ["ontologist", "domain-expert",
                                  "proxy-domain-expert"])
def test_the_default_kinds_may_sign(tool, tmp_path, kind):
    trace_rows = edit_row(4, reviewed_by="A. Person (%s)" % kind)
    assert check(tool, project(tmp_path, trace_rows))["problems"] == []


def test_a_project_may_change_the_reviewers(tool, tmp_path):
    root = project(tmp_path, edit_row(4, reviewed_by="A. D. (architect)"),
                   settings={"reviewers": ["architect", "ontologist",
                                           "proxy-domain-expert"]})
    assert check(tool, root)["problems"] == []


def test_a_reviewer_kind_review_yaml_does_not_declare_is_refused(tool,
                                                                 tmp_path):
    root = project(tmp_path, settings={"reviewers": ["domain-practitioner"]})
    assert said(check(tool, root), "reviewer kind domain-practitioner is "
                                   "not a kind config/review.yaml declares")


# --------------------------------------------------------------- digests


def test_terms_without_their_digest_are_refused(tool, tmp_path):
    root = project(tmp_path, pin=False)
    result = check(tool, root)
    assert said(result, "row 1 names terms and no axioms_sha256")
    assert said(result, "traces CM-01, whose digest ontology/trace.yaml "
                        "does not pin")
    assert said(result, "upstream_sha256 is not set")


@pytest.mark.parametrize("change, message", [
    ({"axioms_sha256": "XYZ"}, "axioms_sha256 is not 64 lowercase hex"),
])
def test_a_malformed_row_digest_is_refused(tool, tmp_path, change, message):
    assert said(check(tool, project(tmp_path, edit_row(0, **change))),
                message)


def test_a_digest_without_terms_is_refused(tool, tmp_path):
    trace_rows = edit_row(4, axioms_sha256="c" * 64)
    assert said(check(tool, project(tmp_path, trace_rows)),
                "row 5 gives axioms_sha256 and names no term")


def test_pins_for_an_unregistered_model_are_refused(tool, tmp_path):
    root = project(tmp_path)
    data = yaml.safe_load((root / "ontology/trace.yaml").read_text())
    data["models"]["CM-09"] = "d" * 64
    data["models"]["CM-01"] = "short"
    (root / "ontology/trace.yaml").write_bytes(yaml.safe_dump(data).encode())
    result = check(tool, root)
    assert said(result, "models pins CM-09, which config/fidelity.yaml does "
                        "not register")
    assert said(result, "models.CM-01 is not 64 lowercase hex digits")


def test_an_unknown_field_is_refused(tool, tmp_path):
    result = check(tool, project(tmp_path, edit_row(0, verdict="faithful")))
    assert said(result, "row 1 has unknown field(s): verdict")


# ---------------------------------------------- the fingerprint, as such


def fingerprint(tool, tmp_path, text, terms, name="m.ttl"):
    path = tmp_path / name
    path.write_bytes((HEAD + text).encode("utf-8"))
    return tool.axiom_digest(tool.merged([path]), [NS + t for t in terms])


BASE = """ex:A a owl:Class ;
    rdfs:label "a" ;
    skos:definition "An A." ;
    rdfs:subClassOf [ a owl:Restriction ; owl:onProperty ex:p ;
                      owl:someValuesFrom [ owl:unionOf ( ex:B ex:C ) ] ] .
ex:p a owl:ObjectProperty ;
    owl:propertyChainAxiom ( ex:q ex:r ) .
"""


@pytest.mark.parametrize("text", [
    # the same axioms, written another way
    """ex:p owl:propertyChainAxiom ( ex:q ex:r ) ; a owl:ObjectProperty .
ex:A rdfs:subClassOf _:r ; skos:definition "An A." ; a owl:Class .
_:r owl:someValuesFrom _:u ; owl:onProperty ex:p ; a owl:Restriction .
_:u owl:unionOf ( ex:C ex:B ) .
ex:A rdfs:label "a" .
""",
    # labels and comments are not axioms
    BASE.replace('rdfs:label "a"', 'rdfs:label "an a"; rdfs:comment "x"'),
    # an annotation on an axiom is not an axiom
    BASE + """[] a owl:Axiom ; owl:annotatedSource ex:A ;
   owl:annotatedProperty rdfs:subClassOf ; rdfs:comment "why" .
""",
])
def test_the_fingerprint_does_not_move_for_the_same_axioms(tool, tmp_path,
                                                           text):
    assert fingerprint(tool, tmp_path, BASE, ["A", "p"]) == fingerprint(
        tool, tmp_path, text, ["A", "p"], "n.ttl")


@pytest.mark.parametrize("text", [
    BASE.replace("someValuesFrom", "allValuesFrom"),
    BASE.replace("ex:B ex:C", "ex:B ex:D"),
    BASE.replace("( ex:q ex:r )", "( ex:r ex:q )"),     # a chain is ordered
    BASE.replace('"An A."', '"Another A."'),
    BASE + "ex:Z owl:disjointWith ex:A .\n",
    BASE + "ex:Z owl:equivalentClass ex:A .\n",
    BASE + "[] a owl:AllDisjointClasses ; owl:members ( ex:A ex:Z ) .\n",
    BASE + "[ owl:intersectionOf ( ex:Y ex:Z ) ] rdfs:subClassOf ex:A .\n",
    BASE + "ex:s owl:inverseOf ex:p .\n",
    BASE + "ex:p a owl:TransitiveProperty .\n",
    BASE + "ex:p rdfs:domain ex:A .\n",
    BASE + "ex:A owl:deprecated true .\n",
])
def test_the_fingerprint_moves_with_any_relevant_axiom(tool, tmp_path, text):
    assert fingerprint(tool, tmp_path, BASE, ["A", "p"]) != fingerprint(
        tool, tmp_path, text, ["A", "p"], "n.ttl")


def test_another_class_using_a_term_is_not_its_axiom(tool, tmp_path):
    more = BASE + "ex:Z rdfs:subClassOf ex:A .\n"
    assert fingerprint(tool, tmp_path, BASE, ["A"]) == fingerprint(
        tool, tmp_path, more, ["A"], "n.ttl")


def test_an_axiom_moved_to_another_module_does_not_move_it(tool, tmp_path):
    one = tmp_path / "one.ttl"
    one.write_bytes((HEAD + BASE).encode())
    a = tmp_path / "a.ttl"
    b = tmp_path / "b.ttl"
    a.write_bytes((HEAD + BASE.split("ex:p a")[0]).encode())
    b.write_bytes((HEAD + "ex:p a" + BASE.split("ex:p a")[1]).encode())
    iris = [NS + "A", NS + "p"]
    assert tool.axiom_digest(tool.merged([one]), iris) == \
        tool.axiom_digest(tool.merged([a, b]), iris)


# ----------------------------------------------------------------- stale


def test_a_changed_axiom_makes_its_row_stale(tool, tmp_path):
    root = project(tmp_path)
    (root / MODULE).write_bytes(TURTLE.replace(
        "owl:someValuesFrom ex:Organization",
        "owl:allValuesFrom ex:Organization").encode())
    result = check(tool, root)
    assert result["problems"] == []
    assert debt(result) == {("stale", "row 3")}
    assert "the axioms of %sBusinessCapability changed" % NS in \
        result["debt"][0]["why"]


def test_an_edited_model_makes_every_row_tracing_it_stale(tool, tmp_path):
    root = project(tmp_path)
    (root / MODEL).write_bytes((MODEL_TEXT + "\nA note.\n").encode())
    result = check(tool, root)
    assert result["problems"] == []
    assert debt(result) == {("stale", "row %d" % n) for n in range(1, 6)}


def test_a_new_upstream_pin_makes_rows_with_terms_stale(tool, tmp_path):
    root = project(tmp_path)
    (root / "config/upstream-sources.yaml").write_bytes(yaml.safe_dump(
        {"version": 1, "sources": [{"id": "bfo", "commit": "b" * 40}]})
        .encode())
    assert debt(check(tool, root)) == {("stale", "row %d" % n)
                                       for n in (1, 2, 3)}


def test_a_comment_in_the_upstream_pins_moves_nothing(tool, tmp_path):
    root = project(tmp_path)
    path = root / "config/upstream-sources.yaml"
    path.write_bytes(b"# a note\n" + path.read_bytes())
    assert check(tool, root)["debt"] == []


def test_a_label_change_is_not_stale(tool, tmp_path):
    root = project(tmp_path)
    (root / MODULE).write_bytes(TURTLE.replace(
        '"organization"', '"organisation"').encode())
    assert check(tool, root)["debt"] == []


def test_the_tool_never_rewrites_the_trace(tool, tmp_path):
    root = project(tmp_path)
    before = (root / "ontology/trace.yaml").read_bytes()
    (root / MODULE).write_bytes(TURTLE.replace("rdfs:domain",
                                               "rdfs:range").encode())
    check(tool, root)
    assert (root / "ontology/trace.yaml").read_bytes() == before


# -------------------------------------------------------------- coverage


def test_an_untraced_term_is_owed(tool, tmp_path):
    trace_rows = edit_row(0, formalized_as={"terms": ["ex:bears"]})
    result = check(tool, project(tmp_path, trace_rows))
    assert result["problems"] == []
    assert debt(result) == {("untraced", NS + "bornBy")}


def test_an_untraced_covered_element_is_owed(tool, tmp_path):
    result = check(tool, project(tmp_path, rows()[:4]))
    assert debt(result) == {("untraced", "CM-01#P1"),
                            ("untraced", "CM-01#P2")}
    assert result["counts"]["untraced_covered"] == 2


def test_an_element_outside_cover_is_not_owed(tool, tmp_path):
    root = project(tmp_path, rows()[:4],
                   settings={"models": [model(cover=COVER[1:])]})
    assert check(tool, root)["debt"] == []


def test_a_pattern_level_row_does_not_trace_what_it_encloses(tool, tmp_path):
    trace_rows = rows()[:3] + [{
        "elements": ["CM-01#§5"], "formalized_as": {},
        "fidelity": "not-formalized", "decision": DECISION}] + rows()[4:]
    root = project(tmp_path, trace_rows, files={
        DECISION: "# D\n\nCM-01#§5 is pattern-level.\n"})
    result = check(tool, root)
    assert result["problems"] == []
    assert ("untraced", "CM-01#RL-02") in debt(result)


def test_an_untraced_reference_is_qualified_when_it_recurs(tool, tmp_path):
    root = project(tmp_path, settings={"models": [model(
        cover=COVER + ["heading:§7/*/Options"])]})
    items = {d["item"] for d in check(tool, root)["debt"]}
    assert items == {"CM-01#DP-1/Options", "CM-01#DP-2/Options"}


# ---------------------------------------------------------------- guards


def prohibiting(**extra):
    return {"models": [model(prohibits=["CM-01#Capacity / exercise"],
                             **extra)]}


def guard_row(**extra):
    row = {"elements": ["CM-01#Capacity / exercise"],
           "formalized_as": {"shapes": ["ex:AdequacyGuard"]},
           "fidelity": "preserves", "reviewed_by": "A. Onto (ontologist)"}
    row.update(extra)
    return row


def test_a_prohibiting_element_is_owed_even_outside_cover(tool, tmp_path):
    result = check(tool, project(tmp_path, settings=prohibiting()))
    assert debt(result) == {("untraced", "CM-01#Capacity / exercise")}


@pytest.mark.parametrize("extra", [{"guards": ["ex:AdequacyGuard"]},
                                   {"guards": ["CQ-001"]},
                                   {"no_guard": "Needs a closed world."}])
def test_a_prohibiting_row_names_a_guard_or_why_not(tool, tmp_path, extra):
    root = project(tmp_path, rows() + [guard_row(**extra)],
                   settings=prohibiting())
    result = check(tool, root)
    assert result["problems"] == [] and result["debt"] == []


@pytest.mark.parametrize("extra, message", [
    ({}, "row 6 traces an element that prohibits an inference, and names "
         "no guard"),
    ({"guards": ["CQ-002"]}, "guard CQ-002 is draft, so "
                             "tools/ontology/competency.py does not run it"),
    ({"guards": ["CQ-009"]}, "guard CQ-009 is not a competency question"),
    ({"guards": ["ex:Nothing"]}, "guard ex:Nothing is neither a competency "
                                 "question nor a shape"),
    ({"guards": ["CQ-001"], "no_guard": "x"}, "names guards and says why it "
                                              "has none"),
])
def test_a_bad_guard_is_refused(tool, tmp_path, extra, message):
    root = project(tmp_path, rows() + [guard_row(**extra)],
                   settings=prohibiting())
    assert said(check(tool, root), message)


def test_an_ambiguous_prohibition_is_refused(tool, tmp_path):
    root = project(tmp_path, settings={"models": [model(
        prohibits=["CM-01#Options"])]})
    assert said(check(tool, root), "prohibits CM-01#Options, which names 2 "
                                   "places")


@pytest.mark.parametrize("value", ["Capacity / exercise",
                                   "CM-02#Capacity / exercise"])
def test_a_prohibition_names_its_own_model(tool, tmp_path, value):
    root = project(tmp_path, settings={"models": [model(prohibits=[value])]})
    assert said(check(tool, root), "prohibits %s, which is not "
                                   "CM-01#<anchor>" % value)


def test_a_conditional_designation_traced_to_a_shape(tool, tmp_path):
    """BCO's second expected change: a conditional designation cannot be
    an OWL class; it becomes a SHACL rule, with no OWL term."""
    row = rows()[3]
    assert row["formalized_as"] == {"shapes": ["ex:DesignationShape"]}
    assert check(tool, project(tmp_path))["problems"] == []


# -------------------------------------------------------------- adoption


def adopted(tmp_path, **settings):
    """A project whose module had ex:Organization only on 2026-01-01, and
    gains the rest on 2026-03-01; the trace names nothing."""
    first = HEAD + "<https://example.org/onto> a owl:Ontology .\n" \
        "ex:Organization a owl:Class .\n"
    root = project(tmp_path, trace_rows=[], pin=False,
                   settings=dict({"models": [model(cover=[])]}, **settings),
                   files={MODULE: first})
    old = commit(root, "2026-01-01")
    (root / MODULE).write_bytes(TURTLE.encode())
    commit(root, "2026-03-01")
    return root, old


def test_without_required_from_every_term_is_owed(tool, tmp_path):
    root, _ = adopted(tmp_path)
    assert {i for k, i in debt(check(tool, root))} == {
        NS + t for t in ("Organization", "BusinessCapability", "bears",
                         "bornBy")}


def test_a_term_at_the_baseline_commit_predates_adoption(tool, tmp_path):
    root, old = adopted(tmp_path)
    config = yaml.safe_load((root / "config/fidelity.yaml").read_text())
    config.update(required_from="2026-02-01", baseline_commit=old)
    (root / "config/fidelity.yaml").write_bytes(yaml.safe_dump(
        config, allow_unicode=True).encode())
    result = check(tool, root)
    assert result["problems"] == []
    assert result["predating"] == [NS + "Organization"]
    assert (("untraced", NS + "Organization")) not in debt(result)
    assert ("untraced", NS + "bears") in debt(result)


def test_without_a_commit_the_last_one_before_the_date_is_the_baseline(
        tool, tmp_path):
    root, _ = adopted(tmp_path)
    config = yaml.safe_load((root / "config/fidelity.yaml").read_text())
    config.update(required_from="2026-02-01")
    (root / "config/fidelity.yaml").write_bytes(yaml.safe_dump(
        config, allow_unicode=True).encode())
    assert check(tool, root)["predating"] == [NS + "Organization"]


def test_a_baseline_not_in_the_history_is_uncertain_never_exempt(tool,
                                                                 tmp_path):
    root, _ = adopted(tmp_path)
    config = yaml.safe_load((root / "config/fidelity.yaml").read_text())
    config.update(required_from="2026-02-01", baseline_commit="e" * 40)
    (root / "config/fidelity.yaml").write_bytes(yaml.safe_dump(
        config, allow_unicode=True).encode())
    result = check(tool, root)
    assert result["predating"] == []
    assert {k for k, _ in debt(result)} == {"uncertain"}
    assert len(result["debt"]) == 4


def test_a_shallow_clone_cannot_date_terms_so_they_are_uncertain(tool,
                                                                 tmp_path):
    origin, _ = adopted(tmp_path / "origin")
    config = yaml.safe_load((origin / "config/fidelity.yaml").read_text())
    config.update(required_from="2026-02-01")
    (origin / "config/fidelity.yaml").write_bytes(yaml.safe_dump(
        config, allow_unicode=True).encode())
    commit(origin, "2026-03-02")
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", "--depth", "1",
                    origin.resolve().as_uri(), str(clone)], check=True)
    result = check(tool, clone)
    assert result["predating"] == []
    assert {k for k, _ in debt(result)} == {"uncertain"}


def test_a_full_history_with_no_commit_before_the_date_exempts_nothing(
        tool, tmp_path):
    root, _ = adopted(tmp_path)
    config = yaml.safe_load((root / "config/fidelity.yaml").read_text())
    config.update(required_from="2025-01-01")
    (root / "config/fidelity.yaml").write_bytes(yaml.safe_dump(
        config, allow_unicode=True).encode())
    result = check(tool, root)
    assert result["predating"] == []
    assert {k for k, _ in debt(result)} == {"untraced"}


@pytest.mark.parametrize("settings, message", [
    ({"baseline_commit": "e" * 40}, "baseline_commit is set and "
                                    "required_from is not"),
    ({"required_from": "2026-02-01", "baseline_commit": "abc"},
     "baseline_commit is not 40 lowercase hex digits"),
])
def test_a_bad_baseline_is_refused(tool, tmp_path, settings, message):
    assert said(check(tool, project(tmp_path, settings=settings)), message)


def test_a_bad_required_from_cannot_be_read(tool, tmp_path):
    root = project(tmp_path, settings={"required_from": "soon"})
    with pytest.raises(tool.Unreadable, match="required_from 'soon' is not "
                                              "a date"):
        check(tool, root)


def test_an_unknown_setting_cannot_be_read(tool, tmp_path):
    root = project(tmp_path, settings={"verdicts": True})
    with pytest.raises(tool.Unreadable, match="unknown field"):
        check(tool, root)


# ------------------------------------------------------------- the gates


def stages(status="done", ident="formalization", runs=True):
    return [{"id": ident, "runs": runs, "status": status, "where": []}]


DEBT = [{"kind": "stale", "item": "row 3", "why": "the axioms changed"}]


def test_a_done_formalization_is_held_by_the_debt(tool):
    assert tool.stage_problems(stages(), DEBT, "formalization") == [
        "formalization: is done, but conceptual fidelity is owed: stale "
        "row 3 (the axioms changed)"]


@pytest.mark.parametrize("plan", [stages(status="in-progress"),
                                  stages(ident="instances"),
                                  stages(runs=False)])
def test_a_stage_not_done_or_not_named_is_not_held(tool, plan):
    assert tool.stage_problems(plan, DEBT, "formalization") == []


def test_another_stage_may_be_named(tool):
    assert tool.stage_problems(stages(ident="instances"), DEBT,
                               "instances") != []


def test_debt_stops_a_release(tool):
    assert tool.release_problems(DEBT) == ["stale row 3 (the axioms "
                                           "changed)"]


def test_debt_never_fails_the_ordinary_check(tool, tmp_path, monkeypatch,
                                             capsys):
    root = project(tmp_path, rows()[:4])
    real = tool.check
    monkeypatch.setattr(tool, "check", lambda r=None: real(
        root, modules=[root / MODULE, root / OTHER], shapes=[root / SHAPES],
        namespace=NS, prefix="ex"))
    monkeypatch.setattr(tool.layout, "repository_root", lambda: root)
    assert tool.main([]) == 0
    out = capsys.readouterr().out
    assert "untraced   CM-01#P1" in out
    assert "it does not show that the formalization is faithful" in out


def test_a_finding_fails_the_ordinary_check(tool, tmp_path, monkeypatch):
    root = project(tmp_path, edit_row(4, reviewed_by=None))
    real = tool.check
    monkeypatch.setattr(tool, "check", lambda r=None: real(
        root, modules=[root / MODULE, root / OTHER], shapes=[root / SHAPES],
        namespace=NS, prefix="ex"))
    monkeypatch.setattr(tool.layout, "repository_root", lambda: root)
    assert tool.main([]) == 1


def test_the_stage_gate_reads_nothing_without_a_model(monkeypatch,
                                                      tmp_path):
    stages_tool = load_tool("t_stages_p6_empty", "tools/stages.py")
    import fidelity as imported

    def refuse(root=None):
        raise AssertionError("the trace was read")

    monkeypatch.setattr(imported, "check", refuse)
    assert stages_tool.fidelity(tmp_path, stages()) == []


def test_stages_check_reaches_the_fidelity_gate(monkeypatch, tmp_path):
    stages_tool = load_tool("t_stages_p6", "tools/stages.py")
    import fidelity as imported

    monkeypatch.setattr(imported, "configuration",
                        lambda root: {"models": [model()]})
    monkeypatch.setattr(imported, "check", lambda root=None: {
        "debt": DEBT, "stage": "formalization"})
    assert stages_tool.fidelity(tmp_path, stages()) == [
        "formalization: is done, but conceptual fidelity is owed: stale "
        "row 3 (the axioms changed)"]


def test_stages_check_runs_the_fidelity_gate_only_when_done(monkeypatch,
                                                            tmp_path):
    stages_tool = load_tool("t_stages_p6_wiring", "tools/stages.py")
    called = []
    monkeypatch.setattr(stages_tool, "fidelity",
                        lambda r, s: called.append(r) or ["HELD"])
    monkeypatch.setattr(stages_tool, "withholding", lambda r, s: [])
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
    release = load_tool("t_release_p6", "tools/release.py")
    monkeypatch.setattr(release.decisions, "check",
                        lambda root=None: {"owed": []})
    monkeypatch.setattr(release.rights, "check",
                        lambda root=None: {"held": []})
    monkeypatch.setattr(release.fidelity, "check",
                        lambda root=None: {"debt": DEBT})
    with pytest.raises(release.Refused, match="conceptual fidelity is owed"):
        release.build("1.2.3", tmp_path / "out")
    assert not (tmp_path / "out").exists()


# -------------------------------------------------------------- printing


def test_digest_prints_and_writes_nothing(tool, tmp_path, monkeypatch,
                                          capsys):
    root = project(tmp_path)
    before = (root / "ontology/trace.yaml").read_bytes()
    monkeypatch.setattr(tool.layout, "repository_root", lambda: root)
    monkeypatch.setattr(tool.layout, "ontology_files",
                        lambda: [root / MODULE, root / OTHER])
    monkeypatch.setattr(tool.project, "namespace", lambda: NS)
    monkeypatch.setattr(tool.project, "prefix", lambda: "ex")
    assert tool.main(["--digest", "ex:bears", "ex:bornBy", "--pins"]) == 0
    out = capsys.readouterr().out
    pinned = yaml.safe_load(before)
    assert "axioms_sha256: %s" % pinned["rows"][0]["axioms_sha256"] in out
    assert "CM-01: %s" % pinned["models"]["CM-01"] in out
    assert "upstream_sha256: %s" % pinned["upstream_sha256"] in out
    assert "nothing was written" in out
    assert (root / "ontology/trace.yaml").read_bytes() == before
