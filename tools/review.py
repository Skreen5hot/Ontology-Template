# SPDX-License-Identifier: MIT
"""The review register: a person's answer to each review candidate.

    python tools/review.py              # candidates, answered and not
    python tools/review.py --propose    # entries for the unanswered ones

tools/ontology/candidates.py lists where a defect no check can decide may
be (backlog item 12, template decision 34). A machine finds the place; a
person owns the answer, here, in config/review-register.yaml:

  rule           the candidate's rule (or external:<source>, below)
  about          the IRIs it is about, as the candidate lists them
  validity       is it a defect?  real | false-alarm | unsure
  resolution     what is done about it?
                 fixed | accepted | deferred | reported | not-a-defect
  classified_by  "<name> (<kind>)", the kind one of config/review.yaml's:
                 the role the answer was given in
  reason         why
  review         YYYY-MM-DD, required with deferred: when it is looked at
                 again
  reference      where it was reported; required with reported

RULES BETWEEN THEM

  fixed          requires real: the defect was corrected
  accepted       requires real: kept deliberately, and the reason says why
  not-a-defect   requires false-alarm
  false-alarm    is not-a-defect, or reported (a defect in the rule)
  unsure         is deferred, with a review date
  deferred       requires a review date
  reported       requires a reference

An entry is matched to a candidate by its rule and IRIs, never by text.
An entry that matches no current candidate is stale: what it answered is
gone, and the entry goes in the commit that removed it -- unless it is
`fixed`, whose candidate is expected to go.

Nothing here judges an answer, and nothing here fails a commit.
tools/stages.py refuses a stage marked done while a candidate in its scope
has no answer from a role the stage requires; that is the only gate.

CANDIDATES FROM ELSEWHERE

A model, another tool or a person's own notes may supply candidates, in
review/candidates/*.yaml (review/candidates/README.md has the format and
an example prompt). Each file names who or what produced it, when, and
the corpus digest it was run on; for a model, the model and a digest of
the prompt. Its candidates' rule is external:<source>. CI reads these
files and never produces them, so no credentials reach it.
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "ontology"))

import findings  # noqa: E402
import layout  # noqa: E402

REGISTER = "config/review-register.yaml"
IMPORTS = "review/candidates"
FORMATS = (1,)
VALUES = {
    "validity": ("real", "false-alarm", "unsure"),
    "resolution": ("fixed", "accepted", "deferred", "reported",
                   "not-a-defect"),
}
REQUIRED = ("rule", "about", "validity", "resolution", "classified_by",
            "reason")
OPTIONAL = ("review", "reference", "text")
PROVENANCE = ("source", "produced_by", "date", "corpus")
MODEL = ("model", "prompt_sha256")
EXTERNAL = re.compile(r"^external:[a-z0-9][a-z0-9-]*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RegisterError(SystemExit):
    """The register or an import cannot be read, so nothing can use it."""


def key(record: dict) -> tuple:
    return (str(record.get("rule") or ""),
            tuple(sorted(str(i) for i in record.get("about") or [])))


def problems_of(entries: list, kinds: tuple) -> list[str]:
    """Every way an entry is unusable, each a reason to refuse the
    register."""
    out, seen = [], {}
    for index, entry in enumerate(entries):
        name = "entry %d" % (index + 1)
        if not isinstance(entry, dict):
            out.append("%s is not a mapping" % name)
            continue
        unknown = sorted(set(entry) - set(REQUIRED) - set(OPTIONAL))
        if unknown:
            out.append("%s has unknown field(s): %s"
                       % (name, ", ".join(unknown)))
        given = {k: entry.get(k) for k in REQUIRED + OPTIONAL}
        for k in REQUIRED:
            if not given[k]:
                out.append("%s has no %s" % (name, k))
        for k in REQUIRED + OPTIONAL:
            if "TODO" in str(given[k] or ""):
                out.append("%s: %s is still a placeholder; an answer is a "
                           "person's, or absent" % (name, k))
                given[k] = None
        about = given["about"]
        if about is not None and (not isinstance(about, list) or not all(
                isinstance(i, str) and i for i in about)):
            out.append("%s: about is not a list of IRIs" % name)
        for k, allowed in VALUES.items():
            if given[k] and given[k] not in allowed:
                out.append("%s: %s %r is not one of %s"
                           % (name, k, given[k], ", ".join(allowed)))
                given[k] = None
        validity, resolution = given["validity"], given["resolution"]

        def rule(holds, text):
            if not holds:
                out.append("%s: %s" % (name, text))
        if resolution in ("fixed", "accepted") and validity:
            rule(validity == "real", "%s requires validity real (it is %s)"
                 % (resolution, validity))
        if resolution == "not-a-defect" and validity:
            rule(validity == "false-alarm", "not-a-defect requires validity "
                 "false-alarm (it is %s)" % validity)
        if validity == "false-alarm" and resolution:
            rule(resolution in ("not-a-defect", "reported"), "a false-alarm "
                 "is not-a-defect, or reported as a defect in the rule (it "
                 "is %s)" % resolution)
        if validity == "unsure" and resolution:
            rule(resolution == "deferred", "unsure requires resolution "
                 "deferred (it is %s)" % resolution)
        review = str(given["review"] or "")
        if resolution == "deferred":
            rule(bool(review), "deferred requires a review date")
        if review:
            try:
                if not DATE.match(review):
                    raise ValueError
                datetime.date.fromisoformat(review)
            except ValueError:
                out.append("%s: review %r is not a date (YYYY-MM-DD)"
                           % (name, review))
        if resolution == "reported":
            rule(bool(given["reference"]), "reported requires a reference")
        by = str(given["classified_by"] or "")
        if by:
            match = findings.CLASSIFIED_BY.match(by)
            if not match:
                out.append("%s: classified_by %r is not '<name> (<kind>)'"
                           % (name, by))
            elif match.group("kind") not in kinds:
                out.append("%s: classified_by names the kind %r, which %s "
                           "does not declare (%s)" % (
                               name, match.group("kind"), findings.REVIEW,
                               ", ".join(kinds)))
        k = key(entry)
        if k in seen:
            out.append("%s repeats entry %d" % (name, seen[k] + 1))
        else:
            seen[k] = index
    return out


def kind_of(entry: dict) -> str:
    match = findings.CLASSIFIED_BY.match(str(entry.get("classified_by")
                                             or ""))
    return match.group("kind") if match else ""


def load(root: Path | None = None) -> list[dict]:
    import yaml

    root = root or layout.repository_root()
    path = root / REGISTER
    if not path.is_file():
        raise RegisterError(REGISTER + " is missing; it holds a person's "
                            "answer to each review candidate")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if raw.get("format_version") not in FORMATS:
        raise RegisterError("%s: format_version %r is not one of %s"
                            % (REGISTER, raw.get("format_version"), FORMATS))
    entries = raw.get("entries") or []
    if not isinstance(entries, list):
        raise RegisterError(REGISTER + ": entries is not a list")
    problems = problems_of(entries, findings.review_kinds(root))
    if problems:
        raise RegisterError(REGISTER + " cannot be used:\n" + "\n".join(
            "  " + p for p in problems))
    for entry in entries:
        if entry.get("review"):
            entry["review"] = str(entry["review"])
    return entries


def imported(root: Path | None = None) -> list[dict]:
    """Every candidate in review/candidates/*.yaml, each with the
    provenance of its file, refused where a file lacks it."""
    import yaml

    root = root or layout.repository_root()
    out = []
    for path in sorted((root / IMPORTS).glob("*.yaml")):
        name = path.relative_to(root).as_posix()
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        header = raw.get("provenance") or {}
        missing = [k for k in PROVENANCE if not header.get(k)]
        if header.get("model") or header.get("prompt_sha256"):
            missing += [k for k in MODEL if not header.get(k)]
        if missing:
            raise RegisterError("%s: provenance lacks %s; a candidate is "
                                "only as good as the record of where it came "
                                "from" % (name, ", ".join(missing)))
        for index, item in enumerate(raw.get("candidates") or []):
            rule = str((item or {}).get("rule") or "")
            about = (item or {}).get("about")
            if not EXTERNAL.match(rule) or not isinstance(about, list) \
                    or not about:
                raise RegisterError(
                    "%s: candidate %d needs rule external:<source> and "
                    "about, a list of IRIs" % (name, index + 1))
            out.append({"rule": rule, "about": sorted(about),
                        "message": str(item.get("message") or ""),
                        "evidence": item.get("evidence") or {},
                        "file": name, "corpus": str(header["corpus"])})
    return out


def judge(candidates: list, entries: list,
          today: datetime.date | None = None) -> dict:
    """Each candidate answered or not; each entry matched or stale; and
    the deferred ones whose review date has passed."""
    today = today or datetime.date.today()
    by_key = {key(e): e for e in entries}
    answered, unanswered, current = [], [], set()
    for record in candidates:
        k = key(record)
        current.add(k)
        if k in by_key:
            answered.append((record, by_key[k]))
        else:
            unanswered.append(record)
    stale = [e for e in entries if key(e) not in current
             and e["resolution"] != "fixed"]
    overdue = [e for e in entries if e["resolution"] == "deferred"
               and datetime.date.fromisoformat(e["review"]) < today]
    return {"answered": answered, "unanswered": unanswered, "stale": stale,
            "overdue": overdue}


def older(records: list, digest: str) -> dict:
    """{import file: its corpus digest}, for each file not run on the
    current corpus."""
    return {r["file"]: r["corpus"] for r in records
            if r.get("corpus") and r["corpus"] != digest}


def propose(records: list) -> str:
    """Entries for `records`, with every judgement left as a placeholder
    the register refuses until a person answers it."""
    import yaml

    out = []
    for record in records:
        out.append({
            "rule": record["rule"], "about": list(record["about"]),
            "text": record["message"][:300],
            "validity": "TODO " + " | ".join(VALUES["validity"]),
            "resolution": "TODO " + " | ".join(VALUES["resolution"]),
            "classified_by": "TODO <name> (<kind>)",
            "reason": "TODO why"})
    return yaml.safe_dump(out, sort_keys=False, allow_unicode=True,
                          width=100) if out else ""


def current(root: Path | None = None) -> tuple[list, str]:
    """Every candidate now, generated and imported, and the digest of the
    corpus they were generated from."""
    import candidates as generator

    root = root or layout.repository_root()
    corpus = generator.corpus(root)
    records = generator.generate(corpus, generator.configuration(root))
    return records + imported(root), generator.corpus_digest(corpus)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--propose", action="store_true",
                    help="print entries for the unanswered candidates, for "
                         "a person to answer")
    args = ap.parse_args(argv)
    records, digest = current()
    verdict = judge(records, load())
    if args.propose:
        sys.stdout.write(propose(verdict["unanswered"]))
        return 0
    print("  %d candidate(s): %d answered, %d unanswered; %d stale "
          "entr%s, %d deferred past review"
          % (len(records), len(verdict["answered"]),
             len(verdict["unanswered"]), len(verdict["stale"]),
             "y" if len(verdict["stale"]) == 1 else "ies",
             len(verdict["overdue"])))
    for record in verdict["unanswered"]:
        print("  UNANSWERED %s %s" % (record["rule"],
                                      " ".join(record["about"])))
    for entry in verdict["stale"]:
        print("  STALE %s %s -- it answers no current candidate; remove it "
              "in the commit that removed the candidate"
              % (entry["rule"], " ".join(entry["about"])))
    for name, corpus in sorted(older(records, digest).items()):
        print("  OLDER CORPUS %s: run on %s, not the current %s; run it "
              "again, or remove it" % (name, corpus[:12], digest[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
