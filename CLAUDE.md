# CLAUDE.md — template grounding

This is the **ontology template**, not an ontology. Its placeholder project is `example`
(`https://fandaws.com/ontology/example#`), which exists so every check has something to run
against. Read `docs/template/ROADMAP.md` for what is built and what is next,
`docs/DEVELOPMENT.md` for how to run things, `docs/process/PROCESS.md` for the method.

## What is true right now

- `config/project.yaml` says `template: true`. `tools/init_project.py` turns a copy into a
  project; never run it in this repository.
- No ontology term exists, and none should: the template ships no terms. The module is an
  `owl:Ontology` header.
- Decisions about the template are in `docs/template/DECISIONS.md`.

## Rules that are easy to break

- **Template-owned files must not name a project.** Components declared `template: owned`
  in `config/repository-layout.yaml` (tools, tests, workflows, PROCESS.md, DEVELOPMENT.md)
  read every project value from `config/project.yaml` through `tools/project.py`. Init
  refuses to write an owned file, so a hardcoded value there would be copied into every
  project unchanged.
- **After changing an owned file**, run `tools/template_status.py --record`. The suite fails
  while the manifest is stale.
- **Anything init rewrites** (the module, the shapes, the fixtures, the skeletons) must keep
  working when `example` becomes another id. `tests/test_init_project.py` runs init in a
  copy and checks.
- **Every tracked file is declared** in the layout contract with a role.
- **A new shape set arrives with its negative fixture** and positive controls in the same
  commit, and its constraint messages are listed by name in a test.
- **Generated files are regenerated, never edited**: `vendor/**`, `vendor/NOTICE.md`,
  `config/upstream-extracts.json`, `config/validation-baseline.json`,
  `config/corpus-digest.json`, `config/template-manifest.json`.
- **Verify before asserting an upstream IRI.** Grep the vendored extract or the cached
  upstream; never write a `cco:`/`obo:` IRI from memory.
- **Line endings are LF.** On Windows, write files as bytes (`write_bytes`).

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
.venv/Scripts/python tools/template_status.py --check
.venv/Scripts/python -m pytest tests/ -q -p no:randomly
```

Commit messages carry the reasoning. Nothing is pushed without the architect's say-so.
