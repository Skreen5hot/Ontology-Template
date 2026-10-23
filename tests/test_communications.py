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
