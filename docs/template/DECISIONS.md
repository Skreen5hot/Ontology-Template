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
