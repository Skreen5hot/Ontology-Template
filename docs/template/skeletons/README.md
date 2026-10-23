# {{title}}

{{description}}

A realist ontology aligned to BFO 2020 and CCO v2.0. Terms are minted in
`{{namespace}}` (prefix `{{prefix}}:`) with readable local names.

> **New here?** Read [`docs/HANDOFF.md`](docs/HANDOFF.md) first for what is in this
> repository and what is not. [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) is how to run
> things; [`docs/process/PROCESS.md`](docs/process/PROCESS.md) is why it is built this way.

## Organization

```text
ontology/   the authored modules ({{module}} to start)
shapes/     SHACL shapes, and the fixtures built to break them
vendor/     pinned partial extracts of BFO and CCO, with attribution
config/     project values, layout contract, upstream pins, manifests, baseline, digest
tools/      layout, licensing, vendoring, validation and digest tools
tests/      the suite, including the falsifications
docs/       handoff, development, process, decisions
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
python -m pytest tests/ -q -p no:randomly
```

The same checks run in CI on every push. What each one refuses is in
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md).

## Provenance

Made from the [ontology template]({{template_url}}), which carries the tooling and method of
the Application Requirement Ontology and the Business Capability Ontology.
`python tools/template_status.py` reports where this repository has diverged from the
template version it was made from.

## Licence

[MIT](LICENSE). The vendored extracts carry their upstream licences: BFO CC BY 4.0, CCO
BSD-3-Clause.
