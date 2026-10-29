# SPDX-License-Identifier: MIT
"""The porting guide and its form (T17, T21), and what they promise.

docs/PORTING.md gives a lossless check as code for a port to adapt. Code
in a document is not run by anything, so it is run here: an exact port
compares equal, and a lost restriction, a lost list member or a lost
blank-node axiom with no subject compares unequal.
"""

from __future__ import annotations

import re

import pytest

GUIDE = "docs/PORTING.md"
FORM = "docs/porting/port-report.md"

OLD = "https://example.org/old#"
NEW = "https://example.org/new#"
SOURCE = """
@prefix o: <https://example.org/old#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
o:A rdfs:subClassOf [ a owl:Restriction ; owl:onProperty o:p ;
                      owl:someValuesFrom o:B ] .
o:C rdfs:subClassOf [ a owl:Restriction ; owl:onProperty o:p ;
                      owl:someValuesFrom o:B ] .
[] a owl:AllDisjointClasses ; owl:members ( o:A o:B o:C ) .
"""


@pytest.fixture(scope="module")
def check(repo):
    """The guide's code, run as written."""
    text = (repo / GUIDE).read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    assert len(blocks) == 1, "the guide should hold one Python block"
    namespace: dict = {}
    exec(blocks[0], namespace)
    return namespace


def port_of(text):
    from rdflib import Graph

    return Graph().parse(data=text.replace(OLD, NEW), format="turtle")


def test_an_exact_port_compares_equal(check):
    from rdflib import Graph

    source = Graph().parse(data=SOURCE, format="turtle")
    renamed = check["renamed"](source, OLD, NEW)
    assert check["statements"](renamed) == check["statements"](
        port_of(SOURCE))


@pytest.mark.parametrize("lose, keep", [
    ("o:C rdfs:subClassOf [ a owl:Restriction ; owl:onProperty o:p ;\n"
     "                      owl:someValuesFrom o:B ] .", ""),
    ("( o:A o:B o:C )", "( o:A o:B )"),
    ("[] a owl:AllDisjointClasses ; owl:members ( o:A o:B o:C ) .", ""),
])
def test_a_loss_is_seen(check, lose, keep):
    assert lose in SOURCE
    whole = check["statements"](port_of(SOURCE))
    assert check["statements"](port_of(SOURCE.replace(lose, keep))) != whole


def test_the_form_asks_for_what_the_guide_requires(repo):
    """The form records the evidence the guide asks for: the template
    commit (T21), the lossless count, the first findings, and the
    template files a port had to change."""
    form = (repo / FORM).read_text(encoding="utf-8")
    for asked in ("template_commit", "Losslessness", "## 4. What the checks found",
                  "python tools/template_status.py", "research/port-report.md"):
        assert asked in form, asked
    guide = (repo / GUIDE).read_text(encoding="utf-8")
    assert "porting/port-report.md" in guide


def test_the_guide_maps_new_to_old(repo):
    """The mapping checker requires the subject to be a term declared
    here, so the guide must not tell a port to write old -> new."""
    guide = (repo / GUIDE).read_text(encoding="utf-8")
    assert "**Direction: new to old.**" in guide
