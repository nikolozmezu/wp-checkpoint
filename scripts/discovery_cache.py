#!/usr/bin/env python3
"""Fingerprint explicitly reviewed discovery inputs; never cache test success.

The caller must pass the plugin's storage gate before capture. This helper cannot
prove that a directory is non-public or that a source was actually reviewed.
Python 3.10+, standard library only. check never writes; capture is explicit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
import sys
import tempfile
from urllib.parse import urlsplit

from validate import TEST_ID, field_value, prose, section

SCHEMA = 1
KIND = "wp-checkpoint-discovery-cache"
MAX_FILES = 10000
MAX_BYTES = 16 * 1024 * 1024
CATEGORIES = {"source", "configuration", "activation", "inventory", "runtime"}
SECRET_NAMES = {"wp-config.php", "auth.json", "credentials", "credentials.json", "id_rsa", "id_ed25519", ".npmrc", ".pypirc"}
SECRET_SUFFIXES = {".pem", ".key", ".pfx", ".p12", ".sql", ".sqlite", ".sqlite3", ".db"}
SECRET_DIRS = {".git", ".ssh", ".aws", ".claude", ".codex"}


class CacheError(ValueError):
    pass


def is_link(path: Path) -> bool:
    """A Windows junction can escape os.walk even with followlinks=False."""
    if path.is_symlink():
        return True
    if hasattr(path, "is_junction") and path.is_junction():
        return True
    try:
        return getattr(path.lstat(), "st_reparse_tag", None) == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    except FileNotFoundError:
        return False


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CacheError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CacheError(f"Expected JSON object: {path}")
    return data


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(path: Path) -> str:
    if path.stat().st_size > MAX_BYTES:
        raise CacheError(f"Input exceeds {MAX_BYTES} bytes: {path.name}")
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def relative_name(value: object, *, allow_dot: bool = False) -> str:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise CacheError("Evidence paths must be nonempty relative paths using '/'")
    posix = PurePosixPath(value)
    if posix.is_absolute() or PureWindowsPath(value).drive or ".." in posix.parts or ":" in value:
        raise CacheError(f"Path must stay within the declared project root: {value}")
    normalized = posix.as_posix()
    if normalized == "." and not allow_dot:
        raise CacheError("Expected a file/directory path, not '.'")
    return normalized


def reject_secret(value: str) -> None:
    parts = PurePosixPath(value).parts
    name = parts[-1].lower() if parts else ""
    if (any(part.lower() in SECRET_DIRS for part in parts)
            or name in SECRET_NAMES or name == ".env" or name.startswith(".env.")
            or PurePosixPath(name).suffix in SECRET_SUFFIXES):
        raise CacheError(f"Secret-bearing input is not eligible for the discovery cache: {value}")


def safe_path(root: Path, value: object, *, allow_dot: bool = False) -> tuple[str, Path]:
    name = relative_name(value, allow_dot=allow_dot)
    reject_secret(name)
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        if is_link(current):
            raise CacheError(f"Symlink/junction evidence is not supported: {name}")
    if not current.resolve().is_relative_to(root):
        raise CacheError(f"Evidence path escapes project root: {name}")
    return name, current


def timestamp(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).utcoffset() is not None
    except ValueError:
        return False


def test_ids(value: object, allowed: set[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not TEST_ID.fullmatch(item) for item in value):
        raise CacheError("test_ids must be an array of real test IDs")
    if set(value) - allowed:
        raise CacheError(f"Evidence references IDs absent from the plan: {sorted(set(value) - allowed)}")
    return sorted(set(value))


def context_value(value: object) -> dict:
    if not isinstance(value, dict) or not value:
        raise CacheError("Manifest context must be a nonempty object")
    allowed = {"environment_id", "site_url", "home_url", "blog_id"}
    if set(value) - allowed:
        raise CacheError("Context accepts only environment_id, site_url, home_url and blog_id; never credentials")
    if not isinstance(value.get("environment_id"), str) or not value["environment_id"].strip():
        raise CacheError("context.environment_id is required")
    for key in ("site_url", "home_url"):
        item = value.get(key)
        if item is not None:
            if not isinstance(item, str):
                raise CacheError(f"context.{key} must be a URL or null")
            parsed = urlsplit(item)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
                raise CacheError(f"context.{key} must be a credential-free HTTP(S) URL without query/fragment")
    blog_id = value.get("blog_id")
    if blog_id is not None and (type(blog_id) is not int or blog_id < 1):
        raise CacheError("context.blog_id must be positive integer or null")
    return value


def plugin_version() -> str:
    manifest = read_json(Path(__file__).resolve().parents[1] / ".claude-plugin/plugin.json")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise CacheError("Plugin manifest has no version")
    return version


def build_snapshot(root: Path, plan: Path, manifest_path: Path) -> dict:
    if is_link(root) or not root.is_dir():
        raise CacheError("Project root must be an existing non-symlink directory")
    root = root.resolve()
    if is_link(plan) or not plan.is_file() or plan.suffix.lower() != ".md":
        raise CacheError("Plan must be an existing Markdown file, not a symlink")
    plan = plan.resolve()
    plan_text = prose(plan.read_text(encoding="utf-8-sig"))
    catalogue = section(plan_text, "F")
    headings = list(re.finditer(r"^####\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3})\b", catalogue, re.M))
    allowed_ids = set()
    for index, heading in enumerate(headings):
        body = catalogue[heading.end():headings[index + 1].start() if index + 1 < len(headings) else len(catalogue)]
        if field_value(body, "Lifecycle") != "REMOVED":
            allowed_ids.add(heading.group(1))
    if not allowed_ids:
        raise CacheError("Plan has no active Section F test cards to index; validate the plan first")
    manifest = read_json(manifest_path)
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != SCHEMA:
        raise CacheError("Unsupported input manifest schema_version")
    context = context_value(manifest.get("context"))
    sources = manifest.get("sources")
    watches = manifest.get("watches", [])
    if not isinstance(sources, list) or not isinstance(watches, list):
        raise CacheError("Manifest sources and watches must be arrays")
    if not sources and not watches:
        raise CacheError("Discovery index needs at least one explicitly reviewed source or scoped watch")
    records: dict[str, dict] = {}
    for source in sources:
        if not isinstance(source, dict):
            raise CacheError("Each source must be an object")
        name, path = safe_path(root, source.get("path"))
        if name in records:
            raise CacheError(f"Duplicate source path: {name}")
        category, source_kind = source.get("category"), source.get("kind")
        if category not in CATEGORIES or source_kind not in {"static", "volatile"}:
            raise CacheError(f"Invalid category/kind for {name}")
        if not timestamp(source.get("captured_at")) or not isinstance(source.get("provenance"), str) or not source["provenance"].strip():
            raise CacheError(f"Source requires provenance and offset-bearing captured_at: {name}")
        if path.exists() and not path.is_file():
            raise CacheError(f"Source is not a regular file: {name}")
        exists = path.is_file()
        records[name] = {
            "sha256": digest(path) if exists else None,
            "test_ids": test_ids(source.get("test_ids"), allowed_ids),
            "kind": "volatile" if category != "source" else source_kind,
            "category": category,
            "provenance": source["provenance"],
            "captured_at": source["captured_at"],
        }
    watch_records = []
    watch_keys = set()
    count = 0
    for watch in watches:
        if not isinstance(watch, dict):
            raise CacheError("Each watch must be an object")
        name, directory = safe_path(root, watch.get("path"), allow_dot=True)
        patterns = watch.get("patterns")
        if not isinstance(patterns, list) or not patterns or any(not isinstance(item, str) or not item or "\\" in item or item.startswith("/") or ".." in PurePosixPath(item).parts or ":" in item for item in patterns):
            raise CacheError(f"Invalid watch patterns for {name}")
        patterns = sorted(set(patterns))
        key = canonical([name, patterns])
        if key in watch_keys:
            raise CacheError(f"Duplicate watch: {name}")
        watch_keys.add(key)
        members = {}
        if directory.exists() and not directory.is_dir():
            raise CacheError(f"Watch is not a directory: {name}")
        if directory.is_dir():
            for current, dirs, files in os.walk(directory, followlinks=False):
                for item in dirs + files:
                    candidate = Path(current) / item
                    if is_link(candidate):
                        raise CacheError(f"Symlink/junction under watched directory: {candidate.relative_to(root).as_posix()}")
                # Metadata/credential directories are excluded without traversing or hashing.
                dirs[:] = [item for item in dirs if item.lower() not in SECRET_DIRS]
                for item in files:
                    candidate = Path(current) / item
                    relative = candidate.relative_to(directory).as_posix()
                    if not any(fnmatch.fnmatchcase(relative, pattern) or pattern.startswith("**/") and fnmatch.fnmatchcase(relative, pattern[3:]) for pattern in patterns):
                        continue
                    member_name, member = safe_path(root, candidate.relative_to(root).as_posix())
                    count += 1
                    if count > MAX_FILES:
                        raise CacheError(f"Watch scope exceeds {MAX_FILES} matching files; narrow it")
                    members[member_name] = digest(member)
        watch_records.append({"path": name, "patterns": patterns, "test_ids": test_ids(watch.get("test_ids"), allowed_ids), "exists": directory.is_dir(), "members": dict(sorted(members.items()))})
    return {
        "kind": KIND, "schema_version": SCHEMA, "plugin_version": plugin_version(),
        "project_root": str(root), "plan_path": str(plan), "plan_sha256": digest(plan),
        "context": context, "test_ids": sorted(allowed_ids), "sources": records,
        "watches": sorted(watch_records, key=lambda item: canonical([item["path"], item["patterns"]])),
    }


def validate_cache(data: dict) -> None:
    if data.get("kind") != KIND or type(data.get("schema_version")) is not int or data["schema_version"] != SCHEMA:
        raise CacheError("Unsupported discovery cache kind/schema")
    if data.get("reviewed") is not True or not timestamp(data.get("saved_at")):
        raise CacheError("Cache lacks an explicit reviewed capture record")
    for key in ("plugin_version", "project_root", "plan_path", "plan_sha256"):
        if not isinstance(data.get(key), str) or not data[key]:
            raise CacheError(f"Cache missing {key}")
    if not isinstance(data.get("test_ids"), list) or any(not isinstance(item, str) or not TEST_ID.fullmatch(item) for item in data["test_ids"]):
        raise CacheError("Cache test_ids malformed")
    if not isinstance(data.get("context"), dict) or not isinstance(data.get("sources"), dict) or not isinstance(data.get("watches"), list):
        raise CacheError("Cache context/sources/watches malformed")
    context_value(data["context"])
    allowed = set(data["test_ids"])
    for name, record in data["sources"].items():
        relative_name(name)
        if not isinstance(record, dict) or not isinstance(record.get("test_ids"), list) or record.get("kind") not in {"static", "volatile"} or record.get("category") not in CATEGORIES:
            raise CacheError(f"Malformed cached source: {name}")
        test_ids(record["test_ids"], allowed)
        if not isinstance(record.get("provenance"), str) or not record["provenance"].strip() or not timestamp(record.get("captured_at")) or "sha256" not in record:
            raise CacheError(f"Malformed cached source provenance/hash: {name}")
        if record.get("sha256") is not None and not re.fullmatch(r"[a-f0-9]{64}", str(record["sha256"])):
            raise CacheError(f"Invalid cached hash: {name}")
    for watch in data["watches"]:
        if not isinstance(watch, dict) or not isinstance(watch.get("path"), str) or not isinstance(watch.get("patterns"), list) or not isinstance(watch.get("test_ids"), list) or not isinstance(watch.get("members"), dict):
            raise CacheError("Malformed cached watch")
        relative_name(watch["path"], allow_dot=True)
        test_ids(watch["test_ids"], allowed)
        if type(watch.get("exists")) is not bool or not watch["patterns"] or any(not isinstance(pattern, str) for pattern in watch["patterns"]):
            raise CacheError("Malformed cached watch patterns/existence")
        for path, value in watch["members"].items():
            relative_name(path)
            if not isinstance(value, str) or not re.fullmatch(r"[a-f0-9]{64}", value):
                raise CacheError("Malformed cached watch fingerprint")


def compare(current: dict, previous: dict | None) -> dict:
    mapped = set(item for source in current["sources"].values() for item in source["test_ids"])
    mapped.update(item for watch in current["watches"] for item in watch["test_ids"])
    unindexed = set(current["test_ids"]) - mapped
    affected: set[str] = set(unindexed)
    reasons = []
    changes = []
    full = previous is None
    if previous is None:
        reasons.append("No previous reviewed discovery cache")
    else:
        validate_cache(previous)
        for key in ("plugin_version", "project_root", "plan_path", "plan_sha256", "context"):
            if previous[key] != current[key]:
                full = True
                reasons.append(f"{key} changed; review the full plan")
    if unindexed:
        reasons.append("Some plan cards have no indexed evidence and still require ordinary discovery")
    old_sources = previous["sources"] if previous else {}
    for path in sorted(set(old_sources) | set(current["sources"])):
        old, new = old_sources.get(path), current["sources"].get(path)
        change_reasons = []
        if old is None:
            change_reasons.append("new evidence source")
        elif new is None:
            change_reasons.append("source removed from discovery manifest")
        elif old.get("sha256") != new.get("sha256"):
            change_reasons.append("source content changed or disappeared")
        if new:
            if new["sha256"] is None:
                change_reasons.append("source missing; cannot reuse an unverified absence")
            if new["kind"] == "volatile":
                change_reasons.append("current configuration/activation/runtime evidence must be read again")
            if old and any(old.get(key) != new.get(key) for key in ("test_ids", "kind", "category", "provenance")):
                change_reasons.append("evidence mapping/provenance changed")
        if change_reasons:
            targets = set((old or {}).get("test_ids", [])) | set((new or {}).get("test_ids", []))
            affected.update(targets)
            if not targets or new is not None and not new["test_ids"]:
                full = True
                reasons.append(f"Unmapped evidence change: {path}")
            changes.append({"path": path, "reasons": change_reasons, "test_ids": sorted(targets)})
    key = lambda item: canonical([item["path"], item["patterns"]])
    old_watches = {key(item): item for item in previous["watches"]} if previous else {}
    new_watches = {key(item): item for item in current["watches"]}
    for identity in sorted(set(old_watches) | set(new_watches)):
        old, new = old_watches.get(identity), new_watches.get(identity)
        if old == new and new and new["exists"]:
            continue
        targets = set((old or {}).get("test_ids", [])) | set((new or {}).get("test_ids", []))
        old_files, new_files = (old or {}).get("members", {}), (new or {}).get("members", {})
        changed_files = sorted(path for path in set(old_files) | set(new_files) if old_files.get(path) != new_files.get(path))
        affected.update(targets)
        if not targets or new is not None and not new["test_ids"]:
            full = True
            reasons.append(f"Watched area has unmapped additions/removals: {(new or old)['path']}")
        changes.append({"watch": (new or old)["path"], "paths": changed_files, "test_ids": sorted(targets), "reasons": ["watch membership/content/configuration changed or directory missing"]})
    if full:
        affected.update(current["test_ids"])
    return {
        "status": "refresh_required" if full or affected else "static_sources_unchanged",
        "full_refresh": full, "affected_test_ids": sorted(affected & set(current["test_ids"])),
        "unindexed_test_ids": sorted(unindexed),
        "reasons": list(dict.fromkeys(reasons)), "changes": changes,
        "reusable_static_sources": sorted(path for path, record in current["sources"].items() if not full and record["kind"] == "static" and record["sha256"] is not None and old_sources.get(path) and all(old_sources[path].get(key) == record.get(key) for key in ("sha256", "test_ids", "kind", "category", "provenance"))),
        "limitations": ["Fingerprint equality is a reading aid, not a semantic review or test PASS.", "Live configuration, activation, routes, roles and runtime prerequisites still require current verification.", "An unlisted/unwatched source is outside this index's coverage."],
    }


def save(snapshot: dict, output: Path, *, reviewed: bool) -> None:
    if not reviewed:
        raise CacheError("Capture requires --reviewed after the actual source/plan review")
    if output.suffix.lower() != ".json" or is_link(output) or not output.parent.is_dir():
        raise CacheError("Output must be a JSON file in an existing storage-gated directory, not a symlink")
    if any(is_link(parent) for parent in output.parents):
        raise CacheError("Symlink/junction output directories are not supported")
    if output.exists():
        old = read_json(output)
        validate_cache(old)
        if old["project_root"] != snapshot["project_root"]:
            raise CacheError("Refusing to overwrite another project's discovery cache")
    document = snapshot | {"reviewed": True, "saved_at": datetime.now(timezone.utc).isoformat()}
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=output.parent, prefix=".discovery-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(document, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "capture"):
        sub = commands.add_parser(name)
        sub.add_argument("--root", type=Path, required=True)
        sub.add_argument("--plan", type=Path, required=True)
        sub.add_argument("--manifest", type=Path, required=True)
        if name == "check":
            sub.add_argument("--cache", type=Path, required=True)
        else:
            sub.add_argument("--output", type=Path, required=True)
            sub.add_argument("--reviewed", action="store_true")
    args = parser.parse_args(argv)
    try:
        current = build_snapshot(args.root, args.plan, args.manifest)
        if args.command == "capture":
            save(current, args.output, reviewed=args.reviewed)
            result = {"status": "captured", "path": str(args.output.resolve()), "source_count": len(current["sources"]), "watch_count": len(current["watches"]), "note": "Reviewed capture records the caller's attestation; the helper does not prove semantic correctness."}
        else:
            if is_link(args.cache):
                raise CacheError("Symlink/junction cache input is not supported")
            previous = read_json(args.cache) if args.cache.exists() else None
            # Unsupported/old schema is conservatively invalidated, never reused.
            if previous is not None and (previous.get("kind") != KIND or previous.get("schema_version") != SCHEMA):
                result = compare(current, None)
                result["reasons"] = ["Cache kind/schema changed or is unsupported; full review required"]
            else:
                result = compare(current, previous)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (CacheError, OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
