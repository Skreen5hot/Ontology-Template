# SPDX-License-Identifier: MIT
"""Claude Code hook: lint the authored Turtle after an agent edits a .ttl.

Registered in .claude/settings.json as a PostToolUse hook on Write and
Edit. Claude Code passes the tool call as JSON on stdin; when the file
written is Turtle inside this repository, this runs
tools/ontology/iri_lint.py over the whole authored scope -- the whole
scope, because a reference in the edited file resolves against
declarations in the others -- and, on a finding, exits 2 with the
findings on stderr, which Claude Code hands back to the agent.

Why a hook rather than a rule in CLAUDE.md: "never write a cco: IRI from
memory" is a rule an agent can read and still break, and the linter's
readable_label finding is exactly that breach, with the right IRI named.
A hook makes the agent see it on the edit that caused it.

Standard library only, so it runs under whatever `python` the hook
finds; the lint itself runs under the repository's .venv when there is
one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LINT = "tools/ontology/iri_lint.py"


def interpreter(root: Path) -> str:
    for candidate in (root / ".venv/Scripts/python.exe",
                      root / ".venv/bin/python"):
        if candidate.is_file():
            return str(candidate)
    return sys.executable


def run_lint(root: Path) -> tuple[int, str]:
    result = subprocess.run([interpreter(root), LINT], cwd=str(root),
                            capture_output=True)
    out = (result.stdout + result.stderr).decode("utf-8", "replace")
    return result.returncode, out


def decide(payload: dict, root: Path, run=run_lint) -> tuple[int, str]:
    """(exit code, message) for one tool call. 0 lets it pass silently;
    2 hands the message back to the agent."""
    path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not path.lower().endswith(".ttl"):
        return 0, ""
    try:
        Path(path).resolve().relative_to(root)
    except ValueError:
        return 0, ""
    code, out = run(root)
    if code == 0:
        return 0, ""
    if code == 1:
        return 2, ("The IRI linter found problems in the authored Turtle "
                   "after this edit. Fix them before going on; a "
                   "suggestion after '->' is the real IRI.\n" + out)
    return 2, "The IRI linter could not run after this edit:\n" + out


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    code, message = decide(payload, ROOT)
    if message:
        print(message, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
