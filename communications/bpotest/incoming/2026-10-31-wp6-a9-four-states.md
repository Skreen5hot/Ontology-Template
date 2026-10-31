---
id: BPOTEST-EXAMPLE-2026-10-31-wp6-a9-four-states
from: BPOTEST
to: EXAMPLE
date: 2026-10-31
type: request
subject: Amendment A9 submitted for formal acceptance — a fourth state (S2u) separating BPO's corrections from the template's effects; P-B1 confirmed; three detection requirements
in_reply_to: EXAMPLE-BPOTEST-2026-10-30-wp6-amendments-decided
refs:
  - repo: Skreen5hot/BPO-Template-Port
    commit: 4cf6c4bf03b7384305307c1488825a8fe21e6a9b
    path: research/wp6/phase-b/change-record.md
    sha256: 7359b8c069920d979c31ab7c0326a093035e39d16d80f810e0fa27eb3152110b
  - repo: Skreen5hot/Ontology-Template
    commit: 08f2bf8263cc19903222c58ac09f980c9ec44a41
    path: communications/bpotest/incoming/2026-10-31-wp6-phase-a-supplement.md
    sha256: 1ff0ba64cf7c476e7de4c7d1a3756e844a98f9bf43d36fc6c0129d5b96448fc4
author: Aaron Damiano, the BPO architect and PO (the amendment); Claude (agent), at the architect's direction (the port notes and the rest)
requires_act: true
source:
  repo: Skreen5hot/BPO-Template-Port
  commit: 62ef12ca81cf17246682cd8c963ba5f4ebefc931
  path: communications/example/outgoing/2026-10-31-wp6-a9-four-states.md
  sha256: 819253e3fb9428bcb21c11b8bf3d9bb70e433fbe5ebaf331cefce5a4f0cc3373
---
---
id: BPOT-EXAMPLE-2026-10-31-wp6-a9-four-states
from: BPOT
to: EXAMPLE
date: 2026-10-31
type: request
subject: Amendment A9 submitted for formal acceptance — a fourth state (S2u) separating BPO's corrections from the template's effects; P-B1 confirmed; three detection requirements
in_reply_to: EXAMPLE-BPOT-2026-10-30-wp6-amendments-decided
refs:
  - repo: Skreen5hot/BPO-Template-Port
    commit: 4cf6c4bf03b7384305307c1488825a8fe21e6a9b
    path: research/wp6/phase-b/change-record.md
    sha256: 7359b8c069920d979c31ab7c0326a093035e39d16d80f810e0fa27eb3152110b
  - repo: Skreen5hot/BPO-Template-Port
    commit: 003e44ae98f97d31539a6ddefbd2b03f46edc029
    path: communications/example/outgoing/2026-10-31-wp6-phase-a-supplement.md
    sha256: 714dfa5b8b036b934479d801fbb1b4feee3f9b1e84049848d462a0d82b67ff1a
author: Aaron Damiano, the BPO architect and PO (the amendment); Claude (agent), at the architect's direction (the port notes and the rest)
requires_act: true
---

This continues the WP6 thread after our Phase A results and their supplement (second
reference). The BPO architect submits protocol amendment A9 for the Template Team's formal
review and acceptance, before Phase B's states are measured, hence `requires_act: true`.

The amendment follows in the architect's words. After it come the port's notes on how it
will be met in this run, then P-B1 and three detection requirements, which need no decision
now.

## A9, as submitted by the BPO architect

The amendment introduces a fourth experimental state, **S2u**, to distinguish changes
originating in BPO's source ontology from changes introduced by the ontology template and
its engineering process.

### 1. Rationale

The objective of WP6 is to determine both:

1. What changes when BPO is subjected to the template's tools, checks, and modeling process.
2. Whether those changes improve the ontology's quality.

The original S0/S1/S2 design provides valuable comparisons, but S2 incorporates both
corrections to BPO and the application of the template. Without an additional control
state, the effects of these two interventions cannot be adequately separated.

The proposed amendment addresses this limitation without modifying S0 or S1.

### 2. Experimental states

| State | BPO source | Template changes |
|---|---|---|
| S0 | Original source | Not applied |
| S1 | Original source | Applied |
| S2u | Corrected source | Not applied |
| S2 | Corrected source | Applied |

S2u and S2 must use exactly the same immutable BPO source commit and pinned ontology
dependencies.

The original S0 and S1 baselines will remain unchanged.

### 3. Required comparisons

**S0 → S1:** Measures changes introduced through the template process when operating on the
original BPO source.

**S0 → S2u:** Measures changes attributable to approved BPO source corrections, using the
unchanged port process.

**S2u → S2:** Measures changes introduced by the template when operating on corrected BPO.

**S0 → S2:** Measures the combined result of BPO corrections and template intervention.

Comparing the two template effects also allows us to identify interactions between the
corrected source and the template process.

All comparisons must use explicit provenance and reproducible build configurations.

### 4. What must be measured

The comparison must separately record:

- Changes in class declarations and asserted subclass axioms.
- Changes in reasoner-derived class hierarchies.
- Changes in other logical axioms and entailments.
- Changes in definitions, labels, comments, and provenance.
- Changes in the intended semantic interpretation of relationships.
- Changes in validation findings and operational behavior, including capability-based
  process dispatch.

Identical class hierarchy entailments must not be reported as proof of complete semantic
equivalence.

Changes must be classified by type, cause, and expected consequence.

### 5. Reproducibility requirements

Each state must record its exact source commit, template commit, BFO/CCO dependency
versions, port configuration, validation configuration, and reproducible output
identifiers.

For S2u and S2, the corrected BPO source SHA must be identical.

Any unavoidable changes to comparison tooling or dependencies must be declared and
accounted for separately.

### 6. Preservation of experimental evidence

Previously observed defects must not be erased from the historical record merely because
corrections are subsequently accepted.

In particular, WP6 has identified significant issues involving class identity, duplicated
annotations, redundant parent assertions, capability-bearing entities, process-dispatch
requirements, and validation behavior.

These findings are part of the evidence used to assess the template's effectiveness.

The record must distinguish defects found automatically by the template, defects discovered
through human analysis, and defects that escaped the template's checks.

### 7. Quality assessment remains separate

A9 changes the experimental comparison design, not the goal of the final quality
evaluation.

The team must first establish what changed and why.

Only after completing that analysis should we decide whether the resulting ontology is more
ontologically correct, semantically accurate, logically coherent, and maintainable.

Semantic change is neither automatically beneficial nor automatically defective.

### 8. Requested decision

I support adopting A9 and request formal approval by the Template Team.

Upon acceptance, update the WP6 protocol and comparison tooling, retain the original S0/S1
historical evidence, and proceed with S2u and S2 using the approved BPO correction commit.

The final evaluation report must identify A9 as a protocol amendment and explain its
rationale and effect on the experimental design.

**The purpose of the amendment is to make our eventual claims about the ontology template
more precise, reproducible, and defensible.**

— BPO Architecture Review

## Port notes: how this run will meet A9

- **The existing states.** S0 and S1 are both ported from BPO `bc64e91`, tagged `s0` and
  `s1`, and stay as they are. Their manifests (`research/wp6/measure/s0|s1/manifest.tsv`)
  record what §5 asks for: the content commit, the instrument commit, the template
  revision, every Python distribution, Java, ROBOT's sha256, the upstream artifact digests,
  and the digest of every check, shape and config file. S2u and S2 will get the same.
- **No S2 commit exists yet.** BPO is preparing its corrections on a reviewable branch. We
  will name one immutable BPO commit for both S2u and S2 once it passes BPO's complete
  suite and A9 is accepted.
- **One declared change to the port's mechanics (§5).** From S2u on, in both modes, the
  port keeps each module header's `dct:rights` (APQC's notice), which APQC's licence
  requires on every derivative. It touches only module headers, which the lossless check
  excludes. S0 → S2u therefore carries this one port change besides BPO's corrections, and
  the record will separate it.
- **Back-ported changes keep their origin (§6).** BPO is adopting four changes the template
  process prompted: the release on each module, property definitions, the re-typed
  `requires*` properties, and the top concepts. They will appear in S2u because they are
  now in BPO's source, but the record attributes them to the template process.
- **The four measurement layers (§4)** already exist for S0 and S1 as separate files:
  asserted axioms and the inferred hierarchy (`entailments.tsv`, ELK, indirect pairs
  included), annotation text, and findings. S0 and S1 entail the same 19,112 subclass pairs;
  we report that as hierarchy equality only.

## P-B1, confirmed

The genus check (`shapes/realist_shapes.ttl`, "Genus") passes a class when *any* of its
definitions *contains* the parent's label anywhere in the text. The BPO architect confirms
this as a template detection gap, and asks that the check evaluate each definition
independently, so that one matching definition cannot hide a conflicting one.

The second half of P-B1, a label matched anywhere rather than in the genus position, stands
as reported in our supplement.

## Three detection requirements

Found in BPO's Phase B work. No check in v0.1.0 finds any of them:

1. **Possible homonyms:** one IRI used for two different kinds. BPO has one, for example:
   PerformanceMeasure means a measure specification in one module and a measured value in
   another.
2. **Duplicate classes:** two IRIs for what may be one kind. BPO had two senior-management
   role classes minted in different modules.
3. **Over-claiming relations:** a relation whose name or definition claims more than its
   axioms support. In BPO, a capability "enables" a process, and the pair was then read as
   the process *requiring* the capability, with no axiom saying so.

The BPO architect's position: these should not be counted as solved by adding syntactic
checks. A check can *flag a candidate*, such as one IRI with conflicting genera across
modules, or two classes with near-identical definitions. Deciding semantic identity still
needs a person. We record them as requirements, not as defects with a known fix.

## What we ask

The Template Team's formal decision on A9, before the four-state measurement. P-B1 and the
three requirements need no decision now: A7 keeps the instrument fixed until WP6 ends.
