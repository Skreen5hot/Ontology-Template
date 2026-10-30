# {{title}}

{{description}}

A realist ontology aligned to BFO 2020 and CCO v2.0. Terms are minted in
`{{namespace}}` (prefix `{{prefix}}:`). New terms get readable local names; the conventions,
and any identifier scheme the project keeps, are in
[`docs/governance/naming.md`](docs/governance/naming.md).

> **New here?** Read [`docs/HANDOFF.md`](docs/HANDOFF.md) first for what is in this
> repository and what is not. [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) is how to run
> things; [`docs/process/PROCESS.md`](docs/process/PROCESS.md) is why it is built this way,
> and [`docs/process/METHOD.md`](docs/process/METHOD.md) is how the ontology is built, starting
> from the scope charter, [`docs/charter.md`](docs/charter.md).

## Organization

```text
ontology/   the authored modules ({{module}} to start)
shapes/     SHACL shapes, and the fixtures built to break them
vendor/     pinned partial extracts of BFO and CCO, with attribution
config/     project values, layout contract, upstream pins, manifests, findings register, digest
tools/      layout, licensing, vendoring, validation and digest tools
tests/      the suite, including the falsifications; the project's own in tests/project/
docs/       handoff, development, process, decisions, porting
```

## Foundations

BFO 2020 is the upper ontology and CCO v2.0 the mid-level one. Both are vendored under
[`vendor/`](vendor/) as pinned partial extracts rather than resolved over the network at
validation time. BFO is carried whole; CCO carries only the terms this repository names
plus their named ancestry. Every axiom whose object is an anonymous class expression is
dropped, so the extracts cannot be used to claim consistency with BFO or CCO.

Pins, digests and licences are in [`config/upstream-sources.yaml`](config/upstream-sources.yaml);
what was taken and what was left is in [`config/upstream-extracts.json`](config/upstream-extracts.json);
attribution is in [`vendor/NOTICE.md`](vendor/NOTICE.md).

## Checks

```bash
python -m venv .venv && .venv/Scripts/activate      # Windows; source .venv/bin/activate elsewhere
python -m pip install -r requirements-dev.txt
git config core.hooksPath .githooks                 # the IRI linter on every commit
python -m pytest tests/ -q -p no:randomly -m "not reasoning and not scale and not corpus"
```

The last command is the Checks workflow's. The tests marked `reasoning` need Java; those
marked `scale` and `corpus` take minutes and run in workflows of their own. Drop the `-m`
to run everything.

**Check every pin** before the first push and before each release: nothing here updates
them by itself. `python tools/pins.py` checks them all (`docs/DEVELOPMENT.md`, "Pins"). The same checks run in CI on every push. What each one refuses is in
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Provenance

Made from the [ontology template]({{template_url}}), which carries the tooling and method of
the Application Requirement Ontology and the Business Capability Ontology.
`python tools/template_status.py` reports where this repository has diverged from the
template version it was made from.

## Licence

[MIT](LICENSE). The vendored extracts carry their upstream licences: BFO CC BY 4.0, CCO
BSD-3-Clause.
