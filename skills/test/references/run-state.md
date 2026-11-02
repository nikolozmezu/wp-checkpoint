# Deterministic selection, continuation and fresh retesting

Read for every execution when Python is available. Helpers resolve from this plugin's
`scripts/`, not the WordPress directory. They perform bookkeeping only: they never
click, submit, create data, collect runtime metadata or establish a PASS. Storage-gate
all JSON/evidence destinations before writing. If Python is unavailable, disclose that
automatic selection/state protection is unavailable and use the existing documented
manual workflow; do not fabricate a resumable ledger.

## Select once from the actual saved plan

```text
python <plugin-root>/scripts/select_tests.py <plan> --scope full
python <plugin-root>/scripts/select_tests.py <plan> --scope smoke
python <plugin-root>/scripts/select_tests.py <plan> --scope targeted --tag php
python <plugin-root>/scripts/select_tests.py <plan> --scope targeted --tag plugin:actual-slug --exclude TEST-003
```

Capture stdout JSON as `selection.json` in the new gated report bundle; do not place
diagnostic stderr in JSON. Repeated `--tag`, `--exclude`, and `--ids` accept comma lists.
Invalid plans, unknown IDs/tags and cycles exit 2 with a JSON error. Selection does not
perform semantic review. The output contains the exact plan path/hash, every ID and
its inclusion/exclusion reason, stable dependency `order`, and `blocked_by` IDs.

- `full`: every non-excluded ACTIVE ID. Removed history remains unselected.
- `smoke`: essential smoke plus transitive prerequisites; no downstream expansion.
- `targeted`: update-tag/runtime-layer seeds, downstream Affects/reverse Depends on,
  then prerequisites, plus smoke/prerequisites. Smoke alone does not cause fanout.
- PHP includes declared php/unknown and conservative legacy cards lacking layers.
  Unqualified env means broad impact, so all active non-excluded cards are selected.
  A narrower explicit ID scope needs established impact and disclosed coverage limits.
- Excluded checks never execute. An exclusion does not erase known downstream impact:
  propagation may traverse that graph node. Excluded prerequisites remain blockers
  unless a current equivalent fixture is actually established and recorded.
- `--ids TEST-001,TEST-002` selects exactly these active IDs plus prerequisites, without
  adding unrelated smoke/downstream tests. Use this only for an explicit limited scope
  or a fresh retest. Existing report labels remain `Yes/targeted-tagged` for requested
  IDs and `Yes/targeted-dependency` for prerequisites; the reason explains the origin.

## Establish fresh context

Write `context.json` in the gated bundle using current non-secret preflight evidence.
It must contain exactly these fields (values below are illustrative, not real data):

```json
{
  "project_root": "C:/sites/example",
  "wordpress_root": "C:/sites/example/app/public",
  "site_url": "http://example.local",
  "home_url": "http://example.local",
  "blog_id": 1,
  "environment_fingerprint": "sha256-of-the-current-relevant-non-secret-context",
  "observed_at": "2026-11-02T12:00:00+00:00"
}
```

The fingerprint must be an actual 64-character lowercase SHA256 of a stable,
canonically serialized record of relevant current software versions/activation,
non-secret configuration, runtime/browser/role/locale/viewport context and any
other facts needed to interpret this run. Use the intended configuration/set of roles
and viewports, not a changing cursor position, current page, temporary cart, generated
log entries or other state deliberately changed by documented test steps. Record those
per-check states in observations/captures. Restore temporary configuration as required
before assessing broader drift. Keep the source record with its evidence
and limitations. Exclude observation time from that fingerprint. Normalize paths and
URLs consistently; preserve the correct site/network identity. `blog_id: null` is
allowed when not established, with the missing context disclosed in the report.
Never include passwords, cookies, API keys, user data or environment-variable dumps.

The helper checks the provided context's format and consistency; it cannot establish
that it is fresh or true. Recollect it before continuation; copying yesterday's context
is not a drift check. Unavailable verified identity/fingerprint means the ledger cannot
promise safe continuation. Independent current checks may still use a new manual run
with explicit limitations.

## Initialize and journal each check

Initialize before writing a new before checkpoint. The directory must already exist
and have passed storage preflight; an existing state/checkpoint is never overwritten.

```text
python <plugin-root>/scripts/run_state.py init --bundle <new-report-directory> --plan <plan> --context <context.json> --selection <selection.json> --mode normal
```

`--mode` also accepts before/after. This creates `run-state.json`, schema 1, separate
from the existing before `checkpoint.json` contract. It contains selection, plan hash,
context, per-check phase/status/attempts/cleanup and an action journal. Its lifecycle
OPEN/COMPLETE controls mutability; report completeness still uses shared selected-test
status rules. Keep report/checkpoint observations reconciled after every assessment.
Mutating CLI commands return compact summaries, not the whole growing ledger; the
complete saved state remains available for explicit inspection.

Before the first action in a selected check, save the action journal successfully:

```text
python <plugin-root>/scripts/run_state.py start <run-state.json> --plan <plan> --context <fresh-context.json> --id TEST-001 --action "Exercise documented disposable local workflow"
```

Use `--read-only` only when the check cannot mutate state. It defaults to potentially
mutating, so an interrupted action has unresolved cleanup until inspected. A second
start while any action is in flight is rejected. A real within-run retry needs explicit
`--retry`; all valid failures remain in history and aggregate FAIL, even after a pass.
This option never performs the retry itself. Do not retry unsafe side effects.

Execute only the authorized plan steps, then save an actual result JSON:

```json
{
  "status": "PASS",
  "observation": "Exact documented outcome directly observed",
  "reason": "",
  "evidence": ["screenshots/TEST-001.png"],
  "cleanup": {"status": "Complete", "notes": "Own disposable record removed and absence verified"}
}
```

```text
python <plugin-root>/scripts/run_state.py record <run-state.json> --plan <plan> --context <fresh-context.json> --id TEST-001 --input <actual-result.json>
```

Terminal statuses are PASS/FAIL/BLOCKED/NOT APPLICABLE. The last two need a reason and
may be recorded from pending without `start` for an unexecuted assessment. PASS/FAIL
requires a prior start journal. Evidence must be an existing relative file within the
bundle; its hash is recorded and checked on continuation. Cleanup is Complete,
Incomplete, or Not needed, with concrete notes. Incomplete cleanup blocks new actions.
The operational selection `reason` stays unchanged; `result_reason` records the actual
assessment. Preserve both when writing reports.

An unavailable prerequisite blocks starting its consumer. If an already-established,
equivalent fixture makes the documented consumer safe and meaningful, a human/agent
must inspect it now and record a review with exactly `ids` (all missing prerequisite
IDs), `observed_at`, and a concrete `observation`. Pass its JSON path to `start` using
`--prerequisite-review`. This does not authorize new setup actions, change the plan,
turn the prerequisite into PASS, or execute an excluded test. Retain the review as
evidence of why the consumer could proceed. An assumption is not an equivalent fixture.

## Resume an interrupted run

`/wp-checkpoint:test resume <run-state.json>` refers only to the explicitly identified
incomplete run. Recheck storage, current capabilities, identity, context and temporary
state first, then call the read-only helper:

```text
python <plugin-root>/scripts/run_state.py resume <run-state.json> --plan <same-plan> --context <fresh-context.json>
```

It returns completed, pending, interrupted, pending_cleanup, blocked_prerequisites and
runnable_now. It never continues an action automatically. Completed entries remain
dated earlier observations, not newly executed passes. Recheck the current fixture
needed by each pending consumer even when a producer previously passed and cleaned up.
Plan/context/evidence drift stops continuation; review it and start a new run. Do not
copy stale fingerprints, change hashes or alter the plan to force acceptance.

For an in-flight check, inspect the actual state before doing anything else. If the
whole documented result is already directly established, record that actual outcome;
do not repeat the action. Otherwise use `resolve` with current-state inspection:

```json
{
  "observation": "Inspected the interrupted local action and restored its disposable state",
  "retry_safe": true,
  "evidence": [],
  "cleanup": {"status": "Complete", "notes": "Original state verified; independent setup can repeat safely"}
}
```

```text
python <plugin-root>/scripts/run_state.py resolve <run-state.json> --plan <plan> --context <fresh-context.json> --id TEST-001 --input <resolution.json>
```

True `retry_safe` plus completed/not-needed cleanup returns the interrupted check to
pending. False records BLOCKED for an interrupted action; unresolved cleanup still
blocks further actions. The journal retains the interrupted observation, never
fabricates success or erases a prior valid failure. `resolve` can also record verified
cleanup completion after an already assessed check, without rerunning it. A stale
`.run-state.lock` means another writer or interrupted write: inspect it before explicit
removal, never auto-delete locks or run two writers against one bundle.

After every selected check is assessed, finalize the ledger:

```text
python <plugin-root>/scripts/run_state.py finish <run-state.json> --plan <plan> --context <fresh-context.json>
```

Pending cleanup remains honestly recorded even on a completed assessment. Finalized
state is immutable. In before mode finish this ledger **before** marking the consistent
checkpoint Complete; an already Complete checkpoint rejects any ledger mutation.
Finalize/reconcile the reports independently; a valid ledger does not prove DOCX
content, browser evidence or a working site. Interrupted entries are operational
history: they are not a sixth report/checkpoint result status.

## Fresh retest after fixes

`/wp-checkpoint:test retest <run-state.json>` reads a finalized old run and creates a
fresh protected bundle. Default seeds are its selected FAIL/BLOCKED IDs; explicit
`--ids` may choose any prior active IDs. The current plan supplies prerequisites.

```text
python <plugin-root>/scripts/run_state.py retest <prior-run-state.json> --plan <current-plan>
python <plugin-root>/scripts/run_state.py retest <prior-run-state.json> --plan <current-plan> --ids TEST-001
```

Save stdout to the **new** bundle's selection.json, collect current context and call
`init` there. Nothing is executed by `retest`; every fresh result begins NOT RUN with
no attempts. The selection retains old run ID/path/hash as provenance. A fixed behavior
may pass in the new run while the old failure remains unchanged. Missing/retired IDs
need an explicit scope decision; do not silently resurrect them. The user applies fixes.
Initialization requires the same project roots, URLs and site/blog identity as the
old run; matching test IDs alone never establish identity. The environment fingerprint
may change after the fix. Relocation needs an explicit reviewed identity mapping,
which this helper does not infer; an unrelated normal run has no retest attribution.

If finalized prior history records unfinished cleanup, first inspect and restore that
state using its authorized cleanup. Save a new `cleanup-review.json` in the fresh gated
bundle with `observed_at`, actual `observation`, `resolved_ids` listing every old pending
cleanup ID, `source_run_id`, `source_state_sha256` (exact finalized old state), `cleanup`
(Complete/Not needed and notes), and relative `evidence` paths. The observation must
be dated at or after the old run's finish; a review from another run is not reusable.
Pass it to retest via `--cleanup-review`. Its hash/evidence are checked; the old report
and state remain immutable. A review documents actual restoration, not future intent.
