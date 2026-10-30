---
name: test-plan-create
description: Discovers a WordPress project's themes, plugins, custom post types, templates, integrations, roles, and architecture, then writes or updates a project-specific testing-after-update.md runbook at the session's captured output base directory (typically the project root). Documentation only — never executes tests, never changes content/settings/code, and never invokes /wp-checkpoint:test. Invoke explicitly before an update-testing cycle, or whenever the project's features, templates, or integrations have changed enough that the existing runbook needs refreshing.
disable-model-invocation: true
---

# /wp-checkpoint:test-plan-create

You study **this specific WordPress project** and produce or refresh one file: `testing-after-update.md`, at an explicitly-supplied location, an already-established existing location, or the session's captured output base directory (typically the project root — see `references/storage-preflight.md`). You do not run tests. You do not touch content, settings, or code beyond that one Markdown file. You never invoke `/wp-checkpoint:test` — that is a separate, explicit, future action for the human to trigger.

Read this whole file before acting. Then read `references/shared-conventions.md` and `references/common-pitfalls.md` in full before Step 2 — the first defines the test-ID format, priorities, statuses, evidence-source labels, severity scale, and update-type tags that Steps 3 and 4 depend on throughout; the second catalogues specific, recurring ways a discovery-based document ends up wrong, untestable, or quietly meaningless despite looking plausible. `references/discovery-checklist.md` and `references/test-catalogue-coverage.md` are mandatory reads at the points Steps 3 and 4 say to, `references/storage-preflight.md` is read in full before Step 4 writes anything, and `assets/testing-after-update-template.md` is read in full at Step 4, before you copy it. None of these six files is optional background reading — skipping any of them, or working from a paraphrased memory of one, produces a shallow, generic document, which defeats the point of this skill.

## Why documentation and testing are two separate skills

Preparing a test plan and executing it are different kinds of action with different risk profiles — one only reads and writes a Markdown file, the other can submit forms, create content, and call out to real systems. Keeping them as two separately-invoked skills means a human explicitly decides when actual testing happens, instead of it happening as a side effect of planning. Never blur this line, no matter how confident discovery leaves you feeling about what would happen if you tested something right now.

## Discovery boundaries — read before doing anything else

**You may:**
- Read source files and existing project documentation.
- Inspect relevant configuration without exposing secrets.
- Use read-only database and WP-CLI metadata queries.
- Read existing logs.
- Passively view existing public pages and accessible admin screens to understand layouts and available workflows.

**You may not:**
- Execute functional acceptance tests or test suites.
- Submit forms or actively exercise workflows to determine whether they pass.
- Create, edit, delete, publish, or schedule content.
- Upload files.
- Run cron jobs, queues, imports, or synchronization.
- Purge caches.
- Install dependencies or update software.
- Change settings, application code, or the database.
- Fix problems discovered during inspection.

The only intentional modification this skill ever makes to the project is creating or updating `testing-after-update.md`. The one narrow, explicitly-scoped exception: `references/storage-preflight.md`'s public-exposure gate may require creating the minimal empty destination directory (only if it doesn't already exist) and a single, inert, harmless probe file inside it, to test whether that destination is web-reachable. The probe file must be deleted immediately after that specific check regardless of outcome; if the gate fails, the directory is removed too, but only if this preflight created it and it's still empty — never a pre-existing file or directory. Nothing beyond that, and never before Step 4 actually needs to write the document.

**The principle behind all of this:** reading code, viewing a config value, or passively loading a page tells you something *exists* and roughly how it's built. It never tells you a feature *works* — that requires actually exercising it, which is `/wp-checkpoint:test`'s job, not this one. Never write a discovery finding into the document as if it were a completed test result.

## Step 1 — Locate the WordPress installation

Before anything else, capture the **output base directory**: the directory this session was actually working in at the moment this skill was invoked. Fix it now and don't silently recompute it later from wherever a subsequent `cd` or file read happens to land — see `references/storage-preflight.md` for the full rule, including why this is kept distinct from the WordPress root, the project root, the repository root, and this plugin's own directory.

Then try to find the WordPress root yourself: look for `wp-config.php` / `wp-load.php` at the working directory and in common layouts (project root itself, `app/public/`, `web/wp/` with a sibling `web/app/`, `public_html/`, `htdocs/`, a bare `wp/` subfolder). Identify the project root separately if it's a superset of the WordPress root (e.g. a repo that also holds build tooling, a design system, or deployment config alongside the WP install).

Ask the user for the path only if you genuinely cannot locate it this way. In the ordinary case the output base directory and the project root are the same path — that's expected, not something to second-guess.

## Step 2 — One concise intake message

Send a single message that:

1. Asks for the **standard site-access inputs**, skipping any already supplied earlier in this conversation:
   - Local website URL.
   - Local WordPress admin username and password — or confirmation that an authenticated browser session already exists, or that the user will log in manually.
   - Live website URL, for reference.
2. Offers these **optional context questions** in the same message, clearly marked optional, "unknown" or "discover it yourself" being acceptable answers that must not block progress:
   - Are there any known existing issues?
   - Are there intentional differences between local and live?
   - Which features or editorial workflows are especially important?
   - Are any pages, features, or integrations excluded?
   - Should the live site be used as the visual reference, or is another approved reference available?

Do not ask for anything you can discover yourself (WordPress root, versions, active plugins — see Step 3). Do not request live admin credentials by default; the live site is a read-only reference unless the user explicitly asks for something broader. Do not assume a local clone is disconnected from production email, webhooks, payments, FTP/CDN storage, or synchronization services — note what you find about these as a discovery item and a caution for later testing, rather than assuming isolation.

**Credential handling, for this and every later step:**
- Ask for credentials only when actually needed for access you don't already have.
- Never write a password, token, or other secret into `SKILL.md`/reference files (not applicable here, but also never into), `testing-after-update.md`, reports, command arguments, URLs, or logs/explanatory output.
- Never echo credentials back to the user.
- If the user has an authenticated session or says they'll log in manually, use that instead of requesting a password.

## Step 3 — Discovery

Read `references/discovery-checklist.md` in full now — it lists everything to study (environment/codebase shape, content model, page builders and template assignment, dynamic behavior, media, people/workflow, background/infrastructure behavior, language) and how to tell active functionality apart from inactive plugins, unused code, and unassigned templates. Follow it; don't substitute your own abbreviated version of it.

Inspect a representative example of every important page/template type and meaningful variation — not every content item. If browser, database, WP-CLI, or admin access is unavailable, continue with what evidence you do have and clearly record what you couldn't inspect. Map every important feature to its actual route, admin location, template, configuration, and an implementation reference (file path, option name, hook) — not a vague description.

## Step 4 — Write or update `testing-after-update.md`

**Resolve where this document lives, in the same order `references/storage-preflight.md` defines:**
- **If the user explicitly supplied a path**, that path is authoritative whether or not a file exists there yet. If it exists, you're in the "existing plan" branch below, at that location. If it doesn't, you're in the "new plan" branch below, at that location — never substitute the output base or a fallback result instead.
- **Otherwise** (no explicit path given): check for an existing plan already at the captured output base directory — if found, you're in the "existing plan" branch, there. If not, run a validated fallback search (the common layouts Step 1 checks: project root itself, `app/public/`, `web/wp/`, `public_html/`, `htdocs/`, a bare `wp/` subfolder) — if that finds one, you're in the "existing plan" branch, there. If neither finds anything, you're in the "new plan" branch, at the output base directory.

A plan found via any path above is used and updated in place; never moved, never duplicated elsewhere.

**Before writing anything**, read `references/storage-preflight.md` in full and pass its public-exposure gate for the location resolved above (its parent directory) — this document will contain site-specific findings (plugin versions, code locations, known issues), and most WordPress project roots are also the public webroot. If protection can't be confirmed, stop and ask the user for a non-public destination rather than guessing one.

You are now in exactly one of these two cases — they are mutually exclusive, and the wrong one would overwrite real content with a blank template or vice versa:

**New plan** (resolution above found nothing — no file exists yet at the resolved location): read `assets/testing-after-update-template.md` in full, then — only after the exposure gate above has passed — copy it to the resolved location as `testing-after-update.md` and fill in every placeholder that represents this project's own content with real findings, preserving actual UI labels, URLs, filenames, field names, and code identifiers exactly as you found them. The template already implements the required structure (Sections A–I below); don't restructure it, and don't skip a section because nothing came to mind quickly — work the checklists first. Preserve the generic format/vocabulary notation in the "Test case card format" block and in Sections G/H exactly as the template has it (see Step 5) — that notation is not project content to fill in.

Do not invent an example or a plausible-sounding expected result merely to fill in the template. Where you cannot establish what the correct or intended behavior actually is, say so: write the test case as far as you can (starting point, actions, evidence to collect), set its **Expected-result basis** to **Requires clarification or runtime confirmation**, and describe the specific uncertainty instead of guessing an answer. A generated document with a confident-looking but fabricated expected result is worse than one that honestly says a question is open.

**Existing plan** (resolution above found one): read it fully first, before writing anything. Review and improve it in place rather than starting over — preserve accurate information and keep existing test IDs stable (see `references/shared-conventions.md`). Treat the recorded versions/environment details as a stale snapshot to refresh, not as still-current facts. If a previously documented feature no longer exists, mark its test case `REMOVED` (with date and reason) instead of deleting it. Never adjust a documented expected result just to make a check look like it would now pass — flag the discrepancy in Section I instead. **Never copy the blank template over an existing plan** — the template is only ever used in the New plan case above.

The required sections, and the rules specific to each:

- **A. Purpose and operating instructions** — already written into the template; keep it, it's what stops a future reader from mistaking this document for completed results.
- **B. Site and environment profile** — local/live URLs, project root, WordPress root (if different), discovery date, versions, active theme/plugins/MU-plugins/drop-ins, permalink structure, architecture notes, local-vs-live differences, and limitations (unavailable integrations, intercepted email, missing licenses, PHP version differences, production-only cache/CDN layers — mark genuinely unknown items as unknown, don't guess).
- **C. Feature and representative-page inventory** — one row per important feature: representative URL/admin location, template/component, variations, dependencies, an implementation/config reference, and an evidence-source label (defined in Section G of the document itself). For every feature that submits data or sends a notification, identify now — not later — exactly which plugin/widget renders it, where its data actually goes (a persistent entries store, or nothing beyond an email), and the literal destination(s) a submission would reach (see `references/common-pitfalls.md` #4). Separate known issues from intended behavior explicitly; where you can't tell which it is, say so rather than guessing.
- **D. Priorities and update-impact matrix** — assign P0/P1/P2 to every test ID (definitions in Section G of the document itself), tag each with the update type(s) it's sensitive to (including `php`/`env` on AJAX/REST/cron/cache/technical-behavior cases, not only on the obvious log-review case — a runtime/PHP update changes code execution paths across every active plugin, not just what's visible on a page), mark the essential smoke subset, and state the broader-coverage rule for major/simultaneous/uncertain-impact updates, explicitly naming PHP/runtime/environment updates as needing more than a log-review case alone. Narrowing to targeted coverage must never silently drop the smoke subset.
- **E. Preconditions for future testing** — a checklist of *future* prerequisites (environment, update details, accounts/roles, test data, known issues, pre-update evidence, integration isolation, cleanup needs). Fill in what's actually knowable now (which roles exist, which integrations would need isolation, which test data is available) — but leave every checkbox unchecked; confirming them is `/wp-checkpoint:test`'s job at the start of a run, not something to mark done during creation.
- **F. Detailed test catalogue** — the bulk of the document. **Before drafting this section, read `references/test-catalogue-coverage.md` in full.** It is the specific, required coverage list (frontend structure/content, navigation/interaction, media, visuals/responsiveness, admin/editorial workflows, technical behavior) with the exact items to evaluate for applicability — do not compress it into generic instructions like "test the frontend" or "check responsiveness." Every test case uses the card format shown in the template (stable ID, feature+priority, update types/dependencies, environment/role/prerequisites, exact starting URL or admin location, suitable test data, numbered actions, specific observable expected result and its expected-result basis, evidence to collect, cleanup, limitations). Tag each expected result with one of the three evidence-source labels defined in Section G, the same labels Section C uses — don't present a guess as if it were an observed or derived fact. Put anything inapplicable or unresolvable in the Applicability/Gaps subsection at the end, with a reason — don't pad the catalogue with speculative cases for things that aren't there, and don't silently drop something that is.

**Before you write a single card, read `references/common-pitfalls.md` in full** (you should already have read it before Step 2 — re-read it now if any time has passed). It is not supplementary advice: every item in it has caused a real, plausible-looking test case to be wrong, untestable, or silently unfalsifiable. Check every card you write against it, especially: don't skip core editorial workflow or scheduled publishing just because you didn't observe them in use; don't call a feature "active" from schema/table presence alone, check its authoritative mode flag; don't assume a caching plugin's own "enabled" setting means this environment can reproduce the behavior; don't let a fallback/degraded path quietly become the accepted expected result when the primary behavior is supposed to be active; don't point a fixture at a dependency that can't actually produce what's needed; and make any dynamically-selected content's real mapping logic concrete rather than describing it vaguely.
- **G. Execution procedure and result definitions** — already written into the template, and it inlines the *entire* shared vocabulary (test-ID format, priorities, statuses, evidence-source labels, severity scale, issue classification, issue IDs, cause classification, role-required labels, update-type tags) directly into the document — keep all of it. This is deliberate: `testing-after-update.md` lives in the project root, not inside either skill's folder, so a pointer to `references/shared-conventions.md` would be a dead link for anyone reading this document on its own. Every test case you write must be at status **NOT RUN** — the document you produce contains zero completed results, however thoroughly you just inspected the project.
- **H. Future report template** — already written into the template; keep it, so `/wp-checkpoint:test` has a report shape tied to this specific document rather than drifting from some separate template. It now describes a self-contained `report-<date>[-N]/` directory (Markdown + DOCX + screenshots + a log excerpt), not just an inline chat block — if you ever touch this section, keep it in sync with `assets/report-template-fallback.md` and `references/reporting-format.md` in the `test` skill folder, the same way `shared-conventions.md` must stay identical across both skills.
- **I. Gaps and maintenance** — list unresolved questions and missing evidence, and state when this document should be revisited (feature/template/route/integration/dependency changes). Reiterate the stability rule for test IDs and expected results.

## Step 5 — Review, then report back

**Before finishing, reopen `testing-after-update.md` from its actual saved destination on disk** (not the in-memory draft you were just writing) and run every check below against that saved file. This catches a write that didn't land where intended, a partial write, or an edit that didn't apply cleanly — don't assume the file on disk matches your draft because the write call didn't error.

Review the saved document for completeness, internal consistency, valid test-ID references (every ID in Section D's matrix exists in Section F and vice versa), and actionable instructions (no vague steps). Specifically confirm:
- No `EXAMPLE —` row or card remains anywhere in the document. No unresolved `<...>` placeholder remains in any *actual* feature row, test case, or other filled-in project content — every real piece of content must be concrete. This does **not** apply to, and you must not "fix" away: Section E's intentionally-unchecked confirmation checkboxes; the generic `<TEST-ID>` / `<Short title>`-style format definition in Section F's "Test case card format" block (that block documents the shape — it is never itself a card); or Section G's and Section H's own vocabulary and report-template notation (e.g. `<AREA>-<NNN>`, `ISSUE-<NNN>`, `<YYYY-MM-DD HH:MM>`, `<n>`) — those are deliberately generic, meant to stay exactly as written for `/wp-checkpoint:test` to fill in later, and are not something this skill resolves now.
- Every test case's status is **NOT RUN** — none fabricated as PASS/FAIL/BLOCKED/NOT APPLICABLE.
- No expected result was invented to fill a gap — anything uncertain is tagged **Requires clarification or runtime confirmation** and listed in Section C's or Section I's open items, not presented as settled fact.
- Every card checked against `references/common-pitfalls.md` — none of this document's cards silently accept a degraded/fallback outcome as equally valid to the intended one, point a fixture at a dependency that can't produce it, describe a dynamically-selected result only vaguely, collapse an unresolved acceptance question into a plain PASS/FAIL, or default an unresolved acceptance question to NOT APPLICABLE instead of BLOCKED (common-pitfalls.md #9 — unknown intent blocks judging the check, it doesn't exempt it).
- Every test ID's **priority and update-type tags match exactly** between its Section D row and its Section F card — not just that the ID exists in both. This is a common, easy-to-miss drift: fix it at the source (`common-pitfalls.md` #13) by changing both together next time, but check it explicitly here too.
- The essential smoke checks line in Section D lists exactly the IDs marked `Smoke: Y` in the matrix, and no others.
- Every "Depends on" reference in Section F names a real test ID that exists elsewhere in this document.

This is a documentation review, not application testing.

Return to the user:
- The document's path.
- A brief coverage summary (what areas are covered, roughly how many test cases, by priority).
- Important gaps or access limitations you hit.
- An explicit statement that no tests were executed and the document contains no completed results.

Do not invoke `/wp-checkpoint:test`. If the user wants to run the tests now, tell them to invoke it themselves.

## Reference files

- `references/shared-conventions.md` — test ID format, priorities, statuses, evidence-source labels, severity scale, issue classification, issue IDs, cause classification, role-required labels, update-type tags. **Read in full before Step 2.** This is the shared contract with `/wp-checkpoint:test`; it is identical to the copy in that skill's folder. Its content is also inlined into Section G of every generated `testing-after-update.md`, so the generated document never depends on this file being reachable.
- `references/common-pitfalls.md` — **read in full before Step 2, and again before writing Section F.** Specific, recurring ways a plausible-looking discovery document turns out to be wrong or untestable.
- `references/discovery-checklist.md` — **read in full at Step 3**, before discovery.
- `references/test-catalogue-coverage.md` — **read in full at Step 4**, before drafting Section F.
- `references/storage-preflight.md` — **read in full before Step 4 writes anything**; the output base directory and the public-exposure gate, shared with `/wp-checkpoint:test`.
- `assets/testing-after-update-template.md` — the document skeleton. **Read in full, then copy it** as the starting point at Step 4.
