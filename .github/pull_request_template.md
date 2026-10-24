## What changes, and why

<!-- What was wrong or missing, why this is the fix, what was measured. -->

## Checked

- [ ] `python -m pytest tests/ -q -p no:randomly` passes (with Java, or `-m "not reasoning"` and the Reasoning workflow)
- [ ] New or changed terms: placed under one parent, defined by their genus, `tools/ontology/iri_lint.py` clean
- [ ] A new upstream term: `tools/ontology/vendor_upstream.py --rebuild` in this pull request
- [ ] The ontology changed: `tools/ontology/corpus_digest.py -o config/corpus-digest.json`
- [ ] A new shape set: its negative fixture and positive controls are in this pull request
- [ ] A competency question moved to `answerable`: it passes here

## Not covered

<!-- What this does not do, or does not check. -->
