# Items 5 and 6: the architect's disposition

**Date:** 2026-11-06. **Decision:** 32 (`docs/template/DECISIONS.md`). In answer to
`2026-11-06-items-5-6-design.md` section 5. The text is headed "Architectural Decision 30";
the template's record already numbers a decision 30 (WP6 closed, 2026-11-05), so it is
recorded as 32, its heading kept as written. The text below the rule is the architect's,
verbatim, as pasted; its SHA-256 is
`3e765528e2a727299e3d179bdf2ee73ccbd989a37a5faedae6e57916a33ec5df`.

---

# Ontology Template — Architectural Decision 30

November 6, 2026 | Items 5 and 6 | Proposed v0.3.0

I approve the design for implementation, with a few targeted amendments. I also approve pushing `f321ed0` for review.

This work directly addresses weaknesses demonstrated by the BPO experiment: human finding classifications were not captured in the register, transitive dependencies were not reproducibly pinned, and the template could not reliably report changes to project-specific validation shapes.

We should implement these improvements without reopening WP6 or expanding the scope of v0.3.0.

## Decisions on the five questions

| # | Question                                      | Decision                                               |
| - | --------------------------------------------- | ------------------------------------------------------ |
| 1 | Finding-classification fields and rules       | Approve with amendments                                |
| 2 | Keep version 1 registers valid                | Approve                                                |
| 3 | Implement P5's shared reviewer vocabulary now | Approve                                                |
| 4 | Use uv to generate the dependency lock        | Approve                                                |
| 5 | Which files should be seeded?                 | Approve all proposed files, including upstream sources |

## 1. Finding classification — approved with amendments

The separation between `validity`, `origin`, and `resolution` is correct. These represent distinct questions that must not be conflated.

I approve the proposed values with one addition to `origin`.

| Field           | Approved values                                          |
| --------------- | -------------------------------------------------------- |
| `validity`      | `real`, `false-alarm`, `unsure`                          |
| `origin`        | `project`, `upstream`, `template`, `unknown`             |
| `resolution`    | `accepted`, `deferred`, `reported`, `not-a-defect`       |
| `classified_by` | Reviewer identity and capacity from `config/review.yaml` |

Why add `unknown`? During WP6, some genuine findings required investigation before their source could be identified. Forcing a reviewer to choose project, upstream, or template prematurely would create false provenance.

`unknown` must require `validity: unsure`, `resolution: deferred`, and an explicit review date. It is not a permanent way to avoid assigning responsibility.

I approve the proposed consistency rules, with these clarifications:

- `accepted` requires `validity: real`; `not-a-defect` requires `validity: false-alarm`.
- `false-alarm` may be `reported` when it represents a known template or upstream checker defect.
- `unsure` must be `deferred`, with a review date.
- `origin: upstream` requires a recorded upstream source. However, merely citing an upstream IRI does not necessarily mean the upstream ontology caused the defect, so the reverse implication should not be automatic.
- `reported` requires a traceable reference.
- `classified_by` must identify a reviewer and their declared review capacity.

The most important rule remains unchanged: human classification must not determine the automated finding verdict.

An invalid register may fail schema validation, but a finding's validity or resolution classification must not independently change whether the underlying ontology check finds that issue.

## 2. Preserve version 1 registers — approved

I approve the proposed migration strategy.

Register v1 — backward compatible

Existing registers remain valid. Missing classifications are reported as unclassified, not invented or treated as ontology failures.

Register v2 — complete classification required

All four fields are required, consistency rules are enforced, and missing or placeholder judgments fail register validation.

No tool should populate `real`, `false-alarm`, or `unsure` automatically.

The decision to classify a finding must come from an identified reviewer. A migration tool may prepare entries for review but must not impersonate human judgment.

I also support retaining the current practice of removing corrected findings from the active register, provided Git history preserves their prior disposition. A future state-comparison tool can reconstruct the history.

## 3. P5 reviewer kinds — approved

Approve `config/review.yaml` with the four proposed kinds:

`ontologist`, `domain-practitioner`, `architect`, and `rights-reviewer`.

Projects may extend this vocabulary, but the four template-defined kinds should remain available.

The reviewer must record the capacity in which the judgment was made, especially when the same person acts in more than one capacity.

The `rights-reviewer` designation records a rights-related review. It must not imply legal approval or professional legal qualification unless such authority has separately been established.

Do not implement P5's stage-gating rules yet. Those belong with item 12, where the human domain-review process will be formally defined.

This avoids implementing half of a review gate before its obligations are agreed.

## 4. Dependency locking — approve uv

I approve uv as the lock generator only, using the proposed universal-resolution and hash-generation approach.

The official uv documentation confirms that universal resolution can retain platform-specific dependency markers in a single requirements file. pip also supports hash-enforced installation and requires all dependencies to be explicitly pinned and hashed in that mode.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.astral.sh\&sz=32)

uv+1



The architecture is appropriate:

`requirements-dev.txt`

Direct dependencies

Pinned uv generator

Universal dependency resolution and hashes

`requirements-lock.txt`

Direct and transitive dependencies

pip installation in CI and development

Hash-verified, reproducible dependency versions

I require three safeguards before release:

1. Cross-platform verification: Test fresh installations on Linux, Windows, and macOS using the same lock. Do not assume universal resolution alone proves every supported environment installs successfully.
2. Bootstrap integrity: Pin the uv generator version and verify the appropriate distribution checksum. Handle pip's bootstrap version explicitly; listing pip in the dependency lock does not by itself control which pip version initiates installation.
3. Dependency security: Scan all locked distributions and distinguish a successful scan with no advisories from a scan that could not run.

I approve pinning the Release workflow to `ubuntu-24.04`.

I also accept recording Python's patch version rather than pinning it, provided the evaluation records the exact interpreter used. Python 3.12 must remain the declared compatibility baseline.

## 5. Seeded files — approve all proposed components

Yes, include `config.upstream-sources` in the seeded set.

This is particularly important because WP6 identified an actual CCO dependency-version discrepancy. A future project must be able to see when the template's BFO or CCO baseline differs from its own.

| Component                                 | Decision                     |
| ----------------------------------------- | ---------------------------- |
| Wellformedness shapes                     | Seeded                       |
| Realist shapes                            | Seeded                       |
| SKOS shapes                               | Seeded                       |
| Three corresponding negative-fixture sets | Seeded                       |
| Annotation profile config                 | Seeded                       |
| Naming config                             | Seeded                       |
| Reasoning config                          | Seeded                       |
| Upstream sources config                   | Seeded                       |
| Generated annotation-profile shapes       | Remain generated; not seeded |

The `seeded` concept is correctly distinguished from `owned` because projects are expected to configure and extend seeded files.

I approve using the same namespace-rewrite code that `init` uses for comparisons. The comparison must distinguish local customization, template changes, and changes on both sides.

One additional safeguard: a change to an upstream BFO/CCO pin must be reported as a dependency change requiring review, never an automatic upgrade instruction.

A project's existing pin remains authoritative until the project explicitly adopts a new one. Changes to upstream versions can affect ontology semantics, and the report should expose that possibility rather than silently normalizing it.

If the historical template checkout is unavailable, the tool must report that the comparison could not be performed. It must not report the file as unchanged.

## 6. Implementation and release authorization

I approve the proposed order:

First — P-A1 dependency lock

Implement and test the generator, lock verification, and CI installation changes.

Second — P-A3 seeded-file drift reporting

Implement the shared rewrite logic, manifest information, and three-way comparison.

Third — P-A7 register classification

Implement the approved schema, reviewer vocabulary, migration behavior, reports, and tests.

Release — v0.3.0

Run the complete suite and release checklist, including negative tests, mutation tests, and compatibility verification.

These three work packages constitute the approved v0.3.0 scope. Do not add other BPOT findings to the release without identifying a release-blocking dependency.

## 7. Should `f321ed0` be pushed?

Yes. Push `f321ed0` for review.

The design has now received architectural dispositions on all five questions. Record the amendments in a follow-up design-decision commit, then proceed with implementation through the normal review process.

The reported 453 passing tests are good evidence that writing the design did not disturb existing behavior, but the three new capabilities will need their own implementation and regression evidence.

### Final architectural direction

I approve items 5 and 6 for v0.3.0 because they strengthen the two capabilities that the BPO experiment demonstrated we need most:

Trustworthy judgments: The register distinguishes what a check found, what a human concluded, and who is responsible for the resulting decision.

Trustworthy reproducibility: The template can reconstruct its dependencies and distinguish actual template changes from deliberate project customization.

These improvements should make future ontology evaluations more reliable without creating new BFO/CCO modeling commitments or weakening the template's checks.

Proceed with implementation of v0.3.0 under the five decisions above. WP6 remains closed; this is post-WP6 template improvement work.
