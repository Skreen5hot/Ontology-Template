# Handoff — state of the repository

Written {{date}}, when this repository was made from the ontology template. It is a
snapshot: where this file and a test disagree, the test is right and this file is stale.
Rewrite it at each handoff.

---

## 1. The one-paragraph version

{{title}}. {{description}}

**No term has been written.** What exists is the setup to write them under: the layout
contract, licensing classification, pinned upstream vendoring (BFO 2020 whole, CCO v2.0 by
reference), a SHACL gate with falsification fixtures, a corpus digest, CI, and the method in
`docs/process/PROCESS.md`. The module `{{module}}` is an empty header, so every green check
about the ontology is green about nothing — the fixtures are the only evidence the checks
work.

## 2. What is ready to rely on

- **The layout contract describes the tree,** both directions (`tests/test_repository_layout.py`).
- **Every tracked file has exactly one licensing disposition,** and nothing unpublishable
  is tracked (`tests/test_licensing.py`). `docs/Reference/` is declared `tracked: false`
  for licensed material.
- **The vendored extracts are complete for what is named,** carry no blank nodes, attribute
  every triple to the file it came from, and say in their headers that they are partial
  (`tests/test_upstream_vendoring.py`).
- **The wellformedness shapes fire** on the fixture, constraint by constraint, and do not
  fire on the positive controls (`tests/test_ontology_checks.py`), and they target
  `{{namespace}}` (`tests/test_namespace.py`).

## 3. What not to trust, and what is not done

- **The extracts are partial, deliberately.** Every axiom whose object is an anonymous class
  expression is dropped. No reasoner runs here yet, so nothing has checked this ontology
  for consistency or unsatisfiable classes.
- **CCO carries only what is named.** Today that is nothing, so the CCO extract is a header.
  Name a CCO term in a module and the offline check fails until it is rebuilt.
- **Nothing is pushed** until the architect says so.

## 4. Where to look

| For | Read |
|---|---|
| how to run things | `docs/DEVELOPMENT.md` |
| why it is built this way | `docs/process/PROCESS.md` |
| what was decided, by whom | `docs/decisions/` |
| what is vendored, and what is not | `config/upstream-extracts.json`, `vendor/NOTICE.md` |
| how far this has moved from the template | `python tools/template_status.py` |
