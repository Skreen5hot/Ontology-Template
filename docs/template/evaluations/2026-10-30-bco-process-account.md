# The BCO team's account of its ontology process (2026-10-30)

Recorded verbatim, as the architect relayed it on 2026-10-30. The architect asked the
Business Capability Ontology (BCO) team, which started from an early version of the
template's structure, for an account of its ontology-building process. The template's
response, which reviews it and proposes what to change, is
[`2026-10-30-bco-process-account-response.md`](2026-10-30-bco-process-account-response.md).
The text below the rule is as received, its first line included (the BCO session's
preamble); its SHA-256 is in the response.

---

I'm reading the remaining records: inventory scope, the repository setup, and what preceded the specification. Then I'll write the accounting.

# BCO: how the ontology has been built so far, and what comes next

This covers the ontology-building process, not the engineering. Stages run in the order they actually happened, then continue to the end. ✅ done · 🟡 in progress · ⬜ not started.

---

## 1. Scope and purpose ✅ (implicitly)
**What we did:** set the purpose in the specification's §1. BPO says what an organization *does*; BCO says what it *can* do. BCO takes its act types from BPO and adds the capabilities those acts realize. It also lists non-goals: individual competency, a new act hierarchy, scoring methods, deontic logic, industry frameworks.

**Key finding:** BCO is a *module* of BPO, not a standalone ontology. That one choice fixed dependency management, pinning and cross-team communication for everything that followed.

**Gate used:** none of its own. Scope was approved inside the specification draft.

**Gate we should have had:** a scope charter gate *before* any drafting. It would approve purpose, non-goals, the dependent ontologies and the competency questions. The competency questions (CQ-1 to CQ-14) only appeared inside the specification.

## 2. Source research and the citation register ✅
**What we did:**
- A register of 63 sources: standards bodies, government, industry frameworks, formal ontology and management practice.
- Each claim was graded by how it was verified: V read in the primary text, P part of the primary read, S secondary only, K prior knowledge, L behind a login or paywall.
- Synthesis findings SF-01 to SF-06.

**Key findings:**
- **"Capability" is a homonym in the sources.** In ISO/IEC 33020 and CMMI it is a quality of a process. In FIBF a "business capability" is a requirement record.
- **BFO placement:** IOF Core and Beverley et al. make capability a BFO Disposition; CCO declines to.
- **Material basis:** using BFO's `has material basis` *entails* a disposition. An "arrangement" cannot be a material basis (SF-03).
- **Bearer:** making the organization the *only* bearer is narrower than every source (SF-05).
- **Artifacts:** treating them as enabling conditions departs from the enterprise-architecture and defence mainstream (SF-06).
- **Process finding:** SRC-GOV-06 stayed secondary-only until the closure set.

**Gate used:** none formal. The register later became data with automated checks.

**Gate we should have had:** a **source adequacy gate**. Every source the design relies on should be primary-verified (V or P), or explicitly excused, before design decisions cite it.

## 3. Specification drafting with external review ✅ (draft only)
**What we did:**
- v0.1 to v0.4 through reviews R2 to R5.
- Design decisions CD1 to CD17, requirements CAP-01 to CAP-31, CQ-1 to CQ-14.
- Ten ratification points (RP-1 to RP-10) and open issues OI-1 to OI-19.
- Two human tests: G1-T admits a capability *type*; G1-I attributes a capability to a particular organization.

**Key finding:** the specification committed to formal choices (Disposition subclassing, OWL patterns, SHACL rules) before a conceptual baseline existed. The two foundational choices were later re-decided in conceptual modeling: RP-1 (what bears a capability, and on what basis) and RP-10 (admission versus attribution).

**Gates used:** review rounds R2 to R5.

**Gate not yet passed:** CP-0, "RP-1 to RP-10 ratified; ADR-002 accepted". Nothing in the specification is normative yet.

**Gate we should have had:** an ordering rule. The specification is *ratified* only after the conceptual model is approved, and is *drafted* as a hypothesis before that.

## 4. Governance foundations ✅
**What we did:**
- Decisions are recorded verbatim, with digests of what they are about.
- Architecture decision records: ADR-003 for the controlled vocabulary; ADR-002 is still pending.
- Five provisional namespaces, still awaiting RP-5.
- Pinned upstream sources (BFO, CCO, BPO).
- A communications protocol with BPO; errata as new records, never edits.

**Key finding:** decisions made *in the course of the work* need a home and a propagation path. DP-1 and DP-2 now live in CM-01 and must still be carried into specification v0.5. The template should say where a decision of record lives, and what forces it into downstream documents.

**Gates used:** ADR ratification, the repository setup decision, and the upstream re-pin process (approval, migration record, notice to BPO).

## 5. Stage 01: Controlled vocabulary ✅ (14 Draft concepts, none ratified)
**What we did:**
- Plan P0 to P5.
- 9 metamodel concepts, one per specification term, and 5 pilot catalog concepts.
- External reviews: R6 (ontological) and R7 (formal, on the Turtle).

**Key findings:**
- **Catalog definitions** first enumerated practices. R6 had them rewritten into one general form: an organization's capability realizable in its planned acts.
- **Weak evidence for the catalog:** 36 of 41 "consistent-with" citations were only *contextual*. No source specifically backs any catalog definition.
- **SKOS is not OWL:** R7 found the output an acceptable SKOS vocabulary, not a formal ontology.
- **Genus:** a definition's genus (Business Capability) was separated from its foundational BFO/CCO ancestor.

**Gates used:** plan approval, acceptance of each phase, and the review dispositions. A ratification act is defined (explicit IRIs plus digests plus two approvals) but has never been performed.

**Gates we should have had:**
- **A Stage 01 standard.** None was ever supplied; ADR-003 stood in for it.
- **An ordering rule.** Catalog concepts were written before the admission criteria (RP-10) existed, which caused rework. Metamodel vocabulary can come first; catalog vocabulary should wait for the conceptual model.

## 6. Stage 02: Conceptual modeling ✅ (CM-01 approved 2026-10-26)
**What we did:** CM-01 under the Stage 02 standard. It has 5 patterns, 33 concepts, 39 relationships and 6 diagrams, with every CQ traced. Two decision points, DP-1 and DP-2, carried options, the register's evidence and a recommendation. Reviews R8 and R9 followed.

**Key findings (the heart of the ontology):**
- **DP-1, bearer and basis:** the organization alone bears a capability. Its basis is its member agents. Artifacts are enabling conditions, and losing one does not by itself end a capability.
- **DP-2, admission and attribution:**
  - G1-T admits capability *types*; G1-I attributes a capability to an organization *on evidence of capacity*.
  - Actually exercising a capability supports a claim but is never required.
  - There is no "interest condition".
- **R9:**
  - Functional adequacy is a separate assessment and is never inferred from possessing components.
  - Standing-function designation is conditional.
  - Inadequate evidence must be distinguished from a "not met" finding.

**Gates used:**
- The standard's §7 quality gates.
- An automated format check (completeness only).
- External review.
- Architect approval.
- After approval, change only by a new reviewed version.

**Gate we should have had:** **domain-stakeholder review.** The standard requires it, but in practice reviewers were ontologists plus the architect. No capability-management practitioner has reviewed the model.

**Still to do:** CM-02, Agent Capability, is planned and not started.

## 7. Stage 03: Taxonomy 🟡 (evidence gathering only)
The Capability Term Inventory gathers source evidence for it. Inventory is *not* vocabulary and *not* admission (scope decision D6).

| Phase | Status | Key findings |
|---|---|---|
| I-1 BPO harvest | ✅ | BPO marks no standing-function nodes. Its capability index breaks the "exercise, not development" rule in 14 places (Q-12). Text tied to the APQC PCF had to be withheld until rights were settled. |
| I-2a rights review | ✅ | APQC terms ambiguous; FEAF BRM is clean US Government work; FIBF is mixed (21 MITRE-marked workbooks, third-party mappings). |
| I-2b APQC PCF 7.4 | ✅ | Published only via BPO, with APQC's notice on every artifact. You accepted the residual risk. |
| I-2c federal catalogs | ✅ | BRM extracted from its tables (20 functions and 20 services appear only in diagrams). The 11 HR lists that link to MITRE are withheld. FIBF "business capability" is flagged as a homonym. |
| E7 release | ✅ | I-1's withheld text released, unchanged and traceable. |
| E4 standing functions | 🟡 | Method decided (Option A); no candidate judged yet. |
| I-3 restricted catalogs | ⬜ | Citation and coverage only. |
| I-4 crosswalk and triage | ⬜ | Grouping and deduplication across sources. |
| I-5 first tranche | ⬜ | A recommendation, for your separate approval. |
| The taxonomy itself | ⬜ | No Stage 03 standard yet. |

**Key process finding:** rights and provenance are a first-class gate. Harvesting before the rights review (I-1) forced withholding. APQC then took three decisions to resolve, and one source was re-sourced through BPO.

**Gates used:** scope approval, a reviewed PR per phase, rights decisions, and the closure set.

**Gate we should have had:** a **rights and provenance gate before any harvest**, with withholding as the default until it passes.

## 8. Stage 04: Thesaurus ⬜
**Expected work:**
- synonyms;
- a homonym register (ISO and CMMI "capability", FIBF "business capability");
- mappings to external schemes (APQC, BRM, FIBF, and later BIZBOK and BIAN).

**Rule to carry:** term hierarchies and associations never become ontological relations automatically (Stage 02 standard §8.1).

**Gates to have:** mapping review, a check against the homonym register, and a Stage 04 standard.

## 9. Specification v0.5 and ratification (CP-0) ⬜
**Expected work:**
- carry DP-1, DP-2 and R9 into CD1 to CD3, CD16, CD17 and §8;
- resolve the BPO act-index dependencies (CM-01's Q-12 to Q-14);
- ratify RP-1 to RP-10, accept ADR-002, and mint the permanent namespace (RP-5).

**Gate:** CP-0. This is the hard stop before any ontology term is written.

## 10. Stage 05: Formalization ⬜
**Expected work:**
- run G1-T on each capability class, then make it a Disposition subclass;
- align to BFO and CCO, and write axioms;
- apply the SHACL rules (CAP-xx);
- run the reasoners: ELK on every commit, HermiT at release.

**Gates (already designed):** Gates A to D, C-A, M and D2; semantic review F; CP-1 (refactored classes, every fixture failing as stated); CP-2 (D2 run, CQ-1 to CQ-14 answered over a fixture organization).

**Gates we should have:** a Stage 05 standard, and a **conceptual-fidelity check**. Each formal choice either preserves CM-01's meaning or documents why it changes it (standard §8.2).

## 11. Stage 06: Knowledge graph ⬜
**Expected work:**
- G1-I attributions for real organizations, each backed by a recorded assessment;
- assessments, maturity ratings, sourcing statements and the coverage register;
- migration of the v0.1 `bc:` vocabulary.

**Gates:** CP-3 (every scope entry audited, the coverage register populated, the migration complete), plus the evidence rules: completeness manifests, and adequacy never derived.

## 12. Release and maintenance ⬜ (parts already practiced)
**Expected work:** versioned releases, change management, re-pinning dependent ontologies, and notices to and from other teams.

**Already practiced:** the BPO re-pin process, the communications protocol, and errata.

**Missing:** a release gate (the D2 reasoner at release, a deprecation policy) and a consumer impact check (OI-10).

---

## What the template's normative process should take from this

1. **Order the stages:** scope charter and CQs → source research → conceptual model → specification ratification → vocabulary and taxonomy population → formalization → knowledge graph. BCO drafted the specification and the catalog vocabulary before the conceptual baseline, and paid in rework.
2. **Supply every stage's standard before the stage starts.** Only Stage 02 had one. The rule "a gate states its conditions before the phase starts" was broken for Stages 01, 03, 04, 05 and 06.
3. **Make four gates explicit that BCO discovered late:**
   - source adequacy;
   - rights and provenance before harvest;
   - domain-stakeholder review;
   - conceptual fidelity at formalization.
4. **Keep three separations:**
   - evidence is not vocabulary is not admission;
   - type admission (G1-T) is not instance attribution (G1-I);
   - conceptual approval is not specification ratification is not OWL.
5. **Hold a closure gate** before opening the next phase, as the 2026-10-30 closure set did. Every outstanding decision is resolved, merged and recorded first.
