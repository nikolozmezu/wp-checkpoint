# Execution and Evidence

Read before executing checks. The same execution, isolation, and evidence rules apply
to normal, before, and after modes. `shared-conventions.md` owns status decisions,
lifecycle, and scope-selection rules; `before-after.md` adds checkpoint mechanics.

## Capability preflight

Use read-only checks to establish the capabilities actually available in this session.
Do not install tools, change settings, or start functional tests as part of preflight.
Record availability, alternatives, and affected test IDs in the report:

| Capability | Determine | Consequence when missing |
| :-- | :-- | :-- |
| Browser interaction and screenshots | Accessible local site; usable role/session; actual interaction and capture support | BLOCKED for checks needing unavailable interaction; missing capture alone is an evidence limitation if the documented result can still be directly verified |
| Project / WordPress metadata | Readable source; WP-CLI or permitted database/admin alternative | Use an available equivalent; mark unverified inventory unknown and block only checks requiring unavailable access |
| Logs and network evidence | Readable relevant sources and request visibility | Record the missing source; block checks whose required evidence cannot otherwise be established |
| Selection / continuation | Python helpers and current verified non-secret context | Manual ordinary testing remains possible; disclose unavailable automatic selection or safe continuation |
| Visual differences | Pillow and comparable recorded screenshot contexts | Keep raw evidence; state optional visual review unavailable, never infer a regression from missing comparison |
| DOCX authoring | Existing authoring/export capability and a way to inspect its output | Continue testing and Markdown; announce capability unavailable, not export failed |

An installed tool is not proof of access or a working integration. Distinguish missing
tools from missing credentials, an unreachable site, and an unconfirmed expected result.
Never claim unavailable capabilities were used. If no meaningful checks can run,
produce an honest blocked report after the storage gate, rather than a fabricated pass.

## Scope and execution order

Use `select_tests.py` and `run-state.md` to compute the selected set/order from the
saved plan when available; otherwise disclose the manual application of the shared
selection algorithm. In brief: full selects all ACTIVE IDs; smoke selects the smoke
subset and its prerequisite closure; targeted selects update-tag matches and their
documented downstream effects, their prerequisite closure, and smoke with its
prerequisites. Explicit user exclusions win and must be visible as coverage limits.
Do not expand downstream from smoke alone and accidentally turn targeted into full.
REMOVED rows remain in the full matrix, unselected NOT RUN with their date/reason.

For runtime/environment updates, also apply the shared execution-layer safeguard:
missing php/env tags must not silently exclude server-side or infrastructure checks.
Read a selected card's Fixture setup and State after cleanup before using a dependency.
Verify the required state still exists after prior cleanup; use only a documented,
authorized setup to recreate it. If the plan cannot establish the fixture, report the
specific plan gap and BLOCKED check rather than improvising a transaction or changing
the canonical plan.

Use `Yes/full`, `Yes/smoke`, `Yes/smoke-dependency`, `Yes/targeted-tagged`, or
`Yes/targeted-dependency` as appropriate; explain prerequisite selection in the reason
field (including smoke prerequisites). Record `No` plus the specific reason for every
unselected ID. Do not use NOT APPLICABLE to represent a scope exclusion.

1. Establish environment/update context and which plan preconditions are met.
2. Complete capability preflight, storage gate, and the saved report initialization.
3. Follow the computed dependency order, prioritizing selected smoke and its
   prerequisites. An explicit limited retest never adds unselected smoke. A missing dependency reference is a plan gap; a cycle
   must not cause repeated traversal or improvised setup. Block only affected checks
   when their actual prerequisites cannot be arranged.
4. Record each assessment/attempt and update the saved result row and cleanup state as
   it happens. In before mode update `checkpoint.json` too.
5. Restore disposable content and temporary state under each card's cleanup rules.
6. Finalize technical findings, the human DOCX, and saved-artifact verification.

## External-service isolation and production

Before a form submission, notification, order, upload/delete, job, or other action
that could reach outside the local copy, check plan Sections B/C/E and confirm the
actual destination and isolation now. Suitable proof includes a mail catcher, test
payment gateway, sandbox API keys, or a disabled outbound webhook. Stored config or
a local URL alone does not prove the action is isolated.

If the destination is unknown, is a real address/service, or isolation is unverified,
mark the check BLOCKED with that specific reason. Never send real messages, execute
real payments, delete shared remote media, or trigger production synchronization
through a local clone. Do not alter an integration merely to make the test possible
unless the plan documents the temporary test step and the user's scope authorizes it.

Live remains a read-only reference. If the user requests test actions on production,
establish the specific actions, affected data, and cleanup scope and obtain any still
missing explicit authorization before those actions. Reuse authorization already given
for that scope; do not ask again simply because the mode changed.

## Observations, attempts, and status

PASS requires actual execution and direct observation of the documented result.
Source inspection or a plausible configuration cannot prove a click, layout, upload,
scheduled event, or cache behavior passed. Missing browser interaction blocks the
checks that require it; source reading is not a substitute.

Record all valid attempts in order with time, status, concrete observation, and
evidence. Any valid FAIL makes the final test status FAIL, even if a retry passes;
retain both and classify the changing outcome as Intermittent. Otherwise apply the
status rules in `shared-conventions.md`. Do not quietly discard a failed attempt as
invalid; describe an actually established setup error if an attempt cannot test the
documented requirement, and keep its observation for traceability.

An unclear documented expected result is a plan gap, not permission to define success
from what happened. Record the question and block the affected acceptance judgment.
Confirm genuine environment non-applicability before using NOT APPLICABLE; uncertain
access, isolation, or prerequisites are BLOCKED. One blocker does not stop independent
checks.

For delayed/asynchronous results, follow the card's prerequisites and observation
deadline. Confirmed prerequisites plus an elapsed deadline without the transition is
FAIL; a named prerequisite that cannot be arranged is BLOCKED. If the run ends before
the deadline, use NOT RUN with the time-budget reason and preserve the partial
observation in Markdown. In a checkpoint, leave its terminal attempts empty; record
the unfinished observation in the test reason/limitations. Do not invent a terminal
outcome from an incomplete observation.

## Evidence collection

Use available evidence appropriate to the behavior: actual screenshots/UI state,
requests and responses, relevant attributed log excerpts, resulting content/job state,
or measurements with an established baseline. For each observed issue, capture its
visible consequence when possible. If no meaningful screenshot is available, record
the precise reason and use the real available evidence; never create a substitute image
or show a healthy screen as proof of a failure.

Save evidence only inside the storage-gated report bundle. Use descriptive names such
as `HOME-001-desktop.png` or `ISSUE-003-checkout-error.png`. In after mode, copied matched
before images belong in `screenshots/before/` and current images in `screenshots/after/`;
gate those actual destinations too. Keep the source checkpoint and report immutable.

Remove or avoid secrets and unnecessary personal data in every saved artifact, including
screenshots, URLs/query strings, network payloads, and checkpoint metadata. Evidence
must remain truthful after redaction; explain material omissions. Do not publish the
bundle externally.

In every mode, record the current run's start time/timezone and each readable log's
starting offset or equivalent boundary before the checks that can generate entries.
Account for rotation/truncation and retain request correlation where timestamps are
ambiguous. Without a reliable current-run boundary, report attribution as unverified.
Attribute a log error to this run only when its timestamp or request identifies this
run. Record source and timestamp range, and save relevant excerpts rather than a whole
raw log. Older errors may be separate context, not newly attributed failures. If no
relevant log evidence exists, state that; do not invent log contents.

For cache invalidation, observe the dated disposable change before any manual purge.
Purging first hides a failed automatic-invalidation behavior. Purge afterward only if
the documented cleanup requires it and the local scope permits it. Likewise, confirm
which configured action actually ran rather than assuming stored fields prove execution.

## Report integrity and cleanup

Use issue classifications from `shared-conventions.md`. A confirmed regression needs
comparable prior passing evidence for the same requirement; without it report a new
issue of uncertain origin, a known issue, or an intermittent finding as established.
Version changes alone do not prove causation.

Account for every plan ID, including unselected, removed, blocked, and unreached IDs.
Keep findings, blocked checks, and unresolved preconditions distinct. Never change the
canonical plan or apply a proposed fix during execution. Record precisely any created
item, changed setting, or other temporary state that remains, with the manual cleanup
needed. A partial or blocked run must never read like a fully verified site.
