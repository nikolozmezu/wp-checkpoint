# Reuse reviewed static discovery without reusing test results

Use the optional discovery cache when refreshing a large existing plan. It reduces
repeated source reading, not required current-state checks or the final all-card
semantic review. A missing cache is ordinary first-time discovery, not a blocker.
The plan remains authoritative; this index contains paths, hashes and provenance,
never a substitute plan, source contents, credentials or recorded PASS results.

## Inputs and storage

Resolve `scripts/discovery_cache.py` from the loaded plugin. Pass the normal storage
gate for both the explicit evidence manifest and cache JSON destination before
writing either. Keep them beside the protected plan or in an explicit protected
working directory; do not put them in a public WordPress directory by default.
Do not create a cache merely to fill a success label or avoid reading missing code.

Write a small manifest from evidence actually used during discovery. Example shape:

```json
{
  "schema_version": 1,
  "context": {
    "environment_id": "local-editorial",
    "site_url": "http://example.local",
    "home_url": "http://example.local",
    "blog_id": 1
  },
  "sources": [
    {
      "path": "wp-content/plugins/site-search/search.php",
      "test_ids": ["SEARCH-001"],
      "kind": "static",
      "category": "source",
      "provenance": "Local source, registered lookup handler",
      "captured_at": "2026-11-02T10:00:00+04:00"
    },
    {
      "path": "evidence/current-options.json",
      "test_ids": ["SEARCH-001"],
      "kind": "volatile",
      "category": "activation",
      "provenance": "Read-only sanitized current site options export; network context recorded separately",
      "captured_at": "2026-11-02T10:00:00+04:00"
    }
  ],
  "watches": [
    {
      "path": "wp-content/plugins",
      "patterns": ["**/*.php", "**/*.js"],
      "test_ids": []
    }
  ]
}
```

Paths use `/` relative to the explicit WordPress/project root. Source categories
are `source`, `configuration`, `activation`, `inventory`, `runtime`. Only `source`
can be reused as static; other categories are always volatile, even if accidentally
declared static. Every source has real plan IDs, provenance and an offset-bearing
observation time. Missing sources remain refresh requirements. Keep secrets out of
the manifest's prose too. Do not export raw options/database data to feed the cache.

Watches enumerate matching files recursively under an explicit narrow directory.
Patterns use case-sensitive `fnmatch` syntax; `**/` also matches files directly in
the watched directory. Map a watch to affected existing IDs when that relationship
is established. An empty mapping means a changed/new component needs full discovery
instead of being silently omitted. Include relevant plugin/theme/MU-plugin/template
directories so newly added code is visible; unlisted/unwatched areas are not covered.
An unknown broader change still requires full discovery. Secret-bearing files,
symlinks, path escapes and excessively broad inputs are rejected with an explanation.

## Refresh workflow

1. Confirm project/environment identity and obtain current activation, configuration,
   roles/routes and runtime prerequisites through the existing discovery access.
   Reuse only reviewed static findings with unchanged source/provenance. Equal files
   cannot establish that a database setting, network plugin or external service stayed
   unchanged. No prior test success is carried forward by this cache.
2. Run the read-only comparison before editing the plan:

   ```text
   python <plugin-root>/scripts/discovery_cache.py check --root <project-root> --plan <plan.md> --manifest <sources.json> --cache <discovery-cache.json>
   ```

   Read `full_refresh`, `affected_test_ids`, `unindexed_test_ids`, `changes` and limitations. Cards
   without an evidence mapping remain ordinary-discovery requirements. A changed
   project/context, plan hash/path, plugin version or unsupported cache schema requires
   full review. A missing cache also requires ordinary discovery. Changed, added,
   deleted, missing or remapped evidence is never reused silently. Volatile sources
   always require a fresh read, regardless of their hash. Expand affected coverage
   through actual feature dependencies; the cache cannot infer missing mappings.
3. Reinspect affected sources/cards, preserve stable IDs and update the plan. Perform
   the usual structural validation and source-backed semantic review of all active
   cards; unchanged static evidence may support that review without rereading its
   bytes. Cache output alone does not grant a Reviewed verdict.
4. Only after that review, update the manifest's actual evidence provenance/time and
   explicitly capture the new index against the final saved plan:

   ```text
   python <plugin-root>/scripts/discovery_cache.py capture --root <project-root> --plan <plan.md> --manifest <sources.json> --output <discovery-cache.json> --reviewed
   ```

   Capture writes atomically to the explicit existing protected directory. It refuses
   an unrelated JSON file or another project's cache. The `--reviewed` flag records
   the caller's attestation; the program does not independently verify source truth.

Both commands print JSON. Exit 0 means the command produced a valid comparison or
capture, not that refresh is unnecessary; inspect `full_refresh`/`status`. Exit 2
means malformed/inaccessible/unsafe input. Fall back to complete discovery when the
helper is unavailable; disclose that optimization was not used. Never weaken coverage
or change project configuration to make a cache check succeed.
