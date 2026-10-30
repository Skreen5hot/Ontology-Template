---
id: BCO-EXAMPLE-2026-10-30-process-proposals-answer
from: BCO
to: EXAMPLE
date: 2026-10-30
type: answer
subject: Answer -- the decision path and lanes are right; add a rights build item; narrow P4 and P6
in_reply_to: EXAMPLE-BCO-2026-10-30-process-proposals
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 4521158b4d1f1c0866093e9995058b902a529606
    path: communications/bco/outgoing/2026-10-30-process-proposals.md
    sha256: 5cdba2d209576719111af568941d9fd1f0655972d29f42fe1bee5c0fb9375b75
author: Claude Code (agent), drafted at Aaron Damiano's direction
requires_act: true
source:
  repo: Skreen5hot/Business-and-Agent-Capabilities-Ontology
  commit: 4c66a535015945ee28dfa94fc5f6878dfbd457f0
  path: communications/example/outgoing/2026-10-30-process-proposals-answer.md
  sha256: ea457afb3e02d627db15b5bda5c656b7dac87cdf6e81e32acf70a33dbcd81328
---
---
id: BCO-EXAMPLE-2026-10-30-process-proposals-answer
from: BCO
to: EXAMPLE
date: 2026-10-30
type: answer
subject: Answer -- the decision path and lanes are right; add a rights build item; narrow P4 and P6
in_reply_to: EXAMPLE-BCO-2026-10-30-process-proposals
refs:
  - repo: Skreen5hot/Business-and-Agent-Capabilities-Ontology
    commit: 08c932f0d39961686d6a5e1cccb8e00d6d0e6f4e
    path: src/02_conceptual_models/CM-01-business-capability.md
    sha256: 292c8f36d64075b9663e159985a15b448aa933c3b5ed4baff3b2a556ca861ccc
  - repo: Skreen5hot/Business-and-Agent-Capabilities-Ontology
    commit: 08c932f0d39961686d6a5e1cccb8e00d6d0e6f4e
    path: src/03_taxonomy/README.md
    sha256: 0d4217e1958bc30b82295408b4c9f6987a0d74acc367635be24d06e92f9c43ce
  - repo: Skreen5hot/Business-and-Agent-Capabilities-Ontology
    commit: 08c932f0d39961686d6a5e1cccb8e00d6d0e6f4e
    path: tools/sources/build_register.py
    sha256: 0d630bb50d1daefa4a698d7c2c0361f85ae5c877c85211339b90e2e29bd427ed
  - repo: Skreen5hot/Business-and-Agent-Capabilities-Ontology
    commit: 08c932f0d39961686d6a5e1cccb8e00d6d0e6f4e
    path: docs/sources/inventory/rights.yaml
    sha256: dfea0b3606903d71fac94516513e010acc3c81d2d2e52cf7d1890cb8bef0e262
author: Claude Code (agent), drafted at Aaron Damiano's direction
requires_act: false
---

# Answer: the path and lanes are right; add a rights build item; narrow P4 and P6

Thank you for reading BCO at `08c932f` and for the proposal. Our answers follow your six
questions. Where we cite BCO, it is at that commit, by the digests in this message's refs.

## Your two observations

Both hold.

- **Stage 03's README** says "not started" and does not point at the Capability Term
  Inventory under `docs/sources/inventory/`, which is the stage's input. BCO will fix the
  README for its own sake.
- **CM-01's stakeholder checkbox** (§10) ticks "Domain stakeholders have reviewed the
  model" on R8, R9 and the architect's review. By the Stage 02 standard's own words, that
  overstates the gate unless the architect reviewed as a domain practitioner. CM-01 is
  approved, so the record is not edited: whether it is corrected by an erratum or a new
  version is the architect's decision, and BCO will record it.

## 1. The decision path and lanes

They match what happened better than the single line in our account. Our account put
"vocabulary and taxonomy population" before formalization; the real lesson was narrower:
catalog terms are admitted only once the admission criteria exist. We withdraw the strict
order.

One refinement: the lanes are not independent; they **join the path at named gates**.

- Metamodel vocabulary (P0 to P3) waited for nothing.
- Catalog concepts (P5) should have waited for G1-T and DP-2; review R6 had them rewritten.
- The inventory waited for the rights review, not for the conceptual model.
- Findings also flow the other way: the homonyms the terminology work found (ISO/IEC
  33020 and CMMI "capability"; FIBF "business capability") shaped scope decisions.

The method should name the join points: catalog admission consumes the type-admission
gate, and a lane finding may raise an open issue on the path.

## 2. P1 to P7

Order by the rework each would have saved: **P1, P3, P2, P8 (below), P7, P4, P5, P6.**

- **P3** would have saved the most. BCO's specification committed before its conceptual
  model existed, so RP-1 and RP-10 were decided again in CM-01, and specification v0.5
  still owes those decisions.
- **P2** next: Stage 01 had no standard, which is how the catalog rework happened.
- **P7** is cheap and would have shown the DP-1 and DP-2 debt at once.
- **P6** last: no BCO Stage 05 work exists, so it should be designed against a real
  formalization.

**What is missing: P8, a rights and provenance record.** You agree with the rights gate
but propose nothing to build for it, and in BCO's Stage 03 it cost more than anything
else: I-1's text withheld and later released under E7, three APQC decisions and a
re-sourcing through BPO, and the eleven HR lists withheld at closure. A model exists in
`docs/sources/inventory/rights.yaml`: evidence pinned by digest, withholding as the
default, release only by a decision. Your clause is right: rights are reviewed and
recorded, and Legal decides use.

## 3. P4, the source register

It carries over, with one correction: BCO has **no check** that every source a decision
cites is V or P. It has a query (`build_register.py --claims <id> --at-least P`) and
ADR-003 D6's rule that a departure cites V or P. The check you describe would be new.

Generic, carry over: the V, P, S, K, L statuses, exactly one per claim; registered quote
keys; quotation marks only from registered quotes or declared mentions; the check that
every SRC identifier in a tracked file names an entry; the freshness check on the generated
Markdown.

BCO-specific, make a parameter or drop: the A1 to A9 authority scale, which leans to
standards bodies and enterprise architecture; the source families; the expected entry
count; the companion prose; the 15-word quote limit, a copyright policy choice; and the
`bcos:` source records, generated in `tools/vocab/build.py` in BCO's namespace.

## 4. P5, reviewer kinds

Ontologist, domain practitioner and architect are right. Add two things:

- **A rights reviewer**, since your clause gives Legal that decision.
- **The capacity a reviewer acted in.** When one person is architect and practitioner,
  the record must say which. That ambiguity is how CM-01's checkbox came to overstate the
  review.

For BCO, a domain practitioner is someone who does capability-based planning: a business
architect who maps capabilities (BIZBOK or BACM practice), a portfolio or strategy
planner, or staff of a FIBF standards lead agency.

## 5. P6, conceptual fidelity

One annotation per formal term would not work as stated:

- **Imported terms** (BFO, CCO, BPO's act types) have no conceptual-model element. Scope
  the rule to the authored namespaces.
- **Mappings are many-to-many.** One CM-01 relationship may become a class and two
  properties; the annotation must allow several elements, and pattern-level mappings.
- **Meaning changes in axioms, not terms.** A per-term annotation cannot catch an axiom
  that infers functional adequacy from components, which CM-01 forbids.

Formal choices we expect to change CM-01's meaning (expected, since none has been made):

- Formalizing DP-1's basis with BFO's `has material basis` entails Disposition, a
  commitment CM-01 does not make.
- Conditional standing-function designation cannot be an OWL class; it becomes a SHACL rule
  or an information entity.
- A competency question about a capability never exercised needs a closed-world check.

## 6. What the response missed

- **P8**, above.
- **Upstream coordination.** The charter names the ontologies a project depends on, but
  the method says nothing of the working relation: pins, re-pins, notice gates, a
  communications protocol. With BPO that was recurring work (re-pins R1 to R5; the
  e3ee6ad notice gate).
- **What is normative before ratification.** In BCO, nothing. The method should say so
  outright: BCO's specification has stayed a draft through every stage so far.
