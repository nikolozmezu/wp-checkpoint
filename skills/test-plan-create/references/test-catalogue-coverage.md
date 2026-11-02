# Test Catalogue Coverage — Section F Source List

Read this in full before drafting Section F of `testing-after-update.md`. It is the specific, non-negotiable coverage list that SKILL.md's instructions point to — treat every bullet as a question to answer for this project ("does this exist here? if yes, is it covered by a test case?"), not as generic boilerplate to copy in verbatim. Where an item doesn't apply, say so briefly in the Applicability/Gaps subsection — don't silently delete it, and don't replace it with a vague stand-in like "check that everything works" or "test responsiveness."

For every applicable item, use the template's schema-3 card: permanent ID, lifecycle, execution layers, implementation evidence, prerequisite/impact IDs, concrete fixture setup and starting point, numbered steps, observable expected result with its basis, evidence, cleanup and resulting state. Every expected branch needs an observing step. Use actual source/configuration rather than generic framework assumptions; use "Requires clarification or runtime confirmation" for unresolved criteria. Retain REMOVED history and keep all plan statuses NOT RUN. Apply `references/plan-quality-review.md` before declaring the document reviewed.

## Frontend structure and content

- Homepage and important landing pages.
- Relevant single-content templates, including custom post types.
- Archives, taxonomy pages, search results, and pagination.
- Important template variations, sidebars, conditional sections, and language variants.
- Correct content selection, ordering, and relevant duplicate/exclusion rules (e.g. a "related posts" block that must exclude the current post, a homepage feed that must exclude a certain category).
- Representative empty, missing-content, and error states (an archive with zero posts, a 404, a shortcode with no matching content).

## Navigation and interaction

- Header/footer links, menus, dropdowns, mobile navigation, and relevant sticky elements.
- Search, filters, pagination, load-more behavior, and URL/state preservation (does a filter choice survive a page reload or back-button navigation?).
- Existing pagination URL structures (e.g. `/page/2/`, `?paged=2`, a custom query var) — confirm what this project actually uses rather than assuming the WordPress default.
- Modals, lightboxes, sliders, carousels, tabs, accordions, and any other interactive components actually present.
- Forms and their relevant validation, success, and failure states.
- Logged-in versus anonymous behavior where applicable.

## Media

- Featured images, responsive images, thumbnails, galleries, and image proportions.
- Relevant upload workflows, supported formats, and generated image sizes.
- Audio/video players and meaningful playback states.
- External embeds and documented fallback behavior.
- Missing or unavailable media where relevant (a post with no featured image, a broken embed URL).

## Visuals and responsiveness

- Header, footer, layouts, typography, spacing, images, cards, sidebars, and overlays.
- Important component states and template variations.
- A practical viewport matrix based on **this project's actual CSS breakpoints and layouts** — don't default to a generic "mobile/tablet/desktop" set without checking what the theme/builder actually defines.
- Relevant behavior near breakpoint boundaries (just above/below each breakpoint, not only a few standard device widths).
- Overflow, clipping, overlap, alignment, readable text, and visible controls.
- Relevant content variations such as long titles or portrait/landscape images — these are what actually break responsive layouts, more often than "happy path" content does.

Derive expected visuals from available evidence (the existing live site, design files if referenced in project docs, or the local site's own current rendering as a baseline). Do not invent an approved design. If no reliable baseline exists, say plainly which observations are possible now and which before/after comparisons will remain unconfirmed until a future run has both states to compare.

For visual cards, specify the page, role, viewport, and meaningful UI state to capture so optional before/after runs can reproduce the view. Identify dynamic regions (dates, rotating content, personalized data) that affect comparison. A screenshot of a different route, state, or viewport is not automatically a compatible before image; document the limitation rather than presenting it as proof of a regression.

## Admin and editorial workflows

- Login and relevant role/permission differences.
- Creating, editing, saving, reopening, previewing, publishing, and scheduling content. This applies to the project's standard content types by default (post/page, or any editable custom post type) regardless of whether the site is built entirely through a page builder and has no custom blocks — "no custom blocks were found" is a reason to skip a block-editor-specific case, not a reason to skip ordinary editorial workflow. The same applies to scheduled publishing: no scheduled content existing in a snapshot means it hasn't been observed in use, not that the capability is unneeded — include it, and say plainly that no prior usage was observed if that's the case. See `references/common-pitfalls.md` #1.
- Relevant custom fields, relationships, repeaters, taxonomies, options, and template assignments.
- Relevant block-editor and page-builder workflows.
- Media uploads and image-size behavior.
- Relevant differences between editorial roles.

## Technical behavior

- AJAX actions and REST endpoints used by actual site features (not WordPress's full default surface); derive request and redirect/reload expectations from the active caller/configuration and handler.
- Scheduled posts, cron jobs, queues, imports, and integrations.
- Relevant page, object, transient, and CDN cache layers. A caching plugin reporting itself "enabled" is not the same as this environment being able to reproduce a production-only cache layer (e.g. a server-level module) — if the environment can't, record that as a limitation rather than asserting coverage or generating a false failure.
- Content/cache invalidation and freshness after changes. Write the steps so invalidation is checked by observing a disposable, dated content change *without* manually purging first — manually purging before checking would hide a failed automatic-invalidation behavior. Purge only as a cleanup step afterward if needed.
- Cached versus uncached and anonymous versus logged-in behavior where relevant.
- PHP/WordPress errors, warnings, and deprecations, attributed to the tested environment and run window rather than copied historical logs.
- Browser-console and network errors.
- Meaningful performance comparisons where a baseline exists.

For every coverage area, infer all execution layers, including PHP behind rendered pages/editorial actions, browser interaction, infrastructure and external integrations. Reconcile those layers with update selection using the shared contract. Do not limit runtime coverage to obvious technical cards or assume a tag matrix proves the relevant paths were included. Unknown layers stay explicit and require conservative scope.

## Four things that look like evidence but aren't

Keep these distinctions sharp in both the document you write and, later, the report `/wp-checkpoint:test` produces:

1. A registered cron event is not the same as a successfully completed job.
2. A configured integration is not the same as a working integration.
3. A cache hit is not the same as correct invalidation.
4. A page loading is not the same as all its interactions working.

## Don't invent performance thresholds

If there's no established baseline (a prior measurement from this project, not an industry rule of thumb), say that no baseline exists rather than asserting a number like "under 2 seconds." A performance comparison is only meaningful against this project's own prior measurement.

## Applicability and gaps

Areas above that don't exist in this project, or that you couldn't resolve with available access, belong in a short "Applicability / Gaps" subsection at the end of Section F — not scattered as silent omissions, and not padded out with speculative test cases for things that aren't there. State which specific areas are unsupported and why (not present in this project / access unavailable / needs user clarification).
