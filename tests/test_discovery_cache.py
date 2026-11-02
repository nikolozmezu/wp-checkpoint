from copy import deepcopy
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import discovery_cache as cache


class DiscoveryCacheTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".validation-discovery-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.project = self.base / "site"
        self.project.mkdir()
        (self.project / "plugins").mkdir()
        (self.project / "plugins/search.php").write_text("<?php // search implementation", encoding="utf-8")
        (self.project / "admin.php").write_text("<?php // editorial implementation", encoding="utf-8")
        (self.project / "options.json").write_text('{"active_plugins": ["search"]}', encoding="utf-8")
        self.plan = self.base / "testing-after-update.md"
        self.plan.write_text("## F. Detailed Test Catalogue\n#### SEARCH-001 — search\n#### ADMIN-001 — editor\n## G. Shared Vocabulary\n", encoding="utf-8")
        self.manifest_path = self.base / "sources.json"
        self.output = self.base / "discovery.json"
        self.manifest = {
            "schema_version": 1,
            "context": {"environment_id": "local-editorial", "site_url": "http://fixture.invalid", "blog_id": 1},
            "sources": [
                {"path": "plugins/search.php", "test_ids": ["SEARCH-001"], "kind": "static", "category": "source", "provenance": "Local plugin source, lookup handler", "captured_at": "2026-11-02T10:00:00+04:00"},
                {"path": "admin.php", "test_ids": ["ADMIN-001"], "kind": "static", "category": "source", "provenance": "Local editorial handler", "captured_at": "2026-11-02T10:00:00+04:00"},
            ],
            "watches": [{"path": "plugins", "patterns": ["**/*.php"], "test_ids": ["SEARCH-001"]}],
        }
        self.write_manifest()

    def write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")

    def snapshot(self):
        self.write_manifest()
        return cache.build_snapshot(self.project, self.plan, self.manifest_path)

    def capture(self):
        snapshot = self.snapshot()
        cache.save(snapshot, self.output, reviewed=True)
        return cache.read_json(self.output)

    def test_unchanged_static_inputs_are_reusable_without_cached_results(self):
        old = self.capture()
        self.manifest["sources"][0]["captured_at"] = "2026-11-03T10:00:00+04:00"
        result = cache.compare(self.snapshot(), old)
        self.assertEqual(result["status"], "static_sources_unchanged")
        self.assertEqual(result["affected_test_ids"], [])
        self.assertEqual(result["reusable_static_sources"], ["admin.php", "plugins/search.php"])
        saved = self.output.read_text(encoding="utf-8")
        self.assertNotIn("<?php", saved)
        self.assertNotIn('"status": "PASS"', saved)

    def test_content_changes_and_deletions_reach_their_cards(self):
        old = self.capture()
        (self.project / "plugins/search.php").write_text("<?php // changed handler", encoding="utf-8")
        result = cache.compare(self.snapshot(), old)
        self.assertFalse(result["full_refresh"])
        self.assertEqual(result["affected_test_ids"], ["SEARCH-001"])
        (self.project / "plugins/search.php").unlink()
        result = cache.compare(self.snapshot(), old)
        self.assertEqual(result["affected_test_ids"], ["SEARCH-001"])
        self.assertTrue(any("source missing" in reason for change in result["changes"] for reason in change["reasons"]))

    def test_watched_new_source_is_detected_even_if_not_in_source_manifest(self):
        old = self.capture()
        (self.project / "plugins/new.php").write_text("<?php // new behavior", encoding="utf-8")
        result = cache.compare(self.snapshot(), old)
        self.assertEqual(result["affected_test_ids"], ["SEARCH-001"])
        self.assertIn("plugins/new.php", next(item["paths"] for item in result["changes"] if "watch" in item))
        self.manifest["watches"][0]["test_ids"] = []
        result = cache.compare(self.snapshot(), old)
        self.assertTrue(result["full_refresh"])
        # An entirely new unbounded watch must also invalidate the plan.
        self.manifest["watches"].append({"path": ".", "patterns": ["*.json"], "test_ids": []})
        result = cache.compare(self.snapshot(), old)
        self.assertTrue(result["full_refresh"])
        self.assertEqual(result["affected_test_ids"], ["ADMIN-001", "SEARCH-001"])

    def test_unindexed_cards_are_not_implicitly_treated_as_reusable(self):
        self.manifest["sources"] = self.manifest["sources"][:1]
        old = self.capture()
        result = cache.compare(self.snapshot(), old)
        self.assertEqual(result["unindexed_test_ids"], ["ADMIN-001"])
        self.assertEqual(result["affected_test_ids"], ["ADMIN-001"])
        self.assertEqual(result["status"], "refresh_required")

    def test_removed_history_does_not_create_unindexed_active_work(self):
        text = self.plan.read_text(encoding="utf-8").replace("## G.", "#### OLD-001 — retired\n- **Lifecycle:** REMOVED\n- **Status:** NOT RUN\n## G.")
        self.plan.write_text(text, encoding="utf-8")
        old = self.capture()
        result = cache.compare(self.snapshot(), old)
        self.assertEqual(result["unindexed_test_ids"], [])
        self.assertNotIn("OLD-001", old["test_ids"])

    def test_configuration_and_activation_are_volatile_even_when_declared_static(self):
        for category in ("configuration", "activation", "inventory", "runtime"):
            with self.subTest(category=category):
                self.manifest["sources"] = [{"path": "options.json", "test_ids": ["ADMIN-001"], "kind": "static", "category": category, "provenance": "Current read-only non-secret options export", "captured_at": "2026-11-02T10:00:00+04:00"}]
                old = self.capture()
                result = cache.compare(self.snapshot(), old)
                self.assertEqual(result["affected_test_ids"], ["ADMIN-001"])
                self.assertEqual(old["sources"]["options.json"]["kind"], "volatile")

    def test_plan_context_and_plugin_version_drift_require_full_refresh(self):
        old = self.capture()
        for key, value in (("plan_sha256", "0" * 64), ("project_root", "different-project"), ("plan_path", "different-plan"), ("plugin_version", "0.1.0"), ("context", {"environment_id": "another-local"})):
            with self.subTest(key=key):
                changed = deepcopy(old)
                changed[key] = value
                result = cache.compare(self.snapshot(), changed)
                self.assertTrue(result["full_refresh"])
                self.assertEqual(result["affected_test_ids"], ["ADMIN-001", "SEARCH-001"])

    def test_missing_cache_and_unsupported_schema_do_not_claim_reuse(self):
        result = cache.compare(self.snapshot(), None)
        self.assertTrue(result["full_refresh"])
        self.output.write_text('{"kind":"wp-checkpoint-discovery-cache","schema_version":99}', encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            code = cache.main(["check", "--root", str(self.project), "--plan", str(self.plan), "--manifest", str(self.manifest_path), "--cache", str(self.output)])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(stream.getvalue())["full_refresh"])

    def test_check_does_not_write_and_capture_requires_review(self):
        before = sorted(path.relative_to(self.base).as_posix() for path in self.base.rglob("*") if path.is_file())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(cache.main(["check", "--root", str(self.project), "--plan", str(self.plan), "--manifest", str(self.manifest_path), "--cache", str(self.output)]), 0)
        after = sorted(path.relative_to(self.base).as_posix() for path in self.base.rglob("*") if path.is_file())
        self.assertEqual(before, after)
        with self.assertRaises(cache.CacheError):
            cache.save(self.snapshot(), self.output, reviewed=False)
        self.assertFalse(self.output.exists())

    def test_escape_secret_and_symlink_sources_are_rejected_before_hashing(self):
        for name in ("../outside.php", "C:/outside.php", "plugins/../../outside.php", ".env.local", "wp-config.php", ".aws/credentials", "dump.sql", "key.pem"):
            with self.subTest(path=name):
                self.manifest["sources"][0]["path"] = name
                with self.assertRaises(cache.CacheError):
                    self.snapshot()
        self.manifest["sources"][0]["path"] = "plugins/search.php"
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path.name == "search.php" or original(path)):
            with self.assertRaisesRegex(cache.CacheError, "Symlink"):
                self.snapshot()

    def test_watch_does_not_hash_matching_secret_files(self):
        (self.project / "wp-config.php").write_text("secret fixture contents", encoding="utf-8")
        self.manifest["watches"] = [{"path": ".", "patterns": ["*.php"], "test_ids": []}]
        with self.assertRaisesRegex(cache.CacheError, "Secret-bearing"):
            self.snapshot()

    def test_junction_watch_and_output_directories_are_rejected(self):
        with patch.object(Path, "is_junction", lambda path: path.name == "plugins", create=True):
            with self.assertRaisesRegex(cache.CacheError, "junction"):
                self.snapshot()
        snapshot = self.snapshot()
        with patch.object(Path, "is_junction", lambda path: path == self.base, create=True):
            with self.assertRaisesRegex(cache.CacheError, "junction"):
                cache.save(snapshot, self.output, reviewed=True)

    def test_invalid_ids_times_and_credential_urls_are_rejected(self):
        original = deepcopy(self.manifest)
        for mutation in (lambda m: m["sources"][0].update(test_ids=["MISSING-001"]), lambda m: m["sources"][0].update(captured_at="2026-11-02"), lambda m: m["context"].update(site_url="https://user:secret@fixture.invalid"), lambda m: m["context"].update(password="fixture-secret")):
            self.manifest = deepcopy(original)
            mutation(self.manifest)
            with self.assertRaises(cache.CacheError):
                self.snapshot()

    def test_capture_will_not_overwrite_unrelated_or_other_project_json(self):
        self.output.write_text('{"unrelated":true}', encoding="utf-8")
        with self.assertRaises(cache.CacheError):
            cache.save(self.snapshot(), self.output, reviewed=True)
        self.output.unlink()
        old = self.capture()
        old["project_root"] = "another-project"
        self.output.write_text(json.dumps(old), encoding="utf-8")
        with self.assertRaises(cache.CacheError):
            cache.save(self.snapshot(), self.output, reviewed=True)

    def test_machine_json_survives_windows_legacy_stdout_with_georgian_paths(self):
        (self.project / "plugins/ძიება.php").write_text("<?php // localized filename", encoding="utf-8")
        self.manifest["sources"][0]["path"] = "plugins/ძიება.php"
        self.write_manifest()
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="cp1252")
        with contextlib.redirect_stdout(stream):
            code = cache.main(["check", "--root", str(self.project), "--plan", str(self.plan), "--manifest", str(self.manifest_path), "--cache", str(self.output)])
        stream.flush()
        payload = buffer.getvalue().decode("ascii")
        self.assertEqual(code, 0)
        self.assertIn("plugins/ძიება.php", [item.get("path") for item in json.loads(payload)["changes"]])


if __name__ == "__main__":
    unittest.main()
