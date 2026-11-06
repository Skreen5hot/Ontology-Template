---
id: EXAMPLE-LEGAL-2026-11-06-t9-policy-adopted
from: EXAMPLE
to: LEGAL
date: 2026-11-06
type: answer
subject: T9 is closed; the architect adopted the template's behaviour as policy
in_reply_to: EXAMPLE-LEGAL-2026-10-28-t9-third-party-text
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 626ac9ab5a742c9109875b3c4498961d4e550ff4
    path: communications/legal/outgoing/2026-10-28-t9-third-party-text.md
    sha256: b3d1d76c5fb4da1e5ddbea9379a8bdc2faf2896bbc435022588509d1efb34668
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

## What changed

The request of 2026-10-28 asked Legal five questions about third-party text inside an
ontology. No Legal correspondent exists to answer them. On 2026-11-06 the architect
answered them instead: "Adopt the current behaviour as my policy; I accept the risk"
(template decision 33).

## The policy

1. A declaration is the annotation property, the source, its release, the licence (an SPDX
   identifier or `unknown`) and the attribution text.
2. The report says: "This report records what the project declares about third-party text
   and checks that the declared source, release and attribution are present. It does not
   judge whether the text may be redistributed." The PENDING LEGAL prefix is removed.
3. Text whose licence is `unknown` is reported, and passes, when it is declared and its
   module carries the declared attribution.
4. The attribution is checked on the module header only.
5. The template refuses nothing for publication by its licence.

## What it does not do

It grants no project permission to redistribute any text. Whether a project may do so stays
that project's question; BPO's B2 stays BPO's.

Nothing is asked of LEGAL. This answer closes the thread.
