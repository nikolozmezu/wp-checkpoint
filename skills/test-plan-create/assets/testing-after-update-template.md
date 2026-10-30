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
  - Every test case's Status field starts at "NOT RUN". Never fill in PASS/FAIL/BLOCKED/NOT APPLICABLE
    while authoring this document — those are only ever written by an actual /wp-checkpoint:test run.
  - Remove the "EXAMPLE —" rows/cards once you've replaced them with real content; keep the structural
    HTML comments that explain how to extend each section, they help whoever maintains this later.
  - Never invent a plausible-sounding expected result to fill a gap. Where the correct or intended
    behavior can't be established, write the test case as far as you can and set its Expected-result
    basis to "Requires clarification or runtime confirmation," naming the specific uncertainty.
  - Never write a password, token, API key, or other secret anywhere in this file.
-->

# Testing After Update — <Project Name>

**Document status:** draft
**Last discovery/update date:** <YYYY-MM-DD>
**Last full test run date:** never

---

## A. Purpose and Operating Instructions

This document is a reusable testing runbook for <Project Name>. It is written and maintained by the `/wp-checkpoint:test-plan-create` Claude Code skill and executed by the `/wp-checkpoint:test` Claude Code skill.

- Preparing or updating this document does not execute or authorize any of the tests listed in it.
- Actual testing happens only through a separate, explicit invocation of `/wp-checkpoint:test`.
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
| Active theme | `<name> <version>` (parent, if child theme: `<name> <version>`) |
| Permalink structure | `<e.g. /%postname%/>` |

**Active plugins:**

| Plugin | Slug | Version | Notes |
| :-- | :-- | :-- | :-- |
| EXAMPLE — Yoast SEO | `wordpress-seo` | 2x.y | — |

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

**Known issues (pre-existing, not regressions):** `<list anything already broken today, so a future run doesn't mistake it for new damage — or "none identified">`

**Intended behavior vs. unclear behavior:** Don't silently treat existing broken behavior as if it were the correct expected result. Where you're not sure whether something is a bug or deliberate, say so explicitly here rather than guessing: `<list items needing clarification, or "none">`

---

## D. Priorities and Update-Impact Matrix

Priority definitions (see Section G below for the full vocabulary, including update-type tags): **P0** = essential availability, primary user journeys, critical editorial functionality. **P1** = important supporting functionality. **P2** = secondary behavior and visual details.

| Test ID | Feature | Priority | Update-type tags | Smoke? | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- |
| EXAMPLE — HOME-001 | Homepage loads and renders | P0 | core, theme, env | Y | — |

**Essential smoke checks after any update:** `<the list of Smoke=Y test IDs — this set must always run, regardless of scope>`

**Broader-coverage rule:** For a major version jump, multiple simultaneous updates, or any update whose impact is unclear, widen the run beyond the directly-tagged IDs to include related areas (anything sharing a template, dependency, or integration) rather than relying solely on the tag mapping above. Selecting targeted coverage must never silently omit the essential smoke checks. **PHP, runtime, or server/environment updates are their own broader-coverage trigger**: a PHP version change affects code execution paths across every active plugin equally, not just what's visible on a page — reviewing the error log alone does not establish runtime compatibility. Such updates should run the full smoke set plus every test ID tagged `php`/`env` (AJAX, REST, cron, cache, and at least one admin save/edit workflow, in addition to the log-review and console-error cases).

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
- **Feature / Priority:** <feature name> — <P0|P1|P2>
- **Update types:** <core|plugin:<slug>|theme|builder|php|env — comma-separated as applicable>
- **Depends on:** <other test IDs this depends on or affects, or "None">
- **Environment / Role / Prerequisites:** <local|live>; <role, e.g. Administrator, Editor, Anonymous>; <prerequisites>
- **Starting point:** <exact URL path or admin screen, e.g. /wp-admin/edit.php?post_type=case_study>
- **Test data:** <existing example to reuse, or disposable data to create, plus how it'll be cleaned up>
- **Steps:**
  1. <numbered action>
  2. <numbered action>
- **Expected result:** <specific, observable>
- **Expected-result basis:** <Observed during discovery | Derived from source or stored configuration | Requires clarification or runtime confirmation>
- **Evidence to collect:** <screenshot / network response / log excerpt / resulting content or job state / etc.>
- **Cleanup:** <steps to restore state, or "None required">
- **Known limitations / dependencies:** <anything relevant, or "None">
- **Status:** NOT RUN
```

For any card that reorders content, edits a shared/reusable template, or changes a persistent setting, the Steps and Test data fields must capture the *exact* pre-change value/order/state — not just a Cleanup field that says "revert the change." "Revert" is only as precise as the record of what to revert to.

### Frontend structure and content

<!-- Homepage, landing pages, single templates incl. CPTs, archives/taxonomy/search/pagination,
     template variations/sidebars/conditional sections/language variants, content selection/ordering/
     duplicate-exclusion rules, empty/missing-content/error states. -->

#### EXAMPLE — HOME-001 — Homepage loads and renders correctly
- **Feature / Priority:** Homepage — P0
- **Update types:** core, theme, env
- **Depends on:** None
- **Environment / Role / Prerequisites:** local; Anonymous; none
- **Starting point:** `/`
- **Test data:** None needed
- **Steps:**
  1. Load the homepage.
  2. Confirm header, main content area, and footer render.
- **Expected result:** Page returns HTTP 200, header/footer/main content render with no visible layout break, no PHP notices/warnings printed on the page.
- **Expected-result basis:** Observed during discovery — the homepage currently renders correctly; this restates its current, confirmed-good behavior as the bar to maintain.
- **Evidence to collect:** Screenshot; HTTP status code.
- **Cleanup:** None required.
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

<!-- This section is deliberately self-contained: it inlines the full shared vocabulary that the
     wp-checkpoint plugin's test-plan-create and test skills also keep in their own
     references/shared-conventions.md. This document lives in the project root, not inside a skill
     folder, so a pointer to that file would be a dead link for anyone reading this document on its
     own — keep this section and that file in sync if either ever changes. -->

**Test ID format:** `<AREA>-<NNN>` — an uppercase area mnemonic, a hyphen, a zero-padded 3-digit sequence number (e.g. `HOME-001`). Once assigned, an ID is permanent: never reused for an unrelated check, never renumbered to keep a sequence tidy. A test case for a since-removed feature is marked `REMOVED` (date + reason) rather than deleted.

**Priorities:** **P0** = essential availability, primary user journeys, critical editorial functionality. **P1** = important supporting functionality. **P2** = secondary behavior and visual details.

**Update-type tags:** `core` (WordPress core) · `plugin:<slug>` (a specific plugin) · `theme` (active theme/child theme) · `builder` (the active page builder) · `php` (PHP version) · `env` (hosting/environment: server config, object cache, CDN, database engine/version).

**Statuses:** NOT RUN, PASS, FAIL, BLOCKED, NOT APPLICABLE.
- **NOT RUN** — not yet executed in the current run.
- **PASS** — actually executed, and the observed result matched the documented expected result. Never assigned from inspection alone.
- **FAIL** — actually executed, and the observed result did not match.
- **BLOCKED** — the check applies but couldn't be completed this run; state the specific reason.
- **NOT APPLICABLE** — doesn't apply to this *project or environment* (the feature doesn't exist here, or this environment can't exhibit it at all); state why. Not the same as being outside this run's selected scope — an ID simply unselected for a smoke/targeted run is NOT RUN with Selected: No and the scope reason stated, never NOT APPLICABLE.

Never count an unexecuted or blocked check as passed.

**Evidence-source labels** (used in Section C, and as each Section F test case's Expected-result basis): **Observed during discovery** (directly viewed) · **Derived from source or stored configuration** (inferred from code/config without viewing it rendered) · **Requires clarification or runtime confirmation** (not yet resolvable with the access available during discovery).

**Finding severity** (for `/wp-checkpoint:test` reports — rates how bad an observed failure is, distinct from priority, which rates how much the feature matters): **Critical** (a P0 journey or essential availability broken with no workaround, data loss/corruption, or a clear security exposure) · **High** (a P0/P1 feature fails in a way a normal user or editor would hit, no reasonable workaround) · **Medium** (limited scope, has a workaround, or affects a P2 behavior) · **Low** (cosmetic/edge-case, negligible practical impact).

**Issue classification** (for `/wp-checkpoint:test` reports): **Confirmed regression** (FAILed, with specific before/after evidence it worked before this update) · **Known issue** (FAILed in a way matching an issue already recorded in Section C/E) · **New issue of uncertain origin** (FAILed, no before/after evidence either way — do not call this a regression without that evidence) · **Intermittent** (different results across repeated attempts in the same run — record every outcome, including the failing one).

**Issue IDs** (for `/wp-checkpoint:test` reports): `ISSUE-<NNN>`, zero-padded, sequential starting at `001` within a single report run — scoped to that run only, not a persistent project-wide ID like a test ID. Every issue also names the test ID(s) it was found through.

**Cause classification** (for `/wp-checkpoint:test` reports — how confidently a finding's root cause is known, separate from severity and issue classification): **Confirmed** (root cause directly verified — code/config read, or reproduced, with the specific evidence cited) · **Suspected** (evidence points strongly to a likely cause but it wasn't independently verified) · **Unknown** (no reliable cause theory yet — state what was ruled out and give concrete diagnostic next steps instead of a guessed fix).

**Role required for remediation** (for `/wp-checkpoint:test` reports): **WordPress Administrator** (fixable from wp-admin alone) · **Developer** (needs a theme/plugin/code change) · **Hosting Administrator** (needs server/infrastructure-level access) — name more than one when remediation spans layers.

**Execution order:**
1. Establish environment, update context, and prerequisites.
2. Run essential smoke checks.
3. Execute the selected expanded coverage.
4. Collect findings and limitations.
5. Clean up test changes.
6. Produce the report.

This document, as created or updated, contains **no completed test results** — every test case above is at NOT RUN.

---

## H. Future Report Template

<!-- /wp-checkpoint:test fills this shape in when it produces a report. Keep it here so the report format
     stays tied to this specific document rather than drifting from a separate template elsewhere.
     This mirrors assets/report-template-fallback.md in the wp-checkpoint:test skill folder exactly — if
     you ever edit one, edit the other the same way. The full rules behind this shape (the output base
     directory and public-exposure gate, the result matrix, the per-issue schema, Markdown/DOCX
     consistency, DOCX scannability) are in that skill's references/storage-preflight.md and
     references/reporting-format.md — this section is the shape to fill in, not the rulebook, so it
     stays readable on its own without those files. /wp-checkpoint:test's own current reporting
     requirements always take precedence over this section if it predates a later rule change — an
     older, intact copy of this section supplies this project's framing, never a ceiling on what the
     current rules require. -->

Each run writes a self-contained `report-<YYYY-MM-DD>[-N]/` directory at the output base directory
captured at invocation (not necessarily the project root, though it usually is — numeric suffix for an
additional run the same date; a prior run's directory is never overwritten), containing
`screenshots/`, `log-excerpt.txt`, `wp-update-report.md`, and — unless the tooling to produce it was
unavailable or the export itself failed, which is stated explicitly if so — `wp-update-report.docx`,
generated from the same finalized content as the Markdown so the two never disagree.
`wp-update-report.md` is initialized right after the public-exposure gate passes, before execution
starts (Run completeness: Incomplete, full result matrix pre-populated from every plan test ID),
updated progressively as each check executes, and finalized at the end — it follows this shape:

```
## Report: <Project Name> — <YYYY-MM-DD HH:MM> — <what was updated>

**Environment:** <local/live base URL>   **Update:** <component(s), from → to version(s)>
**Test-plan reference:** this document, last discovery <date>
**Scope executed:** <full | smoke | targeted: list>   **Scope excluded:** <list + reasons>
**Run completeness:** <Complete — every selected test ID reached a terminal status | Incomplete — list which IDs were never reached and why>
**DOCX generated:** <yes | no — unavailable, or export failed; say which>

### Result counts
Full plan: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
Selected scope: NOT RUN: <n> · PASS: <n> · FAIL: <n> · BLOCKED: <n> · NOT APPLICABLE: <n>
(both reconciled with the full result matrix below — tallies of its Status column, not separately-kept
numbers; "Selected scope" counts only rows with Selected: Yes)

### Full result matrix
<table: Test ID | Selected for this run's scope? | Status | Actual observation | Evidence reference |
Reason (if BLOCKED/NOT RUN/NOT APPLICABLE/excluded) — every test ID in the PLAN, selected and
deliberately-unselected alike. An unselected ID is Status: NOT RUN, Selected: No, with the scope
reason — never NOT APPLICABLE, which is reserved for a genuine project/environment non-applicability.>

### Prioritized issue index
<table: Issue ID | Title | Severity | Related test ID(s) | Cause classification | Role required —
sorted Critical → High → Medium → Low>

### Confirmed issues
<one subsection per issue (ID format ISSUE-<NNN>): severity + reasoning, related test ID(s), issue
classification, what's wrong and who it affects, the exact affected URL/admin location/code reference,
reproduction steps with expected vs. actual, evidence (screenshot/log-excerpt references), a cause
classification (Confirmed/Suspected/Unknown) naming the specific evidence behind it, numbered manual
remediation steps only where the evidence supports one (otherwise diagnostic next steps instead of a
guessed fix — and never described as already applied or verified), the role required to act on it
(WordPress Administrator / Developer / Hosting Administrator), and the observable success criteria plus
which test ID(s) to rerun to verify a correction.>

### Blocked checks
(test ID + specific reason — kept separate from confirmed issues, never blended)

### Unresolved preconditions / open questions
(anything from Section E not met, or an open question from Section C/I still unresolved — kept separate
from confirmed issues, never blended)

### Cleanup status
(what was restored; what, if anything, remains to be cleaned up manually)

### Remaining work
(follow-up fixes needed, a future full run, a missing precondition to unblock, etc.)

### Conclusion
(qualified to the scope actually executed — "no issues found" must name the tested scope and any
unresolved limitations, never stated as an unqualified clean bill of health)
```

---

## I. Gaps and Maintenance

**Open questions / missing evidence:** `<list, or "none at this time">`

**Update this document when:**
- A feature, template, route, integration, or dependency listed above changes.
- A new feature, post type, template, or integration is added.
- A test run (Section H report) surfaces a gap in this plan itself (missing coverage, a stale starting URL, an outdated expected result that no longer matches intended behavior).

**Stability rule:** Keep test IDs stable where possible. Do not change a test case's expected result merely to make a failure appear successful — if the expected result itself seems wrong, flag it here for human review instead of silently editing it away.
