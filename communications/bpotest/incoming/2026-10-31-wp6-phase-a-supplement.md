---
id: BPOTEST-EXAMPLE-2026-10-31-wp6-phase-a-supplement
from: BPOTEST
to: EXAMPLE
date: 2026-10-31
type: notice
subject: Supplement to our Phase A results — two template findings since (P-A8, P-B1), one correction pending, the current record
in_reply_to: EXAMPLE-BPOTEST-2026-10-30-wp6-amendments-decided
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: d634faeb3025acbe0f4cd6848d5d386ac03be956
    path: communications/bpotest/incoming/2026-10-30-wp6-phase-a-results.md
    sha256: aa32783aeaa1dec6f99225f43afa41540aabab030fea1e7ee40faecb102aa0e4
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: false
source:
  repo: Skreen5hot/BPO-Template-Port
  commit: 003e44ae98f97d31539a6ddefbd2b03f46edc029
  path: communications/example/outgoing/2026-10-31-wp6-phase-a-supplement.md
  sha256: 714dfa5b8b036b934479d801fbb1b4feee3f9b1e84049848d462a0d82b67ff1a
---
---
id: BPOT-EXAMPLE-2026-10-31-wp6-phase-a-supplement
from: BPOT
to: EXAMPLE
date: 2026-10-31
type: notice
subject: Supplement to our Phase A results — two template findings since (P-A8, P-B1), one correction pending, the current record
in_reply_to: EXAMPLE-BPOT-2026-10-30-wp6-amendments-decided
refs:
  - repo: Skreen5hot/BPO-Template-Port
    commit: c52a491cc647751fec02a8a84d2e429262e8cbe2
    path: communications/example/outgoing/2026-10-30-wp6-phase-a-results.md
    sha256: 31848c25f2c8516fc75ea16437b140c1cb72fed9d6deb81b494ecfa36fc91b98
  - repo: Skreen5hot/BPO-Template-Port
    commit: 36193d9be42210788bd63ef8ded680be035a9546
    path: research/wp6/phase-a.md
    sha256: 5f5f1631a38ec0b378303cb0422b14a79176c282a397ad9a41afbf5ceb544a06
  - repo: Skreen5hot/Ontology-Template
    commit: ee4353db68c2c9dc36f6531e7e531123e01316bf
    path: shapes/realist_shapes.ttl
    sha256: 852cf9585b92a08c88164379538e2a0463ef9f147e070875fa76e9571e4ce0fa
author: Claude (agent), drafted at the direction of Aaron Damiano, the BPO architect and PO
requires_act: false
---

This adds to our Phase A results, `BPOT-EXAMPLE-2026-10-30-wp6-phase-a-results` (first
reference), which you have not yet recorded. Please read the two together. Nothing here
changes a Phase A figure.

## Summary

- **Two more template findings:** P-A8 (the site footer) and P-B1 (the genus check).
- **One correction to the classification, pending.** 10 of the 53 comment-drift findings
  are not what our reason says. The BPO architect has not yet decided it, so it is
  reported here as pending, not settled.
- **The current record** is `research/wp6/phase-a.md` at `36193d9` (second reference). Our
  results cited it at `119c0e1`. Two changes since: P-A8, and the note that the explorer
  inspected was the local v0.1.0 build of S1.
- **Phase B has started on BPO's side.** BPO's decisions are not made yet; we will write
  when they are, with the S2 commit.

## P-A8. The site footer has no place for a third-party attribution

Found on 2026-10-30, after our results were sent, while adding APQC's notice to the port's
public site. BPO's answer on B2 (APQC's licence, now closed by BPO's architect) requires
the notice in the footer of every page showing PCF text.

The footer says that project-authored content is under the project's licence, and names
only the vendored extracts' licences. A page made mostly of declared third-party text
therefore reads as MIT. v0.1.0's footer is the same, and the attribution declared in
`config/third-party-text.yaml` does not reach the site.

We put the notice in through `site.json`'s `acknowledgment` text, the only curated footer
field (port `main`, `7674579`), and it is live on the port's site. That works, but it uses
a credit line for a licence notice.

## P-B1. The genus check passes a definition that names the parent anywhere

Found on 2026-10-31, in BPO's Phase B work, but it is a defect of the Phase A instrument.

The shape (third reference, the "Genus" constraint) reports a class only when **no**
definition **contains** the parent's label. So it passes in two cases it should not:

1. **One agreeing definition hides a contradicting one.** A class with two definitions
   passes if either names the parent. BPO's PerformanceMeasure is defined under Descriptive
   ICE in one slice and as "a Directive ICE that prescribes…" in another. The second is
   never reported as a genus problem, only as drift.
2. **The label can appear anywhere, not as the genus.** "An Agent that bears a supplier role
   … that supplement an organization's service delivery" passes under the parent
   Organization, because "organization" occurs in the differentia. Its genus, Agent,
   contradicts the parent: Organization is not an Agent in CCO 2.0.

A check that reads the genus position ("a(n) <parent> that…"), and checks each definition,
would report both. We do not ask for a change before Phase B (A7). We record it so that
Phase B's verdict does not read "no genus finding" as "no genus defect".

## Pending: K08's reason is wrong for 10 of 53 findings

Our classification (K08, comment drift, "real") gives the reason "inlined copies of a shared
term have drifted". That is true for 43 of the 53:

- **7** are deliberate review addenda: a second comment in the *same* module, added as a
  caution (e.g. "FALSE-FRIEND note"). That is BPO practice and legal RDF. The proposal
  before the BPO architect is to reclassify them **false alarm**, since the one-comment rule
  meets a legitimate practice there.
- **3** were created by the port, which merged three BPO files into one module. They stay
  **real**, owned by the port.

Under A6, a reclassification is a new, dated register change with its reason. We will make
it, and tell you, once the architect decides. Until then the Phase A totals stand as sent.
