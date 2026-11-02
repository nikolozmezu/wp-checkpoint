# Evidence-backed drafting and semantic review

Use this when authoring cards, then review the whole saved plan against its sources before delivery. Structural validation establishes document consistency; this review checks whether the instructions and expectations follow from the actual project. Neither establishes that the site passed a test. Stay within discovery's read-only boundaries.

## Evidence required while drafting

Every ACTIVE schema-3 card records:

- **Execution layers:** comma-separated `php`, `browser`, `infrastructure`, `external`, `static`, or `unknown`, as established by its actual execution path. A browser-visible journey may also execute PHP or contact an external service. `static` describes a file/config-only check, not an excuse to ignore server execution in the feature being tested. For `unknown`, state the specific uncertainty in **Known limitations / dependencies** and retain conservative coverage.
- **Implementation evidence:** a verified source file and line/definition, hook, option, rendered configuration, or observed request reference that establishes the claimed behavior. Include environment and observation time where they matter. Name the relevant value/branch, not merely the plugin directory. If evidence is inaccessible, write `Unresolved: <specific reason>` and identify the acceptance question it leaves open; do not invent a citation.
- **Fixture setup:** concrete, safe steps that establish the required state for this card, or an explanation that an identified existing example suffices. Default to independent setup/recreation. A shared fixture must name its owner, consumers, lifetime and deferred cleanup arrangement.
- **State after cleanup:** the state left after every step and cleanup, including any deliberately retained shared fixture and who removes it. Match this with the Cleanup field and later consumers.

Retired historical cards need not acquire invented implementation facts. Keep their lifecycle, removal record and NOT RUN status intact.

Separate three questions: what implementation/configuration exists, what it currently does, and what behavior is intended. Code can establish a mechanism without settling business acceptance. An unresolved criterion stays explicitly unresolved, even when the resulting plan is structurally valid.

## Review the saved plan, not the author's summary

Use an independent read-only reviewer when available. Give it the saved plan, relevant project sources/access and these review instructions, without steering it to the author's preferred conclusions. Otherwise perform a separate review pass and disclose that mode. Review all ACTIVE cards; sample representative content during discovery, not a sample of cards during this review. Do not launch functional tests to resolve an authoring gap.

For each card, inspect its cited implementation/configuration and answer these questions:

1. **Does the evidence support the claim in this environment and time?** Check activation and assignment against a current authoritative source and its scope. Site-level `active_plugins` absence alone does not settle network activation; follow the discovery checklist's single-site/network check before claiming overall inactivity. A cached footprint, old log or missing asset does not establish current activation/inactivity. Keep confirmed current observations separate from historical or unverified incidents; a static suspected cause is not a confirmed current failure.
2. **Does the actual path match the proposed action?** Trace the caller, configuration and handler for endpoint/method/action, validation, redirects and response expectations. Do not substitute a familiar framework URL or default for the implementation. Inspect configuration branches that can legitimately change the outcome. An inaccessible source becomes an explicit gap, not a guessed assertion.
3. **Does every expected clause have a step that can observe it?** Map positive, negative, permission, persistence and timing branches to numbered steps and suitable data. For example, an expected rejection needs an actual rejection-triggering step; a saved-state expectation needs a reload/reopen step. Remove unsupported claims or supply justified steps. Do not claim a whole branch was covered by checking markup alone.
4. **Will the fixture still exist when the consumer starts?** Read every dependency through its final step and cleanup. Compare the resulting state with the consumer's setup, role and prerequisites. Prefer recreation in the consumer; shared state requires an explicit lifetime and cleanup owner. Check that reduced scopes still have a valid setup path. A dependency edge is not proof a completed/published/authenticated fixture exists.
5. **Will update selection reach the affected behavior?** Infer execution layers from the source path, then reconcile layers/tags and matrix/card metadata using the shared contract. PHP/runtime impact includes server execution behind public pages, editing, APIs, scheduled work and other active features, regardless of which product category they belong to. Infrastructure changes include affected transport, storage, cache and scheduling paths. Do not rely on a prose claim of broad coverage when the selection metadata omits those checks. Unknown layers or impact require a stated limitation and conservative scope, not guessed tags.
6. **Can the verdict be judged without inventing intent?** Verify that the expected result has a stated basis and a discriminating outcome. “Report whatever happens” can describe observation, but does not establish a PASS/FAIL criterion. Missing acceptance criteria mean future BLOCKED; confirmed non-applicability and deliberate scope exclusions have their separate meanings.

These are source-backed questions, not a checklist to self-certify from the card's wording. Record unresolved IDs and the precise unavailable source, fixture or criterion. Correct author-introduced contradictions in the plan before describing it as reviewed. Never change application code, configuration or acceptance criteria to make the plan seem ready.

## Record two separate review outcomes

In Section I, complete the template's four fields:

- **Structural validation:** the validator result, or manual-check method/limits when unavailable. Record errors honestly; it does not validate factual truth.
- **Semantic review:** `Reviewed`, `Reviewed with gaps`, or `Needs revision`, plus independent-review/separate-pass mode and date. `Reviewed` means the authoring review was completed against available sources, not guaranteed correctness or a test PASS. `Reviewed with gaps` permits specifically documented inaccessible evidence or unsettled requirements. Self-authored contradictions or unreviewed active cards require `Needs revision` until corrected/reviewed.
- **Reviewed test IDs:** the actual ACTIVE IDs checked, and any IDs still unreviewed. Do not substitute “all” unless every active card was covered.
- **Source-check limitations:** affected IDs, missing evidence and its consequence for execution/acceptance; use None only when there are no such limits.

Before review starts, use honest provisional values (Structural validation: Not yet performed; Semantic review: Needs revision — not yet reviewed; Reviewed test IDs: None), not success labels or unresolved template placeholders. Replace them with the actual outcomes.

After corrections, reopen the saved plan, recheck affected source claims and dependent cards, and rerun structural validation if the structure changed. An honest incomplete plan is deliverable with its gaps and status; do not equate a validator success or a large test count with readiness. The final reply distinguishes structural results, semantic review coverage and unresolved execution gaps, while confirming no tests were run.
