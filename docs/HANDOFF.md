# Handoff — state of the template

Written 2026-10-23, at the end of roadmap phase 1; §2 and §3 updated at the ends of phases 2 to 7. It is a snapshot: where this file and a
test disagree, the test is right and this file is stale. In a project made from the
template, init replaces this file with the project's own.

---

## 1. The one-paragraph version

This repository is the ontology template: the Business Capability Ontology's tooling and
method with every project-specific value taken out, so a new BFO/CCO ontology repository
starts with them on its first commit. Its own project is a placeholder called `example`
that exists so every check has something to run against. Phase 1 of
[`docs/template/ROADMAP.md`](template/ROADMAP.md) — extract and generalize — is done; phase 2
phase 3 (the IRI linter), phase 4 (realist shapes, competency questions, examples) and
phase 5 (reasoning and releases) and phase 6 (authoring aids, vocabulary and governance,
crosswalks) and phase 7 (the public site, built and checked, deployed only when a project
publishes from a private repository without linking into it) are done; phase 8 (the end-to-end proof) is next. The
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
- **A public site**, built twice byte-identical, checked for structure, origins, links,
  fragments and checksums, and refused on an undefined or doubly-labelled term; it builds in
  an initialized copy naming the new project (`tests/test_site.py`,
  `tests/test_init_project.py`).
- **BFO is vendored whole** — 36 classes, 40 relations, every class reaching *entity*,
  continuant/occurrent disjointness kept — and **CCO by reference**
  (`tests/test_upstream_vendoring.py`).
- **Several files per source**, read as one graph, every url at the pinned commit
  (`tests/test_upstream_vendoring.py`).
- **A register per source** — every term the pinned files describe, with labels, types and
  deprecation; all 1,995 CCO terms, not only the vendored one — generated, licensed as the
  upstream's, digest-checked offline. It is what phase 3's linter will read.
- **An IRI linter** (`tools/ontology/iri_lint.py`): readable names with the opaque id
  suggested, unknown ids, wrong-case ids, deprecated and redeclared upstream terms, dangling
  authored references; a parse failure exits 2. Run in CI, by a git hook, and by a Claude Code
  hook after each `.ttl` edit (`tests/test_iri_lint.py`).
- **Realist shapes** (`shapes/realist_shapes.ttl`): anchored in BFO, no two disjoint
  categories -- BFO's `AllDisjointClasses` included, through
  `vendor/bfo/bfo-disjointness.ttl` -- domain and range fit, genus in the definition, one
  asserted parent, complete headers, deprecations with a way forward; and a generated
  annotation profile. Every constraint fires on its named fixture case, and no positive
  control is reported (`tests/test_ontology_checks.py`).
- **Competency questions** over **example instance data**, a right answer passing, a wrong
  one failing, an expectation a query matching nothing would meet refused
  (`tests/test_competency.py`). A fresh project has none, and the tool says so.
- **Reasoning** (`tools/ontology/reason.py`, `.github/workflows/reasoning.yml`): ROBOT
  v1.9.10, pinned by digest, with ELK over the modules plus the full pinned BFO and CCO --
  inconsistency, unsatisfiable classes, and the examples' consistency
  (`tests/test_reasoning.py`, marked `reasoning`).
- **Releases** (`tools/release.py`, `.github/workflows/release.yml`): base and full, in
  three serialisations, byte-identical across hash seeds, each parsed back to its source
  graph (`tests/test_release.py`).
- **Authoring aids**: a Protégé edit file and catalog, loaded offline through the OWL API
  (`tests/test_authoring.py`); opt-in canonical form; issue and PR forms; Dependabot, already
  proposing updates (#2, #3); `CITATION.cff`; `research/`, refusing sources.
- **Vocabulary and governance**: reviewed TSV term intake (`tests/test_vocabulary.py`), SKOS
  concept-scheme shapes, naming conventions, `docs/governance/`, and a term-level diff on
  every pull request and in every release.
- **Crosswalks**: SSSOM mapping sets, checked and kept out of the graph
  (`tests/test_mappings.py`).
- Everything the BCO's suite asserted about the layout contract, licensing, the SHACL ladder
  and the corpus digest, carried over and generalized.

## 3. What not to trust, and what is not done

- **The template's GitHub slug is fixed in `config/project.yaml`** as
  `Skreen5hot/Ontology-Template` (decision 7). `--check` compares against it, so renaming the
  repository on GitHub without changing that line makes the template refuse itself.
- **The generators are not exercised by the suite in a copy.** init's regeneration needs the
  network or a warm cache. It was run by hand once (§4); a CI job doing it is phase 8.
- **No pinned upstream deprecates anything.** Neither CCO v2.0, nor the 2026-04-04 CCO, nor
  BFO 2020 carries `owl:deprecated`, an IAO obsolescence annotation, or an "obsolete" label
  (searched 2026-10-23). The rule is shown to work on a real upstream that does (§4) and
  guards against a future release; the suite exercises it on a constructed source.
- **The CCO extract is a header plus what CCO says about BFO**, because the template names no
  CCO term. Nothing about CCO's hierarchy is exercised until a project names one.
- **The git hook is opt-in** (`git config core.hooksPath .githooks`); the Claude Code hook
  runs for any agent session in the repository, using `python` on the PATH. Both were run for
  real once (§4); neither can run in CI, so a change to either is re-run by hand.
- **The realist shapes check asserted triples, not entailments.** BFO's relations give
  their domains and ranges as unions, which the extract drops, so the domain/range checks
  run only on relations with a named domain or range. A reasoner (phase 5) is what finds an
  unsatisfiable class the triples do not spell out.
- **The Release workflow has not published anything.** It refuses in the template, so its
  first run is a project's first tag.
- **ELK is OWL 2 EL.** Universal restrictions, cardinality and most unions are ignored by it;
  an unsatisfiability that depends on them is not found.
- **Dependabot**: setup-java 6.1.0 (#3) is merged; setup-python 7.1.0 (#2) is held until
  after 2026-11-05. `.github/workflows/dependabot-manifest.yml` re-records the template
  manifest on Dependabot's pull requests; it has been rehearsed locally and has not yet run
  on GitHub. Merging is a person's call.
- **The template's own site is public** at https://skreen5hot.github.io/Ontology-Template/,
  from a private repository, with no link into it (decision 10).
- **No end-to-end proof in CI.** Phase 8.

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

Added after phase 3, 2026-10-23, in scratch clones (nothing in the repository changed):

- **Deprecation on real data.** IAO at commit `3006aedacbf813ffd1d2ac15cda10766ca9ed388`,
  `iao.owl` (sha256 `c27ff2964a2ad8165bc365698b628aae95108411384aa4450e6e1b1e82bf0f41`), has
  24 `owl:deprecated "true"^^xsd:boolean` terms. `register_of` over it flagged exactly those
  24 of 398 — none missed, none extra, against rdflib's own boolean reading — and the
  linter, given that register, reported `deprecated_upstream` for `obo:IAO_0000008` on its
  line and nothing for a live IAO term. IAO is RDF/XML, which the vendoring tool does not
  read; the register builder and the linter were driven directly.
- **The git hook, real commits** (`core.hooksPath .githooks`): a module change writing
  `cco:Organization` was refused (`readable_label cco:Organization -> cco:ont00001180`, HEAD
  unchanged); the same change with `cco:ont00001180` was committed; a docs-only commit did not
  run the linter.
- **The Claude Code hook, a live headless session** (Claude Code 2.1.143, `claude -p`, tools
  Read and Edit): asked to add a class under `cco:Organization`, the agent made two edits;
  after the first (the prefix alone) the hook was silent, and after the second the agent's
  reply quoted the hook's feedback verbatim: `ontology/example.ttl:27 readable_label
  cco:Organization -> cco:ont00001180`.

Not covered: `vendor_upstream.py --rebuild` from the network outside CI (CI's weekly job
does it); a real "Use this template". CI on GitHub had not run when this was
written; its first run is on the commit that publishes the repository.

## 5. Where to look

| For | Read |
|---|---|
| what the template is and how to use it | `README.md` |
| what comes next | `docs/template/ROADMAP.md` |
| what was decided, by whom | `docs/template/DECISIONS.md` |
| how to run things | `docs/DEVELOPMENT.md` |
| why it is built this way | `docs/process/PROCESS.md` |
