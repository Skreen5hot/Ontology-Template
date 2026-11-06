# Review: a worked example

The review gate in `docs/process/METHOD.md` §4, on four defects no validation check decides. They
are the kinds the BPO evaluation found (template WP6, analysis §3.3), rewritten as synthetic terms in
an example namespace: over-claiming, a homonym, a duplicate and a misclassification. Each was in an
ontology whose axioms were consistent and whose checks passed.

## 1. The machine lists where to look

```bash
python tools/ontology/candidates.py
```

| Rule | Candidate | Evidence it shows |
|---|---|---|
| `necessity-without-axiom` | `ex:Pump` | The definition says it "requires a power source"; the class has no existential restriction |
| `definitions-differ` | `ex:Profile` | One IRI, two definitions under one genus: "describes a group of customers" in one module, "describes one customer's service requirements" in another |
| `near-duplicate` | `ex:Facility`, `cco:ont00000192` | The same label as CCO's Facility |
| `category-in-differentia` | `ex:Terminal`, `ex:Software` | "A material artifact that includes software": software is an information content entity, under a category BFO declares disjoint from material entity, and no restriction on the class accounts for it |

None of these is a verdict. A candidate is a place a person looks; nothing fails because one
exists. The rules, and what each cannot see, are in `tools/ontology/candidates.py`; their settings
are `config/candidates.yaml`.

## 2. A person answers each

```bash
python tools/ontology/candidates.py --propose >> proposals.yaml
```

prints an entry per unanswered candidate, every judgement a placeholder the register refuses. The
person who holds the role answers in `config/review-register.yaml`:

```yaml
entries:
  - rule: definitions-differ
    about: [https://example.org/ontology#Profile]
    validity: real
    resolution: fixed
    classified_by: Jane Doe (proxy-domain-expert)
    reason: Two kinds under one IRI; split into CustomerSegmentProfile and CustomerAccountProfile.

  - rule: near-duplicate
    about: [https://example.org/ontology#Facility, https://www.commoncoreontologies.org/ont00000192]
    validity: real
    resolution: fixed
    classified_by: Jane Doe (proxy-domain-expert)
    reason: The same kind as CCO's Facility; retired, with isReplacedBy to it.

  - rule: category-in-differentia
    about: [https://example.org/ontology#Software, https://example.org/ontology#Terminal]
    validity: unsure
    resolution: deferred
    review: 2027-01-15
    classified_by: Jane Doe (proxy-domain-expert)
    reason: Whether a terminal is the device or the device with its software is a question for a domain expert.

  - rule: necessity-without-axiom
    about: [https://example.org/ontology#Pump]
    validity: false-alarm
    resolution: not-a-defect
    classified_by: Sam Roe (ontologist)
    reason: '"Requires" describes the design intent, not a property every pump has; the definition is reworded.'
```

The answers are matched by rule and IRIs, never by text. A `fixed` answer's candidate is expected
to go; any other answer whose candidate goes is stale, and is removed in the commit that removed
it. `python tools/review.py` lists what is answered, unanswered, stale and overdue.

## 3. The gate checks the record

The charter names who holds each role (`docs/charter.md`, "Who holds which gate"):

```markdown
- Domain expert: none found yet
- Proxy domain expert: Jane Doe
- Ontologist: Sam Roe
```

and `config/stages.yaml` says which roles answer which rules at each stage. With `formalization`
marked `done`:

| The record | `python tools/stages.py` |
|---|---|
| No answers, no names in the charter | Refused: the charter names no one in the roles; each candidate has no answer |
| Every candidate answered, but the over-claiming one by the proxy domain expert | Refused: answered as `proxy-domain-expert`; this stage needs `ontologist` |
| An answer signed by someone the charter does not name | Refused: not named in the charter in that role |
| The deferral's review date passed | Refused |
| Every candidate answered by someone the charter names in a role the rule allows | Passes |

It passes the same way whatever the answers conclude. It checks that each place was looked at by
the right role, on the current corpus; it cannot check that the person is what the role says. The
charter says it, and the answer is signed.

## What this does not cover

The rules find candidates of a few kinds. Measured on BPO, they raised 2 of the 11 named defects
WP6 found (`docs/template/evaluations/2026-11-06-item-12-measurement.md` in the template). An
over-claiming relation written into a property's name and axioms, or a misclassification stated
without a telling word, is still a reviewer's to notice. Candidates from a model or a person's own
reading come in through `review/candidates/` (its README has the format and an example prompt), and
are answered the same way.
