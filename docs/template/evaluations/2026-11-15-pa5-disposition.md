# P-A5: the architect's disposition

**Date:** 2026-11-15. **Decision:** 47 (`docs/template/DECISIONS.md`). In answer to
`2026-11-15-pa5-design.md` section 7, as committed at `612f982`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`c91d53f92b0f09424232d5e09d204c17874e0a34878f84de01efb500072c294f`. Its heading carries no number; it is
entered in this register as 47, the next number.

---

**Architectural Decision — P-A5 Approved for v0.10.0**

I have reviewed all six P-A5 design questions and approve the proposed implementation.

**Decisions:**

1. Display term comments after definitions, including every conflicting variant and its module provenance.
2. Publish all annotation properties configured under `agree_across_modules`, excluding labels and definitions already handled by the explorer.
3. Display multiple comments within one module, preserving the existing validator findings. Do not implement the separate WP6 row 9 exemption.
4. Keep search behavior unchanged. Comments will not become searchable or affect ranking.
5. Approve the read-only BPO measurement of index size, comment coverage, and conflict visibility.
6. Approve P-A5 as the sole functional change for Ontology Template v0.10.0.

**Implementation safeguards:**

- Distinguish cross-module differences from multiple comments asserted within one module.
- Preserve language information, source-module attribution, and safe text rendering.
- Reuse the existing annotation-variant machinery and avoid unnecessary index duplication.

The site must show what the validator found without independently deciding whether the annotation is correct.

P-A5 must not change ontology axioms, validator semantics, search ranking, or third-party source content.

Proceed with implementation, negative and mutation tests, the BPO measurement, and the established release checklist.

**No further architectural design review is required unless implementation reveals a material conflict with these decisions.**

Following v0.10.0, continue with P-A6, P-A8, and P-A4 as separately scoped backlog items.
