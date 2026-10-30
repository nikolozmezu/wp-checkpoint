# WP Checkpoint

WP Checkpoint is a Claude Code plugin for testing a WordPress site around an update. It first studies a WordPress project and writes a reusable testing runbook (`testing-after-update.md`), then — after you apply an update yourself — executes that runbook and produces an evidence-based report of what passed, failed, or needs attention. It never updates WordPress, installs anything, or fixes problems on its own; it only inspects the project, runs the tests you ask for, and reports what it found.

## Installation

WP Checkpoint is a [Claude Code](https://claude.com/claude-code) plugin, installed through Claude Code's plugin marketplace mechanism directly from this repository.

Inside a Claude Code session:

```
/plugin marketplace add nikolozmezu/wp-checkpoint
/plugin install wp-checkpoint@wp-checkpoint
```

Or from a shell, with the Claude Code CLI:

```
claude plugin marketplace add nikolozmezu/wp-checkpoint
claude plugin install wp-checkpoint@wp-checkpoint
```

Both commands also accept the full repository URL in place of `nikolozmezu/wp-checkpoint` (e.g. `https://github.com/nikolozmezu/wp-checkpoint.git`).

## Prerequisites

- A local WordPress project Claude Code can read, and that the testing skill can interact with — typically opened as the working directory of your session.
- Whatever access the checks you select actually need: a local site URL and a WordPress admin login (or an already-authenticated browser session) for anything that loads pages or the admin area, read-only database or WP-CLI access if you want those checks included, and log file access if you want log excerpts in the report.
- DOCX reports depend on a DOCX-authoring capability being available in your Claude Code environment. If none is available, or the export attempt fails, the testing skill says so explicitly and still produces the Markdown report — it does not silently drop the DOCX without telling you.

## Usage

WP Checkpoint has two skills, invoked explicitly. Neither one ever invokes the other automatically.

**1. Create or refresh the testing plan** — before an update cycle, or whenever the project has changed enough that the plan needs updating:

```
/wp-checkpoint:test-plan-create
```

This only reads the project and writes `testing-after-update.md`. It never touches content, settings, code, or the live site.

**2. Apply your update separately**, outside Claude Code, the way you normally would.

**3. Run the testing skill explicitly**, after the update is applied:

```
/wp-checkpoint:test
```

This executes the existing plan and writes the report. It takes an optional scope argument — `/wp-checkpoint:test full` (the default), `/wp-checkpoint:test smoke`, or `/wp-checkpoint:test targeted`.

## What gets generated

- `testing-after-update.md` — the reusable test plan, written at your project root (or an existing or explicitly given location). This file is documentation only; it never contains test results.
- `report-<YYYY-MM-DD>[-N]/` — a dated, self-contained folder created by each test run, holding `wp-update-report.md` (and `wp-update-report.docx` when DOCX generation is available), a `screenshots/` folder, and a `log-excerpt.txt`. It lists a PASS / FAIL / BLOCKED / NOT APPLICABLE result per test case, plus any issues found, for a human to review and act on.

WP Checkpoint does not modify WordPress and does not fix anything it finds — it plans, tests, and reports.
