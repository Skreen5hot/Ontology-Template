# SPDX-License-Identifier: MIT
"""The reasoner, run: ROBOT with ELK over the full pinned upstreams.

Marked `reasoning`: these need Java and the pinned ROBOT jar. The
Reasoning workflow runs them; the Checks workflow deselects them by that
marker, in its own command line, rather than letting them skip -- a skip
reads as a pass. Locally they run whenever `pytest tests/` does, and fail
loudly without Java.

The fixtures are in tests/fixtures/reasoning/, with `{{namespace}}` and
`{{iri_base}}` filled in on the way to a temporary directory. The
reading of ROBOT's output, which needs no JVM, is tested in
tests/test_release.py with the rest of the pure-Python tooling.
"""

from __future__ import annotations

import pytest

from conftest import load_tool

pytestmark = pytest.mark.reasoning

FIXTURES = "tests/fixtures/reasoning"


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_reason", "tools/ontology/reason.py")


@pytest.fixture(scope="module")
def written(repo, project, tmp_path_factory):
    target = tmp_path_factory.mktemp("reasoning")
    out = {}
    for source in sorted((repo / FIXTURES).glob("*.ttl")):
        text = source.read_bytes().decode("utf-8")
        text = text.replace("{{namespace}}", project.namespace())
        text = text.replace("{{iri_base}}", project.iri_base())
        path = target / source.name
        path.write_bytes(text.encode("utf-8"))
        out[source.stem] = path
    return out


def test_the_ontology_is_consistent_and_nothing_is_unsatisfiable(tool):
    record = tool.reason()
    assert record["ok"], record
    assert record["upstream_files"], "no upstream file was reasoned over"
    assert {"bfo.ttl", "cco.ttl"} <= set(record["upstream_files"])


def test_an_unsatisfiable_class_is_named(tool, written, project):
    """Both cases the realist shapes also catch -- one through a named
    disjointness, one through BFO's AllDisjointClasses, which the reasoner
    reads from the full upstream -- and not the class that is fine."""
    record = tool.reason(modules=[written["unsatisfiable"]], examples=[])
    assert record["ok"] is False
    assert record["consistent"] is True
    assert sorted(record["unsatisfiable_authored"]) == [
        project.namespace() + "ContinuantAndOccurrent",
        project.namespace() + "IndependentAndDependent"]
    assert record["unsatisfiable_upstream"] == [], (
        "the pinned BFO and CCO have unsatisfiable classes of their own")


def test_the_positive_control_reasons_clean(tool, written):
    record = tool.reason(modules=[written["consistent"]], examples=[])
    assert record["ok"], record


def test_an_inconsistent_example_is_reported_as_the_examples(tool, written):
    """The terminology is fine; the example individual is what cannot
    exist. Reported against the examples, in the second pass, not as an
    inconsistent ontology."""
    record = tool.reason(modules=[written["consistent"]],
                         examples=[written["inconsistent-example"]])
    assert record["consistent"] is True
    assert record["unsatisfiable_authored"] == []
    assert record["examples_consistent"] is False
    assert record["ok"] is False


def test_the_command_exits_1_on_a_finding(tool, written, monkeypatch):
    real = tool.reason
    monkeypatch.setattr(tool, "reason", lambda: real(
        modules=[written["unsatisfiable"]], examples=[]))
    assert tool.main([]) == 1
