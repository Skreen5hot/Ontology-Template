---
id: SDD-EXAMPLE-2026-10-27-cco-class-hierarchy-register
from: SDD
to: EXAMPLE
date: 2026-10-27
type: request
subject: Vendor CCO's named class hierarchy alongside the CCO register, from the same pin
in_reply_to: null
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: vendor/cco/cco-register.json
    sha256: 6ae382fafc5b3b1098ec155bf8d5f956921a8219a282ccbda79f3ce22d61185c
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: vendor/cco/cco-extract.ttl
    sha256: 6deeea27246c7483c145f4e6c93af69d5fd1e365788cbab40c19ed67607c7ccc
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: config/upstream-sources.yaml
    sha256: 1306e479b0e1f4be43cc5ce3b32706e74863b58263e52f08e19c41c335184420
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: tools/ontology/vendor_upstream.py
    sha256: ef5a312ee7f98cbbc416583fd3cdeca48504bafa0e5cdbe3ec11ff1a853168b2
  - repo: CommonCoreOntology/CommonCoreOntologies
    commit: 510dad76be0ef710b65a421075af912af25342b7
    path: src/cco-merged/CommonCoreOntologiesMerged.ttl
    sha256: e609db27478a2c8b52b9bb5eb5ac979ac323510e851c368e4d9ec7d1c153fe5b
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 1712390110260f7a608a28ddde51e46963a1c71f
    path: project/PLAN.md
    sha256: 2ed4daf4feb6f5649c8975e6d3a3228a33b67be05f23ae7f4591ae028ecebaf1
author: Claude (agent), drafted at the direction of Aaron Damiano (SDD registrar)
requires_act: true
source:
  repo: Skreen5hot/SemanticDataDictionary
  commit: 5a3c604d03a9e6b3aaf27b760e2ac18ef0d439c5
  path: communications/OT/outgoing/2026-10-27-cco-class-hierarchy-register.md
  sha256: 16c63ddef0ad1aeb63df59215872400662e555617582069ac7101737209fb653
---
---
id: SDD-OT-2026-10-27-cco-class-hierarchy-register
from: SDD
to: OT
date: 2026-10-27
type: request
subject: Vendor CCO's named class hierarchy alongside the CCO register, from the same pin
in_reply_to: null
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: vendor/cco/cco-register.json
    sha256: 6ae382fafc5b3b1098ec155bf8d5f956921a8219a282ccbda79f3ce22d61185c
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: vendor/cco/cco-extract.ttl
    sha256: 6deeea27246c7483c145f4e6c93af69d5fd1e365788cbab40c19ed67607c7ccc
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: config/upstream-sources.yaml
    sha256: 1306e479b0e1f4be43cc5ce3b32706e74863b58263e52f08e19c41c335184420
  - repo: Skreen5hot/Ontology-Template
    commit: 114f28db82adf727f5e31aab4872ed56550e84af
    path: tools/ontology/vendor_upstream.py
    sha256: ef5a312ee7f98cbbc416583fd3cdeca48504bafa0e5cdbe3ec11ff1a853168b2
  - repo: CommonCoreOntology/CommonCoreOntologies
    commit: 510dad76be0ef710b65a421075af912af25342b7
    path: src/cco-merged/CommonCoreOntologiesMerged.ttl
    sha256: e609db27478a2c8b52b9bb5eb5ac979ac323510e851c368e4d9ec7d1c153fe5b
  - repo: Skreen5hot/SemanticDataDictionary
    commit: 1712390110260f7a608a28ddde51e46963a1c71f
    path: project/PLAN.md
    sha256: 2ed4daf4feb6f5649c8975e6d3a3228a33b67be05f23ae7f4591ae028ecebaf1
author: Claude (agent), drafted at the direction of Aaron Damiano (SDD registrar)
requires_act: true
---

## Request

Please vendor, for the CCO source, a **class hierarchy register**: for every class the CCO register lists, its
**named direct superclasses** (`rdfs:subClassOf` whose object is an IRI), derived from the **same pinned file**
(`CommonCoreOntologiesMerged.ttl` @ `510dad76…`, sha256 `e609db27…`) by `tools/ontology/vendor_upstream.py`, with
its digest recorded in `config/upstream-extracts.json` like every other vendored artifact.

## Why

The SDD Service (Skreen5hot/SemanticDataDictionary) takes its permitted BFO/CCO terms only from Ontology-Template's
pins (SDD ADR-005). It must also reject BFO category errors in proposed mappings, for example a material entity
(`cco:House`) used where a `bfo:site` is required. That needs each CCO class's ancestry up to BFO.

The pinned artifacts don't carry it today:

- `vendor/cco/cco-register.json` records every term's existence, labels, OWL types and deprecation, but **no
  superclasses**.
- `vendor/cco/cco-extract.ttl` is `select: named`, so it carries ancestry only for the 2 terms this repository
  names (by design, and correctly for the template's purpose).

So a consumer can prove a CCO term exists, but not which BFO category it falls under. Any project initialised from
the template that wants to check CCO usage, rather than only CCO spelling, has the same gap.

## Suggested shape (the architect decides)

A register-style JSON next to `cco-register.json`, generated and never hand-edited:

```json
{
  "source": "cco",
  "release": "v2.0-2024-11-06",
  "commit": "510dad76be0ef710b65a421075af912af25342b7",
  "files": [{ "url": "…/CommonCoreOntologiesMerged.ttl", "sha256": "e609db27…" }],
  "relation": "rdfs:subClassOf (named objects only; anonymous class expressions dropped and counted)",
  "classes": {
    "https://www.commoncoreontologies.org/ont00000331": { "superclasses": ["https://www.commoncoreontologies.org/…"] }
  },
  "dropped_anonymous_superclass_axioms": 0
}
```

Direct superclasses are enough. A consumer can close them transitively, and with BFO vendored in full
(`select: all`) every chain reaches `obo:BFO_0000001`.

## What SDD is doing meanwhile

SDD is **not waiting** (registrar's decision). It is implementing its own derivation from the same pinned CCO file:
same commit, verified against the same sha256, never a newer release. When Ontology-Template ships the hierarchy
register, SDD will compare the two derivations byte-for-byte as a cross-check, then adopt Ontology-Template's
artifact as the single source of truth and retire its own.

## Requested act

Decide whether the template should vendor this register for CCO (and, generally, for any `select: named` source).
Record the act in `docs/decisions/` citing this message's id, and reply here (`answer`) with the commit that ships
it, or with the reasons if declined.
