# SPDX-License-Identifier: MIT
"""Release artefacts, and the parts of the reasoner that need no JVM.

The release: two builds of one version are byte-identical across
processes and hash seeds; each file is the graph it was written from in
all three serialisations; the base carries no upstream axiom and the full
says it is partial and attributes what it carries. Exercised on the live
module -- a header -- and on the realist fixture as a stand-in module, for
the blank nodes, language tags and typed literals a header does not have.

The reasoner wrapper: how ROBOT's output is read, every branch, from
constructed logs; and a jar that is not the pinned one is refused.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys

import pytest

from conftest import load_tool

OBO = "http://purl.obolibrary.org/obo/"


@pytest.fixture(scope="module")
def release():
    return load_tool("t_release", "tools/release.py")


@pytest.fixture(scope="module")
def built(release, tmp_path_factory, project):
    out = tmp_path_factory.mktemp("release")
    names = release.build("1.2.3", out)
    return out / ("%s-1.2.3" % project.project_id()), names


def graph_of(path, fmt):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(path, format=fmt)
    return graph


def build_in_subprocess(repo, out, seed, modules=None):
    script = (
        "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r)\n"
        "from pathlib import Path\n"
        "import importlib.util\n"
        "spec = importlib.util.spec_from_file_location('r', %r)\n"
        "r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)\n"
        "r.build('1.2.3', Path(%r), modules=%s)\n"
        % (str(repo / "tools"), str(repo), str(repo / "tools/release.py"),
           str(out), "None" if modules is None
           else "[Path(%r)]" % str(modules)))
    result = subprocess.run([sys.executable, "-c", script], cwd=str(repo),
                            capture_output=True,
                            env={**__import__("os").environ,
                                 "PYTHONHASHSEED": str(seed)})
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")


def tree(path):
    return {p.relative_to(path).as_posix(): p.read_bytes()
            for p in sorted(path.rglob("*")) if p.is_file()}


# ------------------------------------------------------------- the files


def test_every_artefact_is_built_and_summed(built, project):
    target, names = built
    pid = project.project_id()
    want = {"%s-%s.%s" % (pid, v, s) for v in ("base", "full")
            for s in ("ttl", "owl", "jsonld")} | {"NOTICE.md", "LICENSE",
                                                  "SHA256SUMS"}
    assert set(names) == want
    sums = dict(line.split("  ")[::-1] for line in
                (target / "SHA256SUMS").read_text(encoding="utf-8")
                .splitlines())
    assert set(sums) == want - {"SHA256SUMS"}
    for name, digest in sums.items():
        assert hashlib.sha256((target / name).read_bytes()).hexdigest() \
            == digest, name


def test_the_three_serialisations_are_one_graph(built, project):
    from rdflib.compare import isomorphic

    target, _ = built
    for variant in ("base", "full"):
        stem = target / ("%s-%s" % (project.project_id(), variant))
        ttl = graph_of(stem.with_suffix(".ttl"), "turtle")
        assert isomorphic(ttl, graph_of(stem.with_suffix(".owl"), "xml"))
        assert isomorphic(ttl, graph_of(stem.with_suffix(".jsonld"),
                                        "json-ld"))


def test_the_header_carries_the_version(built, project):
    import rdflib

    target, _ = built
    pid = project.project_id()
    for variant in ("base", "full"):
        graph = graph_of(target / ("%s-%s.ttl" % (pid, variant)), "turtle")
        heads = list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
        assert [str(h) for h in heads] == [
            "%s/%s-%s" % (project.iri_base(), pid, variant)], heads
        head = heads[0]
        assert str(graph.value(head, rdflib.OWL.versionIRI)) == \
            "%s/1.2.3/%s-%s" % (project.iri_base(), pid, variant)
        assert str(graph.value(head, rdflib.OWL.versionInfo)) == "1.2.3"
        for predicate in ("title", "license", "creator", "description"):
            assert graph.value(head, rdflib.URIRef(
                "http://purl.org/dc/terms/" + predicate)) is not None, (
                variant, predicate)


def test_the_base_carries_no_upstream_axiom(built, project):
    target, _ = built
    graph = graph_of(target / ("%s-base.ttl" % project.project_id()), "turtle")
    upstream = [s for s in graph.subjects() if str(s).startswith(
        (OBO, "https://www.commoncoreontologies.org/"))]
    assert upstream == [], upstream[:5]


def test_the_full_release_carries_the_extracts_and_says_they_are_partial(
        built, project):
    import rdflib

    target, _ = built
    pid = project.project_id()
    graph = graph_of(target / ("%s-full.ttl" % pid), "turtle")
    assert (rdflib.URIRef(OBO + "BFO_0000015"), rdflib.RDF.type,
            rdflib.OWL.Class) in graph
    assert (rdflib.URIRef(OBO + "BFO_0000004"), rdflib.OWL.disjointWith,
            rdflib.URIRef(OBO + "BFO_0000020")) in graph, (
        "the derived disjointness is not in the full release")
    head = rdflib.URIRef("%s/%s-full" % (project.iri_base(), pid))
    comment = str(graph.value(head, rdflib.RDFS.comment))
    assert "PARTIAL" in comment and "CC BY 4.0" in comment \
        and "BSD-3-Clause" in comment, comment
    assert (target / "NOTICE.md").read_text(encoding="utf-8").startswith(
        "# Third-party notices")
    heads = list(graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology))
    assert len(heads) == 1, "an extract's own header survived: %s" % heads


def test_two_builds_are_byte_identical_across_hash_seeds(repo, tmp_path):
    build_in_subprocess(repo, tmp_path / "a", 1)
    build_in_subprocess(repo, tmp_path / "b", 2)
    first, second = tree(tmp_path / "a"), tree(tmp_path / "b")
    assert first and first == second, sorted(
        k for k in first if first.get(k) != second.get(k))


def test_blank_nodes_and_literals_survive_and_stay_deterministic(
        repo, tmp_path, layout):
    """The live module is a header; the realist fixture, as a stand-in
    module, has restrictions, language tags and booleans. RDF/XML and
    JSON-LD are written by this tool, and those are what rdflib could not
    make deterministic."""
    fixture = layout.path("fixture.realist-bad-examples")
    build_in_subprocess(repo, tmp_path / "a", 1, modules=fixture)
    build_in_subprocess(repo, tmp_path / "b", 7, modules=fixture)
    first, second = tree(tmp_path / "a"), tree(tmp_path / "b")
    assert first == second
    owl = next(v for k, v in first.items() if k.endswith("-base.owl"))
    assert b"rdf:nodeID" in owl and b"xml:lang" in owl


@pytest.mark.parametrize("version", ["1.2", "v1.2.3", "1.2.3.4", "latest"])
def test_a_version_that_is_not_semver_is_refused(release, tmp_path, version):
    with pytest.raises(SystemExit) as error:
        release.build(version, tmp_path)
    assert "MAJOR.MINOR.PATCH" in str(error.value)
    assert not any(tmp_path.iterdir()), "a refused build wrote files"


# ---------------------------------------- the reasoner, without a JVM


@pytest.fixture(scope="module")
def reason():
    return load_tool("t_reason_pure", "tools/ontology/reason.py")


def test_robots_answers_are_read(reason):
    assert reason.read_robot(0, "") == {"consistent": True,
                                        "unsatisfiable": []}
    log = ("ERROR ReasonerHelper - There are 2 unsatisfiable classes in the "
           "ontology.\nERROR ReasonerHelper -     unsatisfiable: https://x/a\n"
           "ERROR ReasonerHelper -     unsatisfiable: https://x/b\n")
    assert reason.read_robot(1, log) == {
        "consistent": True, "unsatisfiable": ["https://x/a", "https://x/b"]}
    assert reason.read_robot(1, "ERROR - The ontology is inconsistent. TIP")[
        "consistent"] is False


@pytest.mark.parametrize("code, log, expect", [
    (1, "There are 3 unsatisfiable classes\nunsatisfiable: https://x/a\n",
     "may have changed"),
    (1, "Exception in thread main java.lang.OutOfMemoryError", "without "
     "saying why"),
    (0, "unsatisfiable: https://x/a", "exited 0 and named"),
])
def test_an_answer_robot_did_not_give_is_refused(reason, code, log, expect):
    """A changed log format must not read as "nothing unsatisfiable"."""
    with pytest.raises(reason.Unrunnable) as error:
        reason.read_robot(code, log)
    assert expect in str(error.value)


def test_a_jar_that_is_not_the_pinned_one_is_refused(reason, tmp_path):
    fake = tmp_path / "robot.jar"
    fake.write_bytes(b"not robot")
    pin = {"version": "1.9.10", "url": fake.as_uri(), "sha256": "0" * 64}
    with pytest.raises(reason.Unrunnable) as error:
        reason.fetch_jar(pin, tmp_path / "cache")
    assert "Refusing to run a reasoner that is not the pinned one" in str(
        error.value)
    assert not list((tmp_path / "cache").glob("*.jar"))


def test_the_pin_names_its_release(reason):
    pins = reason.config()
    robot = pins["robot"]
    assert "v%s" % robot["version"] in robot["url"]
    assert len(robot["sha256"]) == 64 and len(robot["tag_commit"]) == 40
    assert pins["reasoner"] in ("ELK", "HermiT")
