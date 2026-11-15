# P-A5: comments in the explorer, measured on BPO's ontology

**Date:** 2026-11-15. **Under:** decision 47, which approved the read-only BPO measurement
of index size, comment coverage and conflict visibility. BPO's public repository
(`Skreen5hot/BusinessProcessOntology`, commit `14a1e2c`) was cloned shallowly into a
throwaway directory. Its Turtle was parsed; none of its code was run, and nothing in it
changed (0 files changed after the run). Counts only.

**How.** The template's own `term_records`, from the P-A5 working tree, was run over BPO's
18 ontology modules under `ontology/`, leaving out the shape files, the bad-example fixture
and `ontology/reference/`. BPO's namespace stood in for the project's, with the template's
vendored extracts merged in for categories. The index was built twice: without the
agreement list, as v0.9.0 builds it, and with the template's default list, as P-A5 builds
it. Then the agreement shape's own query was run over the modules' union, for the terms
its target selects, to see what the validator would report.

## What it found

| | Count |
|---|---|
| Modules, authored terms | 18, 3,129 |
| Index size, without and with comments | 2,452,943 and 3,496,904 bytes (+43%) |
| Terms with a comment | 2,576 (82%) |
| Comment values on them | 2,652 |
| Terms whose comments are listed as variants | 53 |
| Comments that are not a literal | 0 |
| Comment notes: values differing across modules | 46 |
| Comment notes: several asserted in one module | 7 |
| Notes that also name a module asserting several among drifted ones | 0 |
| Terms the site notes, and terms the agreement shape reports | 53 and 53, the same terms |

## What it shows

- **Coverage.** Before P-A5, none of BPO's 2,652 comments reached the site. Now every one
  does, on its term, after the definition.
- **Conflicts are visible, and agree with the validator.** 53 terms carry comments that
  differ within a language. The site notes exactly the terms the agreement shape reports,
  no more and no fewer.
- **The safeguard's distinction is real.** 46 of the 53 differ across modules, and 7 have
  several comments asserted in one module. Seven is the number of second, review-added
  comments in one module that WP6 counted as false alarms (results analysis, §3.2). The
  site now says which kind each is. It still notes both, as the shape reports both (decision
  47, 3); row 9's exemption is not built.
- **Size.** The index grows by 43%, about 400 bytes per commented term. Each comment is
  carried once. Only the 53 terms with several values list them as variants, beside a text
  that joins them, as a drifted definition already is. Nothing else is duplicated.

## What it does not show

- **Upstream terms.** None were included, so none of the counts above is an upstream term.
  The template's vendored extracts carry no term comment.
- **A browser.** The explorer's rendering is tested by running the shipped `explorer.js`
  under Node on planted records (`tests/test_term_contract.py`), not on BPO's index.
- **BPO's own site.** This builds the template's index from BPO's modules. It is not BPO's
  site, its build, or its explorer.
- **Whether any comment is right.** The site shows what the validator finds and decides
  nothing about correctness (decision 47).
