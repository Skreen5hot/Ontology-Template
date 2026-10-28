# SPDX-License-Identifier: MIT
"""Generate the annotation-profile shapes from config/annotation-profile.yaml.

    python tools/ontology/profile_shapes.py            # rewrite the shapes
    python tools/ontology/profile_shapes.py --check    # exit 1 if stale

Generated rather than written, because the shapes have to name the
project namespace in a SPARQL target, which no shape can read from the
project file, and because a profile a reviewer edits as YAML is one they
can read. tests/test_ontology_checks.py compares the committed shapes
with a fresh generation.

A property must be a term of a pinned upstream -- checked against the
registers, as the IRI linter would -- or of a W3C or Dublin Core
vocabulary. A profile naming an annotation nobody defines would be
satisfied by a typo.

AGREE ACROSS MODULES (T8)

`agree_across_modules` lists the annotation properties a term may carry
only one value of per language, however many modules state it. A module
that inlines another's term carries a copy of its text, and the copies
drift: the BPO port had 110 term-and-property pairs whose comments,
definitions or labels differed between modules, and only the labels and
definitions were checked. Each listed property gets a drift constraint
here, on every authored term, class or property, except rdfs:label and
skos:definition: the wellformedness shapes check those as the term
contract, which cannot be turned off, so the list must name them and
they generate nothing twice.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402
import project  # noqa: E402

GENERATOR = "tools/ontology/profile_shapes.py"
PROFILE = "config/annotation-profile.yaml"
OUTPUT = "shapes/annotation_profile_shapes.ttl"
PINS = "config/upstream-sources.yaml"

STANDARD = ("http://www.w3.org/", "http://purl.org/dc/")

#: Checked by the wellformedness shapes as the term contract.
CONTRACT = ("http://www.w3.org/2000/01/rdf-schema#label",
            "http://www.w3.org/2004/02/skos/core#definition")
SEVERITIES = {"violation": "sh:Violation", "warning": "sh:Warning"}


class Refused(SystemExit):
    """The profile names something that cannot be checked."""


def agreement(root: Path) -> list[dict]:
    """The `agree_across_modules` entries, checked: each a property of a
    known vocabulary, with a label, a severity and a reason, and the term
    contract's two among them."""
    import yaml

    raw = yaml.safe_load((root / PROFILE).read_text(encoding="utf-8")) or {}
    entries = raw.get("agree_across_modules") or []
    known = upstream_terms(root)
    seen = set()
    for number, entry in enumerate(entries, 1):
        for key in ("property", "label", "severity", "why"):
            if not entry.get(key):
                raise Refused("%s: agree_across_modules entry %d declares "
                              "no %r" % (PROFILE, number, key))
        if entry["severity"] not in SEVERITIES:
            raise Refused("%s: agree_across_modules entry %d severity %r is "
                          "not %s" % (PROFILE, number, entry["severity"],
                                      " or ".join(SEVERITIES)))
        iri = entry["property"]
        if iri in seen:
            raise Refused("%s: agree_across_modules names %s twice"
                          % (PROFILE, iri))
        seen.add(iri)
        if not (iri.startswith(STANDARD) or iri in known):
            raise Refused("%s: agree_across_modules names %s, which is not a "
                          "term of any pinned upstream and not a W3C or Dublin "
                          "Core IRI" % (PROFILE, iri))
        if iri in CONTRACT and entry["severity"] != "violation":
            raise Refused("%s: %s is part of the term contract, checked as a "
                          "violation by the wellformedness shapes; it cannot "
                          "be made a %s here" % (PROFILE, entry["label"],
                                                 entry["severity"]))
    missing = [iri for iri in CONTRACT if iri not in seen]
    if missing:
        raise Refused("%s: agree_across_modules must name %s. They are the "
                      "term contract and are checked whatever this list "
                      "says; leaving them out would make it say otherwise"
                      % (PROFILE, " and ".join(missing)))
    return entries


def profile(root: Path) -> list[dict]:
    import yaml

    raw = yaml.safe_load((root / PROFILE).read_text(encoding="utf-8")) or {}
    entries = raw.get("annotations") or []
    if not entries:
        raise Refused(
            PROFILE + " lists no annotation. An empty profile would generate "
            "a shape set with nothing in it, which no fixture can make fail; "
            "remove the validation.annotation-profile component instead.")
    known = upstream_terms(root)
    seen = set()
    for number, entry in enumerate(entries, 1):
        for key in ("property", "label", "severity", "why"):
            if not entry.get(key):
                raise Refused("%s: entry %d declares no %r"
                              % (PROFILE, number, key))
        if entry["severity"] not in SEVERITIES:
            raise Refused("%s: entry %d severity %r is not %s"
                          % (PROFILE, number, entry["severity"],
                             " or ".join(SEVERITIES)))
        iri = entry["property"]
        if iri in seen:
            raise Refused("%s names %s twice" % (PROFILE, iri))
        seen.add(iri)
        if not (iri.startswith(STANDARD) or iri in known):
            raise Refused(
                "%s: %s is not a term of any pinned upstream and not a W3C or "
                "Dublin Core IRI, so a profile requiring it would be "
                "satisfied by whatever happens to be spelled that way"
                % (PROFILE, iri))
    return entries


def upstream_terms(root: Path) -> set:
    import yaml

    pins = yaml.safe_load((root / PINS).read_text(encoding="utf-8")) or {}
    found = set()
    for entry in pins.get("sources") or []:
        path = root / entry["register"]
        if path.is_file():
            found |= set(json.loads(path.read_text(encoding="utf-8"))["terms"])
    return found


def shapes_text(entries: list[dict], agree: list[dict] | None = None) -> str:
    namespace = project.namespace()
    base = project.iri_base()
    lines = [
        "@prefix sh:   <http://www.w3.org/ns/shacl#> .",
        "@prefix owl:  <http://www.w3.org/2002/07/owl#> .",
        "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .",
        "@prefix ap:   <%s/shapes/annotation-profile#> ." % base,
        "",
        "# Generated by %s from %s -- do not edit." % (GENERATOR, PROFILE),
        "#",
        "# One property shape per annotation the project requires on every",
        "# authored class, beyond the label and definition the wellformedness",
        "# shapes already require.",
        "",
        "ap:prefixes",
        "    a owl:Ontology ;",
        "    sh:declare",
        "        [ sh:prefix \"owl\" ; sh:namespace "
        "\"http://www.w3.org/2002/07/owl#\"^^xsd:anyURI ] .",
        "",
        "ap:AuthoredClassProfileShape",
        "    a sh:NodeShape ;",
        "    sh:target [",
        "        a sh:SPARQLTarget ;",
        "        sh:prefixes ap:prefixes ;",
        "        sh:select \"\"\"SELECT ?this WHERE {",
        "          ?this a owl:Class .",
        "          FILTER(STRSTARTS(STR(?this), \"%s\"))" % namespace,
        "        }\"\"\" ] ;",
    ]
    for number, entry in enumerate(entries):
        why = " ".join(entry["why"].split()).replace('"', "'")
        end = " ." if number == len(entries) - 1 else " ;"
        lines += [
            "",
            "    # %s" % entry["label"],
            "    sh:property [",
            "        sh:path <%s> ;" % entry["property"],
            "        sh:minCount 1 ;",
            "        sh:severity %s ;" % SEVERITIES[entry["severity"]],
            "        sh:message \"Class has no %s. %s\" ]%s"
            % (entry["label"].replace('"', "'"), why, end),
        ]
    drift = [e for e in agree or [] if e["property"] not in CONTRACT]
    if drift:
        lines += [
            "",
            "# Agree across modules: one value per language, on every authored",
            "# term. rdfs:label and skos:definition are listed too, and checked",
            "# by the wellformedness shapes. One node shape per property, because",
            "# a SPARQL constraint takes its severity from its node shape.",
        ]
    for number, entry in enumerate(drift, 1):
        why = " ".join(entry["why"].split()).replace('"', "'")
        lines += [
            "",
            "# %s" % entry["label"],
            "ap:AuthoredTermAgreementShape%d" % number,
            "    a sh:NodeShape ;",
            "    sh:severity %s ;" % SEVERITIES[entry["severity"]],
            "    sh:target [",
            "        a sh:SPARQLTarget ;",
            "        sh:prefixes ap:prefixes ;",
            "        sh:select \"\"\"SELECT ?this WHERE {",
            "          ?this a ?type .",
            "          FILTER(?type IN (owl:Class, owl:ObjectProperty,",
            "                           owl:DatatypeProperty, "
            "owl:AnnotationProperty))",
            "          FILTER(STRSTARTS(STR(?this), \"%s\"))" % namespace,
            "        }\"\"\" ] ;",
            "    sh:sparql [",
            "        a sh:SPARQLConstraint ;",
            "        sh:message \"Term {$this} carries two different %s "
            "values in the same language. %s\" ;"
            % (entry["label"].replace('"', "'"), why),
            "        sh:prefixes ap:prefixes ;",
            "        sh:select \"\"\"SELECT $this WHERE {",
            "          $this <%s> ?a, ?b ." % entry["property"],
            "          FILTER(isLiteral(?a) && isLiteral(?b))",
            "          FILTER(STR(?a) < STR(?b))",
            "          FILTER(LANG(?a) = LANG(?b)) }\"\"\" ] .",
        ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    root = layout.repository_root()
    text = shapes_text(profile(root), agreement(root)).encode("utf-8")
    target = root / OUTPUT
    if args.check:
        if not target.is_file() or target.read_bytes() != text:
            print("  STALE: %s is not what %s generates from %s. Run python %s"
                  % (OUTPUT, GENERATOR, PROFILE, GENERATOR))
            return 1
        print("  %s is current" % OUTPUT)
        return 0
    target.write_bytes(text)
    print("  wrote %s" % OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
