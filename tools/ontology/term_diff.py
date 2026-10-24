# SPDX-License-Identifier: MIT
"""What changed in the authored terms between two commits, term by term.

    python tools/ontology/term_diff.py --base origin/main          # to the working tree
    python tools/ontology/term_diff.py --base v1.1.0 --head v1.2.0
    python tools/ontology/term_diff.py --head v1.0.0               # no base: all added
    python tools/ontology/term_diff.py --base main --format json

A line diff of a module says which lines moved; after a Protégé save,
that is most of them. This says which terms were added, removed,
deprecated, or changed -- label, definition, parents, type, replacement
-- each with what it was and what it is. The Term diff workflow posts it
on a pull request; the Release workflow ships it as CHANGES.md.

Each side is read at its own commit: the layout contract at that ref
names its modules, and each module is read with `git show`. A module
added or removed between the two is therefore handled, and a ref that
predates the contract has no terms. The project namespace is today's;
a namespace change between the refs shows as every term removed and
added, which is what it is.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

MODULE_ROLES = ("ontology-module", "ontology-module-set")
RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS = "http://www.w3.org/2000/01/rdf-schema#"
OWL = "http://www.w3.org/2002/07/owl#"
SKOS = "http://www.w3.org/2004/02/skos/core#"
DCTERMS = "http://purl.org/dc/terms/"

FIELDS = {
    "types": RDF + "type",
    "labels": RDFS + "label",
    "pref_labels": SKOS + "prefLabel",
    "definitions": SKOS + "definition",
    "parents": RDFS + "subClassOf",
    "broader": SKOS + "broader",
    "replaced_by": DCTERMS + "isReplacedBy",
}


class Refused(SystemExit):
    """A ref that does not exist, or a module that does not parse."""


def git(root: Path, *args: str) -> tuple[int, bytes]:
    result = subprocess.run(["git", *args], cwd=str(root),
                            capture_output=True)
    return result.returncode, result.stdout


def modules_at(root: Path, ref: str) -> dict[str, bytes]:
    """{path: bytes} for every module the contract at `ref` declares."""
    import yaml

    code, _ = git(root, "rev-parse", "--verify", ref + "^{commit}")
    if code:
        raise Refused("%s is not a commit here" % ref)
    code, data = git(root, "show", "%s:config/repository-layout.yaml" % ref)
    if code:
        return {}
    contract = yaml.safe_load(data.decode("utf-8")) or {}
    paths = []
    for entry in contract.get("components") or []:
        if entry.get("role") not in MODULE_ROLES:
            continue
        code, listing = git(root, "ls-tree", "-r", "--name-only", ref, "--",
                            entry["path"])
        paths.extend(p for p in listing.decode("utf-8").splitlines()
                     if p.endswith(".ttl"))
    out = {}
    for path in sorted(set(paths)):
        code, data = git(root, "show", "%s:%s" % (ref, path))
        if code == 0:
            out[path] = data
    return out


def modules_now() -> dict[str, bytes]:
    root = layout.repository_root()
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in layout.ontology_files()}


def terms_of(files: dict[str, bytes], namespace: str) -> dict[str, dict]:
    """{term IRI: {field: sorted values, deprecated: bool}}."""
    import rdflib

    graph = rdflib.Graph()
    for path, data in files.items():
        try:
            graph.parse(data=data.decode("utf-8"), format="turtle")
        except Exception as error:  # rdflib raises several types
            raise Refused("%s does not parse: %s" % (
                path, " ".join(str(error).split())[:200]))
    out = {}
    for subject in set(graph.subjects(rdflib.RDF.type, None)):
        iri = str(subject)
        if not isinstance(subject, rdflib.URIRef) or not iri.startswith(
                namespace):
            continue
        record = {}
        for field, predicate in FIELDS.items():
            values = []
            for obj in graph.objects(subject, rdflib.URIRef(predicate)):
                if isinstance(obj, rdflib.BNode):
                    continue
                if isinstance(obj, rdflib.Literal) and obj.language:
                    values.append("%s@%s" % (obj, obj.language))
                else:
                    values.append(str(obj))
            record[field] = sorted(values)
        record["deprecated"] = any(
            str(o).lower() == "true"
            for o in graph.objects(subject, rdflib.URIRef(OWL + "deprecated")))
        out[iri] = record
    return out


def diff(before: dict, after: dict) -> dict:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    deprecated, changed = [], []
    for iri in sorted(set(before) & set(after)):
        old, new = before[iri], after[iri]
        if new["deprecated"] and not old["deprecated"]:
            deprecated.append(iri)
        fields = {f: {"was": old[f], "now": new[f]} for f in FIELDS
                  if old[f] != new[f]}
        if fields:
            changed.append({"term": iri, "fields": fields})
    return {"added": added, "removed": removed, "deprecated": deprecated,
            "changed": changed}


def short(iri: str) -> str:
    namespace = project.namespace()
    if iri.startswith(namespace):
        return "%s:%s" % (project.prefix(), iri[len(namespace):])
    return "<%s>" % iri


def label_of(terms: dict, iri: str) -> str:
    record = terms.get(iri) or {}
    names = record.get("labels") or record.get("pref_labels") or []
    return names[0].rsplit("@", 1)[0] if names else ""


def markdown(result: dict, before: dict, after: dict, base: str,
             head: str) -> str:
    counts = (len(result["added"]), len(result["removed"]),
              len(result["changed"]), len(result["deprecated"]))
    lines = ["## Terms: %d added, %d removed, %d changed, %d deprecated"
             % counts, "", "`%s` → `%s`" % (base or "(nothing)", head), ""]
    if not any(counts):
        lines.append("No authored term changed.")
        return "\n".join(lines) + "\n"
    if result["added"]:
        lines += ["### Added", "", "| Term | Label | Parents |", "|---|---|---|"]
        for iri in result["added"]:
            lines.append("| `%s` | %s | %s |" % (
                short(iri), label_of(after, iri),
                ", ".join("`%s`" % short(p) for p in after[iri]["parents"])))
        lines.append("")
    if result["removed"]:
        lines += ["### Removed", "", "| Term | Label |", "|---|---|"]
        for iri in result["removed"]:
            lines.append("| `%s` | %s |" % (short(iri), label_of(before, iri)))
        lines.append("")
    if result["deprecated"]:
        lines += ["### Deprecated", "", "| Term | Replaced by |", "|---|---|"]
        for iri in result["deprecated"]:
            lines.append("| `%s` | %s |" % (short(iri), ", ".join(
                "`%s`" % short(r) for r in after[iri]["replaced_by"]) or "--"))
        lines.append("")
    if result["changed"]:
        lines += ["### Changed", "", "| Term | Field | Was | Now |",
                  "|---|---|---|---|"]
        for entry in result["changed"]:
            for field, values in sorted(entry["fields"].items()):
                lines.append("| `%s` | %s | %s | %s |" % (
                    short(entry["term"]), field,
                    "<br>".join(values["was"]) or "--",
                    "<br>".join(values["now"]) or "--"))
        lines.append("")
    return "\n".join(lines)


def run(base: str | None, head: str | None,
        root: Path | None = None) -> tuple[dict, dict, dict]:
    root = root or layout.repository_root()
    namespace = project.namespace()
    before = terms_of(modules_at(root, base), namespace) if base else {}
    after = terms_of(modules_at(root, head) if head else modules_now(),
                     namespace)
    return diff(before, after), before, after


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default=None,
                    help="the commit before; omitted, everything is added")
    ap.add_argument("--head", default=None,
                    help="the commit after; omitted, the working tree")
    ap.add_argument("--format", choices=("markdown", "json"),
                    default="markdown")
    ap.add_argument("-o", "--out", default=None)
    args = ap.parse_args(argv)
    result, before, after = run(args.base, args.head)
    text = (json.dumps(result, indent=2, sort_keys=True) + "\n"
            if args.format == "json"
            else markdown(result, before, after, args.base,
                          args.head or "working tree"))
    if args.out:
        Path(args.out).write_bytes(text.encode("utf-8"))
    else:
        # Bytes, not text: a Windows console encodes stdout as cp1252,
        # which cannot write the arrow in the heading, and the first run
        # of this tool there failed on it.
        sys.stdout.buffer.write(text.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
