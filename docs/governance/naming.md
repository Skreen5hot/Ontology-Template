# Naming

## Local names

Readable, in the project namespace, following `config/naming.yaml` (checked by the IRI
linter as `naming_convention`, and by the vocabulary generator):

| Kind | Convention | Example |
|---|---|---|
| class | UpperCamelCase | `MaintenanceAct` |
| object, datatype or annotation property | lowerCamelCase | `hasMaintainer` |
| concept, concept scheme | letters, digits, `-`, `_` | `P10020`, `asset-status` |

A local name is never reused for a different term, even after the first is deprecated.

## Labels

Not checked by a tool, and a project's call. The default here follows BFO: labels in lower
case except for proper nouns and acronyms (*material entity*, *maintenance act*, *ISO
standard*). CCO writes Title Case (*Organization*); a project closer to CCO may choose that
instead. Write the choice here, and keep to it: a mixed ontology reads as two.

One `rdfs:label` per language for a class, one `skos:prefLabel` per language for a concept;
the wellformedness shapes enforce both.

## Upstream terms

BFO and CCO terms keep their own opaque IRIs (`obo:BFO_0000015`, `cco:ont00001180`) and
their own labels. They are referenced, never redeclared or annotated here; the IRI linter
refuses both.
