# v0.10.0: the architect's release approval

**Date:** 2026-11-15. **Decision:** 48 (`docs/template/DECISIONS.md`). In answer to the
v0.10.0 readiness report, which asked to push `612f982` to `fa26693` to `main`, confirm CI on
`fa26693`, and tag and push v0.10.0. The text below the rule is the architect's, verbatim, as
pasted; its SHA-256 is
`0f95bbe09009c7ad07cad64e7b439935f577524ab1193d1ca3943be49b367eb5`. Its heading carries no number; it is
entered in this register as 48, the next number.

Its item 1 says "the seven commits": the report said seven, and that was a miscount. The
range `612f982` to `fa26693` is six commits, and all six were pushed; nothing was left out.

---

**Architectural Decision — P-A5 v0.10.0 Release Approved**

I have reviewed the reported P-A5 implementation, BPO measurement, regression results, mutation tests, and compatibility evidence.

**P-A5 is architecturally accepted for Ontology Template v0.10.0.**

The implementation meets the approved scope: term comments and configured agreement annotations are published, conflicting values retain their provenance, validation behavior remains unchanged, and search behavior is preserved.

The BPO measurement is accepted. The 53 displayed findings match the validator's reported count. The 43% increase in index size is justified by the additional published information.

The seven within-module findings do not require another review before release. Their possible correspondence with WP6 false alarms may be checked separately.

The Node-based browser simulation is an accepted testing limitation for v0.10.0.

**Release authorization:**

1. Push the seven commits through `fa26693` using the normal repository workflow.
2. Confirm the full required CI suite passes on that exact commit.
3. Tag and push `v0.10.0` on `fa26693`.
4. Verify the tag-triggered workflows and published artifacts.
5. Record the release as complete.

No additional architectural review is required if these conditions pass.

Do not introduce more features into v0.10.0.

Following release completion, proceed with the next separately scoped backlog item, P-A6, rather than reopening completed WP6 findings.

**P-A5 is accepted. Proceed with release.**
