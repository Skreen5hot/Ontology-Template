# Item 12: the candidate generators measured on BPO

**Date:** 2026-11-06. **Under:** decision 34, question 4: run the generators locally against
the BPO corpus WP6 evaluated, recording counts and whether each known WP6 defect is raised;
no BPO text in the template or its CI. BPO is the test corpus here, not the subject: every
change below is to the template's general rules.

**Corpus.** BPO's authored modules (shapes, bad-example fixtures and the reference module
left out), read from a fresh clone, at two commits: `bc64e91`, the source of WP6's S0, and
`2b86c91`, the source of S2, after BPO's 39 corrections. Vendored BFO and CCO are the
template's, the same pins. 3,119 authored classes at S0, 3,122 at S2.

**Known defects.** Eleven, taken from the subjects of BPO's correction commits between the
two states, by the rule that should raise each: one over-claiming relation (B8); two
homonyms (B1); three duplicates, one of them an upstream class; five misclassifications.
"Raised" means a candidate of that rule about that term at S0.

## The first run, and what it showed

| | S0 | S2 |
|---|---|---|
| Candidates | 980 | 960 |
| of which misclassification | 908 | 895 |
| Known defects raised | 3 of 10 | 2 |

Too many to answer, and the hits were not detections: two of the three were still raised at
S2, after BPO had fixed them. Read generally, three gaps, none particular to BPO:

1. **Homonyms.** `genus-differs` compared only the genus. The commonest drift keeps the
   genus and changes the meaning: a term copied into several modules and edited in one.
2. **Duplicates.** Only a project's own classes were compared, so a class duplicating an
   upstream one was never listed.
3. **Misclassification.** Any mention of a class from a disjoint category was listed, and
   most mentions say how a thing is related ("used in a process"), not what it is.

## The changes

1. A rule, `definitions-differ`: one IRI with two different definitions under one genus.
   It joins the domain rules (Domain Expert or Proxy Domain Expert), beside
   `genus-differs`; decisions 34 and 35 named the rules before it existed.
2. `near-duplicate` also lists a class whose label is an upstream class's.
3. `category-in-differentia` lists a mention only after a constitution word ("includes",
   "consists of", "made of", "is also" and the like, `config/candidates.yaml`), within six
   words.

Each has a synthetic positive and negative case; mutation testing caught 23 of 23 across
the generators.

## The second run

| Rule | S0 | S2 |
|---|---|---|
| `necessity-without-axiom` | 43 | 44 |
| `genus-differs` | 4 | 0 |
| `definitions-differ` | 47 | 0 |
| `near-duplicate` | 31 | 26 |
| `category-in-differentia` | 6 | 6 |
| **Candidates** | **131** | **76** |

| Kind | Known defects | Raised at S0 |
|---|---|---|
| Over-claiming | 1 | 0 |
| Homonym | 2 | 1 |
| Duplicate | 3 | 1 (the upstream one) |
| Misclassification | 5 | 0 |
| **All** | **11** | **2** |

Both raised defects are gone at S2, where BPO had fixed them. `definitions-differ` falls
from 47 to 0 between the states, which is what BPO's reconciliation of its drifted shared
terms (B1) did; `genus-differs` falls from 4 to 0.

## What this says

- **The queue is answerable.** 131 candidates for 3,119 classes, against 980 before.
- **Drift is found.** The rules for one IRI meaning two things track BPO's own correction
  of them, state to state.
- **Recall on the named defects is low: 2 of 11.** The over-claiming relation and the
  misclassifications were not raised. Over-claiming in BPO lay in how a relation was named
  and axiomatized, which wording alone does not show; item 4's realization warning is the
  check for its commonest form. The misclassifications were stated in definitions without
  a constitution word, or in parents alone. These remain a reviewer's to find, and the
  template should not say otherwise.
- **The sample is small.** Eleven defects in one corpus; the figures describe BPO, not
  ontologies in general.

The measurement was run once per change, as agreed; the rules were not tuned further to
BPO's wording.
