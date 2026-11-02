#!/usr/bin/env python3
"""Build a fresh, small local marketplace bundle; never install or publish it.

Native local-marketplace installation can copy ignored development files. This
helper selects only WP Checkpoint's distributable source roots and file types.
It preserves bytes, rejects links, and never writes into the source repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


ROOT_FILES = {"README.md", "LICENSE", "LICENSE.md", "LICENSE.txt", "CHANGELOG.md"}
ROOT_DIRS = {".claude-plugin", "skills", "scripts", "evals", "tests"}
RUNTIME_DIRS = {".claude-plugin", "skills", "scripts"}
EXTENSIONS = {".md", ".py", ".txt", ".json", ".php", ".html", ".css", ".js", ".mjs", ".yaml", ".yml", ".png", ".jpg", ".jpeg", ".svg"}
OMIT_DIRS = {"node_modules", ".cache", ".git", "__pycache__", ".venv", "venv", "dist", "build", "test-results", "playwright-report", "reports", "screenshots"}
GENERATED_FILES = {"testing-after-update.md", "wp-update-report.md", "wp-update-report.docx", "checkpoint.json", "run-state.json", "comparison.json", "comparison-input.json", "log-excerpt.txt", "discovery-cache.json", "selection.json", "context.json"}
SECRET_NAMES = {"wp-config.php", "auth.json", "credentials.json", "credentials", "storage-state.json", "id_rsa", "id_ed25519", ".npmrc", ".pypirc"}
SYNTHETIC_LOGS = {"evals/fieldnotes/archive/production-2025.log", "evals/memberlane/archive/production-2025.log"}
REQUIRED = {".claude-plugin/plugin.json", ".claude-plugin/marketplace.json", "README.md", "skills/test/SKILL.md", "skills/test-plan-create/SKILL.md", "scripts/validate.py"}
MAX_ASSET_BYTES = 2 * 1024 * 1024
MAX_RUNTIME_BYTES = 8 * 1024 * 1024
MAX_PACKAGE_BYTES = 32 * 1024 * 1024
CATALOG_MARKER = ".wp-checkpoint-catalog.json"
CATALOG_KIND = "wp-checkpoint-owned-local-catalog"


class PackageError(ValueError):
    pass


def is_link(path):
    return path.is_symlink() or getattr(path, "is_junction", lambda: False)()


def require(condition, message):
    if not condition:
        raise PackageError(message)


def check_ancestors(path):
    for part in (path, *path.parents):
        require(not is_link(part), f"Symlink/junction paths are not packaged: {part}")


def omitted(path, directory=False):
    name = path.name.casefold()
    if directory:
        return name in OMIT_DIRS or name.startswith((".validation-", ".quality-", "report-")) or name.startswith(".") and name != ".claude-plugin"
    return name in GENERATED_FILES or name.startswith((".run-state-", ".discovery-")) or path.suffix.casefold() in {".pyc", ".pyo", ".tmp", ".zip", ".tar", ".gz", ".docx"} or path.suffix.casefold() == ".log" and path.as_posix() not in SYNTHETIC_LOGS


def secret(path):
    name = path.name.casefold()
    return name in SECRET_NAMES or name == ".env" or name.startswith(".env.") or path.suffix.casefold() in {".pem", ".key", ".pfx", ".p12", ".sql", ".sqlite", ".sqlite3", ".db"}


def collect(source):
    """Return a bounded snapshot of allowed source bytes, without following links."""
    files, skipped = {}, []
    total = 0

    def visit(path, relative):
        nonlocal total
        # Prune known development trees before enumerating their contents.
        if path.is_dir() and omitted(relative, directory=True):
            skipped.append(relative.as_posix() + "/")
            return
        require(not is_link(path), f"Symlink/junction source is not allowed: {relative.as_posix()}")
        require(path.resolve().is_relative_to(source), "Source path escapes plugin root")
        if path.is_dir():
            for child in sorted(path.iterdir(), key=lambda item: item.name):
                visit(child, relative / child.name)
            return
        require(path.is_file(), f"Unsupported non-regular source: {relative.as_posix()}")
        runtime = relative.parts[0] in RUNTIME_DIRS
        if omitted(relative):
            skipped.append(relative.as_posix())
            return
        if secret(relative):
            require(not runtime, f"Remove secret-bearing files from runtime directories before packaging: {relative.as_posix()}")
            skipped.append(relative.as_posix())
            return
        allowed = relative.as_posix() in ROOT_FILES or path.suffix.casefold() in EXTENSIONS or relative.as_posix() in SYNTHETIC_LOGS
        if not allowed:
            require(not runtime, f"Unsupported runtime file type; review it explicitly before packaging: {relative.as_posix()}")
            skipped.append(relative.as_posix())
            return
        limit = MAX_RUNTIME_BYTES if runtime else MAX_ASSET_BYTES
        require(path.stat().st_size <= limit, f"Source asset exceeds the packaging limit: {relative.as_posix()}")
        content = path.read_bytes()
        total += len(content)
        require(total <= MAX_PACKAGE_BYTES, "Package exceeds 32 MiB; inspect source assets instead of including development artifacts")
        files[relative.as_posix()] = content

    for name in sorted(ROOT_FILES | ROOT_DIRS):
        path = source / name
        if path.exists() or is_link(path):
            visit(path, Path(name))
    require(REQUIRED <= set(files), "Missing distributable files: " + ", ".join(sorted(REQUIRED - set(files))))
    try:
        plugin = json.loads(files[".claude-plugin/plugin.json"].decode("utf-8-sig"))
        marketplace = json.loads(files[".claude-plugin/marketplace.json"].decode("utf-8-sig"))
        require(isinstance(plugin, dict) and plugin.get("name") == "wp-checkpoint" and isinstance(plugin.get("version"), str) and re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][\w.-]+)?", plugin["version"]), "Invalid WP Checkpoint plugin manifest")
        require(isinstance(marketplace, dict) and any(isinstance(item, dict) and item.get("name") == "wp-checkpoint" and item.get("source") == "." for item in marketplace.get("plugins", [])), "Marketplace must reference wp-checkpoint at source '.'")
    except (ValueError, TypeError, UnicodeError) as exc:
        if isinstance(exc, PackageError):
            raise
        raise PackageError(f"Invalid plugin/marketplace JSON: {exc}") from exc
    return files, skipped, plugin["version"]


def build(source, output):
    source, output = Path(source).absolute(), Path(output)
    require(output.is_absolute() and ".." not in output.parts, "Output must be an explicit absolute path without '..'")
    check_ancestors(source)
    check_ancestors(output)
    source = source.resolve()
    require(source.is_dir(), "Source must be an existing plugin directory")
    require(not output.exists(), "Output already exists; choose a fresh bundle directory")
    require(output.parent.is_dir(), "Output parent must already exist")
    output = output.resolve()
    require(not output.is_relative_to(source), "Output must be outside the source tree")
    files, skipped, version = collect(source)
    output.mkdir()  # No overwrite, including a race that creates this destination.
    for relative, content in sorted(files.items()):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        check_ancestors(target)
        require(target.resolve().is_relative_to(output), "Destination escaped its fresh bundle")
        with target.open("xb") as stream:
            stream.write(content)
    # Detect edits/additions made while assembling this snapshot. An error leaves
    # an explicitly unapproved partial bundle; it is never installed automatically.
    current, _, current_version = collect(source)
    require(current == files and current_version == version, "Source changed during packaging; discard this bundle and build a fresh one")
    return {"status": "prepared", "plugin": "wp-checkpoint", "version": version, "source": str(source), "output": str(output),
            "files": len(files), "bytes": sum(len(value) for value in files.values()),
            "sha256": {name: hashlib.sha256(value).hexdigest() for name, value in sorted(files.items())},
            "omitted": skipped, "note": "Prepared a local marketplace only; nothing was installed or published."}


def read_object(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise PackageError(f"Cannot read owned catalogue metadata: {path}") from exc
    require(isinstance(value, dict), "Catalogue metadata must be an object")
    return value


def build_catalog(source, output, catalog):
    """Publish only a local catalogue pointer, after a fresh release is prepared."""
    source, output, catalog = Path(source).absolute(), Path(output), Path(catalog)
    check_ancestors(source)
    source = source.resolve()
    for path in (output, catalog):
        require(path.is_absolute() and ".." not in path.parts, "Catalogue/output must be explicit absolute paths without '..'")
        check_ancestors(path)
    catalog = catalog.resolve()
    require(not catalog.is_relative_to(source) and not source.is_relative_to(catalog), "Catalogue must be outside the source tree and cannot contain it")
    require(catalog.parent.is_dir(), "Catalogue parent must already exist")
    files, _, version = collect(source)
    marketplace = json.loads(files[".claude-plugin/marketplace.json"].decode("utf-8-sig"))
    entries = marketplace.get("plugins")
    require(isinstance(entries, list) and len(entries) == 1 and entries[0].get("name") == "wp-checkpoint", "Stable catalogue supports only this single-plugin marketplace")
    name = marketplace.get("name")
    require(isinstance(name, str) and bool(name.strip()), "Marketplace needs a name for stable catalogue ownership")
    expected_output = catalog / "releases" / version
    require(output.resolve() == expected_output, "With --catalog, --output must equal <catalog>/releases/<manifest-version>")
    require(not output.exists(), "Release already exists; old releases are immutable, so choose a new source version")
    marker = catalog / CATALOG_MARKER
    pointer = catalog / ".claude-plugin/marketplace.json"
    owner = {"kind": CATALOG_KIND, "schema_version": 1, "plugin": "wp-checkpoint", "source_root": str(source), "marketplace_name": name}
    if catalog.exists():
        require(catalog.is_dir() and marker.is_file() and not is_link(marker), "Refusing an unrelated/unowned catalogue directory")
        require(read_object(marker) == owner, "Catalogue ownership/source differs; use a separate catalogue")
        if pointer.exists() or is_link(pointer):
            check_ancestors(pointer)
            current = read_object(pointer)
            current_entries = current.get("plugins")
            require(current.get("name") == name and isinstance(current_entries, list) and len(current_entries) == 1 and isinstance(current_entries[0], dict) and current_entries[0].get("name") == "wp-checkpoint", "Refusing to replace an unrelated marketplace catalogue")
            reference = current_entries[0].get("source")
            require(isinstance(reference, str) and re.fullmatch(r"\./releases/\d+\.\d+\.\d+(?:[-+][\w.-]+)?", reference), "Current catalogue has an unexpected source path")
            previous = catalog / reference
            check_ancestors(previous)
            prior_path = previous / ".claude-plugin/plugin.json"
            check_ancestors(prior_path)
            prior_manifest = read_object(prior_path)
            require(prior_manifest.get("name") == "wp-checkpoint" and prior_manifest.get("version") == previous.name, "Current catalogue release identity is invalid")
    else:
        catalog.mkdir()
        with marker.open("x", encoding="utf-8") as stream:
            json.dump(owner, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
    (catalog / "releases").mkdir(exist_ok=True)
    check_ancestors(catalog / "releases")
    result = build(source, expected_output)
    require(result["version"] == version, "Source version changed; catalogue pointer was not updated")
    entries[0]["source"] = f"./releases/{version}"
    pointer.parent.mkdir(exist_ok=True)
    check_ancestors(pointer)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=pointer.parent, prefix=".catalog-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(marketplace, stream, ensure_ascii=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, pointer)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    result.update(catalog=str(catalog), catalogue_pointer=str(pointer), note="Prepared a versioned local release and atomically updated its owned catalogue pointer; nothing was registered, installed or published externally.")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True, help="Fresh absolute directory outside the source tree; parent must exist")
    parser.add_argument("--catalog", type=Path, help="Optional owned stable local catalogue; output must be its releases/<manifest-version> directory")
    args = parser.parse_args(argv)
    try:
        result = build_catalog(args.source, args.output, args.catalog) if args.catalog else build(args.source, args.output)
    except (PackageError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc), "note": "Do not install an incomplete bundle; choose a fresh output after correcting the problem."}, ensure_ascii=True))
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
