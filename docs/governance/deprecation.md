# Deprecation

A term somebody may already use is never deleted. It is deprecated:

```turtle
widget:OldName owl:deprecated true ;
    dcterms:isReplacedBy widget:NewName ;          # when there is a successor
    skos:historyNote "Merged into NewName: the two were never distinguished in use."@en .
```

- `owl:deprecated true`, and **at least one** of `dcterms:isReplacedBy` (where to go
  instead) and `skos:historyNote` (why it went). The deprecated-term shape in
  `shapes/realist_shapes.ttl` refuses one with neither.
- The term keeps its label, definition and parent, so what it meant stays readable.
- Its local name is not reused.
- The release's `CHANGES.md` lists it under *Deprecated*, with its replacement.

An upstream term deprecated by its own release (`owl:deprecated` in the pinned BFO or CCO)
is reported by the IRI linter as `deprecated_upstream` wherever this ontology uses it.
