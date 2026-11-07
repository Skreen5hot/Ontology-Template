# SPDX-License-Identifier: MIT
"""The communications record follows its protocol, and the checks can fail.

The live record is checked first. Then every rule in
communications/README.md that a tool can hold is broken, one at a time,
against a header that otherwise passes -- because a checker that accepts
the record and would also accept each of these is checking nothing.

A fresh project has no correspondents and no messages, so every rule is
exercised on constructed records: this repository plays `ABC`, writing to
a team `XYZ`, with the tool's own codes replaced for the duration. Owned
by the ontology template, so nothing here depends on a project's record.
"""

from __future__ import annotations

import copy
import hashlib
import shutil
import subprocess
import sys

import pytest

from conftest import load_tool

SELF = "ABC"
TEAM = "XYZ"
THIS_REPO = "owner/abc-ontology"

GOOD = {
    "id": "ABC-XYZ-2026-10-23-vendoring-pin",
    "from": "ABC",
    "to": "XYZ",
    "date": "2026-10-23",
    "type": "request",
    "subject": "A subject",
    "in_reply_to": None,
    "refs": [{"repo": "owner/xyz-ontology",
              "commit": "66131945b525c54f44e4962f32bb1f52dfa0cd12",
              "path": "ontology/apqc-ext.ttl",
              "sha256": "1b9a9375cb7303003556004effd712b63913d6aa4935"
                        "dbf604a653aec65cab4b"}],
    "author": "Aaron Damiano",
    "requires_act": False,
}
FILENAME = "2026-10-23-vendoring-pin.md"


@pytest.fixture(scope="module")
def tool():
    return load_tool("t_communications", "tools/communications.py")


@pytest.fixture
def comms(tool, monkeypatch):
    """The tool, playing ABC with one correspondent, XYZ."""
    monkeypatch.setattr(tool, "SELF", SELF)
    monkeypatch.setattr(tool, "TEAMS", {TEAM})
    monkeypatch.setattr(tool, "THIS_REPO", THIS_REPO)
    return tool


def header(**changes):
    out = copy.deepcopy(GOOD)
    for key, value in changes.items():
        if value is KeyError:
            out.pop(key)
        else:
            out[key] = value
    return out


# ---------------------------------------------------------- the record


def test_the_record_follows_the_protocol(tool, project):
    """The live record, with this project's own code and correspondents
    -- the tool unpatched."""
    assert tool.SELF == project.code()
    assert tool.TEAMS == project.correspondents()
    record = tool.check()
    assert record["ok"], record["findings"]


def test_a_record_without_its_protocol_is_refused(tool, tmp_path):
    """Guards the test above: a fresh project's record is empty, and an
    empty record passes every per-message check. The protocol file is
    the one thing it must have."""
    root = tmp_path / "r"
    (root / "communications").mkdir(parents=True)
    findings = tool.check(root)["findings"]
    assert any("the protocol, is missing" in f for f in findings), findings


def test_the_good_header_passes(comms):
    """The baseline every falsification below departs from. If it failed,
    every refusal below would be passing for the wrong reason."""
    assert comms.check_header(GOOD, TEAM, "outgoing", FILENAME, b"") == []


# ------------------------------------------------- each rule can fail


@pytest.mark.parametrize("changes, expect", [
    ({"subject": KeyError}, "header lacks subject"),
    ({"date": "2026-10-24"}, "does not match the filename"),
    ({"date": "23 Oct 2026"}, "is not YYYY-MM-DD"),
    ({"from": "XYZ", "to": "ABC"}, "from/to are XYZ -> ABC"),
    ({"id": "ABC-XYZ-2026-10-23-other"}, "its path makes it"),
    ({"type": "memo"}, "is not one of"),
    ({"type": "answer"}, "in_reply_to is null"),
    ({"requires_act": "no"}, "must be true or false"),
    ({"refs": [{"repo": "x", "commit": "6613194", "path": "p",
                "sha256": "0" * 64}]}, "not a full 40-hex SHA"),
    ({"refs": [{"repo": "x", "commit": "a" * 40, "path": "p"}]},
     "lacks sha256"),
    ({"refs": "ontology/xyz.ttl"}, "refs must be a list"),
    ({"source": GOOD["refs"][0]}, "an outgoing message has a source"),
])
def test_each_header_rule_refuses(comms, changes, expect):
    problems = comms.check_header(header(**changes), TEAM, "outgoing",
                                  FILENAME, b"")
    assert any(expect in p for p in problems), problems


def test_a_bad_filename_is_refused(comms):
    problems = comms.check_header(GOOD, TEAM, "outgoing",
                                  "Vendoring Pin.md", b"")
    assert problems == ["filename is not YYYY-MM-DD-<slug>.md"]


def test_an_incoming_copy_must_be_the_original_bytes(comms):
    """Rule: an incoming body is the original, byte for byte. A tidied
    copy -- one changed character -- is refused."""
    original = b"# Reply from XYZ\n\nAcknowledged.\n"
    incoming = header(**{"from": "XYZ", "to": "ABC",
                         "id": "XYZ-ABC-2026-10-23-vendoring-pin",
                         "type": "acknowledgment",
                         "in_reply_to": "ABC-XYZ-2026-10-23-vendoring-pin"})
    incoming["source"] = {"repo": "owner/xyz-ontology",
                          "commit": "b" * 40, "path": "comms/x.md",
                          "sha256": hashlib.sha256(original).hexdigest()}
    assert comms.check_header(incoming, TEAM, "incoming", FILENAME,
                              original) == []

    tidied = original.replace(b"Acknowledged.", b"Acknowledged!")
    assert tidied != original
    problems = comms.check_header(incoming, TEAM, "incoming", FILENAME,
                                  tidied)
    assert any("the body is not the original" in p for p in problems)

    del incoming["source"]
    problems = comms.check_header(incoming, TEAM, "incoming", FILENAME,
                                  original)
    assert any("has no source" in p for p in problems), problems


def test_a_local_ref_is_recomputed_from_its_commit(comms, tree):
    """A ref into this repository is checked against the bytes at the
    commit it names. Run against the throwaway tree, whose one commit is
    known, rather than against a commit of the template's history."""
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(tree),
                            check=True, capture_output=True
                            ).stdout.decode("utf-8").strip()
    path = "communications/README.md"
    ref = {"repo": comms.THIS_REPO, "commit": commit, "path": path,
           "sha256": hashlib.sha256((tree / path).read_bytes()).hexdigest()}
    assert comms.check_local_ref(tree, ref) == []
    wrong = dict(ref, sha256="0" * 64)
    assert any("digests to" in p for p in comms.check_local_ref(tree, wrong))
    missing = dict(ref, path="config/no-such-file.yaml")
    assert any("does not exist" in p
               for p in comms.check_local_ref(tree, missing))


# ------------------------------------------- rules about the whole tree


def message(path, fields):
    import yaml

    text = "---\n" + yaml.safe_dump(fields, sort_keys=False) + "---\n\nBody.\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


@pytest.fixture
def tree(tmp_path, repo):
    """A throwaway repository holding the protocol and one good message,
    so tree-level rules can be broken without touching the real record."""
    root = tmp_path / "r"
    (root / "config").mkdir(parents=True)
    (root / "config/repository-layout.yaml").write_bytes(b"version: 1\n")
    (root / "communications/xyz").mkdir(parents=True)
    shutil.copy(repo / "communications/README.md",
                root / "communications/README.md")
    (root / ".gitattributes").write_bytes(b"communications/** -text\n")
    (root / "communications/xyz/README.md").write_bytes(
        b"# XYZ\n\nA constructed team, for the tests.\n")
    message(root / "communications/xyz/outgoing" / FILENAME, GOOD)
    for args in (["init", "-q"], ["config", "user.email", "t@invalid"],
                 ["config", "user.name", "t"], ["add", "-A"],
                 ["commit", "-q", "-m", "one"]):
        subprocess.run(["git", *args], cwd=str(root), check=True,
                       capture_output=True)
    return root


def test_the_throwaway_tree_starts_clean(comms, tree):
    record = comms.check(tree)
    assert record["ok"], record["findings"]
    assert record["open"] == [GOOD["id"]]


def test_an_answer_closes_the_thread_it_replies_to(comms, tree):
    reply = header(**{"from": "XYZ", "to": "ABC",
                      "id": "XYZ-ABC-2026-10-24-ack", "date": "2026-10-24",
                      "type": "acknowledgment", "in_reply_to": GOOD["id"]})
    body = b"\nBody.\n"
    reply["source"] = {"repo": "owner/xyz-ontology",
                       "commit": "c" * 40, "path": "x.md",
                       "sha256": hashlib.sha256(body).hexdigest()}
    message(tree / "communications/xyz/incoming/2026-10-24-ack.md", reply)
    record = comms.check(tree)
    assert record["ok"], record["findings"]
    assert record["open"] == []


def test_a_reply_to_nothing_is_refused(comms, tree):
    stray = header(id="ABC-XYZ-2026-10-23-stray", type="answer",
                   in_reply_to="ABC-XYZ-2026-01-01-never-sent")
    message(tree / "communications/xyz/outgoing/2026-10-23-stray.md", stray)
    findings = comms.check(tree)["findings"]
    assert any("names no message" in f for f in findings), findings


def test_an_unknown_team_folder_is_refused(comms, tree):
    (tree / "communications/xyy/outgoing").mkdir(parents=True)
    findings = comms.check(tree)["findings"]
    assert any("not a known team folder" in f for f in findings), findings


def test_a_committed_message_that_is_edited_is_refused(comms, tree):
    """Rule 1. The edit is committed, because the rule is about history:
    an uncommitted edit is still a draft."""
    path = tree / "communications/xyz/outgoing" / FILENAME
    before = path.read_bytes()
    path.write_bytes(before.replace(b"Body.", b"Body, revised."))
    assert path.read_bytes() != before
    subprocess.run(["git", "commit", "-qam", "edit"], cwd=str(tree),
                   check=True, capture_output=True)
    findings = comms.check(tree)["findings"]
    assert any("never edited" in f for f in findings), findings


def git_in(tree, *args):
    return subprocess.run(["git", *args], cwd=str(tree), check=True,
                          capture_output=True).stdout.decode("utf-8").strip()


# ------------------------------------------------- protocol v1.1 rules


def test_the_record_names_the_version_it_follows(tool, repo):
    """PROTOCOL.md, "Adopting": the README names the version by commit
    and digest. The live record's statement parses."""
    adopted, problems = tool.adoption(repo)
    assert problems == [], problems
    assert adopted["version"] == "1.1"
    assert len(adopted["commit"]) == 40 and len(adopted["sha256"]) == 64


def test_a_record_without_its_version_statement_is_refused(comms, tree):
    path = tree / "communications/README.md"
    path.write_bytes(b"# Communications\n\nNo version named.\n")
    findings = comms.check(tree)["findings"]
    assert any("does not name the protocol version" in f
               for f in findings), findings


def test_a_record_git_may_rewrite_is_refused(comms, tree):
    """Rule 7: without the attribute, digests are of whatever a checkout
    made of the bytes."""
    (tree / ".gitattributes").write_bytes(b"* text=auto eol=lf\n")
    findings = comms.check(tree)["findings"]
    assert any("communications/** -text" in f for f in findings), findings


def test_a_message_may_move_with_its_bytes(comms, tree):
    """Rule 1 follows renames. A byte-identical move is one commit setting
    the bytes, as before the move."""
    old = "communications/xyz/outgoing/" + FILENAME
    new = "communications/xyz/outgoing/2026-10-23-vendoring-pin-moved.md"
    data = (tree / old).read_bytes()
    git_in(tree, "mv", old, new)
    git_in(tree, "commit", "-qm", "move")
    assert (tree / new).read_bytes() == data
    assert comms.edits(tree, new) == 1


def test_a_move_that_edits_is_refused(comms, tree):
    """Before 1.1, counting commits by path gave a moved file a fresh
    history, so a move that also edited went unnoticed."""
    old = tree / "communications/xyz/outgoing" / FILENAME
    new = "communications/xyz/outgoing/2026-10-23-vendoring-pin-moved.md"
    data = old.read_bytes().replace(b"Body.", b"Body, quietly revised.")
    git_in(tree, "rm", "-q", old.relative_to(tree).as_posix())
    (tree / new).parent.mkdir(parents=True, exist_ok=True)
    (tree / new).write_bytes(data)
    git_in(tree, "add", "-A")
    git_in(tree, "commit", "-qm", "move and edit")
    assert "R" in git_in(tree, "show", "-M", "--name-status", "--format=")
    findings = comms.check(tree)["findings"]
    assert any(new in f and "never edited" in f for f in findings), findings
    assert comms.edits(tree, new) == 2


def test_a_deleted_message_is_refused(comms, tree):
    relative = "communications/xyz/outgoing/" + FILENAME
    git_in(tree, "rm", "-q", relative)
    git_in(tree, "commit", "-qm", "delete")
    findings = comms.check(tree)["findings"]
    assert any(relative in f and "never deleted" in f
               for f in findings), findings


def test_a_file_that_was_never_a_message_may_be_removed(comms, tree):
    stray = "communications/xyz/outgoing/notes.txt"
    (tree / stray).write_bytes(b"scratch, no header\n")
    git_in(tree, "add", "-A")
    git_in(tree, "commit", "-qm", "stray")
    git_in(tree, "rm", "-q", stray)
    git_in(tree, "commit", "-qm", "remove the stray file")
    assert comms.deleted_messages(tree) == []


# --------------------------------------------------------------- alerts


def reply_in(tree):
    """XYZ's answer to the good message, recorded and committed."""
    reply = header(**{"from": "XYZ", "to": "ABC",
                      "id": "XYZ-ABC-2026-10-24-ack", "date": "2026-10-24",
                      "type": "answer", "in_reply_to": GOOD["id"],
                      "subject": "The answer"})
    reply["source"] = {"repo": "owner/xyz-ontology", "commit": "c" * 40,
                       "path": "x.md", "sha256": hashlib.sha256(
                           b"\nBody.\n").hexdigest()}
    message(tree / "communications/xyz/incoming/2026-10-24-ack.md", reply)
    git_in(tree, "add", "-A")
    git_in(tree, "commit", "-qm", "reply")
    return reply


def test_an_alert_is_bound_to_the_committed_bytes(comms, tree):
    """PROTOCOL.md, Alerts 2 and 3: the title carries the ids; the block
    names the commit that holds the file and its digest by git show; the
    link names that commit, never a branch."""
    import yaml

    relative = "communications/xyz/outgoing/" + FILENAME
    found = comms.alert(relative, tree)
    commit = git_in(tree, "log", "-1", "--format=%H", "--", relative)
    data = subprocess.run(["git", "show", "%s:%s" % (commit, relative)],
                          cwd=str(tree), check=True,
                          capture_output=True).stdout
    block = yaml.safe_load(found["yaml"])
    assert found["opens_discussion"] is True
    assert found["title"] == ("[ABC\u2192XYZ] %s \u2014 %s"
                              % (GOOD["id"], GOOD["subject"]))
    assert block["record"] == {"repo": THIS_REPO, "commit": commit,
                               "path": relative,
                               "sha256": hashlib.sha256(data).hexdigest()}
    assert block["link"].endswith("/blob/%s/%s" % (commit, relative))
    assert [k for k in block] == list(comms.ALERT_FIELDS) + ["record",
                                                            "link"]


def test_a_reply_alert_comments_on_its_root(comms, tree):
    reply_in(tree)
    found = comms.alert("communications/xyz/incoming/2026-10-24-ack.md",
                        tree)
    assert found["opens_discussion"] is False
    assert found["root"] == GOOD["id"]
    assert GOOD["id"] in found["title"]


def test_an_uncommitted_message_has_no_alert(comms, tree):
    draft = "communications/xyz/outgoing/2026-10-25-draft.md"
    message(tree / draft, header(id="ABC-XYZ-2026-10-25-draft",
                                 date="2026-10-25"))
    with pytest.raises(SystemExit):
        comms.alert(draft, tree)


def test_the_inbox_lists_what_the_record_does_not_hold(comms, tree):
    """Addressed to this record, by its code or an alias it is given, and
    not yet copied into incoming/ (matched by source.sha256)."""
    held = reply_in(tree)["source"]["sha256"]

    def post(to, sha, mid):
        return {"url": "u/" + mid, "text": (
            "Alert.\n\n```yaml\nid: %s\nfrom: XYZ\nto: %s\ntype: request"
            "\nrecord:\n  sha256: %s\n```\n" % (mid, to, sha))}

    posts = [post("ABC", held, "XYZ-ABC-held"),
             post("ABC", "1" * 64, "XYZ-ABC-new"),
             post("OLD", "2" * 64, "XYZ-OLD-alias"),
             post("QQQ", "3" * 64, "XYZ-QQQ-elsewhere"),
             {"url": "u/talk", "text": "Just talk, no alert."}]
    waiting = comms.inbox(posts, {"ABC"}, tree)
    assert [w["id"] for w in waiting] == ["XYZ-ABC-new"]
    waiting = comms.inbox(posts, {"ABC", "OLD"}, tree)
    assert [w["id"] for w in waiting] == ["XYZ-ABC-new", "XYZ-OLD-alias"]


def test_an_alert_prints_on_a_console_that_cannot_encode_its_arrow(
        comms, tree, monkeypatch):
    """An alert's title is "[A→B] ...". On a Windows console (cp1252)
    printing it raised UnicodeEncodeError before anything was posted; the
    tool writes UTF-8 whatever the console. Run through main, on a cp1252
    stream, for the throwaway tree's committed message: a project made by
    init holds none of the template's messages."""
    import io

    raw = io.BytesIO()
    console = io.TextIOWrapper(raw, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", console)
    monkeypatch.setattr(comms, "repository_root", lambda: tree)
    assert comms.main(["--alert",
                       "communications/xyz/outgoing/" + FILENAME]) == 0
    console.flush()
    assert "→" in raw.getvalue().decode("utf-8")

