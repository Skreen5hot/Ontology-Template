# The architect's acceptance of WP3 and direction for WP4 (2026-10-28)

Recorded verbatim; decision 14 in `docs/template/DECISIONS.md` gives the digest of the text
below the rule and its effect.

---

**WP3 is accepted as complete. Proceed with WP4 (T8–T12, T23).**

The reported implementation and test results demonstrate that the Ontology Template now applies consistent rules across validation and publication and provides transparent reporting of accepted findings and conflicting ontology content.

The following results support acceptance:

**1. Validation and publication consistency (T6)**

The validator now enforces the applicable term and module requirements, including property definitions, annotation cardinality, literal values, module headers, and duplicate declarations.

The site no longer independently rejects ontology content that the validation framework permits under an approved finding. Instead, it publishes the content with the relevant quality finding visible.

Site infrastructure and input-integrity failures remain independently enforced, and site checks now execute during CI.

**2. Transparent representation of conflicts (T7)**

Conflicting definitions and labels are published with their originating modules identified. The site does not silently select one version.

Accepted findings remain visible, including their reasons, owners, and review dates.

The BPO test demonstrated that 51 conflicting definitions and six conflicting labels are represented and reported rather than concealed.

This demonstrates improved visibility and governance of ontology quality issues. It does not constitute approval or resolution of those conflicts.

**3. Regression and performance evidence**

The reported 365 passing tests, detection of all 23 deliberate breakages, and execution time of 7 minutes 46 seconds within the 10-minute budget support WP3 acceptance.

The discovery and correction of the additional concept-label publication defect also demonstrate the value of testing against a larger ontology.

**4. Outstanding verification**

The explorer's actual browser-rendered display of conflicting versions and accepted findings has not yet been independently exercised.

Record a browser-level verification as an outstanding follow-up. Confirm that the rendered explorer presents every conflicting variant, its source module, and applicable findings correctly. This does not block proceeding to WP4.

**5. BPO governance remains separate**

The existing BPO findings remain under BPO ownership. Their appearance in a findings register or on a published site does not establish that they are semantically correct or formally approved.

Continue preserving the distinction between accepted findings, unresolved ontology issues, and upstream BFO/CCO findings.

**6. Proceed with WP4**

WP4 must address the remaining detection gaps in T8–T12 and T23.

For each gap, demonstrate that the template can detect the relevant issue, report it accurately, support an appropriate disposition, and verify that corrective actions prevent recurrence.

Begin coordination with Legal immediately for T9. Do not independently establish legal interpretations or licensing permissions through implementation assumptions.

**7. WP6 obligations remain unchanged**

Retain the outstanding BPO-scale Checks and Reasoning performance measurements, formal disposition of BPO findings, and final assessment of whether the resulting ontology has demonstrably improved.

The final BPO assessment must distinguish improvements in the Ontology Template from improvements in BPO's ontological content.

**WP3 is accepted. WP4 is authorized. Initiate the T9 Legal request now.**

The governing objective remains to establish an auditable, repeatable development process that demonstrably improves ontology quality.
