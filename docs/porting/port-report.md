# Port report: <predecessor> onto the Ontology Template

Copy this file to `research/port-report.md` before you start, and fill it in as you go.
`tools/init_project.py` leaves `research/` alone, so the report can exist before init runs.
Write "none" rather than leaving a section empty, so nothing happening can be told from
nothing recorded. Where a figure can be measured, a command is given; measure it rather
than estimate it, and say which it is. The guide is [`docs/PORTING.md`](../PORTING.md).

## 1. Setup

| | |
|---|---|
| Source ontology | Repository and commit (full SHA) |
| New repository | `owner/name`, and whether it is private |
| Template used | `template_repository`, `label` and `template_commit` from `config/template-manifest.json`. `template_commit` is the commit the manifest was recorded on; a release tag names the commit that carries it |
| Who did the port | Who, and whether they had used the template before |
| AI assistance used | Which tools or models, and for what |

Agreed before starting: namespace id, scope (what is ported and what is not), timebox,
targets.

## 2. Clock

Local time, with its offset from UTC, at each milestone. Leave a milestone blank if you
never reached it, and say why in section 8.

| Milestone | Date and time | Notes |
|---|---|---|
| Started: repository created from the template | | `gh repo create <owner>/<name> --template <template> --private --clone`, or "Use this template" |
| `tools/init_project.py` ran cleanly | | |
| First green CI run (before any ontology content) | | |
| Pages enabled and the site live | | |
| All classes ported | | |
| All properties and axioms ported | | |
| Validation gate green (`tools/ontology/validate.py --gate`) | | |
| Reasoner green (Reasoning workflow) | | |
| Everything green, port complete | | |

Hands-on time in total, excluding waiting: . Machine time on top: . Waiting on answers: .

## 3. Coverage: did everything come across?

| | Source | Ported |
|---|---|---|
| Classes | | |
| Object properties | | |
| Data properties | | |
| Annotation properties | | |
| SKOS concepts and schemes | | |
| Logical axioms: named subClassOf | | |
| Logical axioms: subClassOf a restriction | | |
| Logical axioms: equivalence / disjointness / AllDisjointClasses | | |

Source counts: from the source repository's own tooling or a reasoner report. Ported
counts: the site's `data/terms.json` (`counts`), and `python tools/ontology/corpus_digest.py`.

Mapping set: `mappings/<name>.sssom.tsv`, rows: ; `python tools/ontology/mappings.py`
passes: yes / no.

Losslessness (`docs/PORTING.md`, section 4): statements in the renamed source, statements in
the port, missing, extra; and every exclusion with its reason.

**Terms not carried over, or changed in meaning.** One row each.

| Old IRI | What happened | Why |
|---|---|---|
| | | |

## 4. What the checks found

Run each one on the ported ontology before fixing anything, and record the first result.

| Check | Command | Findings on first run |
|---|---|---|
| Validation ladder | `python tools/ontology/validate.py -o report.json` | |
| IRI linter | `python tools/ontology/iri_lint.py` | |
| Reasoner | `python tools/ontology/reason.py` | |
| Competency questions | `python tools/ontology/competency.py` | |
| Licensing | `python tools/licensing/disposition.py --check` | |

Each finding gets one row. **Class** is one of: *real* (a defect in the source ontology),
*false alarm* (the check is wrong here), *template bug* (the check or tool is broken),
*unsure*. A finding about a BFO or CCO term says so.

| Check | Term | Finding (as printed) | Class | What you did |
|---|---|---|---|---|
| | | | | |

## 5. Template files you changed

The output of `python tools/template_status.py` at the end, pasted whole:

```
```

For each file it lists:

| File | What you changed | Why the template did not work as it was |
|---|---|---|
| | | |

## 6. Questions you had to ask

| When | Question | Who answered | Time lost | Was the answer in the docs? |
|---|---|---|---|---|
| | | | | |

## 7. Friction log

Every point where you got stuck, guessed, worked around something, or were surprised,
including small ones. One line each, as it happens.

| When | Where (file, command, doc section) | What happened | Time lost |
|---|---|---|---|
| | | | |

## 8. Overall

- **Did you finish within the timebox?**
- **Would you start your next ontology from this template?** Yes / with changes / no, and why.
- **The three changes to the template that would have saved the most time:**
- **Anything the template made easier than you expected:**
