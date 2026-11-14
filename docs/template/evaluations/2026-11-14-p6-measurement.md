# P6: conceptual-model reference coverage, measured on BCO's CM-01

**Date:** 2026-11-14. **Under:** decision 42, decision 8, which approved this read-only
measurement and asked that it be called what it is. This is **conceptual-model reference
coverage**: whether `tools/fidelity.py`'s anchor rules find the intended elements of a real
approved model, and handle recurring and qualified anchors. It is **not a measurement of
conceptual fidelity**. BCO has no substantive Stage 05 OWL yet, so no element is traced
to a formal term, and nothing here says whether a formalization would be faithful.

BCO's repository was read, not modified. Its HEAD, its working tree status and CM-01's
SHA-256 (`292c8f36d64075b9…`, the model as approved, unchanged since the design was
written) were the same before and after the run. None of BCO's content is recorded here:
counts only.

**How it was run.** The anchor rules were applied in memory to
`src/02_conceptual_models/CM-01-business-capability.md`, with one `cover` pattern per
element kind of decision 42's inventory. Each selected element was given the reference
the tool prints for it, and that reference was resolved back. Nothing was written to BCO,
and no `config/fidelity.yaml` was made for it.

| Element kind | `cover` pattern | Selected |
|---|---|---|
| Patterns | `heading:§3/P*` | 5 |
| Concepts | `heading:§4/*` | 33 |
| Relationships | `row:§5/RL-*` | 39 |
| Decision points | `heading:§7/DP-*` | 2 |
| Boundary-section rows | `row:§6/*` | 22 |
| **Total** | | **101** |

The counts are the inventory decision 42 approved: 5, 33, 39, 2 and 22.

## What it found

| | Count |
|---|---|
| Anchors the rules read in CM-01 | 397: 57 headings, 131 table rows, 209 bold list items |
| Selected elements whose printed reference resolves to that element and nothing else | 101 of 101 |
| Of those, needing a qualifier | 0 |
| Selected elements with no unique reference | 0 |
| Anchor names that recur anywhere in the model | 9, over 193 places |
| Of those 193, resolvable once by a qualified reference | 193 |
| Bold list items in §4 the `heading:` kind prefix kept out of the concepts | 189 |
| Two runs over the same file | identical anchors, in the same order |

- **The rules find the intended elements.** Every pattern, concept, relationship, decision
  point and boundary row is one anchor, of the kind expected, under the section expected.
  None needs a qualifier, because each is uniquely named.
- **Recurrence is real, and qualifiers resolve it.** The 9 recurring names are the
  structure of the model: the labels of each concept's bullets, the options sub-heading
  under each decision point, and a question id that appears in two tables. Unqualified,
  each resolves to several places and would be refused. Qualified by the headings that
  enclose it, every one of the 193 resolves once. The design read two recurring anchors;
  counting bold list items as anchors, as decision 42 approved, adds the bullet labels.
- **The kind prefix matters.** Without `heading:`, `§4/*` would also select the 189 bullet
  labels under the concepts. With it, the selection is the 33 concepts.

## Decision 8's trace counts

| | Count |
|---|---|
| Covered elements | 101 |
| Traced | 0 |
| Untraced | 101 |
| Intentionally not formalized | 0 |
| Reviewed as preserving meaning | 0 |
| Associated with approved semantic changes | 0 |

All 101 are untraced because no trace exists: BCO has no Stage 05 module, so there is
nothing to trace to. That is the expected state, not a finding.

## What it does not show

- It does not show conceptual fidelity, or that P6 supports the faithful formalization of a
  substantial real ontology (decision 42, decision 7). The axiom digests, the stale
  reviews, the guards and the holds were exercised on the fixtures of
  `tests/test_fidelity.py`, not on BCO.
- It does not show that the `cover` patterns above are the right selection for BCO. That
  is BCO's architect's choice; these patterns were chosen to reproduce the approved
  inventory.
- It is to be repeated when BCO's first substantive Stage 05 module exists. That run
  records the same five counts against real rows: elements traced, untraced, not
  formalized, preserving, and changed by a decision.
