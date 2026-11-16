# v0.12.0: the architect's release authorization

**Date:** 2026-11-16. **Decision:** 53 (`docs/template/DECISIONS.md`). In answer to the
v0.12.0 readiness report, which asked to push `e3443d9` to `f86da5d` to `main` and, once CI
was green on `f86da5d`, to tag and push v0.12.0. The text below the rule is the
architect's, verbatim, as pasted; its SHA-256 is
`2ca16d56d48529133dd0ed2b9c6731bfa601bfdb202d5ec4a22fc61a31836bdf`. Its heading numbers it 53, the next number in this register.

---

# Architectural Decision 53 — P-A8 v0.12.0 Release Authorization

**Disposition: APPROVED, SUBJECT TO FINAL CI**

I accept the reported implementation, tests, and compatibility evidence for P-A8.

The implementation meets the approved architectural requirements:

- Applicable third-party text declarations generate provenance notices on every published page.
- The site checker verifies the presence, integrity, ordering, and placement of those notices.
- No new licensing decisions are introduced.
- Existing rights review, licensing disposition, ontology content, and validation semantics remain unchanged.

The 27 new negative tests and 30-of-30 mutation results are accepted. The reported full-suite, compatibility, fresh-initialization, and manifest-test results support proceeding to release.

The temporary Git index incident is not a blocker, provided the final working tree and commit contents are verified.

**I authorize the following release sequence:**

1. Push the four commits through `f86da5d` to `main`.
2. Confirm Checks, Reasoning, Pages, Install, and Scale pass on that exact commit.
3. Create and push annotated tag `v0.12.0` on `f86da5d`.
4. Verify the tag-triggered Release workflow and manifest.
5. Record release completion in the decisions log and roadmap.

Do not tag if a required CI run fails. Correct the issue and rerun validation on the revised candidate.

No additional architectural approval is required if the stated conditions pass.

P-A8 is accepted for release. The separately recorded Downloads ZIP provenance issue remains outside v0.12.0.

**Following release completion, proceed to P-A4's design as the next separately scoped backlog item. Do not reopen completed WP6 findings.**
