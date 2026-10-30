# Reporting Format — Output Structure, Result Matrix, and the Per-Issue Schema

Read this in full at Step 3, before execution starts — not deferred to Step 6. `wp-update-report.md` is initialized at Step 3 (right after the public-exposure gate passes) and updated progressively through Step 4; Step 6 finalizes it. Read `references/storage-preflight.md` alongside this file — it owns the output base directory and the public-exposure gate, including the minimal empty containers (the report directory, and `screenshots/`) that gate's own probes may need to create before any real content is written. Read `references/shared-conventions.md` too if you haven't already — it defines statuses, severity, issue classification, issue IDs, cause classification, and role-required labels used throughout this file.

## Why a file-based report, not just a chat reply

A chat reply disappears once the conversation scrolls. The people who need this report — a WordPress administrator deciding what to click, a developer deciding what to fix, a hosting administrator deciding what to escalate — usually aren't the person who ran this skill, and won't read the Claude conversation. Every report this skill produces must stand on its own, in plain English, with exact names and locations, as if handed to a stranger with no other context.

## Output location and directory structure

Every run produces a self-contained directory at the **output base directory** (captured and gated per `references/storage-preflight.md` — don't re-derive it here):

```
report-<YYYY-MM-DD>/
  screenshots/
  log-excerpt.txt
  wp-update-report.md
  wp-update-report.docx
```

- `<YYYY-MM-DD>` is today's date. If a `report-<YYYY-MM-DD>/` directory from an earlier run today already exists, do not reuse or overwrite it — create `report-<YYYY-MM-DD>-2/`, incrementing the numeric suffix until you reach a name that doesn't exist yet.
- Never delete, overwrite, or write into a previous run's `report-*/` directory, and never touch `testing-after-update.md` itself (that document is `/wp-checkpoint:test-plan-create`'s to write — see SKILL.md Step 3's hard boundaries).
- `screenshots/` holds every screenshot this run captured, named descriptively and traceably, e.g. `ISSUE-003-checkout-500.png` or `HOME-001-homepage-desktop.png` — not `screenshot1.png`.
- `log-excerpt.txt` holds only the relevant excerpts this run attributed to itself (per Step 4's log-attribution rule), each one labeled with its source file and the timestamp range it covers. Never copy a full raw log file in here, and never include a credential, token, or secret that happened to appear near a relevant line.
- Each new `report-<date>[-N]/` directory must pass the public-exposure gate in `references/storage-preflight.md` before any real content is written into it — the gate's own probes may need to create the empty directory (and `screenshots/`) first, as `storage-preflight.md` describes; what waits for the gate to pass is the real report text, real screenshots, and real evidence, not the empty container itself. Re-run this including the numbered-suffix case on a second run the same day. Don't assume an earlier pass in this same session still holds for a different path.

## Markdown/DOCX consistency rule

Write `wp-update-report.md` first — it is the single source of truth. Generate `wp-update-report.docx` from that same finalized content (the same findings, issue IDs, test IDs, severities, cause classifications, roles, and recommendations, word-for-word where practical) rather than composing the DOCX as a separate, independently-worded document. The two files must never disagree about a fact.

**Use the environment's available DOCX-authoring capability to produce the `.docx` file — do not write or maintain a custom script, library integration, or exporter application as part of this plugin to generate it.** There are two distinct ways DOCX output can fail to appear, and they must be reported differently, both in chat and at the top of `wp-update-report.md`:
- **Capability unavailable** — no DOCX-authoring tool exists in this session at all. State this plainly; `wp-update-report.md` is the only report file produced this run.
- **Export failed** — the tool was available but the generation attempt itself failed (an error, a timeout, an unreadable/corrupt output). State this plainly too, distinctly from "unavailable" — don't blur the two together, and don't retry silently in a way that could produce a half-written or inconsistent file without saying so.

## Making the DOCX easy to scan

- Start with a short executive summary (what was updated, scope executed, result counts by status, result counts by severity, and the run's completeness — see "Run completeness" below).
- Follow it with a **prioritized issue index** — a table of every confirmed issue, sorted Critical → High → Medium → Low, showing Issue ID, title, severity, related test ID(s), cause classification, and role required — so a reader can triage without reading every section.
- Include the **full result matrix** (below) so every test ID in the plan is accounted for — selected and deliberately-unselected alike — not just the ones that became issues.
- Give every issue the same section structure (see the per-issue schema below), in the same order every time, so a reader learns the shape once and can skim subsequent issues.
- Render remediation steps as an actual numbered list, not a paragraph.
- Embed each referenced screenshot as a captioned figure (caption names the Issue ID and what the image shows), not a bare image with no label.

## Section separation — never blend these

Keep these visually and structurally separate, in both the Markdown and the DOCX:

1. **Full result matrix** — every test ID in the plan, accounted for (see below), whether selected for this run's scope or not. Neutral bookkeeping, not findings.
2. **Confirmed issues** — the per-issue schema below. Only things actually observed to fail, per Step 4's evidence-integrity rules.
3. **Blocked checks** — test ID + the specific reason it couldn't be completed. Not a defect; don't let a blocked check drift into looking like a confirmed issue, and don't drop it silently either.
4. **Unresolved preconditions / open questions** — anything from the document's Section E that wasn't met, or an open question from Section C/I that's still unresolved. Not a defect either, and not this run's fault.

A reader should never have to guess which bucket something belongs to.

## Full result matrix (required)

Account for **every test ID in the project's plan** (`testing-after-update.md` Section D), not only the ones selected for this run's scope — this is distinct from, and more complete than, the prioritized issue index (which only lists IDs that produced a confirmed issue):

| Test ID | Selected for this run's scope? | Status | Actual observation | Evidence reference | Reason (if BLOCKED / NOT RUN / NOT APPLICABLE / excluded) |
| :-- | :-- | :-- | :-- | :-- | :-- |

- **Selected for this run's scope?** — **Yes**, with which category put it in scope (the smoke subset, directly tagged to the update for a targeted run, or a dependency/cross-feature effect per Section D) — or **No**, if the ID exists in the plan but this run's scope (smoke-only, or a targeted run that doesn't touch it) deliberately didn't select it.
- **Status** — one of the five statuses from `shared-conventions.md`. An ID with Selected: No is always **NOT RUN** here — it was never attempted this run, by design, not because it's inapplicable. **Never mark an unselected ID NOT APPLICABLE** — that status is reserved for a check that doesn't apply to the project or environment at all (see `shared-conventions.md`), a different fact entirely from "wasn't chosen for this run's scope."
- **Actual observation** — a short, concrete statement of what was actually seen (not just "matched expected" — say what was observed), or "—" for Selected: No rows.
- **Evidence reference** — a `screenshots/`/`log-excerpt.txt` path, or "—" if none applies to this row.
- **Reason** — required whenever Status is BLOCKED, NOT RUN, or NOT APPLICABLE, or Selected is No; state the specific reason (for Selected: No, the specific scope reason — e.g. "not in the smoke subset," "no update-type tag match for this targeted run"), never leave it blank.

**Result counts — two reconciled tallies, both required:**
- **Full plan:** a tally of every row's Status in the matrix above (every test ID the plan defines).
- **Selected scope:** the same tally restricted to rows with Selected: Yes — this is the number that actually describes what this run did.

Both are a tally of this matrix, not a separately-kept number that could drift from it — if either doesn't match the matrix, the matrix is wrong and needs fixing before the report is final.

## Precedence over an older Section H

This skill's own current reporting requirements — this file, `shared-conventions.md`, and `storage-preflight.md` — always govern the report's required structure and fields. **Never omit a currently-required field (the result matrix, the per-issue schema, cause classification, role required, DOCX generation, the public-exposure gate, etc.) because an older project's Section H predates it and doesn't mention it.** An intact Section H still supplies this project's specific report framing and any genuinely project-specific labels it contains — reuse those where they're compatible — but an old template is a source of *site-specific framing*, never a ceiling on what the current rules require. If Section H is missing or badly damaged rather than merely old, use `assets/report-template-fallback.md` as the baseline shape instead, and say so explicitly in the report. Either way, this never means editing `testing-after-update.md` itself — that document is never rewritten during a test run.

## Run completeness and verification before reporting success

Initialize `wp-update-report.md` at Step 3, immediately after the public-exposure gate passes — with the full result matrix pre-populated from the plan's every test ID (Selected/Status set per the agreed scope, every row starting NOT RUN) and **Run completeness: Incomplete**. This is the file Step 4 updates as execution actually happens, not a draft kept only in memory until the end.

A run can be interrupted or run out of time before every selected check executes. Make that visible, don't let a partial run read like a finished one:

- State the run's completeness explicitly in the report header, **assessed against Selected: Yes rows only** — an ID the run deliberately never selected (smoke-only run, or a targeted run that doesn't touch it) never counts against completeness: **Complete** (every *selected* test ID reached a terminal status — PASS/FAIL/BLOCKED/NOT APPLICABLE) or **Incomplete** (some *selected* ID is still NOT RUN because the run itself stopped before reaching it, not because of a per-check blocker) — and if Incomplete, which selected IDs were never reached.
- Save progress into the run's `report-<date>[-N]/` directory as you go, not only at the very end — if the run is interrupted, whatever was written should still be a legible partial report, not nothing.
- **Before telling the user the run succeeded, read back what was actually saved to disk**: open `wp-update-report.md` from its saved path (don't rely on the in-memory draft) and confirm it contains what you intended; confirm every screenshot and log-excerpt path referenced in it actually exists in `screenshots/`/`log-excerpt.txt`; and confirm `wp-update-report.docx` actually exists, has the content you expect, and is consistent with the Markdown (open/inspect it with the same DOCX-authoring capability used to produce it, or an equivalent available check) — rather than assuming the generation step must have worked because it didn't raise an error.

## Per-issue schema (every confirmed issue, in both files)

Use this exact structure for every issue in the "Confirmed Issues" section. Every field is required; write "Not established" or the specific missing piece rather than omitting a field silently.

```
### <ISSUE-NNN> — <clear, specific title>

- **Severity:** <Critical | High | Medium | Low> — <one-line reasoning, per shared-conventions.md>
- **Related test ID(s):** <TEST-ID, TEST-ID, ...>
- **Issue classification:** <Confirmed regression | Known issue | New issue of uncertain origin | Intermittent>

**What's wrong and who it affects:**
<Plain-English description of the defect and its real-world impact on the site or its users/editors/customers.>

**Where:**
<The exact affected page URL, admin screen (exact navigation path and setting/control names as verified —
e.g. "WooCommerce → Status → WooCommerce pages"), component, or verified code location
(file path + line/function, as actually read — never invented).>

**Reproduction steps and expected vs. actual behavior:**
1. <numbered step>
2. <numbered step>
- **Expected:** <what the documented expected result said should happen>
- **Actual:** <what was actually observed>

**Evidence:**
<Screenshot reference(s) — e.g. "see screenshots/ISSUE-004-quiz-confirmation.png" — and/or a log excerpt
reference — e.g. "see log-excerpt.txt, lines 12–28" — matching what Step 4 actually collected.>

**Cause:** <Confirmed | Suspected | Unknown>
<The cause itself, and the specific evidence behind that classification (file/line, config value, log
entry) — or, if Unknown, what was ruled out and the concrete diagnostic next steps to pursue instead of
a guessed fix.>

**What needs to change:**
<If the cause is Confirmed or well-Suspected and a concrete fix is actually supported by the evidence,
give numbered manual remediation steps using exact, verified UI control/setting names or exact code
locations — never an invented menu path, setting name, or code location. If the cause is Unknown, give
diagnostic next steps instead of a repair recipe — do not describe a guessed fix as if it were a
recommendation. Either way, make explicit that this is a proposed action, not something this run
performed: this skill never applies fixes.>

**Role required:** <WordPress Administrator | Developer | Hosting Administrator — one or more, per
shared-conventions.md>

**How to verify the correction:**
<The specific, observable success criteria a human should look for once they've made the change
(e.g. "the page returns HTTP 200 and the price/Add-to-Cart control renders"), and which test ID(s) from
testing-after-update.md to rerun to confirm it, via a future `/wp-checkpoint:test` run.>
```

## What belongs in the chat reply vs. the files

Keep the chat reply itself brief: the selected scope, the result counts (reconciled with the matrix), the run's completeness, the file paths (Markdown, DOCX or the specific "unavailable" vs. "export failed" note, screenshots folder, log excerpt). The full findings, evidence, and recommendations belong in the files, not restated at length in chat.
