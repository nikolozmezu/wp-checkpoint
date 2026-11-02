# Storage Preflight — Plan, Report and Checkpoint Destinations

Keep this reference identical in both skills. Read it before writing any project-specific plan, discovery index, run state, report, checkpoint or evidence. The storage gate precedes execution and screenshot collection, not just final export.

## Resolve paths once, for their distinct purposes

- **invocation_directory** (also called the captured **output base directory** in older plans): the session's working directory at skill invocation, captured before discovery/navigation. It never changes during a run.
- **plan_path**: the single persistent `testing-after-update.md`, resolved below. Discovery may update it; testing only reads it.
- **report_output_directory**: parent for a new run directory. Default to invocation_directory; an explicit user-selected report destination overrides this value, including a replacement supplied after a failed exposure check. Changing it does not change invocation_directory or move the plan.
- **baseline_path**: an existing before-run `checkpoint.json` selected for comparison. It is input, never the destination for a new run.

WordPress root, project root, Git root and plugin installation directory are distinct from these paths. Never silently switch output to the plugin's directory because a tool read a reference there. Resolve relative user paths against invocation_directory and state their resulting absolute paths.

### Plan resolution

1. An explicitly supplied plan path is authoritative. If it exists, use it in place. If missing, discovery may create it after its parent passes the gate; testing stops with `no plan found at <path>`, without substituting another plan.
2. Without an explicit plan path, check invocation_directory first.
3. If absent, search validated project layouts: project root, `app/public/`, `web/wp/`, `public_html/`, `htdocs/`, `wp/`. Verify project identity; if multiple plausible plans remain, ask which project/plan instead of choosing arbitrarily.
4. If none exists, discovery creates at invocation_directory after the gate; testing asks the user to run `/wp-checkpoint:test-plan-create` and stops. It never invokes that skill itself.

An existing plan stays in place and is never replaced by a blank template. If its storage is unsafe, stop writing and ask for a protected destination or separately authorized relocation. Do not silently move or duplicate an existing plan. A newly selected report destination has no effect on plan resolution.

### Fresh run directories and before checkpoints

Create `report-<YYYY-MM-DD>[-N]/` under report_output_directory for every normal, before or after run. Use the user's timezone for the date and record an offset-bearing timestamp/timezone in run metadata. Choose a fresh suffix (`-2`, `-3`, ...) when occupied; never reuse an old directory for a new run or retest. The explicit `resume <run-state.json>` command alone may continue the exact verified OPEN run in its existing bundle after storage/context/evidence/cleanup checks. Recheck that actual destination before new writes. Current OPEN progress may change until finalization; finalized runs and completed before checkpoints are immutable.

Before mode also writes `checkpoint.json` at the report root. After mode reads a validated earlier checkpoint and writes only into a new report directory. An output override never silently changes which baseline was selected. Reuse an established baseline path from the conversation, or resolve candidates as described in `before-after.md` in the test skill. Never scan unrelated home folders or other clients' projects to find one.

Evidence paths inside reports/checkpoints are relative to their run directory, resolve within that directory and identify existing files. Reject traversal, URLs, absolute paths and symlinks escaping that directory for evidence. A baseline's external source path may appear as metadata; to include its screenshots in the new self-contained report, copy only verified, relevant images into the new protected screenshots directory, preserving source attribution/hash and never altering the originals. Do not store credentials, session cookies, authorization headers or a database backup in a checkpoint. Redact secrets and irrelevant personal data from logs/screenshots before saving/sharing.

## Public-exposure gate

Evaluate the actual destination: the plan's parent, or the new report root and screenshots subdirectory. A safe invocation_directory does not establish the safety of a different destination.

1. Establish whether each actual destination is served by any relevant web server, alias or site mapping. If confirmed outside all served paths, no HTTP probe is needed. Do not assume a folder is protected just because its name looks private or the site is local.
2. If it might be served, confirm the filesystem-to-URL mapping using known-existing harmless content. Test access without authentication. A 404 for a nonexistent file proves nothing.
3. Prefer suitable existing harmless files; otherwise create only the minimal empty destination directories and inert probe files needed to test real paths. This is the narrow discovery-write exception. Remove each probe immediately after its request, regardless of the outcome. On failure, remove only directories created by this preflight that remain empty; never delete pre-existing content.
4. Probe each file type that will actually be saved at its actual path:
   - Plan parent: `.md`, plus `.json` wherever an optional discovery manifest/index will be stored.
   - Report root: `.md`, `.txt`, `.docx` if DOCX will be produced, and `.json` for selection, context, run state and any before checkpoint.
   - Visual review destination: `.html`, `.json` and generated `.png` when that optional review is produced.
   - screenshots/: each image extension to be used, such as `.png` or `.jpg`. Additional formats or subdirectories require their own applicable checks.
5. Confirm denial of known-existing content at every required path/type. A timeout, connection failure, unverified mapping, or unrelated redirect is inconclusive, never protection. A clear denial (403 or verified intentional 404 for the existing probe) is acceptable.
6. Only after every applicable check passes, write real content, initialize the report, and collect evidence. Record the conclusion without secrets. Probe files must not remain.
7. If protection is unconfirmed, stop before writing sensitive content. Explain the actual failed/inconclusive destination and request a non-public destination. On a user-supplied replacement report destination, update report_output_directory and re-run this gate there; invocation_directory remains fixed. A new plan destination is handled by plan resolution above. Do not guess a fallback or change server/security configuration.

Run this gate for every new run destination, including numbered suffixes; an earlier run's protection is not proof about another path. If a tool needs staging files, keep those in a verified non-served temporary location and clean them up; never save unprotected screenshots first and check exposure afterward.
