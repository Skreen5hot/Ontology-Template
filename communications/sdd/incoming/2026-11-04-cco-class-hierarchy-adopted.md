---
id: SDD-EXAMPLE-2026-11-04-cco-class-hierarchy-adopted
from: SDD
to: EXAMPLE
date: 2026-11-04
type: answer
subject: Adopted; your classes map equals our derivation for every class; how SDD checks categories
in_reply_to: EXAMPLE-SDD-2026-11-03-cco-class-hierarchy-shipped
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: vendor/cco/cco-hierarchy.json
    sha256: 8d2461b9a5805141713d54e618ad102c18dd7db0680e86a11beb2a4f7c054194
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: vendor/bfo/bfo-hierarchy.json
    sha256: dc404065db47eddd820124e977095d8278c09317373302342a9a7846835e4947
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 71c08e2d25d01d6231bfc331d9bb4c31c5574c2c
    path: project/DECISIONS.md
    sha256: b1858aabb2a419008200ab7ef20bb7410f67cbbb832f8e1843bd51f895368e00
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 71c08e2d25d01d6231bfc331d9bb4c31c5574c2c
    path: ontology/term-list.json
    sha256: b4f223de0d93bf56c774b723f6093c092aa935c4d9f2a457ed487fd56e213e46
author: Claude (agent), drafted at the direction of Aaron Damiano (SDD registrar)
requires_act: false
source:
  repo: Skreen5hot/SemanticDataDictionary
  commit: bebbb0e552c524775da4bc6e37c25a4f90366bbc
  path: communications/ot/outgoing/2026-11-04-cco-class-hierarchy-adopted.md
  sha256: a4fc284a79c85e024a9995e46220956c8b71d585ec389f609d6642cbe3639234
---
---
id: SDD-OT-2026-11-04-cco-class-hierarchy-adopted
from: SDD
to: OT
date: 2026-11-04
type: answer
subject: Adopted; your classes map equals our derivation for every class; how SDD checks categories
in_reply_to: OT-SDD-2026-11-03-cco-class-hierarchy-shipped
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: vendor/cco/cco-hierarchy.json
    sha256: 8d2461b9a5805141713d54e618ad102c18dd7db0680e86a11beb2a4f7c054194
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: vendor/bfo/bfo-hierarchy.json
    sha256: dc404065db47eddd820124e977095d8278c09317373302342a9a7846835e4947
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 71c08e2d25d01d6231bfc331d9bb4c31c5574c2c
    path: project/DECISIONS.md
    sha256: b1858aabb2a419008200ab7ef20bb7410f67cbbb832f8e1843bd51f895368e00
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 71c08e2d25d01d6231bfc331d9bb4c31c5574c2c
    path: ontology/term-list.json
    sha256: b4f223de0d93bf56c774b723f6093c092aa935c4d9f2a457ed487fd56e213e46
author: Claude (agent), drafted at the direction of Aaron Damiano (SDD registrar)
requires_act: false
---

This answers `OT-SDD-2026-11-03-cco-class-hierarchy-shipped`, which you hold as
`EXAMPLE-SDD-2026-11-03-cco-class-hierarchy-shipped`. Thank you for it, and no apology is needed for the week.

## We adopted it

The registrar decided to take the class hierarchy from your hierarchy registers and to re-pin the SDD to
`7cfdfbf` (our ADR-009, third reference). We asked for this register; using it is how we validate it. Our term
list (fourth reference) now reads every class's named superclasses from `bfo-hierarchy.json` and `cco-hierarchy.json`,
each checked against the `hierarchy_sha256` in your `upstream-extracts.json`, including `outside_namespace`.

We know `7cfdfbf` is on your `main` and in no release (your A7). We pin by commit and digest, so that is enough for
us; we will re-pin to the release that carries it.

## The comparison

You asked to be told if the `classes` maps differ. They do not. Before switching we compared your files with our
own derivation (ADR-008, from the same pinned `CommonCoreOntologiesMerged.ttl` and BFO extract):

- For all 1,385 CCO classes and all 36 BFO classes, the named direct superclasses are identical.
- Recomputing every class's BFO ancestors from your two files gives exactly what we had. Our term list's
  `terms_sha256` (`a9e01756…`) did not change.
- Your counts differ from ours only in scope. We parsed every subject in CCO's merged file, which is 36 more than the
  register lists: `obo:BFO_0000144`, which you put under `outside_namespace` with the same superclass we had, and 35
  BFO classes, which your `bfo-hierarchy.json` covers. That is also why we counted 111 dropped anonymous superclass
  expressions to your 80.

## Your open question: how SDD checks categories

SDD uses both of the views you describe, for two different questions.

- **Membership (is this a term a mapping may use?)** is by the namespace owner's pinned register. A mapping may name
  only a term in our term list, which is built from your BFO and CCO registers (our rule R-S7). `obo:BFO_0000144` is
  in neither, so a mapping that names it directly is refused as an unknown term.
- **Category (what does this class fall under?)** is by the effective hierarchy: your BFO and CCO hierarchies
  together, `outside_namespace` included (our rule R-S5, named ancestry only). Under it, `obo:BFO_0000144` is a
  CCO-declared class under Occurrent, and the 74 CCO classes beneath it are Occurrents. None of them is an error.

So, for what it is worth to your IRI linter: in SDD, a reference to `obo:BFO_0000144` as a term is an error, and the
same class as a link in an ancestry chain is not. How your linter treats it is your decision; we are glad to hear what
you decide, and to be told if you think our split is wrong.

## One gap

Your hierarchy registers carry superclasses only. SDD also needs every object property's named `rdfs:domain` and
`rdfs:range` (our R-S8), and still reads those from the CCO file, so our second derivation path is not fully retired.
We ask for them in a separate request, `SDD-OT-2026-11-04-domain-range-register`.
