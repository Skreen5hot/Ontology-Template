# P-A4: the architect's disposition

**Date:** 2026-11-17. **Decision:** 54 (`docs/template/DECISIONS.md`). In answer to
`2026-11-17-pa4-design.md` section 7, as committed at `8b78882`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`de4da7d03af9a20eead20c994a3af834d7fb700388ce6dae3ea7d72eeabaa5a1`. Its heading carries no number; it is
entered in this register as 54, the next number.

---

**Architectural Disposition — P-A4 Approved**

I approve the P-A4 design and authorize pushing commit `8b78882` to `main`.

All four proposed decisions are accepted:

1. Resolve P-A4 through the naming guide and close the finding. Do not introduce a new scheme-rule configuration feature.
2. Test the guide's actual SHACL-SPARQL example and fixture with both Oxigraph and pyshacl, verifying the identities of the expected findings.
3. Release P-A4 alone as Ontology Template v0.13.0, subject to the established validation and release checklist.
4. Notify the BPO Testing Team after release, accurately distinguishing template support from implementation in BPO.

The guide must explain project-controlled exemptions, literal datatypes, language tags, whitespace and multiple values without imposing BPO-specific policy on other projects.

No changes to `config/naming.yaml`, the existing validation engines, or ontology content are authorized.

**P-A4 is approved for implementation. No further architectural design review is required unless a material contradiction emerges.**
