# v0.11.0: the architect's release approval

**Date:** 2026-11-15. **Decision:** 51 (`docs/template/DECISIONS.md`). In answer to the
v0.11.0 readiness report, which asked to push `59bec6e` to `ec4f47c` to `main`, confirm CI on
`ec4f47c`, and tag and push v0.11.0. The text below the rule is the architect's, verbatim, as
pasted; its SHA-256 is
`dc17173dc739d253ded0d603eadfbdc2e001bfcece8f0283edcf284e64f5d839`. Its heading carries no number; it is
entered in this register as 51, the next number.

---

**Architectural Authorization — P-A6 v0.11.0**

I accept the reported P-A6 implementation, testing, compatibility results, and release preparation.

P-A6 satisfies the approved design and safeguards. Selective proposal generation and human-directed batch classification are implemented without changing finding identities, validation results, register rules, or gate behavior.

The distinct-finding counts and incomplete-rung warning are accepted refinements.

The 30-of-31 mutation result is acceptable provided the surviving format-version mutation is documented as behaviorally equivalent for this operation, with its justification. Do not count it as caught.

**Release authorized:**

1. Push `59bec6e` through `ec4f47c` to `main`.
2. Confirm all required CI checks pass on `ec4f47c`.
3. Tag and push `v0.11.0` on that exact commit.
4. Verify the tag-triggered workflow and manifest.
5. Record release completion.

No further P-A6 design review is required if these conditions are met.

After releasing v0.11.0, proceed with P-A8 as the next separately scoped design item, followed by P-A4.

Do not reopen completed WP6 findings or expand v0.11.0.

**P-A6 is accepted. Proceed with release.**
