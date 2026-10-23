# Examples

Instance data — individuals, the ABox — that the competency questions are answered
against. A question like "which processes have an organization as participant?" can only be
answered over individuals; an ontology with none answers every such question with nothing.

## What goes here

One Turtle file per scenario (`assembly-line.ttl`, `supplier-audit.ttl`), small, saying in a
header comment which questions it serves. Individuals are minted in the examples namespace,
`<iri_base>/examples/` (prefix `eg:` in competency queries), never in the ontology's own
namespace, so they are never counted as terms of the ontology, never in the corpus digest,
and never in its base release.

```turtle
@prefix obo:    <http://purl.obolibrary.org/obo/> .
@prefix widget: <https://fandaws.com/ontology/widget#> .
@prefix eg:     <https://fandaws.com/ontology/widget/examples/> .

# Serves CQ-001.
eg:assembly-3 a widget:AssemblyProcess ;
    obo:BFO_0000057 eg:bolt-1 , eg:panel-7 .
eg:bolt-1  a widget:Bolt .
eg:panel-7 a widget:Panel .
```

## The rules they are held to

The IRI linter runs over these files with the modules: every type an example asserts is a
declared authored class or a real upstream term, and a readable CCO name gets the opaque id
suggested, as it would in a module. Example individuals are not checked by the shapes —
those ask about the ontology's terms — and they are not loaded into the SHACL ladder.
