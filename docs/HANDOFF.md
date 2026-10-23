# Handoff — state of the template

Written 2026-10-23, at the end of roadmap phase 1; §2 and §3 updated at the end of phase 2. It is a snapshot: where this file and a
test disagree, the test is right and this file is stale. In a project made from the
template, init replaces this file with the project's own.

---

## 1. The one-paragraph version

This repository is the ontology template: the Business Capability Ontology's tooling and
method with every project-specific value taken out, so a new BFO/CCO ontology repository
starts with them on its first commit. Its own project is a placeholder called `example`
that exists so every check has something to run against. Phase 1 of
[`docs/template/ROADMAP.md`](template/ROADMAP.md) — extract and generalize — is done; phase 2
is done too, pending its network check on GitHub; phase 3 (the IRI linter) is next. The
repository is published, private and marked as a template, at
https://github.com/Skreen5hot/Ontology-Template.

## 2. What is ready to rely on

- **One project file.** `config/project.yaml`, read by every tool through `tools/project.py`,
  which refuses a malformed or self-contradicting file (`tests/test_project.py`).
- **An uninitialized copy fails CI.** `tools/project.py --check` is the first CI step
  (`tests/test_project.py`).
- **init works on a copy.** `tests/test_init_project.py` initializes throwaway copies and runs
  the copy's own layout, namespace, licensing, project and communications suites in it.
- **Owned files name no project**, and the manifest describes them (`tests/test_template.py`).
- **BFO is vendored whole** — 36 classes, 40 relations, every class reaching *entity*,
  continuant/occurrent disjointness kept — and **CCO by reference**
  (`tests/test_upstream_vendoring.py`).
- **Several files per source**, read as one graph, every url at the pinned commit
  (`tests/test_upstream_vendoring.py`).
- **A register per source** — every term the pinned files describe, with labels, types and
  deprecation; all 1,995 CCO terms, not only the vendored one — generated, licensed as the
  upstream's, digest-checked offline. It is what phase 3's linter will read.
- Everything the BCO's suite asserted about the layout contract, licensing, the SHACL ladder
  and the corpus digest, carried over and generalized.

## 3. What not to trust, and what is not done

- **The template's GitHub slug is fixed in `config/project.yaml`** as
  `Skreen5hot/Ontology-Template` (decision 7). `--check` compares against it, so renaming the
  repository on GitHub without changing that line makes the template refuse itself.
- **The generators are not exercised by the suite in a copy.** init's regeneration needs the
  network or a warm cache. It was run by hand once (§4); a CI job doing it is phase 8.
- **Deprecation is untested on real data.** Neither pinned upstream marks a term
  `owl:deprecated`; the register's flag is exercised on a constructed source only.
- **The CCO extract is a header plus what CCO says about BFO**, because the template names no
  CCO term. Nothing about CCO's hierarchy is exercised until a project names one.
- **No reasoner, no release artefacts, no IRI linter, no realist shapes, no site.** Phases 2–8.

## 4. Evidence outside the suite

Measured 2026-10-23, against the tree as it stands uncommitted (nothing here is committed
yet, so there is no commit to cite):

- **Full init, regeneration included**, in a copy of every tracked and unignored file, with
  BFO and CCO served from a warm `.upstream-cache/` at the pinned digests:
  `--id widget-works --title "Widget Works Ontology" --repository owner/Widget-Works`. All
  three generators ran. In the copy, with `GITHUB_REPOSITORY=owner/Widget-Works`, every CI
  step exited 0 — `project.py --check`, `layout.py`, `disposition.py --check`,
  `vendor_upstream.py`, `vendor_upstream.py --confirm`, `validate.py --gate`,
  `communications.py`, `template_status.py --check` — `template_status.py` reported no
  divergence, and the copy's suite passed, 136 tests. The template's suite is 149; the 13
  not in the copy are `tests/test_init_project.py`, which init removes.
- **Every CI step in the template** exited 0 with `GITHUB_REPOSITORY` set to the template's
  slug, `--confirm` included; set to another slug, `project.py --check` exited 1.
- **Falsification.** Six mutations, each staged-then-restored, each failing the test that
  guards it: an owned tool naming the namespace; the upstream ontology header kept under
  `select: all`; the empty-`select: all` refusal removed; init skipping the shapes; the
  uninitialized-copy refusal removed; owned files selected by path prefix. The fourth first
  passed — init's own leftover check walked the same role list as its rewrite, so both missed
  the shapes — and `leftovers()` was rewritten to scan every non-vendored `.ttl` before it
  failed as it should.

Not covered: `vendor_upstream.py --rebuild` from the network (only from the cache, whose
bytes match the pins); a real "Use this template". CI on GitHub had not run when this was
written; its first run is on the commit that publishes the repository.

## 5. Where to look

| For | Read |
|---|---|
| what the template is and how to use it | `README.md` |
| what comes next | `docs/template/ROADMAP.md` |
| what was decided, by whom | `docs/template/DECISIONS.md` |
| how to run things | `docs/DEVELOPMENT.md` |
| why it is built this way | `docs/process/PROCESS.md` |
