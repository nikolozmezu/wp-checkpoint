# Execution and Evidence — Detail Reference

Read this before you start executing checks. It expands on the execution rules in SKILL.md; SKILL.md has the hard boundaries, this file has the operational detail.

## Execution order

1. Establish environment, update context, and prerequisites — confirm the base URL, what was updated (and from/to which versions, where discoverable), the desired scope, and which preconditions from the document's Section E are actually met right now versus BLOCKED.
2. Pass the public-exposure gate and initialize `wp-update-report.md` (Step 3) — the full result matrix pre-populated from every plan test ID, selected ones marked NOT RUN and ready to be updated, unselected ones marked NOT RUN with Selected: No and the scope reason. This happens before any check runs, not after.
3. Run essential smoke checks (the P0 "Smoke" subset from Section D) — always, regardless of scope — updating each one's matrix row as it completes.
4. Execute the selected expanded coverage (full / smoke-only / targeted, per the agreed scope) plus — for a targeted run — the dependencies and cross-feature effects that the document's Section D matrix ties to the updated component. A targeted run is never just the one updated component in isolation; follow its documented dependencies. Keep updating the matrix as you go.
5. Collect findings and limitations as you go — don't defer evidence-gathering to the end, you'll lose the specifics.
6. Clean up test changes — delete/restore any disposable test content or temporary state you created, per each test case's Cleanup field. If a cleanup step can't be completed, don't silently move on: record precisely what's left in place so it reaches the report's Cleanup status section and a human can finish it.
7. Finalize the report (Step 6) — the issue write-ups, the prioritized index, reconciled result counts, the DOCX, and the read-back verification before reporting success.

## Before an action that could reach outside the local copy

A local URL is not proof of isolation. Before submitting a form, triggering a notification, placing a test order, or anything else that could call out to a real external service, check what the project's Section B (environment profile), Section C (feature inventory), and Section E (preconditions) say about that integration, and whether it's been confirmed sandboxed (test API keys, a sandboxed payment gateway, a mail-catcher instead of real SMTP, a disabled webhook). The card should already name the literal destination (an email address, a named external service) — if it doesn't, or if the destination it names is a real address/service rather than a confirmed sandbox, don't submit and don't guess it's safe. If isolation or the destination isn't established, treat the check as **BLOCKED** (reason: "external-service isolation not confirmed" or "submission destination is a real address/service, not sandboxed") rather than guessing it's safe. Never send a real message, place a real payment, delete shared remote media, or trigger a production sync from a local clone.

If the user ever asks to run checks against the live/production site with admin access (not just read-only reference viewing), treat that as a higher-risk, hard-to-reverse action on a shared system: confirm the specific scope and get explicit confirmation before proceeding, the same way you would before any other action on shared production infrastructure.

## When something is unavailable

Mark the specific test ID **BLOCKED** and state exactly what was missing (a credential, a tool, a precondition, network access to an integration) — then continue with every other check that doesn't share that same blocker. One missing piece should never stop an entire run.

## Collecting evidence

Use whatever of these are actually available in this session; don't claim a form of evidence you didn't actually produce:

- Screenshots (when browser automation is available) for visual/interactive checks.
- Actual observed UI behavior (what happened on click/submit, not what the code implies should happen).
- Network requests/responses (status codes, payloads) for AJAX/REST checks.
- Relevant PHP/WordPress/application log excerpts — written or changed during *this* run.
- Resulting content or job state (e.g. the post that was actually created, the cron event's last-run timestamp) rather than just "the setting looks right."
- Measurements, only where Section B/D establishes a baseline to compare against.

Save non-trivial evidence (screenshots, log excerpts) into this run's `report-<date>[-N]/screenshots/` and `report-<date>[-N]/log-excerpt.txt` — the output base directory, directory layout, and the public-exposure gate you must pass before creating it are all in `references/storage-preflight.md` (gate) and `references/reporting-format.md` (layout), both handled at Step 3, before execution starts. Reference the file paths from the report rather than pasting large blobs inline or publishing them anywhere external — this is client/production-adjacent data and should stay local to the project.

### Attributing log errors

Only attribute a log entry to this run if its timestamp falls inside the run, or you can otherwise tie it to a request you just made. Don't assume an error sitting in a log file was caused by the update just because you happened to be looking at the log today — note older entries separately if they're relevant context, but don't fold them into this run's findings.

### Retries

If a check fails once and passes on retry, keep both results — note the failure as an observed intermittent result, don't silently replace it with the passing retry. An intermittent failure is itself a finding.

## Time-dependent or asynchronous checks

When a card's expected result only resolves after a delay (a scheduled transition, a queued job), follow its defined observation deadline and prerequisites exactly — don't invent your own judgment call in the moment.

- **BLOCKED** applies only when a specific, named prerequisite could not be confirmed or arranged (e.g. a required setting couldn't be checked, or there was no way to generate the triggering event within the run). "The environment might just be slow" is not a prerequisite — name the actual missing thing.
- **FAIL** applies when the prerequisites were confirmed met and the defined deadline passed without the expected transition. Do not soften this into BLOCKED just because the cause isn't obvious.
- If the run's own time budget ran out before the deadline was reached, report that specific check as **NOT RUN**, not a guessed BLOCKED or FAIL.

A stored field's value is also not proof an action tied to it is active (see `common-pitfalls.md` #10 in the creation skill) — when evidence depends on which action actually ran, confirm the real active-actions list or documented default, not just that a plausible-looking field value exists in storage.

## Cache invalidation checks

Follow the card's steps in the order written: observe a disposable, dated content change *without* manually purging the cache first. Purging before observing hides a failed automatic-invalidation behavior — if you purge first and then see fresh content, you've learned nothing about whether invalidation actually works on its own. Purge only afterward, as cleanup, if the environment needs it reset.

## What counts as PASS

Only actual execution plus direct observation of the documented expected result. Static code inspection, however confident it makes you feel, cannot establish that a browser interaction, a visual layout, an upload workflow, or a scheduled job actually passed — that requires actually doing it and watching what happens. If browser automation isn't available in this session, say explicitly that visual/interactive checks in scope could not be verified this way — don't claim a PASS for them based on source inspection, and don't quietly skip them without reporting the gap.

## Regression vs. new issue vs. known issue

Use the issue classification definitions in `references/shared-conventions.md` exactly. In short: you need actual before/after evidence to call something a "confirmed regression" — absent that, it's a "new issue of uncertain origin," which is still worth reporting, just not over-claimed.

## Report integrity

- Account for every test ID in the project's plan, not only this run's selected scope — including ones you didn't get to, and including ones deliberately never selected (Selected: No, Status: NOT RUN, the specific scope reason — never NOT APPLICABLE for those). There's no silent default; an ID with no explicit status is a bug in the report, not an implicit PASS or an implicit exclusion.
- Never change a test case's documented expected result to make an observed failure look like a pass. If you think the expected result in `testing-after-update.md` is wrong, say so in the report as a flagged discrepancy — don't edit the canonical document during execution.
- A partial run (smoke-only, or blocked on several IDs) is reported as a partial run. Never phrase a partial run's conclusion as if it were a full pass.
- Incomplete cleanup is reported, never silently left out. If anything created or changed during testing is still in place when you finish, the Cleanup status section must say exactly which item, and what a human needs to do to finish it.
