# SPDX-License-Identifier: MIT
"""Shared fixtures, and the import path for the tools.

`tools/` is not an installed package on purpose. It is a directory of
scripts that the tests import directly, so there is no build step between
writing a tool and testing the tool that ships.

Owned by the ontology template: nothing here names a project. Project
values are read from config/project.yaml through the `project` fixture.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))


def load_tool(name: str, relative: str):
    """Import a tool by path, so tests exercise the file that ships."""
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "reasoning: needs Java and the pinned ROBOT jar; the Reasoning "
        "workflow runs these, the Checks workflow deselects them")
    config.addinivalue_line(
        "markers",
        "scale: time budgets on the generated benchmark corpus; the Scale "
        "workflow runs these, the Checks workflow deselects them")
    config.addinivalue_line(
        "markers",
        "corpus: work that grows with the live ontology (minutes at 3,000 "
        "classes); the Scale workflow runs these, Checks deselects them")


@pytest.fixture(scope="session")
def repo() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def layout():
    import layout as module

    return module


@pytest.fixture(scope="session")
def disposition():
    return load_tool("t_disposition", "tools/licensing/disposition.py")


@pytest.fixture(scope="session")
def project():
    import project as module

    return module
