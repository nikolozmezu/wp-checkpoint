import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import doctor


class DoctorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".validation-doctor-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        self.source.mkdir()
        (self.source / ".claude-plugin").mkdir()
        (self.source / "skills/test").mkdir(parents=True)
        (self.source / "scripts").mkdir()
        (self.source / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "wp-checkpoint", "version": "1.3.0"}), encoding="utf-8")
        (self.source / "skills/test/SKILL.md").write_text("Test skill source", encoding="utf-8")
        (self.source / "scripts/helper.py").write_text("# helper", encoding="utf-8")
        self.installed = self.base / "cache"
        shutil.copytree(self.source, self.installed)
        self.registry = self.base / "installed_plugins.json"
        self.settings = self.base / "settings.json"
        self.plugin_id = "wp-checkpoint@wp-checkpoint"
        self.entry = {"scope": "user", "installPath": str(self.installed), "version": "1.3.0"}
        self.write_registry()
        self.settings.write_text(json.dumps({"enabledPlugins": {self.plugin_id: True}, "env": {"SECRET": "never-show-this"}}), encoding="utf-8")

    def write_registry(self, entries=None):
        self.registry.write_text(json.dumps({"version": 2, "plugins": {self.plugin_id: entries or [self.entry], "unrelated-private-plugin@example": [{"private": "never-show-this-either"}]}}), encoding="utf-8")

    def run_doctor(self, **kwargs):
        return doctor.diagnose(self.source, self.registry, project=self.base, settings=[self.settings], **kwargs)

    def test_identical_cache_is_distinct_from_unknown_current_session(self):
        result = self.run_doctor()
        self.assertEqual(result["status"], "matches")
        self.assertIsNone(result["loaded_session_version"])
        self.assertEqual(result["loaded_version_source"], "unknown")
        installed = result["installations"][0]
        self.assertTrue(installed["cache_matches_source"])
        self.assertEqual(installed["runtime_files_checked"], 3)
        self.assertIsNone(installed["reload_needed"])
        output = json.dumps(result)
        self.assertNotIn("never-show-this", output)
        self.assertNotIn("unrelated-private-plugin", output)

    def test_equal_version_with_changed_runtime_is_detected(self):
        (self.source / "skills/test/SKILL.md").write_text("Updated behavior, same manifest version", encoding="utf-8")
        result = self.run_doctor()
        self.assertEqual(result["status"], "attention")
        item = result["installations"][0]
        self.assertEqual(item["different_files"], ["skills/test/SKILL.md"])
        self.assertIn("runtime_content_mismatch", item["problems"])
        self.assertNotIn("source_cache_version_mismatch", item["problems"])

    def test_matching_reported_version_does_not_prove_loaded_bytes_are_current(self):
        (self.source / "skills/test/SKILL.md").write_text("Edited without a version change", encoding="utf-8")
        item = self.run_doctor(loaded_version="1.3.0")["installations"][0]
        self.assertTrue(item["reported_session_version_matches_cache"])
        self.assertIn("runtime_content_mismatch", item["problems"])
        self.assertIsNone(item["reload_needed"])
        shutil.copyfile(self.source / "skills/test/SKILL.md", self.installed / "skills/test/SKILL.md")
        item = self.run_doctor(loaded_version="1.3.0")["installations"][0]
        self.assertTrue(item["cache_matches_source"])
        self.assertIsNone(item["reload_needed"], "matching disk bytes still cannot prove a running session reloaded")

    def test_registry_cache_source_and_reported_session_versions_remain_separate(self):
        self.entry["version"] = "1.2.0"
        self.write_registry()
        (self.installed / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "wp-checkpoint", "version": "1.2.2"}), encoding="utf-8")
        result = self.run_doctor(loaded_version="1.1.5")
        item = result["installations"][0]
        self.assertEqual(result["source_version"], "1.3.0")
        self.assertEqual(item["registered_version"], "1.2.0")
        self.assertEqual(item["cache_version"], "1.2.2")
        self.assertEqual(result["loaded_session_version"], "1.1.5")
        self.assertEqual(result["loaded_version_source"], "caller-reported")
        self.assertTrue(item["reload_needed"])
        self.assertIn("registry_cache_version_mismatch", item["problems"])

    def test_deleted_and_extra_runtime_files_are_not_hidden(self):
        (self.installed / "scripts/helper.py").unlink()
        (self.installed / "skills/test/obsolete.md").write_text("obsolete", encoding="utf-8")
        item = self.run_doctor()["installations"][0]
        self.assertEqual(item["different_files"], ["scripts/helper.py", "skills/test/obsolete.md"])

    def test_disabled_setting_is_reported_with_its_source(self):
        self.settings.write_text(json.dumps({"enabledPlugins": {self.plugin_id: False}}), encoding="utf-8")
        item = self.run_doctor()["installations"][0]
        self.assertFalse(item["enabled"])
        self.assertIn("disabled", item["problems"])
        self.assertEqual(item["enabled_setting_source"], str(self.settings.resolve()))

    def test_explicit_settings_precedence_and_unknown_enablement(self):
        later = self.base / "settings.local.json"
        later.write_text(json.dumps({"enabledPlugins": {self.plugin_id: False}}), encoding="utf-8")
        result = doctor.diagnose(self.source, self.registry, project=self.base, settings=[self.settings, later])
        self.assertFalse(result["installations"][0]["enabled"])
        result = doctor.diagnose(self.source, self.registry, project=self.base, settings=[])
        self.assertIsNone(result["installations"][0]["enabled"])

    def test_project_registration_is_not_treated_as_active_in_another_project(self):
        self.entry.update(scope="project", projectPath=str(self.base / "other-project"))
        self.write_registry()
        result = self.run_doctor()
        self.assertEqual(result["status"], "no_applicable_registration")
        self.assertFalse(result["installations"][0]["applies_to_project"])
        self.entry["projectPath"] = str(self.base)
        self.write_registry()
        self.assertEqual(self.run_doctor()["status"], "matches")

    def test_missing_registry_and_missing_cache_are_actionable_without_writes(self):
        self.registry.unlink()
        before = sorted(path.relative_to(self.base).as_posix() for path in self.base.rglob("*"))
        result = self.run_doctor()
        self.assertEqual(result["status"], "not_registered")
        self.assertEqual(before, sorted(path.relative_to(self.base).as_posix() for path in self.base.rglob("*")))
        self.write_registry()
        self.entry["installPath"] = str(self.base / "missing-cache")
        self.write_registry()
        result = self.run_doctor()
        self.assertIn("unreadable_installed_copy", result["installations"][0]["problems"])
        self.assertFalse((self.base / "missing-cache").exists())

    def test_malformed_registry_returns_json_error_without_traceback(self):
        self.registry.write_text("{invalid", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()) as output:
            code = doctor.main(["--source", str(self.source), "--registry", str(self.registry), "--settings", str(self.settings), "--json"])
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "error")

    def test_symlink_runtime_does_not_read_arbitrary_targets(self):
        original = Path.is_symlink
        with patch.object(Path, "is_symlink", lambda path: path.name == "helper.py" or original(path)):
            with self.assertRaisesRegex(doctor.DoctorError, "Symlink"):
                self.run_doctor()

    def test_python_caches_do_not_create_false_mismatch(self):
        (self.source / "scripts/__pycache__").mkdir()
        (self.source / "scripts/__pycache__/helper.pyc").write_bytes(b"compiled cache")
        self.assertEqual(self.run_doctor()["status"], "matches")

    def test_junction_runtime_directories_are_rejected_before_walking(self):
        with patch.object(Path, "is_junction", lambda path: path.name == "scripts", create=True):
            with self.assertRaisesRegex(doctor.DoctorError, "junction"):
                self.run_doctor()

    def test_georgian_source_path_outputs_work_under_cp1252(self):
        destination = self.base / "პლაგინი"
        self.source.rename(destination)
        self.source = destination
        args = ["--source", str(self.source), "--registry", str(self.registry), "--settings", str(self.settings)]
        for json_mode in (True, False):
            with self.subTest(json_mode=json_mode):
                buffer = io.BytesIO()
                stream = io.TextIOWrapper(buffer, encoding="cp1252")
                with contextlib.redirect_stdout(stream):
                    code = doctor.main(args + (["--json"] if json_mode else []))
                stream.flush()
                output = buffer.getvalue().decode("ascii" if json_mode else "utf-8")
                self.assertEqual(code, 0)
                if json_mode:
                    self.assertEqual(json.loads(output)["source_root"], str(self.source.resolve()))
                else:
                    self.assertIn("პლაგინი", output)


if __name__ == "__main__":
    unittest.main()
