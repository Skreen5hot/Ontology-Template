# SPDX-License-Identifier: MIT
"""The findings register: every accepted finding, one entry each.

    python tools/findings.py        # check the register, report reviews due

A check that knows of defects it must not fail on needs a record of which
ones. The template's first record was a count per shape set, and the
Business Process Ontology port showed what a count cannot tell apart:
fixing one of 57 findings and introducing an unrelated one leaves 57, and
the gate passed. The IRI linter had no record at all, so one accepted
finding kept the Checks job red, and everything after it never ran.

So the record is per finding, by identity, in config/findings-register.yaml,
shared by every check:

  check     which tool found it: validate, iri_lint
  where     the shape set (validate) or the file (iri_lint)
  focus     the term it is about
  rule      the shape, or the lint rule
  digest    sha256 of the finding's message, first 16 hex digits
  severity  Violation, Warning or Info

and, for a person to read and answer for:

  reason    why it is accepted rather than fixed
  owner     who answers for it
  review    the date by which it is looked at again (YYYY-MM-DD)
  upstream  optional, "<SOURCE> <IRI>": the defect is in a pinned
            upstream's term, not in this ontology (CCO's Organization not
            being an Agent, for one)
  text      optional, the message, for the reader; not matched

POLICY (decision 11)

  A new Violation fails.
  A new Warning fails unless recorded. A warning nobody has to answer for
  is a warning nobody reads.
  A new Info is reported and does not fail.
  An entry that matches nothing fails: the fix is recorded by removing it,
  in the commit that fixes it, so the reduction is in a diff.
  An expired review date is reported, not failed.

A finding against an upstream term -- a focus in a pinned namespace -- can
only be accepted by an entry that names the upstream, so a defect in an
extract is never filed as one in this ontology.

Entries are written by a person. `--propose` on each check prints entries
for its new findings, with the reason, owner and review left for whoever
accepts them; an entry without them is refused.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import layout  # noqa: E402

REGISTER = "config/findings-register.yaml"
PINS = "config/upstream-sources.yaml"
CHECKS = ("validate", "iri_lint")
SEVERITIES = ("Violation", "Warning", "Info")
GATING = ("Violation", "Warning")
IDENTITY = ("check", "where", "focus", "rule", "digest", "severity")
REQUIRED = ("reason", "owner", "review")
OPTIONAL = ("upstream", "text")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RegisterError(SystemExit):
    """The register cannot be read as entries, so no check can use it."""


def digest(message) -> str:
    return hashlib.sha256(str(message or "").encode("utf-8")).hexdigest()[:16]


def finding(check, where, focus, rule, message, severity) -> dict:
    """A finding as the register identifies it, with its message kept for
    the report."""
    return {"check": check, "where": where, "focus": focus or "",
            "rule": rule or "", "digest": digest(message),
            "severity": severity or "Violation", "message": message or ""}


def identity(record: dict) -> tuple:
    return tuple(record.get(key) or "" for key in IDENTITY)


def upstream_ids(root: Path | None = None) -> dict:
    """Pinned upstream id (upper case) -> namespace."""
    import yaml

    root = root or layout.repository_root()
    raw = yaml.safe_load((root / PINS).read_text(encoding="utf-8")) or {}
    return {entry["id"].upper(): entry["namespace"]
            for entry in raw.get("sources") or []}


def problems_of(entries: list, today: datetime.date | None = None,
                sources: dict | None = None) -> list[str]:
    """Every way an entry can be unusable. Each is a reason to refuse the
    register, not one entry: a check that skipped a bad entry would fail
    on the finding it was meant to accept, for a reason it did not say."""
    sources = upstream_ids() if sources is None else sources
    out, seen = [], {}
    for index, entry in enumerate(entries):
        name = "entry %d" % (index + 1)
        if not isinstance(entry, dict):
            out.append("%s is not a mapping" % name)
            continue
        unknown = sorted(set(entry) - set(IDENTITY) - set(REQUIRED)
                         - set(OPTIONAL))
        if unknown:
            out.append("%s has unknown field(s): %s"
                       % (name, ", ".join(unknown)))
        for key in IDENTITY + REQUIRED:
            if not str(entry.get(key) or "").strip():
                out.append("%s has no %s" % (name, key))
        if entry.get("check") and entry["check"] not in CHECKS:
            out.append("%s: check %r is not one of %s"
                       % (name, entry["check"], ", ".join(CHECKS)))
        if entry.get("severity") and entry["severity"] not in SEVERITIES:
            out.append("%s: severity %r is not one of %s"
                       % (name, entry["severity"], ", ".join(SEVERITIES)))
        review = str(entry.get("review") or "")
        if review and not DATE.match(review):
            out.append("%s: review %r is not a date (YYYY-MM-DD)"
                       % (name, review))
        elif review:
            try:
                datetime.date.fromisoformat(review)
            except ValueError:
                out.append("%s: review %r is not a date" % (name, review))
        for key in REQUIRED:
            if "TODO" in str(entry.get(key) or ""):
                out.append("%s: %s is still the proposal's placeholder"
                           % (name, key))
        if entry.get("upstream"):
            parts = str(entry["upstream"]).split()
            if (len(parts) != 2 or parts[0] not in sources
                    or not parts[1].startswith(sources[parts[0]])):
                out.append(
                    "%s: upstream %r is not '<SOURCE> <IRI>' with SOURCE "
                    "one of %s and the IRI in its namespace"
                    % (name, entry["upstream"], ", ".join(sorted(sources))))
        elif str(entry.get("focus") or "").startswith(
                tuple(sources.values())):
            out.append("%s: its focus is an upstream term, so it must name "
                       "the upstream (upstream: <SOURCE> <IRI>)" % name)
        key = identity(entry)
        if key in seen:
            out.append("%s repeats entry %d" % (name, seen[key] + 1))
        else:
            seen[key] = index
    return out


def load(root: Path | None = None) -> list[dict]:
    import yaml

    root = root or layout.repository_root()
    path = root / REGISTER
    if not path.is_file():
        raise RegisterError(
            REGISTER + " is missing. It records the findings this "
            "repository accepts; without it every finding is new, and "
            "nothing says so but the failure.")
    # libyaml's loader where PyYAML has it: a ported ontology's register
    # runs to thousands of entries, and the pure-Python one took 9 s to
    # read the BPO port's 3,717 -- once per check, once per site build.
    loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
    raw = yaml.load(path.read_text(encoding="utf-8"), Loader=loader) or {}
    entries = raw.get("entries") or []
    if not isinstance(entries, list):
        raise RegisterError(REGISTER + ": entries is not a list")
    problems = problems_of(entries, sources=upstream_ids(root))
    if problems:
        raise RegisterError(
            REGISTER + " cannot be used:\n" + "\n".join(
                "  " + p for p in problems))
    for entry in entries:
        entry["review"] = str(entry["review"])
    return entries


def judge(check: str, findings: list, entries: list,
          today: datetime.date | None = None, complete: bool = True) -> dict:
    """Each finding of one check, accepted or new; each of its entries,
    matched or stale; and the entries whose review is due.

    `complete` says the check ran over its whole scope. A run over part
    of it (the linter on one file) cannot say an entry for another part
    matches nothing, so it reports no stale entries.
    """
    today = today or datetime.date.today()
    mine = [e for e in entries if e["check"] == check]
    by_key = {identity(e): e for e in mine}
    accepted, new, matched = [], [], set()
    for record in findings:
        key = identity(record)
        if key in by_key:
            accepted.append(record)
            matched.add(key)
        else:
            new.append(record)
    stale = ([e for e in mine if identity(e) not in matched]
             if complete else [])
    expired = [e for e in mine
               if datetime.date.fromisoformat(e["review"]) < today]
    failing = [r for r in new if r["severity"] in GATING]
    return {"accepted": accepted, "new": new, "stale": stale,
            "expired": expired, "failing": failing,
            "passed": not failing and not stale}


def report(check: str, verdict: dict, out=sys.stdout) -> None:
    """The verdict in words. Every new and stale item is listed, not a
    sample: the list is what the person fixing them works from."""
    print("  register: %d accepted, %d new (%d failing), %d stale, %d "
          "due for review" % (len(verdict["accepted"]), len(verdict["new"]),
                              len(verdict["failing"]), len(verdict["stale"]),
                              len(verdict["expired"])), file=out)
    for record in verdict["new"]:
        print("  NEW %s %s %s %s: %s" % (
            record["severity"], record["where"], record["rule"],
            record["focus"], record["message"][:300]), file=out)
    for entry in verdict["stale"]:
        print("  STALE %s %s %s %s -- it matches nothing; if it was fixed, "
              "remove the entry in this commit" % (
                  entry["severity"], entry["where"], entry["rule"],
                  entry["focus"]), file=out)
    for entry in verdict["expired"]:
        print("  REVIEW DUE %s (%s): %s %s, owner %s" % (
            entry["review"], entry["severity"], entry["rule"],
            entry["focus"], entry["owner"]), file=out)
    if verdict["new"]:
        print("  To accept a new finding instead of fixing it, add its "
              "entry to %s with a reason, owner and review date; --propose "
              "prints the entries." % REGISTER, file=out)


def propose(records: list, reason: str | None = None,
            owner: str | None = None, review: str | None = None) -> str:
    """Register entries for `records`, as YAML to paste under `entries:`.
    What is not given is left as a placeholder the register refuses."""
    import yaml

    out, seen = [], set()
    for record in records:
        if identity(record) in seen:
            continue
        seen.add(identity(record))
        entry = {key: record[key] for key in IDENTITY}
        entry["text"] = record["message"][:300]
        entry["reason"] = reason or "TODO why this is accepted, not fixed"
        entry["owner"] = owner or "TODO who answers for it"
        entry["review"] = review or "TODO YYYY-MM-DD"
        out.append(entry)
    return yaml.safe_dump(out, sort_keys=False, allow_unicode=True,
                          width=100) if out else ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args(argv)
    entries = load()
    today = datetime.date.today()
    by_check = {c: sum(1 for e in entries if e["check"] == c)
                for c in CHECKS}
    print("  %s: %d entr%s (%s)" % (
        REGISTER, len(entries), "y" if len(entries) == 1 else "ies",
        ", ".join("%s %d" % item for item in by_check.items())))
    upstream = [e for e in entries if e.get("upstream")]
    if upstream:
        print("  %d about upstream terms" % len(upstream))
    for entry in entries:
        if datetime.date.fromisoformat(entry["review"]) < today:
            print("  REVIEW DUE %s: %s %s %s, owner %s" % (
                entry["review"], entry["check"], entry["rule"],
                entry["focus"], entry["owner"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
