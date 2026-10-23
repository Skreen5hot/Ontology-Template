# CLAUDE.md — project grounding

{{title}}: a realist ontology aligned to BFO 2020 / CCO v2.0. Read `docs/HANDOFF.md` for
the state, `docs/DEVELOPMENT.md` for how to run things, `docs/process/PROCESS.md` for the
method.

## Rules that are easy to break

- **Namespace.** Author terms in `{{namespace}}` (prefix `{{prefix}}:`) with readable local
  names. The value lives in `config/project.yaml`; the SPARQL in `shapes/` repeats it and
  `tests/test_namespace.py` holds the two together. Change it with both in one commit.
- **Upstream terms are referenced, never redeclared, and never written from memory.**
  BFO is `obo:BFO_*`, CCO is `cco:ont*` — opaque ids, not readable names. Grep the vendored
  register (`vendor/<id>/<id>-register.json`, every term with its label) before using one.
  `tools/ontology/iri_lint.py` checks every IRI, and a hook runs it after each `.ttl` edit:
  a `readable_label` finding names the real IRI after `->`.
- **Every tracked file is declared** in `config/repository-layout.yaml` with a role. A new
  file without a declaration fails the suite.
- **A new shape set arrives with its negative fixture** and positive controls in the same
  commit, and its constraint messages are listed by name in a test.
- **Generated files are regenerated, never edited**: `vendor/**`, `vendor/NOTICE.md`,
  `config/upstream-extracts.json`, `config/validation-baseline.json`,
  `config/corpus-digest.json`. Each names its generator in the layout contract.
  `config/template-manifest.json` is the record of the template this was made from; leave it.
- **Decisions are the architect's.** Record an act verbatim in `docs/decisions/` with the
  digest of what it is about; never perform one.
- **Line endings are LF** (`.gitattributes`). On Windows, write files as bytes
  (`write_bytes`), not `write_text`, which writes CRLF.
- **Communications with other teams** go in `communications/<team>/{incoming,outgoing}/`
  under `communications/README.md`. A committed message is never edited.

## Before committing

```bash
.venv/Scripts/python tools/project.py --check
.venv/Scripts/python tools/layout.py
.venv/Scripts/python tools/licensing/disposition.py --check
.venv/Scripts/python tools/ontology/vendor_upstream.py
.venv/Scripts/python tools/ontology/validate.py --gate
.venv/Scripts/python tools/ontology/iri_lint.py
.venv/Scripts/python tools/ontology/competency.py
.venv/Scripts/python tools/ontology/reason.py        # needs Java; the Reasoning workflow runs it too
.venv/Scripts/python tools/communications.py
.venv/Scripts/python -m pytest tests/ -q -p no:randomly
```

If the ontology changed: `tools/ontology/corpus_digest.py -o config/corpus-digest.json`, and
`tools/ontology/validate.py --record` if a finding was fixed. Commit messages carry the
reasoning — what was wrong, why the fix is the fix, what was measured, what is not covered.
Nothing is pushed without the architect's say-so.
