# Planning behavior evaluations

These small, offline WordPress-shaped projects are synthetic inputs, not runnable sites.
They contain no client data. They exercise evidence interpretation that the structural
validator cannot prove. Run them when planning behavior changes; unit tests alone do
not demonstrate source-backed plan quality.

Copy each case to a fresh, non-web-served scratch directory outside the plugin source.
For `fieldnotes`, invoke test-plan-create to create a plan there. For `memberlane`, copy
`prior-plan.md` to `testing-after-update.md` and invoke the same skill to refresh it.
Supply only the request below, the skill path and the copied project's path to a fresh
reviewer; do not show the assessment criteria until the artifact has been produced.

> Use the test-plan-create skill to create or refresh this project's test plan. The
> supplied folder is a synthetic, non-web-served local project. Its requirements and
> source/evidence files are the available inputs. Browser, network, admin and database
> access are unavailable. Read-only discovery and writing the plan are authorized;
> never execute PHP/JS, install tools or run functional checks. Record inaccessible
> facts honestly. Save the plan in the copied project root and validate it.

Assess the saved plan against the raw evidence, not its self-reported review status:

| Case | Required observable behavior |
| :-- | :-- |
| fieldnotes | Current options establish site activation; an absent plugin's overall state stays Unknown without single-site/network context. Old cached assets/logs cannot override current evidence. Search transport matches the actual caller/handler, not a guessed generic endpoint. PHP request paths get php coverage. Inaccessible runtime behavior stays unexecuted. |
| memberlane | Existing IDs/history are preserved. A revoked invitation is not supplied to the next check: document independent creation or an explicit safe shared lifetime. Both accepted and rejected invitation outcomes have actions/observations. Source transport replaces the assumed wrong request route. Historical-only component activation stays Unknown. |

For both, all plan statuses remain NOT RUN, new schema 3 fields are present, source
limitations are explicit, and Section I separates structural validation from semantic
review. Fix the plugin for a demonstrated failure, then rerun the affected workflow or discovery phase with a fresh reviewer
and raw inputs. Do not edit a generated case merely to make its evaluation pass. These
cases are evidence of specific behavior, not a guarantee for every WordPress project.


## Recorded evaluation — 2026-11-02

The automated validator suite passed 33 tests. Independent full planning trials
created eight Fieldnotes cards and refreshed four Memberlane cards, preserving the
existing IDs. Both saved plans had zero structural errors; Memberlane retained six
warnings for explicitly unknown layers/evidence. All cards stayed NOT RUN. Review
confirmed the source-specific request paths, separate rejection steps, independent
fixtures after cleanup, and broader PHP coverage. Runtime execution was unavailable.

Review of Fieldnotes also found an overclaim: site-level plugin absence was called
overall inactivity without single-site/network evidence. The discovery/review rules
were corrected, then a fresh inventory-only trial against raw Fieldnotes inputs
reported confirmed site activation for Search and Unknown overall activation for
Legacy Notify, with the missing network context stated. The original trial artifact
was not manually edited to make this evaluation pass. These observations validate
specific planning behaviors, not universal correctness or a working live site.


## Real runtime suite

The optional [runtime suite](runtime/README.md) adds real WordPress/PHP/SQLite and
Chromium execution with a controller-only fault oracle. Its public requirements and
blind-test procedure keep implementation/failure expectations away from a fresh skill
evaluator. The deterministic suite exercises real healthy/broken interactions and the
visual-review viewer; it does not claim universal agent accuracy.
