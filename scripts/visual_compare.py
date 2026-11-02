#!/usr/bin/env python3
"""Compare recorded screenshots and build an offline review, never a test verdict.

Python 3.10+; Pillow is an optional dependency, installed separately by the user.
Only explicitly supplied images within the manifest's report bundle are read.
The source images, baseline and previous review outputs are never changed.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime
import hashlib
import html
import io
import json
from pathlib import Path, PureWindowsPath
import re
import sys
from urllib.parse import parse_qsl, urlsplit
import warnings


MAX_IMAGE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_IMAGE_BYTES = 256 * 1024 * 1024
MAX_PIXELS = 40_000_000
UNKNOWN = {"", "unknown", "not established", "unresolved", "not available", "n/a"}
TEST_ID = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}\Z")
DIGEST = re.compile(r"[0-9a-f]{64}\Z")
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
CONTEXT_KEYS = ("url", "role", "viewport", "locale", "state", "fixture")
NOTICE = "Pixel differences are review evidence, not PASS/FAIL or proof of a regression."


class ComparisonError(ValueError):
    pass


class DependencyUnavailable(RuntimeError):
    pass


def image_modules():
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError as exc:
        raise DependencyUnavailable("Visual comparison unavailable: Pillow is not installed. Install scripts/requirements-visual.txt in the chosen Python environment; no files were generated.") from exc
    return Image, ImageChops, ImageDraw


def require(condition, message):
    if not condition:
        raise ComparisonError(message)


def unknown(value):
    return value is None or isinstance(value, str) and value.strip().casefold() in UNKNOWN


def is_link(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def relative_path(value):
    require(isinstance(value, str) and value and "\x00" not in value, "Evidence paths must be nonempty relative strings")
    path = Path(value.replace("\\", "/"))
    windows = PureWindowsPath(value)
    require(not path.is_absolute() and not windows.drive and not windows.root and not urlsplit(value).scheme and ".." not in path.parts,
            f"Evidence path escapes the bundle: {value!r}")
    return path


def contained_file(bundle, value):
    relative = relative_path(value)
    current = bundle
    for component in relative.parts:
        current = current / component
        require(not is_link(current), f"Symlink/junction evidence is not allowed: {value!r}")
    resolved = current.resolve()
    require(resolved.is_relative_to(bundle) and resolved.is_file(), f"Evidence must be an existing file inside the bundle: {value!r}")
    require(resolved.suffix.lower() in IMAGE_EXTENSIONS, f"Unsupported screenshot extension: {value!r}")
    require(resolved.stat().st_size <= MAX_IMAGE_BYTES, f"Screenshot exceeds {MAX_IMAGE_BYTES} bytes: {value!r}")
    return resolved


def check_url(value):
    if unknown(value):
        return
    try:
        url = urlsplit(value)
        require(url.scheme in {"http", "https"} and bool(url.hostname) and not url.username and not url.password,
                "Capture URL must be credential-free HTTP(S), or explicitly unknown")
        # These values must be redacted before any evidence bundle is saved.
        forbidden = {"password", "passwd", "token", "accesstoken", "refreshtoken", "apikey", "authorization", "auth", "nonce", "wpnonce", "secret", "signature", "session", "sessionid", "invite", "invitation"}
        for key, _ in parse_qsl(url.query, keep_blank_values=True) + parse_qsl(url.fragment, keep_blank_values=True):
            normalized = re.sub(r"[^a-z0-9]", "", key.casefold())
            require(normalized not in forbidden and not normalized.endswith(("token", "password", "secret")), "Capture URL contains a secret-bearing parameter; redact it before creating a comparison manifest")
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ComparisonError):
            raise
        raise ComparisonError("Invalid capture URL") from exc


def timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.utcoffset() is not None
    except ValueError:
        return False


def prepare_capture(bundle, capture):
    require(isinstance(capture, dict), "Each before/after capture must be an object")
    for key in ("path", "sha256", "url", "role", "locale", "state", "fixture", "captured_at"):
        require(isinstance(capture.get(key), str) and bool(capture[key]), f"Capture requires {key}")
    require(bool(DIGEST.fullmatch(capture["sha256"])), "Capture sha256 must be a lowercase SHA256 digest")
    check_url(capture["url"])
    require(timestamp(capture["captured_at"]), "Capture captured_at needs an ISO timestamp with UTC offset")
    require("viewport" in capture, "Capture requires viewport metadata, or null for unknown")
    viewport = capture["viewport"]
    require(viewport is None or isinstance(viewport, dict), "Capture viewport must be an object, or null for unknown")
    if viewport is not None:
        require(all(key in viewport and (viewport[key] is None or type(viewport[key]) is int and viewport[key] > 0) for key in ("width", "height")), "Viewport width/height must be positive integers or null")
        scale = viewport.get("device_scale_factor")
        require("device_scale_factor" in viewport and (scale is None or type(scale) in (int, float) and 0 < scale < float("inf")), "Viewport device_scale_factor must be a finite positive number or null")
    provenance = capture.get("provenance")
    require(isinstance(provenance, dict), "Capture requires provenance")
    require(isinstance(provenance.get("run_id"), str) and not unknown(provenance["run_id"]), "Capture provenance requires a known source run_id")
    relative_path(provenance.get("evidence_path"))
    if "checkpoint_sha256" in provenance:
        require(isinstance(provenance["checkpoint_sha256"], str) and bool(DIGEST.fullmatch(provenance["checkpoint_sha256"])), "Invalid provenance checkpoint_sha256")
    path = contained_file(bundle, capture["path"])
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == capture["sha256"], f"Screenshot hash mismatch: {capture['path']!r}")
    return dict(capture), path, raw


def prepare_manifest(manifest_path):
    require(not is_link(manifest_path), "Comparison manifest cannot be a symlink/junction")
    manifest_path = manifest_path.resolve()
    bundle = manifest_path.parent
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ComparisonError(f"Cannot read comparison manifest: {exc}") from exc
    require(isinstance(manifest, dict) and type(manifest.get("schema_version")) is int and manifest["schema_version"] == 1, "Unsupported comparison schema_version (expected 1)")
    threshold = manifest.get("pixel_threshold", 0)
    require(type(threshold) is int and 0 <= threshold <= 254, "pixel_threshold must be an integer from 0 to 254")
    pairs = manifest.get("pairs")
    require(isinstance(pairs, list) and bool(pairs), "Comparison requires a nonempty pairs array")
    prepared, seen, total_bytes = [], set(), 0
    for pair in pairs:
        require(isinstance(pair, dict), "Each pair must be an object")
        pair_id = pair.get("id")
        require(isinstance(pair_id, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}", pair_id)), "Pair id must be a safe identifier of at most 80 characters")
        require(pair_id not in seen, f"Duplicate pair id: {pair_id}")
        seen.add(pair_id)
        test_ids = pair.get("test_ids")
        require(isinstance(test_ids, list) and bool(test_ids) and all(isinstance(value, str) and TEST_ID.fullmatch(value) for value in test_ids), f"{pair_id}: test_ids must contain valid test IDs")
        require(isinstance(pair.get("caption"), str) and bool(pair["caption"].strip()), f"{pair_id}: caption is required")
        captures = {side: prepare_capture(bundle, pair.get(side)) for side in ("before", "after")}
        total_bytes += sum(len(value[2]) for value in captures.values())
        require(total_bytes <= MAX_TOTAL_IMAGE_BYTES, "Screenshot batch exceeds 256 MiB; split it into smaller review manifests")
        masks = pair.get("masks", [])
        require(isinstance(masks, list), f"{pair_id}: masks must be an array")
        for mask in masks:
            require(isinstance(mask, dict), f"{pair_id}: mask must be an object")
            require(all(type(mask.get(key)) is int and mask[key] >= 0 for key in ("x", "y")), f"{pair_id}: mask origin must be nonnegative integers")
            require(all(type(mask.get(key)) is int and mask[key] > 0 for key in ("width", "height")), f"{pair_id}: mask dimensions must be positive integers")
            require(isinstance(mask.get("reason"), str) and not unknown(mask["reason"]), f"{pair_id}: every mask needs a specific reason")
        prepared.append((pair, captures, masks))
    return bundle, threshold, prepared


def context_gaps(before, after):
    gaps = []
    for key in CONTEXT_KEYS:
        viewport_unknown = key == "viewport" and any(isinstance(capture[key], dict) and any(value is None for value in capture[key].values()) for capture in (before, after))
        if unknown(before[key]) or unknown(after[key]) or viewport_unknown:
            gaps.append(f"{key} is unknown")
        elif before[key] != after[key]:
            gaps.append(f"{key} differs")
    return gaps


def open_image(raw, path, Image):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as source:
                require(source.format in {"PNG", "JPEG", "WEBP"}, f"Unsupported screenshot content: {path.name}")
                expected_format = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}[path.suffix.lower()]
                require(source.format == expected_format, "Screenshot file extension does not match its decoded format")
                require(getattr(source, "n_frames", 1) == 1, "Animated screenshots are not comparable; capture a single reproducible state")
                require(source.width * source.height <= MAX_PIXELS, f"Screenshot exceeds {MAX_PIXELS} pixels; use smaller matched captures")
                source.load()
                return source.convert("RGBA")
    except ComparisonError:
        raise
    except Exception as exc:
        raise ComparisonError(f"Cannot decode screenshot {path.name}: {exc}") from exc


def compare_pixels(before, after, masks, threshold=0):
    Image, ImageChops, ImageDraw = image_modules()
    require(before.size == after.size, "Pixel comparison requires equal dimensions")
    before, after = before.convert("RGBA"), after.convert("RGBA")
    width, height = before.size
    mask = Image.new("L", before.size, 0)
    draw = ImageDraw.Draw(mask)
    for rectangle in masks:
        x, y, w, h = (rectangle[key] for key in ("x", "y", "width", "height"))
        require(x + w <= width and y + h <= height, "Mask extends outside the screenshot")
        draw.rectangle((x, y, x + w - 1, y + h - 1), fill=255)
    masked = mask.histogram()[255]
    require(masked < width * height, "Masks cannot hide the entire screenshot")
    # Compare appearance on black AND white: invisible RGB in fully transparent
    # pixels does not count, while an alpha change remains observable.
    maximum = Image.new("L", before.size, 0)
    rendered_after = None
    for background in ((0, 0, 0, 255), (255, 255, 255, 255)):
        base = Image.new("RGBA", before.size, background)
        rendered_before = Image.alpha_composite(base, before).convert("RGB")
        rendered_after = Image.alpha_composite(base, after).convert("RGB")
        difference = ImageChops.difference(rendered_before, rendered_after)
        for channel in difference.split():
            maximum = ImageChops.lighter(maximum, channel)
    changed = maximum.point(lambda value: 255 if value > threshold else 0)
    changed.paste(0, mask=mask)
    count = changed.histogram()[255]
    compared = width * height - masked
    highlight = Image.new("RGB", before.size, (255, 0, 90))
    overlay = Image.composite(highlight, rendered_after, changed)
    return {"changed_pixels": count, "compared_pixels": compared, "masked_pixels": masked, "changed_ratio": count / compared, "pixel_threshold": threshold}, overlay


def data_uri(content, suffix):
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}[suffix.lower()]
    return f"data:{mime};base64," + base64.b64encode(content).decode("ascii")


def render_html(results, title="Screenshot review"):
    escape = html.escape
    cards = []
    for pair in results:
        meta = pair["result"]
        before, after = pair["before_uri"], pair["after_uri"]
        label = f"{meta['id']} · {', '.join(meta['test_ids'])}"
        status = meta["comparison"]
        detail = "; ".join(meta["reasons"]) if meta["reasons"] else f"{meta['metrics']['changed_pixels']:,} changed / {meta['metrics']['compared_pixels']:,} compared pixels ({meta['metrics']['changed_ratio']:.3%}); {meta['metrics']['masked_pixels']:,} masked."
        slider = ""
        diff = ""
        if status == "comparable":
            slider = f'<div class="slider" style="--cut:50%"><img src="{before}" alt="Before"><img class="after" src="{after}" alt="After"><span class="divider" aria-hidden="true"></span></div><label class="range-label">Before/after reveal <input type="range" min="0" max="100" value="50" aria-label="Reveal after image for {escape(meta["id"], quote=True)}"></label>'
            diff = f'<figure><img src="{pair["diff_uri"]}" alt="Changed pixels highlighted in pink"><figcaption>Changed pixels highlighted in pink; original evidence is unchanged.</figcaption></figure>'
        masks = f'<details><summary>Masks ({len(meta["masks"])})</summary><pre>{escape(json.dumps(meta["masks"], ensure_ascii=False, indent=2))}</pre></details>' if meta["masks"] else ""
        context = {side: meta[side] for side in ("before", "after")}
        cards.append(f'<article id="{escape(meta["id"], quote=True)}"><h2>{escape(label)}</h2><p>{escape(meta["caption"])}</p><p class="status">{escape(status)} — {escape(detail)}</p>{slider}<div class="columns"><figure><img src="{before}" alt="Before"><figcaption>Before</figcaption></figure><figure><img src="{after}" alt="After"><figcaption>After</figcaption></figure></div>{diff}{masks}<details><summary>Capture context and provenance</summary><pre>{escape(json.dumps(context, ensure_ascii=False, indent=2))}</pre></details></article>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src data:; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'none'; base-uri 'none'; form-action 'none'"><title>{escape(title)}</title>
<style>body{{font:16px/1.5 system-ui,sans-serif;max-width:1200px;margin:auto;padding:24px;background:#f5f6f8;color:#172331}}h1{{margin-bottom:8px}}article{{background:white;border:1px solid #d6dde5;border-radius:12px;margin:24px 0;padding:20px}}h2{{font-size:20px}}.status{{padding:10px;background:#edf2f7;border-radius:6px}}img{{display:block;max-width:100%;height:auto}}figure{{margin:0}}figcaption{{padding:8px 0;color:#4b596a}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:20px 0}}.slider{{position:relative;width:fit-content;max-width:100%;background:repeating-conic-gradient(#ddd 0 25%,white 0 50%) 0/20px 20px}}.slider .after{{position:absolute;inset:0;width:100%;height:100%;clip-path:inset(0 calc(100% - var(--cut)) 0 0)}}.divider{{position:absolute;left:var(--cut);top:0;bottom:0;width:2px;background:#ff005a}}.range-label{{display:flex;gap:14px;align-items:center;margin-top:10px}}input[type=range]{{flex:1}}details{{margin-top:16px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}}@media(max-width:700px){{.columns{{grid-template-columns:1fr}}body{{padding:12px}}article{{padding:14px}}}}</style></head><body><h1>{escape(title)}</h1><p>{escape(NOTICE)}</p><p>Offline review. Capture URLs below are plain text and are never fetched. Unknown or mismatched context is shown as incomparable.</p>{''.join(cards)}
<script>document.querySelectorAll('input[type=range]').forEach(function(input){{input.addEventListener('input',function(){{input.closest('article').querySelector('.slider').style.setProperty('--cut',input.value+'%');}});}});</script></body></html>'''


def output_path(bundle, requested):
    requested = Path(requested).absolute()
    require(not requested.exists() and not is_link(requested), "Review output already exists; choose a fresh directory")
    require(requested.parent.is_dir(), "Review output parent must already exist inside the gated report bundle")
    resolved = requested.resolve()
    require(resolved != bundle and resolved.is_relative_to(bundle), "Review output must be a fresh directory inside the report bundle")
    require(requested.is_relative_to(bundle), "Review output must be expressed inside the resolved report bundle")
    current = bundle
    for component in requested.relative_to(bundle).parts:
        current /= component
        require(not is_link(current), "Review output cannot traverse a symlink/junction")
    return resolved


def build_review(manifest_path, requested_output):
    Image, _, _ = image_modules()
    bundle, threshold, pairs = prepare_manifest(Path(manifest_path))
    output = output_path(bundle, requested_output)
    output.mkdir()  # Refuse races/existing output; never overwrite an old review.
    summary = {"schema_version": 1, "status": "Incomplete", "notice": NOTICE, "pairs": []}
    summary_path = output / "comparison.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    html_pairs = []
    for pair, captures, masks in pairs:
        before, after = (captures[side][0] for side in ("before", "after"))
        before_image, after_image = (open_image(captures[side][2], captures[side][1], Image) for side in ("before", "after"))
        gaps = context_gaps(before, after)
        if before_image.size != after_image.size:
            gaps.append(f"image dimensions differ: {before_image.size} vs {after_image.size}")
        result = {"id": pair["id"], "test_ids": pair["test_ids"], "caption": pair["caption"], "comparison": "incomparable" if gaps else "comparable", "reasons": gaps, "before": before, "after": after, "masks": masks, "metrics": None, "diff": None}
        row = {"result": result, "before_uri": data_uri(captures["before"][2], captures["before"][1].suffix), "after_uri": data_uri(captures["after"][2], captures["after"][1].suffix), "diff_uri": None}
        if not gaps:
            metrics, overlay = compare_pixels(before_image, after_image, masks, threshold)
            filename = f"{pair['id']}-diff.png"
            overlay.save(output / filename, format="PNG")
            result.update(metrics=metrics, diff=filename)
            row["diff_uri"] = data_uri((output / filename).read_bytes(), ".png")
        summary["pairs"].append(result)
        html_pairs.append(row)
    summary["status"] = "Complete"
    (output / "index.html").write_text(render_html(html_pairs), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Comparison manifest directly inside its gated report bundle")
    parser.add_argument("--output", type=Path, required=True, help="New review directory inside that same bundle")
    args = parser.parse_args(argv)
    try:
        summary = build_review(args.manifest, args.output)
    except DependencyUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (ComparisonError, OSError, UnicodeError) as exc:
        print(f"Visual review not completed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"review": str(args.output.resolve() / "index.html"), "pairs": len(summary["pairs"]), "comparable": sum(pair["comparison"] == "comparable" for pair in summary["pairs"]), "incomparable": sum(pair["comparison"] == "incomparable" for pair in summary["pairs"]), "notice": NOTICE}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
