# Development

How to work in this repository. For *why* it is built this way, read
`docs/process/PROCESS.md`. For what is actually here and what is not, read
`docs/HANDOFF.md` first.

This file is owned by the ontology template (`config/repository-layout.yaml`), so it
describes any project made from it and names none. A project's own conventions go in its
README, its HANDOFF, or a document of its own.

---

## Setup

Python 3.12. Dependencies are pinned exactly, and the pinning is verified the one way it
can be — by installing into an empty environment and running the suite there:

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows;  source .venv/bin/activate elsewhere
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -q -p no:randomly
```

The tests marked `reasoning` need Java 11 or later (they run the pinned ROBOT jar); without
Java they fail, by design, rather than skip. To run everything else, as the Checks workflow
does: `python -m pytest tests/ -q -p no:randomly -m "not reasoning"`.

`tools/` is deliberately not an installed package. It is a directory of scripts that the
tests import by path, so there is no build step between writing a tool and testing the
tool that ships.

---

## The project file

`config/project.yaml` holds the values that make this project this project: `id`, `code`,
`title`, `description`, `namespace`, `prefix`, `iri_base`, `repository`. Every tool reads
them through `tools/project.py`, which refuses a file that contradicts itself (a namespace
that is not `iri_base` plus `#`, for one).

Two places repeat the namespace where no tool can read the project file: the SPARQL targets
in the shapes, and the module headers. `tests/test_namespace.py` requires the shapes to
agree with the project file. To change the namespace, change all three in one commit.

---

## The checks, and what each one actually asserts

Run in this order; each is cheap until the last.

```bash
python tools/project.py --check               # this is a project, not an uninitialized copy
python tools/layout.py                        # the contract describes the tree
python tools/licensing/disposition.py         # one disposition per tracked file
python tools/licensing/disposition.py --check # nothing unpublishable is tracked
python tools/ontology/vendor_upstream.py      # the extracts cover what is named
python tools/ontology/validate.py --gate      # no new ontology findings
python tools/ontology/iri_lint.py             # every IRI is a real term or a declared one
python tools/ontology/competency.py           # every answerable competency question gives its answer
python tools/ontology/profile_shapes.py --check   # the profile shapes are what the profile generates
python tools/ontology/reason.py               # needs Java: consistent, nothing unsatisfiable
python tools/ontology/protege.py --check      # the Protégé edit file and catalog are current
python tools/ontology/vocabulary.py --check   # the vocabulary module is what the intake generates
python tools/ontology/mappings.py             # every SSSOM crosswalk holds
python tools/ontology/term_diff.py --base origin/main   # which terms this branch changes
python tools/ontology/normalize.py --check    # modules declared canonical are canonical
python tools/communications.py                # the communications record follows its protocol
python tools/template_status.py               # where this has diverged from the template
python tools/site/build_site.py && python tools/site/check_site.py   # the public site builds and holds
python -m pytest tests/ -q -p no:randomly     # all of the above, plus the falsifications
```

| Command | What it will refuse |
|---|---|
| `project.py --check` | a copy of the template that still says `template: true` in a repository other than the template's |
| `layout.py` | a declared component whose path does not exist; two components sharing an id; a generated artifact that names no generator and does not admit it has none |
| `disposition.py` | a file matching two rules, or none; an adjudication naming no file; a `LICENSE` naming zero or two recognised licences |
| `disposition.py --check` | a tracked file that may not be redistributed; a vendored extract whose required attribution is missing from `vendor/NOTICE.md` |
| `vendor_upstream.py` | an upstream term the corpus or the shapes name that no extract describes; an extract whose digest is not what the manifest records |
| `validate.py --gate` | a rung with more findings than `config/validation-baseline.json` records, a rung with fewer that has not been re-recorded, a shape set the fixture does not exercise, a rung blocked on missing vocabulary, a violation against a vendored term, and a rung the baseline does not mention |
| `validate.py --record` | raising any recorded count without `--accept-regression "<why>"`. Lowering is always free |
| `iri_lint.py` | an upstream IRI its pinned release does not have (`unverified`), a readable name where the upstream mints ids (`readable_label`, with the id suggested), an id in the wrong case (`case_mismatch`), a deprecated upstream term, an authored file typing an upstream term (`redeclared_upstream`), an authored IRI nothing declares (`dangling_ref`); and, as exit 2, a file it cannot read or parse |
| `competency.py` | an answerable question whose query gives a different answer, or none where rows were expected; an expectation nothing can fail (`rows: []`, `count: 0`, `ask: false`); a question depending on a term nobody defines; an example file that does not exist or lies outside `examples/` |
| `profile_shapes.py --check` | `shapes/annotation_profile_shapes.ttl` differing from what `config/annotation-profile.yaml` generates; a profile property no pinned upstream or W3C vocabulary defines |
| `reason.py` | an unsatisfiable authored class; an ontology with no model; example individuals inconsistent with it; and, as exit 2, no Java, a ROBOT jar that is not the pinned one, or an answer from ROBOT it cannot read |
| `mappings.py` | a mapping set without a set id, licence, creator or semapv prefix; a subject no module declares; an object outside the set's namespaces, in this project's, or in BFO's or CCO's; a predicate that is not a SKOS mapping property or `owl:equivalentClass`; an exact match or equivalence without a matching `object_type`; a row with no `semapv:` justification, or twice; and, as exit 2, a file that is not SSSOM |
| `vocabulary.py --check` | `ontology/vocabulary.ttl` differing from what `vocabulary/terms.tsv` generates; an intake row with a bad status, an accepted row unsigned or unplaced, a local name off the class convention or used twice or already declared, a parent with no known prefix |
| `protege.py --check` | `protege/edit.ttl` or its catalog differing from what the modules and the vendored files generate; a module with no ontology header, or two |
| `normalize.py --check` | a module declared `format: canonical` that is not in canonical Turtle |
| `release.py` | a version that is not MAJOR.MINOR.PATCH; a file that does not parse back to the graph it was written from |
| `template_status.py --check` | in the template only: a manifest that does not describe the owned files. A project's divergence is reported, never refused |

`validate.py` writes a report with `-o config/validation-report.json`. That file is
gitignored on purpose: it is a measurement, not a pin. `config/corpus-digest.json` **is**
committed, because a test compares it against a fresh measure — regenerate it in the commit
that changes the ontology:

```bash
python tools/ontology/corpus_digest.py -o config/corpus-digest.json
```

---

## Writing a term

Authored terms live in the project namespace with readable local names
(`<prefix>:MaintenanceAct`). Upstream terms are referenced by their own IRIs, which for BFO
and CCO are opaque: `obo:BFO_0000015` is *process* and `cco:ont00001180` is
*organization*, and neither is a name anybody should type from memory.

1. **Find the upstream parent in the pinned file, not in memory.** Grep
   `vendor/cco/cco-extract.ttl`; if the term is not there, grep the cached upstream
   (`.upstream-cache/cco.ttl`, present after any rebuild) for its label.
2. **Write the term** in a module: `rdfs:label`, `skos:definition`, and `rdfs:subClassOf`
   its parent.
3. **In the same commit:**

   ```bash
   python tools/ontology/vendor_upstream.py --rebuild     # it names a new upstream term
   python tools/ontology/validate.py --gate               # the shapes now have a subject
   python tools/ontology/corpus_digest.py -o config/corpus-digest.json
   python -m pytest tests/ -q -p no:randomly
   ```

The offline vendoring check fails between steps 2 and 3, naming the term. That failure is
the point: it is the moment somebody looks at what the new reference is.

---

## The IRI linter

```bash
python tools/ontology/iri_lint.py                  # the modules and the shapes, as one corpus
python tools/ontology/iri_lint.py a.ttl b.ttl      # these files
python tools/ontology/iri_lint.py --output json
```

It checks every upstream IRI against its source's register — every term the pinned release
describes, not only what is vendored — and every IRI in the project namespace against the
declarations in the files linted together. A finding names the file and line of each
occurrence:

```text
ontology/widget.ttl:14 readable_label cco:Organization -> cco:ont00001180
ontology/widget.ttl:22 readable_label cco:Process -> obo:BFO_0000015
ontology/widget.ttl:30 unverified cco:ont99999999
```

Exit 0 is clean, 1 is findings, 2 is "could not lint" — a file that does not parse is never a
file with no findings. The rules and the JSON shape are IRI_Linter's; why the code is not is
in the tool's docstring.

**Two hooks run it before CI does.** For agents, `.claude/settings.json` runs it after every
Write or Edit of a `.ttl` and hands findings back to the agent on the edit that caused them.
For people, a git pre-commit hook, enabled once per clone:

```bash
git config core.hooksPath .githooks
```

---

## Adding a file

Every tracked file must be declared in `config/repository-layout.yaml`. An undeclared file
fails the suite in both directions: it has no stated role, and a declared component whose
path is missing is a contract describing something that is not there.

```yaml
  - id: ontology.events                # stable; queries and tests reference the id, not the path
    path: ontology/events.ttl
    role: ontology-module
    description: >-
      What it is, and anything a reader would otherwise have to reconstruct.
```

Roles are not labels — each carries a consequence, and the set of known roles is read from
the licensing tool so the two cannot drift:

| Role | Means |
|---|---|
| `ontology-module`, `ontology-module-set` | authored ontology; in the validation data graph and the corpus digest |
| `ontology-validation` | SHACL shapes; **not** in the data graph |
| `test-fixture` | expected to be invalid on purpose; must never be loaded as ontology |
| `generated-artifact` | derived; must name a `generator`, or declare itself `orphaned` with the reason |
| `specification` | a design document; read by the vendoring tool for the upstream terms it names |
| `historical-draft` | preserved as imported; never loaded |
| `vendored-ontology` | somebody else's, redistributed under their licence, attribution required |
| `vendored-register` | the list of every term a pinned upstream describes; its labels, so its licence; JSON, never loaded as ontology |
| `third-party-reference` | somebody else's, **not** redistributable |
| `site-source` | a public site's pages, copy and assets |
| `example-data` | instance data the competency questions are answered against; linted, never in the digest or the ladder |
| `competency-question` | one YAML file per question, run by `tools/ontology/competency.py` |
| `research` | the project's own notes, tables and bibliographies; never a source itself |
| `vocabulary-intake` | `vocabulary/terms.tsv`, term proposals as rows; accepted rows generate `ontology/vocabulary.ttl` |
| `mapping-set` | SSSOM crosswalks in `mappings/`; checked, never loaded into the ontology graph |
| `communication` | the communications record |
| `documentation`, `configuration`, `tool`, `project-licence` | as they sound |

Three fields worth knowing:

- **`tracked: false`** — the files may exist locally and must never be committed. Stronger
  than `.gitignore`, because an already-tracked file stays tracked. This is what stands
  between `docs/Reference/` and publishing a licensed standard.
- **`generator:` / `orphaned:`** — exactly one is required of a `generated-artifact`.
- **`template:`** — `owned` if the template maintains the component, `only` if it describes
  the template and init removes it. A project's own components leave it out.

Adding a new *role* means adding a licensing rule for it in
`tools/licensing/disposition.py`. The test will tell you; do it deliberately rather than
letting a file inherit a guess.

---

## Adding a shape set

**In the same commit, or not at all:** a new shape set arrives with negative fixture cases
that break it, each named for the constraint it targets, plus positive controls that must
survive. Declare the fixture as its own `test-fixture` component; `validate.py` loads every
one the contract declares.

Why both kinds of case: a shape set reporting zero against the corpus is ambiguous on its
own — clean data and a constraint selecting nothing look identical — and a fixture where
everything fails cannot show that a constraint discriminates. In ARO,
`capabilities_roles_shapes.ttl` reported 202 violations while CCO was missing and zero the
moment it was vendored, and nothing distinguished that zero until named fixture cases
existed.

List the new constraint messages by name in a test, as `WELLFORMEDNESS_CONSTRAINTS` in
`tests/test_ontology_checks.py` does. A count would be satisfied by any N violations.

A shape that filters on the project namespace must spell it exactly as
`config/project.yaml` does; `tests/test_namespace.py` checks every `STRSTARTS` in every
shape set.

**Severity belongs to a shape, not to a SPARQL constraint.** pyshacl gives a `sh:sparql`
result the severity of the node shape that holds it, so a warning needs a node shape of its
own (see `rs:AuthoredClassReviewShape`). The gate counts `sh:Violation` results; warnings
are reported beside them and never block.

**Write SPARQL so each property path is in the block that binds its subject.** rdflib
evaluates a group split by a `FILTER` or a `UNION` on its own; a `?x rdfs:subClassOf* ?y`
there runs with `?x` unbound over every node in the graph. Use path alternatives (`|`, `^`)
instead of `UNION`, and put filters last.

---

## The realist shapes

`shapes/realist_shapes.ttl`, over the modules plus the vendored extracts:

| Constraint | Severity |
|---|---|
| every authored class reaches `obo:BFO_0000001` through named `rdfs:subClassOf` | violation |
| no class under two categories declared disjoint — BFO's named pairs, the pairs derived from its `owl:AllDisjointClasses`, CCO's, the project's | violation |
| a restriction's filler not disjoint with the property's range, the restricted class not disjoint with its domain | violation |
| the filler, or the class, not known to fall under that range or domain | warning |
| one asserted named parent | warning |
| the definition names the parent's label (genus–differentia) | warning |
| a deprecated term names `dcterms:isReplacedBy` or a `skos:historyNote` | violation |
| every ontology header under the IRI base has a title, licence, creator, version IRI and version info | violation |

The disjointness the hardest check leans on — independent, specifically dependent and
generically dependent continuant — BFO states only as `owl:AllDisjointClasses`, a blank-node
list the extract drops. `vendor/bfo/bfo-disjointness.ttl` is those axioms written as the
pairwise `owl:disjointWith` they are equivalent to, generated and labelled as derived.

What it cannot see: BFO 2020's relations give their domains and ranges as unions, which
the extract drops, so the domain and range checks run on relations with a named domain or
range — CCO's and yours. These are checks over asserted triples, not reasoning.

**Saying something about an upstream term** — a comment, a label, a parent on `cco:` or
`obo:` IRI — is the IRI linter's `annotated_upstream`, not a shape: a shape sees the merged
graph and cannot tell an authored triple from a vendored one.

## The annotation profile

`config/annotation-profile.yaml` lists what every authored class must carry beyond a label
and a definition — by default CCO's *definition source* (`cco:ont00001754`), as a warning.
Edit the YAML and regenerate; never the shapes:

```bash
python tools/ontology/profile_shapes.py
```

## Competency questions and examples

What the ontology must be able to answer, as SPARQL with the answer it must give — one YAML
file per question in `competency-questions/` (format in its README) — answered against the
modules, the vendored extracts, and the instance files in `examples/` the question names.

```bash
python tools/ontology/competency.py           # run every answerable question
python tools/ontology/competency.py --list    # every question and its status
```

Only `status: answerable` runs. An expectation a query matching nothing would meet —
`rows: []`, `count: 0`, `ask: false` — is refused, not passed. Example individuals live in
`<iri_base>/examples/` (`eg:` in queries), never in the ontology's namespace; the IRI linter
checks their types like any module's.

---

## Working with the vendored upstream

BFO and CCO are pinned partial extracts, not `owl:imports`. Nothing resolves over the
network at validation time.

```bash
python tools/ontology/vendor_upstream.py            # offline verify — runs in CI
python tools/ontology/vendor_upstream.py --confirm  # fetch and require byte-identity
python tools/ontology/vendor_upstream.py --rebuild  # fetch and rewrite
```

| id | pin | selected | register |
|---|---|---|---|
| `bfo` | release-2024-01-29 | `all`: every term `bfo-core.ttl` describes | `vendor/bfo/bfo-register.json` |
| `cco` | v2.0-2024-11-06 | `named`: the terms this repository names, plus their ancestry | `vendor/cco/cco-register.json` |

**Each source has a register** beside its extract: every term its pinned files describe in its
namespace — all of CCO, not only what is vendored — with labels, OWL types and deprecation. It
answers "is there such a term, and what is it called", which the extract cannot for a term
nothing here names yet. To find the opaque IRI for a readable name:

```bash
python -c "import json; t=json.load(open('vendor/cco/cco-register.json',encoding='utf-8'))['terms']; print([i for i,r in t.items() if any(l['value']=='Organization' for l in r['labels'])])"
```

The register is the upstream's labels, so it is licensed as the upstream is (role
`vendored-register`), generated, and digest-checked offline like the extract.

**A source may be several files** at one commit: `files:` with a `url` and `sha256` each,
instead of a single `url` and `sha256`. They are read as one graph. Every url must name the
commit.

**Seeds** come from the authored modules and the shapes — including terms named only inside
SPARQL text — and from any component with the role `specification`. A specification term no
pinned file describes is recorded in `config/upstream-extracts.json` rather than refused.

**A sister ontology** (one this project builds on, such as the Business Process Ontology) is
another entry in `config/upstream-sources.yaml`: url(s) at a commit, sha256, namespace,
prefix, extract and register paths, licence. If its Turtle states no licence, name its LICENSE
file at the same commit as `statement_url` with a `statement_sha256`. The end of that file
carries a worked entry, commented out: the BPO pin the Business Capability Ontology uses.
Declare the extract as a `vendored-ontology` and the register as a `vendored-register` in the
layout contract, then `--rebuild`.

**What the extracts leave out:** every axiom whose object is an anonymous class
expression. That is recorded in each file's header and in `config/upstream-extracts.json`,
and it means these files cannot support a consistency claim against the upstream.

**A triple is written into the extract of the file that asserts it**, not the extract whose
namespace its subject is in. CCO's merged file annotates BFO terms; those annotations are
CCO's, under CCO's licence.

Downloads cache in `.upstream-cache/` (gitignored). The weekly CI job re-fetches and
requires the committed extracts to be byte-identical.

---

## The template

`config/template-manifest.json` is the digest of every template-owned file as the template
shipped it. In a project it is never rewritten: it is the record of what the project was
made from.

```bash
python tools/template_status.py                                 # what this project changed
python tools/template_status.py --against ../Ontology-Template  # what the template changed since
```

---

## Editing in Protégé

Open `protege/edit.ttl`. It imports every module and every vendored file, and
`protege/catalog-v001.xml` beside it maps each import to the local file, so Protégé loads
BFO and CCO beneath your classes without fetching anything, and saves an edit into the
module the axiom belongs to. Both files are generated; after adding a module or
re-vendoring, regenerate them:

```bash
python tools/ontology/protege.py
```

Protégé rewrites a module in its own Turtle on save, and drops its comments. For a module
you edit only in Protégé, declare `format: canonical` on it in the layout contract and run
`python tools/ontology/normalize.py` after saving: the module is then always in one form,
and a diff shows the axioms that changed rather than every line Protégé reordered. A module
written by hand, with its reasoning in comments, should not be canonical.

## Proposing terms as rows

`vocabulary/terms.tsv` is the intake for people who do not write Turtle: one row per term
— `local_name`, `label`, `definition`, `parent`, `synonyms`, `status`, `requested_by`,
`reviewed_by`, `notes`, and one column per annotation in the profile (`definition_source`
by default). A row is a proposal until a reviewer sets `status` to `accepted` and signs
`reviewed_by` in the pull request; then

```bash
python tools/ontology/vocabulary.py
```

generates `ontology/vocabulary.ttl`, an ordinary module every check reads. Whether the
parent exists is the IRI linter's question, asked of the generated module; a new CCO parent
needs `vendor_upstream.py --rebuild` like any other.

## Concept schemes

A vocabulary about terms — a catalogue, a code list, a taxonomy of business usage — is a
SKOS concept scheme, in a module of its own. `shapes/skos_shapes.ttl` holds its structure:
every concept in a declared scheme, no `skos:broader` cycle, no `broader` across schemes, no
`altLabel` or `hiddenLabel` repeating the `prefLabel`, a top concept in every scheme, and no
concept that is also an `owl:Class`. The scheme sits beside the class hierarchy; no class is
made from a concept.

## Crosswalks

Mappings from this ontology's terms to other vocabularies live in `mappings/`, one SSSOM
set per target (format in its README), checked by `python tools/ontology/mappings.py`. A
term related to BFO or CCO is not a mapping: it is placed under the upstream term, or is
it. Mappings are never loaded into the ontology graph, so an `exactMatch` to a vocabulary
that is not BFO-aligned never becomes a claim about this ontology's types.

## Naming, deprecation, and what changed

`docs/governance/` holds the policy, each rule beside the check that holds it. Local names
follow `config/naming.yaml` (the linter's `naming_convention`); a deprecated term names a
replacement or a reason (the realist deprecated-term shape).
`tools/ontology/term_diff.py` reports the terms added, removed, deprecated or changed
between two commits — the Term diff workflow comments it on every pull request, and the
Release workflow ships it as `CHANGES.md`, inside the checksums.

## Requests, reviews and records

- **Term requests** come in through the issue form (`.github/ISSUE_TEMPLATE/term-request.yml`),
  which asks for what placing a term needs: a label, a definition naming its parent, the
  parent, a source, and why.
- **Pull requests** carry a checklist (`.github/pull_request_template.md`) of the checks a
  change of each kind needs.
- **Dependabot** proposes updates to the SHA-pinned actions and the exact Python pins as
  pull requests; each runs the checks and is merged by a person. It does not touch the
  ontology or ROBOT pins, which move by decision. In the template, where those files are
  template-owned, `.github/workflows/dependabot-manifest.yml` re-records
  `config/template-manifest.json` on a Dependabot pull request -- that file and nothing
  else -- and re-runs Checks and Reasoning on the result, so the pull request is judged on
  what the update does. It approves and merges nothing.
- **`research/`** is the project's own notes. Sources go in `docs/Reference/`, never
  tracked; `disposition.py --check` refuses anything in `research/` that is not a note,
  table or bibliography, and any file that is a byte copy of reference material.
- **`CITATION.cff`** says how to cite the ontology; init writes the project's.

---

## Reasoning

```bash
python tools/ontology/reason.py               # needs Java 11+
```

ROBOT (pinned in `config/reasoning.yaml`, downloaded into `.tool-cache/` and checked against
its sha256) runs ELK over the authored modules plus the **full** pinned BFO and CCO files —
not the extracts, which drop every anonymous class expression and so could not support a
consistency claim. It reports an inconsistent ontology and every unsatisfiable class, then,
in a second pass, whether the `examples/` are consistent with it. Upstream unsatisfiable
classes, if a re-pin ever brought any, are reported apart from authored ones.

ELK is complete for OWL 2 EL: subclass, existential restriction, intersection,
disjointness. It ignores universal restrictions, cardinality and most unions; HermiT
(`reasoner: hermit`) covers OWL 2 DL and is far slower over CCO.

The Reasoning workflow runs this and the `reasoning` tests on every push. The Checks
workflow deselects those tests by marker — named in its command line, not skipped.

## Releasing

Tag the commit: `git tag v1.2.0 && git push origin v1.2.0`. The Release workflow runs every
check and the reasoner on the tagged commit, builds the artefacts twice with different hash
seeds, requires them byte-identical, and publishes a GitHub release:

| File | What |
|---|---|
| `<id>-base.{ttl,owl,jsonld}` | the authored terms, every module merged, under one header |
| `<id>-full.{ttl,owl,jsonld}` | the base plus the vendored extracts and BFO's derived disjointness; the upstream part is partial, and the header says so |
| `NOTICE.md`, `LICENSE`, `SHA256SUMS` | attribution for the vendored part, this project's licence, checksums |

The header's ontology IRI is `<iri_base>/<id>-base` (or `-full`), the version IRI
`<iri_base>/<version>/<id>-base`, `owl:versionInfo` the version; title, licence and creator
come from the main module's header. To build locally: `python tools/release.py --version
1.2.0` (into `dist/`, gitignored). RDF/XML and JSON-LD are written by the tool, flat and
sorted, because rdflib's writers for both are not deterministic across processes.

---

## The public site

`python tools/site/build_site.py` builds it into `_site/` (gitignored); `python
tools/site/check_site.py` checks what was built. To look at it locally, serve the
directory, not the files -- every link is relative, and a browser opening `index.html` from
disk will not run the explorer's scripts: `python -m http.server -d _site 8000`.

| Page | Read from |
|---|---|
| Home, Status | the project file, the term counts, the validation baseline, the lint and competency results, `docs/decisions/`, the latest `v*` tag |
| Explore | every authored term and every upstream term, as `data/terms.json`; category from the `rdfs:subClassOf` chain, never a name |
| Modules, Downloads | the modules, the shape sets, the pins and the extracts, with checksums; a byte-reproducible bundle of the authored files |
| Vocabulary | each authored `skos:ConceptScheme`, as a tree |
| Competency | each question, its query, and its verdict at this commit |
| Crosswalks | each SSSOM mapping set |
| Releases | the `v*` tags reachable from the built commit |
| Specification, Review | only when a component with role `specification` or `review` is declared; otherwise left out of the navigation |

`site/content/site.json` holds only what a person chooses -- the tagline, the navigation
labels, the reviewer guidance, the notices -- and no figure the build can read. The
fragments in `site/pages/` and the assets in `site/src/` are the template's.

**What the build refuses**: an authored term with no label or definition, or two in one
language; a class reaching two unrelated BFO categories; a placeholder nothing fills; a page
fragment no navigation entry names; an asset that is not `.css` or `.js`; and a source file
with CRLF line endings, because the downloads are those bytes and would differ from CI's.
**What the checker refuses**: a page without its structure (lang, one title, one `<h1>`,
`<main id="main">`), a resource from another origin, an inline script or `on*` handler, a
root-absolute or unresolved link or fragment, and a download or bundle that does not match
its checksums.

**Publishing.** The ontology is public; how it was made need not be. The Pages workflow
builds, checks and proves the build reproducible on every push and pull request (pull
requests get the site as a preview artifact), and on main deploys it when
`site/content/site.json` says `"publish": true` -- which it does from the first commit. **A
Pages site is public even when the repository is private**, which is the point: the
repository can stay private and the ontology still be published.

1. Settings > Pages > Build and deployment > Source: **GitHub Actions** -- or `gh api -X
   POST repos/<owner>/<repository>/pages -f build_type=workflow`. Until this is done, the
   first push to main fails at *Configure Pages*, saying Pages is not enabled. (For a
   private repository, Pages needs a plan that allows it.)
2. Decide the notices in `site.json`: `draft.show`, and `iri_resolution.resolve` once the
   namespace actually resolves. If the repository is private, set `contact` (an address or
   an https URL) so a reader has somewhere to send a finding.
3. The site is at `https://<owner>.github.io/<repository>/`.

**A private repository is never linked.** The workflow tells the build the repository's
visibility (`SITE_REPOSITORY_PRIVATE`, from the event). For a private one, the site shows
source paths and the commit as text and releases as tags, and offers the `contact` instead
of the issues; the checker refuses any link into the repository. A local build assumes
private; `SITE_REPOSITORY_PRIVATE=false` builds the public form. The release artefacts on a
private repository's GitHub releases are private too; the site's downloads are the public
copy of the authored files.

A project that will not publish sets `"publish": false`; the site is still built and
checked on every run.

---

## The ontology-pipeline layers, and where each lives here

For someone who knows the layered pipeline associated with Jessica Talisman — controlled
vocabulary, metadata schemas, taxonomy, thesaurus, ontology, knowledge graph. The layers
coexist here rather than as numbered stages: in a realist ontology the `rdfs:subClassOf`
tree under BFO is the classification of types, and a SKOS scheme is a vocabulary about
terms, kept beside it rather than upstream of it. The reasoning, layer by layer, is in the
template's roadmap.

| Layer | Here |
|---|---|
| controlled vocabulary | the vocabulary intake, `vocabulary/terms.tsv` |
| metadata schemas | SHACL in `shapes/`: wellformedness, the realist library, the annotation profile |
| taxonomy | SKOS concept-scheme modules, held by `shapes/skos_shapes.ttl`; the OWL hierarchy is the ontology's own |
| thesaurus | SKOS labels in concept schemes; SSSOM crosswalks in `mappings/` |
| ontology | `ontology/`, with BFO and CCO vendored and pinned |
| knowledge graph | `examples/` and `competency-questions/`; data-lifting pipelines belong in an application repository |

---

## Conventions

### Paying down a finding

Findings are recorded per shape set in `config/validation-baseline.json`, and the gate
requires the file to describe reality — *more* is a regression, *fewer* means re-record so
the reduction shows up in a diff:

```bash
python tools/ontology/validate.py --record     # after fixing something
```

`--record` refuses to raise a count without `--accept-regression "<why>"`, and writes the
reason beside the number it excuses.

### Recording a decision

The architect's acts go in `docs/decisions/YYYY-MM-DD-<slug>.md`: the act verbatim, who and
when, the digest or commit of what it is about (recomputed from the committed file before
recording), and its effect. See `docs/decisions/README.md`. An agent may record an act; it
never performs one.

### The rest

**Falsify every check.** A passing test is not evidence. Evidence is a passing test plus a
demonstration that it can fail: revert the fix, require *that specific* check to fail,
restore, confirm.

**And verify the mutation moved what is measured.** A changed file digest is not enough.
Assert the number you expect to move has moved, *then* run the check.

**Stage before you mutate.** `git checkout --` restores from the index; unstaged work is
destroyed.

**Commit messages carry the reasoning, not the diff.** What was wrong, why the fix is the
fix, what was measured, and what is still not covered.

**Say what was not done.** Every record states its own limits.

**Line endings are content.** `.gitattributes` pins LF repository-wide. A CRLF inside a
`skos:definition` is part of that literal's value.

**Derive, never transcribe.** Paths come from the layout contract. Project values come from
`config/project.yaml`. Licences are read from `LICENSE` and from the upstream artifact.
Upstream namespaces are read from the pins. Counts are measured.

---

## Traps

None of them announces itself.

- **`| head` and `| tail` mask exit codes.** The pipeline exits with the *last* command's
  status.
- **`text=True` in `subprocess` decodes as cp1252 on Windows**, which corrupts multi-byte
  sequences and then blames the file. Decode explicitly as UTF-8.
- **rdflib renames blank nodes on every parse.** Compare ground triples plus a blank-node
  *shape* digest — `tools/ontology/corpus_digest.py` is the worked version.
- **`all()` over an empty sequence is `True`.** `validate.passed_of` is the guard.
- **Scanning file text finds the comment explaining the rule.** Parse and check terms.
- **A green shape set is ambiguous on its own.** Clean data and a constraint selecting
  nothing look identical — and with an empty corpus, every shape set is green.
- **A readable CCO name is not a CCO IRI.** `cco:Organization` parses, and names nothing:
  CCO v2 IRIs are opaque (`cco:ont00001180`). The vendoring check catches it as a term no
  pin describes.
