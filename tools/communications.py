# SPDX-License-Identifier: MIT
"""Check the communications record, and say which threads are open.

    python tools/communications.py          # findings, then open threads
    python tools/communications.py --json   # the same, as one JSON object

The protocol is communications/README.md. This is the part of it a tool
can hold: the header has every field and each is well formed; the id,
date, team and direction agree with where the file sits; a reply names a
message that exists and is not later than itself; every ref names a
commit and a digest, and a ref into this repository still matches; an
incoming copy's body is the original's bytes; and no committed message
has been edited since.

Status is derived here, never stored: a request or finding is open until
some later message answers it. A status field would be one more thing to
forget to update, and a message record that has to be edited to stay true
is not a record.

Exit codes: 0 no findings; 1 findings (each names the file).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import project  # noqa: E402

ROOT_DIR = "communications"

#: This repository's code and slug, from config/project.yaml. Module
#: names rather than calls inside each function so a test can replace
#: them for a constructed record.
SELF = project.code()
THIS_REPO = project.repository()

#: The teams this repository corresponds with, by code: `correspondents`
#: in config/project.yaml. Adding one is a deliberate change there and a
#: folder with a README, so a misspelt folder name is a finding rather
#: than a new correspondent.
TEAMS = project.correspondents()

TYPES = ("request", "finding", "answer", "notice", "acknowledgment")
#: Types that leave a thread open until answered.
OPENING = ("request", "finding")
#: Types that close the thread they reply to.
CLOSING = ("answer", "acknowledgment")

REQUIRED = ("id", "from", "to", "date", "type", "subject", "in_reply_to",
            "refs", "author", "requires_act")
REF_FIELDS = ("repo", "commit", "path", "sha256")
DIRECTIONS = ("incoming", "outgoing")

FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def repository_root() -> Path:
    here = Path(__file__).resolve()
    return next(p for p in (here, *here.parents)
                if (p / "config/repository-layout.yaml").is_file())


def git(root: Path, *args: str) -> tuple[int, bytes]:
    result = subprocess.run(["git", *args], cwd=str(root),
                            capture_output=True)
    return result.returncode, result.stdout


# ------------------------------------------------------------- parsing


def split(data: bytes) -> tuple[dict | None, bytes, str | None]:
    """(header, body, problem). The body is the bytes after the closing
    `---` line, untouched, because an incoming body is compared by digest
    with the original it copies."""
    import yaml

    opener = b"---\n"
    if not data.startswith(opener):
        return None, b"", "does not start with a '---' header line"
    end = data.find(b"\n---\n", len(opener) - 1)
    if end == -1:
        return None, b"", "has no closing '---' header line"
    raw = data[len(opener):end + 1]
    body = data[end + len(b"\n---\n"):]
    try:
        header = yaml.safe_load(raw.decode("utf-8"))
    except Exception as exc:  # yaml raises several types
        return None, b"", "header is not YAML: %s" % exc
    if not isinstance(header, dict):
        return None, b"", "header is not a mapping"
    return header, body, None


def as_date(value) -> str | None:
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    return None


# ------------------------------------------------------------ checking


def check_header(header: dict, team: str, direction: str, filename: str,
                 body: bytes) -> list[str]:
    """Everything about one message that its own file can answer."""
    problems = []
    missing = [f for f in REQUIRED if f not in header]
    if missing:
        return ["header lacks %s" % ", ".join(missing)]

    match = FILENAME.match(filename)
    if not match:
        return ["filename is not YYYY-MM-DD-<slug>.md"]
    file_date, slug = match.groups()

    date = as_date(header["date"])
    if date is None:
        problems.append("date %r is not YYYY-MM-DD" % (header["date"],))
    elif date != file_date:
        problems.append("date %s does not match the filename's %s"
                        % (date, file_date))

    sender, receiver = ((team, SELF) if direction == "incoming"
                        else (SELF, team))
    if header["from"] != sender or header["to"] != receiver:
        problems.append(
            "from/to are %s -> %s, but a message in %s/%s is %s -> %s"
            % (header["from"], header["to"], team.lower(), direction,
               sender, receiver))

    expected_id = "%s-%s-%s-%s" % (sender, receiver, file_date, slug)
    if header["id"] != expected_id:
        problems.append("id is %r; its path makes it %r"
                        % (header["id"], expected_id))

    if header["type"] not in TYPES:
        problems.append("type %r is not one of %s"
                        % (header["type"], ", ".join(TYPES)))
    if not isinstance(header["subject"], str) or not header["subject"].strip():
        problems.append("subject is empty")
    if not isinstance(header["author"], str) or not header["author"].strip():
        problems.append("author is empty")
    if not isinstance(header["requires_act"], bool):
        problems.append("requires_act must be true or false")
    if header["in_reply_to"] is not None and not isinstance(
            header["in_reply_to"], str):
        problems.append("in_reply_to must be an id or null")
    if header["type"] in CLOSING and not header["in_reply_to"]:
        problems.append("an %s replies to something; in_reply_to is null"
                        % header["type"])

    refs = header["refs"]
    if not isinstance(refs, list):
        problems.append("refs must be a list (empty if there are none)")
        refs = []
    for number, ref in enumerate(refs, 1):
        problems.extend("ref %d: %s" % (number, p) for p in check_ref(ref))

    if direction == "incoming":
        source = header.get("source")
        if not isinstance(source, dict):
            problems.append("an incoming message has no source: where the "
                            "original lives, and its digest")
        else:
            problems.extend("source: %s" % p for p in check_ref(source))
            if (isinstance(source.get("sha256"), str)
                    and hashlib.sha256(body).hexdigest() != source["sha256"]):
                problems.append(
                    "the body is not the original: it digests to %s and "
                    "source.sha256 is %s"
                    % (hashlib.sha256(body).hexdigest()[:16],
                       source["sha256"][:16]))
    elif "source" in header:
        problems.append("an outgoing message has a source; it is the "
                        "original")
    return problems


def check_ref(ref) -> list[str]:
    if not isinstance(ref, dict):
        return ["is not a mapping"]
    problems = ["lacks %s" % f for f in REF_FIELDS if not ref.get(f)]
    if problems:
        return problems
    if not COMMIT.match(str(ref["commit"])):
        problems.append("commit %r is not a full 40-hex SHA -- a short one "
                        "can become ambiguous" % ref["commit"])
    if not SHA256.match(str(ref["sha256"])):
        problems.append("sha256 %r is not 64 lowercase hex" % ref["sha256"])
    return problems


def check_local_ref(root: Path, ref: dict) -> list[str]:
    """A ref into this repository, recomputed from the commit it names."""
    code, data = git(root, "show", "%s:%s" % (ref["commit"], ref["path"]))
    if code:
        return ["%s at %s does not exist in this repository"
                % (ref["path"], ref["commit"][:12])]
    got = hashlib.sha256(data).hexdigest()
    if got != ref["sha256"]:
        return ["%s at %s digests to %s, not the %s the message records"
                % (ref["path"], ref["commit"][:12], got[:16],
                   ref["sha256"][:16])]
    return []


def edits(root: Path, relative: str) -> int:
    code, out = git(root, "log", "--format=%H", "--", relative)
    return len(out.split()) if code == 0 else 0


def collect(root: Path) -> tuple[list[dict], list[str]]:
    base = root / ROOT_DIR
    messages, problems = [], []
    if not (base / "README.md").is_file():
        problems.append("%s/README.md, the protocol, is missing" % ROOT_DIR)
        return messages, problems
    for team_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        team = team_dir.name.upper()
        name = team_dir.relative_to(root).as_posix()
        if team not in TEAMS or team_dir.name != team_dir.name.lower():
            problems.append("%s is not a known team folder (known: %s)"
                            % (name, ", ".join(sorted(TEAMS)) or "none"))
            continue
        if not (team_dir / "README.md").is_file():
            problems.append("%s has no README.md saying who the team is"
                            % name)
        for child in sorted(team_dir.iterdir()):
            if child.name == "README.md":
                continue
            if not child.is_dir() or child.name not in DIRECTIONS:
                problems.append("%s/%s: only README.md, incoming/ and "
                                "outgoing/ belong in a team folder"
                                % (name, child.name))
                continue
            for path in sorted(child.iterdir()):
                relative = path.relative_to(root).as_posix()
                header, body, problem = split(path.read_bytes())
                if problem:
                    problems.append("%s %s" % (relative, problem))
                    continue
                found = check_header(header, team, child.name, path.name,
                                     body)
                problems.extend("%s: %s" % (relative, p) for p in found)
                messages.append({"path": relative, "header": header,
                                 "body": body})
    return messages, problems


def check(root: Path | None = None) -> dict:
    root = root or repository_root()
    messages, problems = collect(root)

    ids = {}
    for message in messages:
        mid = message["header"].get("id")
        if mid in ids:
            problems.append("%s: id %s is also used by %s"
                            % (message["path"], mid, ids[mid]["path"]))
        ids[mid] = message

    for message in messages:
        header, path = message["header"], message["path"]
        parent = header.get("in_reply_to")
        if parent:
            if parent not in ids:
                problems.append("%s: in_reply_to %s names no message"
                                % (path, parent))
            elif (as_date(ids[parent]["header"].get("date")) or "") > (
                    as_date(header.get("date")) or ""):
                problems.append("%s: replies to %s, which is dated later"
                                % (path, parent))
        for ref in header.get("refs") or []:
            if isinstance(ref, dict) and ref.get("repo") == THIS_REPO \
                    and not check_ref(ref):
                problems.extend("%s: %s" % (path, p)
                                for p in check_local_ref(root, ref))
        if edits(root, path) > 1:
            problems.append(
                "%s: changed by %d commits. A committed message is never "
                "edited; send a correction that replies to it."
                % (path, edits(root, path)))

    closed = {m["header"].get("in_reply_to") for m in messages
              if m["header"].get("type") in CLOSING}
    open_threads = sorted(
        (m["header"]["id"] for m in messages
         if m["header"].get("type") in OPENING
         and m["header"].get("id") not in closed))
    return {
        "messages": sorted(m["header"].get("id", m["path"])
                           for m in messages),
        "open": open_threads,
        "awaiting_act": sorted(m["header"]["id"] for m in messages
                               if m["header"].get("requires_act") is True
                               and m["header"].get("id") in open_threads),
        "findings": problems,
        "ok": not problems,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    record = check()
    if args.json:
        print(json.dumps(record, indent=2, sort_keys=True))
        return 0 if record["ok"] else 1
    print("  %d message(s)" % len(record["messages"]))
    for finding in record["findings"]:
        print("  FINDING: %s" % finding)
    print("  open: %s" % (", ".join(record["open"]) or "none"))
    if record["awaiting_act"]:
        print("  awaiting the architect: %s"
              % ", ".join(record["awaiting_act"]))
    return 0 if record["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
