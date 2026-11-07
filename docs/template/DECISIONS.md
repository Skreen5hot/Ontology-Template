# Decisions — building the template

The architect's choices about the template, as given in session on 2026-10-23, in answer to
six questions the setup agent (Claude Code) put after reviewing the Business Capability
Ontology repository, the ODK project-setup tutorial and IRI_Linter. The answers are quoted
as given; the question each answers is summarized beneath.

These decide how the template is built. They do not decide anything about any project made
from it.

---

**1. "GitHub template for now"**

How a project is made from the template and kept up with it: a plain GitHub template with an
init script and a drift report, or Copier, which can push later tooling changes into derived
repositories. Effect: a GitHub template; `tools/init_project.py` and
`tools/template_status.py`. Copier is revisited when there are several derived repositories.

**2. "Keep in own CI job"**

Whether Java/ROBOT may be added for reasoning (ELK) and release artefacts. Effect: yes, in a
CI job of its own, so the checks every push runs stay Python-only. Not built yet (roadmap
phase 5).

**3. "Lets use v2.0"**

Which CCO release the template pins by default. Effect: CCO v2.0-2024-11-06, commit
`510dad76be0ef710b65a421075af912af25342b7` — the pin the Business Capability Ontology and
the Business Process Ontology use.

**4. "Readable local IRIs"**

Whether authored terms get opaque ids (`<prefix>:ont00000001`, CCO's style) or readable
local names. Effect: readable local names; no id minter or id ranges by default. Upstream
CCO terms stay opaque — they are CCO's.

**5. "https://fandaws.com/ontology/<id>#"**

The default namespace pattern. Effect: `tools/init_project.py` derives the namespace from
the project id with this pattern (`--iri-base` overrides it).

**6. "MIT"**

The licence of the template and of the tools it carries, which kept Apache-2.0 SPDX headers
from ValueNet and ARO while the repositories they were in said MIT. Effect: every carried
file's header says MIT, and `LICENSE` is MIT.

---

## Later the same day

**7. "The Name is good."**

The template's GitHub slug, `Skreen5hot/Ontology-Template`, which `tools/project.py --check`
compares against. Effect: kept as written in `config/project.yaml`.

**8. "Do we have a research folder? Seems useful for a template same with Competancy
Questions" — then: "As long as it is all covered in the plan. you can keep the roadmap as is
and push then move to the next phase"**

Effect: the roadmap keeps its phase order. Competency questions, as checked SPARQL with
expected answers, are added to phase 4; a `research/` record to phase 6; and phase 7 now
names the GitHub Pages workflow, the site tools and assets explicitly, with the
competency questions on the site. Phase 1 is committed and pushed, and phase 2 begins.

**9. "Agree with your recommendaitons. Update roadmap"**

In answer to a colleague's question whether the repository should be structured on the
ontology pipeline attributed to Jessica Talisman (controlled vocabulary, metadata schemas,
taxonomy, thesaurus, ontology, knowledge graph, as numbered directories). The
recommendation agreed to: weigh the layers for what they add, and do not adopt the numbered
layout, LinkML as the source of truth, OWL derived from SKOS, unpinned tooling, submodule
imports, or RML pipelines. Effect, in the roadmap with its phase order unchanged: example
instance data for competency questions (phase 4); a vocabulary intake, SKOS concept-scheme
modules, governance documents and SSSOM crosswalks (phase 6); crosswalk and vocabulary pages
on the site (phase 7); and a layer-by-layer comparison table, to be carried into
DEVELOPMENT.md.

**10. "Yes publish the site. My principle is an ontology is only worth making if it is public.
The HOW it was made may be private"** (2026-10-24)

In answer to whether the template's own site should be published, the Pages site of a
private repository being public. Effect: Pages is enabled for the template (GitHub Actions
as the source), and `"publish"` in `site/content/site.json` is true -- in the template and,
through it, in every project from its first commit. Because the repository may stay private,
the build is told the repository's visibility and, for a private one, writes no link into
it (source files, commit, issues, releases); the checker refuses one, and an optional
`contact` in `site.json` is the route for findings instead. A project that will not publish
sets `"publish": false`.

**11. "Approved"** (2026-10-26)

In answer to the proposed response to the BPO evaluation,
`docs/template/evaluations/2026-10-26-bpo-evaluation-response.md` (SHA-256 of the proposed
text `5503fbd9a322eaea25eca15623011d9879ba8522b90b97d1d4c3527088b16597`; the approved file differs only in its status line). Effect: the six work
packages are the template's next phases, in order, replacing roadmap phase 8 as written; the
dispositions stand as written, the five changed remedies included; and the three policies
take effect as proposed -- the time budgets (ladder and release build 15 min, the suite on
the BPO port 30 min, the template's own suite 10 min, on GitHub's standard runner), a new
warning fails the gate unless recorded, and an expired review date is reported, not failed.

**12. "going public is the intent. Proceed with WP2"** (2026-10-28)

In answer to whether making this repository public (found on 2026-10-27, when the Pages job
failed on it) was intended, given decision 10's "the HOW it was made may be private".
Effect: the template repository is public, so its site links into it -- source files, the
commit, issues and releases -- as the build does for any public repository. Decision 10
stands for projects: a project's repository may stay private, and its site then links
nothing into it. WP2 begins.

**13. "WP2 is accepted as complete. Proceed with WP3."** (2026-10-28)

In answer to the WP2 report. The whole text, with five numbered decisions, is recorded
verbatim in
[`evaluations/2026-10-28-wp2-acceptance.md`](evaluations/2026-10-28-wp2-acceptance.md)
(SHA-256 of the text below its rule
`5f8d8c2c1e5a637d066796e230f2e94e7b748d78cece9807ee307cc8439b15d9`). Effect:

- WP2 is accepted on its functional tests, regression results and the template's measured
  times. Phase 10 is done.
- The BPO-scale times are an outstanding verification requirement, carried to WP6, and
  are not represented as measured. They are to be measured in the BPO team's private
  repository and its GitHub Actions runner: the complete Checks and Reasoning jobs, under
  documented runner conditions, against the approved budgets. No BPO content, credential or
  execution log goes into this repository's public CI.
- The 3,716 BPO findings are BPO's to evaluate, resolve or accept. That the register can
  hold them says nothing about whether they should be accepted, and upstream BFO/CCO
  findings stay distinguishable from BPO's.
- WP3 begins. Validation must enforce every requirement publication depends on, the site
  must not conceal conflicting definitions or other material findings, and regression tests
  must show both.
- The final evaluation must establish whether using the template measurably improves the
  ontology itself, not only that its tests pass.

The ROADMAP's "Carried to WP6" section holds the open items.

**14. "WP3 is accepted as complete. Proceed with WP4 (T8–T12, T23)."** (2026-10-28)

In answer to the WP3 report. The whole text, with seven numbered points, is recorded
verbatim in
[`evaluations/2026-10-28-wp3-acceptance.md`](evaluations/2026-10-28-wp3-acceptance.md)
(SHA-256 of the text below its rule `35da88b9279dda22afd550afb266c0f5bf7ed3edc89fc2fd4e7c6369cb71404c`). Effect:

- WP3 is accepted; phase 11 is done. Publishing BPO's conflicts shows them; it does not
  approve or resolve them.
- A browser-level check of the explorer is an outstanding follow-up, not a blocker: that
  the rendered page shows every conflicting variant, its module, and the term's findings.
  It is in the ROADMAP's "Carried to WP6" section.
- BPO's findings stay BPO's. Accepted findings, unresolved ontology issues and upstream
  BFO/CCO findings stay distinguishable.
- WP4 begins. For each gap (T8 to T12, T23) it must show detection, accurate reporting, a
  disposition, and a test that a correction does not regress.
- The T9 request to Legal is initiated: `communications/legal/outgoing/2026-10-28-t9-third-party-text.md`,
  with Legal added as a correspondent. No legal interpretation or permission is assumed in
  the implementation: the template ships no default licence, attribution or permission.
- WP6's obligations are unchanged, and its assessment must separate improvements in the
  template from improvements in BPO's content.

**15. "WP4 is accepted as technically complete at commit `a923694`."** (2026-10-29)

In answer to the WP4 report. The whole text, with six numbered points, is recorded verbatim
in [`evaluations/2026-10-29-wp4-acceptance.md`](evaluations/2026-10-29-wp4-acceptance.md)
(SHA-256 of the text below its rule `1a74abf93314480ba3ca00bd1b549af1fc06af8bc57c6839b8bf9d4aa0567fee`). Effect:

- WP4's detection controls and regression tests are accepted; phase 12 is done, except
  T9's policy, which stays open.
- The corrected BPO figures stand and supersede the response's estimates: T10, 2 used
  properties in 494 assertions on 453 classes (`requiresPermission` is declared, unused,
  and not counted); T11, the 78 genus warnings gone and 18 qualifier warnings that are new
  findings; T23, 14 of the 15 modules holding APQC text. The checks are not to be changed
  to reproduce the earlier figures.
- T9's detection and reporting are accepted; its policy is not. The PENDING LEGAL sentence
  and the test pinning it stay. No check is to be described as establishing legal
  permission, the sufficiency of an attribution, or BPO's right to redistribute APQC text.
  When Legal answers, the implementation, tests, report wording and publication controls
  are assessed against the answer, and any change is recorded and verified before the
  dependency closes. B2 stays BPO's and Legal's.
- BPO-derived findings are evaluation evidence, not dispositions. The T11 qualifier
  findings and the trial T12 rule are the BPO team's to decide. Nothing from the scratch
  copies, trial configuration, placeholder attribution or accepted findings, is carried
  into BPO.
- GitHub Actions times are recorded apart from the local time, which is not a measurement.
  BPO-scale times and the ontology-quality verdict stay WP6's.
- The next work package, WP5, begins without waiting for Legal, so long as none of it
  depends on the licensing policy.

**16. "We are turning Dependabot OFF, we will make note in the template that the first responsibility is to check all the pins as part of using the tempate."** (2026-10-29)

In answer to the WP5 report, which asked whether to keep Dependabot, limit it to security
updates, or remove it. Recorded verbatim above (SHA-256 of the quoted text
`cc29e8f4b66994eeb9614cdf553a042025facf487d8fef014d345e4f24bbeaa2`). Effect:

- `.github/dependabot.yml` and the workflow that re-recorded the manifest on Dependabot's
  pull requests are removed. The repository's Dependabot alerts and security updates were
  already off. Its three open pull requests (#2, #6, #7) are closed unmerged.
- Checking every pin is the first thing a project does, before its first push, and it is
  repeated before each template release: `docs/DEVELOPMENT.md`, "Pins", lists each pin,
  where it lives and how to check it. The README's setup steps and the project README
  point to it.
- T19's remedy changes with it: no Dependabot pull request can open on a new project's
  first day, because nothing opens one.

**17. "Approved. Proceed"** (2026-10-30)

In answer to the location of WP5's report, the ROADMAP's "Phase 13, WP5, as built", at
`7bb66ab` with decision 16 applied. Recorded verbatim above (SHA-256 of the quoted text
`ee2f1c16cb76ac05bf5d0dec86237aa816eaf58c59dddb0b3b15f994b6354ecb`). Effect:

- WP5 (T13 to T19, T21) is accepted as built, T19 as decision 16 changed it; phase 13 is
  done.
- Next is a tagged template release under `docs/template/RELEASING.md`, its first item
  every pin checked, then WP6.

**18. CCO: "Keep v2.0 (Recommended)". ROBOT: "Move to 1.9.11 (Recommended)".** (2026-10-30)

The architect's two choices when the pins were checked for the first template release
(`RELEASING.md`, item 1), recorded verbatim (SHA-256 of the two answers, one per line, in
that order: `6845385672a0a90b1aec8c932fd1f7cac9cb46df5029c883eaadf63247df01c8`). Effect:

- CCO stays at `v2.0-2024-11-06` for this release, though v2.1 and v2.2 exist. v2.2
  refactors the communication classes, removes Proposition and deprecates duplicate
  datatype properties; the BPO port WP6 evaluates was built on v2.0, and moving now would
  have WP6 measure two changes at once. The move is its own work, after WP6.
- ROBOT moves from 1.9.10 to 1.9.11 (`config/reasoning.yaml`), which fixes catalog
  handling in `merge`, the command the Protégé catalog test runs. The jar's digest is the
  one GitHub publishes for the asset.

**19. "v0.1.0, tag and push (Recommended)"** (2026-10-30)

The architect's answer to which version the first template release is, recorded verbatim
(SHA-256 `9868d332c6124daebc1118bdabd374342d8ef6aec7ce7a5dd0bfaa19ac4deed6`). Effect:

- The first template release is `v0.1.0`: pre-1.0, since WP6 and T9's policy are open.
  The manifest is recorded with that label in its own commit, the tag goes on that commit
  (`RELEASING.md`, items 4 and 6), and the tag is pushed.

**20. Their reply: "Record it verbatim (Recommended)". A1 to A7: "Accept all as proposed (Recommended)". A8: "Note BPOTEST is BPOT (Recommended)". The pin-check command: "Build now, release after WP6 (Recommended)".** (2026-10-30)

In answer to the BPO Testing Team's reply to the WP6 readiness request,
`BPOTEST-EXAMPLE-2026-10-30-wp6-readiness-answer` in `communications/bpotest/incoming/`,
which asks for these acts (`requires_act: true`). Recorded verbatim (SHA-256 of the four
answers, one per line, in that order:
`bce97a90463d71a9ed9b7f132a4a211fe078fc84396c9a498ed98d044f4db6bf`). Effect:

- Their reply is recorded in this public repository byte for byte, as the protocol
  requires. It is a message written to us for this exchange; it carries no ontology
  content, credentials or execution logs.
- The §7 protocol is amended by A1 to A7 as proposed. WP6 runs in two phases: Phase A (S0
  and S1, the process verdict, the template-controls verdict, the browser run) and Phase B
  (S2, the BPO-quality verdict, the S2 release evidence). S0 is rebuilt by the port tool
  with BPO's approved changes off, tagged, and checked lossless against `bc64e91`. Every
  state is measured on one branch on v0.1.0, its content shown byte-identical to its tag
  first. A real defect new at S2 counts against it. The reasons for dispositions are
  written and approved per class of finding, with one register entry per finding. The
  classification is fixed in Phase A, before any correction. **No template release lands
  between Phase A and Phase B**; if one must, both phases are re-measured with it.
- A8: `BPOTEST` stays this record's code for the team, and its README says that the team's
  own code is `BPOT`. No message already committed changes.
- T19's amendment: a pin-check command whose output can be cited is built on `main` and
  stays unreleased until WP6 ends (A7). Phase A records the pins by hand, as the team
  proposed. v0.1.0 stays the instrument.

**21. "I agree with your recomendations proceed"** (2026-10-30)

In answer to what WP6 is and what building the BCO proposals now, and in which order,
would do. The recommendation, as given: build P1 now, then P3 and P2, in BCO's order; hold
the checks (P4, P5, P7, P8, and P6 last) until WP6 ends or the BPO Testing Team's Phase A
results are in. Recorded verbatim (SHA-256
`48656f70ebee409c686004d931ae9c24433ea35452e5d695c8ffbacf8a7149fc`). It decides on the
response to the BCO team's process account
(`docs/template/evaluations/2026-10-30-bco-process-account-response.md`) as BCO's answer
(`BCO-EXAMPLE-2026-10-30-process-proposals-answer`) amended it. Effect:

- The response's lanes with gates are accepted, with BCO's refinement: the terminology
  lanes join the decision path at named gates, and a lane finding may raise an open issue
  on it. BCO withdrew its strict order.
- P8, a rights and provenance record, is added to the proposals, as BCO asked.
- Built now, on `main` and unreleased under A7: **P1**, the ontology method
  (`docs/process/METHOD.md`); **P3**, a scope charter form; **P2**, a stage-standard
  skeleton and `config/stages.yaml`, with the check that a started stage names a standard.
  P2's check is part of P2 as proposed; it is the one check built now.
- Held: P4, P5, P7, P8 and P6, until WP6 ends or Phase A's results are in, so that each is
  designed with evidence from both teams. BCO's narrowing of P4 and P6 and its additions to
  P5 are carried with them.
- Not decided: how BCO corrects CM-01's stakeholder checkbox, which is BCO's own decision;
  and whether anything is sent to BCO about this decision.

**22. "Commit verbatim now"** (2026-10-31)

In answer to how to record the BPO Testing Team's Phase A results
(`BPOTEST-EXAMPLE-2026-10-30-wp6-phase-a-results`), whose §8 quotes one APQC process-element
name as an example of a false alarm, while T9 is with Legal. The options shown were: hold
the record and ask the team whether the phrase may be public; commit verbatim now; hold
until Legal answers. Recorded verbatim (SHA-256
`f93439ae42c0728613723caf4a3b977b30b98da47a7132b27646912ed647c0ba`). Effect:

- The results are recorded byte for byte in `communications/bpotest/incoming/`, as decision
  20 requires, with the one APQC element name they quote.
- It decides how this message is recorded, nothing more. It is not a finding that APQC text
  may be published, and it does not anticipate T9 (decision 15).
- Phase A is done. Its seven template findings, P-A1 to P-A7, are not yet disposed; under
  A7 none is released before Phase B is measured.

**23. "agree, proceed"** (2026-10-31)

In answer to the proposed handling of the BPO Testing Team's nine template findings from
Phase A: P-A1 to P-A7 in its results, P-A8 and P-B1 in its supplement
(`BPOTEST-EXAMPLE-2026-10-31-wp6-phase-a-supplement`), both checked against the template
and found to hold. The proposal, as given: all nine fixed after WP6, P-B1 first; push the
two records; then draft an acknowledgment to the team. Recorded verbatim (SHA-256
`14110570e83ff5b5667f786be10f665c936fadc99fd46722215981b4054eb982`). Effect:

- The nine findings are accepted as template findings, to be fixed after WP6 ends, so the
  instrument Phase B measures with does not change (A7). P-B1 is first: it is a check that
  passes what it should report.
- P-A4 (a scheme rule relating a local name to a literal) is considered then, not
  committed to: it may be BPO's alone.
- An acknowledgment to the team is drafted for the architect to approve; sending it is the
  architect's call.
- Not decided: the order of the other eight, and whether any is designed with P4 and P5
  (P-A7 touches the same register).

**24. "agree proceed"** (2026-10-31)

In answer to the BPO Testing Team's request for the template's formal decision on protocol
amendment A9 (`BPOTEST-EXAMPLE-2026-10-31-wp6-a9-four-states`), submitted by the BPO
architect: a fourth state, S2u, BPO's corrected source ported without the template's
changes, so that S0 to S2u measures BPO's corrections and S2u to S2 the template's effect on
the corrected source. The recommendation, as given: accept A9 with three clarifications;
note P-B1's confirmed requirement and the three detection requirements in the roadmap;
record the message; draft an answer for the architect's approval. Recorded verbatim (SHA-256
`a0c0312135cd612ac536665473179b3863037729f41245c7f30beefe363d1610`). Effect:

- A9 is accepted, with the original S0 and S1 evidence kept as it is. It is what decision 14
  asks of WP6: improvements in the template kept apart from improvements in BPO's content.
- **The instrument is unchanged.** S2 is ported with template v0.1.0, as S1 was, so S0 to S1
  and S2u to S2 measure the same template; what has landed on `main` since (decision 21) is
  not part of it (A7). The comparison tooling A9 updates is the port's, not the template's.
- **Template-prompted changes count as the template's.** The four changes BPO adopted from
  the template process are in S2u because they are in BPO's source; the final report counts
  them with the template's effect, not with BPO's corrections, so S2u to S2 is not reported
  as the template's whole effect.
- **The kept `dct:rights` notice is accepted as a declared change to the port's mechanics,
  not on its legal premise.** That APQC's licence requires the notice is not established
  here or relied on; T9 is with Legal (decision 15).
- P-B1, already accepted (decision 23), carries the BPO architect's requirement that each
  definition is evaluated on its own. The three detection requirements (possible homonyms,
  duplicate classes, relations that claim more than their axioms) are recorded as
  requirements after WP6, not as defects with a known fix: a check may flag a candidate, and
  a person decides identity.
- An answer to the team is drafted for the architect to approve; sending it is the
  architect's call.

**25. "approved. proceed"** (2026-11-03)

In answer to the Semantic Data Dictionary team's request
(`SDD-EXAMPLE-2026-10-27-cco-class-hierarchy-register`) that the template vendor, for CCO,
every class's named direct superclasses from the same pin, so that a consumer can tell
which BFO category a CCO term falls under. The recommendation, as given: accept; write it
as a separate file beside each register, so the register's bytes do not move; for every
source, not only `select: named` ones; generated by `vendor_upstream.py` and digest-checked,
with a test that fails when a superclass is dropped or invented; on `main`, unreleased until
WP6 ends (A7); and register SDD as a correspondent. Recorded verbatim (SHA-256
`8e8366543809a89ecb7b52d055940433b7ad945572bc0fdd51d01d34ffd56da5`). Effect:

- SDD is a correspondent (`communications/sdd/`). Its code for this repository is `OT`; its
  messages' copies here carry this record's header, which names `EXAMPLE`.
- `vendor/bfo/bfo-hierarchy.json` and `vendor/cco/cco-hierarchy.json`, generated from the
  pins, with their digests in `config/upstream-extracts.json`. The extracts and registers
  are byte-identical to before.
- Building it found that the register alone could not close every chain: CCO v2.0 declares
  BFO 2.0's process profile, which BFO 2020 does not have. Such a class is recorded under
  `outside_namespace`, as the source describes it, and is not added to either register.
- Not released until WP6 ends: v0.1.0 stays the BPO Testing Team's instrument. An answer to
  SDD is drafted for the architect to approve; sending it is the architect's call.
- Not decided: whether the IRI linter should report a reference to a term the pinned BFO
  release does not have, such as `obo:BFO_0000144`.

**26. "Please note we have a new communications repo and policy communicating through
discussions. Align our repos communicaiton to the new policy and then I believe you have a
message."** (2026-11-05)

With the link `https://github.com/Skreen5hot/communications`. Recorded verbatim (SHA-256
of the two lines as given `387dfa6370f153e3534eddcecc6bc44f27f67a147389be97bc599ce47ce3c5d6`). Effect:

- The record follows the shared protocol, version 1.1 (`PROTOCOL.md` at `05068d8`, the
  `protocol-v1.1` tag, sha256 `fb3a0630…`), and `communications/README.md` now says so and
  no longer holds a copy of the rules, which were its version 1.0. What this record adds
  (codes it keeps as aliases, where decisions go, the check, alerts and the inbox) is
  stated there.
- `.gitattributes` keeps `communications/**` byte for byte (Rule 7).
- `tools/communications.py` follows renames: a byte-identical move is allowed, a move that
  edits and a deleted message are refused (Rule 1, as 1.1 states it). It checks the version
  statement and the attribute; `--alert` prints a pushed message's alert, bound to the
  committed bytes; `--inbox` lists the board's alerts this record does not hold. It posts
  nothing, and the board repository's own tools are not run here.
- Codes: this record keeps `EXAMPLE` for itself and `BPOTEST` for the BPO Testing Team,
  aliases the shared list records for `OT` and `BPOT`.
- Not decided: posting alerts for the messages already sent before the board existed,
  which the protocol does not require.

**27. "I accept the verdict"** (2026-11-05)

In answer to `evaluations/2026-11-05-wp6-results-analysis.md` (SHA-256 of the proposed text
`9bb2160215da2c25362321c475c86af5ac8d9deaf3918894b5b5e78e49dda053`; the file differs only in
its status line), which analyses the BPO Testing Team's Phase B results. Recorded verbatim
(SHA-256 `45cf989ffd4c8efc04e3a3a63a36a98e1bd36a415606d2510093cbe10bfd3abe`). Effect:

- The template's own reading of WP6 is §1 of the analysis: an effective detector of
  structural defects and an effective reproducibility frame, not a substitute for
  referent-level review.
- Not decided: the fourteen changes of §4, the order of §5 and when WP6 ends, which the
  architect gives after reviewing them.

**28. "Yes, lets add the domain and ranges However, CCO has some domains and ranges NOT
specified so it means "anything" should we make the value owl:thing? What are the
consiquences of this? Low priority after BPOT"** -- then, after the consequences were
given: **"Regarding SDD domain and range: I like the derived domain and ranges."**
(2026-11-05)

In answer to the Semantic Data Dictionary team's request
(`SDD-EXAMPLE-2026-11-04-domain-range-register`). Recorded verbatim (SHA-256 of each
`79700b548440816ce093d19e030391309506cab412649e342c83f377eaa4377c` and
`cca679ad89bc81ded3a209f8d0746cf709b936b0b5261dfc4e2449945dffd998`). The consequences
given: at these pins, 110 of CCO's 225 object properties state no domain, and 95 of those
inherit one from a superproperty and 1 through an inverse, leaving 14 unconstrained (ranges:
109, 105, 0, 4). Writing `owl:Thing` would be wrong for most of them, would invent an
assertion the source does not make, and would break a check that follows the named
hierarchy to BFO's entity. Effect:

- Accepted. Each source gets a file of every object property its register lists: its named
  domains and ranges as asserted, a count of the anonymous ones, and its superproperties and
  inverses. Beside those, a derived effective domain and range, computed through
  inheritance and labelled as derived. No `owl:Thing` is written where the source states
  none; an effective domain that is empty is documented as unconstrained.
- Low priority: built after the WP6 work, on `main`, unreleased until WP6 ends (A7). The
  answer to SDD is sent when it ships.

**29. "BPO Architect — Final WP6 and BPOT Findings Disposition"** (2026-11-05)

In answer to the fourteen changes of `evaluations/2026-11-05-wp6-results-analysis.md` §4 and
the reading of them given in session. The whole text is recorded verbatim in
[`evaluations/2026-11-05-wp6-disposition.md`](evaluations/2026-11-05-wp6-disposition.md)
(SHA-256 of the text below its rule `af3baa58404ae6b7a68286a64bc2f4c5801d942c24b7d18d3c4efbceece780a5`). Effect:

- Approved: items 1 to 4 for the first release after WP6; item 5, with separate fields for
  a finding's validity, origin and resolution, designed with P5; item 6; items 7 to 9, as
  controlled, lower-priority enhancements; item 10, as documentation of definition
  provenance, without treating the project's authorship as an external source; item 11,
  after dependency locking; item 12, raised to the next governance cycle, with P5.
  Rejected: items 13 and 14.
- Decision 28's low-priority disposition for SDD's domain and range file stands.
- WP6 closeout is authorized once the evaluation artefacts, comparison evidence, finding
  dispositions and reproducibility record are confirmed, including that no unavailable
  validation rung was represented as zero findings. The confirmation is
  `evaluations/2026-11-05-wp6-closeout.md`. Every condition holds except two, which it names
  for the architect: BPO's K20 and K21 are still proposed, and the explorer's browser run
  was less than committed.
- None of the twelve approved improvements is built before WP6 closes. They are the
  prioritized backlog in `ROADMAP.md`, "After WP6".
- The next phase is template improvement informed by WP6, not more WP6 experimentation.

**30. "1. Approve 2. Accept as done"** (2026-11-05)

In answer to the two conditions `evaluations/2026-11-05-wp6-closeout.md` §2 left open:
(1) whether the architect, as BPO's architect, approves BPO's classes K20 and K21 for the
deprecation regression, still marked proposed in the team's classification; (2) whether the
explorer's browser run, a local v0.1.0 build of S1 inspected without screenshots, a per-term
checklist or a planted conflict, is accepted as done with those limits. Recorded verbatim
(SHA-256 `2901570702833e1132425007beb95ec21f0839ec78290f5feaaaaae882f000df`). Effect:

- K20 and K21 are approved. The team's own record still says proposed; correcting it is the
  team's.
- The explorer's browser run is accepted as done, with its stated limits. No planted-conflict
  browser check is added to the backlog.
- Every condition of the closeout holds, so **WP6 is closed** under decision 29's
  authorization. A7 is lifted: the template may be released again.
- The first release after WP6 is begun, with items 1 to 4 of the backlog, item 1 first.

**31. "1. yes push 2. Update the massage and is the message stail does anyone need to
respond? IF NO then we do not need an alert. IF yes ALERT 3. Yes prepare it as v0.2 with
label and release notes"** (2026-11-05)

In answer to three questions: whether to push backlog items 2 to 4; what to do with the
drafted closing message to the BPO Testing Team, which said P-B1 was "next" when items 1 to
4 were built; and whether items 1 to 4 make a release. Recorded verbatim (SHA-256
`51ebbb18a6312ebcffa331eccdee51fbf30d75903bee43997a20d755641bad15`). Effect:

- Items 2 to 4 are pushed. The unsent draft, never pushed, was dropped and written again
  with items 1 to 4 as built: `communications/bpotest/outgoing/2026-11-05-wp6-closed.md`.
- The message asks nothing of the team (`requires_act: false`; its updating
  `classification.md` and tagging `2628fc1` are left to the team, without a reply asked),
  so **no alert is posted** for it.
- The second template release is **v0.2.0**, prepared under `RELEASING.md`: the manifest
  recorded with the label `v0.2.0` in its own commit, and the release notes in `ROADMAP.md`,
  "Release v0.2.0". Tagging and pushing the tag wait for the architect (item 6).

**32. "Ontology Template — Architectural Decision 30"** (2026-11-06)

In answer to the five questions of `evaluations/2026-11-06-items-5-6-design.md` §5. Headed
30 by the architect; numbered 32 here, since 30 and 31 were already recorded. The whole text
is recorded verbatim in
[`evaluations/2026-11-06-items-5-6-disposition.md`](evaluations/2026-11-06-items-5-6-disposition.md)
(SHA-256 of the text below its rule `3e765528e2a727299e3d179bdf2ee73ccbd989a37a5faedae6e57916a33ec5df`). Effect:

- The design is approved for implementation, amended; `f321ed0` is pushed.
- Item 5: `validity` (`real`, `false-alarm`, `unsure`), `origin` (`project`, `upstream`,
  `template`, and **`unknown`**, added), `resolution` (`accepted`, `deferred`, `reported`,
  `not-a-defect`), `classified_by` with a capacity from `config/review.yaml`. `unknown`
  requires `unsure`, `deferred` and a review date. `accepted` requires `real`;
  `not-a-defect` requires `false-alarm`; a false alarm may be `reported` (a checker
  defect); `unsure` requires `deferred`; `reported` requires a reference. `origin: upstream`
  requires the `upstream` field, and **not the reverse**: an upstream IRI does not make the
  upstream the cause. Classification never changes what a check finds or what the gate
  passes.
- Version 1 registers stay valid, unclassified entries reported as such; version 2 requires
  all four fields. No tool fills in a judgement.
- `config/review.yaml` with the four kinds; projects may add, not remove. A
  `rights-reviewer` records a rights review and implies no legal approval or qualification.
  P5's stage gates wait for item 12.
- uv generates the lock, and only the lock. Before release: fresh installs from the one lock
  on Linux, Windows and macOS; uv pinned with its checksum verified, and pip's bootstrap
  version handled explicitly; every locked distribution scanned, a scan that could not run
  told apart from a clean one. The Release workflow pinned to `ubuntu-24.04`. Python's
  patch recorded, not pinned; 3.12 stays the declared baseline.
- Seeded: the three shape sets, their three fixtures, the annotation-profile, naming,
  reasoning and upstream-sources config; the generated profile shapes are not. A change to a
  BFO or CCO pin is reported as a dependency change needing review, never as an upgrade
  instruction; a project's pin stays authoritative. A comparison that cannot be made is
  reported so, never as unchanged.
- Order: P-A1, then P-A3, then P-A7, released as **v0.3.0**, with nothing else from the
  BPOT findings unless a release-blocking dependency is identified.

**33. "Adopt the current behaviour as my policy; I accept the risk"** (2026-11-06)

In answer to the five questions of the T9 request
(`communications/legal/outgoing/2026-10-28-t9-third-party-text.md`), which no Legal
correspondent exists to answer, set beside what the tools already do. Recorded verbatim
(SHA-256 `f1f4bff79aa0f2349136186dac85beb7db72f20a94b36c9f352c94fca7aa987d`). Effect:

- T9's policy is the architect's, and is what the tools did when it was asked:
  1. A declaration is the annotation property, the source, its release, the licence (an
     SPDX identifier or `unknown`) and the attribution text.
  2. The report's statement is the sentence proposed in the request, without its PENDING
     LEGAL prefix: it records what the project declares and checks that the declared
     source, release and attribution are present; it does not judge whether the text may
     be redistributed.
  3. Text whose licence is `unknown` is reported, and passes, when it is declared and its
     module carries the declared attribution.
  4. The attribution is checked on the module header only.
  5. The template refuses nothing for publication by its licence.
- The architect accepts the risk of adopting this without legal counsel. The policy is the
  template's rule for what its checks require; it grants no project permission to
  redistribute any text, which stays each project's own question (BPO's B2 stays BPO's).
- Decision 15's open dependency is closed: T9 is done. The request is answered by
  `communications/legal/outgoing/2026-11-06-t9-policy-adopted.md`, which closes its thread;
  LEGAL has no repository, so no alert is posted.

**34. "1. stages.py 2. domain practioner or proxy, yes name 3. Accept format and example 4.
Yes test 5. fold 7 into 12 6. Agree with order"** (2026-11-06)

In answer to the six questions of the item 12 design
(`evaluations/2026-11-06-item-12-design.md`, section 8). The whole text is recorded
verbatim in
[`evaluations/2026-11-06-item-12-disposition.md`](evaluations/2026-11-06-item-12-disposition.md)
(SHA-256 of the text below its rule `55a6a3efb65f1e740aa65734fb1898ebab9cb8d55385f2327ddfc3146bf009af`). Effect:

- The design is approved, as amended by the answers; where they differ, the answers hold.
- 1: the review gate is in `tools/stages.py`: it refuses a stage marked done while a
  candidate in its scope has no disposition from a kind the stage requires, and never
  fails because a candidate exists.
- 2: a domain question is answered by a domain practitioner **or a proxy**, and the charter
  names them. Read as: a new kind, `domain-proxy`, for a person the charter names as
  standing in for domain practitioners; the domain rules (`genus-differs`,
  `near-duplicate`, `category-in-differentia`) accept `domain-practitioner` or
  `domain-proxy`, and a disposition says which, so a proxy's answer is never recorded as a
  practitioner's. The charter must name both, or say none has been found; `stages.py`
  checks that a stage with a review gate has them named. The ontologist rules
  (`necessity-without-axiom`, `inverse-necessity`) are as proposed, the answer not having
  changed them.
- 3: candidates from a model or any other source come in through the import format with
  its provenance header, and the template ships an example prompt as text; no runner, and
  nothing model-based in CI.
- 4: the generators are run locally against the BPO corpus WP6 evaluated; only counts and
  whether each known WP6 defect is raised are recorded, and no BPO text enters the
  template or its CI.
- 5: item 7 is folded into item 12, as the `genus-differs` and `near-duplicate`
  generators.
- 6: item 12, with P5, is the next release, **v0.4.0**, with the "merge by hand" defect
  fixed alongside; the rest of the backlog keeps its order after it.
- "update and push": the record, the design's status and the ROADMAP are updated and
  pushed. Nothing is built yet.

**35. "the roles are Domain Expert, Proxy Domain Expert, and Ontologist"** (2026-11-06)

Given after decision 34, correcting its reading of "domain practioner or proxy". The whole
text, which also says who holds the proxy role, is recorded verbatim in
[`evaluations/2026-11-06-review-roles.md`](evaluations/2026-11-06-review-roles.md)
(SHA-256 of the text below its rule `c4c0186636b6033deb28fa53f71cfd412c60bf285f3b999f298992922a519eb3`). Effect:

- The review roles for item 12's candidates are **Domain Expert**, **Proxy Domain Expert**
  and **Ontologist**. Decision 34's reading, a kind `domain-proxy` beside
  `domain-practitioner`, is replaced: v0.4.0 renames `domain-practitioner` to
  `domain-expert` in `config/review.yaml`, `tools/findings.py` and the charter form, and
  adds `proxy-domain-expert`. `architect` and `rights-reviewer` stay, for decisions and
  rights reviews (decision 32); they answer no item 12 candidate.
- The domain rules (`genus-differs`, `near-duplicate`, `category-in-differentia`) accept a
  Domain Expert or a Proxy Domain Expert; the ontologist rules accept an Ontologist. A
  disposition names the role it was given in, so a proxy's answer is never recorded as an
  expert's.
- Who holds the proxy role, as the architect states it: the architect is the business
  process Proxy Domain Expert, with twenty years in business and business process and no
  business process certification, acting because the work is needed and no expert has
  stepped forward, and will transfer the role to a Domain Expert when one comes. The work
  goes forward under the proxy. This is recorded in the projects' charters (BPO's and
  BCO's), which are those projects' to write; the template records only the roles.
- Proposed for the v0.4.0 build, not decided: when a charter first names a Domain Expert,
  no proxy answer is invalidated; the dispositions given by a Proxy Domain Expert are
  listed as that expert's review queue.

**36. "Architectural Decision 34 — P4 Source Adequacy"** (2026-11-06)

In answer to the seven questions of `evaluations/2026-11-06-p4-design.md` section 7. The
whole text is recorded verbatim in
[`evaluations/2026-11-06-p4-disposition.md`](evaluations/2026-11-06-p4-disposition.md)
(SHA-256 of the text below its rule `fe907de8ea5df4f74a0c816f5d5fb3b0cc2293faf355dd644ab8a0409b6998f3`). Its heading numbers it 34; it is filed as 36.
Effect:

- P4 is approved for implementation and release as **v0.5.0**, alone: not P7, P8, P6 or
  other source-governance features. The release is authorized once its tests pass.
- The seven answers: `research/sources.yaml`, seeded, with `research/sources.md`
  generated; decisions are `docs/decisions/`, `docs/standards/` and `docs/charter.md` by
  default, in seeded `config/sources.yaml`; the architect approves exceptions, and a
  project may delegate to another reviewer kind; the quote limit is unset by default and
  is not a legal determination; an inadequate citation fails Checks; a whole-source
  citation needs at least one claim and every claim V or P.
- Three refinements before implementation: **A.** each claim has an explicit, stable id
  (`id: C1`), so a citation never depends on list position; BCO's positional claims may
  be read only in the measurement. **B.** a V or P claim states the scope of the primary
  text examined; the documentation warns that a whole-source citation does not certify the
  register's coverage of the source, and prefers claim-level citation. **C.** an explicit
  convention tells a non-evidentiary mention from a citation; an exception never changes a
  grade, and records its reason, scope, approver and decision file.
- With no citations, the check passes and reports zero evaluated, never as evidence that
  decisions are well sourced. Stale exceptions are detected. Delegating exception
  authority to another kind is recorded; adding a kind alone confers none. A rights
  reviewer's judgement is distinct from source adequacy.
- Tests: negative and mutation tests, with regression coverage for stable claim ids,
  missing claims in whole-source citations, stale exceptions, and mentions. The read-only
  measurement on BCO's register reports entries processed, invalid data, adequate and
  inadequate citations and exceptions, BCO's files unmodified.
- "then push": the implementation is pushed when done.

**37. "Send a short answer saying the request is accpeted but in backlog"** (2026-11-06)

In answer to whether SDD's domain-and-range request
(`SDD-EXAMPLE-2026-11-04-domain-range-register`) had been answered: it had not, and the
thread stood open, because decision 28 deferred the answer until the file shipped.
Recorded verbatim (SHA-256 `8afc859dca7ae954736349ab740ac63610c276dc4fee4f391f6fce57bab00f68`). Effect:

- A short answer is sent now:
  `communications/sdd/outgoing/2026-11-06-domain-range-accepted-in-backlog.md`. It says
  the request is accepted as decision 28 describes and where it stands in the backlog,
  and that a notice follows when the file ships. It asks nothing of SDD.
- Decision 28's "the answer to SDD is sent when it ships" is replaced by this answer and a
  later notice. The backlog's order is unchanged.

**38. "Architectural Decision — P7 Approved"** (2026-11-06)

In answer to the seven questions of `evaluations/2026-11-06-p7-design.md` section 7. The
whole text is recorded verbatim in
[`evaluations/2026-11-06-p7-disposition.md`](evaluations/2026-11-06-p7-disposition.md)
(SHA-256 of the text below its rule `a1ab35fba6000bac5e9424a84723565193a299b53d6463ab412be31b52cdd636`). Effect:

- P7 is approved for implementation in **v0.6.0**. The seven proposed answers are
  accepted: YAML front matter with `carries_into` or `carries_nothing`; the records are
  `docs/decisions/*.md` in seeded `config/decisions.yaml`; older records are covered by
  `required_from`; a target is a file; owed targets are reported always and held by the
  stage gate, never failing ordinary CI; the read-only BCO DP-1 and DP-2 measurement; P7
  as v0.6.0.
- Three safeguards: **1.** a valid target not yet created is reported as owed, not
  refused; its stage cannot close until it is created, tracked and cites the decision.
  **2.** an owed target outside every configured stage scope stays visible, and is
  assigned or explicitly accounted for before the project releases. **3.** a decision is
  cited by exact identifier matching: no false matches, and no decision satisfied by
  itself.
- The tool establishes whether a declared obligation is referenced in its target, not
  whether the decision was carried faithfully; that judgement stays with the appropriate
  human reviewer.
- "Proceed with implementation, negative and mutation tests, documentation, and the v0.6.0
  release checklist." No other governance feature, and no later backlog item, without a
  separately approved need. No further design review unless implementation reveals a
  material contradiction.
