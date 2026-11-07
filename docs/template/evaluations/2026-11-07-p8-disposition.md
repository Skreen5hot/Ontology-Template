# P8: the architect's disposition

**Date:** 2026-11-07. **Decision:** 40 (`docs/template/DECISIONS.md`). In answer to
`2026-11-07-p8-design.md` section 7, as committed at `919454d`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`4e0ddae6668fd7c5072126788a153ccf82eaa702558ae8a5b3dbc6d17c6f97c7`. Its heading numbers it 35; it is
entered in this register as 40, the next number, since 35 is the review roles' decision of
2026-11-06.

---

**Architectural Decision 35 — P8 Approved**

The P8 Rights and Provenance Review design is approved for Ontology Template v0.7.0, with four safeguards:

1. Rights assessments must identify the specific source edition and intended use. Permission for one use does not imply permission for another.
2. Evidence must be accurately represented. Manual review without access to verifiable source bytes must not be described as digest-verified.
3. Stage and release controls enforce the existence and scope of recorded authorization decisions, not an automated judgment about licensing terms.
4. Existing accepted architectural decisions, including BPO ADR-003, remain authoritative for the material and uses they cover. P8 must not automatically reopen them.

All seven proposed design choices are accepted subject to these safeguards.

The architect remains the default release authority, with explicit delegation permitted. New covered uses remain withheld pending an applicable decision. Ordinary CI continues to validate records without blocking development solely because a rights-use decision is pending.

The read-only BCO measurement is approved.

**Commit `919454d` is authorized for push and normal review.**

Proceed with implementation, negative and mutation tests, documentation, and the v0.7.0 release checklist.

P6 remains the next separately scoped improvement. Do not add it or additional rights-governance features to v0.7.0.

P8 is approved for implementation; no additional design approval is required unless a material architectural contradiction is discovered.
