# P6: the architect's disposition

**Date:** 2026-11-14. **Decision:** 42 (`docs/template/DECISIONS.md`). In answer to
`2026-11-07-p6-design.md` section 7, as committed at `92077a5`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`0482fac26bc8408b8acbd561cadd595be3fbcd9c19410f2c25b6f80e0df90f41`. Its heading carries no number; it is
entered in this register as 42, the next number.

Its decision 3 names `domain-practitioner`, which decision 35 had replaced by
`domain-expert` (v0.4.0). That was asked, and decision 43 answers it.

---

# Architectural Decision — P6 Conceptual Fidelity

**To:** Ontology Template Team
**From:** Ontology Architect
**Date:** November 14, 2026
**Subject:** Approval of P6 Design for v0.8.0

I have reviewed the proposed P6 Conceptual Fidelity design, including the eight questions in §7.

**P6 is approved for implementation, subject to the amendments below.**

The governing principle is that formalization must preserve the approved conceptual model's intended meaning, or explicitly document and authorize departures from that model.

P6 must enforce traceability and review completeness without claiming to establish semantic fidelity automatically.

## Decision 1 — Location of the trace

**APPROVED: Use separate YAML files.**

Use:

- `config/fidelity.yaml` to identify approved conceptual models, coverage requirements, and applicability.
- `ontology/trace.yaml` to record mappings between conceptual-model elements and their formal representations.

Both files should be seeded.

Do not introduce an ontology annotation property solely for traceability. The mappings are engineering-process metadata and need not become part of the released ontology.

The separate trace also supports many-to-many relationships, SHACL representations, competency questions, and elements deliberately omitted from OWL.

## Decision 2 — Conceptual-model element references

**APPROVED: Use `<model-id>#<anchor>`.**

Approve the proposed Markdown anchor resolution through headings, table rows, bold list items, and qualified section paths.

Requirements:

1. An anchor must resolve uniquely within its registered model.
2. Ambiguous anchors must be rejected until qualified.
3. References must remain deterministic across repeated runs.
4. Models in other formats may declare their anchors explicitly.
5. Explicitly declared anchors must not be represented as independently verified against unsupported document formats.

Do not prescribe a universal conceptual-model document format.

The purpose is to support different conceptual-modeling methods while maintaining reliable traceability.

## Decision 3 — Meaning preservation and authorized changes

**APPROVED WITH AMENDMENT.**

Retain the proposed values:

- `preserves`
- `changes`
- `not-formalized`

A `changes` or `not-formalized` row requires an existing architectural decision that explicitly references every relevant conceptual-model element.

A `preserves` row requires a named reviewer and review capacity.

The reviewer kinds must be drawn from the existing `config/review.yaml` vocabulary. In particular, use the previously accepted `domain-practitioner` designation rather than introducing `domain-expert` as a separate fixed kind without an approved vocabulary change.

A project may register a proxy reviewer kind if its governance process permits one.

The automated check establishes that the appropriate review or decision was recorded. It does not establish that the judgment was correct.

For clarity, `not-formalized` means deliberately not represented in OWL. The conceptual element may still be represented through a competency question, SHACL constraint, or another documented mechanism.

The design should also correct its reference to P8 as the mechanism for decision citations. Decision propagation is governed by P7.

## Decision 4 — Axiom fingerprints and semantic changes

**APPROVED WITH AMENDMENT: Require axiom digests.**

Retain `axioms_sha256` and the conceptual-model digest.

However, the axiom fingerprint must be based on a deterministic canonical representation of the relevant asserted axioms, not simply on textual Turtle serialization.

The implementation must account for the OWL expressions and anonymous structures that define or constrain the traced terms, including relevant restrictions, equivalence axioms, disjointness axioms, and property axioms.

A change in the serialization order must not create a false semantic-change warning.

A change in a relevant asserted axiom must invalidate the previous review fingerprint.

The trace must also record or reference the pinned BFO/CCO dependency context. An upstream ontology change can alter inferred semantics without changing BPO's authored axioms.

**A matching digest proves that the reviewed artifact has not changed; it does not prove that the artifact correctly represents the conceptual model.**

For conceptual-model constraints that explicitly prohibit certain inferences, the reviewer should identify an executable guard where feasible, or document why no such guard is provided.

The template verifies that a declared guard exists and participates in the relevant validation process. The reviewer remains responsible for whether the guard adequately tests the requirement.

Digests must never be silently regenerated to clear a stale review.

## Decision 5 — Enforcement and legacy compatibility

**APPROVED WITH AMENDMENT.**

The proposed enforcement distinction is correct:

- Ordinary CI validates the trace schema, references, and recorded evidence.
- Outstanding traceability or stale-review findings are reported but do not automatically prevent ordinary development.
- A formalization stage marked `done` cannot retain applicable fidelity debt.
- The release process cannot complete with unresolved applicable fidelity debt.

Approve `required_from` for existing projects.

However, historical exemptions must use a reproducible adoption baseline. Prefer a recorded adoption commit or equivalent source snapshot in addition to the effective date.

If history is incomplete and the tool cannot establish whether a term predates adoption, report that uncertainty rather than silently exempting the term.

For a project without a registered approved conceptual model, the report must not claim that conceptual fidelity has passed. It should identify the evaluation as not applicable or not yet established, according to a recorded project decision.

This preserves backward compatibility without creating false evidence of successful verification.

## Decision 6 — Coverage

**APPROVED AS PROPOSED.**

On the formal ontology side, cover every authored class and property within the configured authored namespaces.

Imported BFO/CCO terms are excluded from the requirement to have their own conceptual-model mappings.

On the conceptual-model side, enforce coverage for the anchors explicitly selected in each model's `cover` configuration.

Support pattern-level and many-to-many mappings.

Every covered model element must have a trace row, including elements deliberately left out of OWL.

Report both sides of the coverage assessment:

- Authored ontology entities without a trace.
- Covered conceptual-model elements without a trace.

The source model's coverage selection remains an explicit architectural responsibility. The tool must not assume that an incomplete `cover` selection demonstrates complete conceptual-model coverage.

## Decision 7 — Implement now or wait for BCO formalization?

**APPROVED: Implement now as v0.8.0.**

Do not delay development until BCO completes Stage 05.

The design can be implemented and tested against the approved fixtures, the structure of CM-01, and deliberately constructed examples of faithful and unfaithful formalization.

However, v0.8.0 must describe its demonstrated capability accurately.

At release, the template will have demonstrated:

1. Trace completeness checking.
2. Model-element reference checking.
3. Axiom-change detection.
4. Recorded fidelity-review requirements.
5. Stage and release enforcement.

It will **not yet have demonstrated** that the mechanism reliably supports faithful formalization of a substantial real ontology.

When BCO produces its first substantive Stage 05 module, run P6 against it and record the results as a follow-up evaluation.

If that evaluation exposes a genuine design weakness, address it in a subsequent release. Do not hold v0.8.0 indefinitely awaiting that evidence.

## Decision 8 — BCO measurement

**APPROVED: Read-only measurement.**

Approve recording the reported CM-01 structural inventory:

- 5 patterns
- 33 concepts
- 39 relationships
- 2 decision points
- 22 boundary-section rows

The measurement should verify that the configured anchor-resolution rules identify the intended model elements and correctly handle ambiguous or qualified anchors.

Because BCO has no substantive Stage 05 OWL formalization yet, the current measurement must be identified as **conceptual-model reference coverage**, not demonstrated conceptual fidelity.

Repeat the evaluation when the first substantive formalization exists.

Record the number of model elements traced, untraced, intentionally not formalized, reviewed as preserving meaning, and associated with approved semantic changes.

BCO must remain unchanged during these measurements.

## Implementation authorization

Proceed with the approved P6 design and the amendments stated above.

The v0.8.0 implementation scope consists of:

- The seeded model and trace configurations.
- The fidelity checker.
- Deterministic axiom fingerprints and stale-review detection.
- Integration with stage and release controls.
- Negative, regression, and mutation tests.
- Documentation explaining the limits of automated conceptual-fidelity verification.
- The read-only CM-01 evaluation.

Do not introduce new ontology object properties or require per-term annotations merely to satisfy the traceability mechanism.

Do not expand v0.8.0 into automated semantic interpretation or automatic decisions about whether OWL faithfully implements a conceptual model.

**P6 is approved. No additional architectural design round is required unless implementation reveals a material contradiction with these decisions.**

The goal is to ensure that ontological meaning is carried from the conceptual model into formalization deliberately, transparently, and with accountable human review—not simply to confirm that the resulting OWL files are syntactically valid.
