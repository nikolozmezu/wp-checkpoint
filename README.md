# WP Checkpoint

WP Checkpoint is a Claude Code plugin that studies a WordPress project, writes a reusable test plan, and checks the site around an update. Use it for a standalone check or record a before checkpoint and compare after updating. It produces a short illustrated report for the site owner and detailed evidence for whoever investigates the problems. Software updates and repairs remain separate actions performed by you.

## Installation

In Claude Code:

```text
/plugin marketplace add nikolozmezu/wp-checkpoint
/plugin install wp-checkpoint@wp-checkpoint
```

Or from the shell:

```sh
claude plugin marketplace add nikolozmezu/wp-checkpoint
claude plugin install wp-checkpoint@wp-checkpoint
```

The marketplace source can also be the full repository URL, `https://github.com/nikolozmezu/wp-checkpoint.git`. The install argument remains `wp-checkpoint@wp-checkpoint`.

## Two ways to test

Create or refresh the project's plan first:

```text
/wp-checkpoint:test-plan-create
```

Planning reads source, configuration and representative pages and writes `testing-after-update.md`. It does not run functional tests. Existing plans are refreshed in place, retaining test IDs and removed-test history. Neither skill invokes the other automatically.

Schema 3 plans record execution layers, implementation evidence, fixture setup and the
state left after cleanup. Before delivery, planning performs a separate source-backed
review of all active cards: current versus historical evidence, actual request routes,
fixture lifetime, expected branches and runtime coverage. Unavailable facts remain
explicit gaps. A structural validator result is not a claim that this review proved
every requirement or that the site works.

**Standalone testing** works without a before checkpoint, including for an update already applied:

```text
/wp-checkpoint:test
/wp-checkpoint:test smoke
/wp-checkpoint:test targeted
```

The default scope is `full`. The skill asks what changed only when it is not already known. It tests current behavior and does not call a new failure an update regression without appropriate before evidence.

**Before/after comparison** records actual behavior before the update:

```text
/wp-checkpoint:test before
```

The before run records WordPress, web PHP, theme and plugin versions/activation, screenshots and actual results from the chosen plan checks. It returns a dated `checkpoint.json` path. Then apply the update yourself, and run:

```text
/wp-checkpoint:test after
```

You can also specify a scope, for example `before smoke` or `after targeted`. Supply the earlier checkpoint path when it is not already established. The skill verifies project identity and matching evidence, compares detected version changes with what you say was updated, and tests the current site. A missing or unusable baseline is explained; ordinary testing remains available, without invented before results.

The snapshot is a testing record, not a restorable site/database backup. A screenshot records appearance; functional regression claims require comparable prior functional results. Changes in content, time, animation or viewport are reviewed before treating an image difference as a defect. Multiple simultaneous updates do not prove which component caused a failure.

## Continue or retest

```text
/wp-checkpoint:test resume <absolute-path-to-run-state.json>
/wp-checkpoint:test retest <absolute-path-to-run-state.json>
/wp-checkpoint:test retest <absolute-path-to-run-state.json> --ids CART-001,FORM-001
```

Resume rechecks the exact OPEN run, current environment, evidence and unfinished
cleanup. It continues pending work without blindly repeating a submission. Completed
observations keep their original dates. Plan/context drift requires a new run.
Retest creates a fresh normal run for prior failed/blocked checks or explicit IDs,
plus prerequisites; a new pass never erases the old failure. No fixes are applied.

## Coverage and access

- `full`: all active plan tests.
- `smoke`: essential checks plus their prerequisites.
- `targeted`: smoke, update-tag matches, affected features and prerequisites. PHP/runtime and broad or uncertain updates require wider coverage; explicit user limits remain visible in the report.

When Python is available, `scripts/select_tests.py` computes the selected IDs, dependency
order and a reason for every inclusion/exclusion. PHP and uncertain environment
changes use conservative coverage. Excluding an action does not hide its known
downstream impact; unavailable prerequisites remain explicit blockers.

At startup, the testing skill checks which browser/screenshot, WordPress/DB, log and DOCX capabilities are available. It maps missing capabilities to affected tests and continues independent work. Provide a local URL and appropriate access, preferably an existing authenticated browser session; reuse context already supplied. Live pages are a read-only reference unless you explicitly authorize a different scope. A local clone must have confirmed isolation before any test can send messages, charge money, trigger webhooks or touch shared services.

A before run executes the same kind of documented, reversible local test actions as a normal run. Temporary content/state is restored; unfinished cleanup is reported. Neither mode updates software, edits source, rewrites the test plan or fixes defects.

## Reports

Each run creates a fresh protected `report-<YYYY-MM-DD>[-N]/` directory:

```text
wp-update-report.md      Full technical record, every test ID, attempts and evidence
wp-update-report.docx    Short user-facing report, when DOCX authoring is available
screenshots/            Relevant issue screenshots, paired before/after when available
log-excerpt.txt          Relevant redacted excerpts or an explicit no-log-evidence note
checkpoint.json         Before runs only: versioned index of the saved baseline
selection.json          Selected IDs, reasons and dependency order
context.json            Non-secret current identity and context fingerprint
run-state.json          Action journal, results and cleanup, when available
visual-review/index.html Optional offline before/after slider and highlighted changes
```

The established `wp-update-report` filenames are retained for compatibility. The DOCX uses the user's language, a brief outcome and one compact section per issue: what is wrong, where, impact, expected/actual behavior, a captioned screenshot and a practical next step. It does not repeat the full technical matrix or raw logs. Markdown and DOCX agree on facts, severity and recommendations; their length and layout differ. Missing screenshots are stated honestly. DOCX capability unavailable and export failed are distinct outcomes, reported explicitly.

The five result statuses are NOT RUN, PASS, FAIL, BLOCKED and NOT APPLICABLE. A failed valid attempt remains FAIL even if a retry passes, with an intermittent finding. Removed tests remain historical unselected rows. A Complete run means every selected test was assessed; it can still contain failures or blocked checks. Summaries state those limits.

The invocation directory is the default report parent. You may explicitly choose a different report destination without moving the plan. Before saving site-specific data, each destination is checked for web exposure, including JSON checkpoints and screenshot paths. New runs and retests never overwrite earlier reports. Explicit resume alone can update
the verified OPEN bundle; finalized history and completed checkpoints remain immutable.

## Faster discovery and visual review

On a large project refresh, the optional evidence index reuses reviewed static source
findings whose fingerprints have not changed. It detects changed/deleted/new watched
files and identifies unindexed cards. Activation, settings and runtime evidence always
need current checks; source hashes never reuse old PASS results. The plan stays
authoritative and every active card still receives a source-backed review.

Matched screenshots can produce a self-contained HTML slider, side-by-side views and
pink highlighted pixel differences. Context/hash/dimension checks prevent invalid
comparisons, and explicit masks record excluded dynamic regions. This requires optional
Pillow; missing capability is reported without automatic installation. Pixel differences
are inspection aids, not automatic regressions. The DOCX stays concise.

## Diagnose the installed version

```text
/wp-checkpoint:doctor
```

The read-only diagnostic compares source, registered and cached versions and runtime
file contents. It detects same-version stale caches and relevant disabled settings.
The actually loaded session version remains unknown unless the caller supplies it;
matching files on disk do not prove an open session reloaded. Nothing is installed,
removed or enabled by this diagnostic.

## Validation for maintainers

The dependency-free validator uses Python 3.10+ and checks structural invariants; it does not prove that the site works or that an expected result is correct. From this repository:

```sh
python scripts/validate.py plugin
python scripts/validate.py plan /path/to/testing-after-update.md
python scripts/validate.py report /path/to/wp-update-report.md --plan /path/to/testing-after-update.md
python scripts/validate.py checkpoint /path/to/checkpoint.json
python -m unittest discover -s tests -v
```

Use the absolute path to `scripts/validate.py` when working from a WordPress project. Checks cover duplicate IDs, matrix/card agreement, dependency references, result counts, evidence paths and checkpoint integrity. Legacy plans are handled with explicit defaults/warnings for newer optional fields. Shared conventions/storage copies and the embedded template vocabulary must remain synchronized.

For schema 3 plans, the validator also requires the evidence/state fields and checks
declared php/infrastructure layers against php/env tags. It reports `STRUCTURAL OK`
separately from semantic review; it cannot infer whether an endpoint or fixture claim
is true. Offline editorial and membership projects in [evals](evals/README.md) exercise
those planning decisions with fresh reviewers. They contain synthetic data only.


Reports automatically reconcile with an adjacent run-state.json; use --state for an
explicit ledger. IDs, selection categories, statuses, mode, evidence and recorded plan
hash must agree. Older reports without a ledger remain compatible.

The optional [real WordPress/browser suite](evals/runtime/README.md) runs pinned
WordPress/PHP/SQLite and Chromium against disposable editorial/catalogue fixtures.
It checks known functional failures, an unchanged control and the offline comparison
viewer. It includes a separate blind-skill evaluation procedure; the deterministic
harness alone is not proof of Claude's accuracy on arbitrary projects.

## Package a local development version

Local Claude marketplace installs can copy ignored development files. Build a small
source-only release before installing a checkout that contains browser/npm caches:

```text
python scripts/package_plugin.py --source <checkout> --catalog <workspace>/wp-checkpoint-marketplace --output <workspace>/wp-checkpoint-marketplace/releases/1.3.0
```

Set the final manifest version before packaging. The output must be fresh and outside
the checkout; the catalogue retains prior releases and atomically points to the new
one. Runtime bytes stay identical for doctor comparison. Dependencies, browser caches,
reports and private files are excluded; packaging does not install or publish anything.
Register the stable catalogue path as the local marketplace source. Existing same-name
marketplaces may need native scoped removal/re-addition before switching that source.
Future releases update the catalogue pointer and use the normal plugin update command.
GitHub installations use committed source; local-only changes are not published by
these commands.
