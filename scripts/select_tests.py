#!/usr/bin/env python3
"""Select plan tests deterministically; read-only, Python 3.10+, no dependencies."""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
from pathlib import Path
import re
import sys

import validate as v


class SelectionError(ValueError):
    pass


def split_values(values):
    return sorted({part.strip() for value in values for part in value.split(",") if part.strip()})


def select(plan: Path, scope="full", update_tags=(), exclusions=(), requested_ids=()):
    plan = Path(plan).resolve()
    checked = v.validate_plan(plan)
    if checked.errors:
        raise SelectionError("Invalid plan: " + "; ".join(checked.errors))
    rows, cards = v.plan_data(plan, v.Result())
    all_ids = set(rows)
    active = {key for key, row in rows.items() if row.get("Lifecycle", "ACTIVE") == "ACTIVE"}
    tags = set(split_values(update_tags))
    excluded = set(split_values(exclusions))
    requested = set(split_values(requested_ids))
    if scope not in {"full", "smoke", "targeted"}:
        raise SelectionError("scope must be full, smoke or targeted")
    if any(not re.fullmatch(r"core|theme|builder|php|env|plugin:[a-z0-9][a-z0-9._-]*", tag) for tag in tags):
        raise SelectionError("Invalid update tag")
    if (excluded | requested) - all_ids:
        raise SelectionError("Unknown IDs: " + ", ".join(sorted((excluded | requested) - all_ids)))
    if requested - active:
        raise SelectionError("Requested IDs are removed: " + ", ".join(sorted(requested - active)))
    if requested and requested & excluded:
        raise SelectionError("An explicitly requested ID is also excluded")
    if scope == "targeted" and not tags and not requested:
        raise SelectionError("targeted needs update tags or explicit IDs; unknown impact requires full")
    if requested:
        scope = "targeted"
    allowed = active - excluded
    depends = {key: v.ids(v.field_value(cards[key], "Depends on") or "") for key in active}
    downstream = {key: v.ids(v.field_value(cards[key], "Affects") or "") & active for key in active}
    for consumer, requirements in depends.items():
        for producer in requirements:
            downstream[producer].add(consumer)
    warnings = list(checked.warnings)

    def closure(seeds, graph, universe=None):
        universe = allowed if universe is None else universe
        found = set(seeds) & universe
        todo = list(found)
        while todo:
            for target in graph[todo.pop()]:
                if target in universe and target not in found:
                    found.add(target)
                    todo.append(target)
        return found

    smoke = {key for key in allowed if rows[key].get("Smoke?") == "Y"}
    smoke_closure = closure(smoke, depends)
    direct = set()
    direct_reason = {}
    impacted = set()
    if requested:
        direct = requested
        direct_reason = {key: "Explicitly requested for a fresh check" for key in requested}
        selected = closure(direct, depends)
    elif scope == "full":
        selected = allowed
    elif scope == "smoke":
        selected = smoke_closure
    else:
        for key in active:
            card_tags = v.tags(rows[key]["Update-type tags"])
            layers = v.tags(v.field_value(cards[key], "Execution layers") or "")
            reasons = []
            if card_tags & tags:
                reasons.append("Update tags: " + ", ".join(sorted(card_tags & tags)))
            if "php" in tags and (not layers or {"php", "unknown"} & layers):
                reasons.append("PHP execution or unresolved runtime layer")
            if "env" in tags:
                # No narrower infrastructure change is supplied to this command.
                # A known static-file check can also validate affected storage/config.
                reasons.append("Environment change: conservative full impact until narrower scope is established")
            if reasons:
                direct.add(key)
                direct_reason[key] = "; ".join(reasons)
        if "php" in tags and any(not v.field_value(cards[key], "Execution layers") for key in allowed):
            warnings.append("Legacy cards without execution layers are conservatively included for PHP; refresh the plan")
        if "env" in tags:
            warnings.append("Unqualified env impact includes all active non-excluded checks; use explicit IDs only after documented impact review")
        # Excluding a check's execution does not break real impact propagation.
        impacted = closure(direct, downstream, active) & allowed
        selected = closure(impacted, depends) | smoke_closure

    blocked = {key: depends[key] - selected for key in selected}
    changed = True
    while changed:
        changed = False
        for key in selected:
            inherited = set().union(*(blocked.get(dep, set()) for dep in depends[key]))
            if not inherited <= blocked[key]:
                blocked[key] |= inherited
                changed = True

    # Stable topological order, prioritizing smoke and its prerequisite chain.
    degree = {key: len(depends[key] & selected) for key in selected}
    followers = {key: set() for key in selected}
    for key in selected:
        for dep in depends[key] & selected:
            followers[dep].add(key)
    rank = {key: index for index, key in enumerate(rows)}
    ready = [(key not in smoke_closure, rank[key], key) for key in selected if degree[key] == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        _, _, key = heapq.heappop(ready)
        order.append(key)
        for following in followers[key]:
            degree[following] -= 1
            if degree[following] == 0:
                heapq.heappush(ready, (following not in smoke_closure, rank[following], following))
    if len(order) != len(selected):
        raise SelectionError("Circular selected prerequisites")

    tests = []
    for key, row in rows.items():
        lifecycle = row.get("Lifecycle", "ACTIVE")
        if lifecycle == "REMOVED":
            category, reason = "No", "Removed: " + (v.field_value(cards[key], "Removal date / reason") or "recorded plan history")
        elif key in excluded:
            category, reason = "No", "Explicit user exclusion"
        elif key not in selected:
            category, reason = "No", "Outside selected scope"
        elif requested:
            category = "Yes/targeted-tagged" if key in direct else "Yes/targeted-dependency"
            reason = direct_reason.get(key, "Prerequisite of explicitly requested checks")
        elif scope == "full":
            category, reason = ("Yes/smoke", "Essential smoke check") if key in smoke else ("Yes/full", "Full active coverage")
        elif scope == "smoke":
            category, reason = ("Yes/smoke", "Essential smoke check") if key in smoke else ("Yes/smoke-dependency", "Prerequisite of essential smoke")
        elif key in direct:
            category, reason = "Yes/targeted-tagged", direct_reason[key]
        elif key in impacted or key not in smoke_closure:
            category, reason = "Yes/targeted-dependency", "Downstream update impact or its prerequisite"
        elif key in smoke:
            category, reason = "Yes/smoke", "Essential smoke check"
        else:
            category, reason = "Yes/smoke-dependency", "Prerequisite of essential smoke"
        tests.append({"id": key, "lifecycle": lifecycle, "selected": key in selected,
                      "category": category, "reason": reason,
                      "depends_on": sorted(depends.get(key, set())), "blocked_by": sorted(blocked.get(key, set()))})
    return {"schema_version": 1, "plan": {"path": str(plan), "sha256": hashlib.sha256(plan.read_bytes()).hexdigest()},
            "scope": scope, "update_tags": sorted(tags), "excluded_ids": sorted(excluded), "requested_ids": sorted(requested),
            "order": order, "tests": tests, "warnings": list(dict.fromkeys(warnings))}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--scope", choices=("full", "smoke", "targeted"), default="full")
    parser.add_argument("--tag", action="append", default=[])
    parser.add_argument("--exclude", action="append", default=[])
    parser.add_argument("--ids", action="append", default=[], help="Explicit fresh checks plus prerequisites; does not add smoke or downstream checks")
    args = parser.parse_args(argv)
    try:
        result = select(args.plan, args.scope, args.tag, args.exclude, args.ids)
    except (SelectionError, OSError, UnicodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
