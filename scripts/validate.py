#!/usr/bin/env python3
"""Read-only structural checks for WP Checkpoint; Python 3.10+, no dependencies.

This does not run WordPress, verify activation facts, endpoints, fixture availability
or branch coverage, establish acceptance criteria, inspect DOCX layout, or prove
recorded observations. Exit 0 means structural checks passed; exit 1 means invalid
input. Plan schema 3 adds declared evidence/layer/fixture checks, not a semantic
review. Older plans remain compatible with warnings. Only user-supplied files and
local evidence inside their bundle are read.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from graphlib import CycleError, TopologicalSorter
import hashlib
import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import sys
from urllib.parse import unquote, urlsplit

STATUSES = ("NOT RUN", "PASS", "FAIL", "BLOCKED", "NOT APPLICABLE")
TEST_ID = re.compile(r"\b[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}\b")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
EMPTY = {"", "—", "–", "-", "None", "none", "N/A"}
EXECUTION_LAYERS = {"php", "browser", "infrastructure", "external", "static", "unknown"}
UNINFORMATIVE = {"", "—", "–", "-", "none", "n/a", "not applicable", "unknown", "not established", "unresolved", "tbd", "todo", "to do", "pending"}
SEMANTIC_LIMIT = (
    "Semantic review NOT performed: this validator does not verify activation facts, "
    "actual endpoints, fixture availability, or branch coverage. Source-backed review "
    "is still required, regardless of the plan's recorded Semantic review label."
)


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def require(self, condition: bool, message: str) -> None:
        if not condition:
            self.errors.append(message)

    def warn(self, message: str) -> None:
        if message not in self.warnings:
            self.warnings.append(message)


def read_text(path: Path, result: Result) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        result.errors.append(f"Cannot read {path}: {exc}")
        return ""


def clean(value: str) -> str:
    return re.sub(r"[*`]", "", value).strip()


def prose(text: str) -> str:
    """Exclude comments and fenced format examples, not real cards."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    output: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        marker = re.match(r"\s*(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker.group(1)
            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
            continue
        if fence is None:
            output.append(line)
    return "\n".join(output)


def section(text: str, letter: str) -> str:
    match = re.search(rf"^##\s+{letter}\.\s+.*$", text, re.M)
    if not match:
        return ""
    end = re.search(r"^##\s+[A-I]\.\s+", text[match.end():], re.M)
    return text[match.end():match.end() + end.start()] if end else text[match.end():]


def cells(line: str) -> list[str]:
    return [clean(cell.replace(r"\|", "|")) for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def tables(text: str) -> list[tuple[list[str], list[dict[str, str]]]]:
    lines = text.splitlines()
    found = []
    index = 0
    while index + 1 < len(lines):
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        headers, separator = cells(lines[index]), cells(lines[index + 1])
        if len(headers) != len(separator) or not all(re.fullmatch(r":?-+:?", cell) for cell in separator):
            index += 1
            continue
        rows = []
        index += 2
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            values = cells(lines[index])
            # A malformed row remains visible to callers rather than being lost.
            rows.append(dict(zip(headers, values)) | {"__width__": str(len(values)), "__expected_width__": str(len(headers))})
            index += 1
        found.append((headers, rows))
    return found


def matrix(text: str, required: set[str], result: Result) -> list[dict[str, str]]:
    matches = [(headers, rows) for headers, rows in tables(text) if required <= set(headers)]
    result.require(len(matches) == 1, f"Expected exactly one matrix with columns {', '.join(sorted(required))}; found {len(matches)}")
    if len(matches) != 1:
        return []
    for row in matches[0][1]:
        result.require(row["__width__"] == row["__expected_width__"], f"Malformed table row: {row.get('Test ID', '(missing ID)')}")
    return matches[0][1]


def ids(value: str) -> set[str]:
    return set(TEST_ID.findall(value))


def tags(value: str) -> set[str]:
    return {tag.strip() for tag in value.split(",") if tag.strip()}


def field_value(body: str, name: str) -> str | None:
    match = re.search(rf"^\s*(?:-\s*)?\*\*{re.escape(name)}:\*\*[^\S\n]*(.*)$", body, re.M)
    return clean(match.group(1)) if match else None


def field_block(body: str, name: str) -> str | None:
    """A prose field may use indented lists; do not swallow the next field/card."""
    match = re.search(rf"^\s*(?:-\s*)?\*\*{re.escape(name)}:\*\*[^\S\n]*(.*)$", body, re.M)
    if not match:
        return None
    remaining = body[match.end():]
    end = re.search(r"^\s*(?:(?:-\s*)?\*\*[^\n*]+:\*\*|#{1,6}\s|---\s*$)", remaining, re.M)
    continuation = remaining[:end.start()] if end else remaining
    return clean(match.group(1) + continuation)


def informative(value: str | None) -> bool:
    if value is None:
        return False
    normalized = " ".join(clean(value).split()).casefold().strip(" .:;")
    return normalized not in UNINFORMATIVE


def validate_plan_quality_fields(test_id: str, body: str, update_tags: set[str], result: Result) -> None:
    """Validate declared relationships, never infer runtime facts from names/prose."""
    layers_value = field_value(body, "Execution layers")
    layers = tags(layers_value or "")
    result.require(bool(layers), f"{test_id}: schema 3 requires Execution layers")
    result.require(not (layers - EXECUTION_LAYERS), f"{test_id}: invalid Execution layers {sorted(layers - EXECUTION_LAYERS)}")
    if "php" in layers:
        result.require("php" in update_tags, f"{test_id}: declared php execution layer requires the php update tag")
    if "infrastructure" in layers:
        result.require("env" in update_tags, f"{test_id}: declared infrastructure execution layer requires the env update tag")
    for name in ("Implementation evidence", "Fixture setup", "State after cleanup"):
        value = field_block(body, name)
        result.require(informative(value), f"{test_id}: schema 3 requires informative {name}; use Unresolved: reason for a real gap")
        unresolved = re.match(r"^Unresolved\s*:\s*(.*)$", value or "", re.I | re.S)
        if unresolved:
            result.require(informative(unresolved.group(1)), f"{test_id}: {name} needs a specific Unresolved reason")
            result.warn(f"{test_id}: {name} is unresolved; evidence review is required before relying on this test")
    if "unknown" in layers:
        limitation = field_block(body, "Known limitations / dependencies")
        unresolved = re.match(r"^Unresolved\s*:\s*(.*)$", limitation or "", re.I | re.S)
        detail = unresolved.group(1) if unresolved else limitation
        result.require(informative(detail), f"{test_id}: unknown execution layer requires a specific Known limitations / dependencies reason")
        result.warn(f"{test_id}: execution layers remain unknown; update-impact coverage needs source-backed review")


def index_rows(rows: list[dict[str, str]], result: Result) -> dict[str, dict[str, str]]:
    indexed = {}
    for row in rows:
        test_id = row.get("Test ID", "")
        result.require(bool(TEST_ID.fullmatch(test_id)), f"Invalid test ID: {test_id!r}")
        result.require(test_id not in indexed, f"Duplicate matrix ID: {test_id}")
        indexed[test_id] = row
    return indexed


def plan_data(path: Path, result: Result) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    text = prose(read_text(path, result))
    rows = matrix(section(text, "D"), {"Test ID", "Priority", "Update-type tags", "Smoke?"}, result)
    indexed = index_rows(rows, result)
    catalogue = section(text, "F")
    headings = list(re.finditer(r"^####\s+([^\n]+)$", catalogue, re.M))
    cards: dict[str, str] = {}
    for pos, heading in enumerate(headings):
        card_id = TEST_ID.search(heading.group(1))
        result.require("EXAMPLE" not in heading.group(1), "Example card remains in actual catalogue")
        if not card_id:
            result.errors.append(f"Card heading has no valid ID: {heading.group(1)}")
            continue
        test_id = card_id.group()
        result.require(test_id not in cards, f"Duplicate card ID: {test_id}")
        end = headings[pos + 1].start() if pos + 1 < len(headings) else len(catalogue)
        cards[test_id] = catalogue[heading.end():end]
    result.require(bool(indexed), "Plan matrix must contain at least one test")
    result.require(set(indexed) == set(cards), f"Matrix/card IDs differ: matrix only={sorted(set(indexed) - set(cards))}; cards only={sorted(set(cards) - set(indexed))}")
    return indexed, cards


def validate_plan(path: Path) -> Result:
    result = Result()
    indexed, cards = plan_data(path, result)
    text = prose(read_text(path, result))
    result.notes.append(SEMANTIC_LIMIT)
    schema = field_value(text, "Plan schema version")
    result.require(schema is None or schema in {"1", "2", "3"}, f"Unsupported Plan schema version: {schema!r}")
    if schema in (None, "1", "2"):
        result.warn(f"Legacy plan schema {schema or 'unspecified'}: schema-3 execution-layer, evidence and fixture checks were not applied; structural success is not a semantic-quality verdict")
    for letter in "ABCDEFGHI":
        result.require(bool(section(text, letter).strip()), f"Missing/empty plan section {letter}")
    for test_id, row in indexed.items():
        body = cards.get(test_id, "")
        lifecycle = row.get("Lifecycle", "ACTIVE")
        card_lifecycle = field_value(body, "Lifecycle") or "ACTIVE"
        if "Lifecycle" not in row or field_value(body, "Lifecycle") is None:
            result.warn("Legacy plan: missing Lifecycle is treated as ACTIVE; refresh the plan to record lifecycle explicitly")
        result.require(lifecycle in {"ACTIVE", "REMOVED"}, f"{test_id}: invalid Lifecycle {lifecycle!r}")
        result.require(lifecycle == card_lifecycle, f"{test_id}: matrix/card Lifecycle differs")
        priority = re.search(r"\bP[012]\b", field_value(body, "Feature / Priority") or "")
        result.require(row.get("Priority") in {"P0", "P1", "P2"}, f"{test_id}: invalid priority")
        result.require(bool(priority) and priority.group() == row.get("Priority"), f"{test_id}: matrix/card priority differs")
        result.require(tags(row.get("Update-type tags", "")) == tags(field_value(body, "Update types") or ""), f"{test_id}: matrix/card update tags differ")
        for tag in tags(row.get("Update-type tags", "")):
            result.require(bool(re.fullmatch(r"core|theme|builder|php|env|plugin:[a-z0-9][a-z0-9._-]*", tag)), f"{test_id}: invalid update tag {tag!r}")
        result.require(bool(tags(row.get("Update-type tags", ""))), f"{test_id}: no update tags")
        result.require(row.get("Smoke?") in {"Y", "N"}, f"{test_id}: Smoke? must be Y or N")
        result.require(field_value(body, "Status") == "NOT RUN", f"{test_id}: plan Status must be NOT RUN")
        if schema == "3" and lifecycle == "ACTIVE":
            validate_plan_quality_fields(test_id, body, tags(row.get("Update-type tags", "")), result)
        if lifecycle == "REMOVED":
            result.require(row.get("Smoke?") == "N", f"{test_id}: removed test cannot be smoke")
            removal = field_value(body, "Removal date / reason") or ""
            result.require(bool(re.match(r"\d{4}-\d{2}-\d{2}\s+[—–-]\s+\S", removal)), f"{test_id}: removed card needs dated removal reason")
        for relationship in ("Depends on", "Affects"):
            card_refs = ids(field_value(body, relationship) or "")
            if relationship in row:
                result.require(card_refs == ids(row[relationship]), f"{test_id}: matrix/card {relationship} differs")
            else:
                result.warn(f"Legacy plan: {relationship} missing from matrix; card references still checked")
            result.require(not (card_refs - indexed.keys()), f"{test_id}: unknown {relationship} IDs {sorted(card_refs - indexed.keys())}")
            result.require(test_id not in card_refs, f"{test_id}: self-reference in {relationship}")
            if lifecycle == "ACTIVE":
                retired = [target for target in card_refs if indexed.get(target, {}).get("Lifecycle") == "REMOVED"]
                result.require(not retired, f"{test_id}: active {relationship} refers to removed tests {retired}")
    active_ids = {test_id for test_id, row in indexed.items() if row.get("Lifecycle", "ACTIVE") == "ACTIVE"}
    prerequisites = {test_id: ids(field_value(cards.get(test_id, ""), "Depends on") or "") & active_ids for test_id in active_ids}
    try:
        TopologicalSorter(prerequisites).prepare()
    except CycleError as exc:
        result.errors.append(f"Circular active prerequisites: {' -> '.join(exc.args[1])}")
    smoke = re.search(r"^\*\*Essential smoke checks after any update:\*\*\s*(.*)$", section(text, "D"), re.M)
    result.require(smoke is not None, "Missing essential smoke ID list")
    if smoke:
        expected = {test_id for test_id, row in indexed.items() if row.get("Smoke?") == "Y"}
        result.require(ids(smoke.group(1)) == expected, "Essential smoke list differs from matrix Smoke=Y IDs")
    # Format examples G/H and fenced F are deliberately generic; project fields are not.
    for letter in "ABCDEF I".replace(" ", ""):
        body = section(text, letter)
        for value in re.findall(r"<([^>\n]+)>", body):
            if not re.match(r"/?(?:a|div|span|input|button|form|p|img|script|style|br|h[1-6])(?:\s|/|$)", value, re.I):
                result.errors.append(f"Section {letter}: unresolved project placeholder <{value}>")
        result.require("EXAMPLE —" not in body, f"Section {letter}: example content remains")
    return result


def safe_evidence(bundle: Path, value: str, result: Result) -> Path | None:
    value = unquote(value).replace("\\", "/")
    try:
        candidate = Path(value)
        valid = bool(value) and not candidate.is_absolute() and not PureWindowsPath(value).is_absolute() and not urlsplit(value).scheme and ".." not in candidate.parts
        resolved = (bundle / candidate).resolve()
        valid = valid and resolved.is_relative_to(bundle.resolve())
    except (OSError, ValueError):
        result.errors.append("Invalid evidence path")
        return None
    result.require(valid, f"Evidence must be a relative file inside this bundle: {value!r}")
    if not valid:
        return None
    result.require(resolved.is_file(), f"Missing evidence: {value}")
    return resolved if resolved.is_file() else None


def evidence_refs(value: str) -> list[str]:
    linked = re.findall(r"!?\[[^\]]*\]\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)", value)
    paths = [left or right for left, right in linked]
    without_links = re.sub(r"!?\[[^\]]*\]\([^)]*\)", "", value)
    paths.extend(re.findall(r"(?:screenshots/[^\s,;`\]<>]+\.(?:png|jpe?g|webp)|log-excerpt\.txt)", without_links, re.I))
    return list(dict.fromkeys(path.split("#", 1)[0] for path in paths))


def reconcile_run_state(path: Path, text: str, indexed: dict[str, dict[str, str]], result: Result,
                        plan: Path | None = None, state_path: Path | None = None,
                        require_final: bool = False) -> dict | None:
    """Match a report to its operational ledger without revalidating report structure.

    Historical reports need no ledger. Recorded plan hashes are compared to the
    ledger; a later-edited canonical plan is read only when explicitly supplied.
    """
    try:
        candidate = Path(state_path) if state_path is not None else path.parent / "run-state.json"
        if state_path is None and not candidate.exists() and not candidate.is_symlink():
            return None
        if candidate.is_dir():
            candidate = candidate / "run-state.json"
        if candidate.parent.resolve() != path.parent.resolve():
            result.errors.append("Run state must belong to the same report bundle")
            return None
    except (OSError, ValueError, TypeError) as exc:
        result.errors.append(f"Cannot resolve run state: {exc}")
        return None
    try:
        # Local import prevents a top-level validate -> run_state -> validate cycle.
        import run_state
        state = run_state.load(candidate)
    except (ImportError, OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        result.errors.append(f"Cannot validate run state: {exc}")
        return None
    state_rows = {test["id"]: test for test in state["tests"]}
    result.require(set(indexed) == set(state_rows),
                   f"Report/run-state IDs differ: missing={sorted(set(state_rows) - set(indexed))}; extra={sorted(set(indexed) - set(state_rows))}")
    for test_id in indexed.keys() & state_rows.keys():
        row, test = indexed[test_id], state_rows[test_id]
        result.require(row.get("Status") == test["status"], f"{test_id}: report/run-state status differs")
        result.require(row.get("Lifecycle") == test["lifecycle"], f"{test_id}: report/run-state lifecycle differs")
        selection = row.get("Selected for this run's scope?", "")
        result.require(selection == test["category"], f"{test_id}: report/run-state selection category differs")
        result.require(selection.startswith("Yes") == test["selected"], f"{test_id}: report/run-state selected flag differs")
    result.require(field_value(text, "Mode") == state["mode"], "Report/run-state Mode differs")
    if require_final:
        result.require(state["lifecycle"] == "COMPLETE", "Complete checkpoint requires a finalized run-state ledger")
    reference = field_value(text, "Test-plan reference")
    if reference:
        declared_hash = re.search(r"\bSHA256\s*[:=]?\s*([a-fA-F0-9]{64})(?=\s|[,;]|$)", reference, re.I)
        if declared_hash:
            result.require(declared_hash.group(1).lower() == state["plan"]["sha256"], "Report/run-state recorded plan SHA256 differs")
        elif re.search(r"\bSHA256\b", reference, re.I):
            result.errors.append("Report Test-plan reference contains an invalid or missing SHA256")
        else:
            result.warn("Report Test-plan reference has no recorded SHA256; historical plan identity was not fully checked")
    else:
        result.warn("Report has no Test-plan reference SHA256; historical plan identity was not fully checked")
    if plan is not None:
        try:
            result.require(Path(plan).resolve() == Path(state["plan"]["path"]).resolve(), "Explicit plan path differs from run-state plan")
            result.require(hashlib.sha256(Path(plan).read_bytes()).hexdigest() == state["plan"]["sha256"], "Explicit plan SHA256 differs from run-state plan")
        except (OSError, ValueError) as exc:
            result.errors.append(f"Cannot compare explicit plan with run state: {exc}")
    return state


def validate_report(path: Path, plan: Path | None = None, state_path: Path | None = None) -> Result:
    result = Result()
    text = prose(read_text(path, result))
    rows = matrix(text, {"Test ID", "Status", "Actual observation", "Evidence reference"}, result)
    result.require(bool(rows), "Report matrix must contain at least one test")
    indexed = index_rows(rows, result)
    if plan:
        plan_rows, _ = plan_data(plan, result)
        result.require(set(indexed) == set(plan_rows), f"Report/plan IDs differ: missing={sorted(set(plan_rows) - set(indexed))}; extra={sorted(set(indexed) - set(plan_rows))}")
        for test_id in indexed.keys() & plan_rows.keys():
            result.require(indexed[test_id].get("Lifecycle", "ACTIVE") == plan_rows[test_id].get("Lifecycle", "ACTIVE"), f"{test_id}: report/plan lifecycle differs")
    selected = []
    for test_id, row in indexed.items():
        status = row.get("Status", "")
        selection = row.get("Selected for this run's scope?", "")
        result.require(status in STATUSES, f"{test_id}: invalid report status {status!r}")
        result.require(bool(re.match(r"^(Yes|No)(?:\b|/)", selection)), f"{test_id}: selection must begin Yes or No")
        is_selected = selection.startswith("Yes")
        if is_selected:
            selected.append(row)
            if selection == "Yes":
                result.warn("Legacy report: Selected=Yes has no selection category")
            else:
                result.require(selection in ("Yes/full", "Yes/smoke", "Yes/smoke-dependency", "Yes/targeted-tagged", "Yes/targeted-dependency"), f"{test_id}: unknown selection category {selection!r}")
        else:
            result.require(status == "NOT RUN", f"{test_id}: unselected status must be NOT RUN")
        reason = next((value for name, value in row.items() if name.startswith("Reason")), "")
        if not is_selected or status in {"NOT RUN", "BLOCKED", "NOT APPLICABLE"}:
            result.require(reason not in EMPTY, f"{test_id}: missing reason")
        if row.get("Lifecycle") == "REMOVED":
            result.require(not is_selected and status == "NOT RUN", f"{test_id}: removed history must be unselected NOT RUN")
        if status in {"PASS", "FAIL"}:
            result.require(row.get("Actual observation", "") not in EMPTY, f"{test_id}: executed status needs actual observation")
        for ref in evidence_refs(row.get("Evidence reference", "")):
            safe_evidence(path.parent, ref, result)
    for label, subset in (("Full plan", rows), ("Selected scope", selected)):
        tally_line = re.search(rf"^{label}:\s*(.*)$", text, re.M)
        result.require(tally_line is not None, f"Missing {label} counts")
        if tally_line:
            found = dict(re.findall(r"(NOT APPLICABLE|NOT RUN|PASS|FAIL|BLOCKED):\s*(\d+)\b", tally_line.group(1)))
            actual = Counter(row.get("Status") for row in subset)
            result.require(set(found) == set(STATUSES), f"{label}: all five status counts required")
            for status in STATUSES:
                result.require(found.get(status) == str(actual[status]), f"{label}: {status} count should be {actual[status]}")
    completeness = field_value(text, "Run completeness") or ""
    expected_complete = not any(row.get("Status") == "NOT RUN" for row in selected)
    result.require(completeness.startswith("Complete" if expected_complete else "Incomplete"), "Run completeness disagrees with selected NOT RUN rows")
    # Embedded figures outside the matrix must also resolve to actual bundle evidence.
    for image_ref in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text):
        safe_evidence(path.parent, image_ref.strip("<>"), result)
    reconcile_run_state(path, text, indexed, result, plan, state_path)
    return result


def iso_timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None
    except ValueError:
        return False


def public_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return parsed.scheme in ("http", "https") and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def absolute_filesystem_path(value: object) -> bool:
    """Recorded roots may come from another OS; do not require local existence."""
    return isinstance(value, str) and "\x00" not in value and (
        PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute()
    )


def aggregate_attempts(attempts: list[dict]) -> str:
    if any(attempt.get("status") == "FAIL" for attempt in attempts):
        return "FAIL"
    return attempts[-1].get("status", "") if attempts else "NOT RUN"


def validate_checkpoint(path: Path) -> Result:
    result = Result()
    try:
        data = json.loads(read_text(path, result))
    except json.JSONDecodeError as exc:
        result.errors.append(f"Invalid checkpoint JSON: {exc}")
        return result
    if not isinstance(data, dict):
        result.errors.append("Checkpoint root must be an object")
        return result
    result.require(data.get("schema_version") == 1 and type(data.get("schema_version")) is int, "Unsupported checkpoint schema_version (expected 1)")
    result.require(data.get("mode") == "before", "Only mode=before can be a baseline")
    result.require(data.get("run_id") == path.parent.name, "checkpoint run_id must equal bundle directory name")
    result.require(iso_timestamp(data.get("captured_at")), "captured_at must be ISO8601 with UTC offset")
    result.require(isinstance(data.get("timezone"), str) and bool(data.get("timezone")), "Missing timezone")
    for name in ("project", "plan", "scope", "inventory", "cleanup"):
        result.require(isinstance(data.get(name), dict), f"{name} must be an object")
    if any(not isinstance(data.get(name), dict) for name in ("project", "plan", "scope", "inventory", "cleanup")):
        return result
    limitations = data.get("limitations")
    for key in ("project_root", "wordpress_root", "site_url", "home_url"):
        result.require(key in data["project"], f"Missing project.{key}")
        value = data["project"].get(key)
        if value is None:
            result.require(bool(limitations), f"Unknown project.{key} needs a specific limitation")
            result.warn(f"Comparison unavailable: identity project.{key} is not established")
        elif key in ("project_root", "wordpress_root"):
            result.require(absolute_filesystem_path(value), f"project.{key} must be an absolute filesystem path or null")
        else:
            result.require(public_url(value), f"project.{key} must be a credential-free HTTP(S) URL or null")
    result.require("blog_id" in data["project"] and (data["project"]["blog_id"] is None or type(data["project"]["blog_id"]) is int and data["project"]["blog_id"] > 0), "project.blog_id must be a positive integer or null")
    result.require(isinstance(data["plan"].get("path"), str) and bool(data["plan"].get("path")), "Missing plan.path")
    result.require(bool(SHA256.fullmatch(str(data["plan"].get("sha256", "")))), "Invalid plan.sha256")
    result.require(data["scope"].get("name") in ("full", "smoke", "targeted"), "Invalid scope.name")
    result.require(isinstance(data["scope"].get("update_tags"), list) and all(isinstance(tag, str) for tag in data["scope"].get("update_tags", [])), "scope.update_tags must be a string array")
    result.require(isinstance(limitations, list) and all(isinstance(item, str) for item in limitations), "limitations must be a string array")
    if data["project"].get("blog_id") is None:
        result.require(bool(limitations), "Unknown blog_id needs a limitation")
    inventory = data["inventory"]
    for key in ("wordpress_version", "web_php_version", "cli_php_version"):
        result.require(key in inventory and (inventory[key] is None or isinstance(inventory[key], str)), f"inventory.{key} must be string or null")
        if inventory.get(key) is None:
            result.require(bool(limitations), f"Unknown {key} needs a limitation")
    for collection, keys in (("themes", ("slug", "version", "active", "parent")), ("plugins", ("slug", "version", "active", "kind"))):
        entries = inventory.get(collection)
        result.require(isinstance(entries, list), f"inventory.{collection} must be an array")
        if not isinstance(entries, list):
            continue
        seen = set()
        if not entries:
            result.require(bool(limitations), f"Empty inventory.{collection} needs a limitation")
        for entry in entries:
            result.require(isinstance(entry, dict), f"inventory.{collection} entry must be an object")
            if not isinstance(entry, dict):
                continue
            result.require(all(key in entry for key in keys), f"inventory.{collection} entry missing required fields")
            identity = (str(entry.get("kind", "theme")), str(entry.get("slug", "")))
            result.require(identity not in seen and bool(entry.get("slug")), f"Duplicate/empty inventory identity {identity}")
            seen.add(identity)
            activation = entry.get("active")
            result.require(activation is None or type(activation) is bool, f"{identity}: active must be boolean or null")
            if activation is None:
                note = entry.get("activation_note")
                reason = re.sub(r"^Unresolved\s*:\s*", "", note, flags=re.I) if isinstance(note, str) else None
                result.require(informative(reason), f"{identity}: unknown activation needs a specific activation_note on this entry")
                result.warn(f"{identity}: activation is unknown; activation changes cannot be established from this snapshot")
            result.require(entry.get("version") is None or isinstance(entry.get("version"), str), f"{identity}: version must be string or null")
            if entry.get("version") is None:
                result.require(bool(limitations), f"{identity}: unknown version needs a limitation")
            if collection == "plugins":
                result.require(entry.get("kind") in ("plugin", "mu-plugin", "drop-in"), f"{identity}: invalid kind")
            else:
                result.require(entry.get("parent") is None or isinstance(entry.get("parent"), str), f"{identity}: parent must be a string or null")
    result.require(isinstance(inventory.get("environment_notes"), list), "inventory.environment_notes must be an array")
    tests = data.get("tests")
    result.require(isinstance(tests, list) and bool(tests), "tests must be a nonempty array")
    if not isinstance(tests, list):
        return result
    seen = set()
    incomplete = False
    for test in tests:
        result.require(isinstance(test, dict), "Test entry must be an object")
        if not isinstance(test, dict):
            continue
        test_id = test.get("id", "")
        result.require(isinstance(test_id, str) and bool(TEST_ID.fullmatch(test_id)), f"Invalid test ID: {test_id!r}")
        result.require(str(test_id) not in seen, f"Duplicate checkpoint test ID: {test_id}")
        seen.add(str(test_id))
        result.require(test.get("lifecycle") in ("ACTIVE", "REMOVED"), f"{test_id}: invalid lifecycle")
        result.require(type(test.get("selected")) is bool, f"{test_id}: selected must be boolean")
        result.require(isinstance(test.get("selection_reason"), str) and bool(test.get("selection_reason")), f"{test_id}: missing selection_reason")
        result.require(test.get("status") in STATUSES, f"{test_id}: invalid status")
        result.require(isinstance(test.get("reason"), str), f"{test_id}: reason must be string")
        for key in ("expected_result", "starting_location", "role", "prerequisites"):
            result.require(isinstance(test.get(key), str) and bool(test.get(key)), f"{test_id}: missing {key}")
        actions = test.get("actions")
        result.require(isinstance(actions, list) and all(isinstance(action, str) and bool(action) for action in actions), f"{test_id}: actions must be a string array")
        if test.get("lifecycle") == "ACTIVE":
            result.require(bool(actions), f"{test_id}: active test needs original actions")
        if not test.get("selected"):
            result.require(test.get("status") == "NOT RUN", f"{test_id}: unselected status must be NOT RUN")
        if test.get("lifecycle") == "REMOVED":
            result.require(test.get("selected") is False and test.get("status") == "NOT RUN", f"{test_id}: removed history must be unselected NOT RUN")
        if test.get("status") in ("NOT RUN", "BLOCKED", "NOT APPLICABLE"):
            result.require(bool(test.get("reason")), f"{test_id}: missing reason")
        incomplete |= test.get("selected") is True and test.get("status") == "NOT RUN"
        attempts = test.get("attempts")
        result.require(isinstance(attempts, list), f"{test_id}: attempts must be an array")
        if not isinstance(attempts, list):
            continue
        if not all(isinstance(attempt, dict) for attempt in attempts):
            result.errors.append(f"{test_id}: each attempt must be an object")
            continue
        result.require(test.get("status") == aggregate_attempts(attempts), f"{test_id}: final status disagrees with attempts (any FAIL wins)")
        for number, attempt in enumerate(attempts, 1):
            result.require(type(attempt.get("number")) is int and attempt.get("number") == number, f"{test_id}: attempt numbers must be consecutive from 1")
            result.require(attempt.get("status") in STATUSES[1:], f"{test_id}: attempt needs terminal status")
            result.require(iso_timestamp(attempt.get("observed_at")), f"{test_id}: invalid attempt observed_at")
            result.require(isinstance(attempt.get("observation"), str) and bool(attempt.get("observation")), f"{test_id}: attempt needs observation")
            evidence = attempt.get("evidence")
            result.require(isinstance(evidence, list) and all(isinstance(ref, str) for ref in evidence), f"{test_id}: evidence must be a string array")
            if not isinstance(evidence, list) or not all(isinstance(ref, str) for ref in evidence):
                evidence = []
            for ref in evidence:
                safe_evidence(path.parent, ref, result)
            captures = attempt.get("captures")
            result.require(isinstance(captures, list), f"{test_id}: captures must be an array")
            for capture in captures if isinstance(captures, list) else []:
                if not isinstance(capture, dict):
                    result.errors.append(f"{test_id}: capture must be an object")
                    continue
                ref = capture.get("path")
                result.require(isinstance(ref, str) and ref in evidence, f"{test_id}: capture path must also appear in attempt evidence")
                capture_file = safe_evidence(path.parent, ref, result) if isinstance(ref, str) else None
                digest = capture.get("sha256")
                result.require(isinstance(digest, str) and bool(SHA256.fullmatch(digest)), f"{test_id}: invalid capture sha256")
                if capture_file:
                    result.require(hashlib.sha256(capture_file.read_bytes()).hexdigest() == digest, f"{test_id}: screenshot content hash mismatch: {ref}")
                for key in ("url", "role", "locale", "state", "fixture"):
                    result.require(isinstance(capture.get(key), str) and bool(capture.get(key)), f"{test_id}: capture missing {key}")
                result.require(public_url(capture.get("url")), f"{test_id}: capture url must be credential-free HTTP(S)")
                viewport = capture.get("viewport")
                valid_viewport = isinstance(viewport, dict) and all(type(viewport.get(key)) is int and viewport[key] > 0 for key in ("width", "height")) and type(viewport.get("device_scale_factor")) in (int, float) and viewport["device_scale_factor"] > 0
                result.require(valid_viewport, f"{test_id}: invalid capture viewport")
                result.require(iso_timestamp(capture.get("captured_at")), f"{test_id}: invalid capture captured_at")
    result.require(data.get("run_completeness") == ("Incomplete" if incomplete else "Complete"), "run_completeness disagrees with selected NOT RUN tests")
    result.require(data["cleanup"].get("status") in ("Complete", "Incomplete", "Not needed"), "Invalid cleanup.status")
    result.require(isinstance(data["cleanup"].get("notes"), str), "cleanup.notes must be string")
    if incomplete or data["cleanup"].get("status") == "Incomplete":
        result.warn("Incomplete execution or cleanup: structurally valid metadata is not an automatically eligible comparison baseline")
    # The checkpoint is an index of the run, not an independent set of results.
    report_path = path.parent / "wp-update-report.md"
    report_text = prose(read_text(report_path, result))
    report_rows = index_rows(matrix(report_text, {"Test ID", "Status", "Actual observation", "Evidence reference"}, result), result)
    checkpoint_rows = {test["id"]: test for test in tests if isinstance(test, dict) and isinstance(test.get("id"), str)}
    result.require(set(report_rows) == set(checkpoint_rows), "Checkpoint/report test IDs differ")
    for test_id in report_rows.keys() & checkpoint_rows.keys():
        row, test = report_rows[test_id], checkpoint_rows[test_id]
        result.require(row.get("Status") == test.get("status"), f"{test_id}: checkpoint/report status differs")
        result.require(row.get("Lifecycle", "ACTIVE") == test.get("lifecycle"), f"{test_id}: checkpoint/report lifecycle differs")
        result.require(row.get("Selected for this run's scope?", "").startswith("Yes") == test.get("selected"), f"{test_id}: checkpoint/report selection differs")
    result.require(field_value(report_text, "Mode") == "before", "Checkpoint technical report must have Mode: before")
    result.require((field_value(report_text, "Run completeness") or "").split(" ", 1)[0] == data.get("run_completeness"), "Checkpoint/report completeness differs")
    state = reconcile_run_state(report_path, report_text, report_rows, result,
                                require_final=data.get("run_completeness") == "Complete")
    if state is not None:
        result.require(data["plan"].get("sha256") == state["plan"]["sha256"], "Checkpoint/run-state plan SHA256 differs")
        try:
            result.require(Path(data["plan"]["path"]).resolve() == Path(state["plan"]["path"]).resolve(), "Checkpoint/run-state plan path differs")
        except (TypeError, ValueError, OSError, KeyError) as exc:
            result.errors.append(f"Cannot compare checkpoint/run-state plan paths: {exc}")
    return result


def validate_plugin(root: Path) -> Result:
    result = Result()
    try:
        manifest = json.loads(read_text(root / ".claude-plugin/plugin.json", result))
        result.require(manifest.get("name") == "wp-checkpoint", "Plugin name must be wp-checkpoint")
        result.require(bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", str(manifest.get("version", "")))), "Invalid plugin version")
        result.require(isinstance(manifest.get("description"), str) and bool(manifest.get("description")), "Missing plugin description")
        marketplace = json.loads(read_text(root / ".claude-plugin/marketplace.json", result))
        result.require(any(item.get("name") == manifest.get("name") and item.get("source") == "." for item in marketplace.get("plugins", [])), "Marketplace must reference this plugin at source '.'")
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        result.errors.append(f"Malformed plugin/marketplace manifest: {exc}")
    skill_names = {"test", "test-plan-create"}
    skills_root = root / "skills"
    if skills_root.is_dir():
        skill_names.update(path.name for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())
    for name in sorted(skill_names):
        skill = root / "skills" / name / "SKILL.md"
        text = read_text(skill, result)
        front = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
        result.require(front is not None, f"{name}: missing YAML frontmatter")
        if front:
            # The plugin uses simple top-level scalar fields; no YAML dependency needed.
            fields = re.findall(r"^([a-z][a-z0-9-]*):\s*(.*)$", front.group(1), re.M)
            result.require(len(fields) == len(dict(fields)), f"{name}: duplicate frontmatter key")
            values = dict(fields)
            result.require(values.get("name", "").strip('"\'') == name, f"{name}: frontmatter name differs from directory")
            result.require(bool(values.get("description", "").strip()), f"{name}: missing description")
            result.require(values.get("disable-model-invocation") == "true", f"{name}: explicit invocation policy must be retained")
        skill_root = skill.parent
        # Markdown links are resolved exactly; code-form paths use skill-root convention.
        for resource in skill_root.rglob("*.md"):
            content = read_text(resource, result)
            for target in re.findall(r"\[[^\]]*\]\(([^\s)#]+)(?:#[^\s)]*)?\)", content):
                if urlsplit(target).scheme or target.startswith("#") or "<" in target:
                    continue
                result.require((resource.parent / unquote(target)).exists(), f"Broken local link in {resource.relative_to(root)}: {target}")
            for line in content.splitlines():
                for target in re.findall(r"`((?:references|assets)/[^`]+\.md)`", line):
                    candidates = [skill_root / target]
                    # Some cross-skill references explicitly name the owning folder in prose.
                    if "test-plan-create" in line:
                        candidates.append(root / "skills/test-plan-create" / target)
                    if re.search(r"\btest(?:`|\s|/)", line):
                        candidates.append(root / "skills/test" / target)
                    result.require(any(candidate.is_file() for candidate in candidates), f"Missing reference in {resource.relative_to(root)}: {target}")
    for shared in ("shared-conventions.md", "storage-preflight.md"):
        paths = [root / "skills" / name / "references" / shared for name in ("test", "test-plan-create")]
        result.require(all(path.is_file() for path in paths), f"Missing shared contract: {shared}")
        if all(path.is_file() for path in paths):
            result.require(paths[0].read_bytes() == paths[1].read_bytes(), f"Shared copies differ: {shared}")
    template = read_text(root / "skills/test-plan-create/assets/testing-after-update-template.md", result)
    vocabulary = section(template, "G")
    shared_text = read_text(root / "skills/test/references/shared-conventions.md", result)
    contract_start = re.search(r"^##\s+", shared_text, re.M)
    result.require(contract_start is not None, "Shared vocabulary has no embeddable contract section")
    if contract_start:
        contract = shared_text[contract_start.start():].strip()
        embedded_contract = re.sub(r"^(#{2,5}) ", r"#\1 ", contract, flags=re.M)
        result.require(embedded_contract in vocabulary, "Plan Section G embedded shared contract is out of sync")
    for token in (*STATUSES, "ACTIVE", "REMOVED", "Critical", "High", "Medium", "Low", "Confirmed regression", "Known issue", "New issue of uncertain origin", "Intermittent", "WordPress Administrator", "Developer", "Hosting Administrator"):
        result.require(token in vocabulary, f"Standalone plan vocabulary missing {token!r}")
    fallback = read_text(root / "skills/test/assets/report-template-fallback.md", result)
    report_shape = re.search(r"```(?:markdown|md)\s*\n(.*?)\n```", fallback, re.S)
    embedded_shape = re.search(r"```(?:markdown|md)\s*\n(.*?)\n```", section(template, "H"), re.S)
    result.require(report_shape is not None and embedded_shape is not None, "Both report templates need an embedded Markdown report shape")
    if report_shape and embedded_shape:
        result.require(report_shape.group(1).strip() == embedded_shape.group(1).strip(), "Plan Section H and fallback report shape are out of sync")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plugin = commands.add_parser("plugin", help="Check plugin packaging and shared contracts")
    plugin.add_argument("path", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    commands.add_parser("plan", help="Check generated plan structure").add_argument("path", type=Path)
    report = commands.add_parser("report", help="Check technical report matrix/counts/local evidence")
    report.add_argument("path", type=Path)
    report.add_argument("--plan", type=Path, help="Also require every ID in this plan exactly once")
    report.add_argument("--state", type=Path, help="Reconcile the same-bundle execution ledger; adjacent run-state.json is detected automatically")
    commands.add_parser("checkpoint", help="Check before baseline manifest and evidence").add_argument("path", type=Path)
    args = parser.parse_args(argv)
    functions = {"plugin": validate_plugin, "plan": validate_plan, "report": validate_report, "checkpoint": validate_checkpoint}
    result = functions[args.command](args.path, args.plan, args.state) if args.command == "report" else functions[args.command](args.path)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="backslashreplace")
    for note in result.notes:
        print(f"NOTE: {note}")
    for warning in result.warnings:
        print(f"WARNING: {warning}")
    for error in result.errors:
        print(f"ERROR: {error}")
    verdict = "FAIL" if result.errors else "STRUCTURAL OK" if args.command == "plan" else "OK"
    print(f"{args.command}: {verdict} ({len(result.errors)} errors, {len(result.warnings)} warnings)")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
