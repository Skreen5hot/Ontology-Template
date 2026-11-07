# SPDX-License-Identifier: MIT
"""Rights and provenance: what each source's terms were found to say, on
what evidence, and which decision released each use of its text.

    python tools/rights.py             # check; exit 1 on a finding
    python tools/rights.py --json      # the findings, the holds, the counts
    python tools/rights.py --confirm   # also refetch each url item (network)

METHOD section 4's rights and provenance review (P8, template decision
40): before text is taken from a source, its rights are reviewed and
recorded, and what is taken is withheld until a decision releases it.
In BCO's source stage, rights cost more than anything else: text was
withheld and later released, one framework took three decisions and a
re-sourcing, eleven lists were withheld at closure. Each came from the
same gap: what a source's terms said was found late, and nothing
recorded it where a later step would see it.

THE RECORD, research/rights.yaml

  reviews   one per source of the register (research/sources.yaml) and
            edition:
    source          its register id, SRC-<FAMILY>-<NN>
    rightsholder, work
    edition         the edition reviewed. A review of one edition says
                    nothing of another (decision 40, safeguard 1), so two
                    editions of one source are two reviews
    status          evidence-complete, gap or deferred; gap_reason says
                    what is missing, and only when it is not complete
    terms           unambiguous, ambiguous or not-established: the
                    reviewer's assessment, never the tool's.
                    open_questions lists what is unresolved, and
                    ambiguous terms have at least one
    evidence        what the review rests on, each item one of
                      url         a page: url, sha256, retrieved, checked
                      repository  a file at a commit: repository, commit
                                  (40 hex), path, sha256, retrieved,
                                  checked
                      manual      read where its bytes could not be kept:
                                  retrieved, checked, why_not_refetched,
                                  url if it has one. It has no sha256: no
                                  bytes were pinned, and it is never
                                  reported as digest-verified (safeguard 2)
                    and any item may carry the quote relied on, within
                    config/sources.yaml's max_quote_words, if set
    reviewed_by     "<name> (rights-reviewer)": the review records that a
                    review was made, and implies no legal approval
                    (config/review.yaml)
    uses            each intended use, judged on its own (safeguard 1):
                      intended     what the text would be used for
                      modules      the module files it would be used in
                      use          withheld, until a decision releases
                                   it: released
                      released_by  {decision, by}: the decision record
                                   that released this use, and
                                   "<name> (<kind>)", a kind
                                   config/rights.yaml allows to release:
                                   the architect, unless a recorded
                                   decision delegates (decision 40)

A release names its decision, and the decision names the source: the
two point at each other. A decision taken before config/rights.yaml's
required_from is authoritative as written for what it covers (BPO's
ADR-003 among them, safeguard 4), and is not asked to cite a record made
after it.

WHERE WITHHOLDING IS HELD

A declaration in config/third-party-text.yaml names the review of its
source (`rights: SRC-...`). Text from it, in a module, is held unless a
review of that source exists, of the declaration's release, with a use
listing the module released by a decision that exists and names the
source. A held module

- holds a stage marked done whose `where` components hold it
  (tools/stages.py);
- stops a release (tools/release.py).

Ordinary CI is never failed by a hold: a use waiting for its decision is
the normal state between a review and a release. With required_from set,
a declaration made before it that names no review is listed as
unreviewed, never held. This keeps decision 33's policy: nothing is
refused for its licence. What is held is the absence of a recorded
decision to use the text, at the two points where the project says its
work is done (safeguard 3).

What a finding here refuses, each naming the review or the file:

- the record's schema: an unknown field, a value outside its list, a
  source the register does not hold, or one edition of a source
  reviewed twice;
- a gap or deferred review without its reason, a complete one with one,
  ambiguous terms with no open question, a complete review with no
  evidence;
- an evidence item without its fields, a malformed digest, date or
  commit; a manual item carrying a sha256;
- a quote longer than the project's limit;
- a reviewer not in the rights-reviewer kind;
- a use without what it is for and the modules it covers; a module two
  uses of one review cover; a released use without released_by, or a
  withheld one with it; a release naming no decision record, a decision
  record that does not cite the source, or someone of a kind not allowed
  to release;
- in config/third-party-text.yaml, a `rights` naming no register source;
- with --confirm, a url item whose bytes no longer have its digest, or
  which cannot be fetched. A moved digest is a finding for the reviewer,
  and is never re-pinned.

It decides nothing. It does not read what a licence grants, judge
whether terms are ambiguous, or say whether a use is permitted: `terms`
is the reviewer's assessment, and a release is the architect's act. It
does not see a use nobody declared, and a pinned digest shows that the
document is the one reviewed, not that the review read it rightly.

Exit codes: 0 no findings; 1 findings.
"""

from __future__ import annotations

import argparse
import datetime
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "licensing"))

import findings  # noqa: E402
import layout  # noqa: E402
import sources  # noqa: E402

RECORD = "research/rights.yaml"
CONFIG = "config/rights.yaml"
DECLARATIONS = "config/third-party-text.yaml"
FORMATS = (1,)
REVIEWER = "rights-reviewer"

STATUSES = ("evidence-complete", "gap", "deferred")
TERMS = ("unambiguous", "ambiguous", "not-established")
USES = ("withheld", "released")
TOP_FIELDS = {"format_version", "reviews"}
REVIEW_FIELDS = {"source", "rightsholder", "work", "edition", "status",
                 "gap_reason", "terms", "open_questions", "evidence",
                 "reviewed_by", "uses"}
REQUIRED = ("source", "rightsholder", "work", "edition", "status", "terms",
            "reviewed_by")
#: Each evidence kind's fields: (required, optional).
EVIDENCE = {
    "url": (("url", "sha256", "retrieved", "checked"), ("quote",)),
    "repository": (("repository", "commit", "path", "sha256", "retrieved",
                    "checked"), ("quote",)),
    "manual": (("retrieved", "checked", "why_not_refetched"),
               ("url", "quote")),
}
USE_FIELDS = {"intended", "modules", "use", "released_by"}
RELEASE_FIELDS = {"decision", "by"}
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
DATED = re.compile(r"^(\d{4}-\d{2}-\d{2})-")
#: A character that may continue an SRC identifier: one next to a match
#: means it is part of a longer one (SRC-STD-010 does not cite SRC-STD-01).
EDGE = "A-Za-z0-9_-"

DEFAULTS = {
    "decisions": ["docs/decisions/*.md"],
    "releasers": [{"kind": "architect"}],
    "required_from": None,
}


class Unreadable(SystemExit):
    """A file this reads cannot be read as what it should be."""


# --------------------------------------------------------------- reading


def configuration(root: Path) -> dict:
    import yaml

    path = root / CONFIG
    raw = {}
    if path.is_file():
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise Unreadable("%s cannot be read: %s" % (CONFIG, exc))
    if not isinstance(raw, dict):
        raise Unreadable("%s is not a mapping" % CONFIG)
    unknown = sorted(set(raw) - set(DEFAULTS) - {"version"})
    if unknown:
        raise Unreadable("%s has unknown field(s): %s"
                         % (CONFIG, ", ".join(unknown)))
    settings = dict(DEFAULTS)
    settings.update({k: v for k, v in raw.items() if k != "version"})
    start = settings["required_from"]
    if start is not None and not isinstance(start, datetime.date):
        try:
            settings["required_from"] = datetime.date.fromisoformat(
                str(start))
        except ValueError:
            raise Unreadable("%s: required_from %r is not a date "
                             "(YYYY-MM-DD)" % (CONFIG, start))
    return settings


def record(root: Path) -> dict:
    import yaml

    path = root / RECORD
    if not path.is_file():
        return {"format_version": 1, "reviews": []}
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise Unreadable("%s cannot be read: %s" % (RECORD, exc))
    if not isinstance(raw, dict):
        raise Unreadable("%s is not a mapping" % RECORD)
    if raw.get("format_version") not in FORMATS:
        raise Unreadable("%s: format_version %r is not one of %s"
                         % (RECORD, raw.get("format_version"), FORMATS))
    return raw


def tracked(root: Path) -> set[str]:
    result = subprocess.run(["git", "ls-files"], cwd=str(root),
                            capture_output=True, text=True)
    return set(result.stdout.split()) if result.returncode == 0 else set()


def first_dated(root: Path, path: str, text: str | None = None):
    """The date of the earliest commit that added this file, or, given
    text, that added that text to it; None if no commit did."""
    command = ["git", "log", "--format=%ci"]
    command += ["-S" + text] if text else ["--diff-filter=A"]
    result = subprocess.run(command + ["--", path], cwd=str(root),
                            capture_output=True, text=True)
    lines = result.stdout.splitlines() if result.returncode == 0 else []
    return datetime.date.fromisoformat(lines[-1][:10]) if lines else None


def decided_on(root: Path, path: str):
    """When a decision record was taken: the date its name begins with,
    else the commit that added it, else None (not yet committed)."""
    match = DATED.match(Path(path).name)
    if match:
        try:
            return datetime.date.fromisoformat(match.group(1))
        except ValueError:
            pass
    return first_dated(root, path)


def cites(text: str, source: str) -> bool:
    return re.search(r"(?<![%s])%s(?![%s])" % (EDGE, re.escape(source),
                                                EDGE), text) is not None


def text_of(value) -> str:
    return str(value).strip() if isinstance(value, (str, int, float)) \
        else ""


def is_date(value) -> bool:
    if isinstance(value, datetime.date):
        return True
    try:
        datetime.date.fromisoformat(str(value))
        return True
    except ValueError:
        return False


def words(text) -> int:
    return len(str(text).split())


# ------------------------------------------------------ the record's rules


def releasers(root: Path, settings: dict) -> tuple[set, list[str]]:
    """The kinds allowed to release a use, and what is wrong with the
    list: a kind other than the architect needs a recorded delegation
    (decision 40: the architect releases unless a decision delegates)."""
    kinds, problems = set(), []
    declared = findings.review_kinds(root)
    for item in settings["releasers"] or []:
        kind = str((item or {}).get("kind") or "")
        if kind not in declared:
            problems.append("%s: releaser %r is not a kind "
                            "config/review.yaml declares" % (CONFIG, kind))
            continue
        if kind != "architect":
            delegation = str((item or {}).get("delegated_by") or "")
            if not delegation or not (root / delegation).is_file():
                problems.append(
                    "%s: %s may release a use only by a recorded "
                    "delegation; delegated_by names no decision file"
                    % (CONFIG, kind))
                continue
        kinds.add(kind)
    return kinds, problems


def evidence_problems(where: str, items, limit) -> list[str]:
    if not isinstance(items, list):
        return ["%s: evidence is not a list" % where]
    out = []
    for number, item in enumerate(items, 1):
        at = "%s: evidence %d" % (where, number)
        if not isinstance(item, dict):
            out.append("%s is not a mapping" % at)
            continue
        kind = item.get("kind")
        if kind not in EVIDENCE:
            out.append("%s: kind %r is not one of %s"
                       % (at, kind, ", ".join(EVIDENCE)))
            continue
        required, optional = EVIDENCE[kind]
        if kind == "manual" and "sha256" in item:
            out.append("%s is manual and carries a sha256: no bytes were "
                       "kept, so nothing was digest-verified; pin a copy "
                       "as repository evidence, or remove the digest "
                       "(decision 40, safeguard 2)" % at)
        unknown = sorted(set(item) - set(required) - set(optional)
                         - {"kind"} - ({"sha256"} if kind == "manual"
                                       else set()))
        if unknown:
            out.append("%s has unknown field(s) for %s evidence: %s"
                       % (at, kind, ", ".join(map(str, unknown))))
        missing = [f for f in required if not text_of(item.get(f))
                   and not isinstance(item.get(f), datetime.date)]
        if missing:
            out.append("%s (%s) has no %s" % (at, kind, ", ".join(missing)))
        if item.get("sha256") is not None and kind != "manual" and \
                not SHA256.match(str(item["sha256"])):
            out.append("%s: sha256 is not 64 lowercase hex digits" % at)
        if item.get("retrieved") is not None and not is_date(
                item["retrieved"]):
            out.append("%s: retrieved %r is not a date (YYYY-MM-DD)"
                       % (at, item["retrieved"]))
        if kind == "repository" and item.get("commit") is not None and \
                not COMMIT.match(str(item["commit"])):
            out.append("%s: commit is not 40 lowercase hex digits; a "
                       "repository item is pinned to a commit" % at)
        if limit is not None and "quote" in item and \
                words(item["quote"]) > limit:
            out.append("%s: its quote is %d words, longer than "
                       "max_quote_words (%d) in config/sources.yaml"
                       % (at, words(item["quote"]), limit))
    return out


def use_problems(root: Path, where: str, source: str, uses, known: set,
                 settings: dict, allowed: set) -> list[str]:
    if not isinstance(uses, list):
        return ["%s: uses is not a list" % where]
    out, covered = [], {}
    start = settings["required_from"]
    for number, use in enumerate(uses, 1):
        at = "%s: use %d" % (where, number)
        if not isinstance(use, dict):
            out.append("%s is not a mapping" % at)
            continue
        unknown = sorted(set(use) - USE_FIELDS)
        if unknown:
            out.append("%s has unknown field(s): %s"
                       % (at, ", ".join(map(str, unknown))))
        if not text_of(use.get("intended")):
            out.append("%s does not say what the text would be used for "
                       "(intended); permission for one use implies none "
                       "for another" % at)
        modules = use.get("modules")
        if not isinstance(modules, list) or not modules or not all(
                isinstance(m, str) and m.strip() for m in modules):
            out.append("%s lists no modules it covers" % at)
            modules = []
        for module in modules:
            if (module.startswith(("/", "./")) or "\\" in module
                    or ".." in module.split("/")
                    or any(c in module for c in "*?[")):
                out.append("%s lists %s, which is not a repository path to "
                           "one file" % (at, module))
            elif module in covered:
                out.append("%s covers %s, which use %d covers too; one use "
                           "applies to a module" % (at, module,
                                                    covered[module]))
            else:
                covered[module] = number
        state = use.get("use")
        if state not in USES:
            out.append("%s: use %r is not one of %s"
                       % (at, state, ", ".join(USES)))
            continue
        release = use.get("released_by")
        if state == "withheld":
            if release is not None:
                out.append("%s is withheld and names a release" % at)
            continue
        if not isinstance(release, dict):
            out.append("%s is released and names no released_by "
                       "{decision, by}" % at)
            continue
        unknown = sorted(set(release) - RELEASE_FIELDS)
        if unknown:
            out.append("%s: released_by has unknown field(s): %s"
                       % (at, ", ".join(map(str, unknown))))
        decision = text_of(release.get("decision"))
        if not decision or decision not in known or not any(
                fnmatch.fnmatch(decision, g)
                for g in settings["decisions"]):
            out.append("%s is released by %r, which is not a tracked "
                       "decision record (config/rights.yaml decisions)"
                       % (at, release.get("decision")))
        else:
            taken = decided_on(root, decision)
            prior = start is not None and taken is not None and taken < start
            text = (root / decision).read_text(encoding="utf-8",
                                               errors="replace")
            if not prior and not cites(text, source):
                out.append("%s is released by %s, which does not cite %s; "
                           "the release and the decision point at each "
                           "other" % (at, decision, source))
        match = findings.CLASSIFIED_BY.match(text_of(release.get("by")))
        if not match:
            out.append("%s: released_by.by %r is not '<name> (<kind>)'"
                       % (at, release.get("by")))
        elif match.group("kind") not in allowed:
            out.append("%s was released by %s as %s, a kind "
                       "config/rights.yaml does not allow to release"
                       % (at, match.group("name"), match.group("kind")))
    return out


def record_problems(root: Path, raw: dict, settings: dict, register: set,
                    known: set, allowed: set, limit) -> list[str]:
    out = []
    unknown = sorted(set(raw) - TOP_FIELDS)
    if unknown:
        out.append("%s has unknown field(s): %s"
                   % (RECORD, ", ".join(map(str, unknown))))
    reviews = raw.get("reviews") or []
    if not isinstance(reviews, list):
        return out + ["%s: reviews is not a list" % RECORD]
    seen = set()
    for number, review in enumerate(reviews, 1):
        if not isinstance(review, dict):
            out.append("%s: review %d is not a mapping" % (RECORD, number))
            continue
        source = text_of(review.get("source"))
        where = "%s: %s" % (RECORD, source or "review %d" % number)
        unknown = sorted(set(review) - REVIEW_FIELDS)
        if unknown:
            out.append("%s has unknown field(s): %s"
                       % (where, ", ".join(map(str, unknown))))
        missing = [f for f in REQUIRED if not text_of(review.get(f))]
        if missing:
            out.append("%s has no %s" % (where, ", ".join(missing)))
        if source:
            if source not in register:
                out.append("%s: %s is not a source of %s"
                           % (where, source, sources.REGISTER))
            key = (source, text_of(review.get("edition")))
            if key in seen:
                out.append("%s is reviewed twice for edition %s"
                           % (where, key[1]))
            seen.add(key)
        status, terms = review.get("status"), review.get("terms")
        if status is not None and status not in STATUSES:
            out.append("%s: status %r is not one of %s"
                       % (where, status, ", ".join(STATUSES)))
        reason = text_of(review.get("gap_reason"))
        if status in ("gap", "deferred") and not reason:
            out.append("%s is %s and gives no gap_reason" % (where, status))
        if status == "evidence-complete" and reason:
            out.append("%s is evidence-complete and gives a gap_reason"
                       % where)
        if terms is not None and terms not in TERMS:
            out.append("%s: terms %r is not one of %s"
                       % (where, terms, ", ".join(TERMS)))
        questions = review.get("open_questions")
        if questions is not None and (not isinstance(questions, list) or
                                      not all(text_of(q) for q in questions)):
            out.append("%s: open_questions is not a list of questions"
                       % where)
        if terms == "ambiguous" and not questions:
            out.append("%s: its terms are ambiguous and it lists no open "
                       "question" % where)
        evidence = review.get("evidence")
        if evidence is not None:
            out += evidence_problems(where, evidence, limit)
        if status == "evidence-complete" and not evidence:
            out.append("%s is evidence-complete and lists no evidence"
                       % where)
        reviewer = text_of(review.get("reviewed_by"))
        match = findings.CLASSIFIED_BY.match(reviewer)
        if reviewer and not match:
            out.append("%s: reviewed_by %r is not '<name> (<kind>)'"
                       % (where, reviewer))
        elif match and match.group("kind") != REVIEWER:
            out.append("%s: reviewed_by names the kind %s; a rights review "
                       "is made as %s" % (where, match.group("kind"),
                                          REVIEWER))
        if "uses" in review:
            out += use_problems(root, where, source, review["uses"], known,
                                settings, allowed)
    return out


# ----------------------------------------------------------- where held


def declarations(root: Path) -> list[dict]:
    import third_party

    return third_party.load(root)


def declaration_problems(entries: list[dict], register: set) -> list[str]:
    out = []
    for entry in entries:
        if "rights" not in entry:
            continue
        name = text_of(entry["rights"])
        if name not in register:
            out.append("%s: %s names the review of %r, which is not a "
                       "source of %s" % (DECLARATIONS, entry["property"],
                                         entry["rights"], sources.REGISTER))
    return out


def carriers(root: Path, entries: list[dict], modules=None) -> list[tuple]:
    """(module path, declaration) for each module holding values of a
    declared property."""
    import rdflib

    import third_party

    out = []
    if not entries:
        return out
    for path in (modules if modules is not None
                 else layout.ontology_files()):
        graph = rdflib.Graph()
        graph.parse(path, format="turtle")
        name = Path(path).resolve().relative_to(root.resolve()).as_posix()
        for entry in entries:
            if third_party.values_in(graph, entry):
                out.append((name, entry))
    return out


def standing(root: Path, pairs: list[tuple], reviews: dict,
             settings: dict, valid: set) -> tuple[list[dict], list[dict]]:
    """Each module's text from each declared source: held, with why, or
    listed as unreviewed. `reviews` is keyed by (source, edition), and
    `valid` holds (source, edition, use number) for each release with no
    finding."""
    held, unreviewed = [], []
    start = settings["required_from"]
    for module, entry in pairs:
        row = {"module": module, "property": entry["property"],
               "source": text_of(entry.get("rights")),
               "release": text_of(entry.get("release"))}
        if not row["source"]:
            dated = first_dated(root, DECLARATIONS, entry["property"])
            if start is not None and dated is not None and dated < start:
                unreviewed.append(row)
            else:
                held.append(dict(row, why="its declaration names no rights "
                                          "review (rights: SRC-...)"))
            continue
        editions = sorted(e for s, e in reviews if s == row["source"])
        if not editions:
            held.append(dict(row, why="%s has no review in %s"
                                      % (row["source"], RECORD)))
            continue
        review = reviews.get((row["source"], row["release"]))
        if review is None:
            held.append(dict(row, why="%s was reviewed for edition %s; "
                                      "this text is from release %s"
                             % (row["source"], ", ".join(editions),
                                row["release"])))
            continue
        uses = [(n, u) for n, u in enumerate(review.get("uses") or [], 1)
                if isinstance(u, dict) and module in (u.get("modules")
                                                      or [])]
        if not uses:
            held.append(dict(row, why="no intended use of %s in %s covers "
                                      "it" % (row["source"], RECORD)))
            continue
        number, use = uses[0]
        if use.get("use") != "released":
            held.append(dict(row, why="its use (%s) is withheld"
                             % text_of(use.get("intended"))))
        elif (row["source"], row["release"], number) not in valid:
            held.append(dict(row, why="its release has a finding"))
    return held, unreviewed


def stage_problems(stages: list[dict], held: list[dict], owner) -> list[str]:
    """The stage gate: a stage marked done holds every module in its
    scope with text no decision has released."""
    out = []
    for stage in stages:
        if stage.get("status") != "done" or stage.get("runs") is not True:
            continue
        scope = set(stage.get("where") or [])
        for row in held:
            if owner(row["module"]) in scope:
                out.append("%s: is done, but %s holds text from %s (%s) "
                           "no decision has released: %s" % (
                               stage["id"], row["module"],
                               row["source"] or "an unreviewed source",
                               row["property"], row["why"]))
    return out


def release_problems(held: list[dict]) -> list[str]:
    """Every held module stops a release (P8, decision 40)."""
    return ["%s holds text from %s (%s) no decision has released: %s" % (
        row["module"], row["source"] or "an unreviewed source",
        row["property"], row["why"]) for row in held]


# --------------------------------------------------------------- confirm


def fetch(url: str) -> bytes:
    import urllib.request

    request = urllib.request.Request(url, headers={
        "User-Agent": "ontology-template-rights-confirm"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def confirm(raw: dict, fetcher=None) -> list[str]:
    """Each url item refetched and its digest compared. A moved digest is
    reported, never re-pinned."""
    fetcher = fetcher or fetch
    out = []
    for review in raw.get("reviews") or []:
        for number, item in enumerate((review or {}).get("evidence") or [],
                                      1):
            if not isinstance(item, dict) or item.get("kind") != "url":
                continue
            at = "%s: %s evidence %d" % (RECORD, review.get("source"), number)
            try:
                data = fetcher(str(item.get("url")))
            except Exception as exc:  # noqa: BLE001 - any failure is a finding
                out.append("%s: %s could not be fetched: %s"
                           % (at, item.get("url"), exc))
                continue
            digest = hashlib.sha256(data).hexdigest()
            if digest != item.get("sha256"):
                out.append("%s: %s now has sha256 %s, not the %s pinned on "
                           "%s; the publisher changed it, and the reviewer "
                           "decides what that means. It is not re-pinned."
                           % (at, item.get("url"), digest, item.get("sha256"),
                              item.get("retrieved")))
    return out


# ----------------------------------------------------------------- main


def owner_of(relative_path: str):
    component = layout.owning_component(relative_path)
    return component.id if component else None


def tally(raw: dict) -> dict:
    counts = {"pinned": 0, "manual": 0, "manual_only": []}
    for review in raw.get("reviews") or []:
        items = [i for i in (review or {}).get("evidence") or []
                 if isinstance(i, dict)]
        manual = sum(1 for i in items if i.get("kind") == "manual")
        counts["manual"] += manual
        counts["pinned"] += len(items) - manual
        if items and manual == len(items):
            counts["manual_only"].append(review.get("source"))
    return counts


def check(root: Path | None = None, modules=None, fetcher=None,
          refetch: bool = False) -> dict:
    root = root or layout.repository_root()
    settings = configuration(root)
    raw = record(root)
    register = set(sources.index(sources.register(root)))
    known = tracked(root)
    allowed, problems = releasers(root, settings)
    limit = sources.configuration(root)["max_quote_words"]
    problems += record_problems(root, raw, settings, register, known,
                                allowed, limit)
    entries = declarations(root)
    problems += declaration_problems(entries, register)
    reviews = {(text_of(r.get("source")), text_of(r.get("edition"))): r
               for r in raw.get("reviews") or [] if isinstance(r, dict)}
    valid = set()
    for (source, edition), review in reviews.items():
        uses = review.get("uses")
        if not isinstance(uses, list):
            continue
        for number, use in enumerate(uses, 1):
            if isinstance(use, dict) and use.get("use") == "released" and \
                    not use_problems(root, "", source, [use], known,
                                     settings, allowed):
                valid.add((source, edition, number))
    held, unreviewed = standing(root, carriers(root, entries, modules),
                                reviews, settings, valid)
    if refetch:
        problems += confirm(raw, fetcher)
    return {"problems": problems, "held": held, "unreviewed": unreviewed,
            "reviews": len(reviews), "evidence": tally(raw)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--confirm", action="store_true",
                    help="refetch each url item and compare its digest "
                         "(network)")
    args = ap.parse_args(argv)
    result = check(refetch=args.confirm)
    if args.json:
        print(json.dumps(result, indent=1, default=str))
        return 1 if result["problems"] else 0
    for problem in result["problems"]:
        print("  finding  " + problem)
    for row in result["held"]:
        print("  withheld  %s <- %s (%s): %s" % (
            row["module"], row["source"] or "?", row["property"], row["why"]))
    for row in result["unreviewed"]:
        print("  unreviewed  %s <- %s (declared before required_from)"
              % (row["module"], row["property"]))
    counts = result["evidence"]
    print("\n  %d review(s); %d evidence item(s) pinned by digest, %d manual "
          "and not digest-verified; %d module use(s) withheld, %d "
          "unreviewed" % (result["reviews"], counts["pinned"],
                          counts["manual"], len(result["held"]),
                          len(result["unreviewed"])))
    if counts["manual_only"]:
        print("  Resting on manual evidence only, with no bytes pinned: "
              + ", ".join(map(str, counts["manual_only"])))
    if result["held"]:
        print("  A withheld use fails nothing here; a stage marked done, "
              "or a release, is held for it.")
    print("  This records the reviewer's assessment and the decisions "
          "that released each use. It does not judge what a source's "
          "terms permit.")
    return 1 if result["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
