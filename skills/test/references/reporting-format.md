# Reporting Format

Read before initializing the report. The Markdown is the complete technical record;
the DOCX explains the findings simply, with pictures, for the person deciding what to
fix. They share facts and issue IDs, not a requirement to duplicate every paragraph.

## Output and language

Resolve `report_output_directory` with `storage-preflight.md`; do not recompute the
fixed invocation directory. Create a fresh `report-<YYYY-MM-DD>[-N]/` using the user's
timezone/date. If the name exists, increment `-2`, `-3`, and so on. New runs and retests never reuse an earlier run's directory. Explicit continuation
may update only the exact verified OPEN bundle under `run-state.md`; finalized history
and completed checkpoints stay immutable.

```text
report-<YYYY-MM-DD>[-N]/
  wp-update-report.md       complete technical record
  wp-update-report.docx     concise illustrated human report, when supported
  screenshots/              real captured evidence
  log-excerpt.txt           relevant attributed excerpts, or an honest no-evidence note
  checkpoint.json          before mode only
  selection.json           deterministic selected IDs/order/reasons, when available
  context.json             current non-secret identity/context fingerprint
  run-state.json           journal/results/cleanup for safe continuation, when available
  visual-review/index.html optional offline before/after slider and highlighted differences
```

After mode may use `screenshots/before/` and `screenshots/after/` for the paired images.
Copy selected before evidence into the new bundle without changing the source; record
its source checkpoint and hashes. Gate every actual destination and file type before
writing real content, including JSON and nested screenshot directories. No raw logs,
secrets, or unnecessary personal data belong in the bundle.

Use the user's requested report language, otherwise the conversation language. Keep
the technical Markdown structural labels shown in the fallback template, status
tokens, IDs, and selection values in English for validation. Translate explanations
and the human DOCX; preserve exact UI labels and code/config identifiers where needed.

## Progressive technical record

Initialize the saved Markdown immediately after the storage gate and before tests.
Include Mode (`normal`, `before`, or `after`), environment, declared/planned update,
plan path and SHA256, Baseline reference (path and checkpoint SHA256, or None with
reason), scope/exclusions, capabilities, and **Run completeness: Incomplete**. Populate
the full matrix from every plan ID with NOT RUN, including REMOVED historical IDs.

As each check is assessed, save its attempts, final status, observation, evidence, and
cleanup. This preserves a legible partial report if the run is interrupted. Before
mode also updates its incomplete checkpoint according to `before-after.md`. When a
run ledger is available, write its start journal before actions and record actual
outcomes/evidence/cleanup afterward. Reconcile its selected IDs, attempts and statuses
with this report. Resume retains earlier observation dates; fresh retests name the old
run as history while reporting only their own new attempts. Never erase an old failure.

An optional visual HTML review links from the technical report. Preserve raw captures
and identify highlighted differences as derived aids. Show only issue-relevant images
in the DOCX; unchanged comparisons do not need another issue section.

Required final Markdown sections are: summary, result counts, capabilities/limitations,
update and baseline comparison, full result matrix, attempts, prioritized issue index,
confirmed issues, blocked checks, unresolved preconditions/open questions, cleanup,
remaining work, and a conclusion qualified to what was actually verified. Comparison
gaps and unavailable evidence are limitations, not automatically defects.

Use compatible project framing from plan Section H. These current requirements take
precedence over an older intact Section H, including the shorter human DOCX. If Section
H is missing or damaged, use `assets/report-template-fallback.md` and record that fact.
Never rewrite the canonical plan during testing.

## Matrix, counts, and completeness

Use these exact table headers in the technical Markdown:

| Test ID | Lifecycle | Selected for this run's scope? | Status | Actual observation | Evidence reference | Reason |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |

- **Test ID / Lifecycle:** every plan ID exactly once; ACTIVE or REMOVED. Lifecycle is
  separate from result status. REMOVED rows are unselected NOT RUN, with removal date
  and reason, never attempted or silently deleted.
- **Selected for this run's scope?:** `Yes/full`, `Yes/smoke`, `Yes/smoke-dependency`,
  `Yes/targeted-tagged`, `Yes/targeted-dependency`, or `No`. Use the shared selection
  algorithm and explain prerequisite selection or explicit exclusions in Reason.
- **Status:** NOT RUN, PASS, FAIL, BLOCKED, or NOT APPLICABLE. Unselected means NOT RUN,
  not NOT APPLICABLE. Any valid failing attempt makes the aggregate FAIL. Do not hide
  an intermittent failure behind the last passing retry.
- **Actual observation:** concrete observed behavior, not merely "matched expected";
  use an em dash for an unselected ID.
- **Evidence reference:** relative file paths inside this bundle, with useful captions
  or log line references; an em dash when none applies. Never reference nonexistent
  evidence or use `..`/absolute paths to escape the bundle. Baseline metadata references
  are separate provenance, not evidence-file links.
- **Reason:** required for NOT RUN, BLOCKED, NOT APPLICABLE, and every unselected row.
  Name the actual blocker, environment non-applicability, scope exclusion, or removal.

Preserve these machine-readable tally lines; compute them from the matrix, not a
separate running count:

```text
Full plan: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
Selected scope: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
Issue severity: Critical: <n> · High: <n> · Medium: <n> · Low: <n>
```

Full plan counts all rows; Selected scope counts only Yes rows. Severity counts unique
issue IDs, not failed tests: one issue may affect several tests. Reconcile all tallies
with the actual matrix/index and investigate disagreements rather than assuming which
side is correct.

`Run completeness: Complete` means every selected ID reached PASS/FAIL/BLOCKED/NOT
APPLICABLE. `Incomplete` means a selected ID remains NOT RUN; list those IDs and why.
Unselected history or exclusions do not make the run incomplete. Neither Complete nor
zero failures means all functionality was verified: say, for example, "12 passed;
3 could not be checked" and retain scope limits in the DOCX and chat.

## Technical issue record

Assign each observed issue a run-local `ISSUE-<NNN>`. Sort the issue index and issue
sections Critical → High → Medium → Low. Keep blocked checks and open questions out
of confirmed issues. Each issue in Markdown includes:

1. **Title, severity and reasoning, related test IDs, issue classification.** Use
   shared conventions; confirmed regression requires comparable prior passing evidence.
2. **What is wrong and who it affects.** Explain practical impact, not just an error code.
3. **Where.** Verified URL/admin location/component and useful verified source location.
4. **Reproduction steps; expected versus actual.** Preserve actual UI/control names.
5. **Evidence.** Actual screenshot(s) of the failure or visible consequence, each with
   a caption, or the specific reason a meaningful screenshot could not be obtained.
   Include relevant log/request/state evidence. In after mode include matched before
   and after images when available, with provenance and any comparison limitations.
6. **Cause: Confirmed / Suspected / Unknown.** Give the evidence supporting that level;
   version correlation alone is not confirmation.
7. **Proposed action.** Numbered manual remediation only when evidence supports it;
   otherwise concrete diagnostic next steps. Never imply the fix was applied.
8. **Role required.** WordPress Administrator, Developer, Hosting Administrator, or
   the relevant combination, as defined by shared conventions.
9. **How to verify.** Observable success criteria and test IDs for the next run.

Use "Not established" with the missing fact instead of inventing a location, cause,
or repair recipe. Keep every valid retry outcome in the Attempts section with ordered
attempt number, timestamp, status, observation, and evidence.

## Concise illustrated DOCX

Generate this from the finalized Markdown facts with the environment's available
DOCX-authoring capability. Do not build or maintain a custom exporter script/library
integration for this plugin. Follow the authoring capability's rendering/inspection
workflow when available.

The reader should understand the problem and next action without reading code:

- Start with a short overview: what changed (or before-update state), tested scope,
  issue count/severity, outcome, and material limits. Include a compact issue list only
  when it helps navigate several findings.
- Give **each issue one compact section** with its ID and simple title; affected
  page/feature; what should happen versus what happened; practical impact; a real
  captioned screenshot; and the next action and responsible role. Explain technical
  terms only when necessary. Preserve uncertainty about cause or required diagnosis.
- When comparable before/after images exist, place the pair together with clear labels
  and the visible difference described. Otherwise show the actual available image and
  state that before evidence is unavailable. If no meaningful screenshot is available,
  say why and summarize the actual evidence in plain language. Do not fabricate images
  or use an unrelated screen to fill the space.
- Keep code snippets, raw logs, the full test matrix, detailed attempts, and deep
  diagnostics in Markdown/evidence. Point to that technical report for those details.
- End with a short limitations/remaining-work/cleanup note. A no-issue run needs only a
  brief scoped summary and limitations, not pages of passing-test descriptions.

The DOCX must include every confirmed issue, its correct severity, material impact,
proposed action/owner, and material limitations. Condensation must not hide a blocker,
pending cleanup, uncertainty, or incomplete coverage. It need not repeat technical
field names or detailed prose. Keep images readable, captions attached to images,
headings with their content, and avoid blank pages or clipped tables.

## Failure reporting and read-back

Distinguish **capability unavailable** (no authoring capability) from **export failed**
(available capability attempted but errored, timed out, or produced unusable output).
State which happened both at the top of Markdown and in chat. Retain the Markdown;
never claim a broken/partial DOCX is a finished deliverable. A user-requested omission
is a third case, "not requested," not a capability failure.

Before reporting completion, reopen saved Markdown, reconcile matrix/counts, and check
that every evidence file exists inside this run's bundle. Open/inspect the DOCX for
factual agreement and readable layout, or state the export limitation. For before,
validate checkpoint identities, attempts, hashes, and consistency with Markdown before
finalizing it. Where the plugin's validator is available, resolve its absolute path
from this plugin installation (never from the WordPress working directory), then run
`python <plugin-root>/scripts/validate.py report <report.md> --plan <plan.md>` and,
for before mode, `python <plugin-root>/scripts/validate.py checkpoint <checkpoint.json>`.
An adjacent run-state.json is automatically reconciled with the report; `--state`
can identify it explicitly. Do not delete a conflicting ledger to make validation pass.
These are read-only checks. If Python/the helper is unavailable, perform equivalent
checks and state that limitation. Do not invent validation success.

Keep chat brief: mode/scope, selected counts and completeness, material limitations,
Markdown/DOCX/evidence paths, and before checkpoint or after baseline reference as
applicable. Detailed findings stay in the files.
