# P-A8: the architect's disposition

**Date:** 2026-11-15. **Decision:** 52 (`docs/template/DECISIONS.md`). In answer to
`2026-11-15-pa8-design.md` section 7, as committed at `5899018`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`2adac7b0a7ea4f7d65969737530ad7bba2a623bf33b3cf7caef11c5a85b2262c`. Its heading carries no number; it is
entered in this register as 52, the next number.

---

**Architectural Decision — P-A8 Approved**

I accept the reported completion of Ontology Template v0.11.0. Decision 51 and the release evidence are accepted. P-A6 remains closed.

I have reviewed the five P-A8 design questions.

**P-A8 is approved for implementation as v0.12.0.**

1. **Every-page notices — Approved.** Publish one notice per applicable third-party text declaration in the footer of every generated page, immediately after the existing licence sentence.

2. **Declared licence — Do not display.** Preserve the declared source, release, and attribution. Do not imply that the template has independently established the material's licensing status.

3. **Footer validation — Approved.** Extend `check_site.py` to verify that every page contains the required notices. This is an explicitly authorized extension of Decision 33's module-header-only attribution check.

4. **Downloads ZIP — Separate backlog item.** Record the need for standalone provenance information in downloadable bundles. Do not expand P-A8 to implement it.

5. **Release — Approved.** P-A8 alone will constitute the functional scope of v0.12.0. P-A4 follows as the next separately designed item.

**Implementation safeguards:**

- Publish only applicable declarations, exactly once per page.
- Preserve declared attribution word for word, using safe text rendering.
- Leave the footer unchanged when no applicable third-party text exists.
- Verify expected notices against the declarations and published modules.
- Do not alter the validator, rights-review process, licensing disposition, ontology, explorer, or search.

The notice is a statement of provenance, not a legal authorization.

Run the required negative and mutation tests, the complete suite, compatibility checks, and the release checklist.

**Repository authorization:** Push `c9d6855` and `5899018` to `main` using the normal repository workflow.

The P-A8 implementation is authorized under these decisions. No further architectural design review is required unless implementation reveals a material contradiction.

After v0.12.0, proceed to P-A4. Do not reopen completed WP6 findings.

**P-A8 approved. Proceed.**
