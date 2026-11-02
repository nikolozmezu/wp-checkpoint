#!/usr/bin/env python3
"""Durable local execution ledger. Never executes a test or repeats a browser action.

Use only after the skill's storage gate. Context is freshly supplied by the caller;
this script checks consistency, not the truth of site observations. Python 3.10+.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile

import select_tests as selector
import validate as v


class StateError(ValueError):
    pass


CONTEXT_KEYS = {"project_root", "wordpress_root", "site_url", "home_url", "blog_id", "environment_fingerprint", "observed_at"}
CLEANUP = {"Complete", "Incomplete", "Not needed"}
TERMINAL = {"PASS", "FAIL", "BLOCKED", "NOT APPLICABLE"}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise StateError(f"Cannot read JSON {path}: {exc}") from exc


def require(condition, message):
    if not condition:
        raise StateError(message)


def context_checked(context):
    require(isinstance(context, dict) and set(context) == CONTEXT_KEYS, "Context must contain exactly the documented non-secret fields")
    for key in ("project_root", "wordpress_root"):
        require(v.absolute_filesystem_path(context[key]), f"Context {key} must be an established absolute path")
    for key in ("site_url", "home_url"):
        require(v.public_url(context[key]), f"Context {key} must be a credential-free HTTP(S) URL")
    require(context["blog_id"] is None or type(context["blog_id"]) is int and context["blog_id"] > 0, "Context blog_id must be a positive integer or null")
    require(isinstance(context["environment_fingerprint"], str) and bool(v.SHA256.fullmatch(context["environment_fingerprint"])), "Context environment_fingerprint must be SHA256")
    require(v.iso_timestamp(context["observed_at"]), "Context observed_at needs an ISO timestamp with offset")
    return context


def context_identity(context):
    return {key: value for key, value in context.items() if key != "observed_at"}


def cleanup_checked(cleanup):
    require(isinstance(cleanup, dict) and cleanup.get("status") in CLEANUP, "cleanup.status must be Complete, Incomplete or Not needed")
    require(isinstance(cleanup.get("notes"), str) and bool(cleanup["notes"].strip()), "cleanup needs concrete notes")
    return {"status": cleanup["status"], "notes": cleanup["notes"].strip()}


def state_path(value):
    path = Path(value)
    if path.is_dir():
        path = path / "run-state.json"
    require(path.name == "run-state.json", "State must be named run-state.json inside its report bundle")
    require(not path.is_symlink(), "State path must not be a symlink")
    return path.resolve()


def evidence_checked(bundle, paths):
    require(isinstance(paths, list) and all(isinstance(path, str) for path in paths), "evidence must be an array of relative file paths")
    require(len(paths) == len(set(paths)), "Duplicate evidence paths")
    output = []
    for ref in paths:
        checked = v.Result()
        path = v.safe_evidence(bundle, ref, checked)
        require(not checked.errors, "; ".join(checked.errors))
        require(path.name not in {"run-state.json", ".run-state.lock"} and not path.name.startswith(".run-state-"), "Mutable ledger/lock is not test evidence")
        output.append({"path": path.relative_to(bundle.resolve()).as_posix(), "sha256": digest(path)})
    return output


def verify_evidence(bundle, state):
    for test in state["tests"]:
        for attempt in test["attempts"] + test.get("resolutions", []):
            evidence = attempt.get("evidence")
            require(isinstance(evidence, list), "Attempt evidence must be an array")
            for item in evidence:
                require(isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("sha256"), str), "Malformed evidence hash record")
                current = evidence_checked(bundle, [item["path"]])[0]
                require(current == item, f"Evidence changed since observation: {item['path']}")


def cleanup_review_checked(path, prior, prior_path):
    path = Path(path).resolve()
    review = read_json(path)
    require(isinstance(review, dict) and isinstance(review.get("observation"), str) and bool(review["observation"].strip()), "Cleanup review needs actual restoration/inspection notes")
    require(v.iso_timestamp(review.get("observed_at")), "Cleanup review needs an observation timestamp")
    require(review.get("source_run_id") == prior["run_id"] and review.get("source_state_sha256") == digest(prior_path), "Cleanup review must identify the exact immutable source run/state hash")
    reviewed_at = datetime.fromisoformat(review["observed_at"].replace("Z", "+00:00"))
    finalized_at = datetime.fromisoformat(prior["finished_at"].replace("Z", "+00:00"))
    require(reviewed_at >= finalized_at, "Cleanup review predates the finalized run; inspect current state again")
    cleanup = cleanup_checked(review.get("cleanup"))
    require(cleanup["status"] != "Incomplete", "Prior cleanup is still incomplete")
    pending = {test["id"] for test in prior["tests"] if test["cleanup"]["status"] == "Incomplete"}
    require(isinstance(review.get("resolved_ids"), list) and all(isinstance(key, str) for key in review["resolved_ids"]) and set(review["resolved_ids"]) == pending, "Cleanup review must cover exactly the prior unfinished cleanup IDs")
    return {"path": str(path), "sha256": digest(path), "evidence": evidence_checked(path.parent, review.get("evidence", []))}


def selection_checked(plan, selection):
    require(isinstance(selection, dict) and selection.get("schema_version") == 1, "Unsupported selection schema")
    for key in ("update_tags", "excluded_ids", "requested_ids"):
        require(isinstance(selection.get(key), list) and all(isinstance(item, str) for item in selection[key]), f"Selection {key} must be a string array")
    expected = selector.select(plan, selection.get("scope"), selection["update_tags"], selection["excluded_ids"], selection["requested_ids"])
    require(all(selection.get(key) == value for key, value in expected.items()), "Selection no longer matches the current plan or its deterministic rules")
    origin = selection.get("retest_of")
    if origin is not None:
        require(isinstance(origin, dict) and isinstance(origin.get("state_path"), str), "Invalid retest provenance")
        prior_path = state_path(origin["state_path"])
        prior = load(prior_path)
        require(digest(prior_path) == origin.get("sha256") and prior["run_id"] == origin.get("run_id"), "Retest source state changed; regenerate selection")
        require(prior["lifecycle"] == "COMPLETE", "Retest source must be finalized; use resume for an interrupted run")
        require(set(selection["requested_ids"]) <= {test["id"] for test in prior["tests"]}, "Retest IDs must exist in prior history")
        if any(test["cleanup"]["status"] == "Incomplete" for test in prior["tests"]):
            review = origin.get("cleanup_review")
            require(isinstance(review, dict) and isinstance(review.get("path"), str), "Retest requires a saved review of prior cleanup")
            require(cleanup_review_checked(review["path"], prior, prior_path) == review, "Prior cleanup review or its evidence changed; regenerate selection")
        expected["retest_of"] = origin
    return expected


def load(path):
    path = state_path(path)
    state = read_json(path)
    require(isinstance(state, dict) and state.get("state_schema_version") == 1, "Unsupported run-state schema")
    require(state.get("run_id") == path.parent.name, "State run_id does not match report bundle")
    require(state.get("mode") in {"normal", "before", "after"}, "Invalid run mode")
    require(state.get("lifecycle") in {"OPEN", "COMPLETE"}, "Invalid state lifecycle")
    require(v.iso_timestamp(state.get("created_at")) and v.iso_timestamp(state.get("updated_at")), "State timestamps need ISO offsets")
    context_checked(state.get("context"))
    require(isinstance(state.get("plan"), dict) and isinstance(state["plan"].get("path"), str) and bool(v.SHA256.fullmatch(str(state["plan"].get("sha256", "")))), "Malformed saved plan identity")
    require(isinstance(state.get("selection"), dict) and isinstance(state["selection"].get("tests"), list) and isinstance(state["selection"].get("order"), list), "Missing selection")
    tests = state.get("tests")
    require(isinstance(tests, list) and tests, "State tests must be nonempty")
    expected = {test.get("id"): test for test in state["selection"]["tests"] if isinstance(test, dict)}
    seen = set()
    in_flight = 0
    for test in tests:
        require(isinstance(test, dict), "Malformed test state")
        key = test.get("id")
        require(isinstance(key, str) and key in expected and key not in seen, "Duplicate/unknown state test ID")
        seen.add(key)
        require(all(test.get(field) == value for field, value in expected[key].items()), f"{key}: selection metadata changed inside state")
        require(test.get("phase") in {"unselected", "pending", "running", "assessed"}, f"{key}: invalid phase")
        require(test.get("status") in v.STATUSES, f"{key}: invalid status")
        require(isinstance(test.get("result_reason"), str) and isinstance(test.get("attempts"), list), f"{key}: invalid result record")
        cleanup_checked(test.get("cleanup"))
        if not test["selected"]:
            require(test["phase"] == "unselected" and test["status"] == "NOT RUN" and not test["attempts"] and test.get("in_flight") is None, f"{key}: unselected test has execution history")
        for number, attempt in enumerate(test["attempts"], 1):
            require(isinstance(attempt, dict) and attempt.get("number") == number and attempt.get("status") in TERMINAL | {"INTERRUPTED"}, f"{key}: invalid attempt sequence")
            require(isinstance(attempt.get("observation"), str) and bool(attempt["observation"].strip()) and v.iso_timestamp(attempt.get("observed_at")), f"{key}: invalid attempt observation")
        valid = [attempt for attempt in test["attempts"] if attempt["status"] in TERMINAL]
        aggregate = "FAIL" if any(attempt["status"] == "FAIL" for attempt in valid) else valid[-1]["status"] if valid else "NOT RUN"
        require(test["status"] == aggregate, f"{key}: status differs from retained attempts (any FAIL wins)")
        if test["phase"] == "assessed":
            require(test["status"] in TERMINAL and test.get("in_flight") is None, f"{key}: assessed state needs a terminal result")
        action = test.get("in_flight")
        if action is not None:
            require(test["phase"] == "running" and isinstance(action, dict) and isinstance(action.get("action"), str) and action["action"].strip() and type(action.get("mutates")) is bool and v.iso_timestamp(action.get("started_at")), f"{key}: malformed in-flight action")
            in_flight += 1
        else:
            require(test["phase"] != "running", f"{key}: running state lost its action journal")
    require(seen == set(expected), "State/selection IDs differ")
    require(in_flight <= 1, "Multiple actions in flight; independent concurrent runs need separate bundles")
    if state["lifecycle"] == "COMPLETE":
        require(v.iso_timestamp(state.get("finished_at")), "Finalized state needs finished_at")
        require(all(not test["selected"] or test["phase"] == "assessed" for test in tests), "Finalized state contains unfinished work")
    verify_evidence(path.parent, state)
    return state


def verify_current(state, plan, context):
    context_checked(context)
    require(Path(plan).resolve() == Path(state["plan"]["path"]).resolve() and digest(plan) == state["plan"]["sha256"], "Plan changed; refresh/review and start a new run instead of resuming")
    require(context_identity(context) == context_identity(state["context"]), "Environment/context changed; review drift and start a new run")
    selection_checked(plan, state["selection"])


@contextmanager
def locked(path):
    lock = path.parent / ".run-state.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise StateError("Another state writer or an interrupted lock exists; inspect it before any further mutation") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(now())
        yield
    finally:
        lock.unlink()


def save(path, state):
    state["updated_at"] = now()
    fd, temp_name = tempfile.mkstemp(prefix=".run-state-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(state, handle, ensure_ascii=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if Path(temp_name).exists():
            Path(temp_name).unlink()


def init(bundle, plan, context, selection, mode="normal"):
    bundle = Path(bundle).resolve()
    require(bundle.is_dir(), "Create and storage-gate the report bundle before initializing state")
    path = state_path(bundle / "run-state.json")
    context_checked(context)
    selection = selection_checked(plan, selection)
    if selection.get("retest_of"):
        prior = load(selection["retest_of"]["state_path"])
        identity_keys = ("project_root", "wordpress_root", "site_url", "home_url", "blog_id")
        require(all(context[key] == prior["context"][key] for key in identity_keys), "Retest project/site identity differs from prior run; establish an explicit relocation mapping outside this helper or start an unrelated normal run")
    require(mode in {"normal", "before", "after"}, "Invalid run mode")
    with locked(path):
        require(not path.exists(), "Never overwrite an existing run-state; resume it or use a fresh bundle")
        require(not (bundle / "checkpoint.json").exists(), "Initialize state before writing a new checkpoint; never attach it to a prior baseline")
        tests = [{**test, "phase": "pending" if test["selected"] else "unselected", "status": "NOT RUN",
                  "result_reason": test["reason"], "attempts": [], "in_flight": None,
                  "cleanup": {"status": "Not needed", "notes": "No actions have started"}} for test in selection["tests"]]
        state = {"state_schema_version": 1, "run_id": bundle.name, "mode": mode, "lifecycle": "OPEN", "created_at": now(),
                 "plan": selection["plan"], "context": context, "selection": selection, "tests": tests}
        save(path, state)
    return state


def find_test(state, test_id):
    test = next((test for test in state["tests"] if test["id"] == test_id), None)
    require(test is not None and test["selected"], "Test ID is unknown or unselected")
    return test


def mutation(path, plan, context, callback):
    path = state_path(path)
    with locked(path):
        state = load(path)
        verify_current(state, plan, context)
        require(state["lifecycle"] == "OPEN", "Completed run is immutable; create a fresh retest run")
        checkpoint = path.parent / "checkpoint.json"
        if checkpoint.exists():
            require(read_json(checkpoint).get("run_completeness") != "Complete", "Completed checkpoint is immutable; do not resume or extend its run")
        callback(state, path.parent)
        state["context"]["observed_at"] = context["observed_at"]
        save(path, state)
    return state


def start(path, plan, context, test_id, action, mutates=True, retry=False, prerequisite_review=None):
    require(isinstance(action, str) and bool(action.strip()), "Record the specific action before execution")
    require(type(mutates) is bool and type(retry) is bool, "mutates/retry must be boolean")
    def apply(state, bundle):
        test = find_test(state, test_id)
        require(not any(item["in_flight"] for item in state["tests"]), "An action is in flight; inspect and record/resolve it instead of repeating it")
        require(not any(item["cleanup"]["status"] == "Incomplete" for item in state["tests"]), "Unfinished cleanup must be reviewed/resolved before another action")
        require(test["phase"] == "pending" or retry and test["phase"] == "assessed", "Use an explicit retry for an assessed check")
        by_id = {item["id"]: item for item in state["tests"]}
        missing = set(test["blocked_by"]) | {dep for dep in test["depends_on"] if by_id[dep]["phase"] != "assessed" or by_id[dep]["status"] != "PASS"}
        review = None
        if missing:
            require(isinstance(prerequisite_review, dict), "Prerequisites unavailable; record BLOCKED or supply a current equivalent-fixture review")
            require(set(prerequisite_review) == {"ids", "observed_at", "observation"}, "Prerequisite review requires ids, observed_at and observation only")
            require(isinstance(prerequisite_review["ids"], list) and all(isinstance(key, str) for key in prerequisite_review["ids"]) and set(prerequisite_review["ids"]) == missing, "Prerequisite review must identify every unavailable prerequisite")
            require(v.iso_timestamp(prerequisite_review["observed_at"]) and isinstance(prerequisite_review["observation"], str) and bool(prerequisite_review["observation"].strip()), "Prerequisite review needs a dated actual equivalent-fixture observation")
            review = prerequisite_review
        else:
            require(prerequisite_review is None, "No unavailable prerequisite needs an override")
        test["phase"] = "running"
        test["in_flight"] = {"action": action.strip(), "mutates": mutates, "started_at": now()}
        if review is not None:
            test["in_flight"]["prerequisite_review"] = review
        if mutates:
            test["cleanup"] = {"status": "Incomplete", "notes": "Action started; resulting state and cleanup not yet recorded"}
    return mutation(path, plan, context, apply)


def record(path, plan, context, test_id, result):
    require(isinstance(result, dict) and result.get("status") in TERMINAL, "Result needs a terminal status")
    require(isinstance(result.get("observation"), str) and bool(result["observation"].strip()), "Result needs an actual observation")
    reason = result.get("reason", "")
    require(isinstance(reason, str) and (result["status"] not in {"BLOCKED", "NOT APPLICABLE"} or reason.strip()), "BLOCKED/NOT APPLICABLE needs a reason")
    cleanup = cleanup_checked(result.get("cleanup"))
    def apply(state, bundle):
        test = find_test(state, test_id)
        require(test["phase"] == "running" or test["phase"] == "pending" and result["status"] in {"BLOCKED", "NOT APPLICABLE"}, "An executed result requires its prior start journal; only non-executed assessments may skip start")
        require(not any(item["in_flight"] for item in state["tests"] if item is not test), "Finish the other in-flight check first")
        attempt = {"number": len(test["attempts"]) + 1, "status": result["status"], "observed_at": now(),
                   "observation": result["observation"].strip(), "reason": reason,
                   "action": test["in_flight"], "evidence": evidence_checked(bundle, result.get("evidence", [])), "cleanup": cleanup}
        test["attempts"].append(attempt)
        test["status"] = "FAIL" if any(item["status"] == "FAIL" for item in test["attempts"]) else result["status"]
        test["phase"], test["in_flight"], test["cleanup"], test["result_reason"] = "assessed", None, cleanup, reason
    return mutation(path, plan, context, apply)


def resolve(path, plan, context, test_id, resolution):
    require(isinstance(resolution, dict) and isinstance(resolution.get("observation"), str) and bool(resolution["observation"].strip()), "Resolution needs current-state inspection notes")
    require(type(resolution.get("retry_safe")) is bool, "Resolution must explicitly state retry_safe")
    cleanup = cleanup_checked(resolution.get("cleanup"))
    require(not resolution["retry_safe"] or cleanup["status"] != "Incomplete", "Cannot authorize retry with unfinished cleanup")
    def apply(state, bundle):
        test = find_test(state, test_id)
        require(test["in_flight"] is not None or test["cleanup"]["status"] == "Incomplete", "Nothing interrupted or awaiting cleanup to resolve")
        evidence = evidence_checked(bundle, resolution.get("evidence", []))
        was_running = test["in_flight"] is not None
        if was_running:
            test["attempts"].append({"number": len(test["attempts"]) + 1, "status": "INTERRUPTED", "observed_at": now(),
                                     "observation": resolution["observation"].strip(), "action": test["in_flight"], "evidence": evidence, "cleanup": cleanup})
            test["in_flight"] = None
        test.setdefault("resolutions", []).append({"observed_at": now(), **resolution, "evidence": evidence, "cleanup": cleanup})
        test["cleanup"] = cleanup
        if was_running and resolution["retry_safe"]:
            test["phase"] = "pending"
        elif was_running:
            test["attempts"].append({"number": len(test["attempts"]) + 1, "status": "BLOCKED", "observed_at": now(),
                                     "observation": resolution["observation"].strip(), "reason": "Interrupted action cannot safely be repeated",
                                     "action": None, "evidence": evidence, "cleanup": cleanup})
            test["phase"] = "assessed"
        valid = [attempt for attempt in test["attempts"] if attempt["status"] in TERMINAL]
        test["status"] = "FAIL" if any(item["status"] == "FAIL" for item in valid) else valid[-1]["status"] if valid else "NOT RUN"
        test["result_reason"] = resolution["observation"].strip()
    return mutation(path, plan, context, apply)


def resume(path, plan, context):
    path = state_path(path)
    state = load(path)
    verify_current(state, plan, context)
    pending_cleanup = [test["id"] for test in state["tests"] if test["cleanup"]["status"] == "Incomplete"]
    interrupted = [test["id"] for test in state["tests"] if test["in_flight"]]
    pending = {test["id"] for test in state["tests"] if test["selected"] and test["phase"] == "pending"}
    by_id = {test["id"]: test for test in state["tests"]}
    runnable = []
    blocked = {}
    for key in state["selection"]["order"]:
        if key not in pending:
            continue
        test = by_id[key]
        blockers = list(test["blocked_by"])
        blockers += [dep for dep in test["depends_on"] if by_id[dep]["phase"] != "assessed" or by_id[dep]["status"] != "PASS"]
        if blockers:
            blocked[key] = sorted(set(blockers))
        elif not interrupted and not pending_cleanup:
            runnable.append(key)
    return {"state_path": str(path), "lifecycle": state["lifecycle"], "mode": state["mode"],
            "completed": [test["id"] for test in state["tests"] if test["selected"] and test["phase"] == "assessed"],
            "pending": [key for key in state["selection"]["order"] if key in pending], "interrupted": interrupted,
            "pending_cleanup": pending_cleanup, "blocked_prerequisites": blocked, "runnable_now": runnable,
            "note": "Completed entries are earlier observations, not new passes. No action was executed or repeated."}


def finish(path, plan, context):
    def apply(state, bundle):
        require(all(not test["selected"] or test["phase"] == "assessed" for test in state["tests"]), "Cannot finalize while selected checks are pending or in flight")
        state["lifecycle"], state["finished_at"] = "COMPLETE", now()
    return mutation(path, plan, context, apply)


def retest_selection(path, plan, requested_ids=(), exclusions=(), cleanup_review=None):
    path = state_path(path)
    prior = load(path)
    require(prior["lifecycle"] == "COMPLETE", "Finalize the prior run before retesting; use resume for interrupted work")
    review = None
    if any(test["cleanup"]["status"] == "Incomplete" for test in prior["tests"]):
        require(cleanup_review is not None, "Prior cleanup is unfinished; save a current cleanup review before planning a new retest")
        review = cleanup_review_checked(cleanup_review, prior, path)
    known = {test["id"] for test in prior["tests"]}
    requested = set(selector.split_values(requested_ids))
    require(requested <= known, "Explicit retest IDs must exist in prior history")
    if not requested:
        requested = {test["id"] for test in prior["tests"] if test["selected"] and test["status"] in {"FAIL", "BLOCKED"}}
    require(bool(requested), "No failed/blocked checks to retest; supply explicit prior IDs if needed")
    selected = selector.select(Path(plan), "targeted", (), exclusions, requested)
    selected["retest_of"] = {"state_path": str(path), "sha256": digest(path), "run_id": prior["run_id"]}
    if review is not None:
        selected["retest_of"]["cleanup_review"] = review
    return selected


def summary(path, state, test_id=None):
    selected = [test for test in state["tests"] if test["selected"]]
    result = {"state_path": str(state_path(path)), "run_id": state["run_id"], "mode": state["mode"], "lifecycle": state["lifecycle"],
              "selected_count": len(selected), "counts": {status: sum(test["status"] == status for test in selected) for status in v.STATUSES},
              "in_flight": [test["id"] for test in selected if test["in_flight"]],
              "pending_cleanup": [test["id"] for test in selected if test["cleanup"]["status"] == "Incomplete"]}
    if test_id is not None:
        test = find_test(state, test_id)
        result["test"] = {key: test[key] for key in ("id", "phase", "status", "result_reason")}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    initial = commands.add_parser("init")
    initial.add_argument("--bundle", type=Path, required=True)
    initial.add_argument("--selection", type=Path, required=True)
    initial.add_argument("--mode", choices=("normal", "before", "after"), default="normal")
    current = [initial]
    for name in ("start", "record", "resolve", "resume", "finish"):
        command = commands.add_parser(name)
        command.add_argument("state", type=Path)
        current.append(command)
        if name in {"start", "record", "resolve"}:
            command.add_argument("--id", required=True)
        if name == "start":
            command.add_argument("--action", required=True)
            command.add_argument("--read-only", action="store_true")
            command.add_argument("--retry", action="store_true")
            command.add_argument("--prerequisite-review", type=Path, help="Dated observed equivalent fixture for unavailable prerequisite IDs; never recreates a fixture automatically")
        elif name in {"record", "resolve"}:
            command.add_argument("--input", type=Path, required=True)
    for command in current:
        command.add_argument("--plan", type=Path, required=True)
        command.add_argument("--context", type=Path, required=True)
    retest = commands.add_parser("retest")
    retest.add_argument("state", type=Path)
    retest.add_argument("--plan", type=Path, required=True)
    retest.add_argument("--ids", action="append", default=[])
    retest.add_argument("--exclude", action="append", default=[])
    retest.add_argument("--cleanup-review", type=Path, help="Fresh restoration evidence when finalized prior history records unfinished cleanup")
    args = parser.parse_args(argv)
    try:
        context = read_json(args.context) if hasattr(args, "context") else None
        if args.command == "init":
            result = init(args.bundle, args.plan, context, read_json(args.selection), args.mode)
        elif args.command == "start":
            result = start(args.state, args.plan, context, args.id, args.action, not args.read_only, args.retry, read_json(args.prerequisite_review) if args.prerequisite_review else None)
        elif args.command in {"record", "resolve"}:
            result = globals()[args.command](args.state, args.plan, context, args.id, read_json(args.input))
        elif args.command in {"resume", "finish"}:
            result = globals()[args.command](args.state, args.plan, context)
        else:
            result = retest_selection(args.state, args.plan, args.ids, args.exclude, args.cleanup_review)
        if args.command not in {"resume", "retest"}:
            result = summary(args.bundle if args.command == "init" else args.state, result, getattr(args, "id", None))
    except (StateError, selector.SelectionError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
