---
id: EXAMPLE-BPOTEST-2026-10-30-wp6-readiness
from: EXAMPLE
to: BPOTEST
date: 2026-10-30
type: request
subject: WP1 to WP5 are complete and template v0.1.0 is released; are you ready to run the final evaluation (WP6)?
in_reply_to: null
refs:
  - repo: Skreen5hot/Ontology-Template
    commit: ee4353db68c2c9dc36f6531e7e531123e01316bf
    path: docs/template/evaluations/2026-10-26-bpo-evaluation-response.md
    sha256: 2cb18c99003caf0034c406987681c73862504e55fe9dd10c4dc7b44ff1f2db07
  - repo: Skreen5hot/Ontology-Template
    commit: ee4353db68c2c9dc36f6531e7e531123e01316bf
    path: docs/template/ROADMAP.md
    sha256: 8a609816ba4fc833435cebd4536997274c0a83f35b5c0a52fdda417f79453040
  - repo: Skreen5hot/Ontology-Template
    commit: ee4353db68c2c9dc36f6531e7e531123e01316bf
    path: docs/template/DECISIONS.md
    sha256: 1a64b7eec7a5002b685e95f03a6ec8295123d7ee6c3692c862df237c64daa0a2
  - repo: Skreen5hot/Ontology-Template
    commit: ee4353db68c2c9dc36f6531e7e531123e01316bf
    path: config/template-manifest.json
    sha256: 44145aaaf8189ade0470a29a566048b5ade2c16c0985d4989648d5019f6ad41c
author: Claude (agent), drafted at the direction of Aaron Damiano, the architect
requires_act: false
---

## Why you are hearing from us

On 2026-10-26 we answered your evaluation of the template with a corrective-action plan of
six work packages (the first reference, "the response"). Since then we have built and
closed the first five without writing to you. This message brings you up to date and asks
whether you are ready for the sixth, the final evaluation, which is yours to run.

## Where the template stands

- **WP1 to WP5 are complete**, against the criteria in §5 of the response. WP1 was
  completed on 2026-10-27 and WP2 begun on it (decision 12); the architect accepted WP2
  and WP3 on 2026-10-28 (decisions 13 and 14), WP4 on 2026-10-29 (decision 15) and WP5 on
  2026-10-30 (decision 17). What each one built and how it was measured is in the
  ROADMAP, "Phase 9" to "Phase 13, as built".
- **Template v0.1.0 is released**, the tag `v0.1.0` on commit `ee4353d`, with its manifest
  recorded under that label. This is the template release we propose for the final
  evaluation: S0, S1 and S2 all measured with it (§7, point 1).

## What changed from what you were told

1. **Corrected BPO figures** (decision 15). Re-measured under WP4: T10 is 2 used
   properties in 494 assertions on 453 classes (`requiresPermission` is declared but unused
   and not counted); for T11, the 78 genus warnings are gone and 18 qualifier warnings are
   new findings, not old ones carried over; for T23, 14 of the 15 modules holding APQC text
   lack the source release's identification. These replace the response's estimates.
2. **T9 is detection only, for now.** The check that finds third-party text inside a module
   is built and accepted. The policy for what it must require waits on Legal, and the
   template says so in its output (PENDING LEGAL). No check here establishes legal
   permission, the sufficiency of an attribution, or BPO's right to redistribute APQC text.
   B2 stays yours and Legal's.
3. **T17's worked example is generic.** The response named your port script. Because your
   repository is private, the porting guide (`docs/PORTING.md`) carries a generic lossless
   check instead, and the template's suite runs it.
4. **T19: no Dependabot** (decision 16). Nothing updates the template's pins by itself, so
   checking every pin is now a project's first step (`docs/DEVELOPMENT.md`, "Pins"). v0.1.0
   was released with every pin checked; CCO stays at v2.0, since your port was built on it,
   and moving it would mean WP6 measures two changes at once (decision 18).
5. **T21's manifest field** `template_commit` names the commit the manifest was recorded on,
   the parent of the commit that carries it; the release tag names the carrying commit.

## What we are not asking

Your findings are yours. The register holding BPO's 3,716 findings shows only that it can
hold them; which are real, which get fixed and which are accepted are the BPO team's
decisions, each with BPO's reason and owner. Nothing from your port is carried into the
template, and nothing about your runs goes into its public CI.

## What we ask

1. **Are you ready to run WP6?** If so, when; if not, what you are waiting on.
2. **§8 of the response, still unanswered:** confirm or amend the dispositions in §3,
   especially the five whose remedy changed (T7, T11, T12, T14, T18), and the three above
   that changed since (T9, T17, T19); and confirm or amend the protocol in §7.
3. **The S1 reference:** confirm that your port repository is still at `c062662`, or tagged
   there.
4. **The instrument:** confirm that v0.1.0 is the release you will measure S0, S1 and S2
   with, or say which, and why.
5. **The items carried to WP6** (ROADMAP, "Carried to WP6") that only your side can close:
   - the BPO-scale times of the complete Checks and Reasoning jobs, measured in your
     repository on GitHub's standard runner, with the runner's conditions recorded;
   - BPO's own dispositions of its findings;
   - the evidence for the first verdict, whether the template improves the ontology itself,
     with improvements in the template reported apart from improvements in BPO's content;
   - a browser run of the term explorer on your port's site, showing every conflicting
     variant, its module, and the term's notes and accepted findings.

Please reply to this message, by its id, with your answers. Where you amend the protocol,
the architect decides on the amendment before WP6 begins.
