# SPDX-License-Identifier: MIT
"""The source register, and whether each decision's citations are adequate.

    python tools/sources.py            # check; exit 1 on a finding
    python tools/sources.py --write    # regenerate research/sources.md
    python tools/sources.py --json     # the findings and the citations

METHOD section 4's source adequacy gate (P4, template decision 36): a
source a design decision relies on has been read in the primary text, or
the reliance is individually excused, before the decision cites it. BCO
graded every claim in its register, and still a source stayed secondary
only until its closure set, because nothing compared what the decisions
cited with how each source had been read. This compares them.

THE REGISTER, research/sources.yaml

  entries     each source: id (SRC-<FAMILY>-<NN>), citation, and optional
              urls ([{label, url}]), access_terms, summary, quotes
              ([{key: <id>-Q<n>, text}]) and claims
  claims      [{id: C<n>, status, scope, note}]: what was read, and how.
              status is exactly one of
                V  read in the primary text
                P  part of the primary text read
                S  secondary only
                K  prior knowledge
                L  behind a login or paywall: the primary not read
              A V or P claim states its scope, the part of the primary
              text examined: reading clauses 1 to 5 says nothing of the
              annexes. A claim's id is explicit and stable, so a citation
              never depends on the claim's place in the list.
  exceptions  [{citation, in, scope, reason, approved_by}]: one citation,
              in one decision file, excused by a named person in a role
              allowed to excuse it (config/sources.yaml). An exception
              never changes a grade: the claim stays what it was.

Prose in an entry carries no typed quotation mark: a quotation comes from
a registered quote, placed as {Q1}, and a title or a term's name from a
declared mention, {mention:...}. So every verbatim quotation is in the
quotes list, where a limit, if the project sets one, can see it.

CITATIONS, in the decision files config/sources.yaml names

  SRC-STD-01-C1         cites claim C1: adequate if it is V or P
  SRC-STD-01            cites the source whole: adequate if it has at least
                        one claim and every claim is V or P. That says
                        every claim registered was read; it does not say
                        the register covers the whole source. Where a
                        decision rests on a passage, cite the claim.
  mention:SRC-STD-01    mentions the source, as background, without resting
                        on it: never evaluated

Anything else is inadequate unless an exception names that citation in
that file. An exception whose citation is gone from its file, or whose
citation is now adequate, is stale: what it excused no longer needs it.

What a finding here refuses, each naming the entry or the file:

- a register entry or claim with a missing, unknown or malformed field; a
  repeated id; a claim without exactly one grade; a V or P claim without
  its scope;
- a quote key not of its entry, repeated or malformed; a quote longer
  than the project's limit, if it sets one; a typed quotation mark in
  entry prose; a placeholder naming no quote;
- an SRC identifier, claim key or quote key, in any tracked text file,
  that names nothing;
- an inadequate citation in a decision file with no exception for it;
- an exception malformed, repeated, approved in a role not allowed, or
  stale;
- a research/sources.md that differs from a fresh generation.

It never grades a source and never reads one: a grade is a person's
statement of how they read it, and the check holds decisions to the
statement. It cannot find a source a decision relies on but does not
cite. With no citations, it passes and says so: zero citations evaluated
is not evidence that the decisions are well sourced.

Exit codes: 0 no findings; 1 findings.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import findings  # noqa: E402
import layout  # noqa: E402

REGISTER = "research/sources.yaml"
OUTPUT = "research/sources.md"
CONFIG = "config/sources.yaml"
GRADES = ("V", "P", "S", "K", "L")
ADEQUATE = ("V", "P")
FORMATS = (1,)

ENTRY_ID = re.compile(r"^SRC-([A-Z][A-Z0-9]*)-(\d{2,})$")
CLAIM_ID = re.compile(r"^C[1-9][0-9]*$")
QUOTE_KEY = re.compile(r"^(SRC-[A-Z][A-Z0-9]*-\d{2,})-Q[1-9][0-9]*$")
#: An SRC reference in running text: an entry, a claim (-C<n>) or a quote
#: (-Q<n>), and the shorthand continuations BCO's prose uses
#: (SRC-FO-01, -02 and SRC-OG-01/02). Not preceded by "mention:", which is
#: MENTION's, nor by a letter, digit or hyphen.
REFERENCE = re.compile(
    r"(?<![A-Za-z0-9:\-])SRC-([A-Z][A-Z0-9]*)-(\d{2,})(?:-([CQ][1-9][0-9]*))?"
    r"((?:(?:/|,\s*-)\d{2,})*)")
MENTION = re.compile(r"mention:SRC-([A-Z][A-Z0-9]*)-(\d{2,})"
                     r"(?:-([CQ][1-9][0-9]*))?")
CONTINUATION = re.compile(r"\d{2,}")
#: A reference's entry, and its claim or quote, if it names one.
PARTS = re.compile(r"(SRC-[A-Z][A-Z0-9]*-\d{2,})(?:-([CQ][1-9][0-9]*))?")
PLACEHOLDER = re.compile(r"\{([^{}]*)\}")
TYPED_QUOTES = ("\"", "\u201c", "\u201d", "\u201e", "\u00ab", "\u00bb")
#: The suffixes the reference scan reads: text a person writes.
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".ttl", ".tsv", ".csv", ".txt"}

TOP_FIELDS = {"format_version", "entries", "exceptions"}
ENTRY_FIELDS = {"id", "citation", "urls", "access_terms", "summary",
                "quotes", "claims"}
CLAIM_FIELDS = {"id", "status", "scope", "note"}
QUOTE_FIELDS = {"key", "text"}
URL_FIELDS = {"label", "url"}
EXCEPTION_FIELDS = ("citation", "in", "scope", "reason", "approved_by")

DEFAULTS = {
    "decisions": ["docs/decisions/**/*.md", "docs/standards/**/*.md",
                  "docs/charter.md"],
    "exception_approvers": [{"kind": "architect"}],
    "max_quote_words": None,
    "scan_exclude": ["docs/template/**"],
}


class Unreadable(SystemExit):
    """A file this reads cannot be read as what it should be."""


# --------------------------------------------------------------- reading


def configuration(root: Path) -> dict:
    import yaml

    path = root / CONFIG
    raw = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}
           if path.is_file() else {})
    unknown = sorted(set(raw) - set(DEFAULTS) - {"version"})
    if unknown:
        raise Unreadable("%s: unknown setting(s) %s"
                         % (CONFIG, ", ".join(unknown)))
    out = dict(DEFAULTS)
    out.update({k: v for k, v in raw.items() if k in DEFAULTS})
    limit = out["max_quote_words"]
    if limit is not None and (not isinstance(limit, int) or limit < 1):
        raise Unreadable("%s: max_quote_words %r is not a positive whole "
                         "number, or null" % (CONFIG, limit))
    return out


def register(root: Path) -> dict:
    import yaml

    path = root / REGISTER
    if not path.is_file():
        raise Unreadable(REGISTER + " is missing; it is the source register "
                         "every SRC identifier resolves against")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if raw.get("format_version") not in FORMATS:
        raise Unreadable("%s: format_version %r is not one of %s"
                         % (REGISTER, raw.get("format_version"), FORMATS))
    return raw


# ----------------------------------------------------- the register's rules


def prose(entry: dict) -> list[tuple[str, str]]:
    """(where, text) for every field of an entry a person writes as prose."""
    out = []
    for key in ("citation", "access_terms", "summary"):
        if entry.get(key):
            out.append((key, str(entry[key])))
    for url in entry.get("urls") or []:
        if isinstance(url, dict) and url.get("label"):
            out.append(("urls label", str(url["label"])))
    for claim in entry.get("claims") or []:
        if isinstance(claim, dict):
            for key in ("scope", "note"):
                if claim.get(key):
                    out.append(("claim %s %s" % (claim.get("id"), key),
                                str(claim[key])))
    return out


def register_problems(raw: dict, settings: dict) -> list[str]:
    """Every way the register is unusable, each naming the entry."""
    out = []
    unknown = sorted(set(raw) - TOP_FIELDS)
    if unknown:
        out.append("the register has unknown field(s): %s"
                   % ", ".join(unknown))
    seen = set()
    limit = settings["max_quote_words"]
    for index, entry in enumerate(raw.get("entries") or []):
        if not isinstance(entry, dict):
            out.append("entry %d is not a mapping" % (index + 1))
            continue
        name = str(entry.get("id") or "entry %d" % (index + 1))
        for key in sorted(set(entry) - ENTRY_FIELDS):
            out.append("%s: unknown field %s" % (name, key))
        for key in ("id", "citation"):
            if not str(entry.get(key) or "").strip():
                out.append("%s has no %s" % (name, key))
        if entry.get("id") and not ENTRY_ID.match(str(entry["id"])):
            out.append("%s: id is not SRC-<FAMILY>-<NN>" % name)
        if name in seen:
            out.append("%s is listed twice" % name)
        seen.add(name)
        for url in entry.get("urls") or []:
            if not isinstance(url, dict) or not url.get("url") or set(
                    url) - URL_FIELDS:
                out.append("%s: a url is not {label, url}" % name)
        claims = entry.get("claims") or []
        if not isinstance(claims, list):
            out.append("%s: claims is not a list" % name)
            claims = []
        claim_ids = set()
        for c_index, claim in enumerate(claims):
            where = "%s claim %d" % (name, c_index + 1)
            if not isinstance(claim, dict):
                out.append("%s is not a mapping" % where)
                continue
            for key in sorted(set(claim) - CLAIM_FIELDS):
                out.append("%s: unknown field %s" % (where, key))
            claim_id = str(claim.get("id") or "")
            if not CLAIM_ID.match(claim_id):
                out.append("%s: id %r is not C<n>; a claim's id is explicit "
                           "and stable, never its place in the list"
                           % (where, claim.get("id")))
            elif claim_id in claim_ids:
                out.append("%s: id %s is repeated" % (where, claim_id))
            claim_ids.add(claim_id)
            status = claim.get("status")
            if status not in GRADES:
                out.append("%s: status %r is not exactly one of %s"
                           % (where, status, ", ".join(GRADES)))
            elif status in ADEQUATE and not str(
                    claim.get("scope") or "").strip():
                out.append("%s: a %s claim states its scope, the part of the "
                           "primary text examined" % (where, status))
        quote_keys = set()
        for quote in entry.get("quotes") or []:
            if not isinstance(quote, dict) or set(quote) - QUOTE_FIELDS:
                out.append("%s: a quote is not {key, text}" % name)
                continue
            key = str(quote.get("key") or "")
            match = QUOTE_KEY.match(key)
            if not match or match.group(1) != name:
                out.append("%s: quote key %r is not %s-Q<n>"
                           % (name, key, name))
            elif key in quote_keys:
                out.append("%s: quote key %s is repeated" % (name, key))
            quote_keys.add(key)
            words = len(str(quote.get("text") or "").split())
            if limit is not None and words > limit:
                out.append("%s: quote %s has %d words; this project's limit "
                           "is %d (config/sources.yaml)"
                           % (name, key, words, limit))
        for where, text in prose(entry):
            outside = PLACEHOLDER.sub("", text)
            if any(mark in outside for mark in TYPED_QUOTES):
                out.append("%s: %s has a typed quotation mark; a quotation "
                           "is a registered quote, {Q<n>}, and a title a "
                           "mention, {mention:...}" % (name, where))
            for token in PLACEHOLDER.findall(text):
                if token.startswith("mention:"):
                    continue
                if not re.fullmatch(r"Q[1-9][0-9]*", token) or (
                        "%s-%s" % (name, token)) not in quote_keys:
                    out.append("%s: %s has the placeholder {%s}, which "
                               "names no quote of this entry"
                               % (name, where, token))
    return out


# ----------------------------------------------------------- references


def index(raw: dict) -> dict:
    """{entry id: {"claims": {id: status}, "quotes": set}}."""
    out = {}
    for entry in raw.get("entries") or []:
        if isinstance(entry, dict) and entry.get("id"):
            out[str(entry["id"])] = {
                "claims": {str(c.get("id")): c.get("status")
                           for c in entry.get("claims") or []
                           if isinstance(c, dict)},
                "quotes": {str(q.get("key")) for q in entry.get("quotes")
                           or [] if isinstance(q, dict)}}
    return out


def references(text: str) -> list[str]:
    """Every SRC citation in `text`, expanded, in order; never a mention."""
    out = []
    for match in REFERENCE.finditer(text):
        family, number, part, rest = match.groups()
        out.append("SRC-%s-%s%s" % (family, number,
                                    "-" + part if part else ""))
        for more in CONTINUATION.findall(rest or ""):
            out.append("SRC-%s-%s" % (family, more))
    return out


def mentions(text: str) -> list[str]:
    return ["SRC-%s-%s%s" % (f, n, "-" + p if p else "")
            for f, n, p in MENTION.findall(text)]


def resolves(reference: str, known: dict) -> bool:
    entry, part = PARTS.fullmatch(reference).groups()
    if entry not in known:
        return False
    if part is None:
        return True
    if part.startswith("C"):
        return part in known[entry]["claims"]
    return reference in known[entry]["quotes"]


def tracked_text(root: Path, settings: dict) -> list[str]:
    result = subprocess.run(["git", "ls-files"], cwd=str(root),
                            capture_output=True, text=True)
    names = result.stdout.split() if result.returncode == 0 else []
    return sorted(n for n in names
                  if Path(n).suffix in TEXT_SUFFIXES
                  and not any(fnmatch.fnmatch(n, g)
                              for g in settings["scan_exclude"]))


def unresolved(root: Path, names: list[str], known: dict) -> list[str]:
    out = []
    for name in names:
        path = root / name
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for reference in references(text) + mentions(text):
            if not resolves(reference, known):
                out.append("%s: %s names nothing in %s"
                           % (name, reference, REGISTER))
    return sorted(set(out))


# -------------------------------------------------------------- adequacy


def adequate(reference: str, known: dict) -> bool:
    """A claim graded V or P; or a source with at least one claim, every
    one V or P (a quote key cites its source whole)."""
    entry = re.sub(r"-[CQ][1-9][0-9]*$", "", reference)
    claims = known.get(entry, {}).get("claims", {})
    match = re.search(r"-(C[1-9][0-9]*)$", reference)
    if match:
        return claims.get(match.group(1)) in ADEQUATE
    return bool(claims) and all(s in ADEQUATE for s in claims.values())


def decision_files(root: Path, settings: dict) -> list[str]:
    out = set()
    for pattern in settings["decisions"]:
        for path in root.glob(pattern):
            if path.is_file():
                out.add(path.relative_to(root).as_posix())
    return sorted(out)


def approvers(root: Path, settings: dict) -> tuple[set, list[str]]:
    """The kinds allowed to approve an exception, and what is wrong with
    the list: a kind other than the architect needs a recorded delegation,
    a decision file that exists (decision 36: adding a kind confers no
    authority by itself)."""
    kinds, problems = set(), []
    declared = findings.review_kinds(root)
    for item in settings["exception_approvers"] or []:
        kind = str((item or {}).get("kind") or "")
        if kind not in declared:
            problems.append("%s: exception approver %r is not a kind "
                            "config/review.yaml declares" % (CONFIG, kind))
            continue
        if kind != "architect":
            record = str((item or {}).get("delegated_by") or "")
            if not record or not (root / record).is_file():
                problems.append(
                    "%s: %s may approve exceptions only by a recorded "
                    "delegation; delegated_by names no decision file"
                    % (CONFIG, kind))
                continue
        kinds.add(kind)
    return kinds, problems


def adequacy(root: Path, raw: dict, settings: dict) -> dict:
    """Each citation in each decision file, as adequate, excused or
    inadequate; each exception used or stale; and the problems."""
    known = index(raw)
    allowed, problems = approvers(root, settings)
    files = decision_files(root, settings)
    cited = {}
    for name in files:
        text = (root / name).read_text(encoding="utf-8", errors="replace")
        cited[name] = (references(text), mentions(text))
    exceptions = {}
    for i, item in enumerate(raw.get("exceptions") or []):
        where = "exception %d" % (i + 1)
        if not isinstance(item, dict):
            problems.append("%s is not a mapping" % where)
            continue
        for key in sorted(set(item) - set(EXCEPTION_FIELDS)):
            problems.append("%s: unknown field %s" % (where, key))
        missing = [k for k in EXCEPTION_FIELDS
                   if not str(item.get(k) or "").strip()]
        if missing:
            problems.append("%s has no %s" % (where, ", ".join(missing)))
            continue
        key = (str(item["citation"]), str(item["in"]))
        if key in exceptions:
            problems.append("%s repeats the exception for %s in %s"
                            % (where, key[0], key[1]))
        exceptions[key] = item
        match = findings.CLASSIFIED_BY.match(str(item["approved_by"]))
        if not match:
            problems.append("%s: approved_by %r is not '<name> (<kind>)'"
                            % (where, item["approved_by"]))
        elif match.group("kind") not in allowed:
            problems.append("%s: approved as %s, which may not approve a "
                            "source exception here (%s)"
                            % (where, match.group("kind"),
                               ", ".join(sorted(allowed)) or "none"))
        if key[1] not in cited:
            problems.append("%s: %s is not a decision file %s names"
                            % (where, key[1], CONFIG))
        elif key[0] not in cited[key[1]][0]:
            problems.append("%s is stale: %s no longer cites %s"
                            % (where, key[1], key[0]))
        elif adequate(key[0], known):
            problems.append("%s is stale: %s is now adequate, graded V or P"
                            % (where, key[0]))
    rows = []
    for name in files:
        refs, mentioned = cited[name]
        for reference in sorted(set(refs)):
            if not resolves(reference, known):
                continue                     # the reference scan says so
            if adequate(reference, known):
                verdict = "adequate"
            elif (reference, name) in exceptions:
                verdict = "excused"
            else:
                verdict = "inadequate"
                problems.append(
                    "%s: cites %s, which is not graded V or P%s, and no "
                    "exception excuses it there" % (
                        name, reference,
                        "" if "-C" in reference else
                        " in every claim (or has no claim)"))
            rows.append({"file": name, "citation": reference,
                         "verdict": verdict})
        for reference in sorted(set(mentioned)):
            rows.append({"file": name, "citation": reference,
                         "verdict": "mention"})
    return {"rows": rows, "problems": problems, "files": files}


# ------------------------------------------------------- the Markdown


def rendered(text: str, quotes: dict) -> str:
    def swap(match):
        token = match.group(1)
        if token.startswith("mention:"):
            return "\u201c%s\u201d" % token[len("mention:"):]
        return "\u201c%s\u201d" % quotes.get(token, token)
    return PLACEHOLDER.sub(swap, text).replace("|", "\\|").replace("\n", " ")


def markdown(raw: dict) -> str:
    """research/sources.md: the register, for a reader. Generated; never
    edited."""
    lines = ["# Sources", "",
             "Generated from `research/sources.yaml` by `tools/sources.py "
             "--write`; edit the register, not this file.", "",
             "Grades: **V** read in the primary text; **P** part of it read; "
             "**S** secondary only; **K** prior knowledge; **L** behind a "
             "login or paywall, not read. A grade covers its claim's scope "
             "and nothing more.", ""]
    entries = [e for e in raw.get("entries") or [] if isinstance(e, dict)]
    if not entries:
        lines.append("No source is registered yet.")
    for entry in sorted(entries, key=lambda e: str(e.get("id"))):
        quotes = {str(q.get("key", "")).rsplit("-", 1)[-1]: q.get("text", "")
                  for q in entry.get("quotes") or [] if isinstance(q, dict)}
        lines += ["## %s" % entry.get("id"), "",
                  rendered(str(entry.get("citation") or ""), quotes), ""]
        for url in entry.get("urls") or []:
            if isinstance(url, dict):
                lines.append("- %s: <%s>" % (url.get("label") or "link",
                                             url.get("url")))
        if entry.get("access_terms"):
            lines.append("- Access: %s" % rendered(entry["access_terms"],
                                                   quotes))
        if entry.get("summary"):
            lines.append("- Summary: %s" % rendered(entry["summary"], quotes))
        lines.append("")
        claims = [c for c in entry.get("claims") or [] if isinstance(c, dict)]
        if claims:
            lines += ["| Claim | Grade | Scope | Note |", "|---|---|---|---|"]
            for claim in claims:
                lines.append("| %s-%s | %s | %s | %s |" % (
                    entry.get("id"), claim.get("id"), claim.get("status"),
                    rendered(str(claim.get("scope") or ""), quotes),
                    rendered(str(claim.get("note") or ""), quotes)))
        else:
            lines.append("No claim is registered: cited whole, it is not "
                         "adequate.")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# ----------------------------------------------------------------- main


def check(root: Path | None = None) -> dict:
    root = root or layout.repository_root()
    settings = configuration(root)
    raw = register(root)
    problems = register_problems(raw, settings)
    known = index(raw)
    problems += unresolved(root, tracked_text(root, settings), known)
    result = adequacy(root, raw, settings)
    problems += result["problems"]
    output = root / OUTPUT
    if not output.is_file() or output.read_bytes() != markdown(
            raw).encode("utf-8"):
        problems.append("%s is not what %s generates; run python "
                        "tools/sources.py --write" % (OUTPUT, REGISTER))
    return {"problems": problems, "rows": result["rows"],
            "files": result["files"], "entries": len(known)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true",
                    help="regenerate research/sources.md from the register")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    root = layout.repository_root()
    if args.write:
        (root / OUTPUT).write_bytes(markdown(register(root)).encode("utf-8"))
        print("  wrote %s" % OUTPUT)
    result = check(root)
    if args.json:
        print(json.dumps(result, indent=1))
        return 1 if result["problems"] else 0
    for problem in result["problems"]:
        print("  finding  " + problem)
    tally = {}
    for row in result["rows"]:
        tally[row["verdict"]] = tally.get(row["verdict"], 0) + 1
    evaluated = sum(n for v, n in tally.items() if v != "mention")
    print("\n  %d source(s); %d decision file(s); %d citation(s) evaluated: "
          "%d adequate, %d excused, %d inadequate; %d mention(s)"
          % (result["entries"], len(result["files"]), evaluated,
             tally.get("adequate", 0), tally.get("excused", 0),
             tally.get("inadequate", 0), tally.get("mention", 0)))
    if not evaluated:
        print("  No citation was evaluated. That is not evidence that the "
              "decisions are well sourced: a decision may rely on a source "
              "it does not cite.")
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
