# Real WordPress and browser evaluation

This optional maintainer suite boots real WordPress 6.8.3, PHP 8.3 through WordPress
Playground, an in-memory SQLite database and Chromium. It binds only 127.0.0.1.
The custom editorial/catalogue plugin uses actual WordPress hooks and REST handlers;
it is not a WooCommerce compatibility suite. It never touches a client installation.

## Setup and run

Use Node >=24.18.0 and npm >=11.16.0, matching the pinned Playground dependencies.
Python 3.10+ with Pillow is needed for the visual-review helper. The regular plugin
does not require Node, Playground or Chromium installations just to use its skills.

From this directory:

    npm ci
    npm run setup
    npm test

Setup is an explicit download step: it verifies the pinned WordPress archive SHA256
from versions.json and installs Chromium matching the lockfile. No browser dependency
or application update is installed automatically by the project's normal testing skill.
For an explicitly authorized Python setup use scripts/requirements-visual.txt from the
repository root. The suite was exercised on Windows; supported browser OS libraries
must already be available on other hosts.

npm test creates a fresh .validation-runtime-* directory under the repository root,
with progressive observations, actual before/after screenshots, attributed PHP log
evidence, comparison-input.json, visual-review/index.html and a browser preview.
It asserts five healthy checks, the exact four seeded failures, and an unchanged search
control. It opens the generated review in a browser to check image loading, the slider
and absence of remote requests. Completion is recorded after independent browser/runtime
cleanup attempts; incomplete results or cleanup are not reported as a successful run.

Browser traffic is restricted to this disposable site's origin. WordPress outbound HTTP,
email, automatic updates and cron are disabled. The database/files exist in runtime
memory and are discarded when the server closes. The site does not listen on the LAN.
Browser captures and downloaded caches persist only as local evaluation artifacts.
No screenshot difference is used as an automatic functional PASS/FAIL verdict.

## Blind skill evaluation

The deterministic runner tests the fixture/checker/comparison wiring. It does not by
itself establish that Claude will discover every defect on an unfamiliar site.

For that separate evaluation, run:

    npm run serve -- healthy

The controller can type healthy or broken into that terminal to switch the same
in-memory site without changing its URL/identity. Ctrl+C closes it. Give a fresh tester
only the printed site URL, requirements.md, the actual plugin skill, verified environment
identity and a protected output directory. Withhold this README's oracle details,
fixture.php, run.mjs, oracle.json, controller console and previous evaluation results.

Have the tester create/review its plan and explicitly execute before. The controller
then changes the fixture and only tells the tester the controlled update is complete.
Execute after with the tester's own baseline. Preserve generated artifacts unchanged.
Afterward score actual findings against oracle.json: missed defects, false positives,
functional evidence, visual evidence and honest blocked coverage. Do not edit reports
to make the evaluation pass. Compare source identity explicitly because the WordPress
root /wordpress is virtual, inside this isolated runtime.

Official runtime: https://developer.wordpress.org/playground/
Browser library: https://playwright.dev/docs/library
