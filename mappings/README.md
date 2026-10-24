# Mappings

Crosswalks from this ontology's terms to other vocabularies — Wikidata, Dublin Core, an
industry code list, a standard's glossary — one SSSOM mapping set per target, named
`<target>.sssom.tsv`. SSSOM is the OBO community's Simple Standard for Sharing Ontological
Mappings: a YAML metadata block in `#` lines, then a TSV.

```text
# mapping_set_id: https://fandaws.com/ontology/widget/mappings/wikidata
# license: https://creativecommons.org/licenses/by/4.0/
# creator_id:
#   - https://orcid.org/0000-0000-0000-0000
# curie_map:
#   widget: https://fandaws.com/ontology/widget#
#   wd: http://www.wikidata.org/entity/
#   skos: http://www.w3.org/2004/02/skos/core#
#   semapv: https://w3id.org/semapv/vocab/
subject_id	predicate_id	object_id	mapping_justification	object_type
widget:Bolt	skos:exactMatch	wd:Q00000000	semapv:ManualMappingCuration	owl class
```

(The Wikidata id is illustrative. Look up a real one; never write it from memory.)

`python tools/ontology/mappings.py` checks every set: the metadata names a set id, a
licence and a creator; every subject is a term a module declares; every object is in a
namespace the set declares — not this project's, and not BFO's or CCO's, because a term
related to BFO or CCO is placed under it or is it, which is an axiom in a module; the
predicate is a SKOS mapping property or `owl:equivalentClass`; `exactMatch` and
`equivalentClass` state an `object_type` matching the subject's kind; every row has a
`semapv:` justification.

Mappings are never loaded into the ontology graph. An `exactMatch` to a vocabulary that is
not BFO-aligned would otherwise become a claim about this ontology's types.
