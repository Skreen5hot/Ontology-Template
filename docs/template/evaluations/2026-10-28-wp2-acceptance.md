# The architect's acceptance of WP2 and direction for WP3 (2026-10-28)

Recorded verbatim; decision 13 in `docs/template/DECISIONS.md` gives the digest of the text
below the rule and its effect.

---

**WP2 is accepted as complete. Proceed with WP3.**

The results demonstrate meaningful improvements in the Ontology Template's ability to identify, document, monitor, and enforce decisions concerning individual validation findings.

In particular, the finding-specific register, shared exception handling, complete execution of checks, full reporting, and detection of changed findings address important weaknesses identified during the BPO migration experiment.

The successful regression tests, deliberate failure tests, and discovery and correction of the undeclared-file validation gap provide supporting evidence.

**The following decisions apply:**

**1. WP2 acceptance**

Accept WP2 based on the reported functional tests, regression results, and template performance measurements.

Record the BPO-scale performance measurements as outstanding verification requirements. Do not represent the estimated 20-minute execution time as a measured result.

**2. BPO finding ownership**

The 3,716 findings identified during the BPO trial remain subject to BPO governance.

The template's ability to register and accept individual findings does not establish that those findings are ontologically appropriate or should be accepted.

The BPO team retains authority to evaluate, resolve, or formally accept BPO-specific findings. Upstream BFO/CCO findings must remain distinguishable from BPO-specific findings.

**3. Performance verification**

Defer BPO-scale execution measurements to WP6, using the BPO team's private repository and GitHub Actions environment.

Do not introduce private BPO content, credentials, or potentially sensitive execution logs into public template CI.

WP6 must establish actual execution times for the complete BPO Checks and Reasoning jobs under documented runner conditions and compare them with the approved performance budgets.

**4. Proceed with WP3**

WP3 must establish consistent, enforceable requirements between ontology validation and site publication.

The template must not allow an ontology to pass validation only to fail during publication because of requirements the validator did not enforce.

Likewise, the published site must not conceal conflicting definitions or other material ontology quality findings.

Provide regression tests demonstrating that publication requirements are validated in advance and that relevant inconsistencies are detected and reported.

**5. Preserve the experiment's central objective**

The purpose of the Ontology Template is to improve ontology quality through a repeatable and auditable development process.

Successful execution of tests demonstrates framework functionality. The final BPO evaluation must establish whether using the framework produces measurable improvements in the ontology itself.

**Proceed with WP3. No additional BPO timing exercise is required before starting that work package.**

Maintain the unresolved performance measurements and BPO-specific findings in the appropriate tracking records for WP6 and the final evaluation.
