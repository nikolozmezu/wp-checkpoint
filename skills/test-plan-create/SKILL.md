---
name: test-plan-create
description: Discover a WordPress project and create or refresh its project-specific testing-after-update.md runbook before update testing or when features change. Documentation only; never executes tests or invokes the testing skill.
disable-model-invocation: true
---

# /wp-checkpoint:test-plan-create

Study this WordPress project and create or refresh `testing-after-update.md`. The output is a reusable plan, not test results. Testing is a separate explicit invocation of `/wp-checkpoint:test`, optionally with `before` / `after` for a paired comparison. Never invoke it automatically.

## Boundaries

Read source, non-secret configuration, existing logs, read-only database/WP-CLI metadata, and passively view public pages or accessible admin screens. Do not submit forms, exercise workflows to determine pass/fail, create/edit/delete/publish/schedule content, upload media, trigger cron/queues/imports/sync, purge caches, install dependencies, update software, change settings/code/database, or fix defects.

The primary project output is the plan. An optional incremental-discovery evidence manifest and cache JSON may accompany it after their actual destinations pass the same storage gate. They contain reviewed paths, hashes and provenance, never secrets or test results. The storage preflight may create minimal empty destination directories and an inert exposure probe; follow its cleanup rules exactly. Passive observation can establish what exists, not that a workflow passed. Every card's result status remains **NOT RUN**.

## 1. Capture location and locate WordPress

Capture the **output base directory** immediately: the session's working directory at invocation. Keep it fixed despite later navigation; it is not automatically the WordPress root, repository root, or plugin folder.

Find `wp-config.php` / `wp-load.php` in the working directory and common layouts: project root, `app/public/`, `web/wp/` with `web/app/`, `public_html/`, `htdocs/`, or `wp/`. Record the project root separately if it contains the installation and other tooling. Ask for the path only if discovery cannot locate it.

## 2. Reuse context, then ask only for missing access

Send one concise intake message for the local URL, local admin access if needed, and a live/reference URL if needed. Prefer an authenticated browser session or manual login. Ask for credentials only when access actually requires them; never echo or write secrets into the plan, reports, command arguments, URLs, or explanatory/log output. Do not request live admin credentials by default; live is a read-only reference.

In the same message, make known issues, intentional local/live differences, important workflows, exclusions, and the preferred visual reference optional questions. “Unknown” or “discover it” does not block progress. Discover versions, plugins, and roots yourself. A local clone does not establish isolation from email, payments, webhooks, remote storage, or sync; record these dependencies for later testing.

## 3. Discover the project

For an existing plan or a large source tree, read [references/incremental-discovery.md](references/incremental-discovery.md). If a reviewed index exists, run its read-only comparison before editing the plan and reuse only unchanged static evidence. Reinspect affected/unindexed areas and current activation/configuration; new files and unknown impact still require discovery. Missing indexes/helpers simply use ordinary discovery. This does not skip the final review of every active card.

Read [references/discovery-checklist.md](references/discovery-checklist.md) and [references/shared-conventions.md](references/shared-conventions.md) now. Inspect representative examples of every important template and meaningful variation, not every content item. Map each feature to its real URL/admin screen, template, configuration, dependencies, and implementation reference. Separate active use, inactive plugins, and unused code.

Continue with available evidence when browser, database, WP-CLI, or admin access is incomplete, recording specific limitations in Sections B/C/F. Record activation as Confirmed active, Confirmed inactive or Unknown with its source, environment and date; keep historical incidents separate from confirmed current observations. Use the evidence-source labels consistently. Do not invent intended behavior; unresolved acceptance criteria belong in Sections C/I and use **Requires clarification or runtime confirmation**.

## 4. Resolve storage and author the plan

Read [references/storage-preflight.md](references/storage-preflight.md) before writing. Resolve the plan in this order:

1. An explicit user-supplied path is authoritative, whether or not it exists.
2. Otherwise use an existing plan at the captured output base.
3. Otherwise perform the validated fallback search in common project layouts.
4. If none exists, create the plan at the captured output base.

Update a found plan in place; never move or duplicate it. Pass the exposure gate for the resolved destination before writing site-specific content. If protection is inconclusive, request a non-public destination; do not guess one or modify server configuration.

Read [assets/testing-after-update-template.md](assets/testing-after-update-template.md), [references/test-catalogue-coverage.md](references/test-catalogue-coverage.md), [references/common-pitfalls.md](references/common-pitfalls.md), and [references/plan-quality-review.md](references/plan-quality-review.md) before drafting cards. The last reference defines the evidence/state fields and the source-backed review required before delivery. Read each once for this task; revisit relevant sections when needed.

- **New plan:** copy the template only after the gate passes. Fill project-specific placeholders with established facts; preserve literal UI labels, paths, URLs, field names, and identifiers. Remove example rows/cards. Keep Sections A–I, the generic card-format block, and generic vocabulary/report notation in G/H.
- **Existing plan:** read the whole saved plan first and merge findings in place. Never replace it with a blank template. Refresh discovery metadata, preserve accurate content and stable IDs, and flag disputed expectations in Section I instead of changing them to match a failure. Mark retired cards **Lifecycle: REMOVED**, with date and reason; retain their matrix rows and historical cards. Keep **Status: NOT RUN** on both active and removed cards.

The template owns the output structure. Fill it with these invariants:

- **B/C — Environment and inventory:** distinguish installed versions, confirmed activation, observed footprints and intended acceptance. Use source/time/environment provenance; cached assets, copied logs and absence from a sample do not settle current activation or failure. For each submitting/notifying feature, identify the actual renderer/plugin, persistent entry storage or email-only behavior, active handlers, and literal outbound destinations. Keep current observations, historical/unverified incidents and intended behavior separate.
- **D/F — Selection and cards:** assign priority, update tags, lifecycle, prerequisites (`Depends on`), and downstream cross-impact (`Affects`) in both places. `Depends on` is execution ordering; `Affects` is impact selection, not a prerequisite. All references name real IDs. Active cards must not depend on removed cards; resolve that gap explicitly. Avoid prerequisite cycles when authoring cards; if a real workflow cannot be represented without one, record the gap rather than inventing a fixture. Retired cards are never smoke checks or selected for execution.
- **D — Coverage:** use the shared contract's selection rules: full ACTIVE coverage, smoke with prerequisites, or targeted tags/layers with downstream impact and prerequisites plus smoke. Infer execution layers from actual implementation before assigning tags; PHP/runtime/environment impact must reach affected execution paths even when a manual tag list omits them. Unknown layers/impact require conservative coverage and a concrete limitation. Explicit user exclusions win and remain visible.
- **E — Preconditions:** record available roles, fixtures, reference evidence, integration isolation requirements, and exact cleanup needs, but leave every confirmation checkbox unchecked.
- **F — Actionable tests:** use schema 3's Execution layers, Implementation evidence, Fixture setup and State after cleanup fields. Ground routes/behavior in the actual caller/configuration, map every expected branch to an observing step, and make setup valid after predecessor cleanup. Default to self-contained setup; shared state requires explicit owner/lifetime. Capture original persistent state before changes. Cover every applicable area; unresolved or inapplicable coverage belongs in Applicability/Gaps. Preserve ordinary editorial/scheduled workflows even when current usage was not observed.
- **G/H — Portable contract:** retain the self-contained vocabulary and report shapes. The technical Markdown keeps the full matrix and evidence; the shorter DOCX presents outcomes and actionable issues with relevant screenshots. Shared facts, IDs, severity, recommendations, counts, and limitations must agree; full-text parity is not required. A version snapshot alone cannot confirm a regression.
- **I — Review and maintenance:** record structural validation separately from semantic review, with reviewed IDs and source-check limitations. Retain missing evidence, disputed expectations and refresh triggers. Actual run dates/outcomes belong in run reports, never in fabricated plan results.

## 5. Validate the saved plan and return it

Reopen the actual saved file. Resolve the validator from this plugin's installation, not from the WordPress working directory, and run it read-only:

```text
python <plugin-root>/scripts/validate.py plan <absolute-path-to-testing-after-update.md>
```

The validator checks structure, not whether project facts or expected behavior are true. If Python is unavailable, say so and perform the structural checks manually. Correct structural authoring errors before delivery:

- Every Section D ID has exactly one Section F card and vice versa; lifecycle, priority, tags, `Depends on`, and `Affects` match.
- All references exist, active prerequisite relationships are acyclic, no active card requires a removed card, and the smoke line equals the ACTIVE `Smoke: Y` rows. If a dependency problem cannot be resolved from evidence, preserve and report that gap instead of claiming validation passed.
- REMOVED entries carry a date/reason and stay unselected with NOT RUN; every other plan card also remains NOT RUN.
- No `EXAMPLE —` content or unresolved project placeholder remains. Preserve generic notation in the card-format block and Sections G/H, and intentionally unchecked Section E boxes.
- Schema-3 fields are present on active cards; unavailable facts are explicitly unresolved rather than replaced by invented metadata.

Then perform [references/plan-quality-review.md](references/plan-quality-review.md)'s semantic review of **every ACTIVE card against the saved plan and relevant actual sources**. Use an independent reviewer when available, otherwise a separate pass and disclose it. Check provenance, actual request paths, expected branches, fixture state after cleanup and layer-based update coverage. Record Structural validation, Semantic review, Reviewed test IDs and Source-check limitations in Section I. Fix self-authored contradictions before marking the plan Reviewed; inaccessible evidence may remain as a precise Reviewed with gaps limitation. Reopen corrections and repeat affected checks. A structural pass alone never establishes readiness.

If using incremental discovery, capture/update its storage-gated index only now, against the final saved plan and sources actually reviewed. Record reuse/refresh limitations without copying old runtime outcomes.

Return the saved path, concise coverage counts by priority, separate structural/semantic outcomes, important execution gaps, and an explicit statement that no tests ran and no completed results were written. An incomplete plan may be delivered honestly as Needs revision or Reviewed with gaps; do not call it complete because its IDs/counts validate. Do not invoke `/wp-checkpoint:test`.
