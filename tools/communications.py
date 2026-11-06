# SPDX-License-Identifier: MIT
"""Check the communications record, and say which threads are open.

    python tools/communications.py          # findings, then open threads
    python tools/communications.py --json   # the same, as one JSON object
    python tools/communications.py --alert communications/<team>/outgoing/<file>.md
    python tools/communications.py --inbox [--code OT]   # needs `gh`

The protocol is the shared one, Skreen5hot/communications PROTOCOL.md,
at the version communications/README.md names. This is the part of it a
tool can hold: the README names the version it follows by commit and
digest, and .gitattributes keeps the record's bytes; the header has every
field and each is well formed; the id, date, team and direction agree
with where the file sits; a reply names a message that exists and is not
later than itself; every ref names a commit and a digest, and a ref into
this repository still matches; an incoming copy's body is the original's
bytes; no committed message has had its bytes set by more than one
commit, following renames, so a move is allowed and a move that edits is
not; and no message has been deleted.

`--alert` prints the alert the board takes for a committed message: the
title, whether it opens a Discussion or comments on its thread's, and
the YAML block, bound to the commit that set the file and its digest.
It posts nothing. `--inbox` reads the board's Alerts with `gh` and lists
each one addressed to this record (its code, or any `--code` it is also
known by) whose digest no incoming copy's `source.sha256` holds.

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
#: The README's adoption statement (PROTOCOL.md, "Adopting"), and the
#: attribute line that keeps the record's bytes as committed (Rule 7).
ADOPTION = re.compile(
    r"follows the communications protocol, version (\d+\.\d+):\s*"
    r"Skreen5hot/communications, PROTOCOL\.md at ([0-9a-f]{40}), "
    r"sha256 ([0-9a-f]{64})")
ATTRIBUTE = "communications/** -text"
#: Where the board is, and the link an alert gives.
BOARD = ("Skreen5hot", "communications")
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
    """How many commits set the file's bytes, following renames.

    Read from `git log --raw`: a commit counts when the blob it leaves
    differs from the one it found, so adding the file counts, a rename
    that keeps the bytes does not, and a rename that also edits does
    (PROTOCOL.md, Rule 1)."""
    code, out = git(root, "log", "--follow", "-M", "--raw", "--no-abbrev",
                    "--format=%x01%H", "--", relative)
    if code:
        return 0
    count = 0
    for chunk in out.decode("utf-8", "replace").split("\x01")[1:]:
        for line in chunk.splitlines()[1:]:
            if not line.startswith(":"):
                continue
            old, new = line.split()[2:4]
            if old != new:
                count += 1
                break
    return count


def deleted_messages(root: Path) -> list[str]:
    """Message files history has deleted (Rule 1). A rename is not a
    deletion (`-M`), and a file that never had a header was never a
    message, so removing it is allowed."""
    code, out = git(root, "log", "-M", "--diff-filter=D", "--name-only",
                    "--format=%x01%H", "--", ROOT_DIR)
    if code:
        return []
    found = []
    for chunk in out.decode("utf-8", "replace").split("\x01")[1:]:
        lines = [line for line in chunk.splitlines() if line.strip()]
        commit, paths = lines[0], lines[1:]
        for relative in paths:
            parts = relative.split("/")
            if len(parts) != 4 or parts[2] not in DIRECTIONS:
                continue
            code, data = git(root, "show", "%s^:%s" % (commit, relative))
            if code == 0 and split(data)[0] is not None:
                found.append("%s: deleted by %s. A message is never "
                             "deleted." % (relative, commit[:12]))
    return found


def adoption(root: Path) -> tuple[dict | None, list[str]]:
    """The protocol version the README says it follows, and what is wrong
    with how the record adopts it."""
    problems = []
    path = root / ROOT_DIR / "README.md"
    readme = path.read_bytes().decode("utf-8") if path.is_file() else ""
    match = ADOPTION.search(" ".join(readme.split()))
    adopted = None
    if not match:
        problems.append(
            "%s/README.md does not name the protocol version it follows, "
            "as 'This record follows the communications protocol, version "
            "<n.n>: Skreen5hot/communications, PROTOCOL.md at <commit>, "
            "sha256 <digest>.'" % ROOT_DIR)
    else:
        adopted = {"version": match.group(1), "commit": match.group(2),
                   "sha256": match.group(3)}
    attributes = root / ".gitattributes"
    lines = (attributes.read_bytes().decode("utf-8").splitlines()
             if attributes.is_file() else [])
    if ATTRIBUTE not in (line.strip() for line in lines):
        problems.append(
            ".gitattributes lacks '%s', so git may rewrite the record's "
            "line endings and its digests stop being of committed bytes "
            "(Rule 7)" % ATTRIBUTE)
    return adopted, problems


def collect(root: Path) -> tuple[list[dict], list[str]]:
    base = root / ROOT_DIR
    messages, problems = [], []
    if not (base / "README.md").is_file():
        problems.append("%s/README.md, the protocol, is missing" % ROOT_DIR)
        return messages, problems
    problems.extend(adoption(root)[1])
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

    problems.extend(deleted_messages(root))

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
        "protocol": adoption(root)[0],
        "findings": problems,
        "ok": not problems,
    }


# --------------------------------------------------------------- alerts


#: The header fields an alert carries, in the protocol's order.
ALERT_FIELDS = ("id", "from", "to", "type", "subject", "in_reply_to",
                "requires_act", "author")


def alert(relative: str, root: Path | None = None) -> dict:
    """The alert for one committed message (PROTOCOL.md, "Alerts").

    Bound to the latest commit that has the file at this path, read with
    `git show`, so the digest is of committed bytes (Rule 7). A message
    that opens a thread opens a Discussion; a reply comments on its
    root's, unless the root was never announced, which the caller knows
    and this does not."""
    import yaml

    root = root or repository_root()
    code, out = git(root, "log", "-1", "--format=%H", "--", relative)
    commit = out.decode("utf-8").strip()
    if code or not commit:
        raise SystemExit("%s is not committed; an alert names the commit "
                         "that holds the message" % relative)
    code, data = git(root, "show", "%s:%s" % (commit, relative))
    header, _body, problem = split(data)
    if problem:
        raise SystemExit("%s %s" % (relative, problem))
    by_id = {m["header"].get("id"): m["header"] for m in collect(root)[0]}
    top = header
    while top.get("in_reply_to") in by_id:
        top = by_id[top["in_reply_to"]]
    block = {field: header.get(field) for field in ALERT_FIELDS}
    block["record"] = {"repo": THIS_REPO, "commit": commit, "path": relative,
                       "sha256": hashlib.sha256(data).hexdigest()}
    block["link"] = "https://github.com/%s/blob/%s/%s" % (THIS_REPO, commit,
                                                          relative)
    return {
        "title": "[%s\u2192%s] %s \u2014 %s" % (top["from"], top["to"],
                                                 top["id"], top["subject"]),
        "root": top["id"],
        "opens_discussion": top is header,
        "yaml": yaml.safe_dump(block, sort_keys=False, allow_unicode=True,
                               width=1000),
    }


def alerts_in(text: str) -> list[dict]:
    """The YAML alert blocks in a Discussion's or comment's text: each
    fenced block that parses to a mapping with an id and a record."""
    import yaml

    found = []
    for block in re.findall(r"```(?:ya?ml)?\s*\n(.*?)```", text or "", re.S):
        try:
            parsed = yaml.safe_load(block)
        except Exception:  # yaml raises several types
            continue
        if (isinstance(parsed, dict) and parsed.get("id")
                and isinstance(parsed.get("record"), dict)):
            found.append(parsed)
    return found


def board_posts() -> list[dict]:
    """Every Discussion in the board's Alerts category and its comments,
    as [{url, text}], read with `gh`."""
    query = ("query($o:String!,$n:String!){repository(owner:$o,name:$n){"
             "discussions(first:100,orderBy:{field:CREATED_AT,direction:DESC})"
             "{nodes{url body category{name} comments(first:100)"
             "{nodes{url body}}}}}}")
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", "query=" + query,
         "-F", "o=" + BOARD[0], "-F", "n=" + BOARD[1]],
        capture_output=True)
    if result.returncode:
        raise SystemExit("could not read the board with gh: %s"
                         % result.stderr.decode("utf-8", "replace").strip())
    nodes = json.loads(result.stdout)["data"]["repository"]["discussions"][
        "nodes"]
    posts = []
    for node in nodes:
        if node["category"]["name"] != "Alerts":
            continue
        posts.append({"url": node["url"], "text": node["body"]})
        posts.extend({"url": c["url"], "text": c["body"]}
                     for c in node["comments"]["nodes"])
    return posts


def inbox(posts: list[dict], codes: set[str],
          root: Path | None = None) -> list[dict]:
    """Alerts addressed to one of `codes` whose message the record does
    not hold: no incoming copy's source.sha256 is the alert's digest."""
    held = {(m["header"].get("source") or {}).get("sha256")
            for m in collect(root or repository_root())[0]}
    waiting = []
    for post in posts:
        for found in alerts_in(post["text"]):
            if (found.get("to") in codes
                    and found["record"].get("sha256") not in held):
                waiting.append(dict(found, url=post["url"]))
    return waiting


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--alert", metavar="MESSAGE",
                    help="print the alert for a committed message")
    ap.add_argument("--inbox", action="store_true",
                    help="list the board's alerts this record does not hold")
    ap.add_argument("--code", action="append", default=[],
                    help="another code this record is known by on the board")
    args = ap.parse_args(argv)
    # An alert's title carries an arrow, and a Windows console's code page
    # cannot print it: write UTF-8 whatever the console, as the shared
    # protocol's tools/alert.py does.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if args.alert:
        found = alert(args.alert)
        if found["opens_discussion"]:
            print("  a new Discussion in Alerts, titled:")
        else:
            print("  a comment on the Discussion for %s, titled:"
                  % found["root"])
        print("  " + found["title"])
        print()
        print("```yaml\n" + found["yaml"] + "```")
        return 0
    if args.inbox:
        waiting = inbox(board_posts(), {SELF, *args.code})
        for found in waiting:
            print("  waiting  %s  (%s, %s)\n           %s"
                  % (found["id"], found.get("type"), found["record"].get(
                      "sha256", "")[:16], found["url"]))
        print("  %d alert(s) waiting" % len(waiting))
        return 0
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
