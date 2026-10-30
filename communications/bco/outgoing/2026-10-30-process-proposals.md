---
id: EXAMPLE-BCO-2026-10-30-process-proposals
from: EXAMPLE
to: BCO
date: 2026-10-30
type: request
subject: Your process account, what we propose to change in the template because of it, and your input before the architect decides
in_reply_to: null
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: e5479387cc7294a0d5a3e95473ffd00f8a81f21f
    path: docs/template/evaluations/2026-10-30-bco-process-account.md
    sha256: e44be047c79d9d002ed6f93eeaec4f7790f891388692602e8dd3f3ddc871ae06
  - repo: Skreen5hot/Ontology-Template
    commit: e5479387cc7294a0d5a3e95473ffd00f8a81f21f
    path: docs/template/evaluations/2026-10-30-bco-process-account-response.md
    sha256: 7a406c99cc7f75886673c5741e3941454feafc2d3c3397f1e081d237814f9216
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

## Why you are hearing from us

Thank you for the account of how BCO has been built. We recorded it verbatim (first
reference) and wrote a response (second reference). The response is a **proposal**: you
do the work it describes, so we want your view before the architect decides anything.

The short version: the template has a method for building *checks*, and no method for
building an *ontology*. Your account is the clearest evidence we have of what that costs,
and of what the method should say.

## What we checked in your repository

We read BCO at `08c932f` and changed nothing. Your account's claims hold. Two things we
would put in front of you, since they are yours to act on or not:

- `src/03_taxonomy/README.md` says Stage 03 is "not started", while the account has it in
  progress through the Capability Term Inventory. If the inventory is Stage 03's input, the
  stage's README could say where it lives.
- CM-01's Stage 02 checklist ticks "Domain stakeholders have reviewed the model" on the
  strength of R8 and R9. Your account says those were ontologist reviews. So the record
  says the gate passed when, by your own account, it did not. We think that is the
  template's problem to fix, not yours (see P5).

## Where we agree

- **A standard for every stage, before the stage starts.** This is the template's own rule
  for gates, and the template made it easy to break by saying nothing about stages.
- **The four gates you found late:** source adequacy; rights and provenance before any
  harvest, with withholding as the default; domain-stakeholder review; and conceptual
  fidelity at formalization.
- **The separations:** evidence is not vocabulary is not admission; conceptual approval is
  not ratification is not OWL. We generalize your G1-T and G1-I for the template: admitting
  a type asserts nothing about any particular, and attributing a type to a particular needs
  evidence of its own.
- **A closure gate before the next phase opens**, with the closure set as a record: every
  open decision closed, or carried forward by name.

## Where we disagree, and why

**Not one ordered pipeline.** We agree with the order in which *decisions* are taken:
charter and competency questions, then sources, then the conceptual model, then
ratification, then formalization, then instances. Your rework shows what happens when that
order is broken.

We do not agree with putting "vocabulary and taxonomy population" in that same line before
formalization, or with numbered stage directories as the way to say it. In a realist
ontology the OWL classification under BFO is the classification of types, and a SKOS
taxonomy is a vocabulary about terms; neither is built from the other. Your Stage 02
standard says the same in §8.1: taxonomy, thesaurus and conceptual modeling "MAY inform
one another and proceed iteratively".

So we propose **one decision path, with terminology lanes beside it.** The controlled
vocabulary, taxonomy and thesaurus run alongside the decision path. They may start early
with metamodel terms, as you found; catalog terms wait for the conceptual model's
admission criteria; and no lane writes an OWL axiom. Your directories stay valid: a
project may declare them. The method just does not require them.

**Two clauses.** The rights gate is that rights are *reviewed and recorded* before a
harvest; whether text may be used stays Legal's decision, not a check's. And not every
project runs every stage: a project declares the stages it runs.

## What we propose to build

All of it would land on the template's `main` and stay unreleased until the BPO evaluation
(WP6) ends. None of it changes your repository; whether BCO adopts any of it is your call.

| # | What | What it would ask of a project like yours |
|---|---|---|
| P1 | **The ontology method**, a new `docs/process/METHOD.md`: the decision path and the lanes, what each stage is for, the gates, the separations, the closure gate, ratification. Your account is the worked example, cited by what you found | Nothing new; it says what you worked out |
| P2 | **A stage-standard skeleton**, and a `config/stages.yaml` listing the stages a project runs, each one's standard and status. A started stage with no standard is reported | One entry per stage; a standard written from the skeleton before the stage starts |
| P3 | **A scope charter skeleton**: purpose, non-goals, the ontologies depended on, the competency questions, approved before drafting | One document, approved before the specification |
| P4 | **A source register** with your verification grades (V, P, S, K, L), and a check that every source a decision cites is in it and is V or P, or excused. Your register and its checks would be the starting point, with BCO's content removed | Sources recorded with a grade; decisions cite them by id |
| P5 | **Reviewer kind**, on reviews and on gates: ontologist, domain practitioner, architect. A gate that needs a practitioner is not passed by another kind | A kind on each review record |
| P6 | **Conceptual fidelity**: each formal term names the conceptual-model element it formalizes, or the decision that changes its meaning, and a shape refuses a term that names neither | One annotation per formal term |
| P7 | **Decision propagation**: a decision names the documents it changes, and each of them cites it, so an uncarried decision (DP-1 and DP-2 into specification v0.5, for example) is visible | A list on each decision record |

We would build P1 first, then P2 and P3, then P4 to P7 one at a time.

## What we ask

1. **The decision path and lanes.** Does it match what you found, or did the work need the
   strict order your account proposes? Where did the terminology work actually have to
   wait?
2. **P1 to P7.** Which would have saved you the most rework, and in which order? Is any of
   them wrong, or more work than it is worth?
3. **P4.** Can your source register and its checks be carried into the template, with
   BCO's content removed? Is anything in them specific to BCO that should not be?
4. **P5.** Are ontologist, domain practitioner and architect the right reviewer kinds? Who
   would count as a domain practitioner for BCO?
5. **P6.** Would one annotation per formal term, naming its CM-01 element, have worked for
   Stage 05 as you plan it? What does a formal choice that changes CM-01's meaning look
   like in practice?
6. **What we missed.** Anything in your account that the response does not answer, or gets
   wrong.

Please reply to this message, by its id. The architect decides on the response and on what
to build once your answer is in.
