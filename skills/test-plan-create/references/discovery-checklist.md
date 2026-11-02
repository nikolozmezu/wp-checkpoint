# Discovery Checklist — What to Study

Read this in full before you start discovery, and work through every item that applies to this project. Skip only what genuinely doesn't exist here (e.g. skip "multilingual behavior" if no multilingual plugin is active) — don't skip an item just because checking it takes a few extra minutes.

This is discovery, not testing: everything here is "read code / read config / passively view a page," never "submit a form to see if it works," "publish a post," or "trigger a job." See the Discovery Boundaries section of SKILL.md for the hard do/don't list — this file is the *what*, SKILL.md is the *what's off-limits*.

## 1. Environment and codebase shape

- Locate the WordPress root (where `wp-config.php` / `wp-load.php` live) — it may equal the project root, or sit in a subfolder (`app/public/`, `web/wp/`, `public_html/`, `htdocs/`, `wp/`, a Bedrock-style split between `web/wp/` and `web/app/`, etc.). Check common patterns before asking the user for the path.
- WordPress version, PHP version, and (if visible without credentials) web server and database engine/version.
- Date this environment inventory and identify the local URL and installation root. These discovery facts are not an executed pre-update baseline. Optional `/wp-checkpoint:test before` and `after` runs capture their own dated inventories and behavioral evidence; never infer prior PASS results from this plan's versions.
- Active parent theme and, if present, child theme — names, versions, and which template-override files exist (which core/parent templates they override).
- All active plugins (name, slug, version), separated clearly from installed-but-inactive plugins. Custom/bespoke plugins and MU-plugins (`mu-plugins/`) need the same treatment — read what they actually register (post types, hooks, REST routes, cron events, shortcodes) rather than just listing filenames.
- Relevant drop-ins (`object-cache.php`, `advanced-cache.php`, `db.php`) — their presence implies a caching or DB layer worth covering in Section F.
- Permalink structure, and any custom rewrite rules.

## 2. Content model

- Custom post types and taxonomies — real slugs, not generic names — and whether each is public, has an archive, supports REST.
- Routes implied by the above: front-end URLs for each post type's and taxonomy's single and archive views.
- Shortcodes, blocks (core and custom), widgets, custom fields (ACF, Pods, Meta Box, native meta — whichever is actually in use), and any conditional display logic (conditional tags, display rules from a page builder, membership/visibility plugins).

## 3. Page builders and template assignment

- Which page builder, if any, is active (Elementor, Divi, Beaver Builder, Bricks, WPBakery, Gutenberg-only, etc.).
- How templates are assigned to pages (theme template picker, builder-specific template conditions, a visibility/display-conditions plugin).
- Representative examples of each meaningfully different template/layout — not every page that uses it.

## 4. Dynamic behavior

- AJAX actions (`wp_ajax_*` / `wp_ajax_nopriv_*` hooks) and REST API routes actually registered and used by this site's features (not just everything WordPress core exposes by default).
- Trace each tested request from its actual caller through the current endpoint configuration and handler. Record the file/line, hook or option establishing the URL/method/action, relevant response shape, and any redirect/reload setting. Framework conventions are search clues, not project evidence. If the active path cannot be established, record the exact uncertainty instead of asserting a guessed endpoint or transport behavior.
- Search, filtering, pagination, and any "load more"/infinite-scroll behavior. For any faceted/taxonomy filtering widget, read its actual stored configuration (not just its presence) — most such plugins let an admin set AND vs. OR independently per filter field and separately for how different fields combine; don't assume either without checking.
- Forms on the site (contact, newsletter, checkout, custom) together with their validation and success/failure paths as implemented — read the handler code; don't submit them, that's for `/wp-checkpoint:test`. For each one, identify which plugin/widget actually renders it (don't assume it's whichever forms plugin happens to be active and visible elsewhere on the site — a page-builder's own native forms module is common and easy to mistake for a dedicated forms plugin), where its data goes (a persistent, revisitable entries store, or nothing beyond an outbound email), and the literal destination(s) — real email addresses, or the specific external service — a submission would reach. See `references/common-pitfalls.md` #4.
- If the site sells anything (an active ecommerce plugin), establish whether checkout/payment can actually complete a transaction right now — check for at least one enabled, configured payment method, and confirm the cart/checkout/account pages the ecommerce plugin's own settings point to actually exist and are published. A product catalog with working "add to cart" can still have a completely non-functional checkout; don't infer full store coverage from the plugin being active and products being real, and don't exclude checkout coverage without this check. If it's genuinely non-functional right now, that is itself a finding worth a test case — but write that case to record the observed state as a fact only (e.g. "Cart/Checkout/My Account pages are configured in WooCommerce settings but do not exist, as of &lt;date&gt;"), not as an approval of that state. Whether a non-functional checkout is correct/intended or a defect is a separate, unresolved acceptance question (see `references/common-pitfalls.md` #9) that this skill cannot answer on its own — flag it as open in Section C, and don't let the test case's expected result imply the current broken state is what *should* be preserved. Also record it as a clearly flagged precondition for completing checkout coverage later — not a silent omission.

## 5. Media

- Featured images, registered image sizes, galleries, and responsive-image behavior (`srcset`/`sizes` output). Enumerate the actual registered image sizes — WordPress's own core sizes (thumbnail/medium/medium_large/large, as configured in Settings → Media) plus every project-specific `add_image_size()` call (theme, plugins, WooCommerce's product image sizes, etc.) — including each one's crop setting and dimensions. A future media-upload test needs this list and a source image large enough that none of the applicable sizes are legitimately skipped for being larger than the original (WordPress does not upscale, and that is expected behavior, not a defect).
- Audio/video players (native, plugin-based, or embedded) and external embeds (YouTube, Vimeo, social, etc.), and whatever fallback behavior exists for a missing or blocked embed.

## 6. People and workflow

- User roles actually in use (not just WordPress defaults — custom roles/capabilities too) and how editorial workflow differs by role (who can publish, schedule, or only draft).

## 7. Background and infrastructure behavior

- Scheduled jobs: real `wp-cron` events registered by the theme/plugins (not just whether WP-Cron is enabled), queues, import routines, and third-party integrations (payment, email/CRM, analytics, webhooks) — and what each actually does when it fires.
- Caching layers in play: page cache, object cache, transients, CDN — identify which exist; don't assume none do just because this is a local copy. A caching plugin's own "enabled" setting is not the same as this environment being able to reproduce the behavior (a plugin-level page cache can depend on a server module a local dev stack simply doesn't run) — note this distinction explicitly where relevant, don't just record the plugin setting as if it settles the question.
- For any feature built on a multi-mode storage or processing system (a legacy/new storage switch, a sync-vs-authoritative toggle), check the specific option/flag that controls which mode is actually live — not just whether the newer mode's tables/schema exist or hold data. Schema existing (even schema that's been populated by a prior sync) is not the same as that mode being authoritative right now. Name the plugin/code version, the schema version, the configured mode, and what you actually observed as four separate facts when they could plausibly differ.
- Logging: identify where PHP/WordPress errors would surface and read existing entries without generating any. Record source environment, event timestamp/timezone and observation time separately. A copied log establishes an incident at its recorded time, not a currently active plugin or a currently reproducible local defect. Separate confirmed current observations, historical incidents and unresolved provenance in the inventory/known-issues section. Future log-review cards must establish the tested environment's run window and log offset/rotation context in every mode; absence from the known-issues list does not make an old entry new.

## 8. Language

- Any multilingual setup (WPML, Polylang, native WordPress multisite-per-language, or none) and what differs by language where it exists.

## 9. Distinguish active from inactive

For every item above, record activation/assignment state separately from presence, version and observed use:
- **Confirmed active** — current admin, read-only activation configuration or another authoritative current runtime source identifies the component in this target environment. Record that source and date; distinguish site/network activation when relevant, and an actual MU-plugin loader from files merely stored below its directory.
- **Confirmed inactive** — current activation state establishes inactivity. Do not create execution cards for it unless a separate existing requirement applies; note relevant update risk without inventing current use.
- **Unknown activation** — installed, but current activation cannot be established. Keep it explicitly unknown, including in inventory headings, rather than "likely active" or "active pending confirmation." Cached HTML/assets, a shared namespace, old logs, plugin descriptions and lack of contrary evidence do not settle activation. Missing assets do not prove inactivity.
- **Confirmed unassigned/unused** — assignment configuration establishes that a template/block/feature is unused. Merely not encountering it in a sample is an observation limit, not an exclusion.

An `active_plugins` options export establishes site-level activation only. Before calling an absent regular plugin Confirmed inactive overall, establish that the target is single-site, or also inspect network-wide `active_sitewide_plugins` for the correct multisite network. If that context is unavailable, keep overall activation Unknown and report the narrower site-level fact. Missing network metadata is not proof that network activation is absent.

A new authoritative source can resolve an unknown without running a functional test. Until then, retain any justified candidate coverage with the activation uncertainty as a prerequisite/gap; do not manufacture active use or silently exclude a core capability. Every claim also keeps its evidence-source label and environment/time provenance.

## 10. Representative sampling

Inspect one (or a few, if there's meaningful variation — e.g. a post with a gallery vs. one without) representative example of each page/template type. Do not attempt to visit every post, product, or archive page — that doesn't scale and isn't the point. The goal is to map *types* of pages to their templates and behavior, not catalog every URL on the site.

## 11. If access is incomplete

If browser, database, WP-CLI, or admin access is unavailable or partial, continue with whatever evidence you do have, and say plainly — in Section B (limitations) and next to the relevant Section C/F entries — what could not be inspected and why. A gap you've named is useful; a gap you've silently glossed over is not.

## 12. The one rule that matters most

**Reading code, viewing a config value, or passively loading a page in a browser is not the same as confirming a feature works.** Label everything you learn this way with the matching evidence-source tag from `references/shared-conventions.md` — never write it into Section C or F as if it were a completed test result. The actual test result field for every test case in a newly written or updated document is **NOT RUN**, full stop, regardless of how confident discovery made you feel.

## Practical discovery techniques (generic, non-destructive)

These are suggestions, not a fixed tool list — use whatever subset is actually available in this environment, and clearly record what wasn't:

- **WP-CLI**, if installed and reachable (`wp core version`, `wp theme list`, `wp plugin list`, `wp post-type list`, `wp taxonomy list`, `wp option get <name>` for non-secret options, `wp cron event list`, a read-only `wp db query "SELECT ..."`). Never use a `wp` subcommand that writes, updates, imports, flushes a cache, or deletes anything.
- **Direct file reads** when WP-CLI isn't available: theme/plugin header comments (the `Version:` line in the main plugin file or `style.css`); `wp-config.php` for the table prefix and which drop-ins/constants are defined (read it to learn structure only — never print its secrets; see Credential Handling in SKILL.md).
- **Browser automation**, if a connected tool is available in this session, for passively loading front-end pages and admin screens to see real rendered layout, without clicking anything that submits, publishes, or deletes.
- **Read-only database queries**, only if a safe read-only connection is already available to you — never a connection string or credential you had to go fetch or guess.

If none of the above is available for a given area, say so explicitly rather than guessing or inventing plausible-sounding details.
