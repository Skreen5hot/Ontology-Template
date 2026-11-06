# P4: the architect's disposition

**Date:** 2026-11-06. **Decision:** 36 (`docs/template/DECISIONS.md`). In answer to
`2026-11-06-p4-design.md` section 7. The text is headed "Architectural Decision 34"; the
template's record already numbers decisions 34 (item 12) and 35 (the review roles), so it
is recorded as 36, its heading kept as written. The text below the rule is the architect's,
verbatim, as pasted; its SHA-256 is
`fe907de8ea5df4f74a0c816f5d5fb3b0cc2293faf355dd644ab8a0409b6998f3`.

---

# Architectural Decision 34 — P4 Source Adequacy

Approved with minor amendments

Date: November 6, 2026\
Scope: P4 — Source Register and Source Adequacy Check\
Target release: Ontology Template v0.5.0

I approve P4 for implementation and release as v0.5.0, subject to the refinements below.

This is a worthwhile improvement. The BCO evaluation identified a gap between documenting sources and ensuring that the evidence supporting architectural decisions had actually been examined.

P4 addresses that gap without attempting to automate human judgment about the credibility or meaning of a source.

The distinction is important:

- Human responsibility: Determine what the source says, how thoroughly it has been examined, and whether it supports a decision.
- Template responsibility: Verify that the source, verification grade, citation, and any approved exception are recorded consistently.

That separation is consistent with the Ontology Template's purpose and the decisions reached during WP6.

## 1. Decisions on the seven questions

| # | Question                                                        | Architectural decision                                                                                                                                       |
| - | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1 | Where should the source register live?                          | Approve. Use `research/sources.yaml` as the seeded authoritative register and generate `research/sources.md`.                                                |
| 2 | Which files require source adequacy checking?                   | Approve. Use `docs/decisions/`, `docs/standards/`, and `docs/charter.md` as defaults, configurable through seeded `config/sources.yaml`.                     |
| 3 | Who approves exceptions?                                        | Approve. The project architect by default. Projects may explicitly authorize additional reviewer kinds through `config/review.yaml`.                         |
| 4 | Should the quote limit be configurable?                         | Approve. Leave the limit unset by default. Projects may establish their own restrictions. This is not a legal determination.                                 |
| 5 | Should inadequate citations fail CI?                            | Approve. A declared citation without adequate verification or an approved exception fails Checks.                                                            |
| 6 | Should whole-source citations require every claim to be V or P? | Approve, with safeguards. Require at least one registered claim. Do not accept a source merely because one claim is verified while others remain unexamined. |
| 7 | Should P4 ship alone as v0.5.0?                                 | Approve. Complete P4 and its tests before beginning P7, P8, or P6.                                                                                           |

## 2. Three refinements required before implementation

### A. Source claims need stable identities

The proposed source register identifies claims by position, such as `SRC-STD-01-C2`.

This introduces a reproducibility risk: adding or reordering claims can change what `C2` refers to without changing the citation written in a decision.

Required amendment: Give claims explicit, stable identifiers.

For example:

```
claims:
  - id: C1
    status: V
    scope: clauses 1 to 5
  - id: C2
    status: L
    scope: annex B
    note: primary text not available
```

The resulting citation remains `SRC-STD-01-C2`, but its meaning no longer depends on its list position.

For compatibility with BCO's existing register, the read-only measurement may interpret historical positional claim identifiers. New template projects should use explicit IDs.

This is a small change that prevents a significant provenance defect.

### B. A verification grade must identify what was verified

I approve retaining BCO's five grades exactly: V, P, S, K, and L.

However, a grade must not be interpreted as establishing more evidence than was actually examined.

For V and P, the register should identify the scope of the primary text examined. P must make the partial coverage explicit.

For example, reading clauses 1–5 does not establish that the source's unexamined annexes support the same conclusions.

The adequacy check can verify that a citation points to a suitably graded claim. It cannot independently establish that the cited text actually supports the architectural decision. That remains a human-review responsibility.

For whole-source citations, require at least one claim, all registered claims graded V or P, and a clear warning in the documentation that this does not certify the completeness of the registered source coverage.

Where a decision depends on a particular passage, claim-level citation is preferable.

### C. Distinguish citations from source mentions

A decision may mention a source without relying on that source as evidence.

For example, documenting that an inaccessible standard exists is different from claiming that its requirements justify a particular ontology classification.

The checker must distinguish a declared source citation from a non-evidentiary mention, using an explicit convention.

The existing proposed exception mechanism can handle genuinely necessary citations to inadequately verified material. However, a source mentioned solely as background should not automatically be treated as evidence supporting the decision.

An exception must never silently convert an unread source into verified evidence.

Preserve the original verification grade and identify the exception's reason, scope, approver, and decision file.

## 3. CI and source-adequacy acceptance

I approve the distinction between the source register's validity and the adequacy of citations in decision files.

Adequate citation

A citation references a claim graded V or P, or a source meeting the approved whole-source rule.

Approved exception

A citation is individually excused, with its reason, decision-file location and authorized reviewer recorded.

Inadequate citation

A citation depends on inadequately verified evidence and has no applicable approved exception. Checks fails.

No citations to evaluate

The check passes vacuously but reports zero citations evaluated. This must not be presented as evidence that the project's decisions are adequately sourced.

The last distinction is important. P4 cannot discover a source that a decision relies upon but fails to cite. The human domain-review process must address citation completeness.

I also approve detecting stale exceptions when the citation is removed or its verification status is upgraded sufficiently to eliminate the exception's need.

## 4. Reviewers and authority

The proposed use of `config/review.yaml` is appropriate and reuses the reviewer framework already accepted under P5.

The architect should normally approve source-adequacy exceptions because these involve decisions about the sufficiency of evidence for an architectural conclusion.

A project may delegate that authority explicitly to another reviewer kind. Such delegation must be recorded; adding a reviewer kind alone should not confer approval authority.

A rights reviewer may assess permitted use of source material, but that is distinct from the source-adequacy judgment.

No new BFO/CCO class or object property is necessary for this functionality.

## 5. Testing and release

I approve the proposed read-only measurement against BCO's 63-entry register.

It should report the entries processed, invalid register data, adequate citations, inadequate citations and approved exceptions, without modifying BCO's source files.

This is particularly useful because it tests the new tool against a real project that developed the underlying practice.

I require the existing proposed negative and mutation tests, plus regression coverage for stable claim identifiers, missing claims in whole-source citations, stale exceptions, and decision files containing references that are mentions rather than evidentiary citations.

No additional BPO ontology corrections are required for P4.

## 6. Implementation authorization

P4 architecture

Accepted

Register and verification grades

Accepted

Source adequacy CI gate

Accepted

BCO read-only evaluation

Accepted

v0.5.0 release

Authorized after tests pass

The design is sufficiently mature to proceed. The refinements above do not require another full architectural review.

The Template Team may implement P4 under this decision, run the required tests, complete its BCO compatibility measurement, and prepare v0.5.0 using the established release process.

Do not expand the release to include P7, P8, P6, or additional source-governance features.

### Final architectural recommendation

Accept P4. It fills a genuine evidence-governance gap without overstating what automated validation can establish.

P4 will make the Ontology Template better at ensuring that architectural decisions have traceable, reviewed evidence. It will not pretend that a machine can determine whether a source is credible or whether an ontological interpretation is correct.

That is the appropriate division of responsibility.

Proceed with implementation of v0.5.0, incorporating the three refinements, then push
