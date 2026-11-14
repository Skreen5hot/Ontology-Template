# P-A2: the architect's disposition

**Date:** 2026-11-14. **Decision:** 45 (`docs/template/DECISIONS.md`). In answer to
`2026-11-14-pa2-design.md` section 7, as committed at `d01c353`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`394076ad3732a700bebbfe70ce7ac836636a571e31195c4d4215165505351682`. Its heading carries no number; it is
entered in this register as 45, the next number. The message it came in began, in the
architect's own words, "Fix the message defect. Then:" (SHA-256 `eaefcc92b744aa12a630dbe24f31f74602e63da85ba062cd0160c2c41c09ea14`), and that fix is
`4096a68`.

---

**Architectural Decision — P-A2 Template Upgrade Procedure**

I have reviewed the nine questions in the P-A2 design.

**P-A2 is approved for implementation as Ontology Template v0.9.0, with four safeguards.**

I approve the documented upgrade procedure, `--plan`, `--take`, and `--adopt`; manual three-way merging; preservation of the project's layout contract; reporting of rendered-file changes; and inclusion of all intervening release notes.

I also approve the proposed read-only planning and disposable-project upgrade measurements using v0.1.0 and v0.7.0 projects.

Before implementation, incorporate these requirements:

1. **Legacy bootstrap:** An older project must be able to run the new upgrade planner without first modifying itself to obtain the tool.
2. **Ontology dependency control:** BFO/CCO pin changes must require explicit acceptance. `--take` must not silently upgrade upstream ontologies.
3. **Accurate adoption records:** `--adopt` must preserve original initialization provenance, record the exact new release and commit, and make intentionally retained differences and unresolved manual obligations visible.
4. **Safe file handling:** Never overwrite project modifications, untracked collisions, or unexpected symlinks. Report removed files and changes to layout declarations rather than applying destructive operations automatically.

The upgrade tool must remain a controlled mechanism for carrying template improvements into projects. It must not become an automatic ontology migration or semantic-repair tool.

Proceed with implementation, negative and mutation tests, the two disposable-project upgrade measurements, and the v0.9.0 release checklist.

No additional features should be added to v0.9.0. P-A4 through P-A6 and P-A8 remain separate backlog items.

**P-A2 is approved. No further architectural design review is necessary unless implementation exposes a material conflict with these decisions.**
