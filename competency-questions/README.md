# Competency questions

What this ontology must be able to answer, each written as SPARQL with the answer it must
give. `python tools/ontology/competency.py` runs every `answerable` one, in CI and before a
commit; a wrong answer fails it.

A shape (`shapes/`) says what must never be true. A competency question says what must be
answerable. They are the two halves of "is this ontology right".

## One file per question

`CQ-<number>.yaml`, the id and the filename the same:

```yaml
id: CQ-001
question: Which material entities take part in an assembly process?
status: answerable          # draft | answerable | deferred
depends_on:                 # the terms the question is about; each must exist
  - obo:BFO_0000040
  - widget:AssemblyProcess
examples:                   # the instance files it is answered against
  - examples/assembly-line.ttl
query: |
  SELECT ?thing WHERE {
    ?process a widget:AssemblyProcess ;
             obo:BFO_0000057 ?thing .
    ?thing a/rdfs:subClassOf* obo:BFO_0000040 .
  }
expect:
  rows:
    - [eg:bolt-1]
    - [eg:panel-7]
```

- **status.** Only `answerable` is run. `draft` is written down and not yet expected to
  pass; `deferred` is out of scope for now. A question moves to `answerable` in the commit
  that makes it pass.
- **depends_on.** Every term must be a term of a pinned upstream (its register) or declared
  in an authored module. A question about a term nobody has written yet is a `draft`.
- **examples.** Paths under `examples/`. Only these are loaded with the modules and the
  vendored extracts, so one scenario's individuals cannot answer another's question. Empty
  for a question about the classes alone.
- **query.** PREFIX lines are added for `rdf`, `rdfs`, `owl`, `skos`, `dcterms`, `xsd`, every
  pinned upstream (`obo`, `cco`, …), this project's prefix, and `eg:` for the examples
  namespace (`<iri_base>/examples/`).
- **expect.** Exactly one of:
  - `rows`: the result set, exactly, in any order;
  - `includes`: rows that must be among the results;
  - `count`: how many rows;
  - `ask: true`, for an ASK query.

  Values are `prefix:local`, `<full IRI>`, or a literal's text.

## What is refused

An expectation nothing can fail is refused rather than passed: `rows: []`, `includes: []`,
`count: 0`, `ask: false`. A query that matches nothing meets each of them, and "the
ontology answers nothing" is not an answer. A property that must never hold is a shape.
A result with no rows where rows were expected fails with "returned nothing".
