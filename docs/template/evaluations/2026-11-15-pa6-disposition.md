# P-A6: the architect's disposition

**Date:** 2026-11-15. **Decision:** 50 (`docs/template/DECISIONS.md`). In answer to
`2026-11-15-pa6-design.md` section 7, as committed at `254ff30`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`e4c266368dc303edc0cec7c0c8da32f2fc9893c1f96eb41fda2e04402bd67e46`. Its heading carries no number; it is
entered in this register as 50, the next number.

---

**Architectural Decision — P-A6 Approved**

I have reviewed the P-A6 design and approve its four proposed decisions.

**1. Selection — Approved.**

Implement `--rule`, `--where`, `--focus`, and `--focus-file` on both affected checks.

Values within one selector are alternatives; different selectors are combined. Unknown values and empty resulting selections are errors.

With no new options, existing behavior must remain unchanged. Findings excluded from a proposal remain new and continue to affect the gate.

**2. Human-supplied classification — Approved with safeguards.**

A reviewer may provide all four classification fields once for an explicitly selected group.

No classification or reviewer identity may be inferred. Validate the supplied fields, reviewer capacity, and applicable register rules before producing completed entries.

Report how many findings receive the judgment.

This is a human-directed recording operation, not automated classification. Decision 32 remains in force.

Exclude `origin: upstream` from batch classification because each entry requires its own upstream reference. Do not bypass other required references or review dates.

**3. Exact-identity selection — Deferred.**

Do not implement `--select FILE` in v0.11.0.

Document that focus-based selection cannot distinguish findings sharing the same rule, location and focus. Such cases remain subject to the existing individual classification workflow.

**4. Release — Approved.**

Implement P-A6 alone as Ontology Template v0.11.0.

Run the negative and mutation tests, full suite, compatibility checks and release checklist. No separate BPO measurement is required.

After v0.11.0, proceed to P-A8 and then P-A4 as separately scoped design items.

**Repository authorization:** Push local commits `2d7cc2c` and `254ff30` to `main` through the normal repository process. The P-A6 implementation is authorized once the design reflects these safeguards.

No further architectural design review is required unless implementation reveals a material conflict.

**P-A6 is approved. Proceed.**
