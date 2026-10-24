# SPDX-License-Identifier: MIT
"""Generate the vocabulary module from the reviewed rows of vocabulary/terms.tsv.

    python tools/ontology/vocabulary.py           # write ontology/vocabulary.ttl
    python tools/ontology/vocabulary.py --check   # exit 1 if stale or invalid

The intake for people who do not write Turtle: one row per proposed
term, reviewed in a pull request like any other change. A row is a
proposal until a reviewer sets `status: accepted` and signs `reviewed_by`;
only accepted rows are generated, into an ordinary module that every
check -- the shapes, the IRI linter, the reasoner -- reads like any
other. ROBOT templates do the same with more columns; this keeps to what
placing a realist class needs.

COLUMNS

  local_name     the term's local name in the project namespace
  label          its preferred label
  definition     "A(n) <parent> that ..."
  parent         the class it is a kind of: prefix:local (obo:, cco:, the
                 project's prefix) or <full IRI>
  synonyms       alternative labels, separated by " | "
  status         proposed | accepted | rejected
  requested_by   who asked for it
  reviewed_by    who accepted it -- required for accepted
  notes          anything else; not generated

plus one column per entry of config/annotation-profile.yaml, named by
its label with spaces as underscores (`definition_source` by default),
generated as that annotation. The columns come from the profile rather
than being listed twice.

Refused: a missing column, a status that is not one of the three, an
accepted row lacking a label, definition, parent, requester or reviewer,
a local name that is not the convention for a class
(config/naming.yaml) or is used twice, a term another module already
declares, a parent with an unknown prefix. Whether the parent exists is
the IRI linter's question, asked of the generated module.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

GENERATOR = "tools/ontology/vocabulary.py"
INTAKE = "vocabulary/terms.tsv"
OUTPUT = "ontology/vocabulary.ttl"
PROFILE = "config/annotation-profile.yaml"
NAMING = "config/naming.yaml"
BASE_COLUMNS = ("local_name", "label", "definition", "parent", "synonyms",
                "status", "requested_by", "reviewed_by", "notes")
STATUSES = ("proposed", "accepted", "rejected")


class Refused(SystemExit):
    """The intake has a row that cannot be generated."""


def profile_columns(root: Path) -> dict[str, str]:
    """{column name: annotation property IRI}, from the profile."""
    import yaml

    raw = yaml.safe_load((root / PROFILE).read_text(encoding="utf-8")) or {}
    return {"_".join(entry["label"].split()): entry["property"]
            for entry in raw.get("annotations") or []}


def class_pattern(root: Path):
    import yaml

    raw = yaml.safe_load((root / NAMING).read_text(encoding="utf-8")) or {}
    return re.compile(raw["classes"])


def prefixes() -> dict[str, str]:
    import yaml

    pins = yaml.safe_load((layout.repository_root()
                           / "config/upstream-sources.yaml").read_text(
        encoding="utf-8")) or {}
    out = {entry["prefix"]: entry["namespace"]
           for entry in pins.get("sources") or []}
    out[project.prefix()] = project.namespace()
    return out


def expand(value: str, known: dict) -> str | None:
    value = value.strip()
    if value.startswith("<") and value.endswith(">"):
        return value[1:-1]
    match = re.match(r"^([A-Za-z][\w\-]*):(\S+)$", value)
    if match and match.group(1) in known:
        return known[match.group(1)] + match.group(2)
    return None


def rows_of(text: str) -> tuple[list[str], list[dict]]:
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    return list(reader.fieldnames or []), list(reader)


def declared_elsewhere(output: Path) -> set[str]:
    import rdflib

    found = set()
    for path in layout.ontology_files():
        if path.resolve() == output.resolve():
            continue
        graph = rdflib.Graph()
        graph.parse(path, format="turtle")
        found |= {str(s) for s in graph.subjects(rdflib.RDF.type, None)}
    return found


def check(text: str, root: Path, output: Path) -> tuple[list[dict], list[str]]:
    """(accepted rows, problems)."""
    columns, rows = rows_of(text)
    extra = profile_columns(root)
    wanted = list(BASE_COLUMNS) + sorted(extra)
    problems = ["%s lacks the column %r" % (INTAKE, c)
                for c in wanted if c not in columns]
    if problems:
        return [], problems
    pattern = class_pattern(root)
    known = prefixes()
    elsewhere = declared_elsewhere(output)
    seen, accepted = {}, []
    for number, row in enumerate(rows, 2):
        where = "%s line %d" % (INTAKE, number)
        name = (row["local_name"] or "").strip()
        status = (row["status"] or "").strip()
        if status not in STATUSES:
            problems.append("%s: status %r is not one of %s"
                            % (where, status, ", ".join(STATUSES)))
            continue
        if not name:
            problems.append("%s: no local_name" % where)
            continue
        if name in seen:
            problems.append("%s: %s is also line %d" % (where, name,
                                                       seen[name]))
            continue
        seen[name] = number
        if not pattern.match(name):
            problems.append("%s: %s does not follow the class naming "
                            "convention in %s (%s)"
                            % (where, name, NAMING, pattern.pattern))
        if status != "accepted":
            continue
        for column in ("label", "definition", "parent", "requested_by",
                       "reviewed_by"):
            if not (row[column] or "").strip():
                problems.append("%s: %s is accepted and has no %s"
                                % (where, name, column))
        iri = project.namespace() + name
        if iri in elsewhere:
            problems.append("%s: %s is already declared in another module"
                            % (where, name))
        if (row["parent"] or "").strip() and expand(row["parent"],
                                                   known) is None:
            problems.append("%s: parent %r has no known prefix (%s) and is "
                            "not a <full IRI>"
                            % (where, row["parent"], ", ".join(sorted(known))))
        accepted.append(row)
    return accepted, problems


def literal(text: str) -> str:
    escaped = (text.replace("\\", "\\\\").replace('"', '\\"')
               .replace("\n", "\\n").replace("\r", "\\r"))
    return '"%s"@en' % escaped


def module_text(accepted: list[dict], root: Path) -> str:
    import rdflib

    known = prefixes()
    extra = profile_columns(root)
    main = rdflib.Graph()
    main.parse(layout.component("ontology.main").resolve(), format="turtle")
    head = next(main.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
    version = str(main.value(head, rdflib.OWL.versionInfo) or "0.0.0")
    licence = main.value(head, rdflib.URIRef("http://purl.org/dc/terms/license"))
    creator = main.value(head, rdflib.URIRef("http://purl.org/dc/terms/creator"))
    base = project.iri_base()
    lines = [
        "@prefix rdfs:    <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl:     <http://www.w3.org/2002/07/owl#> .",
        "@prefix skos:    <http://www.w3.org/2004/02/skos/core#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix %s: <%s> ." % (project.prefix(), project.namespace()),
        "",
        "# Generated by %s from %s -- do not edit." % (GENERATOR, INTAKE),
        "# Edit the rows, have them reviewed, and regenerate.",
        "",
        "<%s/vocabulary> a owl:Ontology ;" % base,
        "    dcterms:title %s ;" % literal(project.load()["title"]
                                          + ": vocabulary"),
        "    dcterms:license <%s> ;" % licence,
        "    dcterms:creator %s ;" % ('"%s"' % str(creator).replace('"', "'")),
        "    owl:versionIRI <%s/vocabulary/%s> ;" % (base, version),
        "    owl:versionInfo \"%s\" ;" % version,
        "    rdfs:comment \"The accepted rows of %s. Generated.\"@en ." % INTAKE,
    ]
    for row in sorted(accepted, key=lambda r: r["local_name"].strip()):
        name = row["local_name"].strip()
        statements = [
            "a owl:Class",
            "rdfs:label %s" % literal(row["label"].strip()),
            "skos:definition %s" % literal(row["definition"].strip()),
            "rdfs:subClassOf <%s>" % expand(row["parent"], known),
        ]
        for synonym in sorted(s.strip() for s in (row["synonyms"] or "")
                              .split("|") if s.strip()):
            statements.append("skos:altLabel %s" % literal(synonym))
        for column, iri in sorted(extra.items()):
            if (row.get(column) or "").strip():
                statements.append("<%s> %s" % (iri,
                                               literal(row[column].strip())))
        lines.append("")
        lines.append("%s:%s %s ." % (project.prefix(), name,
                                     " ;\n    ".join(statements)))
    return "\n".join(lines) + "\n"


def generate(root: Path) -> bytes:
    output = root / OUTPUT
    text = (root / INTAKE).read_bytes().decode("utf-8")
    accepted, problems = check(text, root, output)
    if problems:
        raise Refused("the intake cannot be generated:\n  "
                      + "\n  ".join(problems))
    return module_text(accepted, root).encode("utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    root = layout.repository_root()
    data = generate(root)
    target = root / OUTPUT
    if args.check:
        if not target.is_file() or target.read_bytes() != data:
            print("  STALE: %s is not what %s generates. Run python %s"
                  % (OUTPUT, INTAKE, GENERATOR))
            return 1
        print("  %s is current" % OUTPUT)
        return 0
    target.write_bytes(data)
    print("  wrote %s" % OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
