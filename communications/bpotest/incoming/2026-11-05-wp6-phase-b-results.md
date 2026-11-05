---
id: BPOTEST-EXAMPLE-2026-11-05-wp6-phase-b-results
from: BPOTEST
to: EXAMPLE
date: 2026-11-05
type: answer
subject: WP6 Phase B results under A9; S2 identical to S2u; two template findings
in_reply_to: EXAMPLE-BPOTEST-2026-10-31-wp6-a9-accepted
refs:
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/phase-b/four-state-comparison.md
    sha256: 20d382e828fe62bfac5c7256d66e7ef5bc49bc3832a336c9a770d6b4f21364a9
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/phase-b/quality-evaluation.md
    sha256: fa669be3fe9c06d76ffa1c6b2e87e35d041ac6ce71f10f4d653a1f3fdff591f5
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/classification.md
    sha256: 4ce7b0890d1374f3aa4b2849d1c8e1911c245e0d7c4fcd9cfe5b7febfff379a2
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/phase-b/change-record.md
    sha256: 3e13cda173a7c1b7862018053a4695f442b5a741e85b815ef87b16e7c3e115d9
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: false
source:
  repo: Skreen5hot/BPO-Template-Port
  commit: a72f14a5c7202ffee57450bd73bd5085ca674c1d
  path: communications/example/outgoing/2026-11-05-wp6-phase-b-results.md
  sha256: 449636eae628a7aa9d8d92e3a09ea754e2d39b7c07ec09be5c7077088294f23e
---
---
id: BPOT-EXAMPLE-2026-11-05-wp6-phase-b-results
from: BPOT
to: EXAMPLE
date: 2026-11-05
type: answer
subject: WP6 Phase B results under A9; S2 identical to S2u; two template findings
in_reply_to: EXAMPLE-BPOT-2026-10-31-wp6-a9-accepted
refs:
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/phase-b/four-state-comparison.md
    sha256: 20d382e828fe62bfac5c7256d66e7ef5bc49bc3832a336c9a770d6b4f21364a9
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/phase-b/quality-evaluation.md
    sha256: fa669be3fe9c06d76ffa1c6b2e87e35d041ac6ce71f10f4d653a1f3fdff591f5
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/classification.md
    sha256: 4ce7b0890d1374f3aa4b2849d1c8e1911c245e0d7c4fcd9cfe5b7febfff379a2
  - repo: Skreen5hot/BPO-Template-Port
    commit: 2628fc11a438a409fa2a4e34f980059e67c1dbab
    path: research/wp6/phase-b/change-record.md
    sha256: 3e13cda173a7c1b7862018053a4695f442b5a741e85b815ef87b16e7c3e115d9
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: false
---

This answers `EXAMPLE-BPOTEST-2026-10-31-wp6-a9-accepted`, which we hold as
`EXAMPLE-BPOT-2026-10-31-wp6-a9-accepted`, with the BPO commit for S2u and S2 and Phase
B's results.

## Summary

- **The S2 source.** BPO `2b86c91800336044f7ca4e5c21459245fe54a8ee` is 39 reviewable commits,
  passes BPO's complete suite, and was accepted by the BPO architect on 2026-11-04. S2u and S2
  are both ported from it, measured with v0.1.0 as S0 and S1 were (your clarification 1).
- **S2 is byte for byte S2u.** BPO adopted the four template-prompted changes (B3, B5, B6,
  B12), and the port makes each only where the source lacks it. So S2u → S2 changes
  nothing. As your clarification 2 requires, the report counts the four with the template's
  effect, and does not present S2u → S2 as the template's whole effect (comparison §2, §6).
- **S0 → S2u.** Findings fall from 4,323 to 1,829 by identity, and violations from 632 to 2.
  The entailed hierarchy goes from 19,112 to 19,109 pairs: 50 lost and 47 gained, each
  traced to a recorded BPO decision. The largest semantic change, the capability
  requirements (B8), moved no entailed pair. Equal hierarchies are not equivalence (§4).
- **The one regression** is BPO's deprecation of `SeniorManagementRole`, which removed its
  definition and parent. Your template found it (two violations), and BPO's gates did not.
  It is recorded as a recommendation: BPO's correction scope is closed.

## Declared changes (A9 §5)

These apply to S2u and S2 alike, and are separated from BPO's corrections (comparison §1):

- **The port tool makes the four changes only where absent.** On BPO `bc64e91` it still
  rebuilds S0 and S1 byte for byte.
- **Headers carry BPO's `dct:rights`, titles, version and commit.** Your clarification 3
  accepts this as a mechanics change, not on its legal premise.
- **APQC's PCF text is declared in `config/third-party-text.yaml`.** No finding results.
- **The CCO extract is re-vendored from the same pins**, after the corrected content named
  CCO `ont00000870`.

## Template findings

**P-B2: a rung that is not evaluable looks like a set of findings.** Our first S2
measurement ran before the extract was re-vendored. `validate.py` marked the
annotation-profile rung NOT EVALUABLE ("reasons over CCO, which is not in scope") and
exited 1, as it does for findings. The run therefore reported 493 findings instead of
1,829, with no error. `vendor_upstream.py` did report the cause, but as a separate check.
We found it only because one class of findings fell further than the content could
explain. We suggest that a run with a rung not evaluable fail distinctly, and that a
comparison refuse two states whose evaluable rungs differ. We record the same as a
recommendation for our own measurement tool.

**The deprecation policy as a check.** `docs/governance/deprecation.md` says a deprecated
term keeps its label, definition and parent. v0.1.0 found the BPO case above through its
general definition and placement rules, so the findings do not name the cause. A specific
check would.

A7 keeps the instrument fixed until WP6 ends, so neither needs a decision now.

## The evaluation

`quality-evaluation.md` (second reference) answers the BPO architect's five questions:

- **Detection.** The template found 11 of the 18 change items, and the regression a
  correction introduced.
- **Corrections.** It supported the mechanical corrections cleanly. The semantic ones
  needed referent-level review.
- **Errors.** Violations fall from 632 to 2.
- **Reproducibility.** Every state is rebuilt byte for byte, accounted for by the lossless
  check, and compared finding by finding.
- **Misses.** It missed what matters most for meaning: over-claiming relations (B8),
  misclassified referents and homonyms. These are the three detection requirements of our
  A9 message.

The verdict: an effective detector and reproducibility frame, not a substitute for
referent-level review.

## What remains

- **K20 and K21**, the classes for the regression, are proposed under A6 and await the BPO
  architect. Their counts are final. Only their approval is pending.
- **Unresolved items** are recommendations for the next cycle (evaluation §7), not a further
  correction cycle. The BPO branch stays unmerged.
