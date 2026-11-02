<!-- Fallback for a missing/damaged plan Section H. Current reporting-format.md always
     governs; preserve compatible project framing from an intact older Section H.
     Keep this report shape aligned with test-plan-create's template Section H.
     English structural labels/status tokens below support validation. Write narrative
     content and the human DOCX in the user's language unless another was requested. -->

# Fallback Report Template

Initialize `wp-update-report.md` in a fresh, storage-gated `report-<YYYY-MM-DD>[-N]/`
directory before testing. Pre-populate every plan ID as NOT RUN, save progress after
each check, and finalize before generating the concise illustrated DOCX. This is the
technical Markdown shape; do not copy its full matrix or technical issue schema into
the human DOCX. Use `references/reporting-format.md` for both presentation layers.

```markdown
# Report: <Project Name> — <YYYY-MM-DD HH:MM timezone>

**Mode:** <normal | before | after>
**Environment:** <tested base URL>
**Update:** <declared changes / planned changes for before; verified from → to or unknown>
**Test-plan reference:** <path>, SHA256 <hash>, last discovery <date>
**Baseline reference:** <None — reason | source checkpoint path and SHA256>
**Scope executed:** <full | smoke | targeted: tags or explicit retest IDs>
**Run state:** <run-state.json | unavailable — reason>
**Continuation / retest source:** <None | prior run ID/path and original observation dates>
**Visual review:** <visual-review/index.html | not produced — reason>
**Scope excluded:** <IDs and specific reasons, including explicit user exclusions>
**Run completeness:** <Complete | Incomplete>
**Unreached selected IDs:** <None | IDs and reasons>
**DOCX generated:** <yes | no — capability unavailable | no — export failed: reason>

## Summary
<Brief outcome, tested coverage, principal issues, and limitations. Complete means
every selected ID was assessed; it does not mean every check passed.>

## Result counts
Full plan: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
Selected scope: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
Issue severity: Critical: <n> · High: <n> · Medium: <n> · Low: <n>

## Capabilities and limitations
<Capability | Available / unavailable / limited | Affected IDs | Consequence>

## Update and baseline comparison
<Declared changes and verified component/version/activation differences. For after,
compare only compatible tests/captures; identify missing baseline evidence, changed
requirements, and dynamic-content differences. For normal/before, state not applicable.>

## Full result matrix
| Test ID | Lifecycle | Selected for this run's scope? | Status | Actual observation | Evidence reference | Reason |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
<Every plan ID. Yes/full, Yes/smoke, Yes/smoke-dependency, Yes/targeted-tagged, Yes/targeted-dependency,
or No. Unselected and REMOVED rows stay NOT RUN with a reason.>

## Attempts
<For each attempted ID: ordered attempt number, time, status, concrete observation,
and evidence. Keep failures alongside successful retries; any valid FAIL wins.>

## Prioritized issue index
<Issue ID | Title | Severity | Related test ID(s) | Cause classification | Role required>

## Confirmed issues
<One section per issue using reporting-format.md's technical schema: severity and
reason, related IDs, classification, impact, exact location, reproduction, expected
versus actual, actual screenshots or why unavailable, matched before/after evidence
if available, cause confidence and evidence, proposed remediation or diagnostics,
responsible role, and observable verification criteria.>

## Blocked checks
<Test ID and specific blocker; these are not confirmed defects.>

## Unresolved preconditions / open questions
<Plan gaps, unclear expected results, unresolved access or comparison questions.>

## Cleanup status
<What was restored; exact remaining items and how to finish cleanup.>

## Remaining work
<Prioritized follow-up, unverified areas, future rerun IDs.>

## Conclusion
<Qualified to actual selected coverage and remaining limitations.>
```

The DOCX contains a short overview, a compact issue list when useful, and one simple
illustrated section per issue: what/where, expected versus actual, impact, screenshot
(paired before/after when valid), and next action with owner. Include a short
limitations/cleanup note and a pointer to the technical report. Use actual images or
state why none exists. Keep code, raw logs, the full matrix, and detailed diagnostics
in the Markdown/evidence bundle. If there are no issues, deliver a short scoped
summary; do not manufacture issue sections or pad it with passing-test details.
