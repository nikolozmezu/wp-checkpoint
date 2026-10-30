# Shared Conventions — WordPress Update Testing

This file defines the vocabulary that `/wp-checkpoint:test-plan-create` and `/wp-checkpoint:test` both use. `/wp-checkpoint:test-plan-create` assigns these labels when it writes `testing-after-update.md`; `/wp-checkpoint:test` reads and reports using the exact same labels. The two skills live in separate folders, each with its own copy of this file — **keep both copies identical**. If you ever have reason to change one (while running either skill, or when a user asks you to improve the skills themselves), change the other the same way.

This same content is also inlined directly into Section G of every `testing-after-update.md` that `/wp-checkpoint:test-plan-create` writes, because that document lives in the project root (not inside either skill's folder) and must stay readable on its own. If you change this file, update `assets/testing-after-update-template.md`'s Section G to match, and treat already-generated project documents' Section G as needing the same refresh next time `/wp-checkpoint:test-plan-create` runs on them.

## Test IDs

Format: `<AREA>-<NNN>` — an uppercase area mnemonic, a hyphen, then a zero-padded 3-digit sequence number starting at `001` within that area (e.g. `HOME-001`, `SEARCH-003`, `ADMIN-012`). For a specific custom post type, taxonomy, or form, use its real slug/name as (part of) the area code instead of a generic word, so the ID stays meaningful on its own (e.g. `CASESTUDY-001`, not `CPT-001`).

Suggested default area codes — adapt to what this project actually has, don't force-fit every code onto a project that doesn't need it:

| Area code | Covers |
| :-- | :-- |
| `HOME` | Homepage |
| `LAND` | Other important landing pages |
| `SINGLE-<posttype>` | Single/detail template for a post type |
| `ARCH-<posttype-or-taxonomy>` | Archive / taxonomy listing pages |
| `SEARCH` | Search results |
| `NAV` | Header, footer, menus, mobile nav, sticky elements |
| `FILT` | Filters, pagination, load-more, URL/state preservation |
| `FORM-<name>` | A specific form |
| `MEDIA` | Galleries, players, embeds, uploads |
| `RESP` | Responsive layout / breakpoints / visual states |
| `ADM-<area>` | Admin / editorial workflow |
| `AJAX` / `REST` | AJAX actions and REST endpoints |
| `CRON` | Scheduled jobs, queues, imports |
| `CACHE` | Page/object/transient/CDN caching and invalidation |
| `I18N` | Language / locale behavior |
| `SMOKE` | Cross-cutting essential checks (see Priorities below) |

Once an ID is assigned, it is permanent: never reuse it for an unrelated check, and never renumber existing IDs just to keep a sequence tidy. If a feature a test ID covers is removed from the project, mark that test case `REMOVED` (with the date and reason) instead of deleting it — this keeps history traceable and keeps the ID from ever being silently reassigned to something else.

## Priorities

- **P0** — Essential availability, primary user journeys, and critical editorial functionality.
- **P1** — Important supporting functionality.
- **P2** — Secondary behavior and visual details.

Priority is a property of the *feature* (how much it matters if it's broken), independent of whether a given update is likely to touch it.

## Result statuses

Exactly five values, used consistently by both skills:

- **NOT RUN** — Not yet executed in the current run. Every test case in a freshly created or freshly updated `testing-after-update.md` starts here — the document is a plan, not a report.
- **PASS** — Actually executed, and the observed result matched the documented expected result. Never assign PASS without both execution and direct observation of the outcome.
- **FAIL** — Actually executed, and the observed result did not match the documented expected result.
- **BLOCKED** — The check applies to this project and environment but could not be completed this run (missing access, missing tool, unmet precondition, unavailable isolation, etc.). Always record the specific reason.
- **NOT APPLICABLE** — The check does not apply to this *project* or *environment* — the feature it covers doesn't exist here, or this specific environment can't exhibit the behavior at all (e.g. a cache layer requiring a server module this environment doesn't run). Always state why. **This is not the same as being outside this run's selected scope** — a test ID simply left out of a smoke-only or targeted run's selected scope is **NOT RUN** with its matrix row's Selected column set to No and the specific scope reason stated, never NOT APPLICABLE. Reserve NOT APPLICABLE for a genuine, project/environment-level non-applicability, explicitly confirmed or user-excluded — not for "wasn't picked for this run."

A NOT RUN or BLOCKED check is never counted as a pass, in any summary, count, or narrative conclusion.

## Evidence-source labels (discovery time)

Used in Section C of `testing-after-update.md` to mark how each piece of inventory was established, and reused in Section F as each test case's **Expected-result basis** (the same three labels, applied to one expected result instead of a whole feature row):

- **Observed during discovery** — Directly viewed (page, admin screen, rendered behavior) during discovery. This is passive viewing, not a functional test — it confirms a page renders, not that its interactions work.
- **Derived from source or stored configuration** — Inferred by reading theme/plugin code, database option values, or configuration, without viewing it rendered.
- **Requires clarification or runtime confirmation** — Could not be determined with confidence from available access; needs an actual test run later, or needs the user to clarify.

## Finding severity (execution time)

Used in `/wp-checkpoint:test` reports to rate how bad an observed failure is (distinct from the feature's priority, which rates how much the feature matters):

- **Critical** — A P0 journey or essential availability is broken with no workaround, data is lost or corrupted, or there's a clear security exposure.
- **High** — A P0 or P1 feature fails in a way a normal user or editor would hit, with no reasonable workaround.
- **Medium** — A defect that's limited in scope, has a workaround, or affects a P2 behavior.
- **Low** — Cosmetic or edge-case defect with negligible practical impact.

State the one-line reasoning behind the severity you assign — don't derive it mechanically from priority alone. A P0 feature can still fail in a merely Low-severity way (e.g. a misaligned icon on the homepage), and a P2 feature can occasionally fail at High severity (e.g. a secondary form that corrupts data on submission).

## Issue classification (execution time)

- **Confirmed regression** — FAILed, and there's specific before/after evidence (a prior passing run, a dated screenshot, documented prior behavior) showing it worked before this update.
- **Known issue** — FAILed in a way that matches an issue already recorded as pre-existing in `testing-after-update.md` (Section C or E).
- **New issue of uncertain origin** — FAILed, with no before/after evidence either way, and it doesn't match a recorded known issue. Do not call this a regression without that evidence.
- **Intermittent** — Produced different results across repeated attempts in the same run. Record every outcome, including the failing one — never silently keep only the passing retry.

## Update-type tags

Tag every test ID in Section D's matrix with the update type(s) it's sensitive to, so a targeted `/wp-checkpoint:test` run can select, say, "every ID tagged `plugin:woocommerce`" without re-deriving the mapping each time:

- `core` — WordPress core
- `plugin:<slug>` — a specific plugin (use its real slug)
- `theme` — the active theme or child theme
- `builder` — the active page builder, if any (Elementor, Divi, Beaver Builder, Bricks, WPBakery, etc. — name the one actually in use)
- `php` — PHP version
- `env` — hosting/environment (web server config, object cache, CDN, database engine/version)

## Issue IDs (execution time)

Format: `ISSUE-<NNN>` — zero-padded, sequential starting at `001` within a single `/wp-checkpoint:test` report run. Unlike a test ID, an issue ID is scoped to its own report run only — it is not a persistent, project-wide identifier, and numbering restarts on the next run. Every issue must also name the test ID(s) it was found through (a single issue can span more than one test ID; a single test ID can surface more than one issue).

## Cause classification (execution time)

Rates how confidently a finding's root cause is known — a separate axis from severity (how bad) and issue classification (regression vs. known vs. new vs. intermittent):

- **Confirmed** — the root cause was directly verified: read in the actual code/configuration, or reproduced via a controlled change, with the specific file/line, setting, or log entry cited as evidence.
- **Suspected** — available evidence points strongly to a likely cause but it wasn't independently verified (e.g. a timing correlation without a controlled test, or a plausible code path that wasn't traced line-by-line).
- **Unknown** — no reliable cause theory exists yet. Say what was ruled out, if anything, and name concrete diagnostic next steps rather than guessing a fix.

Never mark a cause **Confirmed** without naming the specific evidence that establishes it. Never let a guess be written as if it were Confirmed.

## Role required for remediation (execution time)

Names who is actually positioned to act on a finding:

- **WordPress Administrator** — fixable from wp-admin alone (a setting, content, a plugin's own options page).
- **Developer** — requires a theme, plugin, or other code change.
- **Hosting Administrator** — requires server/infrastructure-level access (PHP version, web server configuration, DNS, SSL certificates, file permissions outside WordPress's own reach).

Name more than one role when remediation spans layers (e.g. "Developer, then Hosting Administrator to deploy").
