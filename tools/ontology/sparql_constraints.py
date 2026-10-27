# SPDX-License-Identifier: MIT
"""SHACL-SPARQL constraints, evaluated once per constraint, in Oxigraph.

pyshacl evaluates a SPARQL constraint once per focus node, through
rdflib, with the focus node passed as an initBinding. Two costs follow,
both measured on the Business Process Ontology port (3,119 classes) and
again on tools/ontology/benchmark.py:

  * rdflib joins an initBinding after evaluating the pattern, so a
    constraint walking `rdfs:subClassOf*` paid for the whole graph on
    every focus node: the realist domain check took 6.6 s per focus node
    at 150 classes, against 0.06 s with the IRI written into the query.
    The ladder did not finish in two hours. BPO's patch (inlining the
    IRI) fixed that case.
  * Even inlined, every query is parsed and evaluated afresh per focus
    node, 30-100 ms each. Thirteen constraints over 3,000 classes is
    still the 35 minutes BPO measured with the patch.

Evaluated once, unbound, in rdflib, the same domain check ran past nine
minutes. So the constraints run here instead, in Oxigraph (pyoxigraph,
MIT OR Apache-2.0), which plans its joins: each constraint is one query,
its focus nodes given in a VALUES block, and a constraint over all 3,205
benchmark classes takes 30-80 ms. pyshacl still evaluates every core
constraint (sh:minCount, sh:datatype, ...), which is fast.

WHAT IS SUPPORTED, AND WHAT IS REFUSED

Exactly what the template's shapes use, and anything else stops the run
rather than being skipped -- a constraint this does not understand and
silently passes is the vacuous-check failure the falsification rung
exists to catch:

  * node shapes whose targets are SPARQL targets (sh:target with sh:select);
  * SPARQL constraints with sh:select projecting $this, at most one
    sh:message, prefixes from sh:prefixes/sh:declare, sh:deactivated;
  * severity from the node shape, sh:Violation by default.

Refused: sh:ask, a subquery (pre-binding does not reach it), the
pre-bound $value, $path, $currentShape or $shapesGraph, a SPARQL
constraint on a property shape, any other kind of target on a shape
holding SPARQL constraints.

WHY A VALUES BLOCK IS PRE-BINDING HERE

SHACL defines pre-binding as substituting the focus node for $this. With
the focus nodes as a VALUES block at the head of the outermost group, every
solution carries $this before the rest of the group is joined, and FILTER
NOT EXISTS and MINUS -- the only places $this appears below the top
level in these shapes -- see it through SPARQL's substitution semantics.
The exception is a subquery, which has its own scope, and is refused.
tests/test_ontology_checks.py holds this module to pyshacl's own results,
record for record, on every fixture and on a benchmark corpus.

RESULTS

As pyshacl would make them: focus = $this, source shape = the node
shape, value = the focus node, and the message with {?var} and {$var}
replaced by each projected value, other variables first, then this and
value, with re.sub and str() -- pyshacl's own substitution, quirks
included, so the two engines write the same words.
"""

from __future__ import annotations

import re

SH = "http://www.w3.org/ns/shacl#"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"

THIS = re.compile(r"[$?]this(?![A-Za-z0-9_])")
REFUSED_VARIABLES = re.compile(
    r"[$](value|path|currentShape|shapesGraph)(?![A-Za-z0-9_])")
SUBQUERY = re.compile(r"\{\s*SELECT\b", re.IGNORECASE)

#: Predicates a node shape may carry besides its SPARQL constraints and
#: still have nothing left for pyshacl to evaluate once they are removed.
NON_CONSTRAINT = {RDF_TYPE, SH + "sparql", SH + "target", SH + "severity",
                  SH + "message", SH + "deactivated", SH + "name",
                  SH + "description",
                  "http://www.w3.org/2000/01/rdf-schema#label",
                  "http://www.w3.org/2000/01/rdf-schema#comment"}


class Unsupported(SystemExit):
    """A shape this runner does not evaluate. Never skipped silently."""


def _prefixes(shapes, holder) -> str:
    import rdflib

    sh = rdflib.Namespace(SH)
    lines = []
    for declared in shapes.objects(holder, sh.prefixes):
        for entry in shapes.objects(declared, sh.declare):
            prefix = shapes.value(entry, sh.prefix)
            namespace = shapes.value(entry, sh.namespace)
            lines.append("PREFIX %s: <%s>" % (prefix, namespace))
    return "\n".join(sorted(set(lines))) + "\n"


def _with_values(select: str, foci_text: str) -> str:
    start = select.find("{")
    if start < 0:
        raise Unsupported("a SPARQL constraint has no WHERE group:\n%s"
                          % select)
    return (select[:start + 1] + "\n  VALUES ?this { " + foci_text + " }\n"
            + select[start + 1:])


def _check_select(select: str, where: str) -> None:
    if SUBQUERY.search(select):
        raise Unsupported("%s uses a subquery, which pre-binding does not "
                          "reach" % where)
    found = REFUSED_VARIABLES.search(select)
    if found:
        raise Unsupported("%s uses the pre-bound variable $%s, which this "
                          "runner does not provide" % (where, found.group(1)))
    head = select[:select.find("{")] if "{" in select else select
    if not THIS.search(head) and "*" not in head:
        raise Unsupported("%s does not project $this" % where)


def split(shapes):
    """(shapes for pyshacl, the SPARQL node shapes to run here)."""
    import rdflib

    sh = rdflib.Namespace(SH)
    core = rdflib.Graph()
    for triple in shapes:
        core.add(triple)
    for prefix, namespace in shapes.namespaces():
        core.bind(prefix, namespace)
    sparql_shapes = sorted(set(shapes.subjects(sh.sparql, None)), key=str)
    for shape in sparql_shapes:
        if (shape, sh.path, None) in shapes:
            raise Unsupported("%s is a property shape with a SPARQL "
                              "constraint" % shape)
        for constraint in shapes.objects(shape, sh.sparql):
            core.remove((shape, sh.sparql, constraint))
        remaining = {str(p) for p, _ in core.predicate_objects(shape)}
        if remaining <= NON_CONSTRAINT:
            # Nothing left for pyshacl: drop the target too, or it runs
            # the target query for a shape with no constraint.
            for target in list(core.objects(shape, sh.target)):
                core.remove((shape, sh.target, target))
    return core, sparql_shapes


def _store(data):
    import pyoxigraph as ox

    # load, never bulk_load: bulk_load parses in parallel chunks, and a
    # blank-node label seen in two chunks becomes two nodes. Measured on
    # the benchmark: a class -> restriction -> property join gave 20 rows
    # after bulk_load and 85 after load, and the realist domain and range
    # checks silently found nothing. test_ontology_checks holds this.
    store = ox.Store()
    store.load(data.serialize(format="nt", encoding="utf-8"),
               ox.RdfFormat.N_TRIPLES)
    return store


def _text(term) -> str:
    """What str() of the matching rdflib term would give."""
    return term.value


def run(data, shapes, sparql_shapes, store=None) -> list[dict]:
    """The SPARQL constraints' results, in run()'s record shape."""
    import rdflib

    sh = rdflib.Namespace(SH)
    store = store or _store(data)
    out = []
    for shape in sparql_shapes:
        targets = list(shapes.objects(shape, sh.target))
        other = [p for p in (sh.targetClass, sh.targetNode,
                             sh.targetSubjectsOf, sh.targetObjectsOf)
                 if (shape, p, None) in shapes]
        if other or not targets:
            raise Unsupported("%s holds SPARQL constraints and has a target "
                              "this runner does not evaluate" % shape)
        foci = set()
        for target in targets:
            select = shapes.value(target, sh.select)
            if select is None:
                raise Unsupported("%s has a target with no sh:select"
                                  % shape)
            text = _prefixes(shapes, target) + THIS.sub("?this", str(select))
            for row in store.query(text):
                foci.add(row["this"])
        severity = shapes.value(shape, sh.severity) or sh.Violation
        if not foci:
            continue
        if any(not hasattr(f, "value") or type(f).__name__ == "BlankNode"
               for f in foci):
            raise Unsupported("%s targets a blank node, which a VALUES "
                              "block cannot name" % shape)
        foci_text = " ".join(str(f) for f in sorted(foci, key=str))
        for constraint in sorted(shapes.objects(shape, sh.sparql), key=str):
            if shapes.value(constraint, sh.deactivated) in (
                    rdflib.Literal(True), rdflib.Literal("true")):
                continue
            if (constraint, sh.ask, None) in shapes:
                raise Unsupported("%s has an sh:ask constraint" % shape)
            select = shapes.value(constraint, sh.select)
            if select is None:
                raise Unsupported("%s has a SPARQL constraint with no "
                                  "sh:select" % shape)
            messages = list(shapes.objects(constraint, sh.message))
            if len(messages) != 1:
                # pyshacl's default wording, for none, is not worth
                # imitating; two would make the record's message depend
                # on which one rdflib returns first.
                raise Unsupported("%s has a constraint with %d messages; "
                                  "exactly one is supported"
                                  % (shape, len(messages)))
            _check_select(str(select), str(shape))
            query = _prefixes(shapes, constraint) + _with_values(
                THIS.sub("?this", str(select)), foci_text)
            results = store.query(query)
            names = [v.value for v in results.variables]
            seen = set()
            for row in results:
                bound = {}
                for name in names:
                    value = row[name]
                    if value is not None:
                        bound[name] = value
                this = bound.pop("this", None)
                if this is None:
                    continue
                key = (str(this), tuple(sorted(
                    (k, str(v)) for k, v in bound.items())))
                if key in seen:
                    continue
                seen.add(key)
                message = str(messages[0])
                # pyshacl's order: the other variables, then this, then
                # value (the focus node, for a node shape).
                order = [(k, _text(v)) for k, v in bound.items()
                         if k not in ("path", "value")]
                order += [("this", _text(this)), ("value", _text(this))]
                for var, val in order:
                    message = re.sub("{[?$]%s}" % var, val, message)
                out.append({
                    "focus": _text(this),
                    # The term itself: validate.stable_shape names it,
                    # as it names pyshacl's.
                    "source": shape,
                    "severity": str(severity).rsplit("#", 1)[-1],
                    "message": message,
                })
    return out
