<!--
  FALLBACK report template for /wp-checkpoint:test.

  The primary source of truth for the report's shape is Section H ("Future Report Template") inside
  the project's own testing-after-update.md — use that whenever it's present and intact, so the report
  stays tied to the specific document you just executed. This skill's own current reporting
  requirements (references/reporting-format.md, references/storage-preflight.md) always take
  precedence over an older Section H, though — reuse its project-specific framing, never let it omit a
  currently-required field. Use *this* file only when Section H is missing or badly damaged (not merely
  old) in the project's document, and say so explicitly in the report ("Section H was missing from
  testing-after-update.md; this report used the wp-checkpoint:test skill's fallback template — consider
  restoring Section H via /wp-checkpoint:test-plan-create").

  This mirrors Section H of assets/testing-after-update-template.md in this plugin's test-plan-create
  skill folder. If you ever edit one, edit the other the same way. Both assume you've already read
  references/storage-preflight.md (output base directory, the public-exposure gate) and
  references/reporting-format.md (the result matrix, the per-issue schema, Markdown/DOCX consistency,
  DOCX scannability) in full. This template is the shape to fill in; those files are the rulebook
  behind it.
-->

# Fallback Report Template

Initialize this as `wp-update-report.md` inside `report-<YYYY-MM-DD>[-N]/` at the output base directory
captured at invocation (numeric suffix for an additional run the same date — never overwrite a prior
run), right after passing the public-exposure gate in `references/storage-preflight.md` and before
execution starts (SKILL.md Step 3) — Run completeness: Incomplete, full result matrix pre-populated.
Update it progressively through execution (Step 4), then finalize it (Step 6): generate
`wp-update-report.docx` from this same finalized content using the environment's available
DOCX-authoring capability — never a custom exporter — or state plainly, here and in chat, whether the
capability was unavailable or the export itself failed.

```
## Report: <Project Name> — <YYYY-MM-DD HH:MM> — <what was updated>

**Environment:** <local/live base URL>   **Update:** <component(s), from → to version(s)>
**Test-plan reference:** <path to testing-after-update.md>, last discovery <date>
**Scope executed:** <full | smoke | targeted: list>   **Scope excluded:** <list + reasons>
**Run completeness:** <Complete — every selected test ID reached a terminal status | Incomplete — list which IDs were never reached and why>
**DOCX generated:** <yes | no — unavailable, or export failed; say which>

### Result counts
Full plan: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
Selected scope: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
(both reconciled with the full result matrix below; "Selected scope" counts only rows with Selected: Yes)

### Full result matrix
<table: Test ID | Selected for this run's scope? | Status | Actual observation | Evidence reference |
Reason (if BLOCKED/NOT RUN/NOT APPLICABLE/excluded) — every test ID in the PLAN, selected and
deliberately-unselected alike. An unselected ID is Status: NOT RUN, Selected: No, with the scope
reason — never NOT APPLICABLE, which is reserved for a genuine project/environment non-applicability.>

### Prioritized issue index
<table: Issue ID | Title | Severity | Related test ID(s) | Cause classification | Role required —
sorted Critical → High → Medium → Low>

### Confirmed issues
<one subsection per issue, in the exact per-issue schema from references/reporting-format.md:
severity + reasoning, related test ID(s), issue classification, what's wrong and who it affects,
exact affected location, reproduction steps and expected vs. actual, evidence (screenshot/log-excerpt
references), cause classification with supporting evidence (or Unknown + diagnostic next steps),
numbered manual remediation steps (never described as applied or verified), role required, and
verification criteria naming which test ID(s) to rerun.>

### Blocked checks
(test ID + specific reason — kept separate from confirmed issues, never blended)

### Unresolved preconditions / open questions
(anything from Section E not met, or an open question from Section C/I still unresolved — kept
separate from confirmed issues, never blended)

### Cleanup status
(what was restored; what, if anything, remains to be cleaned up manually)

### Remaining work
(follow-up fixes needed, a future full run, a missing precondition to unblock, etc.)

### Conclusion
(qualified to the scope actually executed — "no issues found" must name the tested scope and any
unresolved limitations, never stated as an unqualified clean bill of health)
```
