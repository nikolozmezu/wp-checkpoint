from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import visual_compare as visual

HAS_PILLOW = importlib.util.find_spec("PIL") is not None
if HAS_PILLOW:
    from PIL import Image


@unittest.skipUnless(HAS_PILLOW, "Optional Pillow dependency is unavailable")
class VisualCompareTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".validation-visual-", dir=ROOT)
        self.bundle = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.before = self.bundle / "before.png"
        self.after = self.bundle / "after.png"
        Image.new("RGB", (10, 8), (255, 255, 255)).save(self.before)
        Image.new("RGBA", (10, 8), (255, 255, 255, 255)).save(self.after)
        self.manifest = self.bundle / "comparison-input.json"

    def capture(self, path, run_id):
        return {
            "path": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "url": "http://local.example.test/article/?q=sample",
            "role": "Anonymous",
            "viewport": {"width": 10, "height": 8, "device_scale_factor": 1},
            "locale": "en_US", "state": "loaded", "fixture": "article-17",
            "captured_at": "2026-11-02T12:00:00+04:00",
            "provenance": {"run_id": run_id, "evidence_path": "screenshots/article.png"},
        }

    def data(self):
        return {"schema_version": 1, "pairs": [{
            "id": "article-desktop", "test_ids": ["ARTICLE-001"],
            "caption": "Article before and after the theme update",
            "before": self.capture(self.before, "report-before"),
            "after": self.capture(self.after, "report-after"),
        }]}

    def review(self, data=None, dirname="visual-review"):
        self.manifest.write_text(json.dumps(self.data() if data is None else data), encoding="utf-8")
        return visual.build_review(self.manifest, self.bundle / dirname)

    def test_identical_rgb_and_rgba_are_zero_difference(self):
        original = {path: path.read_bytes() for path in (self.before, self.after)}
        result = self.review()["pairs"][0]
        self.assertEqual(result["comparison"], "comparable")
        self.assertEqual(result["metrics"]["changed_pixels"], 0)
        self.assertEqual(result["metrics"]["compared_pixels"], 80)
        self.assertIsNone(result.get("status"))
        for path, content in original.items():
            self.assertEqual(path.read_bytes(), content)
        self.assertTrue((self.bundle / "visual-review/article-desktop-diff.png").is_file())

    def test_actual_changes_and_tolerance_are_measured(self):
        with Image.open(self.after) as image:
            image.putpixel((2, 3), (250, 255, 255, 255))
            image.putpixel((3, 3), (0, 0, 0, 255))
            image.save(self.after)
        result = self.review()["pairs"][0]
        self.assertEqual(result["metrics"]["changed_pixels"], 2)
        self.assertEqual(result["metrics"]["changed_ratio"], 2 / 80)
        data = self.data()
        data["pixel_threshold"] = 5
        tolerant = self.review(data, "tolerant-review")["pairs"][0]
        self.assertEqual(tolerant["metrics"]["changed_pixels"], 1)
        self.assertEqual(tolerant["metrics"]["pixel_threshold"], 5)

    def test_transparent_hidden_rgb_does_not_count_but_alpha_does(self):
        before = Image.new("RGBA", (2, 1), (255, 0, 0, 0))
        after = Image.new("RGBA", (2, 1), (0, 255, 0, 0))
        metrics, _ = visual.compare_pixels(before, after, [])
        self.assertEqual(metrics["changed_pixels"], 0)
        after.putpixel((0, 0), (255, 255, 255, 255))
        metrics, _ = visual.compare_pixels(before, after, [])
        self.assertEqual(metrics["changed_pixels"], 1)

    def test_masks_use_union_count_and_cannot_hide_all_pixels(self):
        before = Image.new("RGB", (4, 4), "white")
        after = Image.new("RGB", (4, 4), "black")
        masks = [{"x": 0, "y": 0, "width": 2, "height": 2, "reason": "Clock region"},
                 {"x": 1, "y": 1, "width": 2, "height": 2, "reason": "Rotating item"}]
        metrics, _ = visual.compare_pixels(before, after, masks)
        self.assertEqual(metrics["masked_pixels"], 7)
        self.assertEqual(metrics["compared_pixels"], 9)
        self.assertEqual(metrics["changed_pixels"], 9)
        self.assertEqual(metrics["changed_ratio"], 1)
        for mask in ({"x": 0, "y": 0, "width": 4, "height": 4}, {"x": 3, "y": 3, "width": 2, "height": 2}):
            with self.assertRaises(visual.ComparisonError):
                visual.compare_pixels(before, after, [mask])

    def test_context_mismatch_or_unknown_never_computes_a_diff(self):
        cases = [("role", "Administrator"), ("locale", "ka_GE"), ("url", "http://other.test/"),
                 ("fixture", "unknown"), ("state", "unresolved"), ("viewport", None),
                 ("viewport", {"width": 10, "height": 8, "device_scale_factor": None})]
        for index, (key, value) in enumerate(cases):
            with self.subTest(key=key, value=value):
                data = self.data()
                data["pairs"][0]["after"][key] = value
                result = self.review(data, f"review-{index}")["pairs"][0]
                self.assertEqual(result["comparison"], "incomparable")
                self.assertIsNone(result["metrics"])
                self.assertIsNone(result["diff"])
                self.assertTrue(any(key in reason for reason in result["reasons"]))

    def test_dimension_change_is_incomparable_not_resized(self):
        Image.new("RGB", (9, 8), "white").save(self.after)
        result = self.review()["pairs"][0]
        self.assertEqual(result["comparison"], "incomparable")
        self.assertTrue(any("dimensions differ" in reason for reason in result["reasons"]))
        with Image.open(self.after) as after:
            self.assertEqual(after.size, (9, 8))

    def test_hash_mismatch_invalidates_manifest_before_output(self):
        data = self.data()
        data["pairs"][0]["before"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(visual.ComparisonError, "hash mismatch"):
            self.review(data)
        self.assertFalse((self.bundle / "visual-review").exists())

    def test_evidence_escape_and_secret_urls_are_rejected(self):
        for path in ("../outside.png", "C:\\private.png", "C:private.png", "/tmp/private.png", "https://remote.test/a.png"):
            with self.subTest(path=path):
                data = self.data()
                data["pairs"][0]["before"]["path"] = path
                with self.assertRaises(visual.ComparisonError):
                    self.review(data)
        for url in ("https://user:password@site.test/", "https://site.test/?access_token=secret", "https://site.test/?_wpnonce=secret", "https://site.test/#token=secret"):
            with self.subTest(url=url):
                data = self.data()
                data["pairs"][0]["after"]["url"] = url
                with self.assertRaises(visual.ComparisonError):
                    self.review(data)

    def test_symlink_input_is_rejected_even_when_inside_bundle(self):
        link = self.bundle / "alias.png"
        try:
            link.symlink_to(self.before)
        except (OSError, NotImplementedError):
            self.skipTest("Host does not permit creating a test symlink")
        data = self.data()
        data["pairs"][0]["before"]["path"] = link.name
        with self.assertRaisesRegex(visual.ComparisonError, "Symlink"):
            self.review(data)

    def test_output_does_not_escape_or_replace_previous_review(self):
        self.review()
        saved = (self.bundle / "visual-review/index.html").read_bytes()
        with self.assertRaisesRegex(visual.ComparisonError, "already exists"):
            self.review()
        self.assertEqual((self.bundle / "visual-review/index.html").read_bytes(), saved)
        with self.assertRaisesRegex(visual.ComparisonError, "inside the report bundle"):
            visual.build_review(self.manifest, self.bundle.parent / "outside-visual-review")

    def test_html_escapes_labels_embeds_images_and_exposes_slider(self):
        data = self.data()
        payload = '</script><script src="https://bad.test/x.js">alert(1)</script>'
        data["pairs"][0]["caption"] = payload
        data["pairs"][0]["after"]["provenance"]["run_id"] = payload
        self.review(data)
        markup = (self.bundle / "visual-review/index.html").read_text(encoding="utf-8")
        self.assertNotIn(payload, markup)
        self.assertIn("&lt;/script&gt;", markup)
        self.assertIn('type="range"', markup)
        self.assertIn("input.value+'%'", markup)
        self.assertIn("data:image/png;base64,", markup)
        self.assertIn("connect-src 'none'", markup)
        self.assertNotIn('src="https://', markup)
        self.assertIn(visual.NOTICE, markup)

    def test_decode_error_leaves_explicit_incomplete_review(self):
        self.after.write_bytes(b"not a png")
        with self.assertRaisesRegex(visual.ComparisonError, "Cannot decode"):
            self.review()
        summary = json.loads((self.bundle / "visual-review/comparison.json").read_text())
        self.assertEqual(summary["status"], "Incomplete")
        self.assertFalse((self.bundle / "visual-review/index.html").exists())

    def test_cli_outputs_review_paths_not_product_verdict(self):
        self.manifest.write_text(json.dumps(self.data()), encoding="utf-8")
        run = subprocess.run([sys.executable, str(ROOT / "scripts/visual_compare.py"), str(self.manifest), "--output", str(self.bundle / "review-cli")], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["comparable"], 1)
        self.assertNotIn("PASS", {key for key in result})
        self.assertTrue(Path(result["review"]).is_file())


class VisualDependencyTests(unittest.TestCase):
    def test_missing_optional_dependency_has_distinct_exit_and_no_output(self):
        with tempfile.TemporaryDirectory(prefix=".validation-visual-", dir=ROOT) as temp:
            output = Path(temp) / "review"
            with patch.object(visual, "image_modules", side_effect=visual.DependencyUnavailable("Visual comparison unavailable: Pillow missing")):
                with patch("sys.stderr"):
                    code = visual.main([str(Path(temp) / "manifest.json"), "--output", str(output)])
            self.assertEqual(code, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
