"""Synthetic documents exercise structural invariants without a WordPress site."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate as v


PLAN = """# Testing After Update — Demo
**Plan schema version:** 2
## A. Purpose
Reusable plan.
## B. Site and Environment Profile
Local site: https://demo.test
## C. Feature Inventory
Homepage and contact form.
## D. Priorities and Update-Impact Matrix
| Test ID | Feature | Lifecycle | Priority | Update-type tags | Smoke? | Depends on | Affects | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| HOME-001 | Homepage | ACTIVE | P0 | core, theme | Y | None | FORM-CONTACT-001 | Landing page |
| FORM-CONTACT-001 | Contact form | ACTIVE | P1 | plugin:contact-form-7 | N | HOME-001 | None | Mail catcher required |
**Essential smoke checks after any update:** HOME-001
## E. Preconditions
- [ ] Test account available
## F. Detailed Test Catalogue
### Test case card format
```
#### <TEST-ID> — <Short title>
- **Status:** NOT RUN
```
### Frontend
#### HOME-001 — Homepage renders
- **Lifecycle:** ACTIVE
- **Feature / Priority:** Homepage — P0
- **Update types:** core, theme
- **Depends on:** None
- **Affects:** FORM-CONTACT-001
- **Expected result:** Header and primary call to action appear.
- **Status:** NOT RUN
#### FORM-CONTACT-001 — Contact reaches local mail catcher
- **Lifecycle:** ACTIVE
- **Feature / Priority:** Contact form — P1
- **Update types:** plugin:contact-form-7
- **Depends on:** HOME-001
- **Affects:** None
- **Expected result:** Mail catcher receives exactly one message.
- **Status:** NOT RUN
## G. Vocabulary
Generic <AREA>-<NNN> notation remains.
## H. Future Report Template
Report at <YYYY-MM-DD HH:MM>, totals <n>.
## I. Maintenance
Refresh when features change.
"""

REPORT = """# Demo test report
**Mode:** normal
**Run completeness:** Complete
Full plan: NOT RUN: 0 · PASS: 1 · FAIL: 0 · BLOCKED: 1 · NOT APPLICABLE: 0
Selected scope: NOT RUN: 0 · PASS: 1 · FAIL: 0 · BLOCKED: 1 · NOT APPLICABLE: 0
| Test ID | Lifecycle | Selected for this run's scope? | Status | Actual observation | Evidence reference | Reason |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| HOME-001 | ACTIVE | Yes/full | PASS | Header and button appeared. | screenshots/home.png | — |
| FORM-CONTACT-001 | ACTIVE | Yes/full | BLOCKED | SMTP isolation could not be verified. | — | No mail catcher available |
"""


def quality_plan(project, test_id, layers, update_tags, evidence, setup, cleanup):
    """Invented project types; never imports a real site's plan or implementation."""
    return f"""# Testing After Update — {project}
**Plan schema version:** 3
## A. Purpose
Plan a representative project check.
## B. Site and Environment Profile
Project: {project}; local test environment.
## C. Feature Inventory
Feature definition is recorded in the card below.
## D. Priorities and Update-Impact Matrix
| Test ID | Feature | Lifecycle | Priority | Update-type tags | Smoke? | Depends on | Affects | Notes |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| {test_id} | Primary feature | ACTIVE | P0 | {update_tags} | Y | None | None | Representative case |
**Essential smoke checks after any update:** {test_id}
## E. Preconditions
- [ ] Access and isolation confirmed before execution
## F. Detailed Test Catalogue
#### {test_id} — Primary feature
- **Lifecycle:** ACTIVE
- **Feature / Priority:** Primary feature — P0
- **Update types:** {update_tags}
- **Execution layers:** {layers}
- **Implementation evidence:** {evidence}
- **Fixture setup:** {setup}
- **State after cleanup:** {cleanup}
- **Depends on:** None
- **Affects:** None
- **Starting point:** /example/
- **Steps:**
  1. Open the documented example with its stated role.
  2. Observe the documented feature result.
- **Expected result:** The documented feature result is observable.
- **Expected-result basis:** Derived from source or stored configuration
- **Known limitations / dependencies:** None
- **Status:** NOT RUN
## G. Vocabulary
Use stable test IDs and the five statuses.
## H. Future Report Template
Record evidence and scoped result counts.
## I. Maintenance
**Structural validation:** Pending
**Semantic review:** Reviewed
**Reviewed test IDs:** {test_id}
**Source-check limitations:** None
"""


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        # Keep fixtures in the known writable checkout, including on sandboxed Windows.
        self.temp = tempfile.TemporaryDirectory(prefix=".validation-", dir=Path(__file__).resolve().parents[1])
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / "report-2026-11-02"
        self.bundle.mkdir()
        (self.bundle / "screenshots").mkdir()
        self.image = self.bundle / "screenshots/home.png"
        self.image.write_bytes(b"synthetic image fixture")
        self.plan = self.bundle / "testing-after-update.md"
        self.plan.write_text(PLAN, encoding="utf-8")
        self.report = self.bundle / "wp-update-report.md"
        self.report.write_text(REPORT, encoding="utf-8")

    def checkpoint(self):
        timestamp = "2026-11-02T12:00:00+04:00"
        return {
            "schema_version": 1, "mode": "before", "run_id": self.bundle.name,
            "captured_at": timestamp, "timezone": "Asia/Tbilisi", "run_completeness": "Complete",
            "project": {"project_root": "C:/sites/demo", "wordpress_root": "C:/sites/demo/public", "site_url": "https://demo.test", "home_url": "https://demo.test", "blog_id": 1},
            "plan": {"path": str(self.plan), "sha256": hashlib.sha256(self.plan.read_bytes()).hexdigest()},
            "scope": {"name": "full", "update_tags": []},
            "inventory": {"wordpress_version": "example", "web_php_version": "example", "cli_php_version": None,
                "themes": [{"slug": "demo", "version": "1.0", "active": True, "parent": None}],
                "plugins": [{"slug": "demo-form", "version": "1.0", "active": True, "kind": "plugin"}], "environment_notes": []},
            "tests": [{"id": "HOME-001", "lifecycle": "ACTIVE", "selected": True, "selection_reason": "full", "status": "PASS", "reason": "", "expected_result": "Header and button appear.",
                "starting_location": "https://demo.test/", "role": "Anonymous", "prerequisites": "Local site available", "actions": ["Load homepage", "Observe header and primary action"],
                "attempts": [{"number": 1, "status": "PASS", "observed_at": timestamp, "observation": "Header and button appeared.", "evidence": ["screenshots/home.png"],
                    "captures": [{"path": "screenshots/home.png", "sha256": hashlib.sha256(self.image.read_bytes()).hexdigest(), "url": "https://demo.test/", "role": "Anonymous", "viewport": {"width": 1440, "height": 900, "device_scale_factor": 1}, "locale": "en-US", "state": "Page idle", "fixture": "Homepage content as captured", "captured_at": timestamp}]}]}],
            "cleanup": {"status": "Not needed", "notes": "No state changed"}, "limitations": ["CLI PHP was unavailable"]}

    def validate_checkpoint(self, data):
        path = self.bundle / "checkpoint.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        # Paired technical document is part of a baseline bundle, even for synthetic runs.
        report = f"**Mode:** before\n**Run completeness:** {data['run_completeness']}\n| Test ID | Lifecycle | Selected for this run's scope? | Status | Actual observation | Evidence reference | Reason |\n| :-- | :-- | :-- | :-- | :-- | :-- | :-- |\n"
        for test in data["tests"]:
            report += f"| {test['id']} | {test['lifecycle']} | {'Yes/full' if test['selected'] else 'No'} | {test['status']} | Recorded observation | — | {test['reason'] or '—'} |\n"
        self.report.write_text(report, encoding="utf-8")
        return v.validate_checkpoint(path)

    def test_valid_plan_preserves_generic_notation_and_unchecked_prerequisites(self):
        self.assertEqual(v.validate_plan(self.plan).errors, [])

    def test_legacy_schema_is_explicitly_structural_not_semantic_quality(self):
        result = v.validate_plan(self.plan)
        self.assertEqual(result.errors, [])
        self.assertTrue(any("Legacy plan schema 2" in warning for warning in result.warnings))
        self.assertTrue(any("fixture availability" in note and "NOT performed" in note for note in result.notes))
        self.plan.write_text(PLAN.replace("**Plan schema version:** 2\n", ""), encoding="utf-8")
        self.assertTrue(any("schema unspecified" in warning for warning in v.validate_plan(self.plan).warnings))

    def test_schema3_diverse_projects_use_declared_layers_not_site_specific_ids(self):
        cases = [
            ("Editorial blog", "ENTRY-001", "php, browser", "core, theme, php", "theme/entry.php: render_entry()", "Create one disposable draft with the documented editor role.", "Disposable draft removed; original published entry unchanged."),
            ("Membership portal", "ACCESS-001", "php, browser, external", "plugin:member-tools, php", "member-tools/access.php: access_policy() and sandbox provider configuration", "Use a sandbox member with an expired trial; no real notifications.", "Sandbox member returned to recorded trial state."),
            ("Product catalogue", "LOOKUP-001", "php, infrastructure", "plugin:catalogue, php, env", "catalogue/index.php: query_index() and local cache configuration", "Create disposable item in a documented empty category.", "Item removed; category and cache configuration restored."),
            ("Static resource library", "NAV-001", "browser, static", "theme", "assets/navigation.js: toggleMenu()", "No generated records; use the existing example page.", "Menu closed; no persistent state changed."),
        ]
        for project in cases:
            with self.subTest(project=project[0]):
                self.plan.write_text(quality_plan(*project), encoding="utf-8")
                result = v.validate_plan(self.plan)
                self.assertEqual(result.errors, [])
                self.assertEqual(result.warnings, [])
                # Even a self-declared semantic review is not independently verified.
                self.assertTrue(any("actual endpoints" in note and "branch coverage" in note for note in result.notes))

    def test_schema3_missing_runtime_and_environment_tags_are_errors(self):
        cases = [
            ("Editorial blog", "ENTRY-001", "php, browser", "theme", "php execution layer"),
            ("Membership portal", "ACCESS-001", "php, external", "plugin:member-tools", "php execution layer"),
            ("Catalogue", "LOOKUP-001", "infrastructure", "plugin:catalogue", "infrastructure execution layer"),
        ]
        for project, test_id, layers, update_tags, expected_error in cases:
            with self.subTest(project=project):
                text = quality_plan(project, test_id, layers, update_tags, "implementation/file: handler", "Use a documented fixture.", "Restore the documented original state.")
                self.plan.write_text(text, encoding="utf-8")
                self.assertTrue(any(expected_error in error for error in v.validate_plan(self.plan).errors))

    def test_schema3_requires_each_active_evidence_and_fixture_field(self):
        complete = quality_plan("Blog", "ENTRY-001", "php", "theme, php", "theme/entry.php: render_entry()", "Create a disposable draft.", "Draft deleted.")
        for name in ("Execution layers", "Implementation evidence", "Fixture setup", "State after cleanup"):
            with self.subTest(field=name):
                text = "\n".join(line for line in complete.splitlines() if not line.startswith(f"- **{name}:**"))
                self.plan.write_text(text, encoding="utf-8")
                self.assertTrue(any(name in error for error in v.validate_plan(self.plan).errors))

    def test_schema3_unknown_layer_needs_specific_limitation_and_warns(self):
        text = quality_plan("Membership", "ACCESS-001", "unknown", "plugin:member-tools", "Unresolved: vendor source is not available for the access handler.", "Use an isolated test account.", "Original test-account state restored.")
        for generic in ("None", "Unknown", "Not established", "Unresolved:", "Unresolved: unknown"):
            with self.subTest(limitation=generic):
                self.plan.write_text(text.replace("**Known limitations / dependencies:** None", f"**Known limitations / dependencies:** {generic}"), encoding="utf-8")
                self.assertTrue(any("unknown execution layer" in error for error in v.validate_plan(self.plan).errors))
        text = text.replace("**Known limitations / dependencies:** None", "**Known limitations / dependencies:** Vendor handler cannot be inspected; the runtime layer is unresolved.")
        self.plan.write_text(text, encoding="utf-8")
        result = v.validate_plan(self.plan)
        self.assertEqual(result.errors, [])
        self.assertTrue(any("execution layers remain unknown" in warning for warning in result.warnings))
        self.assertTrue(any("Implementation evidence is unresolved" in warning for warning in result.warnings))

    def test_schema3_unresolved_fixture_is_not_silently_treated_as_ready(self):
        text = quality_plan("Catalogue", "LOOKUP-001", "php", "plugin:catalogue, php", "catalogue/lookup.php: render_results()", "Unresolved: no reproducible item with an empty optional field was found.", "Disposable item should be removed after execution.")
        self.plan.write_text(text, encoding="utf-8")
        result = v.validate_plan(self.plan)
        self.assertEqual(result.errors, [])
        self.assertTrue(any("Fixture setup is unresolved" in warning for warning in result.warnings))
        self.plan.write_text(text.replace("Unresolved: no reproducible item with an empty optional field was found.", "Unresolved: TBD"), encoding="utf-8")
        self.assertTrue(any("specific Unresolved reason" in error for error in v.validate_plan(self.plan).errors))

    def test_schema3_multiline_fields_and_retired_history_remain_usable(self):
        text = quality_plan("Blog", "ENTRY-001", "php", "theme, php", "theme/entry.php: render_entry()", "\n  1. Create a draft.\n  2. Record its disposable ID.", "Draft deleted; prior state restored.")
        self.plan.write_text(text, encoding="utf-8")
        self.assertEqual(v.validate_plan(self.plan).errors, [])
        text = text.replace("| ACTIVE | P0", "| REMOVED | P0").replace("| Y | None", "| N | None").replace("**Essential smoke checks after any update:** ENTRY-001", "**Essential smoke checks after any update:** None").replace("- **Lifecycle:** ACTIVE", "- **Lifecycle:** REMOVED\n- **Removal date / reason:** 2026-11-02 — Feature retired")
        text = "\n".join(line for line in text.splitlines() if not any(line.startswith(f"- **{name}:**") for name in ("Execution layers", "Implementation evidence", "Fixture setup", "State after cleanup")))
        self.plan.write_text(text, encoding="utf-8")
        self.assertEqual(v.validate_plan(self.plan).errors, [])

    def test_plan_cli_labels_structural_success_and_unverified_semantics(self):
        command = [sys.executable, str(Path(v.__file__)), "plan", str(self.plan)]
        run = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("plan: STRUCTURAL OK", run.stdout)
        self.assertIn("Semantic review NOT performed", run.stdout)
        self.assertIn("Legacy plan schema 2", run.stdout)

    def test_plan_detects_duplicate_ids(self):
        self.plan.write_text(PLAN.replace("**Essential smoke", "| HOME-001 | Duplicate | ACTIVE | P0 | core, theme | Y | None | None | Duplicate |\n**Essential smoke"), encoding="utf-8")
        self.assertTrue(any("Duplicate matrix" in error for error in v.validate_plan(self.plan).errors))

    def test_plan_detects_priority_tag_and_smoke_drift(self):
        self.plan.write_text(PLAN.replace("Contact form — P1", "Contact form — P2").replace("- **Update types:** core, theme", "- **Update types:** core").replace("**Essential smoke checks after any update:** HOME-001", "**Essential smoke checks after any update:** FORM-CONTACT-001"), encoding="utf-8")
        errors = v.validate_plan(self.plan).errors
        self.assertTrue(any("priority differs" in error for error in errors))
        self.assertTrue(any("tags differ" in error for error in errors))
        self.assertTrue(any("smoke list differs" in error for error in errors))

    def test_plan_detects_dangling_dependency(self):
        self.plan.write_text(PLAN.replace("- **Depends on:** HOME-001", "- **Depends on:** MISSING-001"), encoding="utf-8")
        self.assertTrue(any("unknown Depends on" in error for error in v.validate_plan(self.plan).errors))

    def test_plan_rejects_circular_fixture_prerequisites(self):
        text = PLAN.replace("| Y | None | FORM-CONTACT-001", "| Y | FORM-CONTACT-001 | FORM-CONTACT-001").replace("- **Depends on:** None", "- **Depends on:** FORM-CONTACT-001", 1)
        self.plan.write_text(text, encoding="utf-8")
        self.assertTrue(any("Circular active prerequisites" in error for error in v.validate_plan(self.plan).errors))

    def test_plan_rejects_completed_results_and_project_placeholders(self):
        self.plan.write_text(PLAN.replace("Header and primary call to action appear.", "<expected behavior>").replace("- **Status:** NOT RUN\n## G.", "- **Status:** PASS\n## G."), encoding="utf-8")
        errors = v.validate_plan(self.plan).errors
        self.assertTrue(any("unresolved project placeholder" in error for error in errors))
        self.assertTrue(any("Status must be NOT RUN" in error for error in errors))

    def test_legacy_lifecycle_warns_without_rejecting_valid_plan(self):
        text = PLAN.replace(" | Lifecycle", "").replace(" | ACTIVE", "").replace("- **Lifecycle:** ACTIVE\n", "")
        # Remove the matching matrix separator cell when removing a column.
        text = text.replace("| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |", "| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |")
        self.plan.write_text(text, encoding="utf-8")
        result = v.validate_plan(self.plan)
        self.assertEqual(result.errors, [])
        self.assertTrue(result.warnings)

    def test_valid_report_and_full_plan_accounting(self):
        self.assertEqual(v.validate_report(self.report, self.plan).errors, [])

    def test_report_detects_wrong_counts_and_missing_test(self):
        self.report.write_text(REPORT.replace("PASS: 1", "PASS: 2").replace("| FORM-CONTACT-001 | ACTIVE | Yes/full | BLOCKED | SMTP isolation could not be verified. | — | No mail catcher available |", ""), encoding="utf-8")
        errors = v.validate_report(self.report, self.plan).errors
        self.assertTrue(any("Report/plan IDs differ" in error for error in errors))
        self.assertTrue(any("count should be" in error for error in errors))

    def test_report_rejects_unselected_as_not_applicable(self):
        self.report.write_text(REPORT.replace("Yes/full | BLOCKED", "No | NOT APPLICABLE"), encoding="utf-8")
        self.assertTrue(any("unselected status" in error for error in v.validate_report(self.report).errors))

    def test_report_checks_evidence_and_incomplete_runs(self):
        self.image.unlink()
        self.report.write_text(REPORT.replace("Yes/full | BLOCKED", "Yes/full | NOT RUN"), encoding="utf-8")
        errors = v.validate_report(self.report).errors
        self.assertTrue(any("Missing evidence" in error for error in errors))
        self.assertTrue(any("Run completeness" in error for error in errors))

    def test_valid_checkpoint(self):
        self.assertEqual(self.validate_checkpoint(self.checkpoint()).errors, [])

    def test_checkpoint_preserves_unknown_activation_without_losing_version(self):
        data = self.checkpoint()
        for collection in ("themes", "plugins"):
            data["inventory"][collection][0].update(active=None, activation_note="Only local source files are readable; current activation options and admin access are unavailable.")
        result = self.validate_checkpoint(data)
        self.assertEqual(result.errors, [])
        self.assertEqual(sum("activation is unknown" in warning for warning in result.warnings), 2)
        self.assertEqual(data["inventory"]["plugins"][0]["version"], "1.0")
        self.assertEqual(data["run_completeness"], "Complete")

    def test_checkpoint_unknown_activation_requires_its_own_specific_reason(self):
        for collection in ("themes", "plugins"):
            for note in (None, "", "Unknown", "Unresolved: Unknown", [], 1):
                with self.subTest(collection=collection, note=note):
                    data = self.checkpoint()
                    data["limitations"].append("Some unrelated metadata was unavailable")
                    data["inventory"][collection][0].update(active=None, activation_note=note)
                    errors = self.validate_checkpoint(data).errors
                    self.assertTrue(any("specific activation_note" in error for error in errors))
            for invalid in (0, 1, "false", "unknown", []):
                with self.subTest(collection=collection, invalid=invalid):
                    data = self.checkpoint()
                    data["inventory"][collection][0]["active"] = invalid
                    self.assertTrue(any("active must be boolean or null" in error for error in self.validate_checkpoint(data).errors))
        # Existing confirmed booleans remain valid without an added activation note.
        data = self.checkpoint()
        data["inventory"]["plugins"][0]["active"] = False
        self.assertEqual(self.validate_checkpoint(data).errors, [])

    def test_failed_then_passed_retry_stays_failure(self):
        data = self.checkpoint()
        test = data["tests"][0]
        test["attempts"][0]["status"] = "FAIL"
        test["attempts"].append(deepcopy(test["attempts"][0]))
        test["attempts"][1].update(number=2, status="PASS")
        self.assertTrue(any("any FAIL wins" in error for error in self.validate_checkpoint(data).errors))
        test["status"] = "FAIL"
        self.assertEqual(self.validate_checkpoint(data).errors, [])

    def test_checkpoint_rejects_evidence_tampering_and_path_escape(self):
        data = self.checkpoint()
        data["tests"][0]["attempts"][0]["captures"][0]["sha256"] = "0" * 64
        self.assertTrue(any("hash mismatch" in error for error in self.validate_checkpoint(data).errors))
        data["tests"][0]["attempts"][0]["evidence"].append("../outside.txt")
        self.assertTrue(any("inside this bundle" in error for error in self.validate_checkpoint(data).errors))

    def test_checkpoint_rejects_incompatible_schema_identity_and_context(self):
        data = self.checkpoint()
        data["schema_version"] = 99
        data["project"]["site_url"] = "https://user:secret@demo.test"
        del data["tests"][0]["attempts"][0]["captures"][0]["role"]
        errors = self.validate_checkpoint(data).errors
        self.assertTrue(any("schema_version" in error for error in errors))
        self.assertTrue(any("credential-free" in error for error in errors))
        self.assertTrue(any("missing role" in error for error in errors))

    def test_unknown_identity_keeps_blocked_run_honest_without_allowing_comparison(self):
        data = self.checkpoint()
        data["project"] = {key: None for key in data["project"]}
        data["limitations"].append("Project root, WordPress root, site/home URLs, and blog ID could not be established offline")
        test = data["tests"][0]
        test.update(status="BLOCKED", reason="Verified local site identity/access unavailable")
        test["attempts"][0].update(status="BLOCKED", observation="No verified local site was available", evidence=[], captures=[])
        result = self.validate_checkpoint(data)
        self.assertEqual(result.errors, [])
        self.assertEqual(sum("Comparison unavailable: identity" in warning for warning in result.warnings), 4)
        self.assertEqual(data["run_completeness"], "Complete")

    def test_checkpoint_roots_must_be_absolute_paths_not_unknown_labels(self):
        data = self.checkpoint()
        data["project"]["wordpress_root"] = "Not established"
        self.assertTrue(any("absolute filesystem path" in error for error in self.validate_checkpoint(data).errors))
        data["project"]["wordpress_root"] = "/srv/demo/public"
        self.assertEqual(self.validate_checkpoint(data).errors, [])

    def test_checkpoint_rejects_a_mismatched_technical_report(self):
        self.assertEqual(self.validate_checkpoint(self.checkpoint()).errors, [])
        text = self.report.read_text(encoding="utf-8").replace("| PASS |", "| FAIL |")
        self.report.write_text(text, encoding="utf-8")
        self.assertTrue(any("checkpoint/report status differs" in error for error in v.validate_checkpoint(self.bundle / "checkpoint.json").errors))

    def test_checkpoint_missing_and_malformed_are_errors(self):
        self.assertTrue(v.validate_checkpoint(self.bundle / "missing.json").errors)
        path = self.bundle / "checkpoint.json"
        path.write_text("{broken", encoding="utf-8")
        self.assertTrue(v.validate_checkpoint(path).errors)
        path.write_text("[]", encoding="utf-8")
        self.assertTrue(v.validate_checkpoint(path).errors)

    def test_checkpoint_wrong_nested_types_return_errors(self):
        data = self.checkpoint()
        data["scope"]["name"] = []
        data["tests"][0]["lifecycle"] = []
        data["tests"][0]["status"] = []
        data["cleanup"]["status"] = []
        self.assertGreaterEqual(len(self.validate_checkpoint(data).errors), 4)

    def test_plugin_accepts_claude_fields_and_detects_contract_drift(self):
        plugin = self.bundle / "plugin"
        (plugin / ".claude-plugin").mkdir(parents=True)
        (plugin / ".claude-plugin/plugin.json").write_text(json.dumps({"name": "wp-checkpoint", "version": "1.2.0", "description": "Testing"}), encoding="utf-8")
        (plugin / ".claude-plugin/marketplace.json").write_text(json.dumps({"plugins": [{"name": "wp-checkpoint", "source": "."}]}), encoding="utf-8")
        vocabulary = "\n".join((*v.STATUSES, "ACTIVE", "REMOVED", "Critical", "High", "Medium", "Low", "Confirmed regression", "Known issue", "New issue of uncertain origin", "Intermittent", "WordPress Administrator", "Developer", "Hosting Administrator"))
        shared_contract = f"## Vocabulary\n{vocabulary}\nUnselected tests stay NOT RUN."
        for name in ("test", "test-plan-create"):
            skill = plugin / "skills" / name
            (skill / "references").mkdir(parents=True)
            (skill / "SKILL.md").write_text(f'---\nname: {name}\ndescription: Local validation example\ndisable-model-invocation: true\nargument-hint: "[full|smoke|targeted]"\n---\nRead [rules](references/shared-conventions.md).\n', encoding="utf-8")
            (skill / "references/shared-conventions.md").write_text(f"# Shared conventions\n\n{shared_contract}\n", encoding="utf-8")
            (skill / "references/storage-preflight.md").write_text("Same storage", encoding="utf-8")
        assets = plugin / "skills/test-plan-create/assets"
        assets.mkdir()
        report_shape = "```markdown\n# Report\nFull plan: <counts>\n```"
        template_path = assets / "testing-after-update-template.md"
        template_text = f"## G. Vocabulary\n#{shared_contract}\n## H. Future report\n{report_shape}"
        template_path.write_text(template_text, encoding="utf-8")
        fallback = plugin / "skills/test/assets/report-template-fallback.md"
        fallback.parent.mkdir()
        fallback.write_text(report_shape, encoding="utf-8")
        self.assertEqual(v.validate_plugin(plugin).errors, [])
        # Keep all vocabulary tokens while changing a rule: token-presence alone misses this.
        template_path.write_text(template_text.replace("Unselected tests stay NOT RUN.", "Unselected tests may PASS."), encoding="utf-8")
        self.assertTrue(any("embedded shared contract is out of sync" in error for error in v.validate_plugin(plugin).errors))
        template_path.write_text(template_text, encoding="utf-8")
        fallback.write_text(report_shape.replace("Full plan:", "Selected only:"), encoding="utf-8")
        self.assertTrue(any("fallback report shape are out of sync" in error for error in v.validate_plugin(plugin).errors))
        fallback.write_text(report_shape, encoding="utf-8")
        (plugin / "skills/test/references/shared-conventions.md").write_text("Drifted contract", encoding="utf-8")
        self.assertTrue(any("Shared copies differ" in error for error in v.validate_plugin(plugin).errors))
        (plugin / "skills/test/references/shared-conventions.md").unlink()
        self.assertTrue(any("Broken local link" in error for error in v.validate_plugin(plugin).errors))

    def test_checkpoint_incomplete_scope_and_removed_history(self):
        data = self.checkpoint()
        test = data["tests"][0]
        test.update(status="NOT RUN", reason="Time budget ended", attempts=[])
        self.assertTrue(any("run_completeness" in error for error in self.validate_checkpoint(data).errors))
        data["run_completeness"] = "Incomplete"
        self.assertEqual(self.validate_checkpoint(data).errors, [])
        test.update(lifecycle="REMOVED", selected=False, reason="Removed 2026-11-01: no longer exists")
        data["run_completeness"] = "Complete"
        self.assertEqual(self.validate_checkpoint(data).errors, [])

    def test_cli_read_only_exit_codes(self):
        before = {path: path.read_bytes() for path in self.bundle.rglob("*") if path.is_file()}
        command = [sys.executable, str(Path(v.__file__)), "report", str(self.report), "--plan", str(self.plan)]
        run = subprocess.run(command, capture_output=True, text=True, check=False)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(before, {path: path.read_bytes() for path in self.bundle.rglob("*") if path.is_file()})
        self.report.write_text(REPORT.replace("PASS: 1", "PASS: 8"), encoding="utf-8")
        self.assertEqual(subprocess.run(command, capture_output=True, check=False).returncode, 1)


if __name__ == "__main__":
    unittest.main()
