# SPDX-License-Identifier: MIT
"""Check the crosswalks: SSSOM mapping sets from authored terms to other vocabularies.

    python tools/ontology/mappings.py           # every mappings/*.sssom.tsv
    python tools/ontology/mappings.py a.sssom.tsv

Exit codes: 0 every mapping set holds; 1 a finding; 2 a file that cannot
be read as SSSOM.

A crosswalk says how a term here relates to a term in a standard,
catalogue or other ontology that is not this project's foundation --
Wikidata, Dublin Core, an industry code list. SSSOM (the OBO community's
Simple Standard for Sharing Ontological Mappings) is the format: a YAML
metadata block in `#` lines, then a TSV of mappings.

WHAT IS CHECKED

  metadata   mapping_set_id, license, creator_id or creator_label, and a
             curie_map naming every prefix the rows use (semapv: among
             them)
  subject    a term an authored module declares -- class, property,
             concept or scheme
  object     in a namespace the curie_map declares; not the project's
             own; and not a pinned upstream's. A term related to BFO or
             CCO is placed under it, or is it -- an axiom in a module, not
             a mapping
  predicate  skos:exactMatch, closeMatch, broadMatch, narrowMatch,
             relatedMatch, or owl:equivalentClass
  kind       skos:exactMatch and owl:equivalentClass only between things
             of one kind: the row states object_type, and it must be the
             subject's -- "owl class" for a class, "skos concept" for a
             concept. owl:equivalentClass only from a class.
  rows       a mapping_justification from semapv:; no row twice

Mappings are never loaded into the ontology graph: they are TSV, their
role keeps them out of every scope, and an exactMatch to a vocabulary
that is not BFO-aligned would otherwise become a claim about this
ontology's types.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

ROLE = "mapping-set"
SKOS = "http://www.w3.org/2004/02/skos/core#"
OWL = "http://www.w3.org/2002/07/owl#"
SEMAPV = "https://w3id.org/semapv/vocab/"
PREDICATES = {SKOS + p for p in ("exactMatch", "closeMatch", "broadMatch",
                                 "narrowMatch", "relatedMatch")} | {
    OWL + "equivalentClass"}
STRICT = {SKOS + "exactMatch", OWL + "equivalentClass"}
REQUIRED_COLUMNS = ("subject_id", "predicate_id", "object_id",
                    "mapping_justification")

#: The SSSOM entity type each kind of authored term is.
KINDS = {
    OWL + "Class": "owl class",
    OWL + "ObjectProperty": "owl object property",
    OWL + "DatatypeProperty": "owl data property",
    OWL + "AnnotationProperty": "owl annotation property",
    SKOS + "Concept": "skos concept",
    SKOS + "ConceptScheme": "skos concept",
}


class Unreadable(Exception):
    """Exit 2: not SSSOM."""


def read(path: Path) -> tuple[dict, list[dict], list[str]]:
    import yaml

    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise Unreadable("%s cannot be read: %s" % (path, error))
    meta_lines, body = [], []
    for line in text.splitlines():
        (meta_lines if line.startswith("#") else body).append(line)
    try:
        meta = yaml.safe_load("\n".join(l[1:] for l in meta_lines)) or {}
    except Exception as error:  # yaml raises several types
        raise Unreadable("%s: the metadata block is not YAML: %s"
                         % (path.name, " ".join(str(error).split())[:200]))
    if not isinstance(meta, dict):
        raise Unreadable("%s: the metadata block is not a mapping" % path.name)
    reader = csv.DictReader(io.StringIO("\n".join(body)), delimiter="\t")
    return meta, list(reader), list(reader.fieldnames or [])


def authored_kinds(modules: list[Path]) -> dict[str, str]:
    """{authored term IRI: SSSOM entity type}."""
    import rdflib

    graph = rdflib.Graph()
    for path in modules:
        graph.parse(path, format="turtle")
    namespace = project.namespace()
    out = {}
    for subject, kind in graph.subject_objects(rdflib.RDF.type):
        if str(subject).startswith(namespace) and str(kind) in KINDS:
            out.setdefault(str(subject), KINDS[str(kind)])
    return out


def upstream_namespaces() -> tuple:
    import yaml

    pins = yaml.safe_load((layout.repository_root()
                           / "config/upstream-sources.yaml").read_text(
        encoding="utf-8")) or {}
    return tuple(entry["namespace"] for entry in pins.get("sources") or [])


def expand(curie: str, curie_map: dict) -> str | None:
    curie = (curie or "").strip()
    if curie.startswith("<") and curie.endswith(">"):
        return curie[1:-1]
    if ":" not in curie:
        return None
    prefix, local = curie.split(":", 1)
    if prefix not in curie_map or not local:
        return None
    return str(curie_map[prefix]) + local


def check_file(path: Path, kinds: dict, upstream: tuple) -> list[str]:
    meta, rows, columns = read(path)
    where = path.name
    problems = []
    for key in ("mapping_set_id", "license"):
        if not meta.get(key):
            problems.append("%s: the metadata names no %s" % (where, key))
    if not (meta.get("creator_id") or meta.get("creator_label")):
        problems.append("%s: the metadata names no creator_id or "
                        "creator_label" % where)
    curie_map = meta.get("curie_map") or {}
    if not isinstance(curie_map, dict) or not curie_map:
        problems.append("%s: the metadata has no curie_map" % where)
        curie_map = {}
    if curie_map.get("semapv") != SEMAPV:
        problems.append("%s: curie_map does not map semapv: to %s"
                        % (where, SEMAPV))
    missing = [c for c in REQUIRED_COLUMNS if c not in columns]
    if missing:
        return problems + ["%s: no %s column" % (where, c) for c in missing]

    namespace = project.namespace()
    seen = {}
    for number, row in enumerate(rows, 1):
        line = "%s row %d" % (where, number)
        key = (row["subject_id"], row["predicate_id"], row["object_id"])
        if key in seen:
            problems.append("%s: repeats row %d" % (line, seen[key]))
            continue
        seen[key] = number
        subject = expand(row["subject_id"], curie_map)
        predicate = expand(row["predicate_id"], curie_map)
        obj = expand(row["object_id"], curie_map)
        if subject is None or predicate is None or obj is None:
            problems.append("%s: a CURIE whose prefix the curie_map does not "
                            "declare (%s %s %s)" % (line, row["subject_id"],
                                                    row["predicate_id"],
                                                    row["object_id"]))
            continue
        if subject not in kinds:
            problems.append("%s: subject %s is not a term an authored module "
                            "declares" % (line, row["subject_id"]))
        if obj.startswith(namespace):
            problems.append("%s: object %s is this project's own term; a "
                            "crosswalk relates it to another vocabulary"
                            % (line, row["object_id"]))
        elif obj.startswith(upstream):
            problems.append(
                "%s: object %s is a term of a pinned upstream. A term related "
                "to BFO or CCO is placed under it (rdfs:subClassOf) or is "
                "it -- an axiom in a module, not a mapping"
                % (line, row["object_id"]))
        if predicate not in PREDICATES:
            problems.append("%s: predicate %s is not a SKOS mapping property "
                            "or owl:equivalentClass" % (line,
                                                        row["predicate_id"]))
        justification = expand(row["mapping_justification"], curie_map) or ""
        if not justification.startswith(SEMAPV):
            problems.append("%s: mapping_justification %r is not a semapv: "
                            "term" % (line, row["mapping_justification"]))
        if predicate in STRICT and subject in kinds:
            stated = (row.get("object_type") or "").strip()
            if not stated:
                problems.append(
                    "%s: %s needs object_type, so a class is never matched "
                    "exactly to a concept" % (line, row["predicate_id"]))
            elif stated != kinds[subject]:
                problems.append(
                    "%s: %s between a %s and a %s; exact matches and "
                    "equivalences are between things of one kind"
                    % (line, row["predicate_id"], kinds[subject], stated))
            if predicate == OWL + "equivalentClass" and \
                    kinds[subject] != "owl class":
                problems.append("%s: owl:equivalentClass from a %s"
                                % (line, kinds[subject]))
    return problems


def mapping_files() -> list[Path]:
    out = []
    for entry in layout.components(ROLE):
        out.extend(entry.members("*.sssom.tsv"))
    return out


def check(paths: list[Path], modules: list[Path] | None = None) -> dict:
    kinds = authored_kinds(modules if modules is not None
                           else layout.ontology_files())
    upstream = upstream_namespaces()
    findings, rows = [], 0
    for path in paths:
        findings.extend(check_file(path, kinds, upstream))
        rows += len(read(path)[1])
    return {"files": [p.name for p in paths], "rows": rows,
            "findings": findings, "ok": not findings}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="*")
    args = ap.parse_args(argv)
    paths = [Path(f) for f in args.files] or mapping_files()
    try:
        record = check(paths)
    except Unreadable as error:
        print("  CANNOT READ: %s" % error, file=sys.stderr)
        return 2
    for finding in record["findings"]:
        print("  FINDING: %s" % finding)
    if not paths:
        print("  no mapping sets yet")
    else:
        print("  %d mapping set(s), %d mapping(s), %d finding(s)"
              % (len(paths), record["rows"], len(record["findings"])))
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
