# Response to the BPO evaluation of the Ontology Template

**To:** the BPO Testing Team. **From:** the Ontology Template Team. **Date:** 2026-10-26.
**Status:** approved by the template architect, 2026-10-26 (decision 11 in
`docs/template/DECISIONS.md`), with the three policies of §4 and §5 as proposed.

**Responds to:** `research/template-evaluation.md` and `research/port-report.md` in
`Skreen5hot/BPO-Template-Port` at `68f22125f5075f67e6179ae447876b9f8d496fd1`:

| Document | SHA-256 |
|---|---|
| `research/template-evaluation.md` | `9b8264334b8361deedca4e2678ab80ad1abf66a9756e2f1cdc6575f5579ae72f` |
| `research/port-report.md` | `96060f2158955ee35183a11855b121104a9e2081aee03706fee9a8b4e11881bf` |

**Template state evaluated:** `Skreen5hot/Ontology-Template` at `2455bcc`.

---

## 1. Our position

We accept the evaluation's central conclusion: **the success criterion is not met.** The
template detects and reports well. At BPO's size it cannot yet support correction,
verification and prevention of recurrence:

- validation finishes only with a patched template file;
- a release cannot be built;
- an accepted finding cannot be recorded against its identity;
- one accepted finding stops most of CI.

Those are template defects, and this plan treats them as such.

We checked the template findings against the template's code before accepting them. Each
one we tested reproduces as described: T2, T4, T5, T6, T11 and T13 by reading the code, and
T1 through the patch's own equivalence evidence. We disagree with the evaluation on no
finding. On five (T7, T11, T12, T14, T18) we accept the finding but propose a different remedy,
and §3 gives the reasons.

Two of the process findings are ours, not the template's, and we record them as such:

- the report form was not attached to the request;
- the form pre-filled a repository name that did not match the one created.

## 2. How each finding is dispositioned

**Category.** Each finding is placed in one of five categories:

- **Defect**: the template does something wrong.
- **Missing control**: it lacks a check it should have.
- **Scale**: it fails only at BPO's size.
- **Process**: a documentation or procedure gap.
- **BPO-owned**: the decision belongs to the BPO maintainers, not the template.

**Decision.** Each finding gets one of four decisions:

- **Accepted**: the remedy is as the evaluation recommends.
- **Accepted, remedy changed**: §3 says why.
- **Transferred**: to BPO, the BPO architect or Legal.
- **Not accepted**: none this time.

**Rules the plan holds to:**

1. **No ontologically unjustified change.** No template change may require a BFO/CCO model
   to change only to satisfy a naming rule or a check. Where a check and correct modelling
   disagree, the check is changed, or the finding is accepted on the record with its reason.
2. **Every fix must generalize.** Each fix ships with a *template fixture*: a planted
   instance of the problem that is **not** BPO's, so the check is shown to recognize the
   kind of problem and not only this case. BPO is the *external acceptance corpus*. A fix is
   done only when both pass.

## 3. Disposition of every template-related finding

### 3.1 Template findings T1–T21

| ID | Finding (short) | Category | Priority | Decision | Work package |
|---|---|---|---|---|---|
| T1 | Validation is ~O(n²): `$this` is pre-bound late | Scale | **Critical** | Accepted. Adopt the inline-`$this` patch (`056403f`) with a version guard, then restructure the realist constraints that are not led by `$this`, which are 30 of the remaining 35 min | WP1 |
| T2 | Release canonicalization does not scale | Scale | **Critical** | Accepted | WP1 |
| T3 | Suite does not scale; no size benchmark | Scale / missing control | High | Accepted | WP1 |
| T4 | Baseline is a count per check | Defect | High | Accepted, and widened: one findings register shared by every check, warnings included (T22) | WP2 |
| T5 | No lint exceptions; fail-fast Checks hides steps | Defect | High | Accepted | WP2 |
| T6 | Site's term contract is not in the shapes | Defect | High | Accepted | WP3 |
| T7 | Site publishes one module's text for a drifted term | Defect | Medium | Accepted, remedy changed: the site shows every variant, marked as conflicting, and lists the term as a finding. It does not refuse, because a port arrives with known findings and must still publish | WP3 |
| T8 | No cross-module drift check for comments | Missing control | Medium | Accepted. The annotation properties that must agree across modules become a list in `config/annotation-profile.yaml`; the default is `rdfs:label`, `skos:definition` and `rdfs:comment`. BPO's `config/annotation-drift.tsv` becomes register entries | WP4 |
| T9 | Licensing is per file; third-party text inside a module passes | Missing control | High | Accepted. Annotation properties that carry third-party text are declared with their licence and required attribution. The disposition tool classifies them, and a shape requires the attribution. **Whether** BPO may redistribute APQC text is transferred to Legal (B2) | WP4 |
| T10 | No check for punning or property misuse | Missing control | Medium | Accepted | WP4 |
| T11 | Genus check fails on a label with a qualifier | Defect | Low | Accepted, remedy changed. The qualifier is itself the defect (B10). The genus check strips a trailing `(…)` so one defect gives one finding, not two; the qualifier warning stays | WP4 |
| T12 | No capability-as-process rule | Missing control | Medium | Accepted, remedy changed. The rule is BPO's IRI scheme (decision D7), not a realist rule, so the template must not carry it as a BPO rule. The template gets **scheme rules** in `config/naming.yaml`: a local-name pattern that must, or must not, sit under a category. BPO configures D7 with them | WP4 |
| T13 | init changes the disk without staging | Defect | Low | Accepted: init uses `git mv` and `git rm` | WP5 |
| T14 | init refuses a dirty tree | Process | Low | Accepted, remedy changed. The refusal stays, because it is what makes init's diff reviewable. It ignores `research/`, which init never writes, and the form ships in the template (T21) | WP5 |
| T15 | README gaps; rendered CLAUDE.md forbids the push step 5 needs | Process | Low | Accepted | WP5 |
| T16 | Project tests have no home | Defect | Medium | Accepted: `tests/project/` is declared the project's own, collected by the suite and not reported as divergence | WP5 |
| T17 | No guide to porting a predecessor ontology | Process | Medium | Accepted. The guide covers: SSSOM direction (new → old, which is what the checker requires), the justification for a namespace move, carrying header metadata, the lossless check, and BPO's `port_from_bpo.py` as the worked example | WP5 |
| T18 | "Readable local names" not enforced; conflicts with identifier schemes | Process | Low | Accepted, remedy changed. Readable names are the default for new terms, not a rule for ported ones. A project declares its scheme in `config/naming.yaml`. The docs say so, and the IRI-linter text that implies the opposite is corrected | WP5 |
| T19 | Pinned actions stale at copy time | Process | Low | Accepted. Before each template release, every open Dependabot update is either taken or ignored on the record with a reason. (setup-python 7.1.0 was being held on purpose; that hold should not surface in every new project) | WP5 |
| T20 | No progress output; JSON keeps 20 warnings | Defect | Low | Accepted; required by T4 anyway, which needs the full list | WP2 |
| T21 | Form not in the template; manifest has no commit SHA | Process | Low | Accepted: the form ships beside the porting guide (T17), and the manifest records the template commit and release | WP5 |

### 3.2 Findings the evaluation implies but does not number

| ID | Finding | Source | Category | Priority | Work package |
|---|---|---|---|---|---|
| T22 | Warnings are neither gated nor baselined: a new warning is invisible | §3, rows B9 to B14 | Defect | High | WP2 |
| T23 | No provenance shape: a module carrying external text need not name its source and release (BPO caught B3 with its own test) | §3, row B3 | Missing control | Medium | WP4 |
| T24 | Upstream defects (B11, CCO 2.0's Organization ⊄ Agent) have nowhere to be recorded | §3, row B11 | Missing control | Low | WP2 (a register entry may be marked `upstream`, naming the upstream and term) |
| P1 | The request did not attach the form, and the form's pre-filled repository name was wrong | port report §6, §7 | Process (ours) | — | Done for the next trial by T21 |

### 3.3 BPO findings: what the template owes each

The BPO content decisions stay with BPO, the architect and Legal, as the evaluation's
register assigns them. We do not propose any content change. What the template owes each
one is a mechanism to detect it, record a decision against it, and verify the fix:

| BPO finding | Owner of the decision | What the template provides |
|---|---|---|
| B1 drift | Arch, BPO | Drift check with identity (T8) and register entries (T4); the site shows the variants (T7) |
| B2 APQC attribution | Legal, PO | Licence and attribution declaration per annotation property, and the shape (T9) |
| B3, B18 provenance and headers | BPO, PO | Provenance shape (T23); header carry-over in the port guide (T17) |
| B4 IRI naming | Arch | A register entry with identity and reason (T4/T5), or a rename with an SSSOM replacement row |
| B5 property definitions | BPO | The term contract in the shapes (T6) |
| B6 punning | BPO | Punning shape (T10) |
| B7, B8 property semantics | Arch | **No automatic detection** (see §6). A decision in `docs/decisions/`, and a project test in `tests/project/` (T16) |
| B9 to B14 warnings | Arch | Warnings in the register by identity (T22), so each is accepted or fixed on the record |
| B11 Organization ⊄ Agent | Arch | An `upstream` register entry (T24), plus the pattern decision in `docs/decisions/` |
| B15 capability-as-process | BPO | Scheme rules (T12); the count of 39 must be reproduced |
| B16 old CURIEs in comments | PO | The decision record; nothing to build |

## 4. Corrective-action plan

Owners:

- **TT**: the Ontology Template Team. Implementation is done by Claude Code at the template
  architect's direction.
- **TA**: the template architect (Aaron Damiano). Approves this plan, the thresholds and
  every policy choice.
- **BPO-T**: the BPO Testing Team, which runs the acceptance tests.

The work packages run in order. Each one passes its own acceptance criteria before the next
begins, because the later ones are measured with the earlier ones' tools.

| WP | Scope | Priority | Owner | Depends on |
|---|---|---|---|---|
| WP1 | Scale: T1, T2, T3 | Critical | TT | — |
| WP2 | One findings register and complete CI: T4, T5, T20, T22, T24 | High | TT; TA for policy | WP1 |
| WP3 | One term contract, and publication consistent with validation: T6, T7 | High | TT | WP2 |
| WP4 | Detection gaps: T8, T9, T10, T11, T12, T23 | Medium to High | TT; Legal for T9's policy text | WP2 |
| WP5 | Project ergonomics and documentation: T13 to T19, T21 | Low to Medium | TT | — (can run alongside) |
| WP6 | Final evaluation with BPO (§7) | — | BPO-T, TT | WP1 to WP4 |

**Thresholds are provisional.** The time budgets below were proposed by the evaluation or
by us, on GitHub's standard Linux runner. TA ratifies them before WP1 closes.

## 5. Acceptance criteria

Each criterion has four parts:

- **Expected behaviour**: what the template does once fixed.
- **Evidence**: what is produced to show it.
- **Regression tests**: what keeps it true.
- **Generalization**: the planted fixture that is not BPO.

Every test named here goes in the template's suite, and every one is falsified before it
counts. That means the guard it protects is broken on purpose and the test is shown to fail,
as for every check so far.

### WP1: Scale

**A synthetic benchmark corpus.** The size test needs one: generated, not hand-written, at
or above BPO's size, with at least 3,000 classes and 4,000 existential restrictions on a few
properties (BPO's hard case for canonicalization). It carries a planted, known set of
defects, one per check, so the benchmark measures time **and** finding identity at once.

| Item | Expected behaviour | Evidence | Regression tests | Generalization |
|---|---|---|---|---|
| T1 | The full ladder on the benchmark and on the BPO port finishes within **15 min**, with results identical to the unpatched ladder on every fixture | Timings in CI; a result-equality report, patched against unpatched, over every negative fixture | `test_ladder_within_budget_on_the_benchmark` (marked `scale`, run by a scheduled CI job); `test_inlined_this_changes_no_result` over every fixture; a guard that fails if the pinned pyshacl no longer has the patched helper | The benchmark's planted defects are each found, by identity |
| T2 | `release.py` builds the benchmark and the BPO port within **15 min**, byte-identical across hash seeds. Blank-node labels come from a structural hash of each restriction tree, with rdflib's canonicalization only for cyclic or shared blank nodes | Two builds with different seeds; digests equal; time | `test_two_builds_are_byte_identical` on the benchmark (marked `scale`); `test_structural_labels_agree_with_rdflib_on_small_graphs`, which checks the new method is isomorphic to rdflib's on every fixture | A planted pair of restrictions that differ only in filler order |
| T3 | Corpus-dependent tests are marked. The Checks suite on the BPO port finishes within **30 min**, and the template's own suite stays within **10 min** | CI timings, recorded per test (`--durations`) | A scheduled `scale` job with per-tool budgets; it fails, and names the tool, when one is exceeded | The benchmark itself |

### WP2: One findings register, and complete CI

**What the register is.** A single register, `config/findings-register.yaml`, replaces the
count-per-rung baseline. One entry is one accepted finding. It records:

- the check (`validate`, `iri_lint`, `site`, `drift`, `scheme`, …);
- the finding's identity: focus node, shape or rule, and a digest of its message;
- severity;
- a reason, an owner, a review date, and optionally `upstream: <source> <term>`.

**What every check does with it.** Every check reads the register and reports each of its
findings as either *accepted* (an entry matches) or *new*.

**Policy, for TA to ratify:**

- A new violation fails.
- A new warning fails unless recorded; this is what fixes T22.
- An entry that matches nothing fails, because the fix must be recorded.
- An expired review date is reported, not failed.

| Item | Expected behaviour | Evidence | Regression tests | Generalization |
|---|---|---|---|---|
| T4, T22 | Fixing one finding and introducing an unrelated one in the same check fails the gate. So does a new warning | The fixtures below; the BPO port's 57 + 1 findings re-recorded by identity | `test_swapping_one_finding_for_another_fails`; `test_a_new_warning_fails_unless_recorded`; `test_a_stale_entry_fails`; `test_an_entry_needs_reason_owner_and_review_date` | Planted swap fixtures for each check, not BPO's |
| T5 | An accepted IRI-lint finding passes. Every Checks step runs whatever an earlier step did; a final step fails the job and lists every failed step | CI log of a run with one failure: every step reported | `test_checks_runs_every_step` (reads the workflow: every check step continues on error, and the summary step fails on any failure); a CI rehearsal with one planted failure | The planted failure is in a check other than IRI lint |
| T20 | `validate.py` reports progress per shape set to stderr, and its JSON holds every finding | JSON with the full list on the benchmark | `test_report_holds_every_finding` | The benchmark's planted count |
| T24 | A register entry may name an upstream term and source; the status page lists upstream findings separately | Status page | `test_upstream_entries_are_listed` | A planted CCO-term entry |

### WP3: One term contract, and publication consistent with validation

| Item | Expected behaviour | Evidence | Regression tests | Generalization |
|---|---|---|---|---|
| T6 | Every rule under which the site refuses a term is a shape in the ladder: a definition on every authored term, properties included, and at most one value per language. The ladder fails on every input the site refuses | Parity report | `test_every_site_refusal_is_a_ladder_finding`: one fixture per refusal reason, each run through both the ladder and the site | A planted property without a definition, and a planted class with two English labels |
| T7 | A term with differing text across modules is published with every variant, marked as conflicting, and appears on the status page as a finding. The site never silently picks one | The BPO port's 51 drifted classes shown as conflicts | `test_a_drifted_term_shows_every_variant` | A planted two-module drift |

### WP4: Detection gaps

| Item | Expected behaviour | Evidence | Regression tests | Generalization |
|---|---|---|---|---|
| T8 | Any annotation property on the agree-across-modules list that differs across modules is a finding, by identity | BPO: the 110 pairs in `config/annotation-drift.tsv` reproduced exactly | `test_comment_drift_is_found`; `test_the_list_is_configurable` | A planted comment drift |
| T9 | An annotation property declared as carrying third-party text gets that text's licence in the disposition report. A shape requires the declared attribution on the module header | BPO: 3,757 `apqcSourceText` values reported as third-party, with the attribution missing | `test_third_party_text_in_a_module_is_classified`; `test_unattributed_third_party_text_fails` | A planted annotation carrying CC BY-SA text |
| T10 | An object property asserted between two classes, or an annotation property used in `owl:onProperty`, is a violation | BPO S0: the 3 `requires…` properties flagged | `test_class_level_object_property_use_is_found` | Planted cases of both kinds |
| T11 | A trailing `(…)` is ignored when matching a definition's genus; the qualifier warning stays | BPO: genus warnings drop by the number caused only by qualifiers, and the 78 qualifier warnings remain | `test_genus_ignores_a_trailing_qualifier`; `test_the_qualifier_is_still_reported` | Planted qualified labels |
| T12 | `config/naming.yaml` accepts scheme rules: a local-name pattern that must or must not sit under a category | BPO configures D7 and reproduces its Gate F count of **39** | `test_a_scheme_rule_finds_a_misplaced_term`; `test_no_scheme_rule_ships_enabled` (the template ships the mechanism, not BPO's rule) | A planted rule and term unrelated to PCF |
| T23 | A module that declares external source text names its source and release in its header | BPO S0: 17 of 18 slice files flagged (B3) | `test_external_text_without_release_is_found` | A planted module |

### WP5: Project ergonomics and documentation

| Item | Expected behaviour | Evidence | Regression tests |
|---|---|---|---|
| T13 | The suite passes straight after init, before any staging | Init test | `test_the_suite_passes_straight_after_init` (no `git add` in the test) |
| T14 | init ignores `research/` in its clean-tree check, and refuses anything else as today | Init test | `test_research_notes_do_not_block_init`; `test_any_other_change_still_blocks_init` |
| T15 | The README gives: the `gh repo create --template` route, Pages through the API, `core.hooksPath`, the suite command with its expected time. The rendered CLAUDE.md no longer contradicts README step 5 | Docs | `test_the_readme_names_each_setup_step` |
| T16 | `tests/project/` is collected and is not divergence | `template_status.py` on a project with a test | `test_a_project_test_is_not_divergence` |
| T17 | `docs/PORTING.md` exists, and the next port asks no mapping question | Next trial's report §6 | — (measured by the next trial) |
| T18 | The docs state the naming policy for ported ontologies | Docs | — |
| T19 | No Dependabot PR on day 0 of a new project | Next trial | A release checklist item |
| T21 | The form ships as `docs/porting/port-report.md` beside the guide, which init keeps (not under `docs/template/`, which init deletes); the manifest records the template commit | A new project's manifest | `test_the_manifest_records_the_template_commit` |

## 6. Remaining limitations

These stay true after the plan, and the plan should not be read as removing them.

1. **Semantic errors need review.** B7 and B8 (a definition contradicting CCO, a relation
   that means "can" but is used as "requires") were found by the PO's review. No check here
   can find them. The template records the decision and holds it with a project test; it
   does not detect the error.
2. **Licensing is judged by Legal.** The template can require that third-party text be
   declared and attributed. Whether it may be redistributed is not a check.
3. **The reasoner is OWL 2 EL.** ELK ignores universal restrictions, cardinality and most
   unions. "Consistent, nothing unsatisfiable" is necessary, not sufficient.
4. **Scale budgets are runner-specific and provisional** until TA ratifies them. An ontology
   much larger than BPO is not covered by this evidence.
5. **Upstream defects are recorded, not reported upstream.** There is no channel to CCO in
   this plan.
6. **T1's fix depends on pyshacl internals.** It is guarded and tested against the pinned
   version; an upstream fix in pyshacl or rdflib would retire it.

## 7. The final evaluation (WP6)

When WP1 to WP4 pass their criteria, the BPO Testing Team repeats the affected tests. We
propose the following protocol, and ask the team to amend it before it is used.

1. **Same instruments for every state.** S0 (`BusinessProcessOntology` at `bc64e91`,
   ported unchanged), S1 (`c062662`) and S2 (after BPO's approved corrections) are each
   measured with the **same** template release, using the evaluation's §5 metrics table.
   Every count is reported by identity, from the findings register.
2. **Three verdicts, each with its own evidence:**
   - **BPO's quality**: S2 against S0 on confirmed real defects. Each change is traced to a
     decision in `docs/decisions/` and to a check or test that now fails if the defect
     returns.
   - **The template's quality controls**: for each B finding, the stages of the evaluation's
     §3 table (detect, report, evaluate, dispose, correct, verify), re-rated, and for each
     check, whether its planted fixture was found.
   - **The process**: ladder time, release build time and byte-identity, suite time, and
     Checks steps run in CI, against the budgets above.
3. **Required evidence**, as the request specifies:
   - a complete release of S2, built twice, byte-identical, published from a green Release
     workflow;
   - the full Checks job green on S2, with every step run;
   - the findings register showing every remaining accepted finding with its reason.
4. **What does not count as evidence:** a green run alone, a lower count without identities,
   or a finding fixed without a check that would catch its return.

## 8. What we ask of the BPO Testing Team

- Confirm or amend the dispositions in §3, in particular the five with a changed remedy
  (T7, T11, T12, T14, T18).
- Confirm or amend the protocol in §7.
- Keep `Skreen5hot/BPO-Template-Port` at `c062662` (or tag it) as the S1 reference, so the
  final evaluation measures against a fixed state.
