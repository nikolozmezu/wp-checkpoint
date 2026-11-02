#!/usr/bin/env python3
"""Read-only source/installed-cache diagnostic for the WP Checkpoint Claude plugin.

This cannot interrogate a running Claude session. --loaded-version is a caller-
reported value, not independent proof of what an existing session loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

PLUGIN = "wp-checkpoint"
RUNTIME_DIRS = (".claude-plugin", "skills", "scripts")
SKIP_DIRS = {"__pycache__", ".git", "node_modules"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".tmp"}


class DoctorError(ValueError):
    pass


def is_link(path: Path) -> bool:
    """Reject Windows junctions as well as symlinks, including Python 3.10/3.11."""
    if path.is_symlink():
        return True
    if hasattr(path, "is_junction") and path.is_junction():
        return True
    try:
        return getattr(path.lstat(), "st_reparse_tag", None) == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
    except FileNotFoundError:
        return False


def read_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DoctorError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise DoctorError(f"Expected JSON object: {path}")
    return value


def safe_file(root: Path, relative: Path) -> Path:
    current = root
    if relative.is_absolute() or ".." in relative.parts:
        raise DoctorError("Runtime path escapes plugin root")
    for part in relative.parts:
        current /= part
        if is_link(current):
            raise DoctorError(f"Symlink/junction runtime path is not inspected: {relative.as_posix()}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise DoctorError(f"Runtime path escapes plugin root: {relative.as_posix()}")
    return current


def manifest(root: Path) -> dict:
    value = read_object(safe_file(root, Path(".claude-plugin/plugin.json")))
    if value.get("name") != PLUGIN or not isinstance(value.get("version"), str) or not value["version"]:
        raise DoctorError(f"Not a valid {PLUGIN} plugin manifest: {root}")
    return value


def runtime_files(root: Path) -> dict[str, str]:
    result = {}
    for name in RUNTIME_DIRS:
        directory = safe_file(root, Path(name))
        if not directory.is_dir():
            continue
        for parent, dirs, files in os.walk(directory, followlinks=False):
            for item in dirs + files:
                candidate = Path(parent) / item
                if is_link(candidate):
                    raise DoctorError(f"Symlink/junction runtime file/directory is not inspected: {candidate.relative_to(root).as_posix()}")
            dirs[:] = [item for item in dirs if item not in SKIP_DIRS]
            for item in files:
                candidate = Path(parent) / item
                if candidate.suffix.lower() in SKIP_SUFFIXES:
                    continue
                relative = candidate.relative_to(root)
                candidate = safe_file(root, relative)
                hasher = hashlib.sha256()
                with candidate.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        hasher.update(chunk)
                result[relative.as_posix()] = hasher.hexdigest()
    return result


def relevant_settings(paths: list[Path], plugin_ids: set[str]) -> tuple[dict[str, dict], list[str]]:
    resolved = {}
    warnings = []
    for path in paths:
        if not path.exists():
            continue
        try:
            settings = read_object(path)
            enabled = settings.get("enabledPlugins", {})
            if not isinstance(enabled, dict):
                raise DoctorError(f"enabledPlugins must be an object: {path}")
            for plugin_id in plugin_ids:
                if plugin_id in enabled:
                    value = enabled[plugin_id]
                    if type(value) is not bool:
                        raise DoctorError(f"Plugin enabled flag must be boolean: {path}")
                    resolved[plugin_id] = {"enabled": value, "source": str(path.resolve())}
        except DoctorError as exc:
            warnings.append(str(exc))
    return resolved, warnings


def diagnose(source: Path, registry: Path, *, project: Path | None = None,
             settings: list[Path] | None = None, loaded_version: str | None = None) -> dict:
    source = source.resolve()
    project = (project or Path.cwd()).resolve()
    source_manifest = manifest(source)
    source_hashes = runtime_files(source)
    entries = []
    warnings = []
    registered = registry.exists()
    if registered:
        data = read_object(registry)
        plugins = data.get("plugins")
        if not isinstance(plugins, dict):
            raise DoctorError("Registry plugins must be an object")
        for plugin_id, records in plugins.items():
            if plugin_id != PLUGIN and not plugin_id.startswith(PLUGIN + "@"):
                continue
            if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
                raise DoctorError("WP Checkpoint registry entries must be objects in an array")
            for item in records:
                entries.append((plugin_id, item))
    else:
        warnings.append("Registry not found; a --plugin-dir installation may still be usable without registration")
    if settings is None:
        settings = [Path.home() / ".claude/settings.json", project / ".claude/settings.json", project / ".claude/settings.local.json"]
    flags, settings_warnings = relevant_settings(settings, {plugin_id for plugin_id, _ in entries})
    warnings.extend(settings_warnings)
    results = []
    for plugin_id, item in entries:
        scope = item.get("scope", "unknown")
        project_path = item.get("projectPath")
        applicable = True if scope == "user" else None
        if scope in {"project", "local"} and isinstance(project_path, str):
            applicable = Path(project_path).resolve() == project
        problems = []
        recommendations = []
        flag = flags.get(plugin_id, {})
        install = item.get("installPath")
        result = {
            "plugin_id": plugin_id, "scope": scope, "project_path": project_path,
            "applies_to_project": applicable, "registered_version": item.get("version"),
            "install_path": install, "cache_version": None,
            "enabled": flag.get("enabled"), "enabled_setting_source": flag.get("source"),
            "runtime_files_checked": 0, "different_files": [], "cache_matches_source": False,
        }
        if not isinstance(install, str) or not Path(install).is_absolute():
            problems.append("invalid_install_path")
            recommendations.append("Inspect this plugin's registry entry with claude plugin list")
        else:
            installed_root = Path(install)
            try:
                cached = manifest(installed_root)
                result["cache_version"] = cached["version"]
                installed_hashes = runtime_files(installed_root)
                all_paths = sorted(set(source_hashes) | set(installed_hashes))
                result["different_files"] = [name for name in all_paths if source_hashes.get(name) != installed_hashes.get(name)]
                result["runtime_files_checked"] = len(all_paths)
                result["cache_matches_source"] = not result["different_files"]
                if cached["version"] != source_manifest["version"]:
                    problems.append("source_cache_version_mismatch")
                if item.get("version") != cached["version"]:
                    problems.append("registry_cache_version_mismatch")
                if result["different_files"]:
                    problems.append("runtime_content_mismatch")
                if problems:
                    recommendations.append("Refresh the installed plugin from the intended source; a same-version update may keep the old cache")
            except (DoctorError, OSError) as exc:
                problems.append("unreadable_installed_copy")
                result["cache_error"] = str(exc)
                recommendations.append("Check the registered install path and reinstall/update this plugin if its cache is missing")
        if flag.get("enabled") is False and applicable is not False:
            problems.append("disabled")
            recommendations.append("Enable this plugin in Claude's plugin settings for the intended scope")
        elif flag.get("enabled") is None:
            recommendations.append("Verify enabled status with claude plugin list; no explicit enabled flag was found")
        session_mismatch = loaded_version is not None and loaded_version != result["cache_version"]
        if session_mismatch and applicable is not False:
            problems.append("reported_session_version_mismatch")
            recommendations.append("After confirming the correct installed copy, reload plugins or restart the Claude session")
        result.update(status="attention" if problems else "matches", problems=problems,
                      reported_session_version_matches_cache=None if loaded_version is None else loaded_version == result["cache_version"],
                      reload_needed=True if session_mismatch else None,
                      recommendations=recommendations)
        results.append(result)
    applicable_results = [item for item in results if item["applies_to_project"] is not False]
    status = "not_registered" if not results else "no_applicable_registration" if not applicable_results else "attention" if any(item["problems"] for item in applicable_results) else "matches"
    if len(applicable_results) > 1:
        warnings.append("Multiple potentially applicable registrations exist; confirm the scope/source loaded by the current session")
    return {
        "status": status, "source_root": str(source), "source_version": source_manifest["version"],
        "registry_path": str(registry.resolve()), "project_path": str(project),
        "loaded_session_version": loaded_version, "loaded_version_source": "caller-reported" if loaded_version else "unknown",
        "installations": results, "warnings": warnings,
        "limitations": ["Disk/cache equality does not identify the contents already loaded by a running Claude session.", "Settings are read in user, project, local order unless explicitly supplied; managed policy overrides are not inspected.", "No plugin is installed, updated, enabled, removed or reloaded by this diagnostic."],
    }


def print_human(result: dict) -> None:
    print(f"WP Checkpoint: {result['status']}")
    print(f"Source: {result['source_version']} — {result['source_root']}")
    print(f"Current session: {result['loaded_session_version'] or 'unknown'} ({result['loaded_version_source']})")
    if not result["installations"]:
        print("No matching registry entry. Check claude plugin list or the session's --plugin-dir source.")
    for item in result["installations"]:
        enabled = "enabled" if item["enabled"] is True else "disabled" if item["enabled"] is False else "enabled status unknown"
        print(f"- {item['plugin_id']} [{item['scope']}]: registry {item['registered_version']}, cache {item['cache_version']}; {enabled}")
        print(f"  {item['install_path']}")
        print(f"  Runtime files checked: {item['runtime_files_checked']}; differences: {len(item['different_files'])}")
        for problem in item["problems"]:
            print(f"  Attention: {problem}")
        for recommendation in item["recommendations"]:
            print(f"  Next: {recommendation}")
    for warning in result["warnings"]:
        print(f"Warning: {warning}")
    print("A running session's loaded code is not automatically verified; reload/restart if it predates an update.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--registry", type=Path, default=Path.home() / ".claude/plugins/installed_plugins.json")
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--settings", type=Path, action="append", help="Explicit settings file(s), in precedence order; bypasses default settings lookup")
    parser.add_argument("--loaded-version", help="Version reported by this Claude session; never automatically inferred from disk")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.json and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = diagnose(args.source, args.registry, project=args.project, settings=args.settings, loaded_version=args.loaded_version)
        if args.json:
            print(json.dumps(result, ensure_ascii=True, indent=2))
        else:
            print_human(result)
        return 0 if result["status"] == "matches" else 1
    except (DoctorError, OSError, UnicodeError, ValueError, TypeError) as exc:
        if args.json:
            print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=True))
        else:
            print(f"WP Checkpoint diagnostic error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
