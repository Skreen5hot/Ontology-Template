# SPDX-License-Identifier: MIT
"""Build the release artefacts for one version, deterministically.

    python tools/release.py --version 1.2.0          # into dist/<id>-1.2.0/
    python tools/release.py --version 1.2.0 --out /tmp/x

Two variants, each in three serialisations, with checksums:

  <id>-base   the authored terms only -- every module, merged, under one
              release header. What another ontology imports.
  <id>-full   the base plus the vendored BFO and CCO extracts and BFO's
              derived disjointness: everything the checks ran over. The
              upstream part is PARTIAL -- the extracts drop every axiom
              whose object is an anonymous class expression -- and the
              header says so, with the attribution its licences require.

  .ttl  Turtle      .owl  RDF/XML      .jsonld  JSON-LD

plus NOTICE.md (the vendored attribution), LICENSE, CHANGES.md when given
(--changes: the term diff from the previous release), and SHA256SUMS.

The header of each: ontology IRI <iri_base>/<id>-base (or -full), version
IRI <iri_base>/<version>/<id>-base, owl:versionInfo the version; title,
licence and creator from the main module's header. The modules' own
owl:Ontology headers are replaced by it.

DETERMINISM

Two builds of one version are byte-identical, across processes and hash
seeds. Blank nodes get canonical labels (rdflib.compare). Turtle is
rdflib's over the canonical graph, which measured stable across seeds.
RDF/XML and JSON-LD are written here, flat and sorted, because rdflib's
writers for both iterate hash-ordered sets and their bytes changed from
one process to the next for the same graph -- measured 2026-10-23 before
this was written. Every file is parsed back and required to be the same
graph as the one it was written from. Nothing in the output depends on
the date.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402
import project  # noqa: E402

VERSION = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
DCTERMS = "http://purl.org/dc/terms/"
XSD = "http://www.w3.org/2001/XMLSchema#"
NCNAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")


class Refused(SystemExit):
    """Raised before anything is written."""


# ------------------------------------------------------------ graphs


def parsed(paths: list[Path]):
    import rdflib

    graph = rdflib.Graph()
    for path in paths:
        graph.parse(path, format="turtle")
    return graph


def without_ontology_headers(graph):
    """The graph minus every owl:Ontology node and what it says."""
    import rdflib

    out = rdflib.Graph()
    headers = set(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
    for triple in graph:
        if triple[0] not in headers:
            out.add(triple)
    return out


def main_header() -> dict:
    """Title, licence and creator from the main module's own header."""
    import rdflib

    module = layout.component("ontology.main").resolve()
    graph = parsed([module])
    heads = list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
    if len(heads) != 1:
        raise Refused("%s declares %d owl:Ontology headers; the release header "
                      "is built from exactly one" % (module.name, len(heads)))
    head = heads[0]

    def one(predicate):
        values = list(graph.objects(head, rdflib.URIRef(predicate)))
        if len(values) != 1:
            raise Refused("the main module's header has %d %s values; the "
                          "release needs exactly one" % (len(values),
                                                         predicate))
        return values[0]

    return {"title": one(DCTERMS + "title"),
            "license": one(DCTERMS + "license"),
            "creator": one(DCTERMS + "creator")}


def release_graph(variant: str, version: str, modules: list[Path],
                  vendored: list[Path], notice: str | None):
    import rdflib

    content = without_ontology_headers(parsed(modules))
    if variant == "full":
        for triple in without_ontology_headers(parsed(vendored)):
            content.add(triple)
    base = project.iri_base()
    pid = project.project_id()
    head = rdflib.URIRef("%s/%s-%s" % (base, pid, variant))
    header = main_header()
    meta = rdflib.URIRef
    content.add((head, rdflib.RDF.type, rdflib.OWL.Ontology))
    content.add((head, meta(OWL + "versionIRI"),
                 meta("%s/%s/%s-%s" % (base, version, pid, variant))))
    content.add((head, meta(OWL + "versionInfo"), rdflib.Literal(version)))
    content.add((head, meta(DCTERMS + "title"), rdflib.Literal(
        "%s (%s)" % (header["title"], variant), lang=header["title"].language)))
    content.add((head, meta(DCTERMS + "license"), header["license"]))
    content.add((head, meta(DCTERMS + "creator"), header["creator"]))
    content.add((head, meta(DCTERMS + "description"),
                 rdflib.Literal(project.load()["description"], lang="en")))
    if variant == "base":
        comment = ("Base release: the terms this project authors, from every "
                   "module, and no upstream axiom. BFO and CCO terms appear "
                   "only where an authored axiom names them.")
    else:
        comment = ("Full release: the base plus the vendored BFO and CCO "
                   "extracts this project's checks run over. The upstream "
                   "part is PARTIAL: every axiom whose object is an anonymous "
                   "class expression was dropped, so a reasoner over this "
                   "file derives less than one over BFO and CCO, and it is "
                   "not BFO or CCO. Attribution, as their licences require: "
                   + " ".join(notice.split()))
    content.add((head, meta(RDFS + "comment"), rdflib.Literal(comment,
                                                               lang="en")))
    return content


def attribution() -> str:
    import yaml

    pins = yaml.safe_load((layout.repository_root()
                           / "config/upstream-sources.yaml").read_text(
        encoding="utf-8")) or {}
    return " ".join(" ".join(entry["licence"]["attribution"].split())
                    for entry in pins.get("sources") or [])


# ------------------------------------------------------- serialising


def canonical(graph):
    """A plain graph with canonical blank-node labels. to_canonical_graph
    returns a read-only aggregate, which cannot have prefixes bound."""
    import rdflib
    from rdflib.compare import to_canonical_graph

    out = rdflib.Graph()
    for triple in to_canonical_graph(graph):
        out.add(triple)
    return out


def known_prefixes() -> dict[str, str]:
    import yaml

    pins = yaml.safe_load((layout.repository_root()
                           / "config/upstream-sources.yaml").read_text(
        encoding="utf-8")) or {}
    out = {"rdf": RDF, "rdfs": RDFS, "owl": OWL, "dcterms": DCTERMS,
           "xsd": XSD, "skos": "http://www.w3.org/2004/02/skos/core#"}
    for entry in pins.get("sources") or []:
        out[entry["prefix"]] = entry["namespace"]
    out[project.prefix()] = project.namespace()
    return out


def turtle(graph) -> bytes:
    for prefix, namespace in sorted(known_prefixes().items()):
        graph.bind(prefix, namespace, override=True, replace=True)
    return graph.serialize(format="turtle", encoding="utf-8")


def split(iri: str) -> tuple[str, str]:
    cut = max(iri.rfind("#"), iri.rfind("/"))
    return iri[:cut + 1], iri[cut + 1:]


def node_text(term) -> str:
    import rdflib

    return str(term) if isinstance(term, rdflib.URIRef) else "_:" + str(term)


def sort_key(term) -> tuple:
    import rdflib

    if isinstance(term, rdflib.URIRef):
        return (0, str(term), "", "")
    if isinstance(term, rdflib.BNode):
        return (1, str(term), "", "")
    return (2, str(term), term.language or "", str(term.datatype or ""))


def rdfxml(graph) -> bytes:
    """Flat RDF/XML: one rdf:Description per subject, everything sorted."""
    import rdflib

    known = {ns: p for p, ns in known_prefixes().items()}
    predicates = sorted({str(p) for p in graph.predicates()})
    used, names = {}, {}
    for iri in predicates:
        namespace, local = split(iri)
        if not local or not NCNAME.match(local):
            raise Refused("predicate %s has no XML-safe local name, so it "
                          "cannot be written as RDF/XML" % iri)
        prefix = known.get(namespace)
        if prefix is None or prefix in used and used[prefix] != namespace:
            prefix = "ns%d" % (len([u for u in used if u.startswith("ns")]) + 1)
        used[prefix] = namespace
        names[iri] = "%s:%s" % (prefix, local)
    used.setdefault("rdf", RDF)
    lines = ['<?xml version="1.0" encoding="utf-8"?>', "<rdf:RDF"]
    for prefix, namespace in sorted(used.items()):
        lines.append('    xmlns:%s=%s' % (prefix, quoteattr(namespace)))
    lines[-1] += ">"
    for subject in sorted(set(graph.subjects()), key=sort_key):
        if isinstance(subject, rdflib.URIRef):
            lines.append("  <rdf:Description rdf:about=%s>"
                         % quoteattr(str(subject)))
        else:
            lines.append("  <rdf:Description rdf:nodeID=%s>"
                         % quoteattr(str(subject)))
        pairs = sorted(graph.predicate_objects(subject),
                       key=lambda po: (str(po[0]), sort_key(po[1])))
        for predicate, obj in pairs:
            name = names[str(predicate)]
            if isinstance(obj, rdflib.URIRef):
                lines.append("    <%s rdf:resource=%s/>"
                             % (name, quoteattr(str(obj))))
            elif isinstance(obj, rdflib.BNode):
                lines.append("    <%s rdf:nodeID=%s/>"
                             % (name, quoteattr(str(obj))))
            else:
                attrs = ""
                if obj.language:
                    attrs = ' xml:lang=%s' % quoteattr(obj.language)
                elif obj.datatype:
                    attrs = ' rdf:datatype=%s' % quoteattr(str(obj.datatype))
                lines.append("    <%s%s>%s</%s>"
                             % (name, attrs, escape(str(obj)), name))
        lines.append("  </rdf:Description>")
    lines.append("</rdf:RDF>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def jsonld(graph) -> bytes:
    """Flattened, expanded JSON-LD: full IRIs, every list sorted."""
    import rdflib

    nodes = []
    for subject in sorted(set(graph.subjects()), key=sort_key):
        node = {"@id": node_text(subject)}
        for predicate in sorted({str(p) for p in graph.predicates(subject)}):
            values = []
            for obj in sorted(graph.objects(subject, rdflib.URIRef(predicate)),
                              key=sort_key):
                if isinstance(obj, (rdflib.URIRef, rdflib.BNode)):
                    values.append({"@id": node_text(obj)})
                elif obj.language:
                    values.append({"@value": str(obj),
                                   "@language": obj.language})
                elif obj.datatype:
                    values.append({"@value": str(obj),
                                   "@type": str(obj.datatype)})
                else:
                    values.append({"@value": str(obj)})
            key = "@type" if predicate == RDF + "type" else predicate
            node[key] = ([v["@id"] for v in values] if key == "@type"
                         else values)
        nodes.append(node)
    return (json.dumps({"@graph": nodes}, indent=1, sort_keys=True,
                       ensure_ascii=False) + "\n").encode("utf-8")


FORMATS = (("ttl", "turtle", turtle), ("owl", "xml", rdfxml),
           ("jsonld", "json-ld", jsonld))


def same_graph(data: bytes, rdflib_format: str, graph) -> bool:
    import rdflib
    from rdflib.compare import isomorphic

    back = rdflib.Graph()
    back.parse(data=data.decode("utf-8"), format=rdflib_format)
    return isomorphic(back, graph)


# -------------------------------------------------------------- build


def build(version: str, out: Path, modules: list[Path] | None = None,
          vendored: list[Path] | None = None,
          changes: Path | None = None) -> list[str]:
    if not VERSION.match(version):
        raise Refused("version %r is not MAJOR.MINOR.PATCH (a tag v1.2.0 is "
                      "released as 1.2.0)" % version)
    root = layout.repository_root()
    modules = list(modules if modules is not None else layout.ontology_files())
    vendored = list(vendored if vendored is not None
                    else layout.vendored_files())
    notice_path = layout.path("docs.vendor-notice")
    pid = project.project_id()
    target = out / ("%s-%s" % (pid, version))
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    written = []
    for variant in ("base", "full"):
        graph = canonical(release_graph(variant, version, modules, vendored,
                                        attribution()))
        for suffix, rdflib_format, writer in FORMATS:
            data = writer(graph)
            if not same_graph(data, rdflib_format, graph):
                raise Refused("%s-%s.%s does not parse back to the graph it "
                              "was written from" % (pid, variant, suffix))
            name = "%s-%s.%s" % (pid, variant, suffix)
            (target / name).write_bytes(data)
            written.append(name)
    shutil.copyfile(notice_path, target / "NOTICE.md")
    shutil.copyfile(root / "LICENSE", target / "LICENSE")
    written += ["NOTICE.md", "LICENSE"]
    if changes is not None:
        # Before the checksums, so CHANGES.md is one of the files they
        # cover rather than an unchecked attachment beside them.
        shutil.copyfile(changes, target / "CHANGES.md")
        written.append("CHANGES.md")
    sums = "".join("%s  %s\n" % (hashlib.sha256(
        (target / name).read_bytes()).hexdigest(), name)
        for name in sorted(written))
    (target / "SHA256SUMS").write_bytes(sums.encode("utf-8"))
    return sorted(written) + ["SHA256SUMS"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--version", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--changes", default=None,
                    help="a CHANGES.md to ship, from tools/ontology/term_diff.py")
    args = ap.parse_args(argv)
    root = layout.repository_root()
    out = Path(args.out) if args.out else root / "dist"
    written = build(args.version, out,
                    changes=Path(args.changes) if args.changes else None)
    target = out / ("%s-%s" % (project.project_id(), args.version))
    for name in written:
        print("  %s/%s" % (target.as_posix(), name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
