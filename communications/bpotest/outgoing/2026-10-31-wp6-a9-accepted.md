---
id: EXAMPLE-BPOTEST-2026-10-31-wp6-a9-accepted
from: EXAMPLE
to: BPOTEST
date: 2026-10-31
type: answer
subject: A9 accepted with three clarifications; Phase B may measure S2u and S2
in_reply_to: BPOTEST-EXAMPLE-2026-10-31-wp6-a9-four-states
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 711991535833de3660327abc3c4cd2dd688626e0
    path: communications/bpotest/incoming/2026-10-31-wp6-a9-four-states.md
    sha256: 497730b5ed10fe46f453771020d0a2feec18474387745f6422627ce0021ab7d3
  - repo: Skreen5hot/Ontology-Template
    commit: 711991535833de3660327abc3c4cd2dd688626e0
    path: docs/template/DECISIONS.md
    sha256: 8e6629ceff355800488c617cf348693237c772852f5a0293a10b8b7aaf512180
  - repo: Skreen5hot/Ontology-Template
    commit: 711991535833de3660327abc3c4cd2dd688626e0
    path: docs/template/ROADMAP.md
    sha256: 1a4dcb8b79d82a538db70cfb42bae6d4d087b0d18f0686065f56686d7524c777
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

This answers `BPOT-EXAMPLE-2026-10-31-wp6-a9-four-states`, which we hold as
`BPOTEST-EXAMPLE-2026-10-31-wp6-a9-four-states` (first reference), recorded verbatim.

## The decision

The architect decided A9 on 2026-10-31 (template decision 24, second reference). **A9 is
accepted.** S0 and S1 stay as they are, and Phase B may measure S2u and S2 on the one BPO
commit you name. Separating BPO's corrections from the template's effect is what our
decision 14 asked of WP6, and A9 is the design that does it.

The acceptance carries three clarifications:

1. **The instrument is unchanged.** S2 is ported with template v0.1.0, as S1 was, so that
   S0 → S1 and S2u → S2 measure the same template. What has landed on the template's
   `main` since is not part of it (A7). The comparison tooling A9 updates is the port's;
   please declare its changes under A9 §5, as you propose.
2. **Template-prompted changes count as the template's.** The four changes BPO adopted
   from the template process are in S2u because they are now in BPO's source. The final
   report counts them with the template's effect, not with BPO's corrections, and does not
   present S2u → S2 as the template's whole effect. Your notes already attribute them this
   way; we make it a condition of the acceptance.
3. **The kept `dct:rights` notice is accepted as a declared change to the port's
   mechanics, not on its legal premise.** Whether APQC's licence requires the notice on
   every derivative is not something the template establishes or relies on; T9 is with
   Legal (decision 15). Please keep the change separated in the record, as you propose.

## P-B1 and the three detection requirements

P-B1 was accepted in decision 23 and is fixed first after WP6. The fix will evaluate each
definition on its own, as the BPO architect asks, and match the parent's label in the genus
position. Both halves stand.

The three detection requirements are in our roadmap (third reference) as requirements, not
as defects with a known fix, under the BPO architect's framing: a check can flag a
candidate, and deciding semantic identity needs a person.

## What we expect next

The BPO commit for S2u and S2 when you name it, and Phase B's results as a reply to this
message.
