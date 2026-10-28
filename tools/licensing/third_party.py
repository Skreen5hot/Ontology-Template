# SPDX-License-Identifier: MIT
"""Third-party text inside the ontology: what a project declares of it.

    python tools/licensing/third_party.py      # the declarations, checked

The licensing disposition is per file, and a module holding quotations
from somebody else's framework is still one file under the project's own
licence. The BPO port published 3,757 verbatim passages of a third-party
framework in modules licensed MIT, and the per-file check passed them
(BPO evaluation, T9). Nothing can find such text unasked: a quotation is
a string like any other. So a project declares the annotation properties
that carry it, in config/third-party-text.yaml, and the declaration is
what the checks hold the modules to:

  property     the annotation property's IRI
  source       the work the text is taken from, as the module header
               names it in dcterms:source
  release      the release of that work the text is taken from, named
               in the same dcterms:source value (T23)
  licence      the licence the project has been told the text is under:
               an SPDX identifier, or "unknown"
  attribution  the attribution or notice the project has been told is
               required, carried verbatim in the header's dcterms:rights

tools/ontology/validate.py fails a module that holds such text and whose
header does not name the source and release, or does not carry the
attribution. tools/licensing/disposition.py lists the text apart from the
module's own licence.

WHAT THIS IS NOT

It records what a project was told and checks that it is present. It does
not decide whether the text may be redistributed, or on what terms, and
the template ships no declaration, licence or attribution of its own. That
is Legal's to say; the request is
communications/legal/outgoing/2026-10-28-t9-third-party-text.md, and the
sentence below is held until Legal answers it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import layout  # noqa: E402

DECLARATIONS = "config/third-party-text.yaml"
FIELDS = ("property", "source", "release", "licence", "attribution")
SPDX = re.compile(r"^[A-Za-z0-9.+\-]+$")

#: What a report about third-party text may claim. Pending Legal (the
#: request named in the docstring): the template's proposed wording, not
#: Legal's, and marked as such wherever it is shown.
STATEMENT = (
    "PENDING LEGAL (EXAMPLE-LEGAL-2026-10-28-t9-third-party-text): proposed "
    "wording, not yet Legal's. This report records what the project "
    "declares about third-party text and checks that the declared source, "
    "release and attribution are present. It does not judge whether the "
    "text may be redistributed.")


class Refused(SystemExit):
    """The declarations cannot be read as declarations."""


def load(root: Path | None = None) -> list[dict]:
    """The declarations, checked; [] when the project declares none."""
    import yaml

    path = (root or layout.repository_root()) / DECLARATIONS
    if not path.is_file():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = raw.get("declarations") or []
    seen = set()
    for number, entry in enumerate(entries, 1):
        missing = [f for f in FIELDS
                   if not str(entry.get(f) or "").strip()]
        if missing:
            raise Refused("%s: declaration %d has no %s"
                          % (DECLARATIONS, number, ", ".join(missing)))
        if entry["licence"] != "unknown" and not SPDX.match(entry["licence"]):
            raise Refused("%s: declaration %d licence %r is neither an SPDX "
                          "identifier nor \"unknown\""
                          % (DECLARATIONS, number, entry["licence"]))
        if entry["property"] in seen:
            raise Refused("%s declares %s twice"
                          % (DECLARATIONS, entry["property"]))
        seen.add(entry["property"])
    return entries


def values_in(graph, declaration: dict) -> int:
    """How many values of the declared property the graph holds."""
    import rdflib

    return sum(1 for _ in graph.subject_objects(
        rdflib.URIRef(declaration["property"])))


def main(argv=None) -> int:
    entries = load()
    print("  %s: %d declaration(s)" % (DECLARATIONS, len(entries)))
    for entry in entries:
        print("    %s  from %s %s, licence as declared: %s"
              % (entry["property"], entry["source"], entry["release"],
                 entry["licence"]))
    print("  " + STATEMENT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
