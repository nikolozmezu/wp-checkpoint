---
name: doctor
description: Diagnose which WP Checkpoint source and installed Claude cache versions exist, compare their runtime files, and explain stale-version or disabled-plugin problems. Read-only; never installs, updates, removes, enables or reloads a plugin automatically.
disable-model-invocation: true
argument-hint: "[--loaded-version <version-reported-by-this-session>]"
---

# /wp-checkpoint:doctor

Diagnose the WP Checkpoint version/cache confusion with a short explanation and the
next useful action. Resolve `scripts/doctor.py` from this loaded plugin and record the
actual source root; a checkout named in the conversation may differ from the copy
containing this skill. If the user asks to compare a particular checkout, use that
explicit checkout as `--source` instead.

Run read-only from the user's invocation directory:

```text
python <plugin-root>/scripts/doctor.py --source <intended-plugin-root> --project <invocation-directory> --json
```

Pass `--loaded-version <version>` only if the current session/user actually supplied
that value. Never derive it from the manifest on disk and present it as a measured
live-session version. Optional `--registry <path>` and repeated `--settings <path>`
support an explicitly identified installation/configuration; do not search unrelated
home directories or expose other plugin/account/settings values.

The helper reads the matching plugin registry entries, source/cache manifests and
runtime-file hashes. It distinguishes:

- source, registered and cached manifest versions;
- identical version numbers with different runtime file contents;
- missing/unreadable caches, explicit disabled settings and project scope;
- a caller-reported session version versus an unknown currently loaded version.

Default settings are read in user → project → local order. Managed policy overrides
are not inspected, so name that limit if enablement remains disputed. Multiple
registrations need scope/source inspection, not an arbitrary winner. An absent
registry entry does not prove that a session using `--plugin-dir` has no plugin.

Reply in the user's language with the relevant versions/path, concrete mismatch or
uncertainty and one next step. Keep full hashes and unrelated configuration out of the
response. A matching cache does not prove an already-open session refreshed its code.
Recommend `/reload-plugins` or restarting Claude when a verified update postdates the
session; a same-version update may retain the old cache, so maintainers should version
final source changes before updating the installed copy.

Exit 0 means the inspected source/cache registrations match; exit 1 means attention
or no applicable registration; exit 2 means malformed/inaccessible input. If Python
is unavailable, compare only the same manifests/relevant registry/settings fields
manually and state that runtime-file comparison was not performed. Do not install
dependencies, alter registry/cache/settings, run updates, delete directories or claim
to reload the current session as part of this diagnostic.
