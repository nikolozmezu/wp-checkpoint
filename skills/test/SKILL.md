---
name: test
description: Executes the project's existing testing-after-update.md runbook (written by /wp-checkpoint:test-plan-create) after a WordPress/plugin/theme/PHP/environment update, and produces an actionable, evidence-based report — PASS/FAIL/BLOCKED/NOT APPLICABLE per test ID, plus a structured Markdown+DOCX issue report with screenshots and log excerpts, written to a report-<date>/ directory. Requires testing-after-update.md to already exist. Invoke explicitly after applying an update, to verify nothing broke.
disable-model-invocation: true
argument-hint: "[full|smoke|targeted]"
---

# /wp-checkpoint:test

You execute **this project's existing** `testing-after-update.md` and produce an actionable report — for both Claude and a human who may fix the issues manually, without having read this conversation. You do not invent a checklist, and you do not write `testing-after-update.md` yourself — that document only ever comes from `/wp-checkpoint:test-plan-create`.

Read this whole file before acting, then read `references/shared-conventions.md`, `references/storage-preflight.md`, and `references/reporting-format.md` in full before Step 3, and `references/execution-and-evidence.md` in full before Step 4. `shared-conventions.md` defines the test-ID format, priorities, the five statuses, evidence-source labels, severity scale, issue classification, issue IDs, cause classification, and role-required labels you must use consistently in every result and finding; `storage-preflight.md` owns where either skill writes site-specific output and the public-exposure gate that must pass before any of it is written; `reporting-format.md` holds the complete, non-negotiable report spec (output directory layout, report initialization and progressive updates, the result matrix, the per-issue schema, Markdown/DOCX consistency, DOCX scannability) that Step 3 starts acting on and Step 6 finalizes; `execution-and-evidence.md` holds the operational detail (execution order, isolation checks, evidence attribution, retry handling) behind the rules in Step 4. None of these is optional background — the statuses, classifications, and report shape only work if you're using the exact vocabulary and structure they define.

## Step 1 — Capture the output base, then read the document

Before anything else — before locating the plan, before any other directory navigation — capture the **output base directory**: the directory this session was actually working in at the moment this skill was invoked. Fix it now and don't recompute it later; see `references/storage-preflight.md` for the full rule, including why this is kept distinct from the WordPress root, the project root, the repository root, and this plugin's own directory. Step 3 uses this exact captured value.

Locate `testing-after-update.md`, in the same order `references/storage-preflight.md` defines:
- **If the user explicitly supplied a path**, that path is authoritative. If a plan exists there, read it from there. **If nothing exists there, stop immediately** with a clear, specific "no plan found at `<that path>`" response — do not fall back to the output base or a fallback search, and do not substitute a different plan you happen to find elsewhere. This skill never creates a plan.
- **Otherwise** (no explicit path given): check for an existing plan already at the captured output base directory; only if that finds nothing, run a validated fallback search (the same common layouts `/wp-checkpoint:test-plan-create`'s Step 1 checks: project root itself, `app/public/`, `web/wp/`, `public_html/`, `htdocs/`, a bare `wp/` subfolder — relevant when the session's working directory sits above the WordPress root). If neither finds it, tell the user that `/wp-checkpoint:test-plan-create` needs to run first, and stop.

Read whatever plan this resolves to in full.

- Either way, do not silently generate a substitute checklist, and do not invoke `/wp-checkpoint:test-plan-create` yourself.
- **Verify it actually fits this run:** does it belong to this project, and is it still sufficiently applicable to the target environment? If parts are outdated or incomplete (a changed URL, a removed feature, a section that's clearly stale), identify the specific gaps. Continue with every check that's still valid, but don't invent requirements to fill the gaps — report them as gaps instead, in the Blocked/excluded part of your report.

## Step 2 — Intake (reuse context; ask only what's missing or changed)

Send one concise message covering whatever of this you don't already know:
- Local website URL.
- Local admin access, or confirmation of an existing authenticated session.
- Live URL, if you need it as a read-only reference for this run.
- What was updated.
- Previous version(s), if available — discover current versions yourself; mark any historical version you can't determine as unknown, don't guess it.
- Desired coverage: **full** (default if unspecified), **smoke**, or **targeted**. If this skill was invoked with an argument (`/wp-checkpoint:test full`, `smoke`, or `targeted`), treat that as the answer and don't ask again; treat any other argument text as a free-form note about what was updated.
- Any additional exclusions or restrictions affecting test data or integrations.

Once the user has invoked this skill and supplied the essentials, proceed — don't ask again for approval to begin. State the selected environment and scope in one line, then start.

**Credential handling** (same rules as discovery): ask only for what you don't already have; never write a password, token, or secret into the report, a command argument, a URL, or any log/explanatory output; never echo credentials back; prefer an existing authenticated session over requesting a password; don't request live admin credentials by default — live stays read-only reference unless the user explicitly asks for more.

## Step 3 — Pass the public-exposure gate, then initialize the report

Do this now, before any check runs or any evidence is collected — not deferred to the reporting step. Read `references/storage-preflight.md` **and** `references/reporting-format.md` in full now if you haven't already; both are needed before execution starts, not just at the end.

Evaluate the gate against the actual destination — this run's new `report-<YYYY-MM-DD>[-N]/` directory under the output base captured at Step 1, and its `screenshots/` subdirectory — not the output base in the abstract, before any real content is written into either: confirm the filesystem-to-URL mapping, test denial of known-existing content (not a nonexistent path) at each relevant path for each relevant file type — Markdown, plain text (`log-excerpt.txt`), `.docx`, and image, per `storage-preflight.md` — using unauthenticated requests, treating a timeout/connection failure/unrelated redirect/unverified mapping as inconclusive rather than reassuring. The gate's own probes may need to create the minimal empty directories first — that's the one narrow exception `storage-preflight.md` describes; no real report, screenshot, or evidence content is written until the gate actually passes. If protection can't be confirmed, stop here and ask the user for a non-public destination — don't guess one, don't fall back to the home directory, and don't edit server configuration to manufacture protection.

Once the gate passes (or both the actual report directory and its `screenshots/` subdirectory are confirmed not web-served, which needs no probe), **initialize `wp-update-report.md`** in the new `report-<date>[-N]/` directory: header fields filled in (environment, update, scope), **Run completeness: Incomplete**, and the full result matrix pre-populated with every test ID from the project's Section D — Selected set per the agreed scope (Yes/smoke, Yes/targeted-tagged, Yes/targeted-dependency, or No with the specific scope reason — never NOT APPLICABLE for an unselected ID), every row's Status starting at NOT RUN. This is the file Step 4 updates as it goes; it's not a draft kept only in memory until Step 6.

Only once this is done do you proceed to Step 4.

## Step 4 — Execute

Follow the document's test IDs, preconditions, role requirements, actions, expected results, evidence requirements, and cleanup instructions exactly. Always include the essential smoke checks (Section D), regardless of scope. For a targeted run, also include the dependencies and cross-feature effects Section D ties to the updated component — never treat the updated piece as isolated without evidence that it actually is. Use the local site for test actions; use live only for the permitted read-only reference. Read `references/execution-and-evidence.md` now for the full execution order and the detail behind every rule in this step.

As each check completes, update its row in `wp-update-report.md`'s result matrix — Status, actual observation, evidence reference — and keep its Cleanup status current. Don't defer all of this to Step 6; Step 6 finalizes the report (the issue write-ups, the prioritized index, the DOCX, the read-back verification), it doesn't originate it.

Perform ordinary, reversible local test actions within the agreed scope: use disposable test content or existing suitable examples, and restore temporary state afterward per each test case's cleanup instructions. If a cleanup step can't be completed — a created item won't delete, a setting won't revert — don't treat it as resolved: note exactly what's left in place, it has to reach the report's Cleanup status section. **Before any action that could reach an external service** (sending a message, placing an order, firing a webhook), confirm the documented test environment actually isolates that integration — a local URL alone does not establish isolation. Never send a real message, execute a real payment, delete shared remote media, or trigger production synchronization through a local clone.

If required access, isolation, tools, or prerequisites are unavailable for a check, mark that test ID **BLOCKED** with the specific reason and continue with every other check that doesn't share the same blocker.

**Never, during execution:**
- Update software.
- Modify application source.
- Fix a defect you discover.
- Silently change configuration outside a documented temporary test step.
- Change a documented expected result to match what you observed (flag the discrepancy in the report instead).
- Rewrite the canonical `testing-after-update.md` — if the plan itself needs fixing, that's `/wp-checkpoint:test-plan-create`'s job, say so in your report.

## Step 5 — Evidence integrity

PASS requires actual execution and direct observation of the expected result — never assign it from static inspection alone. Static code inspection cannot establish that a browser interaction, visual layout, upload workflow, or scheduled job passed. If browser automation is unavailable in this session, say so explicitly for every visual/interactive check in scope — don't claim those passed, and don't quietly drop them without reporting the gap.

Collect whatever evidence is actually available (don't claim a form you didn't produce): screenshots, observed UI behavior, network requests/responses, relevant PHP/WordPress/application log excerpts, resulting content or job state, measurements only where a baseline exists. Attribute a log error to this run only if its timestamp or request falls inside it — don't assume an older entry was caused by the update just because you noticed it today. If a retry passes after an initial failure, keep both results; don't erase the failure.

Don't call a failure a "confirmed regression" without supporting before/after evidence — otherwise it's a "new issue of uncertain origin" (exact definitions and the full severity scale are in `references/shared-conventions.md`).

## Step 6 — Finalize the report

Use the five statuses from `references/shared-conventions.md` consistently: NOT RUN, PASS, FAIL, BLOCKED, NOT APPLICABLE. Account for every test ID in the project's plan, not only this run's selected scope — unexecuted, blocked, unselected, and not-applicable checks are all reported honestly in the result matrix, never silently folded into a pass or silently dropped. An ID the run deliberately didn't select is NOT RUN with Selected: No and the specific scope reason — never NOT APPLICABLE, which is reserved for a genuine project/environment non-applicability.

You already initialized and have been updating `wp-update-report.md` since Step 3 — this step finalizes it, it doesn't originate it. Confirm the **full result matrix** is complete and accurate (every plan test ID present, Selected/Status/observation/evidence/reason all filled in) and that both required result-count tallies — full plan, and selected scope only — reconcile against it exactly.

For each finding, assign it an issue ID (`ISSUE-<NNN>`, per `shared-conventions.md`) and write it using the exact per-issue schema in `reporting-format.md`: title, severity with reasoning, related test ID(s), issue classification, what's wrong and who it's affected, the exact affected URL/admin location/code reference, reproduction steps with expected vs. actual, the evidence collected (screenshot/log-excerpt references), a cause classification (Confirmed/Suspected/Unknown) naming the specific evidence behind it, numbered manual remediation steps **only** where the evidence actually supports one (otherwise concrete diagnostic next steps, never a guessed fix), which role (WordPress Administrator / Developer / Hosting Administrator) is positioned to act on it, and the observable success criteria plus which test ID(s) to rerun to verify a correction. Use the project's actual, verified UI labels, URLs, filenames, field names, and code identifiers exactly as `testing-after-update.md` records them or as you directly confirmed during this run — never invent a menu path, setting name, or code location to fill a gap. Keep the result matrix, confirmed issues, blocked checks, and unresolved preconditions/open questions in separate sections — never blend them, and never describe a proposed fix as if this run had applied or verified it.

Confirm the report's structure as the single source of truth: an executive summary (including this run's completeness — assessed over selected IDs only, Complete or Incomplete, and which selected IDs were never reached if Incomplete), the full result matrix, a prioritized issue index (sorted Critical → High → Medium → Low), the confirmed issues themselves, blocked checks, unresolved preconditions/open questions, cleanup/restoration status, remaining work, and a conclusion qualified to the scope actually executed — "no issues found" must name the tested scope and any unresolved limitations, never stand alone as an unqualified clean bill of health. Never present a partial run as a full pass. **This skill's own current reporting requirements always take precedence over an older but intact Section H of this project's `testing-after-update.md`** — reuse Section H's project-specific framing where it's compatible, but never let an old template omit a field these current rules require. Only if Section H is missing or badly damaged (not merely old), use `assets/report-template-fallback.md` instead and say so explicitly in the report.

Then generate `wp-update-report.docx` from that same finalized Markdown content, using the environment's available DOCX-authoring capability — **never a custom exporter script or application built for this plugin.** The DOCX must contain the same findings, IDs, severities, and recommendations as the Markdown, structured for scanning: a summary, the result matrix, the prioritized issue index, consistent per-issue sections, real numbered-list remediation steps, and captioned screenshots. If the capability is unavailable, or available but the export attempt itself fails, keep the Markdown report and say so plainly — and say which of the two it was — in both the chat reply and a note at the top of `wp-update-report.md`. Don't silently produce only half the deliverable without saying so.

**Before telling the user the run succeeded, read back what was actually saved to disk**: re-open `wp-update-report.md` from its saved path, confirm every screenshot/log-excerpt path it references actually exists, and confirm `wp-update-report.docx` exists and is consistent with the Markdown (or that you've explicitly reported why it doesn't). Don't assume the writes worked because nothing raised an error.

Keep the chat reply itself brief: selected scope, result counts (reconciled with the matrix), run completeness, and the report's file paths (Markdown, DOCX or the specific unavailable/failed note, screenshots folder, log excerpt). The full findings and recommendations live in the files, not restated at length in chat.

## Reference files

- `references/shared-conventions.md` — test ID format, priorities, statuses, evidence-source labels, severity scale, issue classification, issue IDs, cause classification, role-required labels, update-type tags. **Read in full before Step 1.** Identical to the copy in this plugin's `test-plan-create` skill folder.
- `references/storage-preflight.md` — **read in full before Step 3**; the output base directory and the public-exposure gate, shared with `test-plan-create`.
- `references/execution-and-evidence.md` — **read in full before Step 4**; the operational detail behind execution order, isolation checks, evidence collection, and report integrity.
- `references/reporting-format.md` — **read in full before Step 3**, alongside `storage-preflight.md`; the complete report spec: output directory layout, report initialization and progressive updates, the result matrix, the per-issue schema, Markdown/DOCX consistency, and DOCX scannability. Step 6 finalizes using it, it doesn't read it for the first time there.
- `assets/report-template-fallback.md` — fallback report shape; **read in full** only when the project's own Section H is missing or damaged.
