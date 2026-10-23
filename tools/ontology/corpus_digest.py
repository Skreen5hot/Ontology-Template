# SPDX-License-Identifier: MIT
"""Measure the ontology, so a change to it is visible.

    python tools/ontology/corpus_digest.py
    python tools/ontology/corpus_digest.py -o config/corpus-digest.json

Two measures, because one is not enough.

GROUND DIGEST

Triples with no blank node anywhere. These carry the named terms, and
they are stable across parses, so a digest over them changes when and
only when the asserted content changes.

BLANK-NODE FINGERPRINT

Blank nodes are renamed by every parse, so they cannot be digested
directly -- a naive set comparison reports every restriction as both
added and removed. What is stable is their shape: how many there are,
how many triples touch them, and the multiset of predicate/object pairs
with the identities erased.

Between them the two cover every triple. That matters: a measure that
covered only ground triples would be blind to exactly the constructs OWL
uses most, and an ontology can be rewritten substantially without a
single named term changing.

WHAT IS MEASURED

The scope comes from the layout contract, not from a directory walk. A
walk would pick up the reasoner's own output and a fixture whose purpose
is to be invalid, and would then report the result as a property of the
ontology.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402

FORMAT_VERSION = 1
GENERATOR = "tools/ontology/corpus_digest.py"


def parse(path: Path):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(path, format="turtle")
    return graph


def ground(graph) -> list[str]:
    """Triples with no blank node, as sorted text."""
    import rdflib

    rows = []
    for s, p, o in graph:
        if isinstance(s, rdflib.BNode) or isinstance(o, rdflib.BNode):
            continue
        rows.append("%s %s %s" % (s.n3(), p.n3(), o.n3()))
    return sorted(rows)


def bnode_shape(graph) -> dict:
    """Structure without identities.

    Erasing the blank node and keeping the predicate and object is what
    makes this comparable between parses. Two graphs with the same shape
    digest have the same anonymous structure even though no blank node
    name is shared.
    """
    import rdflib

    touching, nodes = 0, set()
    pairs: collections.Counter = collections.Counter()
    for s, p, o in graph:
        s_blank = isinstance(s, rdflib.BNode)
        o_blank = isinstance(o, rdflib.BNode)
        if not (s_blank or o_blank):
            continue
        touching += 1
        if s_blank:
            nodes.add(s)
        if o_blank:
            nodes.add(o)
        pairs[("_:b" if s_blank else s.n3(), p.n3(),
               "_:b" if o_blank else o.n3())] += 1

    text = "\n".join("%s %s %s %d" % (s, p, o, n)
                     for (s, p, o), n in sorted(pairs.items()))
    return {
        "blank_nodes": len(nodes),
        "triples_touching": touching,
        "distinct_shapes": len(pairs),
        "shape_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def digest_of(rows: list[str]) -> str:
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def measure() -> dict:
    root = layout.repository_root()
    files = layout.ontology_files()
    if not files:
        raise SystemExit(
            "the ontology scope is empty, so every measure below would be "
            "a digest of nothing")

    per_file, merged_ground = {}, []
    merged = None
    import rdflib

    merged = rdflib.Graph()

    for path in files:
        graph = parse(path)
        rows = ground(graph)
        relative = path.relative_to(root).as_posix()
        per_file[relative] = {
            "triples": len(graph),
            "ground_triples": len(rows),
            "ground_sha256": digest_of(rows),
            "blank_nodes": bnode_shape(graph),
        }
        merged_ground.extend(rows)
        for triple in graph:
            merged.add(triple)

    merged_rows = sorted(set(merged_ground))
    return {
        "format_version": FORMAT_VERSION,
        "generated_by": GENERATOR,
        "scope": {
            "files": len(files),
            "from": "config/repository-layout.yaml, roles ontology-module "
                    "and ontology-module-set",
            "paths": sorted(per_file),
        },
        "merged": {
            "triples": len(merged),
            "ground_triples": len(merged_rows),
            "ground_sha256": digest_of(merged_rows),
            "blank_nodes": bnode_shape(merged),
        },
        "per_file": per_file,
        "note": (
            "Ground triples and blank-node shape together cover every "
            "triple. Blank nodes are renamed by every parse, so their "
            "identities are erased and only their structure is digested."),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)

    record = measure()

    print("  %d file(s) in scope" % record["scope"]["files"])
    print("  merged: %d triples, %d ground"
          % (record["merged"]["triples"], record["merged"]["ground_triples"]))
    print("    ground   %s" % record["merged"]["ground_sha256"][:32])
    blanks = record["merged"]["blank_nodes"]
    print("    blank    %s  (%d nodes, %d triples touching)"
          % (blanks["shape_sha256"][:32], blanks["blank_nodes"],
             blanks["triples_touching"]))

    if args.out:
        target = Path(args.out)
        target = target if target.is_absolute() else (
            layout.repository_root() / target)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(json.dumps(record, indent=2, sort_keys=True,
                                      ensure_ascii=False).encode("utf-8")
                           + b"\n")
        print("  wrote %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
