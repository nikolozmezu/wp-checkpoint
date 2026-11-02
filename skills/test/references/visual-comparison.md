# Recorded screenshot comparison

Use this for matched before/after screenshots when a visual review is useful. Ordinary
testing and functional judgments do not depend on this optional capability. The helper
does image analysis only; it never visits a site, generates substitute evidence, chooses
a new baseline, changes the original images or issues a product PASS/FAIL verdict.

## Prepare evidence

Use the matching rules in `references/before-after.md`: same known URL, role, viewport,
device scale, locale, state and fixture/content. Copy the matched before image into the
new report bundle, preserving its hash and source provenance. Obtain the after image
through the actual browser. Do not normalize, resize or retouch screenshots to make
them agree. Different image dimensions, unknown context or any differing context
field make a pair **incomparable**; the review still displays both images and explains
why no pixel comparison was made. Deliberate URL relocation requires separately
established identity mapping and manual review; this helper does not guess equivalence.

Pass the storage gate for the report bundle, the input `.json` and output `.html`,
`.json` and `.png` destinations before writing. Remove secrets and unnecessary personal
data from the captured evidence itself; the helper cannot reliably recognize arbitrary
personal data inside images or prose. URLs must contain no credentials, secret query
parameters or invitation tokens. Original source runs remain immutable.

Pillow is optional. Check it in the Python environment used for the plugin. If missing,
report **visual comparison unavailable** and retain ordinary screenshots/evidence;
never auto-install dependencies during a project test. For an explicitly authorized
setup, the dependency declaration is `scripts/requirements-visual.txt` (Pillow 10+).

## Input and command

Write `comparison-input.json` directly inside the current report bundle. Every image
path is relative to that bundle and must identify an existing PNG, JPEG or single-frame
WebP file within it; symlinks/junctions and path escapes are rejected. Every capture
must include its actual SHA256 and offset-bearing capture time.

```json
{
  "schema_version": 1,
  "pixel_threshold": 0,
  "pairs": [{
    "id": "HOME-001-desktop",
    "test_ids": ["HOME-001"],
    "caption": "Homepage navigation before and after the theme update",
    "before": {
      "path": "screenshots/before/HOME-001.png",
      "sha256": "ACTUAL_64_CHARACTER_LOWERCASE_SHA256",
      "url": "http://project.local/",
      "role": "Anonymous",
      "viewport": {"width": 1280, "height": 720, "device_scale_factor": 1},
      "locale": "en_US",
      "state": "loaded, menu closed",
      "fixture": "homepage content revision 17",
      "captured_at": "2026-11-02T10:00:00+04:00",
      "provenance": {
        "run_id": "report-2026-11-02",
        "evidence_path": "screenshots/HOME-001.png"
      }
    },
    "after": {
      "path": "screenshots/after/HOME-001.png",
      "sha256": "ACTUAL_64_CHARACTER_LOWERCASE_SHA256",
      "url": "http://project.local/",
      "role": "Anonymous",
      "viewport": {"width": 1280, "height": 720, "device_scale_factor": 1},
      "locale": "en_US",
      "state": "loaded, menu closed",
      "fixture": "homepage content revision 17",
      "captured_at": "2026-11-02T11:00:00+04:00",
      "provenance": {
        "run_id": "report-2026-11-02-2",
        "evidence_path": "screenshots/after/HOME-001.png"
      }
    },
    "masks": []
  }]
}
```

The example digests are placeholders: calculate the actual saved bytes. Optional
`provenance.checkpoint_sha256` records the source checkpoint hash. `run_id` and
`evidence_path` identify the original run/image, even when the before image was copied.
They are provenance to inspect, not a claim that an unavailable original was verified.

Use `unknown` for unavailable string context; use `viewport: null` or null for its
unavailable numeric values. Do not fabricate dimensions/device scale. These explicit
unknowns are accepted but make the comparison incomparable. Missing mandatory fields,
incorrect hashes, invalid images or unsafe paths are invalid input.

```text
python <plugin-root>/scripts/visual_compare.py <bundle>/comparison-input.json --output <bundle>/visual-review
```

The output parent must already exist within that same gated bundle. The output directory
must be new; choose `visual-review-2` for another review instead of replacing a prior
one. No source image, prior report or baseline is overwritten. The script reads the
hashed bytes once and uses those same bytes for decoding/display. Limits: 32 MiB per
input image, 256 MiB per batch, 40 million pixels per image; split very large captures.

## Masks and thresholds

Default `pixel_threshold: 0` counts any visible channel difference. An explicitly
chosen threshold from 0 to 254 ignores smaller per-channel differences and is recorded
with the results. It is not an acceptance threshold or a regression confidence score.

Use a mask only for an identified dynamic region that is irrelevant to this check,
such as a clock. Each mask is `{ "x": 10, "y": 20, "width": 80, "height": 25,
"reason": "Clock changes each minute; navigation under test is outside this region" }`
in **image pixels**, with the same coordinates applied to both captures. Record a
specific reason. Never mask the behavior being tested or use masking to hide a defect.
The helper checks bounds and refuses a fully masked image; semantic relevance still
needs review. Overlapping regions count once. Original images remain visible unmasked.

RGBA is compared as displayed on both black and white backgrounds: invisible RGB under
fully transparent pixels does not count, while changed opacity can still be detected.
Fonts, browser/OS rendering, animations and real content changes can produce legitimate
differences. Match capture conditions and assess the meaning of a highlighted change.

## Outputs and reporting

- `index.html`: offline, self-contained comparison with a keyboard-operable reveal
  slider, side-by-side images, highlighted changed pixels, captions and provenance.
  All images are embedded; capture URLs are plain text and no network is used.
- `comparison.json`: per-pair comparable/incomparable status, reasons, changed/compared/
  masked pixel counts, ratio, threshold, context and provenance.
- `<pair-id>-diff.png`: changed pixels highlighted in pink over the current capture,
  produced only for comparable pairs. It is a derived inspection aid, not raw evidence.

Exit 0 means review generation completed; it can include incomparable pairs and says
nothing about the site's correctness. Exit 1 means invalid input or output failure;
an interrupted directory retains `status: Incomplete` and is never a completed review.
Exit 2 means the optional image dependency is unavailable and no output was created.

Link the HTML from the technical report when generated. Each confirmed issue still
needs an observed consequence and the report's ordinary severity/classification rules.
Use the relevant before/after/diff figures in the short DOCX only when they explain that
issue; do not dump every successful comparison or convert a changed-pixel ratio into a
failure. Identical screenshots cannot establish an untested functional PASS.
