---
id: SDD-EXAMPLE-2026-11-04-domain-range-register
from: SDD
to: EXAMPLE
date: 2026-11-04
type: request
subject: Ship every object property's named rdfs:domain and rdfs:range, from the same pins, like the hierarchy registers
in_reply_to: null
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: vendor/cco/cco-hierarchy.json
    sha256: 8d2461b9a5805141713d54e618ad102c18dd7db0680e86a11beb2a4f7c054194
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: config/upstream-extracts.json
    sha256: 734c25b37b60113631036fd3bb5d0be2a014014d8f6cedb058d9736a782efe36
  - repo: CommonCoreOntology/CommonCoreOntologies
    commit: 510dad76be0ef710b65a421075af912af25342b7
    path: src/cco-merged/CommonCoreOntologiesMerged.ttl
    sha256: e609db27478a2c8b52b9bb5eb5ac979ac323510e851c368e4d9ec7d1c153fe5b
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 71c08e2d25d01d6231bfc331d9bb4c31c5574c2c
    path: project/DECISIONS.md
    sha256: b1858aabb2a419008200ab7ef20bb7410f67cbbb832f8e1843bd51f895368e00
author: Claude (agent), drafted at the direction of Aaron Damiano (SDD registrar)
requires_act: true
source:
  repo: Skreen5hot/SemanticDataDictionary
  commit: bebbb0e552c524775da4bc6e37c25a4f90366bbc
  path: communications/ot/outgoing/2026-11-04-domain-range-register.md
  sha256: 1d87305097270e90052a1d605a92a0a28e680b82ca99562a656a0dccd81bda84
---
---
id: SDD-OT-2026-11-04-domain-range-register
from: SDD
to: OT
date: 2026-11-04
type: request
subject: Ship every object property's named rdfs:domain and rdfs:range, from the same pins, like the hierarchy registers
in_reply_to: null
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: vendor/cco/cco-hierarchy.json
    sha256: 8d2461b9a5805141713d54e618ad102c18dd7db0680e86a11beb2a4f7c054194
  - repo: Skreen5hot/Ontology-Template
    commit: 7cfdfbfe5dde13be7a0fd99b52711bdb0cdee3fb
    path: config/upstream-extracts.json
    sha256: 734c25b37b60113631036fd3bb5d0be2a014014d8f6cedb058d9736a782efe36
  - repo: CommonCoreOntology/CommonCoreOntologies
    commit: 510dad76be0ef710b65a421075af912af25342b7
    path: src/cco-merged/CommonCoreOntologiesMerged.ttl
    sha256: e609db27478a2c8b52b9bb5eb5ac979ac323510e851c368e4d9ec7d1c153fe5b
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 71c08e2d25d01d6231bfc331d9bb4c31c5574c2c
    path: project/DECISIONS.md
    sha256: b1858aabb2a419008200ab7ef20bb7410f67cbbb832f8e1843bd51f895368e00
author: Claude (agent), drafted at the direction of Aaron Damiano (SDD registrar)
requires_act: true
---

## Request

Please ship, for each source (BFO and CCO), the **named `rdfs:domain` and `rdfs:range` of every object property its
register lists**, derived from the same pinned file as the register and recorded in your manifest with a digest, the
way you now ship the class hierarchy.

## Why

SDD checks that a relation fits the types it connects (our rule R-S8): the contained type's class must descend from
every named domain of the relation, and the container type's from every named range. Your hierarchy registers carry
superclasses only, so SDD still reads domain and range from `CommonCoreOntologiesMerged.ttl` (third reference) and
your BFO extract. That is the last thing keeping our second derivation path alive (ADR-009, fourth reference). With
this, we delete our copy of the CCO file and build from your artifacts alone.

## A sketch, not a demand

The form is yours to choose. What we would use, by analogy with `cco-hierarchy.json`:

- `properties`: each object property the register lists, with `domain` and `range`, each a sorted list of named IRIs
  (empty when there is none);
- a count of the anonymous domain and range expressions dropped (class expressions such as unions), since we do not
  evaluate those;
- the register's provenance fields: `source`, `release`, `commit`, `files`, `licence`, `attribution`;
- its digest in `upstream-extracts.json`.

It could equally be keys added to the hierarchy files. For comparison: at the current pins we read 265 object
properties, 161 of which have a named domain or range (BFO: 28 domain and 31 range edges; CCO: 148 and 149), and 30
anonymous expressions in CCO. We will compare yours against ours and tell you if they differ, as we did for the
hierarchy.

## Not urgent

Our current path works and is digest-bound to the same pin, so nothing in SDD is blocked. It can wait for your WP6.
