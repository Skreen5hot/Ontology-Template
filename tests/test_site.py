# SPDX-License-Identifier: MIT
"""The public site: built deterministically, checked, and able to fail.

The site is what an external validator sees instead of the repository, so
the questions are the repository's own, asked of the artifact: is every
figure derived rather than typed, does every link resolve on a subpath,
does ontology text stay text, and is what was built what gets deployed.
The Pages workflow builds twice and compares; this suite does the same,
and then breaks the checker's inputs one at a time to show it notices.

Carried from the Business Capability Ontology's suite and generalized:
the project's name, namespace and files are read from the project file
and the layout contract, never written here. The specification and
review pages are optional, so they are built here from a stand-in
component -- a project without either still has those pages tested.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import zipfile

import pytest

from conftest import load_tool


@pytest.fixture(scope="module", autouse=True)
def private_by_default():
    """The tests describe the default build, for a private repository.
    The Pages workflow sets SITE_REPOSITORY_PRIVATE from the repository's
    real visibility, so in a public repository's Pages job the default
    tests inherited "false" and failed. A test of the public build sets
    it itself."""
    mp = pytest.MonkeyPatch()
    mp.setenv("SITE_REPOSITORY_PRIVATE", "true")
    yield
    mp.undo()


@pytest.fixture(scope="module")
def builder():
    return load_tool("t_build_site", "tools/site/build_site.py")


@pytest.fixture(scope="module")
def checker():
    return load_tool("t_check_site", "tools/site/check_site.py")


@pytest.fixture(scope="module")
def built(builder, tmp_path_factory):
    """One build, shared. Never the working `_site/`: a test that read the
    developer's last build would pass or fail on whether they had built."""
    out = tmp_path_factory.mktemp("site") / "_site"
    written = builder.build(out)
    return out, written


class StandIn:
    """A layout component the repository does not declare, for the
    optional pages: a role, a path, and members."""

    def __init__(self, role, path, members=()):
        self.role, self._path, self._members = role, path, list(members)

    def resolve(self):
        return self._path

    def members(self, pattern="*.md"):
        return self._members


@pytest.fixture(scope="module")
def built_with_documents(builder, repo, tmp_path_factory):
    """A build with a specification and a review in force. Two documents
    the repository already carries stand in for them, so the rendering is
    tested on real Markdown with tables, code and headings."""
    real = builder.layout.components
    extra = [StandIn("specification", repo / "docs/process/PROCESS.md"),
             StandIn("review", repo / "docs", [repo / "docs/DEVELOPMENT.md"])]

    def components(role=None):
        found = list(real(role))
        return found + [e for e in extra if role is None or e.role == role]

    mp = pytest.MonkeyPatch()
    mp.setattr(builder.layout, "components", components)
    try:
        out = tmp_path_factory.mktemp("site-docs") / "_site"
        builder.build(out)
    finally:
        mp.undo()
    return out


@pytest.fixture
def copy(built, tmp_path):
    """A disposable copy for tests that damage the artifact."""
    out, _ = built
    target = tmp_path / "_site"
    shutil.copytree(out, target)
    return target


def terms(out):
    return json.loads((out / "data/terms.json").read_text(encoding="utf-8"))


def site_json(repo):
    return json.loads((repo / "site/content/site.json")
                      .read_text(encoding="utf-8"))


# ------------------------------------------------------------ the build


def test_two_builds_of_one_commit_are_identical(builder, built, tmp_path):
    """The only way to tell a deployment matches its commit is to rebuild
    and compare, and that only works if the build is deterministic."""
    _, first = built
    second = builder.build(tmp_path / "again")
    assert first == second
    assert builder.tree_digest(first) == builder.tree_digest(second)


def test_the_built_site_passes_its_own_check(checker, built):
    out, _ = built
    assert checker.check(out) == []


def test_every_unconditional_navigation_entry_is_a_page(built, repo):
    out, _ = built
    for item in site_json(repo)["navigation"]:
        if not item.get("when"):
            assert (out / (item["path"] + "index.html")).is_file(), item


def test_an_optional_page_is_built_only_with_its_component(
        built, built_with_documents, layout, repo, checker):
    """No specification component, no Specification page and no link to
    one; with one, both, and the result still passes the checker."""
    out, _ = built
    roles = {c.role for c in layout.components()}
    home = (out / "index.html").read_text(encoding="utf-8")
    for item in site_json(repo)["navigation"]:
        if item.get("when") and item["when"] not in roles:
            assert not (out / item["path"]).exists(), item
            assert 'href="%s"' % item["path"] not in home, item
        if item.get("when"):
            assert (built_with_documents / item["path"]
                    / "index.html").is_file(), item
    assert checker.check(built_with_documents) == []


def test_the_name_and_namespace_come_from_the_project_file(built, project):
    out, _ = built
    home = (out / "index.html").read_text(encoding="utf-8")
    assert "<title>%s</title>" % project.load()["title"] in home
    assert project.namespace() in home, "the IRI notice names the namespace"


def test_a_private_repository_is_never_linked(built, project, checker):
    """The default build is for a private repository: the ontology is
    public and how it was made is not, so no page links into the
    repository -- not a source file, the commit, the issues or a release.
    The checker agrees the clean build has none."""
    out, _ = built
    repository = "https://github.com/" + project.repository()
    linked = [p.relative_to(out).as_posix() for p in out.rglob("*.html")
              if 'href="%s' % repository in p.read_text(encoding="utf-8")]
    assert linked == [], linked
    manifest = json.loads((out / "data/downloads.json")
                          .read_text(encoding="utf-8"))
    assert manifest["repository_linked"] is False
    assert checker.check(out) == []


def test_upstream_entries_are_listed(builder, project):
    """T24: a register entry about an upstream term -- planted here on
    CCO's Organization, the case the Business Process Ontology met -- is
    listed apart on the status page, with the term, reason and owner."""
    cco = builder.register.upstream_ids()["CCO"]
    planted = {
        "check": "validate", "where": "validation.realist",
        "focus": project.namespace() + "Firm", "rule": "urn:planted:shape",
        "digest": "0" * 16, "severity": "Warning",
        "reason": "CCO 2.0 does not place Organization under Agent",
        "owner": "the architect", "review": "2027-01-01",
        "upstream": "CCO %sont00001180" % cco}
    # The section alone: the page is shown to carry it by the test below,
    # on the shared build, and a second whole build costs a minute on a
    # ported corpus.
    status = builder.register_section([planted])
    section = status.split("Findings about upstream terms", 1)[1]
    assert "%sont00001180" % cco in section
    assert "does not place Organization under Agent" in section
    assert "None recorded." not in section
    assert "It has 1: 1 validate warning." in status


def test_with_no_upstream_entry_none_is_listed(built):
    out, _ = built
    status = (out / "status/index.html").read_text(encoding="utf-8")
    section = status.split("Findings about upstream terms", 1)[1]
    assert "None recorded." in section or "<table>" in section


def test_a_public_repository_is_linked(builder, project, checker, tmp_path,
                                       monkeypatch):
    """Guards the test above: a builder that never linked would pass it."""
    monkeypatch.setenv("SITE_REPOSITORY_PRIVATE", "false")
    out = tmp_path / "_site"
    builder.build(out)
    home = (out / "index.html").read_text(encoding="utf-8")
    assert "https://github.com/%s/issues" % project.repository() in home
    assert "https://github.com/%s/tree/" % project.repository() in home
    modules = (out / "modules/index.html").read_text(encoding="utf-8")
    assert "https://github.com/%s/blob/" % project.repository() in modules
    assert checker.check(out) == []


def test_a_release_links_only_into_a_public_repository(builder):
    """No tag exists in the template, so the releases page is tested on a
    constructed one: a tag, linked to its GitHub release only when a
    reader could open it."""
    data = {"releases": [{"tag": "v1.0.0", "commit": "a" * 40}]}
    for private, linked in ((True, False), (False, True)):
        ctx = {"private": private, "repository": "https://github.com/o/r"}
        html_out = builder.release_list(data, ctx)
        assert "v1.0.0" in html_out
        assert ("https://github.com/o/r/releases/tag/v1.0.0" in html_out)             is linked, (private, html_out)


def test_a_contact_is_the_route_for_findings_when_private(builder, tmp_path,
                                                          monkeypatch):
    real = builder.read_json

    def with_contact(path):
        data = real(path)
        if path == builder.CONTENT:
            data = dict(data, contact="ontology@example.invalid")
        return data

    monkeypatch.setattr(builder, "read_json", with_contact)
    out = tmp_path / "_site"
    builder.build(out)
    home = (out / "index.html").read_text(encoding="utf-8")
    assert 'href="mailto:ontology@example.invalid">Report an issue' in home


def test_the_checker_refuses_a_link_into_a_private_repository(
        checker, copy, project):
    damage(copy / "modules/index.html", "</main>",
           '<a href="https://github.com/%s/blob/x/y">y</a></main>'
           % project.repository())
    problems = checker.check(copy)
    assert any("links into the private repository" in p
               for p in problems), problems


def test_the_workflow_tells_the_build_the_visibility(repo):
    import yaml

    workflow = yaml.safe_load((repo / ".github/workflows/pages.yml")
                              .read_text(encoding="utf-8"))
    env = workflow["jobs"]["build"]["env"]
    assert env["SITE_REPOSITORY_PRIVATE"] == \
        "${{ github.event.repository.private }}"


def test_downloads_are_the_repository_bytes(built, repo, layout):
    """Copied, never re-serialised: a re-serialised file says the same
    thing and hashes differently, and its checksum would describe the
    serialiser."""
    out, _ = built
    manifest = json.loads((out / "data/downloads.json")
                          .read_text(encoding="utf-8"))
    for row in manifest["authored"] + manifest["upstream"]:
        sub = "downloads/" if row["origin"] == "authored" \
            else "downloads/upstream/"
        assert (out / sub / row["file"]).read_bytes() == \
            (repo / row["path"]).read_bytes(), row["file"]
    assert len(manifest["upstream"]) == len(layout.vendored_files())
    assert {r["path"] for r in manifest["authored"]} >= {
        p.relative_to(repo).as_posix() for p in layout.ontology_files()}


def test_the_bundle_holds_authored_files_only(built, layout, project):
    """Upstream extracts are somebody else's and are offered separately,
    under their own licences -- not packed into an archive that carries
    this repository's LICENSE."""
    out, _ = built
    pid = project.project_id()
    with zipfile.ZipFile(out / "downloads" / ("%s-ontology.zip" % pid)) \
            as archive:
        names = archive.namelist()
    assert "%s/LICENSE" % pid in names and "%s/SHA256SUMS" % pid in names
    vendored = {p.name for p in layout.vendored_files()}
    assert not [n for n in names if n.split("/")[-1] in vendored], names
    for path in layout.ontology_files():
        assert "%s/%s" % (pid, path.name) in names


def test_a_crlf_source_file_stops_the_build(builder, tmp_path):
    """The guard behind cross-machine determinism. CRLF in the working tree
    -- from core.autocrlf=true, or from Python's write_text on Windows --
    made a local BCO build publish six files that differed from CI's under
    the same commit."""
    lf = tmp_path / "lf.css"
    crlf = tmp_path / "crlf.css"
    lf.write_bytes(b"a {}\nb {}\n")
    crlf.write_bytes(b"a {}\r\nb {}\r\n")
    assert lf.read_bytes() != crlf.read_bytes()
    assert builder.source_bytes(lf) == b"a {}\nb {}\n"
    with pytest.raises(SystemExit) as error:
        builder.source_bytes(crlf)
    assert "CRLF" in str(error.value)


def test_an_unfilled_placeholder_stops_the_build(builder):
    with pytest.raises(SystemExit) as error:
        builder.fill("<p>{{nothing_fills_this}}</p>", {}, "x")
    assert "nothing_fills_this" in str(error.value)


def test_the_deploy_waits_for_the_project_to_publish(repo):
    """A Pages site is public even for a private repository, so nothing is
    deployed until site.json says `"publish": true` -- and every run still
    builds and checks, so a broken site is found before that day."""
    import yaml

    assert isinstance(site_json(repo).get("publish"), bool)
    workflow = yaml.safe_load((repo / ".github/workflows/pages.yml")
                              .read_text(encoding="utf-8"))
    build, deploy = workflow["jobs"]["build"], workflow["jobs"]["deploy"]
    assert "needs.build.outputs.publish == 'true'" in deploy["if"]
    for step in build["steps"]:
        uses = step.get("uses", "")
        if "configure-pages" in uses or "upload-pages-artifact" in uses:
            assert "steps.publish.outputs.publish == 'true'" in step["if"]
        if step["name"] in ("Build the site", "Check the built artifact"):
            assert "if" not in step, step["name"]
    assert workflow["permissions"] == {"contents": "read"}
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}


def test_an_asset_with_no_rule_stops_the_build(builder, repo, tmp_path,
                                              monkeypatch):
    """An artifact that deploys whatever it finds cannot say what it
    deployed: a file under site/src/ that is not .css or .js is refused."""
    assets = tmp_path / "src"
    shutil.copytree(repo / builder.ASSETS, assets)
    (assets / "assets/logo.png").write_bytes(b"not a stylesheet")
    monkeypatch.setattr(builder, "ASSETS", str(assets))
    with pytest.raises(SystemExit) as error:
        builder.build(tmp_path / "out")
    assert "assets/logo.png" in str(error.value)


def test_a_fragment_no_navigation_names_stops_the_build(builder, repo,
                                                        tmp_path,
                                                        monkeypatch):
    """A page nobody can reach is a page nobody checks."""
    pages = tmp_path / "pages"
    shutil.copytree(repo / builder.PAGES, pages)
    (pages / "orphan.html").write_bytes(b"<h1>Orphan</h1>\n")
    monkeypatch.setattr(builder, "PAGES", str(pages))
    with pytest.raises(SystemExit) as error:
        builder.build(tmp_path / "out")
    assert "orphan" in str(error.value)


# ------------------------------------------------------- the term index


def test_the_index_holds_every_upstream_term_and_marks_it(built, builder):
    out, _ = built
    index = terms(out)
    upstream = [r for r in index["classes"] if r["origin"] == "upstream"]
    assert len(upstream) >= 70, len(upstream)
    assert {r["module"] for r in upstream} == {p["id"]
                                               for p in builder.pins()}
    assert index["counts"]["authored"] == len(
        [r for r in index["classes"] if r["origin"] == "authored"])


def test_every_record_carries_the_term_contract(built):
    """Every record in the built index has the fields the explorer reads
    for variants, findings and accepted findings
    (tests/test_term_contract.py), so it never meets one without them."""
    out, _ = built
    for record in terms(out)["classes"]:
        for key in ("variants", "notes", "accepted", "declared_in"):
            assert key in record, (record["id"], key)


def test_category_comes_from_the_hierarchy(built, builder):
    """Read from the subClassOf chain of the vendored BFO, never from a
    name: fiat object part is shown as a material entity because BFO puts
    it there."""
    out, _ = built
    by_id = {r["id"]: r for r in terms(out)["classes"]}
    assert by_id["obo:BFO_0000024"]["category"] == "material entity"
    assert by_id["obo:BFO_0000203"]["category"] == "temporal region"
    assert by_id["obo:BFO_0000001"]["category"] == "other"


def chain(text, project):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(data=(
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix obo: <http://purl.obolibrary.org/obo/> .\n"
        "@prefix cco: <https://www.commoncoreontologies.org/> .\n"
        "@prefix : <%s> .\n" % project.namespace()) + text, format="turtle")
    return graph


def test_the_most_specific_category_wins(builder, project):
    graph = chain(
        ":Report rdfs:subClassOf cco:ont00000958 .\n"
        "cco:ont00000958 rdfs:subClassOf obo:BFO_0000031 .\n", project)
    iri = project.namespace() + "Report"
    assert builder.category_of(iri, "class", graph) == \
        "information content entity"


def test_two_unrelated_categories_are_both_shown_and_noted(builder,
                                                          project):
    """Not refused: the realist shapes report it, and an accepted finding
    must still publish (tests/test_term_contract.py)."""
    graph = chain(":Both rdfs:subClassOf obo:BFO_0000015, obo:BFO_0000040 .",
                  project)
    notes = []
    shown = builder.category_of(project.namespace() + "Both", "class", graph,
                                notes)
    assert shown == "material entity / process"
    assert "unrelated categories" in notes[0]["text"]


def authored_source(text, project):
    import rdflib

    graph = rdflib.Graph()
    graph.parse(data=(
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
        "@prefix : <%s> .\n" % project.namespace()) + text, format="turtle")
    return graph, {"key": "m", "path": "m.ttl", "graph": graph,
                   "origin": "authored"}


def test_an_authored_term_without_a_definition_is_noted(builder, project):
    """No fallback text: the definition is shown as absent and noted, and
    the validator fails on it unless the register accepts it."""
    graph, source = authored_source(':X a owl:Class ; rdfs:label "X" .',
                                    project)
    [record] = builder.term_records([source], graph, builder.prefixes())
    assert record["definition"] == ""
    assert [n["kind"] for n in record["notes"]] == ["missing"]


def test_two_labels_in_one_language_are_both_shown(builder, project):
    graph, source = authored_source(
        ':X a owl:Class ; rdfs:label "A"@en, "B"@en ; skos:definition "d" .',
        project)
    [record] = builder.term_records([source], graph, builder.prefixes())
    assert record["label"] == "A / B"
    assert [n["kind"] for n in record["notes"]] == ["conflict"]


def test_a_well_formed_authored_term_is_indexed(builder, project):
    """Guards the two above: a builder that noted every authored term
    would pass both."""
    graph, source = authored_source(
        ':X a owl:Class ; rdfs:label "X"@en ; skos:definition "d"@en ;\n'
        '  rdfs:subClassOf <http://purl.obolibrary.org/obo/BFO_0000015> .',
        project)
    [record] = builder.term_records([source], graph, builder.prefixes())
    assert record["id"] == project.prefix() + ":X"
    assert record["origin"] == "authored" and record["category"] == "process"
    assert record["notes"] == []


# --------------------------------------------------- text is not markup


def test_raw_html_in_a_document_is_shown_not_run(builder):
    body, _ = builder.render_markdown(
        "Text <script>alert(1)</script> and `<Filler>`.\n\n<div>raw</div>")
    assert "<script>" not in body and "<div>" not in body
    assert "&lt;script&gt;" in body and "&lt;Filler&gt;" in body


def test_the_explorer_never_writes_markup(repo):
    """Ontology text reaches the page through textContent only. Looked for
    as an assignment, not as a word: the file's own comment says "never
    innerHTML", and a scan for the bare word would fail on the rule's
    explanation."""
    for name in ("explorer.js", "ranking.js"):
        text = (repo / "site/src/assets/js" / name).read_text(
            encoding="utf-8")
        assert not re.search(r"\.(innerHTML|outerHTML)\s*[+]?=", text), name
        assert "insertAdjacentHTML" not in text, name
        assert "document.write" not in text, name


def test_the_specification_is_rendered_whole(built_with_documents, repo):
    """Every heading in the Markdown arrives on the page, as a heading one
    level down -- the page owns the only <h1>."""
    source = (repo / "docs/process/PROCESS.md").read_text(encoding="utf-8")
    page = (built_with_documents / "specification/index.html").read_text(
        encoding="utf-8")
    # Fenced code first: a `# comment` line inside a code block is not a
    # heading, and counting it is the scan-finds-the-comment trap.
    prose = re.sub(r"^```.*?^```", "", source, flags=re.M | re.S)
    headings = re.findall(r"^#{1,4} ", prose, flags=re.M)
    assert len(headings) >= 5, len(headings)
    assert page.count("<h1") == 1
    assert len(re.findall(r"<h[2-5] id=", page)) >= len(headings)


def test_the_ranking_the_explorer_runs(repo, tmp_path):
    """The explorer's ranking, run by Node on the shipped file rather than
    re-implemented here. Skipped where Node is not installed; the Checks
    workflow has it."""
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    script = tmp_path / "rank.js"
    script.write_bytes(("""
const r = require(%s);
const records = [
  {id: "x:A", iri: "https://x/A", label: "process", definition: "",
   synonyms: [], module: "m", category: "process"},
  {id: "x:B", iri: "https://x/B", label: "process boundary", definition: "",
   synonyms: [], module: "m", category: "process boundary"},
  {id: "x:C", iri: "https://x/C", label: "history", definition:
   "the sum of the processes", synonyms: [], module: "m",
   category: "process"},
];
const hits = r.search(records, "process", {}, []);
console.log(JSON.stringify(hits.map(h => [h.record.id, h.score])));
const only = r.search(records, "", {category: "process boundary"}, []);
console.log(JSON.stringify(only.map(h => h.record.id)));
""" % json.dumps(str(repo / "site/src/assets/js/ranking.js"))).encode())
    result = subprocess.run([node, str(script)], capture_output=True)
    assert result.returncode == 0, result.stderr.decode("utf-8", "replace")
    first, second = result.stdout.decode("utf-8").splitlines()
    ranked = json.loads(first)
    assert [row[0] for row in ranked] == ["x:A", "x:B", "x:C"], ranked
    assert ranked[0][1] < ranked[1][1] < ranked[2][1], (
        "exact before prefix before definition substring")
    assert json.loads(second) == ["x:B"]


# ------------------------------------------------ the checker can fail


def damage(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text, (path.name, old[:60])
    changed = text.replace(old, new, 1)
    assert changed != text
    path.write_bytes(changed.encode("utf-8"))


@pytest.mark.parametrize("page, old, new, expect", [
    ("modules/index.html", 'href="../assets/css/site.css"',
     'href="https://cdn.invalid/site.css"', "from another origin"),
    ("modules/index.html", 'href="../downloads/"',
     'href="../downloadz/"', "resolves to nothing"),
    ("modules/index.html", 'href="../downloads/"',
     'href="/downloads/"', "root-absolute"),
    ("modules/index.html", "</main>",
     "<script>alert(1)</script></main>", "inline script"),
    ("modules/index.html", "<h2>", "<h1>x</h1><h2>", "<h1> elements"),
    ("modules/index.html", '<main id="main"',
     '<main onclick="x()" id="main"', "event handler"),
])
def test_the_checker_refuses_each_kind_of_damage(checker, copy, page, old,
                                                 new, expect):
    """Each refusal, falsified on a real artifact. A checker that passed
    the clean build and also passed these would be checking nothing."""
    damage(copy / page, old, new)
    problems = checker.check(copy)
    assert any(expect in p for p in problems), problems


def test_the_checker_refuses_a_concealed_conflict_in_the_index(checker,
                                                               copy):
    """Through check(), on a real artifact: a record given two English
    definitions and no note is published concealing one of them (T7)."""
    path = copy / "data/terms.json"
    index = json.loads(path.read_text(encoding="utf-8"))
    record = index["classes"][0]
    record["variants"]["definition"] = [
        {"value": "one", "lang": "en", "literal": True, "modules": ["a"]},
        {"value": "two", "lang": "en", "literal": True, "modules": ["b"]}]
    record["definition"] = "one"
    path.write_bytes(json.dumps(index).encode("utf-8"))
    problems = checker.check(copy)
    assert [p for p in problems if "no note says so" in p], problems
    assert [p for p in problems if "not all of them" in p], problems


def test_the_status_page_has_the_published_findings(built):
    out, _ = built
    status = (out / "status/index.html").read_text(encoding="utf-8")
    section = status.split("Terms and modules published with findings", 1)[1]
    assert ("Every term has one label" in section
            or "finding(s) the published pages show" in section), section[:300]
    assert "Terms published with conflicting or missing text" in (
        out / "index.html").read_text(encoding="utf-8")


def test_the_checker_refuses_a_broken_fragment(checker, built_with_documents,
                                               tmp_path):
    target = tmp_path / "_site"
    shutil.copytree(built_with_documents, target)
    damage(target / "specification/index.html", 'href="#',
           'href="#no-such-')
    problems = checker.check(target)
    assert any("fragment" in p for p in problems), problems


def test_the_checker_notices_a_tampered_download(checker, copy, layout):
    name = layout.ontology_files()[0].name
    target = copy / "downloads" / name
    original = target.read_bytes()
    target.write_bytes(original + b"\n# tampered\n")
    assert target.read_bytes() != original
    problems = checker.check(copy)
    assert any("%s does not match" % name in p for p in problems), problems


def test_the_checker_notices_a_tampered_specification(checker,
                                                      built_with_documents,
                                                      tmp_path):
    """The specification is optional, so its checksum is checked only when
    there is one -- and then it is checked."""
    target = tmp_path / "_site"
    shutil.copytree(built_with_documents, target)
    manifest = json.loads((target / "data/downloads.json")
                          .read_text(encoding="utf-8"))
    name = manifest["specification"]["file"]
    path = target / "downloads" / name
    path.write_bytes(path.read_bytes() + b"\ntampered\n")
    problems = checker.check(target)
    assert any("%s does not match" % name in p for p in problems), problems
