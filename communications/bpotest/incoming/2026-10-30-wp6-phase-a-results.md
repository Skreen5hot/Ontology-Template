---
id: BPOTEST-EXAMPLE-2026-10-30-wp6-phase-a-results
from: BPOTEST
to: EXAMPLE
date: 2026-10-30
type: answer
subject: WP6 Phase A results; seven template findings
in_reply_to: EXAMPLE-BPOTEST-2026-10-30-wp6-amendments-decided
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: d476a2f185f4a6ddb4eddba15ee3b7e278af3390
    path: communications/bpotest/outgoing/2026-10-30-wp6-amendments-decided.md
    sha256: 107c25aaae85917504364a45f8a8cf1b7020b1afc62484c0f1ef44a52c021c15
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: true
source:
  repo: Skreen5hot/BPO-Template-Port
  commit: c52a491cc647751fec02a8a84d2e429262e8cbe2
  path: communications/example/outgoing/2026-10-30-wp6-phase-a-results.md
  sha256: 31848c25f2c8516fc75ea16437b140c1cb72fed9d6deb81b494ecfa36fc91b98
---
---
id: BPOT-EXAMPLE-2026-10-30-wp6-phase-a-results
from: BPOT
to: EXAMPLE
date: 2026-10-30
type: answer
subject: WP6 Phase A results; seven template findings
in_reply_to: EXAMPLE-BPOT-2026-10-30-wp6-amendments-decided
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: d476a2f185f4a6ddb4eddba15ee3b7e278af3390
    path: communications/bpotest/outgoing/2026-10-30-wp6-amendments-decided.md
    sha256: 107c25aaae85917504364a45f8a8cf1b7020b1afc62484c0f1ef44a52c021c15
  - repo: Skreen5hot/BPO-Template-Port
    commit: 119c0e17fd7bcaccd18f5fa936dfedcdb45fa408
    path: research/wp6/phase-a.md
    sha256: b5b8a3429e3564586344887f6359ce6e67ce59b6556117c25ede310f2306aa35
  - repo: Skreen5hot/BPO-Template-Port
    commit: 1abd33e99aa56c34fcc21d1a2c73139c9f3a32c2
    path: research/wp6/classification.md
    sha256: 4ec98d472b2e0794c0ad3cc72f4ae0d8c4426e52b39a7f99c3e0b2423a4a6b6f
  - repo: Skreen5hot/BPO-Template-Port
    commit: 1abd33e99aa56c34fcc21d1a2c73139c9f3a32c2
    path: config/findings-register.yaml
    sha256: fa0bfcb4463c58360d5ada2686b9cef56b6b3bd604ba9d55cfcd296d87837654
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: false
---

This answers `EXAMPLE-BPOTEST-2026-10-30-wp6-amendments-decided`, which we hold as
`EXAMPLE-BPOT-2026-10-30-wp6-amendments-decided`.

## Summary

- **Phase A is done.** All nine steps are complete. The explorer's browser run was an
  inspection by the BPO architect, without the screenshots and per-term checklist we had
  planned (§7).
- **S1 introduces no finding.** S0 has 4,323 findings by identity, S1 has 3,749, and every S1
  finding is an S0 finding. The 574 removed are exactly the PO's changes.
- **The checks finish at BPO size.** Validation takes 15 s on the runner, the Checks job
  6 to 9 minutes, Reasoning about 1 minute, and the release build 2.5 to 3.5 minutes.
- **The classification is approved and the register is filled.** Every S0 finding is in one
  of 17 classes, approved class by class by the BPO architect on 2026-10-30. With one entry
  per finding, Checks is green.
- **Seven template findings,** P-A1 to P-A7, below. None blocks Phase B. Under A7 we do not
  ask for any of them to be released before Phase B is measured.

The full record is `research/wp6/phase-a.md` on branch `wp6` (third reference).

## 1. Pins (step 1)

Checked by hand, pin by pin. Every action, Python package, BFO and ROBOT pin is current, and
each tag resolves to its pinned commit or digest. No advisory applies at any pin.

CCO v2.2 was released on 2026-08-14. BPO stays on v2.0 by its own decision: the pin is
shared with the BCO.

Not covered by any pin: the transitive Python dependencies (P-A1).

## 2. The upgrade to v0.1.0 (step 2)

A three-way merge of every file the template changed between `2455bcc` and `ee4353d`, with
init's transforms applied to both template sides:

- 54 files taken from v0.1.0;
- 2 merged;
- **0 conflicts**;
- 3 decided by hand: our `validate.py` patch gives way to your T1 fix, the manifest is yours,
  and the validation baseline gives way to the register.

The ontology did not move: it is byte-identical to `s1`, with an equal corpus digest.

The template documents no upgrade procedure (P-A2). `template_status.py --against` sees
none of the changes to a project's checks, because shapes, fixtures and the
profile, naming and reasoning config are project-owned. Those changes include over 300 lines
of shapes and the move from ROBOT 1.9.10 to 1.9.11 (P-A3).

## 3. S0 (step 3)

Tagged `s0` at `3690d2af73ebb3c6ca66ec19558cbd7a9220b5ef`, built by
`tools/port_from_bpo.py --unchanged` on BPO `bc64e91`.

Lossless check, by PORTING.md §4's method:

- **S0:** 49,336 statements on each side, none missing, none extra.
- **S1:** against the same source, S1 differs by exactly the PO-approved changes.

## 4. S0 and S1 measured by identity (step 4)

Each state's content was checked out from its tag and shown byte-identical, with an equal
corpus digest, before it was measured (A3).

| | S0 | S1 |
|---|---:|---:|
| Findings, by identity | 4,323 | 3,749 |
| Only in this state | 574 | **0** |
| Reasoner | consistent | consistent |
| Release build | pass, 210 s | pass, 145 s |

At `2455bcc` the ladder had not finished after 1 h 56 min, and the release build had not
finished after 5 h 22 min. **T1 and T2 are fixed at BPO scale.**

Your corrected figures:

- **T11:** confirmed, 18 qualifier warnings.
- **T23:** confirmed for S0, 14 of 15 modules. S1 names the release on all 15.
- **T10:** v0.1.0 reports 563 placement findings at S0, one per (class, property, class)
  assertion, not "2 used properties in 494 assertions on 453 classes". S1 removes all 563.

Our totals differ from your §3 count (3,716) because v0.1.0 measures more:

- comment agreement (53);
- placement (563);
- the scheme rule (39);
- a broader genus check (233 where `2455bcc` gave 13).

## 5. BPO's D7 rule (step 5)

Configured as a scheme rule in `config/naming.yaml`. It reproduces Gate F's 39 exactly.

BPO's second D7 rule cannot be stated: a non-capability class with a `pcfID` must be named
`P<pcfID>`. It relates a local name to a literal (P-A4). Measured outside the instrument, it
holds at both states.

## 6. CI on GitHub's standard runner (step 6)

Runner `ubuntu-24.04`, image 20261025.353.1, private-repository minutes.

| Run | Checks | Reasoning |
|---|---|---|
| Cold, empty register | 8 min 41 s (41073682960) | 59 s (41073705706) |
| Warm, empty register | 6 min 46 s (41076561290) | 64 s (41076566073) |
| **Register filled** | **8 min 20 s, green** (41106582545) | — |

With the register empty, every check still ran (T5 fixed), and the verdict named the three
that failed. With it filled, the verdict reads "every check passed" and 396 tests pass.
The 3.1 MB register does not measurably slow the job.

## 7. The explorer (step 7)

All 137 label and definition variants of the 51 drifted classes are in the explorer's data,
each with its module and a conflict note. T7 is fixed.

The BPO architect inspected the explorer in a browser and found it good. That is less than
we said we would record in our readiness answer: there are no screenshots, no per-term
checklist and no planted conflict. The data check above is the per-term evidence.

The explorer shows no comments at all, so the 53 comment-drift warnings cannot be seen on
the site (P-A5).

## 8. Classification and the dispose stage (step 8)

**Approved.** `research/wp6/classification.md` (second reference) sorts every S0 finding into
one of 17 classes. A tool does the sorting, and it refuses to finish if a finding is in no
class or in two. Each class has a classification, an owner and a reason, approved by the BPO
architect on 2026-10-30. Under A6 the classification is now fixed for S2.

| Classification | S0 findings |
|---|---:|
| real | 4,301 |
| upstream (CCO 2.0's Organization ⊄ Agent) | 5 |
| false alarm (APQC's own element names, e.g. "Process accounts payable (AP)") | 9 |
| unsure (8 classes with two genuinely different parents) | 8 |
| template bug | 0 |

Six known defects that no check finds are listed with it (G1 to G6). G1 and G2 are the APQC
text and its release, pending Legal.

**Register.** 3,749 entries, one per S1 finding, each carrying its class's reason, owner and
review date (fourth reference). The 5 upstream entries name the CCO term.

**The dispose stage, exercised.** `validate.py --gate` on S1:

| Plant | Count | Gate |
|---|---:|---|
| none | 3,748 | pass |
| a new finding | 3,749 | fail, `NEW`, by name |
| a finding fixed, its entry left | 3,747 | fail, `STALE`, by name |
| an entry deleted | 3,748 | fail, `NEW`, by name |
| a fix and a new finding together | **3,748** | **fail, both by name** |

The last row is the case the count-based gate at `2455bcc` passed.

## 9. The template-controls verdict, re-rated (step 9)

| Stage | At `2455bcc` | At v0.1.0 |
|---|---|---|
| Detect | structure only; missing punning, licensing, scheme rules | stronger: placement, comment drift, scheme rules, property definitions |
| Report | one count per check; fail-fast | by identity, every finding, every check run |
| Evaluate | nowhere to classify | used: 17 classes, approved per class (but see P-A7) |
| Dispose | a count per rung; none for IRI lint | works at BPO scale, by identity (but see P-A6) |
| Correct | the template reports, people fix | unchanged |
| Verify | did not finish at BPO size | finishes, well within budget |
| Keep up with the template | — | no procedure (P-A2, P-A3) |

The verdict on BPO's own quality is Phase B's, from S2 (A1).

## Template findings from Phase A

| Id | Finding |
|---|---|
| P-A1 | Transitive Python dependencies are unpinned (owlrl, html5rdf, prettytable, …). `requirements-dev.txt` says owlrl needs no pin because nothing imports it, but pyshacl imports it |
| P-A2 | No documented procedure for upgrading a project to a new template release |
| P-A3 | `template_status.py --against` does not cover the checks a project runs. Shapes, fixtures and the profile, naming and reasoning config are project-owned, so a changed shape or a ROBOT move is invisible to it |
| P-A4 | A scheme rule cannot relate a local name to a literal |
| P-A5 | The explorer shows no comments, so comment drift reported by the validator is invisible on the site |
| P-A6 | `--propose` writes one reason, owner and review for every new finding of a check. A project that disposes by class (A5) cannot use it as it stands; we called `findings.propose()` once per class instead. A filter by rule, or by a list of identities, would do |
| P-A7 | The register has no field for a finding's classification (real, false alarm, unsure); only `upstream` has one. The S2 verdict counts real defects, which then has to be read from the reason text |

One defect of our own: S1's mapping rows say "ported unchanged" for the three re-typed
properties (G3). Correcting it changes the mapping set, so it is corrected in the S2 port,
not on `s1`.

## What comes next

Phase B, when the BPO architect and Legal have dated their decisions, as we offered.
