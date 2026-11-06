# Candidates from elsewhere

`tools/ontology/candidates.py` lists review candidates by fixed rules. A language model, another
tool or a person's own reading can find others: an over-claiming definition no word list catches, a
class placed under the wrong category without a telling word. Put them here, one YAML file per run,
and `tools/review.py` lists them beside the generated ones, to be answered in
`config/review-register.yaml` the same way (backlog item 12, template decision 34).

The template ships no model runner, and nothing here runs in CI: a file is produced locally, under
whoever runs it, and committed. CI only reads it.

## The format

```yaml
provenance:
  source: model-review          # names the rule: external:model-review
  produced_by: Jane Doe, running a model locally
  date: 2026-11-06
  corpus: <the corpus digest from `python tools/ontology/candidates.py --json`>
  model: <the model's identifier>          # for a model, with:
  prompt_sha256: <sha256 of the prompt as sent>

candidates:
  - rule: external:model-review
    about: [https://example.org/ontology#Terminal]
    message: The definition says every terminal is used in ordering; no axiom says so.
    evidence:
      definition: A material artifact that is always used in ordering.
```

Every `provenance` field is required, and `model` and `prompt_sha256` together when either is
given. A file run on another corpus than the current one is reported as such; run it again, or
remove it. A candidate's identity is its rule and `about`, so its answer survives a rerun that
rewords the message.

## An example prompt

A starting point, to be adapted; record the digest of the version you send.

> You are reviewing an ontology aligned to BFO and CCO. For each class below you are given its IRI,
> its label, its definition and its axioms (parents and restrictions). List only the classes where
> one of these may be true, and for each say which and quote the words that suggest it:
>
> 1. The definition claims something every instance has or does that no axiom states.
> 2. The definition describes a different kind of thing from the class's parents (for example, a
>    material thing defined as including information or software).
> 3. Two classes in the list describe the same kind of thing.
> 4. One class's definition could be read as two different kinds of thing.
>
> Do not judge whether the ontology is right. A person will answer each item. Output YAML in the
> `candidates:` format given.
