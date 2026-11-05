# WP6 closeout

**To:** the architect. **From:** the Ontology Template Team. **Date:** 2026-11-05.
**Status:** confirmed. **WP6 closed** 2026-11-05 (decision 30): the architect approved
K20 and K21 and accepted the explorer's browser run as done. A7 is lifted.

**Under:** decision 29, the architect's final disposition, which authorizes the closeout
once the final evaluation artefacts, the comparison evidence, the finding dispositions and
the reproducibility record are confirmed, and asks that unavailable validation rungs be
checked not to have been represented as zero findings.

The BPO Testing Team's records stay private (decision 20). They were checked where they
are, in `Skreen5hot/BPO-Template-Port`. This record names them by commit, path and digest,
and copies nothing from them.

---

## 1. What was confirmed, and how

| Condition | Confirmed | Evidence |
|---|---|---|
| **Final evaluation artefacts** | Yes | The four records the team's Phase B message cites, each read at port `2628fc1` (branch `wp6`) and matching its digest: `four-state-comparison.md` `20d382e8…`, `quality-evaluation.md` `fa669be3…`, `classification.md` `4ce7b089…`, `change-record.md` `3e13cda1…`. The template's reading is `2026-11-05-wp6-results-analysis.md`, verdict accepted (decision 27) |
| **Comparison evidence** | Yes | Per-state measurements under `research/wp6/measure/{s0,s1,s2u,s2}/` at `2628fc1`: findings, check outcomes, entailments, manifest. The states are tagged in the port: `s0` `3690d2a`, `s1` `c062662`, `s2u` `7d7cfa5`, `s2` `fdcf000`. Each manifest names its own content commit, and the four agree with the tags |
| **Finding counts** | Yes | Findings by identity, counted from each state's `findings.tsv`: S0 4,323; S1 3,749; S2u 1,829; S2 1,829, as the message reports |
| **Reproducibility record** | Yes, with one note | Every state's manifest records template commit `a754332`. That is the parent of the `v0.1.0` tag `ee4353d`, which differs from it only in `config/template-manifest.json`'s release label (2 lines). So the checks, shapes and tools measured are v0.1.0's. Each manifest also records the content commit, the distributions, ROBOT and the upstream digests |
| **No unavailable rung counted as zero findings** | Yes, for the accepted measurement | See §1.1 |
| **Template finding dispositions** | Yes | P-A1 to P-A8 and P-B1 (decision 23); P-B2 and the deprecation check, items 1 and 3 (decision 29); the three detection requirements (decision 24), carried as items 7 and 12 |

### 1.1 What was carried to WP6 (decision 13)

The roadmap kept five items open until WP6 closed them. From the team's recorded messages:

| Item | Status | Evidence |
|---|---|---|
| BPO-scale time of the complete Checks job (budget 30 min) | **Met** | 8 min 20 s, green, register filled (run 41106582545). Cold 8 min 41 s, warm 6 min 46 s. Runner `ubuntu-24.04`, image 20261025.353.1. Phase A results §6 |
| BPO-scale time of the Reasoning job | **Met** | 59 s cold, 64 s warm (runs 41073705706, 41076566073). The same section |
| BPO's findings: real, fixed or accepted, each with BPO's reason and owner | **Met, but for K20 and K21** | The classification, K01 to K19 approved by the BPO architect; each S0 finding in exactly one class. K20 and K21: §2, item 4 |
| Whether the template improves the ontology, not only whether its tests pass | **Met** | The four-state comparison and the quality evaluation; the template's reading accepted (decision 27). Improvements in the template are reported apart from BPO's (decision 24) |
| The explorer, rendered in a browser | **Partly met** | All 137 variants of the 51 drifted classes are in the explorer's data, each with its module and a conflict note. The BPO architect inspected it in a browser (the local v0.1.0 build of S1) and found it good, with no screenshots, no per-term checklist and no planted conflict, which is less than the readiness answer committed to. The explorer shows no comments (P-A5) |

### 1.2 Unavailable rungs

A rung is NOT EVALUABLE exactly when an upstream term the merged data references is not
described in scope (`validate.py`, `unresolved_vocabularies` and the rung loop). The
offline vendoring check passes ("every reference resolves") only when every upstream term
the corpus and shapes name is described, and nothing the extracts mention dangles. So in a
state where the vendoring check passed, no rung was blocked.

- In all four accepted states, `vendor_upstream` exited 0 with "every reference resolves"
  (each state's `checks.tsv` at `2628fc1`).
- Every rung that reports findings in S0 reports findings in S2u and S2 (annotation profile,
  realist, wellformedness, naming), except SKOS. SKOS already reported none in S1, after the
  top-concept fix.
- The one invalid measurement, `d446e52`, in which the annotation-profile rung was not
  evaluable, is superseded. The S2u and S2 records at `2628fc1` were last set by `838120e`,
  "S2u and S2 re-measured with all four rungs evaluable".

The defect that made the invalid run possible, P-B2, is in the template's instrument. It is
item 1 of the backlog.

## 2. Conditions

1. Evaluation artefacts: confirmed.
2. Comparison evidence and reproducibility record: confirmed.
3. Template finding dispositions: confirmed.
4. **Not yet confirmed: the BPO classification of the regression.** K20 and K21 (the
   deprecated `SeniorManagementRole`'s missing definition and placement) are still marked
   "PROPOSED, pending the BPO architect" in `classification.md` at `2628fc1` and on the
   port's `wp6` branch. They are BPO's to approve under A6, not the template's. Decision 29
   does not mention them.
   **Met** 2026-11-05: the architect, as BPO's architect, approved them (decision 30). The
   team's `classification.md` still reads PROPOSED; updating it is the team's.
5. **For the architect: the explorer's browser run** (§1.1). Accept it as done, with its
   stated limits, or carry a browser check of a planted conflict into the backlog.
   **Met** 2026-11-05: accepted as done, with its stated limits (decision 30).

## 3. To preserve the results

- The evidence is on the port's `wp6` branch (`2628fc1`), which has diverged from the port's
  `main`, and in the four state tags. A branch can be deleted. We recommend the team tag the
  evidence commit, for example `wp6-final`, and say so in its closing message. That is the
  team's repository and the team's call.
- In this repository: the team's messages are recorded verbatim; the analysis, the verdict
  (decision 27), the disposition (decision 29) and this record are committed.

## 4. After closure

- A7 is lifted, and the template may be released again.
- The backlog is `docs/template/ROADMAP.md`, "After WP6", in decision 29's order. The first
  release after WP6 carries items 1 to 4.
