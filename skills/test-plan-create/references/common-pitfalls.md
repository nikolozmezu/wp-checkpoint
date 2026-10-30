# Common Pitfalls — Read Before Finalizing Section C/D/F

These are specific, recurring failure patterns found in real discovery runs. Each one looks like a reasonable shortcut in the moment and produces a plausible-sounding document — but the resulting test case is wrong, untestable, or quietly stops meaning what it claims to mean. Check your draft against every item below before you finish Section F.

## 1. Absence of observed use is not evidence a capability is unneeded

Finding zero examples of something in a snapshot (no future-dated posts, no custom blocks, no large titles) tells you it hasn't been *observed*, not that it's irrelevant. A capability that ships with WordPress core, the active theme, or an active plugin by default is in scope by default, whether or not you happened to see it used. This applies especially to:
- **The ordinary content lifecycle** (create → save → reopen → preview → publish, and edit by each relevant role) — this applies to every project with any editable content type, regardless of whether the site is built entirely through a page builder or uses custom blocks. "No custom Gutenberg blocks were found" is a reason to skip a block-editor-specific case, not a reason to skip editorial workflow entirely.
- **Scheduled (future-dated) publishing** — standard core capability, available by default to any role that can publish. Zero `future`-status content in a point-in-time snapshot does not establish that scheduling was never used — a post scheduled and later published no longer carries `future` status by the time you're looking (see #12 below), so the honest statement is that there's no *current* evidence of it, not that it "hasn't been used yet." Either way, it's not broken, unsupported, or out of scope by default. Include it (a modest priority is fine if there's truly no evidence of active use) and say plainly in the card that no current usage was observed, without claiming it was never used.

## 2. Schema/table existence is not the same as the authoritative, active mode

Some features ship a multi-mode storage or processing system where the newer mode's database objects get created ahead of the mode actually being switched on (WooCommerce's High-Performance Order Storage is the canonical example: its tables can exist and even hold synced data while the feature flag that makes them *authoritative* is still off). Before describing a feature as "active," check the specific option/flag that controls which mode is live — not just whether the newer mode's tables exist, have ever been created, or happen to contain rows. Name all four of these separately when they differ: the plugin/code version, the database schema version, the configured/flagged mode, and what you directly observed happening. If a table that should hold live data is actually empty, say that plainly — don't let an older "this exists so it's real" inference stand uncorrected.

## 3. A plugin's own "enabled" setting is not the same as the environment's ability to reproduce it

A caching plugin (or similar environment-dependent feature) showing "enabled" in its own settings does not mean your current environment can actually exhibit the behavior — a plugin-level cache may depend on a server module (e.g. a web-server-level page cache) that a local dev stack doesn't run at all, even though the plugin considers itself configured and active. Verify the actual observable behavior (response headers, timing, before/after content) rather than inferring it from the setting. If the environment genuinely can't reproduce a production-only layer, record that explicitly as a limitation (and the eventual test result as BLOCKED with that reason) rather than either assuming coverage exists or generating a false FAIL.

## 4. Identify a submission's real destination during discovery — before any test case reaches the point of submitting

For every form that sends a notification, stores an entry, or integrates with an external service, determine during discovery (not left for the testing skill to discover mid-run): which widget/plugin actually renders it (don't assume a form is built with whichever forms plugin happens to be the only one active — site builders frequently use a page builder's own native forms module instead); where its data actually goes (a persistent entries table you can revisit, or email-only with nothing retained); and the literal destination(s) — real email addresses, or the specific external service/add-on — a submission would reach. If you can't pin this down with confidence, say so explicitly in the card rather than leaving "which form/provider this is" as an open question that only gets resolved by actually submitting it later.

## 5. A degraded or fallback path must not silently become the "new" expected result

When a feature's behavior is gated by a configuration flag (a plugin option, a conditional `require_once`, a feature toggle), establish the flag's actual current value during discovery. If the feature is enabled and intended to be active, the expected result is the feature working correctly — a failure to activate is a FAIL, full stop, not a fallback-is-also-acceptable outcome. Only describe a fallback/degraded path as the expected result when you've separately confirmed the primary feature is *intentionally* disabled (a deliberate, documented configuration choice). If you cannot determine the flag's value, mark the expected result as unresolved (`Requires clarification or runtime confirmation`) instead of writing an expected result that accepts either outcome — accepting either outcome means the check can never actually fail, which defeats its purpose.

## 6. A test case's fixture must be genuinely producible by the steps you wrote

Before finalizing a card's Test data / Starting point, confirm the dependency or fixture-creation method you're pointing to can actually produce what this specific case needs — not something adjacent to it. A card that says "create the needed record via case X" is broken if case X only produces a partial precursor (e.g. adding an item to a cart is not the same as producing a complete order to view in an order-detail screen). Where no valid, low-risk path to a real fixture exists yet, either find one (an admin screen that can create the record directly and in isolation, bypassing a riskier public-facing flow) or mark that specific portion BLOCKED with the precise missing piece, rather than cross-referencing an inadequate mechanism and calling it done.

Relatedly: a fixture's status must match what the test's role/environment actually grants. Don't write a draft-status fixture into a check whose Environment/Role is Anonymous — a draft isn't visible to anonymous visitors by definition. Use a published disposable fixture (with cleanup) or change the check to an authenticated preview.

## 7. Make dynamic/computed content checks deterministic — find the real selection logic

For any feature where a form or input dynamically selects different output content (a quiz, a calculator, a personalization rule), read the actual selection/mapping code during discovery — not just the hook that triggers it. The real mechanism is sometimes much simpler (or much different) than it first appears: it may key off the submitted answers, or it may key off something else entirely (e.g. which form was submitted, independent of the answers given). Document the real mechanism and the concrete fixtures/identifiers it implies (exact IDs, exact expected output posts/content) so the test case has one specific, checkable expected result — not a vague "the matching content for the submitted answers." If the mapping genuinely can't be established from available access, say precisely what's missing rather than writing a plausible-sounding guess.

## 8. Record the exact pre-change state before any modifying step, not just an intent to "revert"

Any card that reorders content, edits a shared/reusable template, or changes any persistent setting must have its steps capture the *exact* original value/order/state before changing it — not merely a promissory "revert the change" in the Cleanup field. "Revert" is only as good as the record of what to revert to. This matters most for manual drag-ordering, shared theme-builder templates, and site-wide options.

## 9. Observed configuration and approved acceptance criteria are different kinds of evidence

Confirming what's currently configured (a gateway disabled, a page missing) is a factual observation — record it as evidence on its own, independent of whatever verdict the check ends up with. Whether that configuration is *correct* — intentional catalogue-only operation, a known defect that should be fixed, or genuinely undecided — is a business/acceptance question this skill cannot answer on its own, and the two must never collapse into a single expected-result assertion.

Unknown business intent or missing acceptance criteria is a **blocker to judging the check, not a reason the check doesn't apply**:
- Use **BLOCKED** when acceptance cannot be assessed because the intended behavior itself is unresolved — name the specific unresolved question (e.g. "whether checkout completion is required has not been confirmed by the client"). This applies whether the observed configuration matches a prior baseline or has changed — a changed configuration is still BLOCKED, not FAIL, since there's no confirmed criterion to fail it against yet.
- Use **NOT APPLICABLE** only once a genuine scope exclusion has been affirmatively established — the client has actually confirmed catalogue-only operation, or stated another specific, settled reason this check doesn't apply. Intent being merely unknown is not the same as a confirmed exclusion, and must not default to NOT APPLICABLE.
- Never let either collapse into PASS (would wrongly imply the acceptance question is settled and satisfied) or FAIL (would wrongly penalize a configuration that later improves, or blame this run for a pre-existing condition whose correctness is still undecided).

Keep the configuration observation and the status verdict visibly separate in the write-up: report what's configured as its own piece of evidence every time, independent of whichever verdict — BLOCKED, NOT APPLICABLE, or eventually PASS/FAIL once criteria exist — the current state of knowledge produces.

## 10. A stored field's value is not proof that its action is active

Many systems (a page builder's form widget, a plugin's settings panel) keep a setting's input values on screen or in storage even when the feature that consumes them isn't currently selected or enabled — deselecting an action doesn't clear its fields. Before concluding "X will happen" from seeing a populated field for X, confirm the actual list of active actions/handlers (the real selector/toggle value, or, in its absence, the documented code default — read the relevant source if you need to), not just whether a plausible-looking value exists somewhere in storage.

## 11. Derive a negative/validation test case from the feature's actual field configuration

Don't write a generic "check that validation works" step. Read which fields are actually required and which have a type constraint (email, number, etc.), and write the negative case against those specific fields — "submit with field X blank" only means something if X is actually marked required in this project's stored configuration; a field that's optional here is not a valid target for a required-field rejection test.

## 12. A database snapshot shows the state at discovery time, not history

Don't phrase a finding using words like "never" or "ever" for anything before that snapshot — a post that was scheduled and already published, for example, leaves no `future`-status row behind, so "no `future` rows exist now" only means "not observed as of this snapshot," not "this has never happened."

## 13. Keep a test ID's priority and update-type tags identical in both places you record them

A test case's priority and update-type tags are recorded twice — once in the Section D matrix row, once on the Section F card itself. When you change either one for an existing test ID, change both in the same edit. Section D and Section F drifting out of sync on a shared ID is exactly the kind of error Step 5's review must catch.
