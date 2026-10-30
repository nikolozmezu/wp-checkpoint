# Storage Preflight — Output Location and the Public-Exposure Gate

This file is identical in both `test-plan-create/references/` and `test/references/` — it's the shared contract for *where* either skill writes site-specific output and how each confirms that location is safe, before any sensitive content is written. If you ever have reason to change one copy, change the other the same way.

Read this before either skill writes anything to disk. For `/wp-checkpoint:test-plan-create`, that means before Step 4 writes `testing-after-update.md`. For `/wp-checkpoint:test`, that means at Step 3 — before execution starts, and before Step 6's reporting work, since Step 3 is where the report file itself gets initialized. Neither skill defers this to its final reporting step.

## The output base directory

Capture the directory this session was actually working in **at the moment this skill was invoked** — as the very first action, before locating any existing plan, before any other directory discovery, before any `cd` or file read takes you somewhere else. Call this the **output base directory** and keep it fixed for the rest of the run; later steps use this exact captured value and never recompute it.

Keep it explicitly distinct from:
- The discovered **WordPress root** (which may be a subfolder, e.g. `app/public/`, or a Bedrock-style split).
- The discovered **project root** (a superset of the WordPress root, if the repo also holds build tooling or deployment config).
- The **git repository root**, if the project is nested inside a larger monorepo.
- This **plugin's own directory** (never write output into `wp-checkpoint`'s own skill folder).
- Any directory a later `cd`, file read, or tool call happens to land in during the rest of the session — don't silently recompute "current directory" later and let it drift from what you captured at invocation.

In the ordinary case (the session was started from inside the WordPress project), the output base directory and the project root are the same path — that's expected, not a coincidence to second-guess. The point is to capture it once, explicitly, rather than re-deriving "where am I" at each step and risking a different answer if something moved the shell's working directory in between — including when the session's working directory sits *above* the WordPress root (a parent folder holding several sites, say) and the WordPress root itself is found one or more levels down.

**Resolution rule, for both skills — unambiguous, in this exact order:**

1. **An explicitly user-supplied path is authoritative**, whether or not a file exists there yet:
   - If it exists: use it in place. `/wp-checkpoint:test-plan-create` updates it there; `/wp-checkpoint:test` reads it from there.
   - If it doesn't exist: `/wp-checkpoint:test-plan-create` creates it there (after that location's parent directory passes the exposure gate below) — never substitute the output base or a fallback result instead. `/wp-checkpoint:test` never creates a plan: an explicitly-supplied path with nothing at it produces a clear, specific "no plan found at `<that path>`" response, and stops there — it does not fall back to searching the output base or elsewhere, and does not substitute a different plan it happens to find.
2. **With no explicit path**, check for an existing plan already at the **captured output base directory** first.
3. **Still nothing, with no explicit path**: run a **validated fallback search** — the common layouts `/wp-checkpoint:test-plan-create`'s own Step 1 checks (project root itself, `app/public/`, `web/wp/`, `public_html/`, `htdocs/`, a bare `wp/` subfolder).
4. **No explicit path, and steps 2–3 found nothing:** `/wp-checkpoint:test-plan-create` creates a new plan at the output base directory (the same location step 2 checked). `/wp-checkpoint:test` never creates one — tell the user `/wp-checkpoint:test-plan-create` needs to run first, and stop.

If an existing plan is found anywhere at all — step 1, 2, or 3 — it stays exactly where it was found. Never move it, never duplicate it into the output base or anywhere else; `/wp-checkpoint:test-plan-create` updates it in place.

**The output base directory itself never changes** once captured — it's the fixed input to steps 2 and 4 above, not something re-derived per step.

**An existing plan vs. an earlier report — these are not the same kind of thing.** `testing-after-update.md` is a single, persistent, reusable document, resolved by the rule above. A `report-<date>[-N]/` directory is the opposite: a point-in-time, immutable record of one run, always created fresh at the *current* run's output base. **An earlier report must never become the destination for a new run, regardless of where it lives** — never reuse, update, or write into a previous run's report directory, even one that happens to sit at what is now the resolved output base.

## The public-exposure gate

Most WordPress project roots are also the public webroot. Before writing anything site-specific, establish whether **the actual resolved write destination** — not the output base directory — is reachable over the public internet, and if so, whether the web server actually denies it. Evaluate this at:

- **`/wp-checkpoint:test-plan-create`:** the parent directory of the `testing-after-update.md` path the resolution rule above actually resolved to — whichever of the four cases applied. This is frequently the output base, but never assume that without checking: an explicit path or a fallback-search result can resolve somewhere else entirely, and a non-public output base never exempts a plan that resolution placed inside a public WordPress directory.
- **`/wp-checkpoint:test`:** the actual new `report-<date>[-N]/` directory for this run, and its `screenshots/` subdirectory — these are always under the output base (reports are never found via an explicit path or fallback search), but are still evaluated as their own destination, not inferred safe from a check of some higher-level directory.

**A 404 from a path that was never going to exist proves nothing.** Testing a made-up filename and getting 404 only tells you that path doesn't exist — it says nothing about whether a *real* file placed at that same location would be served or denied. The gate below tests denial of real content, not the absence of fake content.

1. **Determine if the actual resolved destination is web-served at all.** If you can establish *that specific destination* is outside the web server's document root entirely (a path the user explicitly chose for exactly this reason, or a location with no vhost/site config serving it), there is nothing to probe there — skip straight to writing. Reaching this conclusion about the output base does not carry over to a different resolved destination (an explicit path or fallback-search result elsewhere) — evaluate each destination you're actually about to write to on its own.
2. **If it might be web-served, confirm the actual filesystem-to-URL mapping first.** Don't assume a 1:1 path-to-URL structure. Confirm it by requesting the URL for a file you already know exists near the intended destination (an existing project file at a known path) and checking that it resolves where you expect. An unverified mapping is a reason to continue to the next step carefully, not a reason to skip it.
3. **Test denial of known-existing, harmless content at each relevant path — not a nonexistent path.** If a suitable existing file is already there to test with, request it directly; this needs no new file or directory. Otherwise, create the **minimal empty container** needed to place a probe at each real path you're actually about to write to:
   - `/wp-checkpoint:test-plan-create` only ever needs one: the directory that will hold `testing-after-update.md`.
   - `/wp-checkpoint:test` needs the `report-<date>[-N]/` directory itself and, since screenshots live in a separate subdirectory that could be governed by a different rule, `report-<date>[-N]/screenshots/` too.
   Place one small, inert, harmless probe file of the relevant type (see point 4) in each location that needs checking, request each one individually, and **remove every probe file immediately afterward, regardless of outcome.** This — creating the minimal empty container directories and harmless probe files strictly needed for this check — is the one narrow, explicitly-scoped exception to each skill's otherwise strict boundaries. No sensitive plan, report, or evidence content is written anywhere until the gate has actually passed. If the gate fails overall, remove any directory this preflight itself created, but only while it's still empty — never delete a pre-existing file or directory, and never remove a directory you didn't create yourself during this check.
4. **Check each relevant file type you're actually about to write, not just one.** A web server or security plugin can deny one extension while still serving another — denial of one type never establishes denial of another. Minimums:
   - `/wp-checkpoint:test-plan-create` writes only Markdown — a single `.md`-type probe at its one destination is sufficient.
   - `/wp-checkpoint:test` writes Markdown, plain text, image, and DOCX content across two locations — at the report root, test a `.md`-type probe, a `.txt`-type probe (`report-<date>/log-excerpt.txt` is a required output — don't let it slip through unchecked just because it looks like plain text), and a file carrying the `.docx` extension (`wp-update-report.docx` also lives at the report root, not inside `screenshots/`). Test an image-type probe (`.png`/`.jpg`) inside `screenshots/` specifically, since that subdirectory is a separate path that could be governed by its own rule.
5. **Use unauthenticated requests.** An authenticated session may see different access than the public does — the question is what a random internet visitor would get.
6. **Treat these as inconclusive, not reassuring:** a timeout, a connection failure, an unrelated redirect (to the homepage, a login page, or anywhere other than a clear 403/404 at the exact path you probed), or an unverified filesystem-to-URL mapping. Any of these means protection is **not established** — handle it the same as a failed check, not as a pass.
7. **If protection is confirmed for every relevant file type at every relevant path:** proceed — the minimal empty containers created in step 3 can stay; you're about to fill them with real content.
8. **If it cannot be confirmed:** stop before writing any sensitive content. Tell the user plainly that the default output location would be web-reachable (or that reachability couldn't be determined), and ask them to name a non-public destination. Do not silently fall back to the user's home directory, a guessed "safer-looking" path, or anywhere else without being told to. Do not edit server configuration (`.htaccess`, an nginx/Apache vhost, a security plugin's access rules) yourself to manufacture protection — that is a production configuration change outside either skill's scope, and needs the user's own, separate decision.

Re-run this gate fresh for each new output location this run creates (including a numbered-suffix `report-<date>-2/` on a later run the same day) — a check from earlier in the session, or against a different path, doesn't carry over.
