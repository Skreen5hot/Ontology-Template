---
id: EXAMPLE-LEGAL-2026-10-28-t9-third-party-text
from: EXAMPLE
to: LEGAL
date: 2026-10-28
type: request
subject: How the Ontology Template should record and report third-party text inside an ontology (T9)
in_reply_to: null
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: 7c4c84d70705ed3096de84f7ed27fe8804f08091
    path: docs/template/evaluations/2026-10-26-bpo-evaluation-response.md
    sha256: 2cb18c99003caf0034c406987681c73862504e55fe9dd10c4dc7b44ff1f2db07
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

## What we are asking

The Ontology Template is a starting point for public BFO/CCO ontologies. Its licensing
check works on whole files: each tracked file gets one licence disposition. An evaluation
found that this check passes third-party text quoted *inside* an ontology module. In the
evaluated case, thousands of verbatim passages from a third-party framework sat in a
module that was published under MIT, with no attribution to their source (finding T9 in
the referenced response).

We are building a control for this in work package WP4. Before we build it, we need your
wording and your limits. We do not want the tool to make, or appear to make, a legal
judgement.

## What we propose to build

1. **A declaration.** A project lists each annotation property that carries text from a
   third party. For each one it records the source and its release, the licence as the
   project understands it, and the attribution or notice the project has been told is
   required. The project supplies these values; the template ships none.
2. **Classification.** The licensing report shows that text as third-party, separately from
   the project's own licence.
3. **A check.** It fails when a module holds such text and its header does not carry the
   declared attribution, or does not name the declared source and release. It cannot find
   third-party text that nobody declared: a quotation looks like any other string. The
   declaration is what makes the text visible.
4. **A fixed statement.** Each report says it records declarations and checks that they are
   present, and that it does not judge whether redistribution is permitted.

## Questions

1. What must a declaration contain for the record to be adequate?
   - Is an SPDX identifier (or a "no known licence" value), plus an attribution text, the
     source and its release, enough?
   - Or does it also need, for example, a reference to the permission itself, who granted
     it, and when?
2. What should the report and the documentation say?
   - Is the statement in point 4 correct as a limit on what the check means?
   - Please give or amend the exact sentence you want used.
3. Text whose licence is unknown, or which no one has permission for:
   - Should the check fail the build until you decide?
   - Or should it report the text and pass?
4. Is checking the attribution on the module header enough?
   - Or must it also appear in released files (the release notice, the site's download
     page)?
5. Is there anything the template should refuse to publish at all, whatever a project
   declares?

## What we are not asking

Whether any particular project may redistribute any particular text is not part of this
request. The evaluated project's own question is B2 in the referenced response:
redistribution of 3,757 passages from APQC's Process Classification Framework. That
question is the Business Process Ontology team's to bring to you, under their governance.
The template provides only the mechanism to record whatever you decide.

## Until you answer

We will build the mechanism with no default licence, attribution or permission. Where the
report needs your wording, we will hold a placeholder that names this request. We will not
merge a version that presents a legal conclusion.
