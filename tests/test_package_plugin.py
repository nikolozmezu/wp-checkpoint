import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import package_plugin as package


class PackagePluginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".validation-package-", dir=ROOT.parent)
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.source.mkdir()
        self.output = self.base / "bundle"
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "wp-checkpoint", "version": "1.3.0"}))
        self.write(".claude-plugin/marketplace.json", json.dumps({"name": "wp-checkpoint", "plugins": [{"name": "wp-checkpoint", "source": "."}]}))
        for path in package.REQUIRED - {".claude-plugin/plugin.json", ".claude-plugin/marketplace.json"}:
            self.write(path, "Source bytes with Georgian: ქართული\r\n")

    def write(self, name, content):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode("utf-8"))
        return path

    def test_bundle_preserves_runtime_bytes_and_small_eval_sources(self):
        additions = ["scripts/package_plugin.py", "scripts/requirements-visual.txt", "skills/test/references/visual-comparison.md", "tests/test_example.py", "evals/runtime/fixture.php", "evals/runtime/run.mjs", "evals/runtime/package.json", "evals/runtime/package-lock.json", "evals/fieldnotes/evidence/current-options.json", "evals/fieldnotes/archive/production-2025.log"]
        for name in additions:
            self.write(name, b"intentional source\r\n")
        result = package.build(self.source, self.output)
        self.assertEqual(result["status"], "prepared")
        self.assertEqual(result["version"], "1.3.0")
        self.assertEqual(result["files"], len(package.REQUIRED) + len(additions))
        for name in package.REQUIRED | set(additions):
            content = (self.source / name).read_bytes()
            self.assertEqual((self.output / name).read_bytes(), content)
            self.assertEqual(result["sha256"][name], hashlib.sha256(content).hexdigest())
        marketplace = json.loads((self.output / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(marketplace["plugins"][0]["source"], ".")

    def test_development_generated_and_secret_inputs_are_not_copied(self):
        omitted = [".git/config", ".validation-forward/old.json", "node_modules/large.js", "wp-config.php", "other-root/private.json",
                   "evals/runtime/node_modules/package/index.js", "evals/runtime/.cache/browser/chrome.exe", "evals/runtime/report-2026-11-02/checkpoint.json", "evals/runtime/screenshots/full.png", "evals/runtime/generated.log", "evals/runtime/.env", "evals/runtime/credentials.json", "tests/__pycache__/test.pyc", "evals/runtime/storage-state.json", "evals/runtime/run-state.json", "evals/runtime/wp-update-report.md", "scripts/example.tmp"]
        for name in omitted:
            self.write(name, "must not be copied")
        result = package.build(self.source, self.output)
        for name in omitted:
            self.assertFalse((self.output / name).exists(), name)
        self.assertEqual(result["files"], len(package.REQUIRED))

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        marker = self.output / "owned.txt"
        marker.write_text("preserve")
        with self.assertRaisesRegex(package.PackageError, "already exists"):
            package.build(self.source, self.output)
        self.assertEqual(marker.read_text(), "preserve")

    def test_output_cannot_recurse_into_source_or_use_ambiguous_paths(self):
        for output in (self.source / "bundle", Path("relative-output"), self.base / "not-created" / "bundle", self.base / "unused" / ".." / "bundle"):
            with self.subTest(output=output), self.assertRaises(package.PackageError):
                package.build(self.source, output)
        self.assertFalse((self.source / "bundle").exists())

    def test_unknown_or_secret_runtime_inputs_require_explicit_review(self):
        for name in ("scripts/credentials.json", "skills/test/private.key", "scripts/unknown.exe"):
            with self.subTest(name=name):
                path = self.write(name, "private or unsupported")
                with self.assertRaises(package.PackageError):
                    package.build(self.source, self.output)
                self.assertFalse(self.output.exists())
                path.unlink()

    def test_link_guard_rejects_source_junction_and_output_parent(self):
        original = package.is_link
        linked_source = self.source / "evals" / "linked"
        linked_source.mkdir(parents=True)
        with patch.object(package, "is_link", side_effect=lambda p: Path(p) == linked_source or original(p)):
            with self.assertRaisesRegex(package.PackageError, "Symlink/junction"):
                package.build(self.source, self.output)
        with patch.object(package, "is_link", side_effect=lambda p: Path(p) == self.base or original(p)):
            with self.assertRaisesRegex(package.PackageError, "Symlink/junction"):
                package.build(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_missing_or_external_marketplace_source_fails_before_writes(self):
        self.write(".claude-plugin/marketplace.json", json.dumps({"plugins": [{"name": "wp-checkpoint", "source": "../external"}]}))
        with self.assertRaisesRegex(package.PackageError, "source '.'"):
            package.build(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_large_asset_is_not_silently_vendored(self):
        self.write("evals/runtime/large.json", "x" * 100)
        with patch.object(package, "MAX_ASSET_BYTES", 50):
            with self.assertRaisesRegex(package.PackageError, "limit"):
                package.build(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_cli_handles_unicode_source_and_builds_no_installation(self):
        renamed = self.base / "პლაგინი"
        self.source.rename(renamed)
        run = subprocess.run([sys.executable, str(ROOT / "scripts/package_plugin.py"), "--source", str(renamed), "--output", str(self.output)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result["source"], str(renamed))
        self.assertIn("nothing was installed", result["note"])
        self.assertFalse((self.base / ".claude").exists())

    def test_stable_catalog_updates_pointer_and_preserves_prior_release(self):
        catalog = self.base / "catalog"
        first = catalog / "releases/1.3.0"
        package.build_catalog(self.source, first, catalog)
        prior = (first / ".claude-plugin/plugin.json").read_bytes()
        original_marketplace = (first / ".claude-plugin/marketplace.json").read_bytes()
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "wp-checkpoint", "version": "1.3.1"}))
        second = catalog / "releases/1.3.1"
        result = package.build_catalog(self.source, second, catalog)
        pointer = json.loads((catalog / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(pointer["plugins"][0]["source"], "./releases/1.3.1")
        self.assertEqual((first / ".claude-plugin/plugin.json").read_bytes(), prior)
        self.assertEqual((first / ".claude-plugin/marketplace.json").read_bytes(), original_marketplace)
        self.assertEqual((second / ".claude-plugin/marketplace.json").read_bytes(), (self.source / ".claude-plugin/marketplace.json").read_bytes())
        self.assertEqual(result["catalog"], str(catalog))

    def test_stable_catalog_refuses_unowned_wrong_target_and_repeated_version(self):
        catalog = self.base / "catalog"
        catalog.mkdir()
        with self.assertRaisesRegex(package.PackageError, "unrelated/unowned"):
            package.build_catalog(self.source, catalog / "releases/1.3.0", catalog)
        fresh = self.base / "fresh-catalog"
        with self.assertRaisesRegex(package.PackageError, "must equal"):
            package.build_catalog(self.source, fresh / "releases/wrong", fresh)
        self.assertFalse(fresh.exists())
        target = fresh / "releases/1.3.0"
        package.build_catalog(self.source, target, fresh)
        with self.assertRaisesRegex(package.PackageError, "already exists"):
            package.build_catalog(self.source, target, fresh)

    def test_failed_new_release_does_not_change_existing_catalogue_pointer(self):
        catalog = self.base / "catalog"
        package.build_catalog(self.source, catalog / "releases/1.3.0", catalog)
        pointer = catalog / ".claude-plugin/marketplace.json"
        original = pointer.read_bytes()
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "wp-checkpoint", "version": "1.3.1"}))
        with patch.object(package, "build", side_effect=OSError("simulated copy failure")):
            with self.assertRaises(OSError):
                package.build_catalog(self.source, catalog / "releases/1.3.1", catalog)
        self.assertEqual(pointer.read_bytes(), original)

    def test_catalog_cannot_redirect_to_unrelated_release(self):
        catalog = self.base / "catalog"
        package.build_catalog(self.source, catalog / "releases/1.3.0", catalog)
        pointer = catalog / ".claude-plugin/marketplace.json"
        data = json.loads(pointer.read_text())
        data["plugins"][0]["source"] = "../outside"
        pointer.write_text(json.dumps(data))
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "wp-checkpoint", "version": "1.3.1"}))
        with self.assertRaisesRegex(package.PackageError, "unexpected source path"):
            package.build_catalog(self.source, catalog / "releases/1.3.1", catalog)
        self.assertFalse((catalog / "releases/1.3.1").exists())


if __name__ == "__main__":
    unittest.main()
