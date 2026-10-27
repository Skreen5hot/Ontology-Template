# SPDX-License-Identifier: MIT
"""Canonical blank-node labels that scale, and graph equality built on them.

A release is byte-identical across builds only if every blank node gets
the same label every time, and rdflib's to_canonical_graph is how the
template did that. It is a general graph-isomorphism canonicalizer, and
its cost is driven by how alike the blank nodes look: on the Business
Process Ontology's 4,381 existential restrictions, most of them on three
properties with a few fillers, one release build had not finished after
5 h 22 min. isomorphic(), used to check each serialization parses back to
its graph, is the same algorithm and the same cost.

WHY A TREE IS EASY

Almost every blank node in an OWL ontology written in Turtle is a tree:
a restriction, a class expression, an RDF list, an axiom annotation --
each referenced from at most one place, with no cycle. A tree's content
can be summarised bottom-up: hash each node's (predicate, object) pairs,
with a blank-node object replaced by its own hash. Two trees with the
same hash are the same structure. The label is that hash together with
where the node hangs -- its parent and the predicate -- so two identical
restrictions on two different classes stay two nodes. Two identical
restrictions on the same class are interchangeable: they get the same
hash and a counter, and either assignment writes the same bytes.

Linear in the triples, with no search.

WHEN IT IS NOT A TREE

A blank node referenced from two places, or on a cycle, has no single
parent to place it by. Then the whole graph goes to rdflib, which is
correct for any graph and slow only for large alike ones. `is_forest`
says which path a graph takes, so a test can require the fast one.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _incoming(graph) -> dict:
    """Each blank node's referring (subject, predicate) pairs."""
    import rdflib

    refs = defaultdict(list)
    for s, p, o in graph:
        if isinstance(o, rdflib.BNode):
            refs[o].append((s, p))
    return refs


def is_forest(graph) -> bool:
    """Every blank node referenced at most once, and no cycle among them."""
    import rdflib

    refs = _incoming(graph)
    if any(len(r) > 1 for r in refs.values()):
        return False
    # With one parent each, a cycle is a chain that never reaches a root.
    for node in refs:
        seen, current = set(), node
        while current in refs:
            if current in seen:
                return False
            seen.add(current)
            parent = refs[current][0][0]
            if not isinstance(parent, rdflib.BNode):
                break
            current = parent
    return True


def _labels(graph) -> dict:
    """Blank node -> canonical label, for a forest."""
    import rdflib

    refs = _incoming(graph)
    out_edges = defaultdict(list)
    bnodes = set()
    for s, p, o in graph:
        if isinstance(s, rdflib.BNode):
            bnodes.add(s)
            out_edges[s].append((p, o))
        if isinstance(o, rdflib.BNode):
            bnodes.add(o)

    # Bottom-up structure hashes, iteratively: an RDF list can be longer
    # than Python's recursion limit.
    structure = {}
    for start in bnodes:
        if start in structure:
            continue
        stack = [(start, False)]
        while stack:
            node, expanded = stack.pop()
            if node in structure:
                continue
            children = [o for _, o in out_edges[node]
                        if isinstance(o, rdflib.BNode)
                        and o not in structure]
            if children and not expanded:
                stack.append((node, True))
                stack.extend((c, False) for c in children)
                continue
            parts = sorted("%s %s" % (p.n3(), structure[o]
                                      if isinstance(o, rdflib.BNode)
                                      else o.n3())
                           for p, o in out_edges[node])
            structure[node] = _digest("\n".join(parts))

    # Top-down labels: a root's place is nothing, a child's is its
    # parent's label and the predicate that reaches it.
    labels = {}

    def place(node):
        if node not in refs:
            return ""
        subject, predicate = refs[node][0]
        anchor = labels[subject] if isinstance(subject, rdflib.BNode) \
            else subject.n3()
        return "%s %s" % (anchor, predicate.n3())

    # Roots: no parent, or a parent that is an IRI.
    pending = [b for b in bnodes
               if b not in refs or not isinstance(refs[b][0][0], rdflib.BNode)]
    while pending:
        # Identical (place, structure) pairs at one level are
        # interchangeable; number them in a fixed order of their keys.
        keyed = defaultdict(list)
        for node in pending:
            keyed[_digest(place(node) + "\n" + structure[node])].append(node)
        following = []
        for key in sorted(keyed):
            for index, node in enumerate(keyed[key]):
                labels[node] = "c" + key[:32] + ("" if index == 0
                                                 else "x%d" % index)
                following.extend(o for _, o in out_edges[node]
                                 if isinstance(o, rdflib.BNode))
        pending = following
    return labels


def canonical(graph):
    """A plain graph whose blank nodes carry canonical labels."""
    import rdflib

    out = rdflib.Graph()
    if not is_forest(graph):
        from rdflib.compare import to_canonical_graph

        for triple in to_canonical_graph(graph):
            out.add(triple)
        return out
    labels = _labels(graph)

    def term(t):
        return rdflib.BNode(labels[t]) if isinstance(t, rdflib.BNode) else t

    for s, p, o in graph:
        out.add((term(s), p, term(o)))
    return out


def same_graph(a, b) -> bool:
    """Whether two graphs are isomorphic: by canonical triples when both
    are forests, by rdflib otherwise."""
    if len(a) != len(b):
        return False
    if is_forest(a) and is_forest(b):
        return set(canonical(a)) == set(canonical(b))
    from rdflib.compare import isomorphic

    return isomorphic(a, b)
