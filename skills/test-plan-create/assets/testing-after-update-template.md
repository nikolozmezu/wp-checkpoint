<!--
  TEMPLATE for testing-after-update.md, produced by the /wp-checkpoint:test-plan-create Claude Code skill
  and consumed by the /wp-checkpoint:test Claude Code skill.

  HOW TO USE THIS FILE (instructions for the model filling it in — delete this comment block once done):
  - SKILL.md's Step 4 resolves exactly one of two cases before you touch this file — follow whichever
    applies, they are mutually exclusive:
      - New plan — created only at: an explicit user-supplied path where no plan exists yet; or the
        captured output base, when no explicit path was supplied and neither the output-base check nor
        a validated fallback search found an existing plan. Copy this whole file there as
        testing-after-update.md, only after that location's exposure gate has passed. Fallback search
        selects among *existing* plans for in-place updates — it never selects a new-file destination.
      - Existing plan (one was found at the resolved location — an explicit path, the captured output
        base, or via the fallback search): do NOT copy this template over it. Read the existing file
        fully first, then merge your updated findings into it in place — see the "Existing plan"
        guidance in SKILL.md's Step 4.
  - Replace every <...> placeholder that represents this project's own content with real,
    project-specific content. Preserve actual UI labels, URLs, filenames, field names, and code
    identifiers exactly as you found them. This does NOT mean touching the generic format/vocabulary
    notation in the "Test case card format" block or in Sections G/H (e.g. <AREA>-<NNN>, <n>,
    <YYYY-MM-DD HH:MM>) — those are deliberately generic, meant to stay exactly as written for
    /wp-checkpoint:test to fill in later (see SKILL.md's Step 5).
  - Every test case's Status remains "NOT RUN". Results belong in run reports, not this plan.
    Lifecycle is separate: ACTIVE, or REMOVED with a date/reason and a retained historical row/card.
  - Remove the "EXAMPLE —" rows/cards once you've replaced them with real content; keep the structural
    HTML comments that explain how to extend each section, they help whoever maintains this later.
  - Never invent a plausible-sounding expected result to fill a gap. Where the correct or intended
    behavior can't be established, write the test case as far as you can and set its Expected-result
    basis to "Requires clarification or runtime confirmation," naming the specific uncertainty.
  - Never write a password, token, API key, or other secret anywhere in this file.
-->

# Testing After Update — <Project Name>

**Document status:** draft
**Plan schema version:** 3
**Last discovery/update date:** <YYYY-MM-DD>
**Run reports:** Execution dates, outcomes, and before/after comparisons belong in dated report directories, maintained by `/wp-checkpoint:test`; this plan is a discovery snapshot.

---

## A. Purpose and Operating Instructions

This document is a reusable testing runbook for <Project Name>. It is written and maintained by the `/wp-checkpoint:test-plan-create` Claude Code skill and executed by the `/wp-checkpoint:test` Claude Code skill.

- Preparing or updating this document does not execute or authorize any of the tests listed in it.
- Actual testing happens only through a separate, explicit invocation of `/wp-checkpoint:test`.
- Optional `resume <run-state.json>` continues a verified OPEN run after fresh context/cleanup checks; `retest <run-state.json>` creates a fresh check of prior problems. Finalized history stays immutable.
- Optional paired testing uses `/wp-checkpoint:test before [full|smoke|targeted]`, then a user-applied update, then `/wp-checkpoint:test after [full|smoke|targeted]`. Both modes perform actual tests and capture their own version inventories. Normal `/wp-checkpoint:test [full|smoke|targeted]` remains available without a prior before run. Planning never launches any mode or applies updates.
- Discovery versions and inventory do not establish prior passing behavior. A before/after version difference alone is not evidence of a behavioral regression.
- Every check below that shows status **NOT RUN** is a planned check, not a completed result — treat it that way regardless of how long it's been sitting in this file.
- Source-code inspection and passively viewing a page can establish that something *exists*; neither can establish that an interactive feature, visual layout, upload workflow, or scheduled job actually *works*. Only an executed `/wp-checkpoint:test` check can.

---

## B. Site and Environment Profile

<!-- This is a discovery-time snapshot. Before relying on it for a future test run, confirm versions
     haven't changed — note that explicitly at the top of the report when they have. -->

| Field | Value |
| :-- | :-- |
| Local base URL | `<http://project.local>` |
| Live URL (reference) | `<https://example.com>` |
| Project root | `<filesystem path>` |
| WordPress root (if different from project root) | `<filesystem path, or "same as project root">` |
| Discovery date | `<YYYY-MM-DD>` |
| WordPress version | `<x.y.z>` |
| PHP version | `<x.y>` |
| Theme and activation evidence | `<theme/parent versions; Confirmed active or Unknown; current source, environment and observation date>` |
| Permalink structure | `<e.g. /%postname%/>` |

**Plugin inventory and activation evidence:**

| Plugin | Slug | Installed version | Activation state | State evidence and scope | Observed at | Feature use / limitations |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| EXAMPLE — Site search | `site-search` | 1.0 | Unknown | Source header proves installation; no current activation metadata | discovery date | Cached asset reference alone does not establish current activation |

Use Confirmed active, Confirmed inactive, or Unknown for activation. Record feature-use observations separately. Identify whether evidence belongs to this local environment, a live reference, a cached response, or historical logs. Missing front-end assets do not prove inactivity; copied log entries do not prove current activity or a current defect. Unknown state is a finding to preserve, not a blank to fill with an assumption.

**MU-plugins / relevant drop-ins:** `<list, or "none found">`

**Site architecture notes:** `<multisite? headless/decoupled front end? page builder in use? ecommerce platform? multilingual? anything else structurally important>`

**Known local-vs-live differences:** `<explicit differences you found, or "unknown — not yet compared">`

**Limitations recorded at discovery time:** `<unavailable integrations, intercepted/disabled email, missing licenses, different PHP version than live, production-only cache/CDN layers, anything you could not inspect and why>`

---

## C. Feature and Representative-Page Inventory

For each important feature, record where it lives, how it's implemented, and how confident you are in that information. Use the evidence-source labels defined in Section G exactly: **Observed during discovery**, **Derived from source or stored configuration**, or **Requires clarification or runtime confirmation**.

| Feature | Representative URL / admin location | Template / component | Variations | Dependencies | Implementation / config reference | Evidence source |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| EXAMPLE — Blog single post | `/sample-post/` | `single.php` | with/without featured image | — | `wp-content/themes/<theme>/single.php` | Observed during discovery |

**Current confirmed observations / known issues:** `<observation, actual environment, timestamp/source and whether correct behavior is established; or "none confirmed">`

**Historical or unverified observations:** `<old logs, cached output, possible issues with missing current evidence; include source environment/date and required confirmation, or "none">`

**Intended behavior vs. unclear behavior:** Don't silently treat existing broken behavior as if it were the correct expected result. Where you're not sure whether something is a bug or deliberate, say so explicitly here rather than guessing: `<list items needing clarification, or "none">`

---

## D. Priorities and Update-Impact Matrix

Priority definitions (see Section G below for the full vocabulary, including update-type tags): **P0** = essential availability, primary user journeys, critical editorial functionality. **P1** = important supporting functionality. **P2** = secondary behavior and visual details.

| Test ID | Feature | Lifecycle | Priority | Update-type tags | Smoke? | Depends on | Affects | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| EXAMPLE — HOME-001 | Homepage loads and renders | ACTIVE | P0 | core, theme, php, env | Y | None | None | — |

**Essential smoke checks after any update:** `<exactly the ACTIVE Smoke=Y test IDs, or None>`

**Lifecycle and graph:** Every row has a matching card with identical lifecycle, priority, tags, `Depends on`, and `Affects`. Lifecycle is ACTIVE or REMOVED; a removed row/card retains its ID and removal date/reason, has Smoke N, and stays unselected with NOT RUN in every report. `Depends on` lists prerequisite test IDs; `Affects` lists downstream cross-impact IDs. Use None for empty lists. Historical edges on removed cards do not enter scope selection. Active prerequisites must resolve to active cards; missing references/cycles are explicit plan gaps, never grounds to invent a fixture.

**Scope selection:** Full selects all ACTIVE IDs. Smoke selects ACTIVE Smoke=Y IDs and their transitive prerequisites. Targeted starts with ACTIVE update-tag matches, follows downstream `Affects` and reverse `Depends on` edges to closure, then includes their prerequisites, plus smoke and its prerequisites. Traverse each ID once per closure. Explicit user exclusions override selection and are recorded as coverage limitations; affected dependent checks need their own prerequisite assessment. Retain every unselected row with NOT RUN and a specific reason.

**Broader-coverage rule:** For major, simultaneous, or uncertain-impact updates, widen beyond direct tag matches to related templates, dependencies, and integrations. **PHP/runtime/environment updates also trigger broader coverage:** derive affected coverage from the cards' actual Execution layers, not only tags. Include php/unknown-layer cards for PHP changes, and relevant infrastructure/unknown cases for environment changes, plus smoke and dependencies. This includes applicable AJAX, REST, cron, cache and admin save/edit paths; log review alone does not establish compatibility. Missing layer data or tags in older plans is a coverage gap, not a reason to silently exclude a case. Respect explicit exclusions and report their consequences.

---

## E. Preconditions for Future Testing

<!-- Fill in what's actually knowable now (which roles exist, which integrations would need isolation,
     which test data is available) in the descriptive fields below. Leave every checkbox unchecked —
     confirming them is /wp-checkpoint:test's job at the start of a run, not something to mark done here. -->

- [ ] Target environment and base URL confirmed
- [ ] Update details known: component(s), from version → to version
- [ ] Required accounts/roles available: `<list>`
- [ ] Existing reusable examples or disposable test data identified: `<list>`
- [ ] Known existing issues reviewed (see Section C)
- [ ] Pre-update evidence / approved visual reference available: `<what, if anything>`
- [ ] Integration isolation requirements understood for: `<list integrations that need isolation confirmed before testing, e.g. payment gateway, SMTP, webhooks, FTP/CDN sync>`
- [ ] Checks that will modify local test data identified, with cleanup planned
- [ ] Cleanup/restoration requirements understood for the above

---

## F. Detailed Test Catalogue

<!-- Before drafting this section, read references/test-catalogue-coverage.md in full — it is the
     authoritative, specific coverage list. Organize test cases under the area headings below.
     Every test case MUST use the card format shown in the example. Avoid vague steps such as
     "check that everything works." -->

### Test case card format

```
#### <TEST-ID> — <Short title>
- **Lifecycle:** <ACTIVE|REMOVED>
- **Removal date / reason:** <YYYY-MM-DD — reason, required only for REMOVED; omit for ACTIVE>
- **Feature / Priority:** <feature name> — <P0|P1|P2>
- **Update types:** <core|plugin:<slug>|theme|builder|php|env — comma-separated as applicable>
- **Execution layers:** <php, browser, infrastructure, external, static, unknown — choose actual applicable values>
- **Implementation evidence:** <actual file:line/hook, non-secret option or observed request reference with environment; or Unresolved: specific missing evidence>
- **Depends on:** <prerequisite test IDs, or "None">
- **Affects:** <downstream/cross-impact test IDs, or "None">
- **Environment / Role / Prerequisites:** <local; live only for passive reference>; <role, e.g. Administrator, Editor, Anonymous>; <prerequisites>
- **Starting point:** <exact URL path or admin screen, e.g. /wp-admin/edit.php?post_type=case_study>
- **Test data:** <existing example to reuse, or disposable data to create, plus how it'll be cleaned up>
- **Fixture setup:** <self-contained preparation; or explicit shared fixture creator, consumers, lifetime and cleanup owner; or None required>
- **Steps:**
  1. <numbered action>
  2. <numbered action>
- **Expected result:** <specific, observable>
- **Expected-result basis:** <Observed during discovery | Derived from source or stored configuration | Requires clarification or runtime confirmation>
- **Evidence to collect:** <screenshot / network response / log excerpt / resulting content or job state / etc.>
- **Cleanup:** <steps to restore state, or "None required">
- **State after cleanup:** <exact state remaining for subsequent tests; or unchanged/no temporary state>
- **Known limitations / dependencies:** <anything relevant, or "None">
- **Status:** NOT RUN
```

For any card that reorders content, edits a shared/reusable template, or changes a persistent setting, the Steps and Test data fields must capture the *exact* pre-change value/order/state — not just a Cleanup field that says "revert the change." "Revert" is only as precise as the record of what to revert to.

Every expected-result clause needs an explicit action and observation step, including negative/rejection branches. Discover transport endpoints from the actual caller and registered handler/configuration; do not guess from a framework name. A prior card's dependency does not guarantee its fixture survives cleanup. Review the entire setup → actions → expected result → cleanup sequence against the implementation before marking the plan reviewed.

### Frontend structure and content

<!-- Homepage, landing pages, single templates incl. CPTs, archives/taxonomy/search/pagination,
     template variations/sidebars/conditional sections/language variants, content selection/ordering/
     duplicate-exclusion rules, empty/missing-content/error states. -->

#### EXAMPLE — HOME-001 — Homepage loads and renders correctly
- **Lifecycle:** ACTIVE
- **Feature / Priority:** Homepage — P0
- **Update types:** core, theme, php, env
- **Execution layers:** php, browser, infrastructure
- **Implementation evidence:** EXAMPLE — verified active homepage template and current local response; replace with real source/config references
- **Depends on:** None
- **Affects:** None
- **Environment / Role / Prerequisites:** local; Anonymous; none
- **Starting point:** `/`
- **Test data:** None needed
- **Fixture setup:** Existing published homepage; no temporary fixture needed.
- **Steps:**
  1. Load the homepage.
  2. Inspect the HTTP response status and confirm it is 200.
  3. Confirm header, main content area, and footer render, check for layout breaks, and inspect the rendered page for PHP notices/warnings.
- **Expected result:** Page returns HTTP 200, header/footer/main content render with no visible layout break, no PHP notices/warnings printed on the page.
- **Expected-result basis:** Observed during discovery — the homepage currently renders correctly; this restates its current, confirmed-good behavior as the bar to maintain.
- **Evidence to collect:** Screenshot; HTTP status code.
- **Cleanup:** None required.
- **State after cleanup:** Unchanged; no temporary state created.
- **Known limitations / dependencies:** None.
- **Status:** NOT RUN

*(Replace this example with this project's real homepage/landing-page/archive/single-template/search/pagination test cases, following the source list in `references/test-catalogue-coverage.md`.)*

### Navigation and interaction

<!-- Header/footer/menus/mobile nav/sticky elements; search/filters/pagination/load-more + URL/state
     preservation; pagination URL structure; modals/lightboxes/sliders/carousels/tabs/accordions;
     forms + validation/success/failure; logged-in vs anonymous. -->

*(Add this project's real test cases here.)*

### Media

<!-- Featured images/responsive images/thumbnails/galleries/proportions; upload workflows/formats/
     generated sizes; audio/video players + playback states; external embeds + fallback; missing media. -->

*(Add this project's real test cases here.)*

### Visuals and responsiveness

<!-- Header/footer/layouts/typography/spacing/images/cards/sidebars/overlays; component states/template
     variations; a viewport matrix based on THIS project's actual CSS breakpoints; near-breakpoint
     behavior; overflow/clipping/overlap/alignment/readable text/visible controls; long titles,
     portrait/landscape images. -->

**This project's breakpoint matrix:** `<list the actual breakpoints found in the theme/builder CSS, with the viewport widths to check just above and below each>`

*(Add this project's real test cases here.)*

### Admin and editorial workflows

<!-- Login + role/permission differences; create/edit/save/reopen/preview/publish/schedule; custom
     fields/relationships/repeaters/taxonomies/options/template assignments; block-editor/page-builder
     workflows; media uploads + image-size behavior; editorial role differences. -->

*(Add this project's real test cases here.)*

### Technical behavior

<!-- AJAX actions/REST endpoints actually used; scheduled posts/cron/queues/imports/integrations; page/
     object/transient/CDN cache layers; cache invalidation/freshness; cached vs uncached, anon vs
     logged-in; PHP/WP errors/warnings/deprecations; browser console/network errors; performance
     comparisons only where a baseline exists. Remember: a registered cron event ≠ a completed job, a
     configured integration ≠ a working one, a cache hit ≠ correct invalidation, a page loading ≠ all
     its interactions working. Do not invent performance thresholds. -->

*(Add this project's real test cases here.)*

### Applicability / Gaps

List coverage areas from `references/test-catalogue-coverage.md` that don't apply to this project, or that couldn't be resolved with available access, with a one-line reason each: `<list, or "none — full catalogue applies and was covered above">`

---

## G. Shared Vocabulary, Execution Procedure, and Result Definitions

### Test IDs and lifecycle

Use `<AREA>-<NNN>`: an uppercase area mnemonic and a zero-padded sequence starting at `001`. Use real feature names in the area, for example `HOME-001`, `FORM-CONTACT-001`, `SINGLE-CASESTUDY-001`, `ADM-EDITOR-001`. Useful areas include HOME, LAND, NAV, SEARCH, FILT, MEDIA, RESP, AJAX, REST, CRON, CACHE and I18N; use only those the project needs.

IDs are permanent: never renumber or reuse them for unrelated checks. Each card has a separate **Lifecycle: ACTIVE | REMOVED** field. Retain removed cards and matrix rows, with removal date and reason. Their plan Status remains NOT RUN. Historical REMOVED rows are unselected in execution, Status NOT RUN, Reason naming removal; they never count as active coverage. A request to exercise a removed feature is a plan discrepancy to resolve, not permission to silently resurrect its old test. Older plans without a lifecycle field default to ACTIVE unless explicitly marked removed.

### Priorities and update tags

- **P0** — essential availability, primary journeys and critical editorial functionality.
- **P1** — important supporting functionality.
- **P2** — secondary behavior and visual details.

Priority measures the feature's importance, not the likelihood that an update affects it. Record it identically in the impact matrix and card.

Tags: `core` (WordPress), `plugin:<slug>` (actual plugin slug), `theme` (active parent/child theme), `builder` (the actual page builder), `php` (PHP runtime), `env` (server, database, cache/CDN or other environment changes). Record identical tags in the matrix and card, including php/env on relevant execution paths.

Schema 3 cards also record **Execution layers**, using comma-separated `php`, `browser`, `infrastructure`, `external`, `static`, `unknown`. These describe what the tested behavior actually executes or depends on, not the name of its area. `php` requires the `php` update tag; `infrastructure` requires `env`. A server-rendered page or server-handled form can involve both php and browser; do not label it browser-only because it is viewed in a browser. `static` applies only to a check genuinely confined to static assets/files. `unknown` requires a specific explanation in Known limitations / dependencies. Do not invent a layer or add a meaningless tag solely to satisfy validation.

Each active schema 3 card also records **Implementation evidence** (actual source/config/request reference, or `Unresolved: <specific missing evidence>`), **Fixture setup** (how this card obtains its required state) and **State after cleanup** (what is left). These are reviewable claims, not proof by themselves. A structural validator cannot establish their truth; source-backed semantic review is separate.

### Dependencies and coverage selection

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

### Result statuses and decisions

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

### Evidence-source labels (discovery)

Use the same labels in feature inventory and each card's Expected-result basis:

- **Observed during discovery** — passively viewed; confirms observed appearance, not unexercised interactions.
- **Derived from source or stored configuration** — inferred from actual code/configuration without runtime verification.
- **Requires clarification or runtime confirmation** — correct behavior cannot yet be established; name the uncertainty.

### Finding severity

- **Critical** — essential availability or a P0 journey broken without workaround, data loss/corruption, or clear security exposure.
- **High** — a normal user/editor hits a P0/P1 failure without a reasonable workaround.
- **Medium** — limited impact, a workaround, or an affected P2 behavior.
- **Low** — cosmetic/edge-case defect with negligible practical impact.

Give one sentence explaining impact. Do not mechanically derive severity from priority: a homepage icon can be Low, and a secondary form corrupting data can be High.

### Issue classification and IDs

- **Confirmed regression** — observed failure with comparable before evidence establishing that this behavior worked. A before screenshot establishes appearance, not prior form submission or scheduled-job success. A version difference alone is insufficient.
- **Known issue** — the failure matches a documented pre-existing issue or a comparable failed baseline check.
- **New issue of uncertain origin** — observed failure with no sufficient before evidence and no matching known issue.
- **Intermittent** — valid executed attempts produced differing outcomes; preserve the failing attempt and aggregate FAIL. Report before/after context separately where available.

Use `ISSUE-<NNN>` starting at 001 within each report. Issue IDs are local to a run; test IDs are persistent. Every issue links its test ID(s); one issue may affect several checks. Cross-run issue matching uses behavior, location and test IDs, never equal ISSUE numbers alone.

### Cause confidence and responsible role

**Confirmed** means specific evidence establishes the cause (a traced code path/configuration or a permitted controlled test); cite it. **Suspected** means evidence supports a theory without proving it. **Unknown** means no reliable theory; provide concrete diagnostic next steps. Temporal coincidence with an update, especially several simultaneous updates, does not establish causation. Never apply a fix or an undocumented configuration change just to prove a cause.

Roles: **WordPress Administrator** for wp-admin changes, **Developer** for code, **Hosting Administrator** for infrastructure. Name multiple roles when needed. The technical report retains these labels, IDs and exact references; the user-facing report explains the problem, impact and next step in the user's language without dumping internal details.

---

## H. Future Report Template

<!-- Keep the technical report shape and human DOCX guidance synchronized with
     skills/test/assets/report-template-fallback.md in the plugin. Current test-skill
     reporting requirements govern older plans; preserve compatible project framing.
     English structural labels/status tokens support validation. Narrative and DOCX
     use the user's language unless another was requested. -->

Each explicitly invoked test run creates a fresh `report-<YYYY-MM-DD>[-N]/` directory
under the captured output base, or an explicit user-supplied destination, after the storage
exposure gate passes. Never overwrite an earlier run. The bundle contains
`wp-update-report.md`, `wp-update-report.docx` (or an explicit unavailable/export-failed
note), `screenshots/`, and `log-excerpt.txt`. Before mode also saves `checkpoint.json`; after mode references the selected
immutable checkpoint and records comparison evidence in its new report bundle.

Initialize the technical Markdown before testing with every plan ID and NOT RUN,
then save progress after each check. Finalize it before generating the concise DOCX.
The two deliverables agree on facts, IDs, severities, counts, recommendations, and
limitations; their detail and layout differ. Use this technical report shape:

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

---

## I. Gaps and Maintenance

**Structural validation:** `<command/result, or unavailable with reason; this does not verify factual correctness>`

**Semantic review:** `<Reviewed | Reviewed with gaps | Needs revision; reviewer/method and evidence-backed conclusions>`

**Reviewed test IDs:** `<all reviewed ACTIVE IDs; explicitly name any not reviewed and why>`

**Source-check limitations:** `<unavailable sources or unresolved acceptance/activation/fixture/transport questions, affected IDs and effect on future testing; or none>`

**Open questions / missing evidence:** `<list, or "none at this time">`

**Update this document when:**
- A feature, template, route, integration, or dependency listed above changes.
- A new feature, post type, template, or integration is added.
- A test run (Section H report) surfaces a gap in this plan itself (missing coverage, a stale starting URL, an outdated expected result that no longer matches intended behavior).

**Stability rule:** Keep test IDs stable where possible. Do not change a test case's expected result merely to make a failure appear successful — if the expected result itself seems wrong, flag it here for human review instead of silently editing it away.

Retain retired IDs as Lifecycle REMOVED with a date/reason in the matrix and card. Keep their Status NOT RUN and Smoke N. Update matrix/card metadata together. Run reports own test dates, actual results, and baseline comparisons; do not copy completed results into this plan.
