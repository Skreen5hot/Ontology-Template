# SPDX-License-Identifier: MIT
"""Keep the modules a project edits in Protégé in one canonical Turtle form.

    python tools/ontology/normalize.py            # rewrite every opted-in module
    python tools/ontology/normalize.py --check    # exit 1 if one is not canonical

Protégé rewrites a module in its own Turtle on save: prefixes re-declared,
statements reordered, comments gone. The meaning is unchanged and the
corpus digest proves it; the diff is unreadable, and a reviewer cannot
see the one axiom that changed among two hundred reordered lines.

A module opts in with `format: canonical` in its layout declaration.
Canonical means rdflib's Turtle of the module's graph with canonical
blank-node labels and the project's and the pins' prefixes -- the form
tools/release.py writes, measured stable across processes. Comments do
not survive it, which is why it is opt-in: a module written by hand, with
its reasoning in comments, should not be canonical; a module edited in
Protégé already has no comments to lose.

The rewrite is refused if the canonical text does not parse back to the
same graph.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

FORMAT = "canonical"


class Refused(SystemExit):
    """The canonical form would change the graph."""


def prefixes() -> dict[str, str]:
    import yaml

    pins = yaml.safe_load((layout.repository_root()
                           / "config/upstream-sources.yaml").read_text(
        encoding="utf-8")) or {}
    out = {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
           "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
           "owl": "http://www.w3.org/2002/07/owl#",
           "skos": "http://www.w3.org/2004/02/skos/core#",
           "dcterms": "http://purl.org/dc/terms/",
           "xsd": "http://www.w3.org/2001/XMLSchema#"}
    for entry in pins.get("sources") or []:
        out[entry["prefix"]] = entry["namespace"]
    out[project.prefix()] = project.namespace()
    return out


def canonical_text(text: str) -> bytes:
    """The canonical Turtle of a module's text."""
    import rdflib
    from rdflib.compare import isomorphic, to_canonical_graph

    source = rdflib.Graph()
    source.parse(data=text, format="turtle")
    graph = rdflib.Graph()
    for triple in to_canonical_graph(source):
        graph.add(triple)
    for prefix, namespace in sorted(prefixes().items()):
        graph.bind(prefix, namespace, override=True, replace=True)
    data = graph.serialize(format="turtle", encoding="utf-8")
    back = rdflib.Graph()
    back.parse(data=data.decode("utf-8"), format="turtle")
    if not isomorphic(back, source):
        raise Refused("the canonical form does not parse back to the same "
                      "graph; refusing to rewrite")
    return data


def opted_in() -> list[Path]:
    out = []
    for entry in layout.components():
        if entry.format == FORMAT:
            out.extend(entry.members("*.ttl"))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    paths = opted_in()
    if not paths:
        print("  no module declares format: canonical")
        return 0
    stale = []
    for path in paths:
        current = path.read_bytes()
        wanted = canonical_text(current.decode("utf-8"))
        if current == wanted:
            continue
        if args.check:
            stale.append(path.name)
        else:
            path.write_bytes(wanted)
            print("  rewrote %s" % path.name)
    if stale:
        print("  NOT CANONICAL: %s -- run python tools/ontology/normalize.py"
              % ", ".join(stale))
        return 1
    print("  %d module(s) canonical" % len(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
