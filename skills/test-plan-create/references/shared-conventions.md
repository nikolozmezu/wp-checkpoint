# Shared Conventions — WordPress Update Testing

The two skills use this contract. Keep the copies in both `references/` directories identical. When maintaining the plugin, synchronize the vocabulary in the plan template's Section G; generated plans must remain readable without this plugin. Do not edit plugin instructions while executing a project test.

## Test IDs and lifecycle

Use `<AREA>-<NNN>`: an uppercase area mnemonic and a zero-padded sequence starting at `001`. Use real feature names in the area, for example `HOME-001`, `FORM-CONTACT-001`, `SINGLE-CASESTUDY-001`, `ADM-EDITOR-001`. Useful areas include HOME, LAND, NAV, SEARCH, FILT, MEDIA, RESP, AJAX, REST, CRON, CACHE and I18N; use only those the project needs.

IDs are permanent: never renumber or reuse them for unrelated checks. Each card has a separate **Lifecycle: ACTIVE | REMOVED** field. Retain removed cards and matrix rows, with removal date and reason. Their plan Status remains NOT RUN. Historical REMOVED rows are unselected in execution, Status NOT RUN, Reason naming removal; they never count as active coverage. A request to exercise a removed feature is a plan discrepancy to resolve, not permission to silently resurrect its old test. Older plans without a lifecycle field default to ACTIVE unless explicitly marked removed.

## Priorities and update tags

- **P0** — essential availability, primary journeys and critical editorial functionality.
- **P1** — important supporting functionality.
- **P2** — secondary behavior and visual details.

Priority measures the feature's importance, not the likelihood that an update affects it. Record it identically in the impact matrix and card.

Tags: `core` (WordPress), `plugin:<slug>` (actual plugin slug), `theme` (active parent/child theme), `builder` (the actual page builder), `php` (PHP runtime), `env` (server, database, cache/CDN or other environment changes). Record identical tags in the matrix and card, including php/env on relevant execution paths.

Schema 3 cards also record **Execution layers**, using comma-separated `php`, `browser`, `infrastructure`, `external`, `static`, `unknown`. These describe what the tested behavior actually executes or depends on, not the name of its area. `php` requires the `php` update tag; `infrastructure` requires `env`. A server-rendered page or server-handled form can involve both php and browser; do not label it browser-only because it is viewed in a browser. `static` applies only to a check genuinely confined to static assets/files. `unknown` requires a specific explanation in Known limitations / dependencies. Do not invent a layer or add a meaningless tag solely to satisfy validation.

Each active schema 3 card also records **Implementation evidence** (actual source/config/request reference, or `Unresolved: <specific missing evidence>`), **Fixture setup** (how this card obtains its required state) and **State after cleanup** (what is left). These are reviewable claims, not proof by themselves. A structural validator cannot establish their truth; source-backed semantic review is separate.

## Dependencies and coverage selection

**Depends on** lists prerequisite test IDs or fixtures established by those tests. **Affects** lists downstream test IDs whose behavior this feature can change. Both fields contain actual IDs, or `None`; keep matrix and card consistent. An Affects edge does not claim that the target creates a prerequisite fixture. For legacy plans with ambiguous combined dependencies, inspect the documented actions, retain conservative coverage and report anything still unresolved.

A dependency establishes ordering, not persistence of another card's temporary data. Default to a self-contained Fixture setup. If a fixture is shared, document its creator, consumers, lifetime and cleanup owner; it must still exist after the producing card's actual steps/cleanup. A completed create/delete test cannot supply its deleted object to a later check. Do not silently postpone cleanup or recreate a fixture through an unsafe external action.

Select deterministically, keeping every historical plan ID in the result matrix:

1. Exclude REMOVED IDs and explicit user exclusions from execution first. Set Selected: No, Status: NOT RUN and a specific reason. An explicit user exclusion can narrow smoke coverage; disclose that limitation.
2. **full**: select all remaining ACTIVE IDs. Use `Yes/full` (or `Yes/smoke` for the essential smoke subset).
3. **smoke**: select the active smoke subset and its transitive prerequisites. Use `Yes/smoke` and `Yes/smoke-dependency`.
4. **targeted**: start with IDs matching the actual update tags. Follow downstream Affects edges and reverse Depends on edges transitively; add prerequisites of the resulting set. Union this with smoke and smoke prerequisites. Use `Yes/targeted-tagged`, `Yes/targeted-dependency`, `Yes/smoke` or `Yes/smoke-dependency`, choosing the first direct reason that applies. Do not expand downstream solely from smoke IDs and accidentally turn every targeted run into full.
5. An explicit exclusion suppresses execution, not known impact: downstream impact traversal may pass through an excluded active node. Filter it from the final selected set without erasing affected consumers. Traverse each ID once. Missing references and circular fixture requirements are gaps to record, not invented prerequisites. If an excluded, removed or blocked prerequisite prevents a selected check, that check is BLOCKED unless an already-established equivalent fixture exists.

Use the installed `scripts/select_tests.py` helper to compute this set/order/reasons when available. An explicit limited list or fresh retest selects the requested active IDs plus prerequisites; it does not add unrelated smoke/downstream coverage. Use existing Yes/targeted-tagged and Yes/targeted-dependency labels, with the explicit/retest origin stated in Reason. Record the resulting coverage limits.

For PHP/runtime updates, seed selection with every active card whose Execution layers includes php or unknown, as well as php-tagged cards, before applying dependency/impact closure. For environment changes, include the affected infrastructure/execution layers; if the affected layer is unknown, use conservative broad coverage. Missing or incorrect tags in an old plan must not silently narrow runtime testing. When layers are absent, inspect documented behavior; include unresolved server/runtime cases conservatively and record that the plan needs refresh. Do not infer safe exclusion from an arbitrary ID prefix.

With unknown update impact, propose full coverage; never guess tags. PHP/runtime/environment changes need smoke plus relevant runtime checks, including AJAX/REST, cron, cache and admin saves. Major or simultaneous updates need broader related coverage. Honor a user's explicit narrower scope and state the resulting limits. Targeted without enough update context needs clarification before selecting its additional tests.

## Result statuses and decisions

Exactly five statuses apply to execution; every card in a generated or refreshed plan stays **NOT RUN**.

| Situation | Status |
| :-- | :-- |
| Unselected, removed, or never reached; run ends before a required observation deadline | NOT RUN |
| Executed completely and directly observed all documented expected outcomes | PASS |
| Valid execution contradicted an established expectation, including a missed deadline with prerequisites met | FAIL |
| Applicable check lacks access, tools, isolation, fixture, a required precondition or settled acceptance criteria | BLOCKED |
| Confirmed non-applicability to this project/environment | NOT APPLICABLE |

Missing browser access is BLOCKED, not NOT APPLICABLE. A production-only cache that this local stack is confirmed incapable of exhibiting is NOT APPLICABLE, with the production coverage gap stated; uncertainty about the cache prerequisite is BLOCKED. A feature explicitly confirmed absent by design can be NOT APPLICABLE; merely choosing not to test it this run is NOT RUN with Selected: No. Unknown intent is BLOCKED, never an inferred exclusion.

Record a specific reason for BLOCKED, NOT RUN, NOT APPLICABLE and all unselected rows. Static source inspection cannot establish an interaction, screenshot comparison, upload or background-job PASS.

**Attempts:** keep every valid attempt with its observation and evidence. If any valid attempt fails, the aggregate test status is FAIL even when a retry passes; differing executed outcomes create an Intermittent finding. Do not count attempts as separate test IDs. Without a failure, PASS requires a complete observed success; partial progress with a named unmet prerequisite is BLOCKED, and an interrupted run without that prerequisite failure is NOT RUN. An invalid setup is a recorded prerequisite problem, not evidence of a product failure.

**Continuation:** Only an explicitly identified OPEN execution ledger can resume after fresh identity/context/evidence and cleanup checks. Preserve completed observations with their original dates; never blindly repeat an interrupted action. Finalized runs/checkpoints are immutable. Retesting after fixes creates a new run; the old failure remains historical evidence. OPEN/COMPLETE ledger lifecycle is operational bookkeeping, not another result status.

**Completeness:** Complete means every selected ID reached PASS, FAIL, BLOCKED or NOT APPLICABLE. Incomplete means a selected ID is still NOT RUN. Complete does not mean all passed. Present both full-plan counts and selected-scope counts, derived from the same matrix; explicitly name blocked coverage and pending cleanup. Unselected IDs do not reduce run completeness and never count as passes.

## Evidence-source labels (discovery)

Use the same labels in feature inventory and each card's Expected-result basis:

- **Observed during discovery** — passively viewed; confirms observed appearance, not unexercised interactions.
- **Derived from source or stored configuration** — inferred from actual code/configuration without runtime verification.
- **Requires clarification or runtime confirmation** — correct behavior cannot yet be established; name the uncertainty.

## Finding severity

- **Critical** — essential availability or a P0 journey broken without workaround, data loss/corruption, or clear security exposure.
- **High** — a normal user/editor hits a P0/P1 failure without a reasonable workaround.
- **Medium** — limited impact, a workaround, or an affected P2 behavior.
- **Low** — cosmetic/edge-case defect with negligible practical impact.

Give one sentence explaining impact. Do not mechanically derive severity from priority: a homepage icon can be Low, and a secondary form corrupting data can be High.

## Issue classification and IDs

- **Confirmed regression** — observed failure with comparable before evidence establishing that this behavior worked. A before screenshot establishes appearance, not prior form submission or scheduled-job success. A version difference alone is insufficient.
- **Known issue** — the failure matches a documented pre-existing issue or a comparable failed baseline check.
- **New issue of uncertain origin** — observed failure with no sufficient before evidence and no matching known issue.
- **Intermittent** — valid executed attempts produced differing outcomes; preserve the failing attempt and aggregate FAIL. Report before/after context separately where available.

Use `ISSUE-<NNN>` starting at 001 within each report. Issue IDs are local to a run; test IDs are persistent. Every issue links its test ID(s); one issue may affect several checks. Cross-run issue matching uses behavior, location and test IDs, never equal ISSUE numbers alone.

## Cause confidence and responsible role

**Confirmed** means specific evidence establishes the cause (a traced code path/configuration or a permitted controlled test); cite it. **Suspected** means evidence supports a theory without proving it. **Unknown** means no reliable theory; provide concrete diagnostic next steps. Temporal coincidence with an update, especially several simultaneous updates, does not establish causation. Never apply a fix or an undocumented configuration change just to prove a cause.

Roles: **WordPress Administrator** for wp-admin changes, **Developer** for code, **Hosting Administrator** for infrastructure. Name multiple roles when needed. The technical report retains these labels, IDs and exact references; the user-facing report explains the problem, impact and next step in the user's language without dumping internal details.
