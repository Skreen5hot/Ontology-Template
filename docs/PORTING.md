# Porting a predecessor ontology

How to bring an ontology that already exists into a project made from this template. Six
things a port has to decide, in the order a port meets them. The form for recording the
port, [`porting/port-report.md`](porting/port-report.md), asks for the evidence of each.

Before starting: copy the form to `research/port-report.md` and fill it in as you go.
`tools/init_project.py` refuses a dirty tree, except `research/`, which it never writes and
does not stage.

## 1. The namespace move

A port mints its terms in the project's namespace, so every term's IRI changes. Keep the
local names: `old:Invoice` becomes `<prefix>:Invoice`. A local name is the term's identity
for everyone who used the predecessor, and changing it at the same time as the namespace
turns one mechanical change into thousands of judgments.

Say why in a decision (`docs/decisions/`): what the predecessor's namespace was, why the
terms cannot stay in it (the namespace belongs to another project, or to a draft, or is not
resolvable), and that the move is the only change. If the move is *not* the only change,
because terms are renamed, merged, split or re-parented, each such term gets a row of its
own in the form's coverage table and a reason.

## 2. The mapping set

The move is recorded as an SSSOM mapping set in `mappings/`, one row per term, checked by
`tools/ontology/mappings.py` like any other set.

- **Direction: new to old.** The subject is the term here; the object is the predecessor's.
  The checker requires the subject to be a term a module declares, so a set written old to
  new is refused. A request worded "old IRI to new IRI" means this set read backwards.
- **Predicate:** `skos:exactMatch` for a term carried unchanged. A term whose meaning
  changed is not an exact match; say what it is (`skos:closeMatch`, `skos:broadMatch`, ...)
  and why, in that row's `comment`.
- **Justification.** SEMAPV has no term for "the same term, namespace moved" (its term list,
  checked 2026-10-29). `semapv:ManualMappingCuration` fits best: a person decided the rule
  (same local name, new namespace) and the rule produced every row. Name the decision in each
  row's `comment` and the script that wrote the rows in `mapping_tool`.
  `semapv:UnspecifiedMatching` is SEMAPV's term for a mapping whose method is no longer
  known, which is not this case.
- `object_type` states each subject's kind (`owl class`, `owl object property`,
  `skos concept`, ...), as the checker requires for an exact match.

## 3. The module headers

Each module gets an `owl:Ontology` header of its own in the project's namespace, with what
the realist header shape requires (`dcterms:title`, `dcterms:license`, `dcterms:creator`,
`owl:versionIRI`, `owl:versionInfo`). The predecessor's headers are replaced, not copied,
because they name the predecessor's ontology IRIs. Carry what they said:

- `dcterms:source` naming the predecessor and the commit or release the module was ported
  from, so a reader can find the text it came from;
- the predecessor's `rdfs:comment` and any `dcterms:description`, where they are still true;
- a `dcterms:source` with the source's **name and release** on every module that holds text
  from a third-party source, which the validator requires once the text's annotation
  property is declared in `config/third-party-text.yaml` (section 5).

## 4. The lossless check

Before anything is fixed, show that the port lost nothing and added nothing. Compare every
statement of the predecessor, renamed into the new namespace, with every statement of the
port:

- **Ground statements** as sets of triples.
- **Blank nodes** (restrictions, lists) as trees, not as canonicalized graphs. Write each
  blank node as the sorted text of everything under it, and compare those. Canonicalizing
  the whole graph (`rdflib.compare.to_canonical_graph`) degrades badly on thousands of
  similar restrictions, which is what an OWL ontology has.

```python
from rdflib import BNode, URIRef


def tree(graph, node):
    """A blank node as the sorted text of everything under it."""
    if not isinstance(node, BNode):
        return node.n3()
    rows = sorted("%s %s" % (p.n3(), tree(graph, o))
                  for p, o in graph.predicate_objects(node))
    return "[" + "; ".join(rows) + "]"


def statements(graph):
    """Every statement whose subject is named, blank objects as trees;
    and every blank node nothing points to (an owl:AllDisjointClasses
    axiom, say) as a tree of its own."""
    named = {(s.n3(), p.n3(), tree(graph, o))
             for s, p, o in graph if not isinstance(s, BNode)}
    roots = {("", "", tree(graph, s)) for s in set(graph.subjects())
             if isinstance(s, BNode) and (None, None, s) not in graph}
    return named | roots


def renamed(graph, old, new):
    """The graph with every IRI in namespace `old` moved to `new`."""
    def move(term):
        if isinstance(term, URIRef) and str(term).startswith(old):
            return URIRef(new + str(term)[len(old):])
        return term
    out = type(graph)()
    for s, p, o in graph:
        out.add((move(s), move(p), move(o)))
    return out
```

Then `statements(renamed(source, OLD, NEW))` and `statements(port)` should be equal, apart
from what the port excludes by design. List every exclusion, with its reason, in the form:
typically the predecessor's `owl:Ontology` headers (section 3), and statements about
upstream terms that the pinned BFO or CCO already asserts (check each in the pinned file;
a statement the upstream does not assert is not an exclusion, it is a loss). Two identical
restrictions in two predecessor files are one statement here; say how many there were.

Re-run the port script and compare its output with the committed modules byte for byte:
a port that cannot be reproduced cannot be reviewed.

## 5. The findings it arrives with

A port arrives with defects of its own: drifted definitions, missing headers, terms the
realist shapes question. Run every check before fixing anything, and record the first
result in the form. Then each finding is fixed, or accepted, by a person:

- **Accepted** findings are entries in `config/findings-register.yaml`, one per finding,
  by identity. `validate.py --propose` and `iri_lint.py --propose` print the entries for a
  person to complete with a reason, an owner and a review date. Filling many at once
  (`--reason`, `--owner`, `--review`) is one decision about all of them; record whose.
- **Findings about BFO or CCO terms** are entered with `upstream:`, so they stay apart from
  the project's own.
- **Third-party text** (passages quoted from a framework or a standard) is declared in
  `config/third-party-text.yaml`, so the licensing report lists it apart from the module's
  licence. That report records what is declared; it does not decide whether the text may be
  redistributed. That question goes to whoever can answer it for the project, before the
  port is published.
- **The project's own requirements**, the ones its decisions add, are tests in
  `tests/project/` (see its README), not edits to the template's tests.

## 6. The naming scheme it already has

New terms get readable local names: UpperCamelCase classes, lowerCamelCase properties
(`config/naming.yaml`, template decision 4). **That is the default for new terms, not a rule
for ported ones.** A predecessor that minted identifiers on purpose, such as a code from a
classification (`P10002`), keeps them: renaming would break every reference to it, and the
code is often the point.

So a port declares its scheme rather than conforming to the default:

- **`config/naming.yaml`'s patterns** say what a local name may look like here. Widen them
  to admit the scheme, and say why in the file.
- **Scheme rules** in the same file say what a pattern *means*: names matching `P[0-9]+`
  must sit under a process category, say. The validator gates them under `where: naming`.
- **`docs/governance/naming.md`** states the policy in words: which names are readable,
  which follow the scheme, and what a new term gets.

A term that matches neither the default nor the scheme is a finding (`naming_convention`),
fixed or accepted like any other.

## After the port

`python tools/template_status.py` should list nothing the port changed: a port that had to
edit a template-owned file has found something the template should fix. Record each such
file, with what was changed and why, in the form's section 5, and report it to the
template.
