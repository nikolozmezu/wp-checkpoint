"""Reconcile otherwise plausible report/checkpoint results with the saved ledger."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_state as runs
import select_tests as selection
import validate as v
from test_selection import entry, make_plan


class StateReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".validation-state-report-", dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = self.root / "plan.md"
        self.plan.write_text(make_plan([entry("HOME-001", True), entry("OTHER-001")]), encoding="utf-8")
        self.bundle = self.root / "report-case"
        self.bundle.mkdir()
        self.state_path = self.bundle / "run-state.json"
        self.report = self.bundle / "wp-update-report.md"
        self.context = {"project_root": str(self.root), "wordpress_root": str(self.root), "site_url": "http://demo.invalid", "home_url": "http://demo.invalid", "blog_id": 1,
                        "environment_fingerprint": hashlib.sha256(b"synthetic environment").hexdigest(), "observed_at": runs.now()}
        runs.init(self.bundle, self.plan, self.context, selection.select(self.plan, "smoke"), mode="before")

    def render(self, changes=None, mode=None, plan_reference=True):
        state = runs.load(self.state_path)
        tests = deepcopy(state["tests"])
        for test in tests:
            test.update((changes or {}).get(test["id"], {}))
        selected = [test for test in tests if test["category"].startswith("Yes")]
        completeness = "Incomplete" if any(test["status"] == "NOT RUN" for test in selected) else "Complete"
        text = f"# Test report\n**Mode:** {mode or state['mode']}\n**Run completeness:** {completeness}\n"
        if plan_reference:
            text += f"**Test-plan reference:** `{self.plan}`, SHA256 {state['plan']['sha256']}, last discovery 2026-11-02\n"
        for label, values in (("Full plan", tests), ("Selected scope", selected)):
            counts = Counter(test["status"] for test in values)
            text += label + ": " + " · ".join(f"{status}: {counts[status]}" for status in v.STATUSES) + "\n"
        text += "| Test ID | Lifecycle | Selected for this run's scope? | Status | Actual observation | Evidence reference | Reason |\n"
        text += "| :-- | :-- | :-- | :-- | :-- | :-- | :-- |\n"
        for test in tests:
            text += f"| {test['id']} | {test['lifecycle']} | {test['category']} | {test['status']} | {test.get('observation', 'Recorded observation or pending assessment')} | — | {test.get('result_reason') or 'Documented assessment'} |\n"
        self.report.write_text(text, encoding="utf-8")
        return text

    def assess_home(self, status="PASS"):
        runs.start(self.state_path, self.plan, self.context, "HOME-001", "Read the synthetic example", mutates=False)
        runs.record(self.state_path, self.plan, self.context, "HOME-001", {"status": status, "observation": "Observed the documented result", "reason": "", "evidence": [],
                    "cleanup": {"status": "Not needed", "notes": "Read-only synthetic fixture"}})

    def checkpoint(self):
        state = runs.load(self.state_path)
        tests = []
        for test in state["tests"]:
            attempts = [{"number": index + 1, "status": attempt["status"], "observed_at": attempt["observed_at"], "observation": attempt["observation"],
                         "evidence": [item["path"] for item in attempt["evidence"]], "captures": []}
                        for index, attempt in enumerate(test["attempts"]) if attempt["status"] in runs.TERMINAL]
            tests.append({"id": test["id"], "lifecycle": test["lifecycle"], "selected": test["selected"], "selection_reason": test["category"],
                          "status": test["status"], "reason": test["result_reason"] or "Recorded result", "starting_location": "http://demo.invalid/example/", "role": "Anonymous",
                          "prerequisites": "Synthetic fixture", "actions": ["Read example", "Observe result"], "expected_result": "Documented result", "attempts": attempts})
        complete = not any(test["selected"] and test["status"] == "NOT RUN" for test in tests)
        return {"schema_version": 1, "mode": "before", "run_id": self.bundle.name, "captured_at": runs.now(), "timezone": "UTC", "run_completeness": "Complete" if complete else "Incomplete",
                "project": {key: self.context[key] for key in ("project_root", "wordpress_root", "site_url", "home_url", "blog_id")}, "plan": state["plan"], "scope": {"name": "smoke", "update_tags": []},
                "inventory": {"wordpress_version": "synthetic", "web_php_version": None, "cli_php_version": None, "themes": [], "plugins": [], "environment_notes": []},
                "tests": tests, "cleanup": {"status": "Not needed", "notes": "Synthetic read-only fixture"}, "limitations": ["No WordPress runtime exists in this unit fixture"]}

    def save_checkpoint(self, data):
        path = self.bundle / "checkpoint.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_valid_interrupted_report_keeps_pending_results_not_run(self):
        runs.start(self.state_path, self.plan, self.context, "HOME-001", "Begin documented action")
        self.render()
        original = self.state_path.read_bytes()
        result = v.validate_report(self.report, self.plan)
        self.assertEqual(result.errors, [])
        self.assertEqual(self.state_path.read_bytes(), original)
        self.assertEqual(runs.load(self.state_path)["tests"][0]["status"], "NOT RUN")

    def test_plausible_wrong_subset_with_correct_counts_is_rejected(self):
        text = self.render({"HOME-001": {"category": "No"}, "OTHER-001": {"category": "Yes/smoke"}})
        legacy_copy = self.root / "report-without-ledger.md"
        legacy_copy.write_text(text, encoding="utf-8")
        self.assertEqual(v.validate_report(legacy_copy, self.plan).errors, [])
        errors = v.validate_report(self.report, self.plan).errors
        self.assertTrue(any("selection category differs" in error for error in errors))
        self.assertTrue(any("selected flag differs" in error for error in errors))

    def test_fabricated_pass_and_changed_failure_are_rejected(self):
        self.render({"HOME-001": {"status": "PASS", "observation": "Claimed successful interaction"}})
        self.assertTrue(any("status differs" in error for error in v.validate_report(self.report).errors))
        self.assess_home("FAIL")
        self.render({"HOME-001": {"status": "PASS"}})
        self.assertTrue(any("status differs" in error for error in v.validate_report(self.report).errors))

    def test_category_lifecycle_and_ids_must_match_exactly(self):
        self.render({"HOME-001": {"category": "Yes/full"}, "OTHER-001": {"lifecycle": "REMOVED"}})
        errors = v.validate_report(self.report).errors
        self.assertTrue(any("selection category differs" in error for error in errors))
        self.assertTrue(any("lifecycle differs" in error for error in errors))
        text = self.render().replace("OTHER-001", "OTHER-002")
        self.report.write_text(text, encoding="utf-8")
        self.assertTrue(any("Report/run-state IDs differ" in error for error in v.validate_report(self.report).errors))

    def test_mode_and_same_bundle_are_required(self):
        self.render(mode="after")
        self.assertTrue(any("Mode differs" in error for error in v.validate_report(self.report).errors))
        self.render()
        foreign = self.root / "elsewhere" / "run-state.json"
        result = v.validate_report(self.report, state_path=foreign)
        self.assertTrue(any("same report bundle" in error for error in result.errors))
        missing = self.bundle / "missing-state.json"
        self.assertTrue(v.validate_report(self.report, state_path=missing).errors)

    def test_reference_hash_and_explicit_plan_integrity(self):
        text = self.render()
        plan_hash = runs.digest(self.plan)
        self.report.write_text(text.replace(plan_hash, "0" * 64), encoding="utf-8")
        self.assertTrue(any("recorded plan SHA256 differs" in error for error in v.validate_report(self.report).errors))
        self.report.write_text(text.replace(plan_hash, "unavailable"), encoding="utf-8")
        self.assertTrue(any("invalid or missing SHA256" in error for error in v.validate_report(self.report).errors))
        self.report.write_text(text, encoding="utf-8")
        self.plan.write_text(self.plan.read_text(encoding="utf-8") + "\nLater discovery changed this canonical plan.\n", encoding="utf-8")
        self.assertEqual(v.validate_report(self.report).errors, [])
        self.assertTrue(any("Explicit plan SHA256 differs" in error for error in v.validate_report(self.report, self.plan).errors))

    def test_older_partial_report_missing_hash_warns_without_fabricating_identity(self):
        self.render(plan_reference=False)
        result = v.validate_report(self.report)
        self.assertEqual(result.errors, [])
        self.assertTrue(any("no Test-plan reference SHA256" in warning for warning in result.warnings))

    def test_malformed_adjacent_state_is_reported_without_traceback(self):
        self.render()
        original = self.state_path.read_bytes()
        for bad in ("{broken", "[]", '{"state_schema_version":1}', json.dumps({**json.loads(original), "tests": [{"id": ["invalid"]}]})):
            with self.subTest(bad=bad[:50]):
                self.state_path.write_text(bad, encoding="utf-8")
                self.assertTrue(any("Cannot validate run state" in error for error in v.validate_report(self.report).errors))
        self.state_path.write_bytes(original)

    def test_legacy_report_without_ledger_remains_compatible(self):
        text = self.render(plan_reference=False)
        legacy = self.root / "legacy-report.md"
        legacy.write_text(text, encoding="utf-8")
        result = v.validate_report(legacy, self.plan)
        self.assertEqual(result.errors, [])
        self.assertFalse(any("run-state" in warning for warning in result.warnings))

    def test_complete_checkpoint_rejects_open_ledger(self):
        self.assess_home()
        self.render()
        errors = v.validate_checkpoint(self.save_checkpoint(self.checkpoint())).errors
        self.assertTrue(any("requires a finalized run-state" in error for error in errors))

    def test_complete_checkpoint_accepts_finalized_matching_ledger(self):
        self.assess_home()
        runs.finish(self.state_path, self.plan, self.context)
        self.render()
        data = self.checkpoint()
        self.assertEqual(v.validate_checkpoint(self.save_checkpoint(data)).errors, [])
        data["plan"] = {**data["plan"], "sha256": "0" * 64}
        self.assertTrue(any("Checkpoint/run-state plan SHA256 differs" in error for error in v.validate_checkpoint(self.save_checkpoint(data)).errors))

    def test_incomplete_checkpoint_accepts_open_ledger_and_pending_results(self):
        self.render()
        self.assertEqual(v.validate_checkpoint(self.save_checkpoint(self.checkpoint())).errors, [])

    def test_checkpoint_rejects_report_selection_that_only_looks_consistent(self):
        self.assess_home()
        runs.finish(self.state_path, self.plan, self.context)
        self.render({"HOME-001": {"category": "Yes/full"}})
        self.assertTrue(any("selection category differs" in error for error in v.validate_checkpoint(self.save_checkpoint(self.checkpoint())).errors))

    def test_cli_explicit_state_reconciles_and_reports_bad_json_as_error(self):
        self.render()
        command = [sys.executable, str(Path(v.__file__)), "report", str(self.report), "--state", str(self.state_path), "--plan", str(self.plan)]
        good = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
        self.state_path.write_text("{bad json", encoding="utf-8")
        bad = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(bad.returncode, 1, bad.stdout + bad.stderr)
        self.assertIn("Cannot validate run state", bad.stdout)
        self.assertNotIn("Traceback", bad.stderr)


if __name__ == "__main__":
    unittest.main()
