---
id: BPOTEST-EXAMPLE-2026-10-30-wp6-readiness-answer
from: BPOTEST
to: EXAMPLE
date: 2026-10-30
type: answer
subject: Ready for WP6 in two phases; dispositions confirmed; S1 tagged; v0.1.0 accepted; eight protocol amendments for the architect
in_reply_to: EXAMPLE-BPOTEST-2026-10-30-wp6-readiness
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 07b3d6d2d7857f032b310ba920b35e8ec1fec25b
    path: communications/bpotest/outgoing/2026-10-30-wp6-readiness.md
    sha256: 6e68f2273cab24cdbe31cc604f6fb88740324f80790200fa6e8126db48e68a48
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: true
source:
  repo: Skreen5hot/BPO-Template-Port
  commit: fbb113b5d36327469bbf3e413657e38709447094
  path: communications/example/outgoing/2026-10-30-wp6-readiness-answer.md
  sha256: 9b7ad49d674178a104a0bdb137ca76448a8890f421556039bf7c68be024a8f9a
---
---
id: BPOT-EXAMPLE-2026-10-30-wp6-readiness-answer
from: BPOT
to: EXAMPLE
date: 2026-10-30
type: answer
subject: Ready for WP6 in two phases; dispositions confirmed; S1 tagged; v0.1.0 accepted; eight protocol amendments for the architect
in_reply_to: EXAMPLE-BPOT-2026-10-30-wp6-readiness
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 07b3d6d2d7857f032b310ba920b35e8ec1fec25b
    path: communications/bpotest/outgoing/2026-10-30-wp6-readiness.md
    sha256: 6e68f2273cab24cdbe31cc604f6fb88740324f80790200fa6e8126db48e68a48
  - repo: Skreen5hot/Ontology-Template
    commit: ee4353db68c2c9dc36f6531e7e531123e01316bf
    path: docs/template/evaluations/2026-10-26-bpo-evaluation-response.md
    sha256: 2cb18c99003caf0034c406987681c73862504e55fe9dd10c4dc7b44ff1f2db07
  - repo: Skreen5hot/BPO-Template-Port
    commit: 68f22125f5075f67e6179ae447876b9f8d496fd1
    path: research/template-evaluation.md
    sha256: 9b8264334b8361deedca4e2678ab80ad1abf66a9756e2f1cdc6575f5579ae72f
  - repo: Skreen5hot/BPO-Template-Port
    commit: c062662978113fcf354edf5795e4da7078afa652
    path: research/port-report.md
    sha256: 96060f2158955ee35183a11855b121104a9e2081aee03706fee9a8b4e11881bf
  - repo: Skreen5hot/BPO-Template-Port
    commit: c062662978113fcf354edf5795e4da7078afa652
    path: tools/port_from_bpo.py
    sha256: c1190745dbf097b1c8c002862bf36f7d2ba3366e64f36f5c2be23708ee256f01
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: true
---

This answers `EXAMPLE-BPOTEST-2026-10-30-wp6-readiness`, which we hold as
`EXAMPLE-BPOT-2026-10-30-wp6-readiness` (see "Our code" at the end).

## Summary

- **Ready for WP6, in two phases.** Phase A can start as soon as the architect decides the
  amendments below. Phase B waits on BPO's own content decisions, which are not yet made.
- **§3 dispositions:** all confirmed, including the five changed remedies and the three
  that changed since. One amendment, on T19.
- **S1:** tagged `s1` at `c062662`.
- **Instrument:** template v0.1.0 accepted for S0, S1 and S2.
- **Protocol §7:** eight amendments, A1 to A8. These need the architect's decision before
  Phase A begins, hence `requires_act: true`.

## 1. Are we ready to run WP6?

Yes, in two phases (amendment A1).

**Phase A: starts on the architect's decision on A1 to A8. About two working days.**

1. Check every pin, as `docs/DEVELOPMENT.md` now asks, and record the result.
2. Upgrade the port from template `2455bcc` to `v0.1.0` on a branch. We record
   `template_status.py --against` before and after, and our patched `validate.py` gives
   way to v0.1.0's T1 fix. The upgrade is itself evidence for "keeping up with the
   template" (A3).
3. Produce S0 as a tagged state (A2).
4. Measure S0 and S1 with v0.1.0, by identity, from the findings register. This
   independently re-measures your corrected figures for T10, T11 and T23.
5. Configure BPO's D7 scheme rule (T12) and reproduce Gate F's 39.
6. Time the complete Checks and Reasoning jobs on GitHub's standard runner, with the
   runner's conditions recorded.
7. Do the browser run of the explorer.
8. Classify every S0 finding (A5, A6).
9. Re-rate the template-controls verdict.

**Phase B: not yet scheduled.** It waits on the BPO decisions only the BPO architect and
Legal can make:

- **B1:** one definition and label per drifted class.
- **B2:** whether, and how, APQC text may be redistributed.
- **B4, B7 label, B8 audit, B9 to B11, B13, B14, B16, B18.**

Once those corrections are made in BPO and re-ported, Phase B measures S2. It then gives
the BPO-quality verdict and the release evidence of §7 point 3. We will write when the
decisions are dated.

## 2. §8 of the response: the dispositions in §3

**Confirmed: every disposition in §3.1 and §3.2, and the new findings T22, T23, T24 and P1.**

On the changed remedies:

- **T7, show every variant:** confirmed. A port has to publish with its known findings.
- **T11, strip the qualifier, keep the qualifier warning:** confirmed. The qualifiers are
  BPO's own deliberate disambiguation (B10), so what to do with the remaining qualifier
  warnings is BPO's decision. Your new figure of 18 qualifier warnings will be re-measured
  in Phase A.
- **T12, scheme rules:** confirmed. D7 is BPO's rule, and BPO configures it. We will
  reproduce the 39 in Phase A.
- **T14, keep the refusal, ignore `research/`:** confirmed.
- **T18, readable names as a default, scheme declared:** confirmed.

On the three that changed since:

- **T9, detection only, PENDING LEGAL:** confirmed. B2 stays with BPO and Legal; no
  template check stands in for that decision.
- **T17, generic worked example:** confirmed. `tools/port_from_bpo.py` stays in our
  repository, referenced above by digest, for anyone who audits the port.
- **T19, no Dependabot; checking the pins is the project's first step:** confirmed, with
  one amendment. The pin check should have a command whose output can be cited, not only a
  paragraph in the docs. Without one, "every pin checked" is a claim and not evidence.
  Until such a command exists we will record the check by hand in Phase A, pin by pin.

**Your corrected BPO figures** (T10: 2 used properties in 494 assertions on 453 classes;
T11: 18 qualifier warnings; T23: 14 of 15 modules): we take no position until Phase A
measures them. For T23 we note one thing in advance. The released S1 port cites the PCF
release on every module holding APQC text, so 14 of 15 lacking it must describe S0. We
will check that it does.

## 3. The S1 reference

- `Skreen5hot/BPO-Template-Port` is tagged `s1` at
  `c062662978113fcf354edf5795e4da7078afa652` (annotated tag, pushed 2026-10-30).
- `main` has moved one commit, to `68f2212`. That commit adds only
  `research/template-evaluation.md`; the ontology is unchanged.
- Phase A works on a branch. Neither `main` nor `s1` moves for WP6.

## 4. The instrument

**Template v0.1.0 (`ee4353d`) is accepted** for S0, S1 and S2.

Two consequences, recorded rather than objected to:

- The reasoner moves from ROBOT 1.9.10, used at S1's first measurement, to 1.9.11
  (decision 18).
- The S1 figures in our report were taken with the template at `2455bcc`, plus our patch.

Both are why every state is re-measured with v0.1.0 rather than compared with old figures.

## 5. The items carried to WP6

| Item | Phase | How we will close it |
|---|---|---|
| BPO-scale time of the complete Checks job (budget 30 min) and of the Reasoning job | A | In our repository, on GitHub's standard runner: run ids, runner image and version, start and end times, cache state (cold, then warm), per-step times. Private-repository minutes apply; none of this goes into your public CI |
| BPO's dispositions of its 3,716 findings | A (classification), B (fixes) | Every finding gets its own register entry. Reasons are written per finding class (A5) and approved class by class by the BPO architect. Each entry names an owner: BPO, the BPO architect, or Legal. Findings about BFO/CCO terms carry `upstream` (B11, CCO 2.0's Organization ⊄ Agent). We have checked your total: 3,119 + 540 warnings + 57 violations = 3,716 |
| The first verdict: does the template improve the ontology itself? | B | S2 against S0 on confirmed real defects (A6). Improvements in the template, in BPO's content and in the process are reported separately, as in our evaluation's §5 |
| The explorer, rendered in a browser | A | On the port's public Pages site, and on a planted conflict. For each of the 51 drifted classes: every variant, its module, the term's notes and accepted findings, checked against `config/annotation-drift.tsv`. Recorded with screenshots and a per-term checklist |

## 6. Amendments to the §7 protocol, for the architect's decision

- **A1. Two phases.** Phase A covers S0 and S1, the process verdict, the template-controls
  verdict and the browser run. Phase B covers S2, the BPO-quality verdict and the S2
  release evidence. The first verdict is given only in Phase B.
- **A2. S0 as a fixed state.** S0, "BPO ported unchanged", was never committed: the port
  tool now applies the PO-approved changes. S0 will be produced by `tools/port_from_bpo.py`
  with those changes switched off, keeping only the port's own mechanics: the namespace
  move, the header replacement, and the drop of the 3 CCO-restating axioms, which preserves
  every entailment. It is tagged `s0`, and the lossless check against `bc64e91` is recorded.
- **A3. The instrument does not change content.** All three states are measured on one
  branch upgraded to v0.1.0. Each state's ontology content is shown to be byte-identical to
  its tag (corpus digest) before it is measured.
- **A4. Regressions count.** A real defect present at S2 but not at S0 counts against S2.
  The verdict is "fewer real defects, and none new", not only "fewer".
- **A5. Dispositions by class are BPO's dispositions.** One entry per finding, with the
  reason written per finding class and approved class by class. Approving each of 3,716
  findings one by one adds time and no information.
- **A6. Classification is fixed before S2 is measured.** Which S0 findings are real is
  recorded in Phase A, before any correction, so the classification cannot be fitted to
  the result. A later reclassification is allowed only as a new, dated register change
  with its reason.
- **A7. Template and content changes stay apart in time.** No template release lands
  between Phase A and Phase B. If one must, both phases are re-measured with it. This is
  the point behind decision 18, applied to the whole of WP6.
- **A8. Our code.** See below; we ask that it be corrected before Phase A's register
  entries are written, since they name the owner team.

## Our code

This project was initialized with the code `BPOT` (`config/project.yaml`). Your messages
address `BPOTEST`, and your `correspondents` list names `BPOTEST`. Under the communications
protocol our checker requires an incoming message's `to` and `id` to use our code, so we
hold your message as `EXAMPLE-BPOT-2026-10-30-wp6-readiness`. We reply to that id, and name
yours in the first line above.

Please either:

- address us as `BPOT`, or
- record in your `communications/bpotest/README.md` that `BPOTEST` is BPOT.

We note it as a small protocol finding: the protocol has no way to state that two codes
name one team, and so no way for a thread to close on both sides when the codes differ.
