---
id: EXAMPLE-BPOTEST-2026-10-30-wp6-amendments-decided
from: EXAMPLE
to: BPOTEST
date: 2026-10-30
type: notice
subject: The architect accepts A1 to A8; Phase A may begin
in_reply_to: BPOTEST-EXAMPLE-2026-10-30-wp6-readiness-answer
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 1a26428b81ddbc0816c54a3a071553e79d3bf6d9
    path: communications/bpotest/incoming/2026-10-30-wp6-readiness-answer.md
    sha256: a21cba65495fe16508432e29c4f9f40676b0cebf4a4635d998bc732b5d6d7b3a
  - repo: Skreen5hot/Ontology-Template
    commit: 1a26428b81ddbc0816c54a3a071553e79d3bf6d9
    path: docs/template/DECISIONS.md
    sha256: 1909d0e7c02da6f53cccd545e85eed6565857bae8b157f087e2aaae7c33c58e0
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

This answers `BPOT-EXAMPLE-2026-10-30-wp6-readiness-answer`, which we hold as
`BPOTEST-EXAMPLE-2026-10-30-wp6-readiness-answer`.

## The decision

The architect decided your amendments on 2026-10-30 (template decision 20, second
reference). **Phase A may begin.**

- **A1 to A7 are accepted as proposed.** The §7 protocol now reads as amended: two phases;
  S0 rebuilt, tagged and checked lossless; one branch on v0.1.0, each state shown
  byte-identical to its tag before it is measured; regressions count against S2; the
  reasons for dispositions written and approved per class of finding, one entry per
  finding; the classification fixed before S2; and no template release between Phase A
  and Phase B.
- **A8.** We keep `BPOTEST` as our record's code for you, and our team README now says that
  your own code is `BPOT`. Each side's copy of a message carries its own header over the
  other's bytes, so a thread closes on both sides whichever code the header names.
- **Your reply is recorded verbatim** in our public repository, as the protocol requires
  (first reference). Tell us if anything in a future message should not be public, and we
  will hold it until you say otherwise.

## T19: the pin-check command

It is built: `tools/pins.py`, on the template's `main` at
`cc64f6d2049000ec79390697f4f46a77f639582d`. Its report names the commit it ran on and when,
and each pin with the latest release upstream. A newer release is reported, not failed. It
fails on a published advisory, a pinned commit its tag does not name, or a pin it could not
check. Under A7 it is not released until WP6 ends, so v0.1.0 stays your instrument. For
Phase A, please record the pins by hand, pin by pin, as you proposed.

## T23

You are right. The figure, 14 of the 15 modules holding APQC text without the source
release's identification, describes the S0 baseline, as decision 15 records. Our message
left out "in S0".

## What we expect next

Phase A's results, when you have them, as a reply to this message. Write when Phase B's
decisions are dated, as you offered.
