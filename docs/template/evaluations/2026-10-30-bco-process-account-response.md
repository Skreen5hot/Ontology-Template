# Response to the BCO team's account of its ontology process

**To:** the architect, and through the architect the BCO team. **From:** the Ontology Template
Team. **Date:** 2026-10-30. **Status:** proposed. Sent to the BCO team for its input on
2026-10-30 (`communications/bco/outgoing/`), since BCO does the work it describes; the
architect decides after. BCO answered the same day
(`communications/bco/incoming/2026-10-30-process-proposals-answer.md`). **Decided**
2026-10-30, decision 21: §3.1's lanes accepted with BCO's join points, P8 added, P1, P3
and P2 built, P4 to P8 held. Left as written; the decision says what changed.

**Responds to:** [`2026-10-30-bco-process-account.md`](2026-10-30-bco-process-account.md),
SHA-256 of the text below its rule
`03435b731ee6085039369538b63ff4a71b06391dd5f821681bf5b66a311dc2b7`.

**BCO state checked:** `Skreen5hot/Business-and-Agent-Capabilities-Ontology` at `08c932f`,
read only.

---

## 1. What the account shows the template is missing

The template carries a method for building *checks*: `docs/process/PROCESS.md` is about
falsification, gates, evidence, determinism and pinning. It has no method for building an
*ontology*: when scope is fixed, how sources are weighed, where a conceptual model comes
before OWL, what a stage must state before it starts. A project made from the template gets
excellent machinery and no account of the work the machinery serves.

BCO started from an early version of the template's structure and worked that method out
for itself. The account is the record of what it cost: a specification and a catalog
vocabulary drafted before the conceptual baseline, and redone; a harvest done before the
rights review, and withheld; one stage standard out of six. The account is candid about
its own failures. We take it as the best evidence available of what the template should
say.

## 2. What we checked

At `08c932f`, read only:

| Claim | Found |
|---|---|
| A register of 63 sources | `docs/sources/register.yaml`: 63 entries |
| Only Stage 02 has a standard | `docs/standards/` holds `stage-02-conceptual-modeling.md` alone |
| The Stage 02 standard requires domain-stakeholder review | §7: "Domain stakeholders have reviewed the model", and "stakeholder agreement require[s] human review" |
| Taxonomy and formalization rules (§8.1, §8.2) | As quoted: terminological hierarchies "do not automatically become formal ontological relationships"; formalization "MUST preserve the intended conceptual meaning or explicitly document justified changes" |
| A closure gate held on 2026-10-30 | `docs/decisions/2026-10-30-closure-decided.md` |

One correction, and one thing the account understates:

- **Stage 03's status.** The account has it in progress; `src/03_taxonomy/README.md` says
  "not started. Nothing is here yet." Both can be true: the inventory lives elsewhere and
  feeds the taxonomy. But the stage's own README should say so, or it misreports the stage.
- **Stakeholder review was not just missing, it was recorded as done.** CM-01 ticks "Domain
  stakeholders have reviewed the model" on the strength of R8 and R9, which were ontology
  reviews. This is PROCESS.md §1 exactly: a gate that reports on something adjacent to the
  question. The fix is the template's to make: a review records what kind of reviewer did
  it, and a gate names the kind it needs.

## 3. The account's five recommendations

### 3.1 Order the stages: **agreed for decisions, not for artefacts**

We agree with the order in which *decisions* are taken: scope and competency questions,
then sources, then the conceptual model, then ratification of the specification, then
formalization, then instances. Each depends on the one before, and BCO's rework is what
happens when that order is broken.

We disagree with a single line that puts "vocabulary and taxonomy population" before
formalization, and with numbered stage directories as the way to say it. Clause: in a
realist ontology the OWL classification under BFO is the classification of types, and a
SKOS taxonomy is a vocabulary about terms. Neither is built from the other. The template
decided this when it weighed the six-layer pipeline (ROADMAP, "Layers compared with the
ontology pipeline"), and BCO's own Stage 02 standard says the same in §8.1: taxonomy,
thesaurus and conceptual modeling "MAY inform one another and proceed iteratively". A
numbered order says the opposite.

So we propose **lanes with gates**, not a pipeline:

- one **decision path** in strict order: charter, sources, conceptual model, ratification,
  formalization, instances;
- **terminology lanes**, the controlled vocabulary, taxonomy and thesaurus, that run beside
  it. They may start early with *metamodel* terms, as BCO found. *Catalog* terms wait for
  the conceptual model's admission criteria. No lane writes an OWL axiom.

The layout contract keeps roles, not numbered directories. A project that wants BCO's
directories can declare them; the method does not need them.

### 3.2 A standard for every stage, before it starts: **agreed**

This is PROCESS.md §3's own rule, "the gate states its conditions before the phase starts",
applied to stages. BCO broke it five times out of six, and the template made that easy by
saying nothing about stages.

Clause: the template cannot write a project's standards. What a taxonomy standard demands
of capability terms is BCO's to decide. What the template can supply is the *shape* of a
standard, the questions every one must answer (inputs, outputs, the gate's conditions, who
holds it, what is out of scope), and a record of which stages a project runs, which have a
standard, and which have started. A stage that has started without a standard is then a
finding the project sees.

Not every project runs every stage. A small domain ontology may have no knowledge graph and
no thesaurus. A project declares the stages it runs; it does not inherit six.

### 3.3 Four gates found late: **agreed, with one clause**

| Gate | Agreed | What the template can support |
|---|---|---|
| **Source adequacy:** a source a design decision relies on is primary-verified, or explicitly excused, before it is cited | Yes | A source register with BCO's verification grades (V, P, S, K, L), and a check that every source a decision cites exists in it and is V or P, or carries an excuse |
| **Rights and provenance before any harvest**, withheld by default | Yes, with a clause | The gate is that rights are *reviewed and recorded* before harvest, with withholding the default. Whether text may be used is Legal's decision, not the template's, as T9 already holds (decision 15). The template's third-party text record and research rule are where the check attaches |
| **Domain-stakeholder review** | Yes | A review records its reviewer's kind (ontologist, domain practitioner, architect). A gate that needs a practitioner names it, and is not passed by another kind. This is the fix for the CM-01 checkbox above |
| **Conceptual fidelity at formalization** | Yes | Each formal term names the conceptual-model element it formalizes, or the decision that changes its meaning. A shape can then refuse a term that names neither |

### 3.4 Three separations: **agreed, one generalized**

- *Evidence is not vocabulary is not admission*: agreed as written. It holds for any
  ontology built from sources.
- *Type admission (G1-T) is not instance attribution (G1-I)*: agreed, and generalized for the
  template. G1-T and G1-I are BCO's tests for capabilities. The general rule is that
  admitting a type into the ontology asserts nothing about any particular, and asserting
  that a particular instantiates a type needs evidence of its own.
- *Conceptual approval is not specification ratification is not OWL*: agreed as written.

### 3.5 A closure gate before the next phase: **agreed**

Every outstanding decision resolved, merged and recorded before the next phase opens. The
template already asks for a gate at the end of each phase and for what was not done to be
said (PROCESS.md §3, §5). What it lacks is the closure set as an artefact: the list of open
decisions, each closed or carried forward by name.

## 4. Two more findings from the account

- **A decision needs a propagation path** (account §4). DP-1 and DP-2 were decided in CM-01
  and still have to be carried into specification v0.5, by hand. The template records
  decisions verbatim but says nothing about what they change downstream. A decision record
  could name the documents it changes, and each of those cite it, so that an uncarried
  decision is visible rather than remembered.
- **The specification has no place in the template.** BCO's design lives in a specification
  that is drafted, reviewed and ratified, and the template has no notion of one. We do not
  propose adding one in general. A small ontology's specification can be its charter and its
  conceptual model. The method should say what ratification means, and that nothing in a
  draft is normative until it happens.

## 5. What we propose to build

All of it lands on the template's `main` and stays unreleased until WP6 ends (decision 20,
A7), so the BPO Testing Team's instrument does not change.

| # | What | Kind |
|---|---|---|
| P1 | **The ontology method**, `docs/process/METHOD.md`: the decision path and the lanes; what each stage is for; the gates of §3.3; the separations of §3.4; the closure gate; ratification. BCO is the worked example, cited by what it found, not copied | Docs |
| P2 | **A stage-standard skeleton**, and `config/stages.yaml`: which stages a project runs, each one's standard and status. A check reports a started stage with no standard | Docs, config, a check |
| P3 | **A scope charter skeleton**: purpose, non-goals, the ontologies depended on, and the competency questions, approved before drafting. The template's `competency-questions/` holds the questions; the charter says why they are the right ones | Docs |
| P4 | **A source register** with verification grades, and the check of §3.3. BCO's register and its checks are the starting point, carried as the template has carried BCO's tools before, with BCO's content removed | Config, a tool, tests |
| P5 | **Reviewer kind on reviews, and on gates** (§3.3) | Config, a check |
| P6 | **Conceptual fidelity**: an annotation naming the conceptual-model element a term formalizes, and a shape | Annotation profile, shape, fixture |
| P7 | **Decision propagation** (§4): a decision names what it changes; each of those cites it | Docs, a check |

We would build P1 first. It is the account's main point, it costs no tooling, and the others
are each a section of it made checkable. P2 and P3 are next. P4 to P7 are each a check, and
each needs its negative fixture, so they follow one at a time.

## 6. What we ask

1. The architect: accept or amend this response, in particular the disagreement in §3.1
   (lanes with gates, not a numbered pipeline) and the generalization in §3.4.
2. The architect: choose which of P1 to P7 to build, and in what order.
3. The BCO team: its input on all of it, before the architect decides. It is sent to them as
   a request (`communications/bco/outgoing/2026-10-30-process-proposals.md`).
