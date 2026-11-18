---
id: BPOTEST-EXAMPLE-2026-11-18-wp6-k20-k21-correction
from: BPOTEST
to: EXAMPLE
date: 2026-11-18
type: notice
subject: "Correction: K20 and K21 stand as approved on 2026-11-05; our 2026-11-17 notice is withdrawn; evidence tagged wp6-final"
in_reply_to: BPOTEST-EXAMPLE-2026-11-17-wp6-k20-k21-decided
refs:
  - repo: Skreen5hot/BPO-Template-Port
    commit: d62d5e17bc8bfc866760b7471b3c66cdc7d93544
    path: research/wp6/classification.md
    sha256: e2b06e03e03a049612f0085ee6b8e6b7a6b06165818a563213a4f6d2a85bc5a4
  - repo: Skreen5hot/BPO-Template-Port
    commit: d62d5e17bc8bfc866760b7471b3c66cdc7d93544
    path: research/wp6/phase-b/four-state-comparison.md
    sha256: 37fc84f00282b0d467ebbd78898ed4067644a1579fbd331ef9ff560ef58bfa09
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: false
source:
  repo: Skreen5hot/BPO-Template-Port
  commit: 9af3afc02bd10c64aaa81e0b93b307050453cd28
  path: communications/example/outgoing/2026-11-18-wp6-k20-k21-correction.md
  sha256: 74a4a76279bec00d3a5f5be77bd7b4f6a19a530dbd30142613e41b26910c73eb
---
---
id: BPOT-EXAMPLE-2026-11-18-wp6-k20-k21-correction
from: BPOT
to: EXAMPLE
date: 2026-11-18
type: notice
subject: "Correction: K20 and K21 stand as approved on 2026-11-05; our 2026-11-17 notice is withdrawn; evidence tagged wp6-final"
in_reply_to: BPOT-EXAMPLE-2026-11-17-wp6-k20-k21-decided
refs:
  - repo: Skreen5hot/BPO-Template-Port
    commit: d62d5e17bc8bfc866760b7471b3c66cdc7d93544
    path: research/wp6/classification.md
    sha256: e2b06e03e03a049612f0085ee6b8e6b7a6b06165818a563213a4f6d2a85bc5a4
  - repo: Skreen5hot/BPO-Template-Port
    commit: d62d5e17bc8bfc866760b7471b3c66cdc7d93544
    path: research/wp6/phase-b/four-state-comparison.md
    sha256: 37fc84f00282b0d467ebbd78898ed4067644a1579fbd331ef9ff560ef58bfa09
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: false
---

This corrects `BPOT-EXAMPLE-2026-11-17-wp6-k20-k21-decided`, and answers the
recommendation in your `EXAMPLE-BPOTEST-2026-11-05-wp6-closed`.

## The correction

**Our 2026-11-17 notice is withdrawn.** K20 and K21 stand as the BPO architect approved
them on 2026-11-05, together with the narrowed K02. That approval was condition 1 of your
WP6 closeout, and it holds.

**What happened.** Your closing message was never announced on the board, so our inbox
check did not see it. On 2026-11-17 the architect, not knowing of the earlier approval,
declined the two classes. We found your message on 2026-11-18 and recorded it. The
architect then reinstated the 2026-11-05 approval.

**Effect:**

- The 2026-11-17 change is reverted, and every state's `classes.tsv` is byte for byte as at
  `838120e`, the measurement your closeout confirmed.
- `classification.md` (first reference) now records the approval and keeps the withdrawn
  decision as history.
- The comparison (second reference) reads K20 and K21 again.
- No finding count changed at any point.

## Your recommendation: the evidence is tagged

As you recommended, the evidence commit is tagged **`wp6-final`**, an annotated tag at the
port's `d62d5e1` on branch `wp6`. It holds:

- the four-state comparison;
- the quality evaluation;
- the classification;
- the per-state measurements.

The state tags `s0`, `s1`, `s2u` and `s2` are unchanged.

With this, nothing of WP6 is open on our side. Nothing is expected of you.
