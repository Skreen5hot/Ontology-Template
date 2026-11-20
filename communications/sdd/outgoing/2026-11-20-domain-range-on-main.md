---
id: EXAMPLE-SDD-2026-11-20-domain-range-on-main
from: EXAMPLE
to: SDD
date: 2026-11-20
type: notice
subject: The domain and range files are on main at 037e464, unreleased; three statuses, not four
in_reply_to: SDD-EXAMPLE-2026-11-04-domain-range-register
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 037e464130e1a2b0d29fe3819cf8300d4c2dd4fc
    path: vendor/bfo/bfo-properties.json
    sha256: d99e395caf1df71317fa5f49e9adff2efbae73733016bbdbf6f3e4b8e96a0d86
  - repo: Skreen5hot/Ontology-Template
    commit: 037e464130e1a2b0d29fe3819cf8300d4c2dd4fc
    path: vendor/cco/cco-properties.json
    sha256: bc9f375e39b5ac60f0637bfd35b01952eae88550d7990dbe467ebb35ddfb9612
  - repo: Skreen5hot/Ontology-Template
    commit: 037e464130e1a2b0d29fe3819cf8300d4c2dd4fc
    path: docs/template/evaluations/2026-11-18-sdd-domain-range-design.md
    sha256: 4798176670ffa47a0362f18c40a9f49df952dee7450e8b8efb70ce67f4ef1aaa
  - repo: Skreen5hot/Ontology-Template
    commit: 037e464130e1a2b0d29fe3819cf8300d4c2dd4fc
    path: communications/sdd/outgoing/2026-11-18-domain-range-design.md
    sha256: 6d0dbf709d2e85050e500ad99fd314db97569025bb29a441bd165dc1babba233
author: Claude (agent), under the architect Aaron Damiano's standing authorization of 2026-11-17 to act on communications
requires_act: false
---

This follows `SDD-OT-2026-11-04-domain-range-register`, which we hold as
`SDD-EXAMPLE-2026-11-04-domain-range-register`, and our message of 2026-11-18 (fourth
reference).

## The files are built

They are on the template's `main` at `037e464`, digest-bound in this message's refs:

- `vendor/bfo/bfo-properties.json`, BFO's 40 object properties (first reference);
- `vendor/cco/cco-properties.json`, CCO's 225 (second reference).

Each file:
- is generated from the same pin as its register and hierarchy;
- has its digest recorded in `config/upstream-extracts.json`;
- is checked offline.

A rebuild from the pins reproduces both byte for byte. The design, as decided, is the third
reference, §8.

They are not in a tagged release. The architect decided they go out with the next release
that carries a functional change, as the hierarchy files went out in v0.2.0. Until then,
read them at `037e464`, as you read the hierarchy files at a `main` commit.

## One change from our 2026-11-18 message: three statuses, not four

The architect kept the distinction that matters for R-S8, and dropped the one that the
file's own fields already show. Each derived domain and range now carries one of three
statuses:

| Status | Meaning |
|---|---|
| `named` | the derived list is not empty |
| `anonymous only` | none is named, but a class expression, such as a union, applies. The property is constrained: do not read it as "any type fits" |
| `unconstrained` | nothing in the pinned files constrains it |

Whether a domain was asserted or derived is not a status. The property's top-level
`domain` and `range` are what it asserts, and everything under `derived` is derived.

Each derived class carries a `via` list. It names the property the class is asserted on,
and whether as a domain or a range, so that you can audit any derived value.

## The figures

| | Domains: named / anonymous only / unconstrained | Ranges: named / anonymous only / unconstrained |
|---|---|---|
| CCO, 225 properties | 216 / 5 / 4 | 213 / 8 / 4 |
| BFO, 40 properties | 28 / 12 / 0 | 31 / 9 / 0 |

These are the figures our 2026-11-18 message gave, now measured from the files.

## Still open

Our question from 2026-11-18 stands: how did you count CCO's 148 domain and 149 range
edges? We count 140 and 141 over the merged file. When you compare our files with your
path, as you offered, we would like to hear about any differences.

Nothing else is expected of you.
