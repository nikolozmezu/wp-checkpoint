---
name: test
description: Execute an existing WordPress testing-after-update.md plan and produce a technical Markdown report plus a concise illustrated DOCX. Supports ordinary testing, a before-update checkpoint, and after-update comparison. Requires an existing plan; never performs updates or fixes.
disable-model-invocation: true
argument-hint: "[before|after] [full|smoke|targeted] [--baseline <path>] | resume <run-state.json> | retest <run-state.json> [--ids <IDs>]"
---

# /wp-checkpoint:test

Execute this project's existing `testing-after-update.md`. Keep its requirements unchanged. All modes perform real selected tests; `before` additionally saves a reusable checkpoint, and `after` can compare against one. Neither mode updates WordPress, PHP, themes, plugins, or infrastructure.

## 1. Resolve the mode, location, and plan

Capture `invocation_directory` before navigating. Read `references/storage-preflight.md` and `references/shared-conventions.md` now. Keep the invocation directory fixed for plan lookup; resolve the separately overridable `report_output_directory` using the storage rules.

| Invocation | Mode | Scope |
| :-- | :-- | :-- |
| `/wp-checkpoint:test` or `full` | normal | full |
| `/wp-checkpoint:test smoke` or `targeted` | normal | named scope |
| `/wp-checkpoint:test before [full\|smoke\|targeted]` | before | full if omitted |
| `/wp-checkpoint:test after [full\|smoke\|targeted]` | after | full if omitted |

For `resume <run-state.json>` or `retest <run-state.json>`, first read [references/run-state.md](references/run-state.md). These are exclusive continuation commands. Resume refers to the exact OPEN run, its saved plan/mode/bundle and fresh verified context; finalized runs/checkpoints cannot resume. Retest reads finalized history, selects failed/blocked or explicitly requested IDs plus prerequisites, and creates a fresh normal run. Old failures remain unchanged. Neither command repeats an interrupted action automatically, invents cleanup completion or treats a matching ID as project identity. Resolve stale/unknown context before dependent work.

Parse `--baseline <path>` as an explicit checkpoint path in `after` mode; a directory means its `checkpoint.json`. A baseline supplied conversationally is equally authoritative. Other text describes update context. For conflicting modes/scopes, clarify rather than guessing. Read `references/before-after.md` for `before` or `after` only; ordinary testing does not require a checkpoint.

Find the plan at the explicitly supplied path, otherwise at the invocation directory, otherwise through the validated common-layout search in the storage reference. An explicitly supplied missing plan stops this skill; never substitute another. If no plan exists, tell the user to run `/wp-checkpoint:test-plan-create` and stop. Do not invoke it yourself.

Read the whole plan and verify its project/environment identity. Record stale or missing requirements as gaps; continue valid checks without inventing requirements. Never rewrite the plan or change an expected result to fit an observation.

## 2. Resolve access, update context, and capabilities

Ask once for information that is still missing: local URL and admin access (prefer an existing session or manual login), live URL only if needed as a read-only reference, what was updated (`normal`/`after`) or is planned (`before`), and any exclusions or integration restrictions. Discover current versions yourself. Use a valid checkpoint for prior versions; otherwise mark unavailable history unknown. Reuse prior answers and explicit scope; default to full. Targeted mode needs the affected components/tags established before selecting checks.

Use the user's language for report prose unless another report language was requested. Preserve exact UI labels, identifiers, filenames, and machine-readable report fields.

Check available capabilities before execution using `references/execution-and-evidence.md`: browser interaction/screenshots, project and WP-CLI/database access, relevant logs, and DOCX authoring. Record which checks a missing capability blocks; continue independent checks. Announce a known DOCX limitation early. Once the essentials are available, state mode, environment, scope, and baseline choice and proceed without asking again to begin.

Never put passwords, tokens, or secrets in reports, checkpoint metadata, command arguments, URLs, logs, or explanatory output. Ask for credentials only if needed; never echo them. Live is read-only reference by default. A request for production test actions requires an explicit production scope, as described in the execution reference.

## 3. Gate storage and initialize progress

Read `references/reporting-format.md` before writing. Pass the storage reference's public-exposure gate for this run's actual new `report-<YYYY-MM-DD>[-N]/` directory and screenshot destinations, including the types being written (`.json` for a before checkpoint). Only the gate's permitted inert probes may precede it. Inconclusive protection is not a pass: ask for a non-public destination, never guess one or change server configuration.

Read [references/run-state.md](references/run-state.md) and use `scripts/select_tests.py` against the saved plan when Python is available. Save its selection, order, reasons and excluded-prerequisite blockers; do not independently re-guess its selected set. Explicit exclusions affect execution but do not erase downstream update impact. For fresh retests use `run_state.py retest` instead. Missing Python permits disclosed manual ordinary testing, not a fabricated resumable state.

After the gate, initialize `wp-update-report.md` with the mode, update context, baseline reference, capability limitations, **Run completeness: Incomplete**, and every plan ID in the result matrix. Select IDs by the rules in `references/shared-conventions.md`, applied in `references/execution-and-evidence.md`; every row begins NOT RUN. Keep REMOVED history unselected, with its removal date/reason. Collect current non-secret context and initialize `run-state.json` using the run-state reference before any check; its context fingerprint must be computed from actual current evidence. If verified context is unavailable, disclose that safe continuation is unavailable and continue independent ordinary checks with manual progress. For `before`, initialize the ledger first, then `checkpoint.json` as Incomplete using `references/before-after.md`. Explicit resume reopens only its verified OPEN bundle and existing progress.

## 4. Execute and preserve evidence

Read `references/execution-and-evidence.md` in full before the first check. Follow the computed dependency order, which prioritizes selected smoke and its prerequisites, then the remaining selected checks. Never execute unselected smoke during an explicit limited retest. Follow the plan's roles, prerequisites, actions, expected results, evidence, and cleanup. Update the saved matrix and cleanup record after each check; in `before`, update checkpoint attempts and captures too. `after` compares matched evidence according to `references/before-after.md` while still executing the current tests.

When a ledger is available, persist `run_state.py start` successfully before the first action in a check, then record its actual result, local evidence hashes and cleanup. On interruption use the reference's read-only resume assessment and explicit current-state resolution. Reconcile the Markdown and before checkpoint after each ledger result; preserve earlier attempts and timestamps.

Use reversible local test actions and disposable content. Before any action that could reach an external service, verify its actual destination and isolation: a local URL is not proof. Never send a real message, make a real payment, delete shared remote media, or trigger production synchronization from a clone. Missing access, tools, or isolation blocks the affected check, not unrelated checks.

Do not update software, modify source, apply fixes, or silently change configuration outside a documented temporary test step. Restore temporary state and report precisely what remains if cleanup fails.

PASS requires execution and direct observation, not static inspection. Preserve all attempts; any valid failing attempt makes the aggregate FAIL even when a retry passes. Record that differing outcome as Intermittent. Attribute logs to this run only with matching timestamps/requests. A confirmed regression needs comparable evidence that this behavior passed before; a screenshot alone does not prove an interaction worked.

## 5. Finalize and verify deliverables

Finalize the technical Markdown using `references/reporting-format.md`: every plan ID, both reconciled status tallies, severity counts, findings, blocked checks, comparison gaps, cleanup, and scoped conclusion. Current reporting rules override an older plan Section H; preserve compatible project framing. Use `assets/report-template-fallback.md` only if Section H is missing or damaged, and say so.

For matched before/after images, read [references/visual-comparison.md](references/visual-comparison.md) and generate an optional offline `visual-review/index.html` with the real pixel-difference helper. Gate its HTML/JSON/PNG destinations first. Missing Pillow leaves ordinary evidence available; no automatic dependency installation. Highlighted differences are inspection aids, never automatic failures or baseline replacements.

Generate `wp-update-report.docx` with the environment's DOCX-authoring capability, never a custom exporter built for this plugin. It is the concise, illustrated human report: each issue has a plain-language explanation and real screenshot, or an explicit reason no screenshot exists. Keep technical matrices, code, and raw logs in Markdown/evidence. Both deliverables must agree on facts; they need not duplicate prose. Report capability-unavailable and export-failed distinctly in chat and Markdown.

Reopen saved Markdown, verify evidence paths, and inspect the DOCX for factual agreement and readable layout. Reconcile and finalize the OPEN execution ledger after selected checks are assessed; its finalized history is immutable. For `before`, finish that ledger first, then validate and reopen the checkpoint and mark it Complete only under `references/before-after.md`'s finalization rules. Never modify a prior run or a completed checkpoint.

Reply briefly with mode/scope, selected-scope counts, completeness and limitations, and artifact paths. In `before`, identify the checkpoint to use after the user performs the update; in `after`, state whether comparison was available and any limits. A completed run with blocked checks is not a fully verified site.
