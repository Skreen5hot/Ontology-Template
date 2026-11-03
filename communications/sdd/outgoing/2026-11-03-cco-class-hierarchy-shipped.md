---
id: EXAMPLE-SDD-2026-11-03-cco-class-hierarchy-shipped
from: EXAMPLE
to: SDD
date: 2026-11-03
type: answer
subject: Accepted; the CCO class hierarchy is vendored, on main and unreleased until WP6 ends
in_reply_to: SDD-EXAMPLE-2026-10-27-cco-class-hierarchy-register
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: communications/sdd/incoming/2026-10-27-cco-class-hierarchy-register.md
    sha256: eaad85187b1b8c7459100327e024e4849a28a149b0d8ccecde6abab704da15e0
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: docs/template/DECISIONS.md
    sha256: d4f3bca58b59a0a9331817b0b02ff8c1f00c99098e68f1686860980d2a1960af
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: vendor/cco/cco-hierarchy.json
    sha256: 8d2461b9a5805141713d54e618ad102c18dd7db0680e86a11beb2a4f7c054194
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: config/upstream-extracts.json
    sha256: 734c25b37b60113631036fd3bb5d0be2a014014d8f6cedb058d9736a782efe36
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

This answers `SDD-OT-2026-10-27-cco-class-hierarchy-register`, which we hold as
`SDD-EXAMPLE-2026-10-27-cco-class-hierarchy-register` (first reference), recorded
verbatim. Our record's code for this repository is `EXAMPLE`; `OT` reaches us too. We are
sorry for the week it took: you were not yet one of our correspondents, and the message
was not seen until 2026-11-02.

## The decision

The architect accepted the request on 2026-11-03 (template decision 25, second reference).
It is commit `7cfdfbf`. It was made on the template's local `main` and is pushed to
`main` on GitHub (`Skreen5hot/Ontology-Template`) in the same push as this answer, so
`7cfdfbf` is on the remote `main` by the time this answer is. Being on `main` is not a
release (below).

- **`vendor/cco/cco-hierarchy.json`** (third reference): every class the CCO register
  lists, 1,385 at v2.0, with its named direct superclasses, derived by
  `tools/ontology/vendor_upstream.py` from `CommonCoreOntologiesMerged.ttl` at `510dad76…`
  (sha256 `e609db27…`). Its digest is in `config/upstream-extracts.json` (fourth
  reference), and the offline check fails if it is edited.
- **For every source, not only `select: named` ones**, so BFO has
  `vendor/bfo/bfo-hierarchy.json` too, by the same rule.
- **A separate file**, so `cco-register.json` and the extracts are byte-identical to the
  ones your refs name.

## Where it differs from your sketch

- The keys you proposed are there: `classes`, each with `superclasses`, and
  `dropped_anonymous_superclass_axioms` (80 for CCO). So are the register's provenance
  fields: `source`, `release`, `commit`, `files`, `licence`, `attribution`.
- **One addition, `outside_namespace`.** Building it found that the registers alone do
  not close every chain. `obo:BFO_0000144`, Process Profile, is in BFO's namespace but is
  not in the pinned BFO 2020 release, so the BFO register does not list it; and it is
  outside CCO's namespace, so the CCO register does not either. CCO v2.0's Event Ontology
  declares it, as a subclass of `obo:BFO_0000003` (Occurrent), and puts 12 classes under
  it; 74 CCO classes reached it and stopped. The key is relative to the source whose file
  it is in: in `cco-hierarchy.json` it holds a class outside CCO's namespace that no other
  pinned source lists and that CCO's file declares, with the superclasses CCO asserts for
  it. It preserves CCO's asserted hierarchy without modifying the pinned BFO register or
  adding the class to BFO's hierarchy. With it, every CCO class at this pin reaches
  `obo:BFO_0000001`, through `cco-hierarchy.json` and `bfo-hierarchy.json` together, and
  `cco:ont00000331` (House) reaches material entity. A test holds both.
- So a byte-for-byte comparison with your derivation will differ by that key and by the
  provenance fields. Comparing the `classes` map should be exact, and if it is not, we
  would like to know.

## Release

Under the template's own commitment to the BPO evaluation (A7), nothing is released until
WP6 ends, so the file is on `main` and in no release or tag. You can cross-check against `7cfdfbf`
on the remote `main` now; the release that carries it will be the first after WP6.

## Not decided

Whether the template's IRI linter should report a reference to a term the pinned BFO
release does not have, such as `obo:BFO_0000144`. It is declared in the pinned graph as a
whole (by CCO), but not by the ontology that owns its namespace. How the SDD Service
checks categories would help us decide: by membership in the namespace owner's pinned
release, under which `BFO_0000144` is an error, or by the effective CCO and BFO class
hierarchy, under which it is a CCO-declared class under Occurrent.
