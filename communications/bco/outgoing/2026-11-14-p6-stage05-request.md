---
id: EXAMPLE-BCO-2026-11-14-p6-stage05-request
from: EXAMPLE
to: BCO
date: 2026-11-14
type: request
subject: P6 (conceptual fidelity) is in template v0.8.0; please tell us when your first substantive Stage 05 module exists
in_reply_to: BCO-EXAMPLE-2026-10-30-process-proposals-answer
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 20f5c814dcb94c3ef862507b1258b410bafbc5d7
    path: docs/template/evaluations/2026-11-07-p6-design.md
    sha256: 667bd1d4761baecf1fd7336c6e695313a820339f846add373578ca1f52f34d7d
  - repo: Skreen5hot/Ontology-Template
    commit: 20f5c814dcb94c3ef862507b1258b410bafbc5d7
    path: docs/template/evaluations/2026-11-14-p6-disposition.md
    sha256: 9a6fbc38970cc12241841eea73a3cdee416870da9aa98858e778e7aea9051c20
  - repo: Skreen5hot/Ontology-Template
    commit: 20f5c814dcb94c3ef862507b1258b410bafbc5d7
    path: docs/template/evaluations/2026-11-14-p6-measurement.md
    sha256: 7f2a0d51ce44395b31040197b93769fc41adff91c39f5334daf10e9c0104507a
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

## Why you are hearing from us

Your answer of 2026-10-30 asked that P6, conceptual fidelity, be designed against a real
formalization. None existed, so the architect decided to build it now and test it on
yours when there is one (decision 42, second reference). It shipped in template v0.8.0
on 2026-11-14.

## What it does, in short

- `ontology/trace.yaml` links each element of an approved conceptual model, written
  `CM-01#RL-01`, to the authored terms, shapes and competency questions that formalize
  it. Each link is either reviewed as preserving meaning, or covered by a decision that
  authorizes the change or the omission from OWL.
- Your three points are all in it: imported terms are out of scope, links are
  many-to-many, and axioms are digested so a changed axiom reopens the review.
- Your three expected changes are its test cases: `has material basis` entailing
  Disposition, conditional designation as a shape, and the closed-world question.

## What we measured on BCO, and what we did not

We read CM-01 read-only, counts only, and changed nothing in BCO (third reference). The
anchor rules find all 101 of its elements: 5 patterns, 33 concepts, 39 relationships, 2
decision points and 22 boundary rows. This is reference coverage, not fidelity. Nothing
was traced, because no Stage 05 module has a term yet.

## What we ask

When your first substantive Stage 05 module exists, please send a short notice naming
the commit. We would then run the same read-only measurement against it and report the
counts to you: elements traced, untraced, not formalized, preserving, and changed by a
decision. Nothing in BCO would be modified. You need not adopt P6 to take part, and
nothing here asks you to decide anything now.
