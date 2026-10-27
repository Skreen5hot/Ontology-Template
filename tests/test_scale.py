# SPDX-License-Identifier: MIT
"""The checks at a real ontology's size, and the engines that make it possible.

The Business Process Ontology port found that the template's checks were
built and timed on a module with no terms: at 3,119 classes the ladder did
not finish in two hours and a release build not in five. Two changes fixed
that, and each is held here twice -- to the old engine's results, so the
speed was not bought with a different answer, and to a time budget on a
generated corpus a little larger than BPO, so it stays fixed.

  * SPARQL constraints run set-based in Oxigraph
    (tools/ontology/sparql_constraints.py). Held to pyshacl, record for
    record, on every fixture and a small benchmark.
  * Blank nodes are labelled by structure (tools/ontology/canon.py). Held
    to rdflib's canonicalization on every fixture.

The budget tests are marked `scale`, and tests elsewhere whose cost grows
with the live corpus are marked `corpus`. The Checks workflow deselects them;
the Scale workflow runs them on a schedule and on any change to the tools,
the shapes or the pins. The budgets are decision 11's: 15 min for the
ladder and for a release build, on GitHub's standard runner.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time

import pytest

from conftest import load_tool

LADDER_BUDGET = 15 * 60
RELEASE_BUDGET = 15 * 60


@pytest.fixture(scope="module")
def validator():
    return load_tool("t_scale_validate", "tools/ontology/validate.py")


@pytest.fixture(scope="module")
def runner():
    return load_tool("t_scale_sparql", "tools/ontology/sparql_constraints.py")


@pytest.fixture(scope="module")
def canon():
    return load_tool("t_scale_canon", "tools/ontology/canon.py")


@pytest.fixture(scope="module")
def benchmark():
    return load_tool("t_scale_benchmark", "tools/ontology/benchmark.py")


@pytest.fixture(scope="module")
def vendored(validator, layout):
    return validator.load(layout.vendored_files())


def records(result):
    return sorted(tuple(sorted(r.items())) for r in result["violations"])


# ------------------------------------------------ the engines agree


def cases(validator, vendored, benchmark):
    # Not the live corpus: pyshacl, the reference, is the quadratic engine
    # this replaces, and on a project's real ontology the comparison would
    # take the hours the replacement saves. The fixtures and the benchmark
    # are the cases built to make each constraint fire.
    out = {}
    for path in validator.fixtures():
        out["fixture " + path.name] = validator.load([path]) + vendored
    # Small: pyshacl takes about two minutes on 60 classes of it.
    out["benchmark"] = vendored + benchmark.generate(20, 28)
    return out


def test_the_set_based_engine_gives_pyshacls_results(validator, vendored,
                                                     benchmark):
    """Every record -- focus, shape, severity, message -- the same from
    both engines, for every shape set, on every fixture, the corpus, and a
    benchmark with every planted defect. This is what licenses running the
    constraints anywhere but pyshacl."""
    differ = []
    for name, path in sorted(validator.shape_sets().items()):
        shapes = validator.load([path])
        for case, data in cases(validator, vendored, benchmark).items():
            reference = validator.run(data, shapes, engine="pyshacl")
            fast = validator.run(data, shapes, engine="oxigraph")
            if (records(reference) != records(fast)
                    or reference["conforms"] != fast["conforms"]):
                differ.append((name, case))
    assert differ == [], differ


def test_the_comparison_is_not_vacuous(validator, vendored, benchmark):
    """Guards the test above: both engines find the planted defects, so
    agreeing is not agreeing on nothing."""
    data = vendored + benchmark.generate(20, 28)
    found = set()
    for name, path in sorted(validator.shape_sets().items()):
        result = validator.run(data, validator.load([path]))
        for record in result["violations"]:
            for planted, expected in benchmark.PLANTED.items():
                if (record["focus"] or "").endswith("#" + planted) \
                        and name == expected:
                    found.add(planted)
    assert found == set(benchmark.PLANTED), set(benchmark.PLANTED) - found


def test_blank_nodes_keep_their_identity_in_the_store(runner, vendored,
                                                      benchmark):
    """Oxigraph's bulk_load parses in parallel chunks and splits a blank
    node seen in two of them: a class-restriction-property join gave 20
    rows of 85, and the realist domain and range checks silently found
    nothing. The store must give rdflib's answer."""
    data = vendored + benchmark.generate(60, 84)
    query = ("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
             "PREFIX owl: <http://www.w3.org/2002/07/owl#>\n"
             "SELECT ?s ?p WHERE { ?s rdfs:subClassOf ?r . "
             "?r owl:onProperty ?p }")
    expected = len(list(data.query(query)))
    assert expected > 60
    assert len(list(runner._store(data).query(query))) == expected


SHAPES_HEAD = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix ex: <https://example.invalid/shapes#> .
"""

TARGET = ('sh:target [ a sh:SPARQLTarget ; '
          'sh:select "SELECT ?this WHERE { ?this a ?t }" ]')


@pytest.mark.parametrize("body, refusal", [
    ('ex:S a sh:NodeShape ; %s ; sh:sparql [ sh:message "m" ; '
     'sh:select "SELECT $this WHERE { { SELECT $this WHERE { $this ?p ?o } } }" ] .'
     % TARGET, "subquery"),
    ('ex:S a sh:NodeShape ; %s ; sh:sparql [ sh:message "m" ; '
     'sh:select "SELECT $this WHERE { $this ?p $value }" ] .' % TARGET,
     "$value"),
    ('ex:S a sh:NodeShape ; %s ; sh:sparql [ sh:message "a", "b" ; '
     'sh:select "SELECT $this WHERE { $this ?p ?o }" ] .' % TARGET,
     "2 messages"),
    ('ex:S a sh:NodeShape ; %s ; sh:sparql [ sh:message "m" ; '
     'sh:ask "ASK { $this ?p ?o }" ] .' % TARGET, "sh:ask"),
    ('ex:S a sh:NodeShape ; sh:targetClass ex:C ; sh:sparql [ sh:message "m" ; '
     'sh:select "SELECT $this WHERE { $this ?p ?o }" ] .', "target"),
    ('ex:S a sh:NodeShape ; %s ; sh:sparql [ sh:message "m" ; '
     'sh:select "SELECT ?o WHERE { $this ?p ?o }" ] .' % TARGET,
     "does not project"),
])
def test_what_the_runner_does_not_evaluate_is_refused(runner, body, refusal):
    """Never skipped: a constraint this runner silently passed would be a
    check that cannot fail, the failure the fixtures exist to catch."""
    import rdflib

    shapes = rdflib.Graph()
    shapes.parse(data=SHAPES_HEAD + body, format="turtle")
    data = rdflib.Graph()
    data.parse(data="<https://example.invalid/x> a "
                    "<https://example.invalid/T> .", format="turtle")
    _core, sparql_shapes = runner.split(shapes)
    with pytest.raises(SystemExit) as error:
        runner.run(data, shapes, sparql_shapes)
    assert refusal in str(error.value), str(error.value)


# --------------------------------------------- canonical blank nodes


def turtle_files(repo):
    out = []
    for path in sorted(repo.rglob("*.ttl")):
        relative = path.relative_to(repo).as_posix()
        if relative.startswith((".venv", ".upstream-cache", "_site", "dist")):
            continue
        if "{{" in path.read_text(encoding="utf-8"):
            continue
        out.append(path)
    return out


def test_structural_labels_agree_with_rdflib(canon, repo):
    """On every Turtle file here: the canonical graph is isomorphic to the
    source by rdflib's own test, and a second parse -- fresh blank-node
    labels -- canonicalizes to exactly the same triples."""
    import rdflib
    from rdflib.compare import isomorphic

    files = turtle_files(repo)
    assert len(files) >= 10, files
    wrong = []
    for path in files:
        first, second = rdflib.Graph(), rdflib.Graph()
        first.parse(path, format="turtle")
        second.parse(path, format="turtle")
        labelled = canon.canonical(first)
        if not (isomorphic(labelled, first)
                and set(labelled) == set(canon.canonical(second))):
            wrong.append(path.name)
    assert wrong == [], wrong


def graph(text):
    import rdflib

    out = rdflib.Graph()
    out.parse(data="@prefix : <https://example.invalid/> .\n"
                   "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
                   "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
              + text, format="turtle")
    return out


def test_alike_restrictions_on_two_classes_stay_two(canon):
    g = graph(":A rdfs:subClassOf [ owl:onProperty :p ; owl:someValuesFrom :X ] .\n"
              ":B rdfs:subClassOf [ owl:onProperty :p ; owl:someValuesFrom :X ] .")
    assert len(canon.canonical(g)) == len(g) == 6


def test_alike_restrictions_label_the_same_whatever_the_parse_order(canon):
    """Where a restriction hangs is part of its label. Without it, eight
    alike restrictions on eight classes would be told apart only by a
    counter, assigned in set order -- a different class getting a
    different label on each parse, and different release bytes."""
    names = ["C%d" % i for i in range(8)]
    lines = [":%s rdfs:subClassOf [ owl:onProperty :p ; owl:someValuesFrom :X ] ."
             % n for n in names]
    forward = canon.canonical(graph("\n".join(lines)))
    for _ in range(5):
        backward = canon.canonical(graph("\n".join(reversed(lines))))
        assert set(backward) == set(forward)


def test_duplicate_restrictions_on_one_class_are_kept_and_stable(canon):
    text = (":A rdfs:subClassOf [ owl:onProperty :p ; owl:someValuesFrom :X ] ,"
            " [ owl:onProperty :p ; owl:someValuesFrom :X ] .")
    first, second = canon.canonical(graph(text)), canon.canonical(graph(text))
    assert len(first) == 6 and set(first) == set(second)


def test_filler_order_does_not_change_the_labels(canon):
    one = graph(":A rdfs:subClassOf [ owl:intersectionOf ( :X :Y ) ] .")
    two = graph(":A rdfs:subClassOf [ owl:intersectionOf ( :Y :X ) ] .")
    # Different graphs (list order is content), so different triples ...
    assert set(canon.canonical(one)) != set(canon.canonical(two))
    # ... and each is stable on its own.
    assert set(canon.canonical(one)) == set(canon.canonical(graph(
        ":A rdfs:subClassOf [ owl:intersectionOf ( :X :Y ) ] .")))


def test_different_graphs_are_not_the_same_graph(canon):
    """The release refuses a serialization that does not parse back to its
    graph; that refusal is only as good as this answer."""
    a = graph(":A rdfs:subClassOf [ owl:onProperty :p ; owl:someValuesFrom :X ] .")
    b = graph(":A rdfs:subClassOf [ owl:onProperty :p ; owl:someValuesFrom :Y ] .")
    c = graph(":A rdfs:subClassOf [ owl:onProperty :p ; owl:someValuesFrom :X ] .")
    assert canon.same_graph(a, c)
    assert not canon.same_graph(a, b)


def test_a_shared_blank_node_falls_back_to_rdflib(canon):
    """Not a tree: two parents. Labelled by rdflib, correctly."""
    import rdflib
    from rdflib.compare import isomorphic

    g = rdflib.Graph()
    shared = rdflib.BNode()
    ex = rdflib.Namespace("https://example.invalid/")
    g.add((ex.A, ex.p, shared))
    g.add((ex.B, ex.p, shared))
    g.add((shared, ex.q, ex.X))
    assert not canon.is_forest(g)
    assert isomorphic(canon.canonical(g), g)


def test_the_benchmark_takes_the_fast_path(canon, benchmark):
    """If generated restrictions stopped being trees, the release would
    fall back to rdflib and the budget test would be measuring that."""
    g = benchmark.generate(200, 280)
    assert canon.is_forest(g)
    start = time.perf_counter()
    canon.canonical(g)
    assert time.perf_counter() - start < 10


def test_the_marked_tests_run_somewhere(repo):
    """Checks deselects `scale` and `corpus`; the Scale workflow selects
    both. If either drifted, the budgets would silently stop being
    measured, or Checks would take the hours this exists to remove."""
    import yaml

    def commands(name):
        workflow = yaml.safe_load((repo / ".github/workflows" / name)
                                  .read_text(encoding="utf-8"))
        return " ".join(step.get("run", "") for job in
                        workflow["jobs"].values() for step in job["steps"])

    checks, scale = commands("checks.yml"), commands("scale.yml")
    assert '-m "not reasoning and not scale and not corpus"' in checks
    assert '-m "scale or corpus"' in scale


# ------------------------------------------------------ the budgets


@pytest.mark.scale
def test_the_ladder_on_the_benchmark_is_within_budget(validator, vendored,
                                                      benchmark):
    data = vendored + benchmark.generate()
    found, start = set(), time.perf_counter()
    for name, path in sorted(validator.shape_sets().items()):
        for record in validator.run(data, validator.load([path]))[
                "violations"]:
            for planted, expected in benchmark.PLANTED.items():
                if (record["focus"] or "").endswith("#" + planted) \
                        and name == expected:
                    found.add(planted)
    elapsed = time.perf_counter() - start
    assert elapsed < LADDER_BUDGET, "ladder took %.0f s" % elapsed
    assert found == set(benchmark.PLANTED), set(benchmark.PLANTED) - found


@pytest.mark.scale
def test_a_release_of_the_benchmark_is_within_budget_and_identical(
        repo, tmp_path, benchmark):
    module = tmp_path / "benchmark.ttl"
    module.write_bytes(benchmark.generate().serialize(format="turtle",
                                                      encoding="utf-8"))
    builds = []
    for seed in (1, 2):
        out = tmp_path / ("build-%d" % seed)
        start = time.perf_counter()
        script = (
            "import sys; sys.path.insert(0, %r)\n"
            "from pathlib import Path\n"
            "import importlib.util\n"
            "spec = importlib.util.spec_from_file_location('r', %r)\n"
            "r = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(r)\n"
            "r.build('1.0.0', Path(%r), modules=[Path(%r)])\n"
            % (str(repo / "tools"), str(repo / "tools/release.py"), str(out),
               str(module)))
        result = subprocess.run(
            [sys.executable, "-c", script], cwd=str(repo),
            capture_output=True,
            env={**__import__("os").environ, "PYTHONHASHSEED": str(seed)})
        elapsed = time.perf_counter() - start
        assert result.returncode == 0, result.stderr.decode("utf-8",
                                                            "replace")
        assert elapsed < RELEASE_BUDGET, "a build took %.0f s" % elapsed
        builds.append({p.relative_to(out).as_posix(): p.read_bytes()
                       for p in sorted(out.rglob("*")) if p.is_file()})
    assert builds[0] and builds[0] == builds[1]
    shutil.rmtree(tmp_path / "build-1")
