# P7: the architect's disposition

**Date:** 2026-11-06. **Decision:** 38 (`docs/template/DECISIONS.md`). In answer to
`2026-11-06-p7-design.md` section 7, as committed at `0c3cec2`. The text below the rule is
the architect's, verbatim, as pasted; its SHA-256 is
`a1ab35fba6000bac5e9424a84723565193a299b53d6463ab412be31b52cdd636`.

---

**Architectural Decision — P7 Approved**

I approve P7 Decision Propagation for implementation in Ontology Template v0.6.0.

All seven proposed design choices are accepted, with three safeguards:

1. A valid target file that has not yet been created is reported as owed, rather than immediately rejected. The relevant stage cannot close until it is created, tracked, and references the decision.
2. Outstanding targets outside all configured stage scopes must remain visible and be assigned or explicitly accounted for before project release.
3. Decision references must use exact identifier matching, avoiding false matches and self-satisfaction.

Retain file-level targets, YAML front matter, backward compatibility through `required_from`, and stage-closure enforcement rather than failing ordinary CI on outstanding propagation debt.

Approve the read-only BCO DP-1/DP-2 measurement.

The tool establishes whether a declared propagation obligation has been referenced in its target. It does not determine whether the decision was implemented faithfully. That judgment remains with the appropriate human reviewer.

Proceed with implementation, negative and mutation tests, documentation, and the v0.6.0 release checklist.

Do not expand the scope to additional governance features or subsequent backlog items without a separately approved need.

**P7 is approved. No further architectural design review is required unless implementation reveals a material contradiction with these decisions.**
