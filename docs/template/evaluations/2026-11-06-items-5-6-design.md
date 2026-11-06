# Backlog items 5 and 6: design

**To:** the architect. **From:** the Ontology Template Team. **Date:** 2026-11-06.
**Status:** proposed. Nothing in it is built. **Under:** decision 29, which approved item 5
"with separate finding-validity, origin, and resolution fields, coordinated with P5" and
item 6 "for reproducibility improvements". §5 lists what is asked.

---

## 1. Item 5: a finding's validity, origin and resolution (P-A7, with P5)

### 1.1 What is wrong now

A register entry says that a finding is accepted, why, who answers for it and when it is
looked at again. It cannot say whether the finding is true. In WP6 the BPO Testing Team
classified 4,323 findings as real, false alarm, unsure, upstream or template bug, and that
classification is what made them reviewable (analysis §3.4). The register had no field for
it, so the team kept it in a document beside the register. Every project with many findings
would do the same, and the classification would drift from the entries it describes.

The team's five classes mix three questions. "Upstream" and "template bug" say where the
cause is; "real", "false alarm" and "unsure" say whether the finding is true; and none of
them says what is being done about it. Decision 29 asks for the three to be separate.

### 1.2 The fields

Three new fields on an entry, each with a closed set of values, and one for who decided:

| Field | Question | Values |
|---|---|---|
| `validity` | Is the finding true of the ontology? | `real`, `false-alarm`, `unsure` |
| `origin` | Where is its cause? | `project`, `upstream`, `template` |
| `resolution` | Why is it in the register rather than fixed? | `accepted`, `deferred`, `reported`, `not-a-defect` |
| `classified_by` | Who judged the validity, and in what capacity (P5) | `<name> (<kind>)` |

The resolution values:
- `accepted`: real, and kept on purpose (a modelling choice the check disagrees with).
- `deferred`: to be fixed here; the review date is when.
- `reported`: waiting on another party, the upstream or the template; needs `reference`, a
  URL or a message id.
- `not-a-defect`: a false alarm the check cannot tell apart, kept so the check stays exact
  (item 14 rejected loosening it).

A fixed finding is still recorded the way it is now, by removing its entry in the commit
that fixes it. There is no `fixed` value.

### 1.3 The rules the register check adds

| Rule | Why |
|---|---|
| `false-alarm` goes with `not-a-defect` or `reported` | A false alarm cannot be accepted or deferred as a defect |
| `unsure` goes with `deferred` only | An unsure finding is a question someone owes an answer to, by the review date |
| `origin: upstream` if and only if the entry has `upstream: <SOURCE> <IRI>` | Today only one direction is checked: an upstream focus needs `upstream` |
| `origin: template` with `reported` names the template issue or message in `reference` | A template bug nobody reported is not resolved by sitting in a project's register |
| `classified_by` names a kind from `config/review.yaml` | So a domain question decided by an ontologist is visible as such (§1.4) |
| `--propose` writes `TODO` for all four, and an entry with a `TODO` is refused | As it already does for reason, owner and review |

**None of this changes what the gate passes.** The gate still matches findings by
identity. The classification is for the people reading the register, and for the reports
in §1.5. A gate that passed or failed on `validity` would be a person's judgement counted
as a check's verdict, which item 13 rejected.

### 1.4 The part of P5 it needs

P5 is reviewer kind and capacity on reviews and gates. BCO asked for two additions: a
rights reviewer, and the capacity a reviewer acted in when one person holds two roles
(their answer, §4). Deciding that a finding is real or a false alarm is a review, so the
register needs P5's vocabulary of kinds now. It does not need P5's gates.

So item 5 builds the shared half:

```yaml
# config/review.yaml
version: 1
kinds:
  ontologist:          an ontology engineer judging the formal modelling
  domain-practitioner: someone who does the work the ontology describes
  architect:           the project's decision holder
  rights-reviewer:     whoever records a rights review (Legal decides)
```

A project may add kinds; the template's four may not be removed. `classified_by` is written
`Jane Doe (domain-practitioner)`. For one person who holds two roles, the kind is the
capacity they acted in for this entry.

P5's other half is a review record that names its reviewer and kind, and gates in
`config/stages.yaml` that name the kinds they need. It is held for its own design, with item
12 (domain review as a named gate). It uses the same file and the same kinds, so the two
halves cannot drift.

### 1.5 Reports

`tools/findings.py` prints counts by validity, origin and resolution, and by validity for
each check, rung and rule. That is the table the BPO team built by hand. The site, where it
shows accepted findings, shows the three fields with each. Item 11's
comparison of states can then compare real findings with real findings, and ignore false
alarms.

### 1.6 Registers already written

The register is `format_version: 1`, and a project's entries, the BPO port's among them,
have none of the new fields. The proposal:

- **Version 1 stays valid.** The new fields are not required, and the check prints how many
  entries are unclassified, as information.
- **Version 2 requires all four.** A project moves by setting `format_version: 2` once it
  has classified every entry.
- **No tool fills them in.** A migration that wrote `unsure` or `real` would state a
  judgement nobody made. `--propose --classify` may print the `TODO` fields for existing
  entries, for a person to fill in.

The template's own register is empty, so it moves to version 2 at once.

### 1.7 Tests

- One negative case per rule in §1.3, each refused with a message that names the rule.
- A version 1 register with no new fields passes and reports its unclassified count.
- A version 2 register missing any one field is refused.
- Gate behaviour is unchanged: the same findings with any classification give the same
  exit code. This test is what holds the line drawn in §1.3.
- Mutations: drop each rule and confirm a named test fails, then restore.

---

## 2. Item 6, part 1: transitive dependency locking (P-A1)

### 2.1 What is wrong now

`requirements-dev.txt` pins the six packages the tools import directly. The checks install
ten more that nobody pinned, in versions that change from one day to the next: owlrl, which
pyshacl uses for inference, and html5rdf, iniconfig, packaging, pluggy, prettytable,
Pygments, pyparsing and wcwidth; on Windows, colorama as well. CI also runs
`pip install --upgrade pip`, which moves pip itself.

So two runs of the same commit can run different code. The template's strongest claim is
that a measurement can be reproduced, and on this point it rests on PyPI's state on the day
of the run. The BPO port had to record the installed distributions in a manifest of its own
to make its states comparable.

### 2.2 The design

| Piece | What |
|---|---|
| `requirements-dev.txt` | Unchanged: the direct pins, each justified, checked by `pins.py` |
| `requirements-lock.txt` (new, generated) | Every distribution the direct pins pull in, plus pip: exact versions, the sha256 of every file PyPI publishes for that version, and environment markers (`colorama ... ; sys_platform == "win32"`). One lock serves Linux CI and Windows and macOS development |
| `tools/lock.py` (new) | Writes the lock (`--write`, online). Without arguments it checks offline that the lock names the digest of the `requirements-dev.txt` it was made from, that each direct pin appears in it at the same version, and that each entry has a hash. A stale lock fails the suite, as the corpus digest does |
| CI and `docs/DEVELOPMENT.md` | Every workflow installs `pip install --require-hashes -r requirements-lock.txt`, in place of the unpinned pip upgrade and the direct file. In hash-checking mode pip refuses any distribution the lock does not list, so an incomplete lock fails the install. The lock checks itself |
| `tools/pins.py` | Asks osv.dev about every locked distribution, not only the six. A newer release of a transitive one is reported for information; it moves when a direct pin moves, or when an advisory names it |
| Layout | The lock is a `generated-artifact` with `generator: tool.lock`, and `template: owned`, so `--against` reports it to projects |

**How the lock is resolved.** One lock for three platforms needs a resolver that keeps the
environment markers rather than evaluating them. There are three options:

| Option | For | Against |
|---|---|---|
| **uv** (`uv pip compile --universal --generate-hashes --python-version 3.12`), pinned with its sha256 in a new `config/tooling.yaml`, run only by `tools/lock.py --write` | Resolves for every platform at once, and keeps the markers. Fast. Never needed to run the checks | One more tool, used only when the lock changes |
| pip-tools (`pip-compile --generate-hashes`) | Long established, pure Python | Resolves only for the platform it runs on: a lock made on Linux leaves out colorama, and Windows then fails the install. One lock per platform, or a merge we would write ourselves |
| Our own: `pip install --dry-run --report` for each platform, merged, with hashes from PyPI's JSON | No new tool | A resolver merge is the kind of code the template should not own; `--platform` also needs wheels only |

**Recommendation: uv**, confined to the generator. The checks and CI never run it; they run
pip against the lock.

### 2.3 Tests

- Offline: the lock is current; a direct pin missing from it, at another version, or
  without a hash fails with a message naming it.
- In CI, the hash-checking install is itself the test that the lock is complete.
- A test in a fresh environment, installing from the lock alone and running the suite. It
  is the existing "install into an empty environment" claim in `requirements-dev.txt`,
  made a test.

### 2.4 Not covered

- **Python's patch version.** `setup-python` takes `3.12`, which moves with each patch
  release. The proposal is to record it rather than pin it: item 11's state manifest
  records the interpreter, and a pinned patch would be a pin to move every few weeks for
  nothing measured.
- **The Release workflow's runner.** Its first job runs on `ubuntu-latest`, which GitHub
  is moving to Ubuntu 26; the other jobs run on `ubuntu-24.04`. It is pinned in the same
  change, since it belongs with this item.

---

## 3. Item 6, part 2: the drift report sees shapes and config (P-A3)

### 3.1 What is wrong now

`template_status.py` compares only components declared `template: owned`. The shapes, their
fixtures, and the annotation-profile, naming and reasoning config have no `template:` value,
which the layout contract reads as "the project's own from the first commit". So when v0.2.0
changed the genus and deprecation checks, `--against` reported nothing for
`shapes/realist_shapes.ttl` to a v0.1.0 project. A project upgrading would learn about the
template's most important change from the release notes, or not at all.

They are not `owned` for a reason. `init` rewrites the namespace and the prefix inside every
shape and fixture, because SPARQL in a shape cannot read the project file. So a project's
shapes never have the template's bytes, and a byte comparison would report every one as
changed from the first commit.

### 3.2 The design

A third value of `template:`, **`seeded`**: the template ships it and keeps improving it,
and a project is expected to change it. For these:

| Component | Seeded because |
|---|---|
| `validation.wellformedness`, `validation.realist`, `validation.skos` | The checks; a project may add constraints |
| The three `fixture.*-bad-examples` | They move with their shapes |
| `config.annotation-profile`, `config.naming`, `config.reasoning` | The template's defaults, which a project sets for itself |
| `config.upstream-sources` | The BFO and CCO pins; a template move (CCO v2.2) should reach projects as a change to review |

Not seeded: `validation.annotation-profile`, which is generated from the profile config.
Its generator is owned, and its config is seeded, so a change reaches projects through
those.

**How a seeded file is compared.** The project's file is never rewritten back to the
template's form. Instead, the template's version goes through `init`'s own rewrite
(`init_project.turtle()`, moved to `tools/project.py` so both tools call one function) with
the project's values, and the result is compared with the project's file. An unchanged
shape then matches exactly, because the comparison makes the same change `init` made. The
YAML config is not rewritten by `init`, so it is compared as bytes.

The base has to be the template's file as the project received it. Two sources:
- **New projects.** `init` adds a block to the manifest, `initialized`: the project values
  it used and the digest of each seeded file after its rewrite. The plain report (no
  `--against`) then works offline: a seeded file whose digest differs is "configured here".
- **Projects made from v0.1.0 or v0.2.0**, whose manifest has no such block. `--against`
  takes the file from the template checkout's git history at the manifest's
  `template_commit`, and applies the rewrite. Without a checkout, the report says it cannot
  compare seeded files, and does not report them as unchanged.

**What the report says:**

```
  the template changed 2, added 1 seeded file(s) since this project's record
    changed  shapes/realist_shapes.ttl
    changed  shapes/realist_bad_examples.ttl
  configured here (expected): config/naming.yaml
  changed both here and in the template -- merge by hand:
    shapes/realist_shapes.ttl
```

A local change to an owned file is still reported as divergence. A local change to a
seeded file is reported as configuration, which is expected. A file changed on both sides
is flagged for a person to merge, for both kinds alike.

### 3.3 Tests

- Init a project in a temporary copy: every seeded file reports unchanged (the rewrite
  round trip). This is the test that would have caught the gap.
- Edit one shape in the project: it is reported "configured here". Edit it in a template
  copy too: it is reported "both".
- A v0.1.0-shaped manifest (no `initialized` block) with a template checkout: compared
  through git. Without a checkout: "cannot compare", never "unchanged".
- The template's `--check` covers the seeded files, so a stale record fails in the
  template.
- Mutations: compare seeded files as bytes, or skip the rewrite, and a named test fails.

### 3.4 Not covered

- **Merging.** The tool still reports and never merges. P-A2, the upgrade procedure, is
  where a person is told how; it builds on this report.
- **Generated files** are regenerated after an upgrade, not compared.

---

## 4. Order and size

1. **Item 6, P-A1 first.** It is small, and the rest is measured on top of it. One commit
   adds the lock, the tool and its tests; a second switches the workflows.
2. **Item 6, P-A3.** It adds `seeded`, moves the rewrite into `tools/project.py`, and adds
   the manifest block and the report.
3. **Item 5.** `config/review.yaml`, the register's version 2, the rules, the reports, and
   the site page.

Each part lands on `main` with its negative cases and mutations, as items 1 to 4 did. They
are released together as v0.3.0, under the release checklist.

## 5. What we ask

1. **Item 5:** accept or amend the three fields and their values (§1.2), and the rules that
   tie them together (§1.3).
2. **Item 5:** version 1 registers stay valid until a project moves (§1.6). The
   alternative is to require classification at once; that would turn the BPO port's
   unclassified entries into failures.
3. **Item 5 and P5:** build P5's shared half now, `config/review.yaml` with the four kinds
   and `classified_by` (§1.4), and leave its gates to their own design with item 12.
4. **Item 6:** uv as the lock's resolver, confined to the generator (§2.2), or one of the
   other two options.
5. **Item 6:** the seeded components (§3.2), and whether `config.upstream-sources` is among
   them.
