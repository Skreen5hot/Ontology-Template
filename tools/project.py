# SPDX-License-Identifier: MIT
"""The project's own values, read from config/project.yaml.

    python tools/project.py            # print them
    python tools/project.py --check    # exit 1 in an uninitialized copy

Every tool that needs the namespace, prefix, code or repository asks
here. In the projects this template was cut from, each tool carried its
own constant -- the namespace in validate.py, the extract base in
vendor_upstream.py, the sender code in communications.py -- and starting
a new project meant finding all of them. One that was missed did not
fail: it kept answering for the old project.

THE TEMPLATE AND ITS COPIES

`template: true` is what the template repository says about itself. A
repository made with "Use this template" inherits the file unchanged, so
it says the same thing until tools/init_project.py runs. `--check` tells
the two apart by asking which repository this is -- GITHUB_REPOSITORY in
Actions, the origin remote otherwise -- and refuses a copy that still
claims to be the template. Without that, an uninitialized copy runs
every check green against a namespace called `example` and nothing says
the project was never set up.
"""

from __future__ import annotations

import functools
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402

CONFIG = "config/project.yaml"

#: What the template ships with. A project that still has these after
#: init has not been initialized, whatever `template` says.
PLACEHOLDER_ID = "example"

ID = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
CODE = re.compile(r"^[A-Z][A-Z0-9]+$")
PREFIX = re.compile(r"^[a-z][a-z0-9_]*$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

REQUIRED = ("template", "id", "code", "title", "description", "namespace",
            "prefix", "iri_base", "repository", "licence_holder",
            "correspondents")


class ProjectError(SystemExit):
    """The project file is missing a value or contradicts itself."""


def problems_of(raw: dict) -> list[str]:
    """Every way the values can be malformed or disagree with each other.

    Separate from `load` so a test can hand it a constructed mapping and
    watch each rule refuse.
    """
    out = ["%s declares no %r" % (CONFIG, key)
           for key in REQUIRED if key not in raw]
    if out:
        return out
    if not isinstance(raw["template"], bool):
        out.append("template must be true or false")
    if not ID.match(str(raw["id"])):
        out.append("id %r is not lowercase letters, digits and single "
                   "hyphens" % raw["id"])
    if not CODE.match(str(raw["code"])):
        out.append("code %r is not uppercase letters and digits"
                   % raw["code"])
    if not PREFIX.match(str(raw["prefix"])):
        out.append("prefix %r is not a Turtle-safe lowercase name"
                   % raw["prefix"])
    if not REPOSITORY.match(str(raw["repository"])):
        out.append("repository %r is not owner/name" % raw["repository"])
    if raw["namespace"] != str(raw["iri_base"]) + "#":
        out.append(
            "namespace %r is not iri_base %r plus '#'. Module IRIs and term "
            "IRIs would then live under different roots, and the prefix "
            "test in tests/test_namespace.py could not tell an authored "
            "IRI from a stray one" % (raw["namespace"], raw["iri_base"]))
    if not str(raw["namespace"]).startswith("https://"):
        out.append("namespace %r is not https" % raw["namespace"])
    if not isinstance(raw["correspondents"], list) or not all(
            isinstance(c, str) and CODE.match(c)
            for c in raw["correspondents"]):
        out.append("correspondents must be a list of uppercase team codes")
    elif raw["code"] in raw["correspondents"]:
        out.append("code %s is listed as its own correspondent"
                   % raw["code"])
    if raw["template"] is False and raw["id"] == PLACEHOLDER_ID:
        out.append(
            "template is false and the id is still %r, the template's "
            "placeholder. init sets both; one without the other is a "
            "hand edit" % PLACEHOLDER_ID)
    return out


@functools.lru_cache(maxsize=1)
def load() -> dict:
    import yaml

    path = layout.repository_root() / CONFIG
    if not path.is_file():
        raise ProjectError(CONFIG + " is missing")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    found = problems_of(raw)
    if found:
        raise ProjectError("%s is not usable:\n  %s"
                           % (CONFIG, "\n  ".join(found)))
    return raw


def namespace() -> str:
    return load()["namespace"]


def iri_base() -> str:
    return load()["iri_base"]


def prefix() -> str:
    return load()["prefix"]


def project_id() -> str:
    return load()["id"]


def code() -> str:
    return load()["code"]


def repository() -> str:
    return load()["repository"]


def is_template() -> bool:
    return load()["template"]


def correspondents() -> set[str]:
    return set(load()["correspondents"])


def repository_of_remote(url: str) -> str | None:
    """owner/name from a GitHub remote url, https or ssh, or None."""
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$",
                      url.strip())
    return match.group(1) if match else None


def current_repository() -> tuple[str | None, str]:
    """Which repository this checkout is, and how that was found out."""
    env = os.environ.get("GITHUB_REPOSITORY")
    if env:
        return env, "GITHUB_REPOSITORY"
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=str(layout.repository_root()), capture_output=True)
    if result.returncode == 0:
        url = result.stdout.decode("utf-8").strip()
        return repository_of_remote(url), "origin " + url
    return None, "no origin remote"


def initialization_problem(raw: dict, current: str | None) -> str | None:
    """Why this checkout is an uninitialized copy, or None.

    Pure, so the refusal can be tested without changing the environment.
    """
    if not raw["template"]:
        return None
    if current is None:
        return None
    if current.lower() == str(raw["repository"]).lower():
        return None
    return (
        "this is %s, and %s still describes the template (%s, project id "
        "%r). Run tools/init_project.py to make it a project of its own; "
        "until then every check here is about a placeholder ontology."
        % (current, CONFIG, raw["repository"], raw["id"]))


def main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if this is an uninitialized copy of the "
                         "template")
    args = ap.parse_args(argv)

    raw = load()
    for key in REQUIRED:
        print("  %-15s %s" % (key, raw[key]))
    current, how = current_repository()
    print()
    print("  this checkout  %s  (%s)" % (current or "unknown", how))

    if args.check:
        problem = initialization_problem(raw, current)
        if problem:
            print()
            print("  NOT INITIALIZED: %s" % problem)
            return 1
        if raw["template"] and current is None:
            print("  template: true, and which repository this is cannot "
                  "be determined, so whether it is the template or an "
                  "uninitialized copy is not known")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
