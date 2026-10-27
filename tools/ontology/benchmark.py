# SPDX-License-Identifier: MIT
"""A generated ontology at a real ontology's size, with planted defects.

    python tools/ontology/benchmark.py                    # summary
    python tools/ontology/benchmark.py -o bench.ttl       # write it
    python tools/ontology/benchmark.py --classes 600      # smaller

The template's checks were built and timed on a module with no terms, and
the Business Process Ontology showed what that hides: at 3,119 classes and
4,381 existential restrictions the validation ladder did not finish in two
hours, a release build had not finished after five, and the suite ran for
fifteen. A check that never finishes verifies nothing. This is the corpus
the template measures itself on instead, so its time budgets are tested
here, on every scheduled run, rather than discovered in a project.

WHAT IT IS

Deterministic: the same arguments give the same triples, with no random
source, so a timing or a finding count can be compared between runs. By
default it is a little larger than BPO in the two dimensions that cost:

  * 3,200 classes in the project namespace, 60% under BFO process and 40%
    under BFO material entity, each with an English label and a
    genus-differentia definition naming its parent -- so the realist
    shapes walk real chains to BFO;
  * 4,500 existential restrictions on three BFO relations, drawn from a
    few fillers, so most of them are structurally alike. That is the
    shape that made rdflib's blank-node canonicalization degrade on BPO.

The relations, read from the vendored BFO register when this was
written: has participant (BFO_0000057, domain process), has occurrent
part (BFO_0000117) and has continuant part (BFO_0000178).

PLANTED DEFECTS

One per kind of check, each on a class whose local name says what it is,
so a check that runs in budget but stops finding things fails too:

  * PlantedNoDefinition       no skos:definition       (wellformedness)
  * PlantedTwoLabels          two English labels       (wellformedness)
  * PlantedDisjointParents    under process and material entity (realist)
  * PlantedWrongGenus         definition names no parent (realist warning)
  * PlantedParticipantMisuse  a material entity "has participant" (realist)

`PLANTED` maps each to the shape set expected to report it.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import project  # noqa: E402

OBO = "http://purl.obolibrary.org/obo/"
PROCESS = OBO + "BFO_0000015"
MATERIAL = OBO + "BFO_0000040"
HAS_PARTICIPANT = OBO + "BFO_0000057"
HAS_OCCURRENT_PART = OBO + "BFO_0000117"
HAS_CONTINUANT_PART = OBO + "BFO_0000178"

CLASSES = 3200
RESTRICTIONS = 4500
#: How many fillers the restrictions draw from. Few, on purpose: alike
#: restrictions are the hard case for blank-node canonicalization.
FILLERS = 12

PLANTED = {
    "PlantedNoDefinition": "validation.wellformedness",
    "PlantedTwoLabels": "validation.wellformedness",
    "PlantedDisjointParents": "validation.realist",
    "PlantedWrongGenus": "validation.realist",
    "PlantedParticipantMisuse": "validation.realist",
}


def generate(classes: int = CLASSES, restrictions: int = RESTRICTIONS):
    """The corpus, as an rdflib Graph, deterministically."""
    import rdflib
    from rdflib import BNode, Literal, URIRef
    from rdflib.namespace import OWL, RDF, RDFS, SKOS

    ns = project.namespace()
    graph = rdflib.Graph()
    processes = int(classes * 0.6)
    names, labels = [], {}

    def declare(name, label, parent_iri, parent_label, definition=None):
        iri = URIRef(ns + name)
        graph.add((iri, RDF.type, OWL.Class))
        graph.add((iri, RDFS.label, Literal(label, lang="en")))
        graph.add((iri, RDFS.subClassOf, URIRef(parent_iri)))
        graph.add((iri, SKOS.definition, Literal(
            definition or "A %s that is benchmark %s." % (parent_label,
                                                          label),
            lang="en")))
        return iri

    for i in range(classes):
        is_process = i < processes
        base = 0 if is_process else processes
        kind = "process" if is_process else "material entity"
        local = i - base
        # A tree four wide: the first few hang from the BFO root, the rest
        # from an earlier class of the same kind.
        if local < 4:
            parent, parent_label = (PROCESS if is_process else MATERIAL), kind
        else:
            parent_index = base + (local - 4) // 4
            parent, parent_label = ns + names[parent_index], \
                labels[names[parent_index]]
        name = ("BenchProcess%d" if is_process else "BenchMaterial%d") % local
        label = "%s %d" % (kind, local)
        names.append(name)
        labels[name] = label
        declare(name, label, parent, parent_label)

    process_names = names[:processes]
    material_names = names[processes:]
    fill_processes = process_names[:FILLERS]
    fill_materials = material_names[:FILLERS]
    for n in range(restrictions):
        if n % 3 == 2:
            subject = material_names[n % len(material_names)]
            relation, filler = HAS_CONTINUANT_PART, \
                fill_materials[n % len(fill_materials)]
        else:
            subject = process_names[n % len(process_names)]
            if n % 3 == 0:
                relation, filler = HAS_PARTICIPANT, \
                    fill_materials[n % len(fill_materials)]
            else:
                relation, filler = HAS_OCCURRENT_PART, \
                    fill_processes[n % len(fill_processes)]
        restriction = BNode()
        graph.add((restriction, RDF.type, OWL.Restriction))
        graph.add((restriction, OWL.onProperty, URIRef(relation)))
        graph.add((restriction, OWL.someValuesFrom, URIRef(ns + filler)))
        graph.add((URIRef(ns + subject), RDFS.subClassOf, restriction))

    # ---- planted defects
    no_def = URIRef(ns + "PlantedNoDefinition")
    graph.add((no_def, RDF.type, OWL.Class))
    graph.add((no_def, RDFS.label, Literal("planted no definition",
                                           lang="en")))
    graph.add((no_def, RDFS.subClassOf, URIRef(PROCESS)))

    two = declare("PlantedTwoLabels", "planted two labels", PROCESS,
                  "process")
    graph.add((two, RDFS.label, Literal("planted second label", lang="en")))

    both = declare("PlantedDisjointParents", "planted disjoint parents",
                   PROCESS, "process")
    graph.add((both, RDFS.subClassOf, URIRef(MATERIAL)))

    declare("PlantedWrongGenus", "planted wrong genus", PROCESS, "process",
            definition="A thing that is planted with no parent named.")

    misuse = declare("PlantedParticipantMisuse", "planted participant misuse",
                     MATERIAL, "material entity")
    restriction = BNode()
    graph.add((restriction, RDF.type, OWL.Restriction))
    graph.add((restriction, OWL.onProperty, URIRef(HAS_PARTICIPANT)))
    graph.add((restriction, OWL.someValuesFrom,
               URIRef(ns + fill_materials[0])))
    graph.add((misuse, RDFS.subClassOf, restriction))
    return graph


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--classes", type=int, default=CLASSES)
    ap.add_argument("--restrictions", type=int, default=RESTRICTIONS)
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)
    start = time.perf_counter()
    graph = generate(args.classes, args.restrictions)
    print("  %d triples in %.1f s" % (len(graph),
                                       time.perf_counter() - start))
    if args.out:
        Path(args.out).write_bytes(graph.serialize(format="turtle",
                                                   encoding="utf-8"))
        print("  wrote %s" % args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
