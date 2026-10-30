# Scope charter

**Status:** draft. **Approved:** not yet (the decision record that approves it, when it
does). **Holder of the gate:** the person who approves it, and in what capacity.

What this ontology is for, decided before anything else is drafted (`docs/process/METHOD.md`,
§2 and §4). A specification, a conceptual model or a module written before the charter is
approved is a hypothesis about it. Change the charter by a new decision, never silently.

Replace each paragraph below with the project's answer. Delete none of the headings: a
question that does not apply is answered "none", with why.

## Purpose

What the ontology lets someone say or answer that they cannot now, and for whom. One
paragraph.

## Non-goals

What it will not model, even where a reader might expect it to. Each with a line on why, so
that the question is not reopened by the next contributor.

## The ontologies it depends on

Each upstream, the terms or patterns it is used for, and whether this ontology is a module
of it or only reuses it. Each is pinned (`config/upstream-sources.yaml`); a sister ontology
another team owns is also a correspondent (`communications/`).

| Ontology | Used for | Relation |
|---|---|---|
| BFO 2020 | the upper categories | aligned |
| CCO | (the mid-level terms used) | aligned |

## Competency questions

What the ontology must be able to answer. Each becomes a `CQ-<number>.yaml` in
`competency-questions/`, first as `draft`; the charter says why these are the right
questions, and the files say what the answers must be.

| Id | Question | Why it is in scope |
|---|---|---|
| CQ-001 | | |

## The stages it runs

Which stages of the decision path and which lanes this project runs, and which it does
not, with why (`config/stages.yaml`).

## Who holds which gate

For each stage the project runs: who approves its standard and its gate, and in what
capacity (ontologist, domain practitioner, architect, rights). Name the domain
practitioners, or say that none has been found yet.
