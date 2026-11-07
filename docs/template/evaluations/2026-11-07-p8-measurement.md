# P8: the rights check measured on BCO

**Date:** 2026-11-07. **Under:** decision 40, which approved the read-only measurement of
the design's section 6: BCO's rights record, mapped in memory to the template's schema and
checked with `tools/rights.py`. BCO's repository was read, not modified (its working tree,
and the record's SHA-256, were the same before and after the run), no URL was fetched, and
none of BCO's content is recorded here: counts only.

**How BCO's record was mapped.** Each of BCO's source entries became one review: its
register id, rightsholder, work, edition, status, terms, open questions and gap reason, as
recorded. Evidence by its kind: BCO's `url` items as `url`; its one item from a BPO
commit as `repository`; its two `browser-text` items, read in a browser and their rendered
text digested, as `manual`, with their digest kept, so the check could say what it makes
of one; and its three unpinned observations as `manual` items without a digest. BCO
records the decision on each source, not on each use, so each became one use with that
decision as its release and nothing else. BCO records its reviewer once for the whole
record, so no review names one. The check ran with the template's defaults: a release
names `docs/decisions/*.md`, and the architect releases.

## What it found

| | Count |
|---|---|
| Reviews read | 4 |
| Statuses | 3 evidence-complete, 1 gap |
| Terms | 2 ambiguous, 1 not-established, 1 unambiguous |
| Evidence items | 76: 70 url and 1 repository, pinned by digest; 5 manual, not digest-verified |
| Reviews resting on manual evidence only | 1 |
| Reviews naming a decision record | 4, each of which exists |
| Of those, decision records citing the review's register id | 0 |
| Decisions BCO records as superseded | 2 |
| Quotes | 9, the longest 15 words; the template's limit is unset |
| Findings | 22 |

The 22 findings, by kind:

| Finding | Count | What it is |
|---|---|---|
| A use says nothing of what it is for | 4 | BCO decides per source; P8 asks for each intended use (safeguard 1) |
| A use lists no modules | 4 | The same: a use's scope is the modules it covers |
| A release names no one, `<name> (<kind>)` | 4 | BCO's decision record is the architect's, but the record does not say so per release |
| A review names no reviewer | 4 | BCO names its reviewer once, for the record |
| A release's decision does not cite the source's register id | 4 | BCO's decisions name the material, not the register id |
| A manual item carries a digest | 2 | BCO's `browser-text` items digest the rendered text, not the source's bytes (safeguard 2) |

With `required_from` set to the day P8 is adopted (2026-11-07), the four decisions not citing
the register id are taken before it and stand as written (safeguard 4): 18 findings, every
one of them a field BCO's record does not have, none a decision reopened.

## What it shows

- **The edition rule came from here.** BCO reviews two editions of one work under one
  register id. The design's "one review per register source" refused that as a source
  reviewed twice, against safeguard 1, which asks that each assessment name its edition.
  The check now takes a review as one source and one edition: the same edition twice is
  refused, and a declaration's text is held to the review of its own release.
- **The digests hold up.** Every one of BCO's 71 digested items, apart from the two read in
  a browser, is a url or a file at a commit, and every digest is well formed. P8's evidence
  rules cost BCO nothing there.
- **Manual evidence is reported apart.** BCO's two browser-read items have a digest, but of
  text as a browser rendered it, which no one can refetch to compare. Under safeguard 2,
  P8 refuses a digest on a manual item. The bytes would be pinned as `repository`
  evidence, a copy kept at a commit; otherwise the digest goes, and the item is counted as
  manual.
- **What BCO would add to adopt it.** A reviewer on each review, and each decision split
  into the uses it released, with the modules each covers and who released it. The terms,
  statuses, evidence and decisions are already there.

It does not show that BCO's assessments or decisions are right: the check reads what the
record says, not what the sources permit.
