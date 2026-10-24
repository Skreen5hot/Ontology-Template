# Governance

How a term gets into this ontology, what it must be called, and how it leaves. Each rule
here that a tool can hold is held by one, named beside it; the rest is for reviewers.

| Topic | Document | Held by |
|---|---|---|
| Proposing a term | below | `.github/ISSUE_TEMPLATE/term-request.yml`, `vocabulary/terms.tsv` |
| Naming | [`naming.md`](naming.md) | `config/naming.yaml`, the IRI linter's `naming_convention` |
| Deprecation | [`deprecation.md`](deprecation.md) | `shapes/realist_shapes.ttl` (the deprecated-term shape) |
| What changed | below | `tools/ontology/term_diff.py`: every pull request, every release's `CHANGES.md` |

## Proposing a term

Either open a **term request** (the issue form asks for a label, a definition naming the
parent, the parent, a source and why), or add a **row** to `vocabulary/terms.tsv` with
`status: proposed` in a pull request. A reviewer accepts a row by setting `status:
accepted` and signing `reviewed_by`; only then is it generated into
`ontology/vocabulary.ttl`. A term written straight into a module goes through the same
review, in the pull request that adds it.

A term is accepted when a reviewer can place it: one parent, a BFO category above it, a
definition of the form *a(n) &lt;parent&gt; that …*, a source. The checks enforce the first
three; the source is the annotation profile's (`config/annotation-profile.yaml`).

## What changed

Every pull request gets a comment listing the terms it adds, removes, deprecates or
changes, field by field. Every release ships the same diff against the previous release as
`CHANGES.md`. Nothing is kept by hand: a change log written by people is right until the
first change nobody remembered to write down.
