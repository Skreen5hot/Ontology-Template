---
id: EXAMPLE-SDD-2026-11-06-domain-range-accepted-in-backlog
from: EXAMPLE
to: SDD
date: 2026-11-06
type: answer
subject: Accepted; the domain and range file is in our backlog, not yet built
in_reply_to: SDD-EXAMPLE-2026-11-04-domain-range-register
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: a645d34fcd22c5827238771dba3f988c96c534b1
    path: communications/sdd/incoming/2026-11-04-domain-range-register.md
    sha256: e82649ffe58aa10c439aa9c0b40c9f6afae29b726f23e8e0fbfbd152a709c35b
  - repo: Skreen5hot/Ontology-Template
    commit: 4d328d5bfbb13ecadf9681eefe00190b0965a8f1
    path: docs/template/DECISIONS.md
    sha256: c21a01c6a6fffb00d31a32241dc40910e1c7551386934d658a188095e336b297
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

This answers `SDD-OT-2026-11-04-domain-range-register`, which we hold as
`SDD-EXAMPLE-2026-11-04-domain-range-register` (first reference). We should have answered
sooner.

## Accepted

The architect accepted your request on 2026-11-05 (template decision 28, second reference).
For each pinned source, a file of every object property its register lists, with:

- its named `rdfs:domain` and `rdfs:range` values as asserted, and a count of anonymous ones;
- its superproperties and inverses;
- a derived effective domain and range, computed through inheritance and labelled as
  derived.

Where the source states no domain or range, none is written: no `owl:Thing` is filled in.
At these pins, 14 of CCO's 225 object properties have no domain even after inheritance, and
4 no range; the file will mark them unconstrained.

## Not yet built

It is in the template's backlog, after P7, P8, P6 and the remaining process findings
(P-A2, P-A4 to P-A6, P-A8), so it is not in the current release, v0.5.0. We will send a
notice when it ships, naming the release and the file.

Nothing is asked of you; no reply is needed.
