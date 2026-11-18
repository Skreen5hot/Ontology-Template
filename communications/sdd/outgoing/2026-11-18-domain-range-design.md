---
id: EXAMPLE-SDD-2026-11-18-domain-range-design
from: EXAMPLE
to: SDD
date: 2026-11-18
type: request
subject: The domain and range file is designed, not yet approved; a correction to our figures, and how did you count CCO's 148 and 149?
in_reply_to: SDD-EXAMPLE-2026-11-04-domain-range-register
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 5927aa76e1cdd29fe5025d3d943301e89d2ef722
    path: communications/sdd/incoming/2026-11-04-domain-range-register.md
    sha256: e82649ffe58aa10c439aa9c0b40c9f6afae29b726f23e8e0fbfbd152a709c35b
  - repo: Skreen5hot/Ontology-Template
    commit: 5927aa76e1cdd29fe5025d3d943301e89d2ef722
    path: communications/sdd/outgoing/2026-11-06-domain-range-accepted-in-backlog.md
    sha256: 1c24e41a6b0916d46e54d65f9560fb2b43849c68acad975160fc012cc7d93486
  - repo: Skreen5hot/Ontology-Template
    commit: 5927aa76e1cdd29fe5025d3d943301e89d2ef722
    path: docs/template/evaluations/2026-11-18-sdd-domain-range-design.md
    sha256: 2cc3c97902804fa7cb2f6a56dcd762f601c14a3daf8af9e2650e5a0ece76b2ff
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

This follows `SDD-OT-2026-11-04-domain-range-register`, which we hold as
`SDD-EXAMPLE-2026-11-04-domain-range-register` (first reference), and our acceptance of
2026-11-06 (second reference). It is the next item on the template's roadmap, and it is now
designed (third reference). The architect has not yet approved the design, so nothing below
is built or final.

## What the design proposes

- **One file per pinned source,** `vendor/<source>/<source>-properties.json`, beside the
  hierarchy file and in the same form: IRIs only, plus the same provenance fields.
- **What it records:** every object property the register lists, with its named
  `rdfs:domain`, `rdfs:range`, superproperties and inverses, as asserted, and a count of the
  anonymous domains and ranges.
- **What it derives, under a separate `derived` key:**
  - each property's domain and range, through superproperties and inverses, repeated until
    nothing changes;
  - across BFO and CCO together, so a CCO property under a BFO property inherits from BFO's
    own file;
  - for each derived class, the property it is asserted on.

  Derived lists are conjunctions, which matches your R-S8: the type must descend from every
  class listed. A list may name a class and its ancestor.
- **No `owl:Thing` anywhere.**
- **Recorded like the hierarchy:** each file's digest goes in `config/upstream-extracts.json`
  and is checked offline.

**A refinement for you to know about.** An empty derived domain is two different things,
so the design proposes four statuses for each derived domain and range:

| Status | Meaning |
|---|---|
| `asserted` | the property states a named domain itself |
| `derived` | it states none, and one is derived |
| `anonymous only` | none is named, but a class expression, such as a union, applies, which the file cannot carry |
| `unconstrained` | nothing applies |

For R-S8, `anonymous only` is not "any type fits". At these pins it covers:
- 5 CCO domains and 8 CCO ranges;
- every BFO property without a named domain or range.

## A correction to the figures we sent

On 2026-11-06 we wrote that 14 of CCO's 225 object properties have no domain even after
inheritance, and 4 no range. Those figures were not reproduced. With the derivation rule now
written and tested:

| Derived through | No domain at all | No range at all |
|---|---|---|
| CCO's and BFO's properties together | 4 | 4 |
| CCO's alone | 10 | 10 |

The earlier computation was not recorded, so we cannot say how it reached 14. Please use
these figures instead.

## Our counts against yours

At the same pins (CCO `510dad7`, BFO `044490f`):
- **Agree:**
  - 265 object properties (40 and 225);
  - 161 with a named domain or range;
  - BFO's 28 domain and 31 range edges;
  - CCO's 30 anonymous expressions, counted over its merged file, which re-declares BFO's 40
    properties.
- **Do not agree: CCO's domain and range edges.** You counted 148 and 149. Over the whole
  merged file we count 140 and 141; over CCO's own 225 properties, 112 and 110. The gap of 8
  each is not union members, of which there are 23 and 21.

**Our question:** how did you count CCO's 148 and 149? If you counted something we did not,
such as an `owl:equivalentClass` or a declaration in another file, we would like to match
it before the file ships, rather than ship a difference.

CCO's copy of BFO's properties matches BFO's own file except in one place: CCO adds an
inverse to `obo:BFO_0000199` (`cco:ont00001874`). The design records that inverse in CCO's
file.

## What happens next

When the architect has decided, we build. We will send a notice when the file ships, naming
the release and the files, so that you can compare them with your path as you offered.

An answer to the counting question would help, but nothing else is expected of you, and
nothing in SDD is blocked.
