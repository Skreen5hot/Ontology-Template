# The architect's acceptance of WP4 (2026-10-29)

Recorded verbatim; decision 15 in `docs/template/DECISIONS.md` gives the digest of the text
below the rule and its effect.

---

Team,

**WP4 is accepted as technically complete at commit `a923694`. Proceed to the next work package under the approved roadmap.**

The reported evidence satisfies Decision 14's technical requirements for T8–T12 and T23: detection, accurate reporting, register-based disposition, and regression protection.

The following decisions apply.

**1. WP4 acceptance**

Accept the implemented detection controls and supporting regression tests.

The 16 regression tests, 15 successful mutation tests, correction of the two implementation defects, and successful CI results provide adequate evidence for technical acceptance.

Record the measured GitHub Actions results separately from the unrepresentative local execution time.

**2. Corrected BPO measurements**

The following corrections are approved:

- **T10:** Two used properties, with 494 assertions across 453 classes. `requiresPermission` is declared but unused and is excluded from the observed misuse count.
- **T11:** The previous 78 genus warnings are eliminated and 18 new qualifier warnings are correctly reported. These are new findings, not warnings preserved from an earlier check.
- **T23:** Fourteen of the 15 modules containing APQC text lack the required source-release identification in the S0 baseline.

These figures supersede the earlier estimates. Do not modify the checks to reproduce the superseded figures.

**3. T9 technical acceptance and legal-policy dependency**

Accept T9's implemented detection and reporting capability.

Final policy approval remains withheld pending Legal's response to `EXAMPLE-LEGAL-2026-10-28-t9-third-party-text`.

Retain the PENDING LEGAL designation and the test protecting it.

The current checks must not be represented as establishing legal permission, attribution sufficiency, or BPO's right to redistribute APQC-derived content.

When Legal responds, assess whether the policy requires adjustments to the implementation, tests, reporting language, or publication controls. Record and verify any necessary changes before closing the T9 policy dependency.

BPO's redistribution question, B2, remains a separate matter for BPO and Legal.

**4. BPO-specific findings**

Retain all BPO-derived findings as evaluation evidence, not approved dispositions.

In particular, the T11 qualifier findings and trial T12 scheme rule require decisions by the BPO team.

Do not automatically transfer trial configuration, placeholder attribution, or accepted findings from the scratch copies into BPO.

**5. Roadmap and decision records**

Record this acceptance in the template's decision history.

Correct the outstanding roadmap statement concerning the subsequent CI timing commit. Include the actual GitHub Actions timing results in the same commit that records this decision; a separate preliminary commit is unnecessary.

Retain the BPO-scale performance measurements and final ontology-quality evaluation as WP6 responsibilities.

**6. Authorization to proceed**

Proceed to the next scheduled work package without waiting for Legal, provided unrelated work does not depend on an unresolved licensing-policy determination.

The objective remains unchanged: demonstrate that the Ontology Template supplies a repeatable, auditable framework for identifying ontology quality issues, supporting their resolution, verifying corrections, and preventing recurrence.

**WP4 technical implementation is accepted. The three corrected measurements are confirmed. T9 legal-policy approval remains open.**
