# How an ontology is built here

`PROCESS.md` is the method for building *checks*: falsification, gates, evidence,
determinism, pins. This is the method for building the *ontology* the checks serve: when
scope is fixed, how sources are weighed, where a conceptual model comes before OWL, what a
stage states before it starts, and what closes a phase.

It was written on 2026-10-30 from the Business Capability Ontology (BCO) team's account of
building BCO from an early version of this template, and from BCO's answer to the
template's response (template decision 21). BCO is cited below by what it found, because
almost every rule here is something BCO worked out by paying for its absence. The account
and the response are in the template's `docs/template/evaluations/`.

---

## 1. Nothing is normative until it is ratified

A specification, a conceptual model, a vocabulary row: each is a draft until the person
who holds the gate ratifies it, by an act recorded in `docs/decisions/`. Before that it is
a hypothesis, and may be written as one. Nothing may be implemented as if a draft had
decided it.

BCO's specification has stayed a draft through every stage so far, and that was right:
two of its foundational choices were decided again, differently, once a conceptual model
existed.

## 2. One decision path, with terminology lanes beside it

The ontology is built along **one decision path**, in strict order, because each decision
depends on the one before it:

| Stage | What it decides | Its gate | Here |
|---|---|---|---|
| `charter` | purpose, non-goals, the ontologies depended on, the competency questions | the charter approved, before any drafting | `docs/charter.md`, `competency-questions/` |
| `sources` | what the design may rely on, how well each source was read, what may be used | source adequacy; rights recorded before any harvest (§4) | `research/` |
| `conceptual-model` | the domain's kinds, relations and admission criteria, before any OWL | the model approved, with the reviews it needs (§4) | the project's choice |
| `specification` | the design, as ratified | ratification; only after the conceptual model is approved | the project's choice |
| `formalization` | classes, properties, axioms, shapes, under BFO and CCO | conceptual fidelity (§4); the checks of `DEVELOPMENT.md` | `ontology/`, `vocabulary/terms.tsv`, `shapes/` |
| `instances` | particulars, and the evidence that each instantiates its type | the competency questions answered over them | `examples/`, `competency-questions/` |

A small ontology may have no separate specification: its charter and its conceptual model
are the design, and ratifying them is the step. A project says so in `config/stages.yaml`
(§7).

Beside the path run the **terminology lanes**:

| Lane | What it holds | Here |
|---|---|---|
| `vocabulary` | a controlled vocabulary: preferred terms, definitions, review status | a SKOS concept-scheme module |
| `taxonomy` | the terms arranged for use: a catalogue, a code list, a classification of usage | a SKOS concept-scheme module, held by `shapes/skos_shapes.ttl` |
| `thesaurus` | synonyms, homonyms, mappings to other schemes | SKOS labels; SSSOM sets in `mappings/` |

The lanes are not a stage before formalization. In a realist ontology the `rdfs:subClassOf`
tree under BFO is the classification of types, and a SKOS scheme is a vocabulary about
terms; neither is built from the other. **No lane writes an OWL axiom**, and a term
hierarchy never becomes an ontological relation by being there. (`vocabulary/terms.tsv` is
not a lane: an accepted row becomes a class, so the intake belongs to formalization.)

The lanes are not independent either. They **join the path at named gates**:

- Terms about the method or the model itself (what a "capability" or a "catalog entry" is,
  as a metamodel term) may start at once. BCO's metamodel vocabulary waited for nothing.
- Terms that classify the domain's particulars wait for the conceptual model's admission
  criteria. BCO wrote its catalog concepts before those criteria existed, and an external
  review had them rewritten.
- Source evidence gathered for a lane (BCO's capability term inventory, entry by entry
  from other catalogues) waits for the rights review, not for the conceptual model. It is
  `sources` work, beside the path, and a lane consumes it only through admission.
- Findings flow the other way too. A homonym the terminology work finds ("capability" as a
  quality of a process in ISO/IEC 33020 and CMMI; "business capability" as a requirement
  record in FIBF) may raise an open issue on the path, and in BCO it shaped scope.

`config/stages.yaml` records, for each lane, the path stages it joins (§7).

## 3. A standard for every stage, before the stage starts

`PROCESS.md` §3: a gate states its conditions before the phase starts. Applied to stages,
every stage a project runs has a **standard** in `docs/standards/`, written from the
skeleton there and approved before the stage begins. A standard says what the stage takes
in and gives out, what its gate requires, who holds the gate and in what capacity, and what
is out of scope.

The template cannot write a project's standards: what a taxonomy standard demands of a
domain's terms is the project's to decide. It supplies the skeleton, and a check that a
started stage names a standard that exists (§7). BCO had a standard for one stage of six;
for the vocabulary stage, the lack of one is how the catalog rework happened.

## 4. The gates BCO found late

Each was found by doing without it.

- **Scope charter.** Purpose, non-goals, the ontologies depended on and the competency
  questions are approved before the specification is drafted (`docs/charter.md`). BCO's
  competency questions first appeared inside its specification, which then committed to
  formal choices before a conceptual baseline existed.
- **Source adequacy.** A source a design decision relies on has been read in the primary
  text, or the reliance is explicitly excused, before the decision cites it. BCO grades
  each claim by how it was verified: read in the primary text, partly read, secondary only,
  prior knowledge, behind a login.
- **Rights and provenance, before any harvest.** Before text is taken from a source, its
  rights are reviewed and recorded, and what is gathered is withheld until they are.
  Whether the text may be used is a legal decision, recorded as one, never a check's
  verdict. BCO harvested before its rights review and had to withhold the result; one
  catalogue took three decisions and a re-sourcing to settle.
- **Domain review, by the right kind of reviewer.** A gate that needs a domain
  practitioner is not passed by an ontologist's review, however good. A review records who
  did it, and in what capacity when one person holds two roles. BCO's conceptual model
  ticked "domain stakeholders have reviewed the model" on two ontology reviews and the
  architect's: the record said the gate passed when, by BCO's own account, no practitioner
  had looked.
- **Conceptual fidelity at formalization.** Each formal choice preserves the approved
  conceptual model's meaning, or documents why it changes it, in a decision. Meaning
  changes in axioms as well as in terms: an axiom that infers adequacy from components can
  break a model that forbids exactly that, with every term faithful.
- **Closure, before the next phase opens.** Every open decision is closed, or carried
  forward by name, and the list of them is a record. BCO's closure set of 2026-10-30 is
  the example.

## 5. Three separations

- **Evidence is not vocabulary, and vocabulary is not admission.** A source saying a term
  exists puts nothing in the vocabulary; a term in the vocabulary puts nothing in the
  ontology.
- **Admitting a type asserts nothing about any particular.** Asserting that a particular
  instantiates a type needs evidence of its own. (BCO's two tests, G1-T and G1-I, are this
  rule for capabilities.)
- **Conceptual approval is not ratification, and ratification is not OWL.** Each is a
  separate act, by a separate record.

## 6. Decisions, and where they go

A decision is recorded verbatim, with the digest of what it is about (`docs/decisions/`).
A decision taken in the course of the work often changes documents downstream of it: BCO
decided two foundational questions inside its conceptual model, and they still had to be
carried into the next specification by hand. Say, in the decision's effect, which
documents it changes, and carry it into each of them by name, so that a decision nobody has
carried is visible rather than remembered.

## 7. Declaring the stages a project runs

`config/stages.yaml` lists the path's stages and the lanes, each with whether the project
runs it, its status (`not-started`, `in-progress`, `done`), its standard, and the layout
components where its work lives; each lane names the path stages it joins. A project does
not inherit every stage: one with no knowledge graph or no thesaurus says `runs: false`.

`python tools/stages.py` checks it, in CI and before a commit. It refuses:

- a stage that has started, or is done, without a standard, or naming one that does not
  exist;
- a path stage done before every earlier stage the project runs is done;
- a lane done before every path stage it joins is done;
- a stage the project does not run with any status but `not-started`;
- an unknown status or layout component, a lane joining a stage that is not on the path,
  or a stage listed twice.

It does not read a standard, or judge whether a gate's conditions were met. Those are for
the person who holds the gate.

## 8. Working with the ontologies you depend on

The charter names the ontologies a project depends on; the work with them recurs. Each is
pinned, to a commit, with its digest (`DEVELOPMENT.md`, "Pins"). A re-pin is a decision,
with a record of what moved and a notice to the team that owns the upstream. Messages
between teams go in `communications/` under its protocol, so what was said, and what is
still unanswered, is a record rather than a memory. BCO re-pinned BPO five times.

## 9. Not covered yet

The gates in §4 are rules for people. Four of them are planned as checks and not yet
built, on purpose, until the BPO evaluation of the template ends (decision 21): a source
register with verification grades, reviewer kind and capacity on reviews and gates,
decision propagation, and a rights and provenance record. Conceptual fidelity is last,
because it should be designed against a real formalization. Until then, §4 is held by the
gate's holder, and a standard can say what the holder checks by hand.
