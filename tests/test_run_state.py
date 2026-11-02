"""Execution state prevents accidental repeats and preserves genuine observations."""
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
from test_selection import entry, make_plan


class RunStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".validation-state-", dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plan = self.root / "plan.md"
        self.plan.write_text(make_plan([entry("CHECK-001", True), entry("FOLLOW-001", deps=("CHECK-001",))]), encoding="utf-8")
        self.bundle = self.root / "report-one"
        self.bundle.mkdir()
        self.path = self.bundle / "run-state.json"
        self.context = {"project_root": str(self.root), "wordpress_root": str(self.root), "site_url": "http://demo.invalid", "home_url": "http://demo.invalid", "blog_id": 1,
                        "environment_fingerprint": hashlib.sha256(b"current versions and config").hexdigest(), "observed_at": runs.now()}
        self.selection = selection.select(self.plan)
        runs.init(self.bundle, self.plan, self.context, self.selection)

    def start(self, test_id="CHECK-001", **kwargs):
        return runs.start(self.path, self.plan, self.context, test_id, "Exercise documented local action", **kwargs)

    def result(self, status="PASS", cleanup="Complete", evidence=None):
        return {"status": status, "observation": "Observed the documented outcome", "reason": "Required capability unavailable" if status in {"BLOCKED", "NOT APPLICABLE"} else "",
                "evidence": evidence or [], "cleanup": {"status": cleanup, "notes": "Verified disposable state removed" if cleanup != "Incomplete" else "Disposable record remains"}}

    def record(self, status="PASS", test_id="CHECK-001", **kwargs):
        return runs.record(self.path, self.plan, self.context, test_id, self.result(status, **kwargs))

    def test_resume_does_not_repeat_in_flight_action_or_mark_it_successful(self):
        self.start()
        original = self.path.read_bytes()
        status = runs.resume(self.path, self.plan, self.context)
        self.assertEqual(status["interrupted"], ["CHECK-001"])
        self.assertEqual(status["runnable_now"], [])
        self.assertEqual(runs.load(self.path)["tests"][0]["status"], "NOT RUN")
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(runs.StateError):
            self.start()

    def test_resume_continues_pending_checks_after_prior_observations(self):
        self.start(mutates=False)
        self.record()
        status = runs.resume(self.path, self.plan, self.context)
        self.assertEqual(status["completed"], ["CHECK-001"])
        self.assertEqual(status["runnable_now"], ["FOLLOW-001"])
        self.assertIn("earlier observations", status["note"])

    def test_plan_context_and_selection_drift_stop_resume(self):
        original = self.plan.read_bytes()
        self.plan.write_bytes(original + b"\nChanged plan")
        with self.assertRaisesRegex(runs.StateError, "Plan changed"):
            runs.resume(self.path, self.plan, self.context)
        self.plan.write_bytes(original)
        changed = deepcopy(self.context)
        changed["environment_fingerprint"] = "b" * 64
        with self.assertRaisesRegex(runs.StateError, "Environment/context changed"):
            runs.resume(self.path, self.plan, changed)
        raw = json.loads(self.path.read_text())
        raw["selection"]["scope"] = "smoke"
        self.path.write_text(json.dumps(raw), encoding="utf-8")
        with self.assertRaisesRegex(runs.StateError, "Selection no longer matches"):
            runs.resume(self.path, self.plan, self.context)

    def test_result_cannot_claim_execution_without_start_journal(self):
        with self.assertRaises(runs.StateError):
            self.record()
        self.record("BLOCKED")
        self.assertEqual(runs.load(self.path)["tests"][0]["status"], "BLOCKED")

    def test_dependency_not_passed_blocks_start(self):
        with self.assertRaises(runs.StateError):
            self.start("FOLLOW-001")

    def test_current_equivalent_fixture_review_does_not_execute_excluded_dependency(self):
        bundle = self.root / "report-limited"
        bundle.mkdir()
        selected = selection.select(self.plan, exclusions=["CHECK-001"])
        runs.init(bundle, self.plan, self.context, selected)
        review = {"ids": ["CHECK-001"], "observed_at": runs.now(), "observation": "Observed independent local fixture ready for the consumer; no producer action required"}
        state = runs.start(bundle, self.plan, self.context, "FOLLOW-001", "Read the independently verified fixture", mutates=False, prerequisite_review=review)
        self.assertFalse(state["tests"][0]["selected"])
        self.assertEqual(state["tests"][0]["attempts"], [])
        self.assertEqual(state["tests"][1]["in_flight"]["prerequisite_review"], review)
        self.record("BLOCKED")
        with self.assertRaises(runs.StateError):
            self.start("FOLLOW-001")

    def test_resolution_requires_review_and_cleanup_before_safe_retry(self):
        self.start()
        resolution = {"observation": "Inspected current record and removed own partial fixture", "retry_safe": True,
                      "cleanup": {"status": "Incomplete", "notes": "Record still exists"}}
        with self.assertRaises(runs.StateError):
            runs.resolve(self.path, self.plan, self.context, "CHECK-001", resolution)
        resolution["cleanup"] = {"status": "Complete", "notes": "Verified own record absent; independent setup can repeat safely"}
        runs.resolve(self.path, self.plan, self.context, "CHECK-001", resolution)
        status = runs.resume(self.path, self.plan, self.context)
        self.assertEqual(status["runnable_now"], ["CHECK-001"])
        self.start()
        state = self.record()
        self.assertEqual([attempt["status"] for attempt in state["tests"][0]["attempts"]], ["INTERRUPTED", "PASS"])

    def test_unsafe_interruption_becomes_explicit_blocker(self):
        self.start()
        runs.resolve(self.path, self.plan, self.context, "CHECK-001", {"observation": "Cannot establish whether external operation occurred", "retry_safe": False,
                     "cleanup": {"status": "Incomplete", "notes": "Outcome needs investigation"}})
        state = runs.load(self.path)
        self.assertEqual(state["tests"][0]["status"], "BLOCKED")
        self.assertEqual(runs.resume(self.path, self.plan, self.context)["runnable_now"], [])

    def test_valid_failure_survives_retry_success(self):
        self.start()
        self.record("FAIL")
        with self.assertRaises(runs.StateError):
            self.start()
        self.start(retry=True)
        state = self.record("PASS")
        self.assertEqual(state["tests"][0]["status"], "FAIL")
        self.assertEqual([attempt["status"] for attempt in state["tests"][0]["attempts"]], ["FAIL", "PASS"])
        runs.load(self.path)

    def test_cleanup_blocks_further_actions_until_resolution(self):
        self.start()
        self.record(cleanup="Incomplete")
        with self.assertRaises(runs.StateError):
            self.start("FOLLOW-001")
        runs.resolve(self.path, self.plan, self.context, "CHECK-001", {"observation": "Verified own temporary item removed", "retry_safe": False,
                     "cleanup": {"status": "Complete", "notes": "Restored original state"}})
        self.start("FOLLOW-001")

    def test_evidence_cannot_escape_bundle_or_change_after_recording(self):
        (self.root / "outside.txt").write_text("outside", encoding="utf-8")
        self.start()
        for ref in ("../outside.txt", str(self.root / "outside.txt"), "%2e%2e/outside.txt", "run-state.json"):
            with self.subTest(ref=ref), self.assertRaises(runs.StateError):
                self.record(evidence=[ref])
        (self.bundle / "evidence.txt").write_text("actual observation", encoding="utf-8")
        self.record(evidence=["evidence.txt"])
        (self.bundle / "evidence.txt").write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(runs.StateError, "Evidence changed"):
            runs.resume(self.path, self.plan, self.context)

    def test_completed_run_and_completed_checkpoint_are_immutable(self):
        self.start()
        self.record()
        self.start("FOLLOW-001")
        self.record(test_id="FOLLOW-001")
        runs.finish(self.path, self.plan, self.context)
        original = self.path.read_bytes()
        with self.assertRaises(runs.StateError):
            self.start(retry=True)
        self.assertEqual(self.path.read_bytes(), original)
        with self.assertRaises(runs.StateError):
            runs.init(self.bundle, self.plan, self.context, self.selection)

    def test_completed_checkpoint_cannot_be_extended_even_if_ledger_open(self):
        (self.bundle / "checkpoint.json").write_text('{"run_completeness":"Complete"}', encoding="utf-8")
        with self.assertRaisesRegex(runs.StateError, "Completed checkpoint"):
            self.start()

    def test_retest_creates_fresh_selection_and_keeps_failure_history(self):
        self.start()
        self.record("FAIL")
        self.record("BLOCKED", test_id="FOLLOW-001")
        runs.finish(self.path, self.plan, self.context)
        original = self.path.read_bytes()
        selected = runs.retest_selection(self.path, self.plan, requested_ids=["FOLLOW-001"])
        self.assertEqual(selected["order"], ["CHECK-001", "FOLLOW-001"])
        new_bundle = self.root / "report-retest"
        new_bundle.mkdir()
        new_context = deepcopy(self.context)
        new_context["environment_fingerprint"] = "c" * 64
        fresh = runs.init(new_bundle, self.plan, new_context, selected)
        self.assertTrue(all(test["status"] == "NOT RUN" and not test["attempts"] for test in fresh["tests"]))
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(runs.load(self.path)["tests"][0]["status"], "FAIL")

    def test_retest_rejects_same_ids_from_another_project(self):
        self.record("BLOCKED")
        self.record("BLOCKED", test_id="FOLLOW-001")
        runs.finish(self.path, self.plan, self.context)
        selected = runs.retest_selection(self.path, self.plan)
        for field, value in (("project_root", "C:/different"), ("wordpress_root", "C:/other/public"), ("site_url", "http://different.invalid"), ("home_url", "http://other.invalid"), ("blog_id", 2)):
            with self.subTest(field=field):
                changed = deepcopy(self.context)
                changed[field] = value
                bundle = self.root / ("report-other-" + field)
                bundle.mkdir()
                with self.assertRaisesRegex(runs.StateError, "Retest project/site identity differs"):
                    runs.init(bundle, self.plan, changed, selected)
                self.assertFalse((bundle / "run-state.json").exists())

    def test_writer_lock_and_invalid_context_stop_before_changes(self):
        lock = self.bundle / ".run-state.lock"
        lock.write_text("active writer", encoding="utf-8")
        with self.assertRaises(runs.StateError):
            self.start()
        lock.unlink()
        context = deepcopy(self.context)
        context["token"] = "must-not-be-accepted"
        with self.assertRaises(runs.StateError):
            runs.resume(self.path, self.plan, context)

    def test_finalized_cleanup_can_be_reviewed_without_rewriting_old_run(self):
        self.start()
        self.record("FAIL", cleanup="Incomplete")
        self.record("BLOCKED", test_id="FOLLOW-001")
        runs.finish(self.path, self.plan, self.context)
        original = self.path.read_bytes()
        with self.assertRaises(runs.StateError):
            runs.retest_selection(self.path, self.plan)
        review_path = self.root / "cleanup-review.json"
        review_data = {"observed_at": runs.now(), "source_run_id": self.bundle.name, "source_state_sha256": runs.digest(self.path), "observation": "Inspected and removed the old disposable record", "resolved_ids": ["CHECK-001"],
                       "cleanup": {"status": "Complete", "notes": "Original record state restored"}, "evidence": []}
        review_path.write_text(json.dumps(review_data), encoding="utf-8")
        for field, value in (("source_run_id", "another-run"), ("source_state_sha256", "0" * 64), ("observed_at", "2020-01-01T00:00:00+00:00")):
            with self.subTest(field=field):
                wrong = {**review_data, field: value}
                review_path.write_text(json.dumps(wrong), encoding="utf-8")
                with self.assertRaises(runs.StateError):
                    runs.retest_selection(self.path, self.plan, cleanup_review=review_path)
        review_path.write_text(json.dumps(review_data), encoding="utf-8")
        selected = runs.retest_selection(self.path, self.plan, cleanup_review=review_path)
        fresh_bundle = self.root / "report-restored"
        fresh_bundle.mkdir()
        runs.init(fresh_bundle, self.plan, self.context, selected)
        self.assertEqual(self.path.read_bytes(), original)
        review_path.write_text(review_path.read_text() + " ", encoding="utf-8")
        with self.assertRaisesRegex(runs.StateError, "cleanup review or its evidence changed"):
            runs.resume(fresh_bundle, self.plan, self.context)

    def test_cli_resume_is_read_only(self):
        context_path = self.root / "context.json"
        context_path.write_text(json.dumps(self.context), encoding="utf-8")
        original = self.path.read_bytes()
        run = subprocess.run([sys.executable, str(Path(runs.__file__)), "resume", str(self.path), "--plan", str(self.plan), "--context", str(context_path)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["runnable_now"], ["CHECK-001"])
        self.assertEqual(original, self.path.read_bytes())

    def test_cli_outputs_ascii_safe_json_with_georgian_paths(self):
        bundle = self.root / "ანგარიში"
        bundle.mkdir()
        runs.init(bundle, self.plan, self.context, self.selection)
        context_path = self.root / "კონტექსტი.json"
        context_path.write_text(json.dumps(self.context), encoding="utf-8")
        run = subprocess.run([sys.executable, str(Path(runs.__file__)), "resume", str(bundle), "--plan", str(self.plan), "--context", str(context_path)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        output = run.stdout.decode("ascii")
        self.assertEqual(json.loads(output)["state_path"], str(bundle / "run-state.json"))


if __name__ == "__main__":
    unittest.main()
