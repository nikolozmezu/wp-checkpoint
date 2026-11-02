"""Selection assertions cover dependency behavior, not document wording."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import select_tests as selection


def make_plan(entries, schema=3):
    """entries: (ID, smoke, tags, layers, prerequisites, downstream, lifecycle)."""
    text = f"# Synthetic project\n**Plan schema version:** {schema}\n"
    text += "## A. Purpose\nPlanned checks.\n## B. Site\nLocal synthetic site.\n## C. Features\nRepresentative flows.\n## D. Matrix\n"
    text += "| Test ID | Lifecycle | Priority | Update-type tags | Smoke? | Depends on | Affects |\n| :-- | :-- | :-- | :-- | :-- | :-- | :-- |\n"
    join = lambda values: ", ".join(values) or "None"
    for key, smoke, tags, layers, deps, affected, life in entries:
        text += f"| {key} | {life} | P1 | {join(tags)} | {'Y' if smoke else 'N'} | {join(deps)} | {join(affected)} |\n"
    text += "**Essential smoke checks after any update:** " + join([e[0] for e in entries if e[1]]) + "\n"
    text += "## E. Preconditions\n- [ ] Local runtime ready\n## F. Cards\n"
    for key, smoke, tags, layers, deps, affected, life in entries:
        text += f"#### {key} — Representative check\n- **Lifecycle:** {life}\n- **Feature / Priority:** Representative flow — P1\n- **Update types:** {join(tags)}\n"
        if layers:
            text += f"- **Execution layers:** {join(layers)}\n"
        text += "- **Implementation evidence:** Source handler and fixture configuration.\n- **Fixture setup:** Create independent disposable fixture.\n- **State after cleanup:** Fixture removed and existing data unchanged.\n"
        text += f"- **Depends on:** {join(deps)}\n- **Affects:** {join(affected)}\n"
        text += "- **Starting point:** /example/\n- **Steps:**\n  1. Exercise the documented flow.\n- **Expected result:** Documented outcome appears.\n"
        text += "- **Known limitations / dependencies:** Vendor handler unavailable for unresolved layers.\n- **Status:** NOT RUN\n"
        if life == "REMOVED":
            text += "- **Removal date / reason:** 2026-11-02 — Feature retired.\n"
    return text + "## G. Vocabulary\nFive statuses.\n## H. Report\nRecord observed results.\n## I. Maintenance\nReview sources before use.\n"


def entry(key, smoke=False, tags=("core",), layers=("browser",), deps=(), affected=(), life="ACTIVE"):
    return key, smoke, tags, layers, deps, affected, life


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix=".validation-selection-", dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.plan = Path(self.temp.name) / "plan.md"

    def write(self, entries, schema=3):
        self.plan.write_text(make_plan(entries, schema), encoding="utf-8")

    def selected(self, **kwargs):
        return selection.select(self.plan, **kwargs)

    def test_smoke_includes_prerequisites_but_not_downstream(self):
        self.write([entry("SETUP-001"), entry("HOME-001", True, deps=("SETUP-001",), affected=("DETAIL-001",)), entry("DETAIL-001")])
        result = self.selected(scope="smoke")
        self.assertEqual(result["order"], ["SETUP-001", "HOME-001"])
        self.assertFalse(result["tests"][2]["selected"])

    def test_targeted_closes_impact_and_prerequisites_without_smoke_fanout(self):
        self.write([entry("HOME-001", True, affected=("OTHER-001",)), entry("OTHER-001"), entry("SETUP-001"),
                    entry("API-001", tags=("plugin:catalogue",), deps=("SETUP-001",), affected=("SEARCH-001",)),
                    entry("SEARCH-001"), entry("CONSUMER-001", deps=("SEARCH-001",))])
        result = self.selected(scope="targeted", update_tags=["plugin:catalogue"])
        self.assertEqual(set(result["order"]), {"HOME-001", "SETUP-001", "API-001", "SEARCH-001", "CONSUMER-001"})
        self.assertLess(result["order"].index("SETUP-001"), result["order"].index("API-001"))
        self.assertLess(result["order"].index("SEARCH-001"), result["order"].index("CONSUMER-001"))

    def test_excluded_prerequisite_blocks_dependents_without_reselection(self):
        self.write([entry("SETUP-001"), entry("MID-001", deps=("SETUP-001",)), entry("FINAL-001", True, deps=("MID-001",))])
        result = self.selected(scope="smoke", exclusions=["SETUP-001"])
        self.assertEqual(result["order"], ["MID-001", "FINAL-001"])
        self.assertEqual(result["tests"][2]["blocked_by"], ["SETUP-001"])
        self.assertFalse(result["tests"][0]["selected"])

    def test_exclusion_does_not_hide_downstream_update_impact(self):
        self.write([entry("SOURCE-001", tags=("plugin:catalogue",), affected=("MID-001",)),
                    entry("MID-001", affected=("FINAL-001",)), entry("FINAL-001")])
        result = self.selected(scope="targeted", update_tags=["plugin:catalogue"], exclusions=["SOURCE-001", "MID-001"])
        self.assertEqual(result["order"], ["FINAL-001"])
        self.assertTrue(all(not test["selected"] for test in result["tests"][:2]))

    def test_php_includes_unknown_layers_and_legacy_without_id_heuristics(self):
        self.write([entry("BANANA-001", tags=("php",), layers=("php",)), entry("OPAQUE-001", layers=("unknown",)), entry("STATIC-001", layers=("static",))])
        self.assertEqual(set(self.selected(scope="targeted", update_tags=["php"])["order"]), {"BANANA-001", "OPAQUE-001"})
        self.write([entry("LEGACY-001", layers=())], schema=2)
        result = self.selected(scope="targeted", update_tags=["php"])
        self.assertEqual(result["order"], ["LEGACY-001"])
        self.assertTrue(any("Legacy cards" in warning for warning in result["warnings"]))

    def test_env_unknown_impact_is_broad_but_exclusions_still_win(self):
        self.write([entry("STATIC-001", layers=("static",)), entry("HOME-001", True)])
        result = self.selected(scope="targeted", update_tags=["env"], exclusions=["HOME-001"])
        self.assertEqual(result["order"], ["STATIC-001"])
        self.assertTrue(any("Unqualified env" in warning for warning in result["warnings"]))

    def test_explicit_retest_ids_add_only_prerequisites(self):
        self.write([entry("HOME-001", True), entry("SETUP-001"), entry("FAILURE-001", deps=("SETUP-001",), affected=("OTHER-001",)), entry("OTHER-001")])
        result = self.selected(requested_ids=["FAILURE-001"])
        self.assertEqual(result["order"], ["SETUP-001", "FAILURE-001"])
        self.assertEqual(result["tests"][2]["category"], "Yes/targeted-tagged")

    def test_removed_history_is_retained_and_never_run(self):
        self.write([entry("HOME-001", True), entry("OLD-001", life="REMOVED")])
        result = self.selected()
        self.assertEqual(len(result["tests"]), 2)
        self.assertEqual(result["order"], ["HOME-001"])
        self.assertIn("2026-11-02", result["tests"][1]["reason"])
        with self.assertRaises(selection.SelectionError):
            self.selected(requested_ids=["OLD-001"])

    def test_cycles_unknown_ids_and_empty_targeted_are_rejected(self):
        self.write([entry("ONE-001", deps=("TWO-001",)), entry("TWO-001", deps=("ONE-001",))])
        with self.assertRaises(selection.SelectionError):
            self.selected()
        self.write([entry("ONE-001")])
        for kwargs in ({"requested_ids": ["MISSING-001"]}, {"scope": "targeted"}, {"update_tags": ["bad-tag"]}, {"requested_ids": ["ONE-001"], "exclusions": ["ONE-001"]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(selection.SelectionError):
                self.selected(**kwargs)

    def test_cli_is_read_only_and_emits_machine_readable_result(self):
        self.write([entry("HOME-001", True)])
        original = self.plan.read_bytes()
        run = subprocess.run([sys.executable, str(Path(selection.__file__)), str(self.plan), "--scope", "smoke"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["order"], ["HOME-001"])
        self.assertEqual(self.plan.read_bytes(), original)

    def test_cli_json_handles_georgian_plan_path_on_windows_console(self):
        self.write([entry("HOME-001", True)])
        translated = self.plan.with_name("გეგმა.md")
        translated.write_bytes(self.plan.read_bytes())
        run = subprocess.run([sys.executable, str(Path(selection.__file__)), str(translated)], capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout.decode("ascii"))["plan"]["path"], str(translated.resolve()))


if __name__ == "__main__":
    unittest.main()
