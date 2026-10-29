# Ontology Template

A GitHub template for realist ontologies aligned to BFO 2020 and CCO v2.0. Making a new
ontology repository used to mean copying the last one's tools, finding every constant that
named the old project, and re-deriving the pins. This is that setup done once.

It carries the tooling and method of the Application Requirement Ontology and the Business
Capability Ontology, which carried them from BFO-Aligned ValueNet. What it gives a new
project on its first commit:

| What | Where |
|---|---|
| One file with the project's values (id, namespace, prefix, code, repository) | `config/project.yaml` |
| A layout contract that every tracked file must be declared in, with a role | `config/repository-layout.yaml` |
| Licensing: one disposition per file, attribution checked, licensed reference material kept out of the index | `tools/licensing/disposition.py` |
| BFO 2020 (whole) and CCO v2.0 (what is named) vendored from pinned commits, digest-checked, rebuilt weekly | `tools/ontology/vendor_upstream.py` |
| A SHACL ladder gated through a findings register (one entry per accepted finding, by identity), where every shape set must fail on a fixture built to break it | `tools/ontology/validate.py` |
| Realist shapes: anchored in BFO, no two disjoint categories (BFO's `AllDisjointClasses` included), genus-differentia definitions, domains and ranges, headers, deprecations; and a configurable annotation profile | `shapes/realist_shapes.ttl`, `config/annotation-profile.yaml` |
| Competency questions as SPARQL with the answer each must give, over example instance data | `competency-questions/`, `examples/`, `tools/ontology/competency.py` |
| A corpus digest that survives blank-node renaming | `tools/ontology/corpus_digest.py` |
| An IRI linter: every upstream IRI a term of its pinned release, every authored one declared, and an upstream term written by a readable name (`cco:Organization`) answered with the opaque IRI it means -- in CI, a git hook, and a Claude Code hook | `tools/ontology/iri_lint.py` |
| A communications record for other teams, and a decision record for the architect | `communications/`, `docs/decisions/` |
| Protégé: an edit file importing every module and vendored file, with a catalog resolving each offline; canonical Turtle for modules edited there | `protege/`, `tools/ontology/normalize.py` |
| Term-request and defect forms, a pull-request checklist, Dependabot for the pinned actions and Python, a citation file, a research record | `.github/`, `CITATION.cff`, `research/` |
| Term intake as reviewed TSV rows, generated into a module; SKOS concept-scheme shapes; naming and deprecation rules; a term-level diff on every pull request and in every release | `vocabulary/`, `shapes/skos_shapes.ttl`, `docs/governance/`, `tools/ontology/term_diff.py` |
| Crosswalks to other vocabularies as checked SSSOM mapping sets, kept out of the ontology graph | `mappings/`, `tools/ontology/mappings.py` |
| Reasoning: ROBOT and ELK over the modules plus the full pinned BFO and CCO -- consistency, unsatisfiable classes, examples -- in a CI job of its own | `tools/ontology/reason.py`, `.github/workflows/reasoning.yml` |
| Releases on a version tag: base and full, as Turtle, RDF/XML and JSON-LD, byte-identical across builds, with checksums | `tools/release.py`, `.github/workflows/release.yml` |
| A public site: term explorer, modules, concept schemes, competency questions, crosswalks, status, releases and checksummed downloads -- every figure read from the repository, byte-reproducible, checked, deployed to GitHub Pages only when the project says so | `tools/site/`, `site/`, `.github/workflows/pages.yml` |
| CI with actions pinned to commit SHAs | `.github/workflows/checks.yml` |
| The method, and the defects each rule exists because of | `docs/process/PROCESS.md` |

What it does not have yet (an end-to-end proof in CI) is in [`docs/template/ROADMAP.md`](docs/template/ROADMAP.md).

## Starting a project

1. Create the repository from the template and clone it, from the command line:

   ```bash
   gh repo create owner/Widget-Ontology --template Skreen5hot/Ontology-Template --private --clone
   ```

   or on GitHub, **Use this template** → create the new repository, then clone it.
   Porting an existing ontology? Read [`docs/PORTING.md`](docs/PORTING.md) first, and copy
   the form in `docs/porting/` to `research/port-report.md` now: init leaves `research/`
   alone.
2. Set up Python 3.12, the pinned dependencies, and the git hook that runs the IRI linter
   on every commit (git does not turn a repository's hooks on by itself):

   ```bash
   python -m venv .venv && .venv/Scripts/activate      # Windows; source .venv/bin/activate elsewhere
   python -m pip install -r requirements-dev.txt
   git config core.hooksPath .githooks
   ```

3. Initialize, from a clean checkout (`research/` excepted):

   ```bash
   python tools/init_project.py --id widget --title "Widget Ontology" \
       --description "What widgets are, and what they are for." \
       --repository owner/Widget-Ontology
   ```

   This writes `config/project.yaml`, sets the namespace to
   `https://fandaws.com/ontology/widget#` in the module, the shapes and the fixtures,
   renames the module to `ontology/widget.ttl`, renders the project's README, CLAUDE.md and
   HANDOFF, removes the template's own docs, regenerates every generated file (which
   fetches BFO and CCO once), and stages all of it. `--dry-run` shows what it would change.

4. Run the suite, review `git diff --staged`, commit:

   ```bash
   python -m pytest tests/ -q -p no:randomly -m "not reasoning and not scale and not corpus"
   ```

   That is what the Checks workflow runs: 80 s on GitHub's standard runner at the
   template's size (measured 2026-10-28). The tests marked `reasoning` need Java and add
   minutes; `scale` and `corpus` add minutes more, and run in workflows of their own. Every
   figure grows with the ontology.
5. Enable GitHub Pages, before the first push: Settings > Pages > Source: **GitHub
   Actions**, or

   ```bash
   gh api -X POST repos/owner/Widget-Ontology/pages -f build_type=workflow
   ```

   The site is published from the first push to main, even from a private repository, and
   without Pages enabled that push fails at *Configure Pages*. `"publish": false` in
   `site/content/site.json` opts out. Then push. The first push is part of setting up, and
   the rendered CLAUDE.md says so; after it, nothing is pushed without the project owner's
   say-so.

Until step 3 runs, `python tools/project.py --check` — the first step in CI — fails the copy:
it still says it is the template, and every check would be about a placeholder ontology.

## Keeping up with the template

A project keeps `config/template-manifest.json` as it arrived: the digest of every file the
template owns (tools, tests, workflows, PROCESS.md, DEVELOPMENT.md).

```bash
python tools/template_status.py                                # what this project changed
python tools/template_status.py --against ../Ontology-Template # what the template changed since
```

A file in both lists is where an update needs a person. Nothing merges automatically.

## Working on the template itself

The template is an initialized-looking project called `example`, so that every check has
something to run against. Change a template-owned file, then:

```bash
python tools/template_status.py --record
python -m pytest tests/ -q -p no:randomly
```

The suite fails while the manifest is stale.

## Licence

[MIT](LICENSE). The vendored extracts carry their upstream licences: BFO CC BY 4.0, CCO
BSD-3-Clause.
