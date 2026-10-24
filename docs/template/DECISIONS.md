# Decisions — building the template

The architect's choices about the template, as given in session on 2026-10-23, in answer to
six questions the setup agent (Claude Code) put after reviewing the Business Capability
Ontology repository, the ODK project-setup tutorial and IRI_Linter. The answers are quoted
as given; the question each answers is summarized beneath.

These decide how the template is built. They do not decide anything about any project made
from it.

---

**1. "GitHub template for now"**

How a project is made from the template and kept up with it: a plain GitHub template with an
init script and a drift report, or Copier, which can push later tooling changes into derived
repositories. Effect: a GitHub template; `tools/init_project.py` and
`tools/template_status.py`. Copier is revisited when there are several derived repositories.

**2. "Keep in own CI job"**

Whether Java/ROBOT may be added for reasoning (ELK) and release artefacts. Effect: yes, in a
CI job of its own, so the checks every push runs stay Python-only. Not built yet (roadmap
phase 5).

**3. "Lets use v2.0"**

Which CCO release the template pins by default. Effect: CCO v2.0-2024-11-06, commit
`510dad76be0ef710b65a421075af912af25342b7` — the pin the Business Capability Ontology and
the Business Process Ontology use.

**4. "Readable local IRIs"**

Whether authored terms get opaque ids (`<prefix>:ont00000001`, CCO's style) or readable
local names. Effect: readable local names; no id minter or id ranges by default. Upstream
CCO terms stay opaque — they are CCO's.

**5. "https://fandaws.com/ontology/<id>#"**

The default namespace pattern. Effect: `tools/init_project.py` derives the namespace from
the project id with this pattern (`--iri-base` overrides it).

**6. "MIT"**

The licence of the template and of the tools it carries, which kept Apache-2.0 SPDX headers
from ValueNet and ARO while the repositories they were in said MIT. Effect: every carried
file's header says MIT, and `LICENSE` is MIT.

---

## Later the same day

**7. "The Name is good."**

The template's GitHub slug, `Skreen5hot/Ontology-Template`, which `tools/project.py --check`
compares against. Effect: kept as written in `config/project.yaml`.

**8. "Do we have a research folder? Seems useful for a template same with Competancy
Questions" — then: "As long as it is all covered in the plan. you can keep the roadmap as is
and push then move to the next phase"**

Effect: the roadmap keeps its phase order. Competency questions, as checked SPARQL with
expected answers, are added to phase 4; a `research/` record to phase 6; and phase 7 now
names the GitHub Pages workflow, the site tools and assets explicitly, with the
competency questions on the site. Phase 1 is committed and pushed, and phase 2 begins.

**9. "Agree with your recommendaitons. Update roadmap"**

In answer to a colleague's question whether the repository should be structured on the
ontology pipeline attributed to Jessica Talisman (controlled vocabulary, metadata schemas,
taxonomy, thesaurus, ontology, knowledge graph, as numbered directories). The
recommendation agreed to: weigh the layers for what they add, and do not adopt the numbered
layout, LinkML as the source of truth, OWL derived from SKOS, unpinned tooling, submodule
imports, or RML pipelines. Effect, in the roadmap with its phase order unchanged: example
instance data for competency questions (phase 4); a vocabulary intake, SKOS concept-scheme
modules, governance documents and SSSOM crosswalks (phase 6); crosswalk and vocabulary pages
on the site (phase 7); and a layer-by-layer comparison table, to be carried into
DEVELOPMENT.md.

**10. "Yes publish the site. My principle is an ontology is only worth making if it is public.
The HOW it was made may be private"** (2026-10-24)

In answer to whether the template's own site should be published, the Pages site of a
private repository being public. Effect: Pages is enabled for the template (GitHub Actions
as the source), and `"publish"` in `site/content/site.json` is true -- in the template and,
through it, in every project from its first commit. Because the repository may stay private,
the build is told the repository's visibility and, for a private one, writes no link into
it (source files, commit, issues, releases); the checker refuses one, and an optional
`contact` in `site.json` is the route for findings instead. A project that will not publish
sets `"publish": false`.
