---
id: EXAMPLE-BPOTEST-2026-11-17-pa4-resolved
from: EXAMPLE
to: BPOTEST
date: 2026-11-17
type: notice
subject: P-A4 resolved in template v0.13.0; BPO's second D7 rule can be a shape set
in_reply_to: BPOTEST-EXAMPLE-2026-10-30-wp6-phase-a-results
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 02401c8a7fb563bf304ff9af1f254811d11e8247
    path: communications/bpotest/incoming/2026-10-30-wp6-phase-a-results.md
    sha256: aa32783aeaa1dec6f99225f43afa41540aabab030fea1e7ee40faecb102aa0e4
  - repo: Skreen5hot/Ontology-Template
    commit: 02401c8a7fb563bf304ff9af1f254811d11e8247
    path: docs/template/evaluations/2026-11-17-pa4-design.md
    sha256: 8a5a447a22c49a7438bb008ca5120e6e8d62def8052e1e0efd153aeaa0c87008
  - repo: Skreen5hot/Ontology-Template
    commit: 02401c8a7fb563bf304ff9af1f254811d11e8247
    path: docs/template/evaluations/2026-11-17-pa4-disposition.md
    sha256: 9d6ff0e120a13c6f3d161a2693ece1a769c931ff671618df04d2b77b176b5e27
  - repo: Skreen5hot/Ontology-Template
    commit: 02401c8a7fb563bf304ff9af1f254811d11e8247
    path: docs/DEVELOPMENT.md
    sha256: 8d18cb4fde719ef784cffaaf5b6b281d47e0af0b50a216ef0cc3559d6b52b28a
  - repo: Skreen5hot/Ontology-Template
    commit: 02401c8a7fb563bf304ff9af1f254811d11e8247
    path: tests/test_naming_guide.py
    sha256: 52672476bc0fa430357b1a2f997457c4fb2556e4c0ea5145db4b6f3da3a5c2c8
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

This follows up §5 of `BPOTEST-EXAMPLE-2026-10-30-wp6-phase-a-results` (first reference).
You reported that BPO's second D7 rule cannot be stated as a scheme rule. The rule is that a
non-capability class with a `pcfID` must be named `P<pcfID>`. You measured it outside the
instrument, and found that it holds at both states. The template took it up as P-A4. It is
now resolved, in template **v0.13.0**.

## What we found

Your finding stands as you stated it. A scheme rule in `config/naming.yaml` relates a
local-name pattern to a category, and it cannot read a value off a class. That has not
changed.

The template could already run the rule another way: as a project's own SHACL-SPARQL shape
set, declared in the project's layout file. SPARQL can compare a local name with a literal
directly. Before proposing anything, we measured this on the template, not on your port
(second reference, §3). On planted classes, the template's Oxigraph runner and pyshacl
reported the same cases. With the shape set declared in a copy of the template, the gate
reported a misnamed class as a new Violation, and passed once the class was renamed.

What was missing was the way to it. The guide described scheme rules as the only naming
mechanism, and nothing pointed to a shape set.

## What the template now does (v0.13.0)

The architect resolved P-A4 in the guide and closed it (template decision 54, third
reference):

- **The guide.** `docs/DEVELOPMENT.md` has a new section, "A naming rule that relates a
  local name to a value" (fourth reference). It gives:
  - a worked shape set;
  - its fixture, with breaking cases and positive controls;
  - the two layout entries;
  - a project test listing the shape's message.
- **The choices.** The section says which choices are the project's, and where in the query
  each is made: exemptions, literal datatypes, language tags, whitespace and several
  values. The example makes one set of them, and says that none is a template rule.
- **A test.** `tests/test_naming_guide.py` (fifth reference) reads the example out of the
  guide and runs it through both engines. It requires each to report exactly the expected
  classes, by IRI and by code.

What it does not do:

- **No new scheme-rule form.** There is no `name_from` or similar. The architect decided
  against one.
- **Unchanged:** `config/naming.yaml`, the validator, the SPARQL runner, and the shape sets
  the template ships.
- **Nothing runs your rule.** The template ships no shape set for it, and nothing in the
  template knows `pcfID`, BPO's capability category or BPO's namespace.

## What it means for BPO

This is template support, not an implementation in BPO. BPO's second D7 rule is still
measured where you measure it. Nothing in your port has changed, and we have not looked at
it.

If you choose to move the rule into the instrument:

1. **Upgrade the port.** Take v0.13.0 by the upgrade procedure (`docs/DEVELOPMENT.md`,
   "Upgrading to a new template release"). From v0.12.0 the plan takes two files, the
   guide and the new test, and changes no layout entry. We measured that on a throwaway
   project made at v0.12.0, not on your port.
2. **Adapt the example.** Copy it into your own files, then replace:
   - the namespace;
   - the code property, with BPO's `pcfID` property's actual IRI;
   - the exempt category, with BPO's capability class.

   Make the choices the section lists as your own. BPO's governance decides them, not the
   template.
3. **Declare and test it.** Add the shape set and its fixture to your layout file, and the
   message test to `tests/project/`. None of these files is the template's, so none is
   reported as drift.

The gate then reports any class that breaks the rule as a finding, through the same
register as every other finding. You measured the rule as holding at both states, but we
make no prediction about what the shape set would find on BPO.

Whether to do any of this is BPO's call. Phase A's §5 measurement stands as you made it.
This message does not reopen any completed WP6 finding.

## What we expect next

Nothing. This message needs no reply and no act. If you do adopt the shape set and find
that the guide's example does not fit BPO's rule, we would like to hear what did not fit.
