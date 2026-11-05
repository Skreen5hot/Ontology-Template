# What WP6 shows about the template, and what to change

**To:** the architect. **From:** the Ontology Template Team. **Date:** 2026-11-05.
**Status:** proposed. Nothing here is decided until the architect decides it. **Verdict
accepted** 2026-11-05, decision 27 (SHA-256 of the proposed text
`9bb2160215da2c25362321c475c86af5ac8d9deaf3918894b5b5e78e49dda053`); §4 to §7 await the
architect's review.

**Analyses:** the BPO Testing Team's Phase B results,
`BPOTEST-EXAMPLE-2026-11-05-wp6-phase-b-results`
(`communications/bpotest/incoming/2026-11-05-wp6-phase-b-results.md`), with its Phase A
results and supplement before it. The team's working records stay private (decision 20).
They were read to check this analysis, and nothing from them is copied here: every figure
below is either in the team's recorded messages or measured in this repository.

**Scope of the evidence:** one ontology (BPO), one template release (v0.1.0), one port.
What follows is what that evidence supports, and no more.

---

## 1. The result in one paragraph

The template is **an effective detector of structural defects and an effective
reproducibility frame. It is not a substitute for referent-level review**, and it should not
claim to be. Over the four states, violations fell from 632 to 2. The template's checks found
11 of the 18 change items, and they found the one regression a correction introduced, which
BPO's own gates passed. Every state was rebuilt byte for byte and compared finding by
finding. What it missed is what matters most for meaning: relations that claim more than
their axioms, misclassified referents, homonyms and duplicate classes. Each of those needed a
person.

## 2. Strengths, and why each worked

Each strength comes from a design choice. A change that weakens the choice weakens the
strength.

| Strength | Evidence | The design choice behind it |
|---|---|---|
| **It sees across modules** | One IRI read differently depending on the module loaded. That was the drift behind the homonym and duplicate cases, and BPO, which validates each slice alone, could not see it | Validation over the merged corpus, with BFO and CCO in scope |
| **It catches structural OWL errors** | 563 class-to-class object-property assertions (punning) were found and removed | Realist placement shapes over the vendored upstream |
| **It reasons over entailment, not assertion** | BPO's own capability-as-process gate read asserted parents only, so a change that left entailment alone moved its count. The template's scheme rule follows `rdfs:subClassOf` transitively and kept the true count | Transitive SPARQL over the merged graph |
| **It catches regressions in the corrections** | A deprecation removed a class's definition and parent. Two template violations; BPO's gates passed it | The general definition and placement rules apply to every class, deprecated or not |
| **It raises few false alarms** | 16 of 4,323 Phase A findings, all from the label and comment checks | Narrow, explained shapes; a findings register instead of loosened checks |
| **Pinning by digest** | It exposed a CCO file that carried the pinned version IRI with later content, which a version check alone would pass | Pins name a commit and a SHA-256, never a version string |
| **Reproducibility** | Every state rebuilt byte for byte; findings compared by identity, not by count | Generated files never hand-edited; digests of committed bytes; a register keyed by finding identity |
| **The site build refuses an undefined term** | Undefined properties were found by the site build before any shape | Publishing depends on the same rules the gate holds |

## 3. Gaps

### 3.1 The instrument can mislead about itself (P-B2)

**Confirmed in this repository.** `tools/ontology/validate.py` marks a rung NOT EVALUABLE when
its upstream vocabulary is not in scope.
- In `--gate` mode it then exits 1, the same as for findings (lines 811–813).
- The rung's results are left out of the finding count (`register_findings`, line 674).

So a run where a check could not execute reports **fewer** findings, and is not otherwise
distinguishable from a run with findings. In Phase B this happened once: a measurement
reported 493 findings instead of 1,829, with no error. It was caught only because a count
fell further than the content could explain.

This is the most serious gap, because it is about the instrument's honesty rather than its
coverage. Every other gap is a missed defect. This one is a wrong number that looks right.

### 3.2 Checks that are imprecise

| Gap | Evidence | Cause |
|---|---|---|
| **P-B1**: the genus check passes a class if *any* definition contains the parent's label *anywhere* | Accepted, decision 23 | `NOT EXISTS` over a `CONTAINS` of the label |
| A source's own names are flagged as editorial qualifiers | 9 of the 16 false alarms: APQC element names ending in a parenthetical | The label check cannot tell declared third-party text from a note |
| One comment per language meets a legitimate practice | 7 false alarms: a second, review-added comment in the same module | The rule does not separate a second note from drift |
| A project's co-parent convention reads as defects | The co-asserted anchor parents a project keeps for offline validation raise genus and extra-parent warnings, accepted entry by entry | No way to declare an accepted modelling convention once, project-wide |
| No convention for a definition the project wrote itself | Definition-source warnings remain on every BPO-authored definition, because what "source" means for them is undecided | The annotation profile asks for a source and does not say what a project's own authorship looks like |

### 3.3 Defects no check finds

| Gap | Why it matters | What a check could do |
|---|---|---|
| **Over-claiming relations**: a name or definition that claims more than the axioms. In BPO, a possible realization was read as a necessary requirement, and that drove dispatch | The largest change in meaning in the whole evaluation. It moved no entailed pair, so no entailment-based check can see it | Flag candidates. (a) A *realizable* class with an existential `has realization` restriction (`C ⊑ ∃ obo:BFO_0000054.P` where C is under `obo:BFO_0000017`): it says every instance *is* realized, which a realist reading rarely means. Cheap, grounded in BFO, verified IRIs. (b) An object property declared as another's inverse whose definition uses necessity language. Low precision; a review queue, not a gate |
| **Homonyms**: one IRI, two kinds | Consumers get different classes from one name | Flag one IRI whose definitions name different genera across modules. The drift check already finds the variants; this would rank the ones whose *genus* differs |
| **Duplicate classes**: two IRIs, one kind | Splits instances that should be counted together | Flag pairs of classes with near-identical definitions or labels. A candidate list for a person |
| **Misclassified referents**: for example, a material artifact defined to include software | Wrong placement with consistent axioms | None mechanical. It needs the domain review METHOD §4 already names |
| **The deprecation policy**: a deprecated class keeps its label, definition and parent | Caught this time by the general rules, whose messages do not name the cause | **Confirmed:** the deprecated-term shape checks only `isReplacedBy` or `historyNote`. A specific constraint would name the cause |

### 3.4 Process and tooling gaps, already accepted (decision 23)

P-A1 (transitive dependencies unpinned), P-A2 (no upgrade procedure), P-A3 (the drift report
does not see shapes and config), P-A4 (a scheme rule cannot compare a local name with a
literal), P-A5 (the explorer shows no comments), P-A6 (`--propose` class by class), P-A7 (no
classification field on a register entry), P-A8 (no third-party attribution in the footer).

Two observations from Phase B bear on them:
- **P-A7 is more important than it looked.** The team's classification (real, false alarm,
  unsure, upstream, template bug) is what made 4,323 findings reviewable. A template that
  cannot record it pushes every project to build its own, as the port did.
- **The port built tools the template lacks**: a state manifest (every distribution, Java,
  ROBOT, the upstream digests) and a comparison of findings by identity. Both are general.
  P-A1 is the minimal half of the first.

## 4. What could change, and what should

**Should** is recommended now, for the first work after WP6. **Could** is worth doing,
designed when its turn comes. **Should not** is not recommended, with the reason.

| # | Change | Kind | Verdict | Why |
|---|---|---|---|---|
| 1 | **P-B2**: a rung that is not evaluable exits with its own code (2), is named in the summary and in `--json`, and is never counted as zero findings | tool, tests | **Should, first** | The instrument's honesty. Small, and testable on the existing constructed scopes |
| 2 | **P-B1**: each definition judged alone, and the parent's label in genus position | shape, fixture | **Should** (decided) | A check that passes what it should report |
| 3 | **Deprecation check**: a deprecated class keeps its definition and parent | shape, fixture | **Should** | The policy is the template's own; one constraint and its negative example |
| 4 | **Realizable-with-existential-realization warning** (§3.3 (a)) | shape, fixture | **Should** | The one over-claiming pattern that is grounded in BFO and cheap to find. A warning, not a violation |
| 5 | **P-A7**: a classification on each register entry | config, check | **Should** | §3.4. Designed with P5, as decision 23 noted |
| 6 | **P-A1, P-A3**: transitive pins; the drift report sees shapes and config | tool | **Should** | Reproducibility, which is the template's strongest claim. It should not rest on the port's own tooling |
| 7 | **Candidate reports for homonyms and duplicates** | tool, report (not the gate) | **Could** | Useful review queues. They need tuning against a real corpus, and their output is a list for a person, never a verdict |
| 8 | **A declared convention for co-asserted anchor parents**, accepted once in config instead of entry by entry | config, shape | **Could** | Removes most remaining warnings in a project like BPO without loosening the check. Needs a careful definition of the pattern |
| 9 | **Exempt declared third-party label text from the qualifier check**; **allow more than one comment in one module** where a project says so | config, shapes | **Could** | Removes the known false alarms by declaration, not by loosening |
| 10 | **A convention for a project's own authorship of a definition** in the annotation profile | docs, profile | **Could** | Decides what "source" means for authored text, so the warning means something |
| 11 | **A state manifest and a findings-by-identity comparison** | tools | **Could** | General, proven in the port. It would also hold item 1 across states: refuse two states whose evaluable rungs differ |
| 12 | **Domain review as a named gate**, tied to P5 (reviewer kind), with the misses of §3.3 as the worked example | docs | **Could**, with P5 | The verdict's own conclusion: the template should say where its checks stop and a person starts |
| 13 | An automatic **over-claiming** or **homonym** verdict in the gate | — | **Should not** | The BPO architect's position, which the evidence bears out: semantic identity needs a person. A syntactic check counted as solving it would overstate the template |
| 14 | Loosening a check to remove false alarms | — | **Should not** | The register and declarations exist so that a check stays exact and its exceptions stay visible |

## 5. A proposed order after WP6

1. Items 1 and 2: the instrument's honesty, then the accepted genus fix.
2. Items 3 and 4: two new shapes, each with its negative fixture.
3. Items 5 and 6, with P4/P5 (decision 21), since the register's shape is changing anyway.
4. P-A2, P-A4 to P-A6 and P-A8 (decision 23), and the SDD domain-and-range register.
5. Items 7 to 12, one at a time, each designed against a real corpus.

The release after WP6 would carry 1 to 4 at least, so that the next evaluation does not
measure with an instrument that can hide a rung.

## 6. What WP6 still needs before it ends

- The BPO architect's approval of the two classes for the regression (K20, K21). This is
  BPO's decision, and the team says only the approval is pending.
- The architect's act that WP6 has ended. That act lifts A7 and allows a template release.
  It is not taken here.
- An acknowledgment to the team, which can wait for the architect's decisions on §4.

## 7. What we ask

1. Accept or amend the verdict of §1 as the template's own reading of WP6.
2. Decide items 1 to 14 of §4: should, could, or should not.
3. Decide the order of §5, and when WP6 is declared ended.
