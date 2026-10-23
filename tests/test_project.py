# SPDX-License-Identifier: MIT
"""The project file, and the refusal that keeps an uninitialized copy red.

Every tool reads the project's values from config/project.yaml through
tools/project.py. The file is checked for being well formed and for
agreeing with itself, and each rule is broken once, against a mapping
that otherwise passes.

The second half is `--check`: a repository made with "Use this template"
says `template: true` until init runs, and CI must fail it, because
otherwise every check passes about a placeholder ontology called
`example` and nothing says the project was never set up.
"""

from __future__ import annotations

import copy

import pytest

from conftest import load_tool


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_project", "tools/project.py")


@pytest.fixture(scope="module")
def good(tool):
    """The live project file, as the baseline every refusal departs from."""
    return copy.deepcopy(dict(tool.load()))


def changed(good, **changes):
    out = copy.deepcopy(good)
    for key, value in changes.items():
        if value is KeyError:
            out.pop(key)
        else:
            out[key] = value
    return out


# ------------------------------------------------------------ the file


def test_the_project_file_is_usable(tool, good):
    assert tool.problems_of(good) == []
    assert good["namespace"] == good["iri_base"] + "#"


def test_the_tools_read_the_same_values(tool, project, good):
    """The fixture's module and the one the tools import are the same
    file read twice; if they disagreed, a test would be checking a
    different project from the one the tools run against."""
    assert project.namespace() == good["namespace"]
    assert project.prefix() == good["prefix"]
    assert project.code() == good["code"]


@pytest.mark.parametrize("changes, expect", [
    ({"title": KeyError}, "declares no 'title'"),
    ({"template": "yes"}, "template must be true or false"),
    ({"id": "Widget"}, "is not lowercase"),
    ({"id": "widget--works"}, "is not lowercase"),
    ({"code": "abc"}, "is not uppercase"),
    ({"prefix": "Widget"}, "Turtle-safe"),
    ({"repository": "widget"}, "is not owner/name"),
    ({"namespace": "https://fandaws.com/ontology/other#"},
     "is not iri_base"),
    ({"namespace": "http://insecure.invalid/x#",
      "iri_base": "http://insecure.invalid/x"}, "is not https"),
    ({"correspondents": ["xyz"]}, "uppercase team codes"),
    ({"correspondents": "XYZ"}, "uppercase team codes"),
])
def test_each_rule_refuses(tool, good, changes, expect):
    problems = tool.problems_of(changed(good, **changes))
    assert any(expect in p for p in problems), problems


def test_a_project_listing_itself_as_a_correspondent_is_refused(tool, good):
    problems = tool.problems_of(changed(good, correspondents=[good["code"]]))
    assert any("its own correspondent" in p for p in problems), problems


def test_a_hand_edited_template_flag_is_refused(tool, good):
    """init sets `template: false` and a new id together. The flag flipped
    by hand, with the placeholder id still there, is a project nobody
    initialized."""
    problems = tool.problems_of(changed(good, template=False,
                                        id=tool.PLACEHOLDER_ID))
    assert any("placeholder" in p for p in problems), problems


# ---------------------------------------------- the uninitialized copy


@pytest.mark.parametrize("url, expect", [
    ("https://github.com/owner/Widget-Ontology.git", "owner/Widget-Ontology"),
    ("https://github.com/owner/Widget-Ontology", "owner/Widget-Ontology"),
    ("git@github.com:owner/Widget-Ontology.git", "owner/Widget-Ontology"),
    ("https://gitlab.invalid/owner/x.git", None),
])
def test_the_repository_is_read_from_the_remote(tool, url, expect):
    assert tool.repository_of_remote(url) == expect


def test_a_copy_still_claiming_to_be_the_template_is_refused(tool, good):
    template = changed(good, template=True,
                       repository="owner/Ontology-Template")
    problem = tool.initialization_problem(template, "owner/Widget-Ontology")
    assert problem and "init_project.py" in problem, problem


def test_the_template_itself_is_not_refused(tool, good):
    template = changed(good, template=True,
                       repository="owner/Ontology-Template")
    assert tool.initialization_problem(
        template, "owner/Ontology-Template") is None
    assert tool.initialization_problem(
        template, "OWNER/ontology-template") is None, (
        "GitHub slugs are case-insensitive; the template refused itself")


def test_an_initialized_project_is_not_refused(tool, good):
    project = changed(good, template=False, id="widget",
                      repository="owner/Widget-Ontology")
    assert tool.initialization_problem(project, "owner/Other") is None


def test_check_fails_in_actions_for_an_uninitialized_copy(tool, monkeypatch,
                                                          good):
    """The step CI runs, end to end: GITHUB_REPOSITORY is how Actions
    says which repository this is."""
    if not good["template"]:
        # A project: --check has nothing to refuse, whatever the
        # repository is called.
        monkeypatch.setenv("GITHUB_REPOSITORY", "owner/Somewhere-Else")
        assert tool.main(["--check"]) == 0
        return
    monkeypatch.setenv("GITHUB_REPOSITORY", "owner/Somewhere-Else")
    assert tool.main(["--check"]) == 1
    monkeypatch.setenv("GITHUB_REPOSITORY", good["repository"])
    assert tool.main(["--check"]) == 0
