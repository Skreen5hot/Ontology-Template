# Naming

## Local names

New terms get readable local names, in the project namespace, following
`config/naming.yaml` (checked by the IRI linter as `naming_convention`, and by the
vocabulary generator):

| Kind | Convention | Example |
|---|---|---|
| class | UpperCamelCase | `MaintenanceAct` |
| object, datatype or annotation property | lowerCamelCase | `hasMaintainer` |
| concept, concept scheme | letters, digits, `-`, `_` | `P10020`, `asset-status` |

A local name is never reused for a different term, even after the first is deprecated.

## Identifiers a port keeps

Readable names are the default for new terms, not a rule for ported ones. A predecessor
ontology that minted identifiers on purpose (a classification's codes, `P10002`) keeps
them: renaming would break every reference to the term, and the code is often the point.
Such a project widens the patterns in `config/naming.yaml` to admit its scheme, says what
the scheme means in scheme rules there, and states the policy here: which names are codes,
which are readable, and what a new term gets. `docs/PORTING.md` section 6 has the steps.

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
