# P-A2: two throwaway projects upgraded to the release

**Date:** 2026-11-14. **Under:** decision 45, which approved the two disposable-project
upgrade measurements, from v0.1.0 and from v0.7.0. Each project was made as "Use this
template" makes one: a fresh clone of the release tag reduced to one commit, initialized
with the network rebuild, and init committed. Each was then upgraded to the P-A2 commit
`15ccaa0` by the procedure in `docs/DEVELOPMENT.md`, every step by its command, with the
release's `tools/upgrade.py` run from the template checkout. No other team's repository was
touched. Counts only.

`15ccaa0` carries the manifest label `unreleased`, so `--take` and `--adopt` ran with
`--allow-unreleased`; its files are the release's, which records the label in a commit of
its own (`RELEASING.md` item 4).

**The person's steps** were done as a person would do them, and only as the plan said:
- each layout entry the plan listed was copied from the release's contract;
- each changed entry's fields were brought to the release's;
- each file the plan said to copy from the release was copied;
- init's generators were run, the vendoring rebuild included, with `tools/sources.py
  --write` for the register the plan named;
- the starting files the release changed were carried over by hand, since a fresh project
  had edited none of them.

There was nothing to merge, and nothing was retained. The project had changed nothing.

## What the plan found

| | From v0.7.0 | From v0.1.0 |
|---|---|---|
| take | 9 | 33 |
| added | 5 | 37 |
| merge, collision, removed | 0 | 0 |
| pins (a BFO or CCO pin moved) | 0 | 0 |
| layout entries added | 4, each taken by `--take` | 34: 26 taken by `--take`, 4 starter files to copy, 3 generated, 1 present |
| layout entries changed | 0 | 10 (`template: seeded`, which v0.3.0 introduced) |
| skeletons changed | README.md, CLAUDE.md | README.md, CLAUDE.md, docs/HANDOFF.md |
| starting files changed | 0 | 4 (the communications README, the findings register, the third-party-text declarations, the research README) |
| release notes printed | v0.8.0 | v0.2.0 to v0.8.0 |
| not compared | none | none |

## After the procedure

| | From v0.7.0 | From v0.1.0 |
|---|---|---|
| files taken, files skipped | 14, 0 | 70, 0 |
| `--adopt` | adopted; nothing retained or unresolved; 2 for review | adopted; nothing retained or unresolved; 11 for review |
| original init block kept, exact commit recorded | yes, `15ccaa0` | yes, `15ccaa0` |
| a second plan: files to take or add | 0 | 0 |
| `template_status.py --against` the release | 0 changed, removed or added, owned and seeded | the same |
| every check | exits 0 | exits 0 but `tools/communications.py` |
| the project's suite | 930 passed | 928 passed, 2 failed |

The two failures from v0.1.0 are both named by the plan, and neither is a file the upgrade
carries:

- `tools/communications.py` refuses a message init deleted when the project was made. That
  is the defect decision 39 fixed in v0.6.0 for projects made from then on. A project made
  at v0.5.0 or earlier keeps the deletion in its history, as the v0.6.0 release notes the
  plan printed say.
- `tests/test_pins.py` looks for the pins command in the project's `README.md`. That file
  was rendered at init from a skeleton later releases changed, and the plan listed it for
  review, with the diff, for a person to carry over by hand.

## What the runs changed in the tool

The first runs found three gaps in the plan, fixed before these figures were taken (`bde1354`,
`13def77`, `15ccaa0`):

- An added layout entry for a file neither owned nor seeded was listed without saying its
  file was missing. Each now says what its file needs.
- Any change to `config/upstream-sources.yaml` was held back as a pin change. From v0.1.0
  the pins were the release's, and the file had only gained the vendoring outputs, which
  then could not be written. Now only a moved pin needs `--accept-pins`.
- Starting files the release changed were not mentioned. Each is now shown as a diff and
  listed for review, never written.

## What it does not show

- A project with changes of its own, which would put files in merge, collision or kept,
  and need `--retain`. Both projects were fresh. The tests plant those cases; these runs
  do not.
- That a migration of a project's own data is done. The procedure carries template files
  and reports the rest; a format change to a project's data is the release notes' to
  describe and a person's to make.
- Anything about BPO's or BCO's own repositories, which were not touched.
