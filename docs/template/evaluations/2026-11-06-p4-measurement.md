# P4: the source checks measured on BCO

**Date:** 2026-11-06. **Under:** decision 36, section 5: run the template's register check
over BCO's 63-entry register, and the adequacy check over BCO's decision records,
read-only, reporting entries processed, invalid register data, adequate and inadequate
citations and exceptions. BCO's repository was read, not modified (its working tree was
clean after the run), and none of its content is recorded here: counts only.

**How BCO's register was read.** BCO's register predates decision 36's refinements, so it
was mapped in memory before the check: its claims, which have no ids, were numbered by
position (C1, C2, ...), which decision 36 allows for this measurement only; its
`definition` was read as `summary`; its BCO-specific fields (the authority scale, the
URL prefix and suffix) were left out; and the quote limit was set to BCO's 15 words. The
decision files were BCO's `docs/decisions/` and `docs/adr/`.

## The register

| | |
|---|---|
| Entries processed | 63 |
| Claims | 83: V 22, P 15, S 22, K 13, L 11 |
| Invalid register data | 12 findings, all one kind: a V or P claim that does not state its scope |
| Quote keys, quotation marks, placeholders, the 15-word limit, unknown fields | no finding |

The carried part reads BCO's own register. Its one kind of finding is the one decision 36's
refinement B adds: 12 of BCO's 37 V and P claims do not say which part of the primary text
was examined.

## The decisions

| | |
|---|---|
| Decision and ADR files | 43 |
| Files citing a register source | 3 |
| Citations (distinct per file) | 8, all of a whole source |
| Adequate | 7 |
| Inadequate | 1 |
| Unresolved | 0 |
| Mentions | 0 (BCO has no mention convention) |
| Exceptions | 0 recorded in this form |

Under the template's rule, one BCO decision cites a source not read to V or P in every
claim, with no exception recorded. BCO's own practice, from 2026-10-31, is an individually
approved exception; it was not recorded in the register, so the check cannot see it.

## What this says

- **The carried part works on the register it came from**, with one kind of finding, the
  scope a V or P grade now has to state.
- **The new check has little to read in BCO's decision records.** Most of BCO's reliance on
  sources is in its specification and conceptual models, which a BCO configuration would
  name as decision files; three of 43 records cite a source by its register id. The
  adequacy check covers what is cited where it is configured to look, and nothing else:
  a decision that relies on a source without citing it is not seen (decision 36, section 3).
- **Every BCO citation is of a whole source.** Under the template's rule a whole source is
  adequate only if every registered claim is V or P; citing claims would say which part a
  decision rests on.

The figures describe BCO's records on 2026-11-06, not projects in general.
