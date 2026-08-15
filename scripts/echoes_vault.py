#!/usr/bin/env python3
"""Deterministic local storage engine for the EchoesVault Codex plugin."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


PLUGIN_VERSION = "0.1.0"
STATE_VERSION = 1
VAULT_DIRNAME = "EchoesVault"
STATE_RELATIVE_PATH = Path(".codex") / "echoes-vault-state.json"
DEFAULT_INDEX = """# EchoesVault Index

This registry tracks all structured pages in the project knowledge vault.

## Pages
"""
REQUIRED_FRONTMATTER = ("type", "stack", "status")
INDEX_ENTRY_RE = re.compile(r"^- \[\[([^\]]+)\]\]:\s*(.*)$")


class EchoesError(RuntimeError):
    """An expected, user-actionable vault error."""


def now() -> datetime:
    return datetime.now().astimezone()


def timestamp() -> str:
    return now().isoformat(timespec="seconds")


def today() -> str:
    return now().date().isoformat()


def resolve_workspace(value: str | None) -> Path:
    candidate = Path(value or os.getcwd()).expanduser().resolve()
    if not candidate.is_dir():
        raise EchoesError(f"Workspace is not a directory: {candidate}")
    try:
        result = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=3,
        )
        root = Path(result.stdout.strip()).resolve()
        if root.is_dir():
            return root
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    return candidate


def vault_paths(workspace: Path) -> dict[str, Path]:
    vault = workspace / VAULT_DIRNAME
    paths = {
        "workspace": workspace,
        "vault": vault,
        "raw": vault / "raw",
        "pages": vault / "pages",
        "daily": vault / "daily",
        "assets": vault / "assets",
        "index": vault / "index.md",
        "state": workspace / STATE_RELATIVE_PATH,
    }
    for key, candidate in paths.items():
        if key == "workspace":
            continue
        try:
            candidate.resolve(strict=False).relative_to(workspace)
        except ValueError as exc:
            raise EchoesError(
                f"Managed path escapes the workspace through a symlink: {candidate}"
            ) from exc
    return paths


def default_state() -> dict[str, Any]:
    return {
        "version": STATE_VERSION,
        "pluginVersion": PLUGIN_VERSION,
        "initialized": False,
        "session": {
            "started": False,
            "saved": False,
            "lastStart": None,
            "lastSave": None,
        },
        "stats": {
            "totalPages": 0,
            "totalDailyLogs": 0,
            "deprecatedPages": 0,
        },
    }


def merge_state(raw: Any) -> dict[str, Any]:
    state = default_state()
    if not isinstance(raw, dict):
        return state
    state["initialized"] = bool(raw.get("initialized", False))
    session = raw.get("session")
    if isinstance(session, dict):
        for key in ("started", "saved", "lastStart", "lastSave"):
            if key in session:
                state["session"][key] = session[key]
    state["pluginVersion"] = PLUGIN_VERSION
    return state


def read_state(paths: dict[str, Path]) -> dict[str, Any]:
    try:
        return merge_state(json.loads(paths["state"].read_text(encoding="utf-8")))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default_state()


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def append_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise EchoesError(f"Refusing to append through a symbolic link: {path}")
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(descriptor, content.encode("utf-8"))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def ensure_structure(paths: dict[str, Path]) -> None:
    for key in ("raw", "pages", "daily", "assets"):
        paths[key].mkdir(parents=True, exist_ok=True)
    if not paths["index"].exists():
        atomic_write(paths["index"], DEFAULT_INDEX)


def require_initialized(paths: dict[str, Path]) -> dict[str, Any]:
    state = read_state(paths)
    if not state["initialized"] or not paths["index"].is_file():
        raise EchoesError("EchoesVault is not initialized. Run the echoes-init workflow first.")
    ensure_structure(paths)
    return state


def markdown_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        (
            item
            for item in directory.iterdir()
            if item.is_file() and not item.is_symlink() and item.suffix == ".md"
        ),
        key=lambda item: item.name.casefold(),
    )


def vault_inventory(vault: Path) -> dict[str, Any]:
    """Collect size and filesystem integrity without following symbolic links."""
    total_bytes = 0
    total_files = 0
    markdown_count = 0
    symlinks: list[str] = []
    unreadable: list[str] = []
    latest_mtime: float | None = None
    if not vault.is_dir():
        return {
            "totalBytes": 0,
            "totalFiles": 0,
            "markdownFiles": 0,
            "symlinks": [],
            "unreadableFiles": [],
            "lastModified": None,
        }

    for root_name, directory_names, file_names in os.walk(vault, followlinks=False):
        root = Path(root_name)
        safe_directories: list[str] = []
        for directory_name in directory_names:
            directory = root / directory_name
            if directory.is_symlink():
                symlinks.append(str(directory.relative_to(vault)))
            else:
                safe_directories.append(directory_name)
        directory_names[:] = safe_directories

        for file_name in file_names:
            file_path = root / file_name
            relative = str(file_path.relative_to(vault))
            if file_path.is_symlink():
                symlinks.append(relative)
                continue
            try:
                stat = file_path.stat()
            except OSError:
                unreadable.append(relative)
                continue
            if not file_path.is_file():
                continue
            total_files += 1
            total_bytes += stat.st_size
            markdown_count += int(file_path.suffix.casefold() == ".md")
            latest_mtime = max(latest_mtime or stat.st_mtime, stat.st_mtime)

    return {
        "totalBytes": total_bytes,
        "totalFiles": total_files,
        "markdownFiles": markdown_count,
        "symlinks": sorted(symlinks),
        "unreadableFiles": sorted(unreadable),
        "lastModified": (
            datetime.fromtimestamp(latest_mtime).astimezone().isoformat(timespec="seconds")
            if latest_mtime is not None
            else None
        ),
    }


def format_bytes(value: int) -> str:
    amount = float(max(0, value))
    units = ("B", "KB", "MB", "GB", "TB")
    unit = units[0]
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            break
        amount /= 1024
    if unit == "B":
        return f"{int(amount)} {unit}"
    return f"{amount:.1f} {unit}"


def state_file_health(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "valid": False, "error": "state file is missing"}
    if path.is_symlink():
        return {"exists": True, "valid": False, "error": "state file is a symbolic link"}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"exists": True, "valid": False, "error": str(exc)}
    if not isinstance(raw, dict):
        return {"exists": True, "valid": False, "error": "state root is not an object"}
    return {"exists": True, "valid": True, "error": None}


def parse_index(content: str) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    for line in content.splitlines():
        match = INDEX_ENTRY_RE.match(line)
        if match:
            entries.append((match.group(1), match.group(2).strip(), line))
    return entries


def collect_health(paths: dict[str, Path]) -> dict[str, Any]:
    pages = markdown_files(paths["pages"])
    daily = markdown_files(paths["daily"])
    deprecated = []
    invalid_frontmatter: list[str] = []
    page_slugs = {page.stem for page in pages}
    for page in pages:
        try:
            content = page.read_text(encoding="utf-8")
            if "DEPRECATED" in content:
                deprecated.append(page.stem)
            try:
                validate_frontmatter(content)
            except EchoesError:
                invalid_frontmatter.append(page.stem)
        except (OSError, UnicodeError):
            invalid_frontmatter.append(page.stem)
            continue

    try:
        index_content = paths["index"].read_text(encoding="utf-8")
    except OSError:
        index_content = ""
    entries = parse_index(index_content)
    indexed_slugs = [slug for slug, _, _ in entries]
    seen: set[str] = set()
    duplicates: list[str] = []
    for slug in indexed_slugs:
        if slug in seen and slug not in duplicates:
            duplicates.append(slug)
        seen.add(slug)

    today_file = paths["daily"] / f"{today()}.md"
    try:
        today_content = today_file.read_text(encoding="utf-8")
    except OSError:
        today_content = ""

    required_paths = {
        "index.md": paths["index"].is_file() and not paths["index"].is_symlink(),
        "pages/": paths["pages"].is_dir() and not paths["pages"].is_symlink(),
        "daily/": paths["daily"].is_dir() and not paths["daily"].is_symlink(),
        "assets/": paths["assets"].is_dir() and not paths["assets"].is_symlink(),
        "raw/": paths["raw"].is_dir() and not paths["raw"].is_symlink(),
    }
    inventory = vault_inventory(paths["vault"])
    state_health = state_file_health(paths["state"])
    problems = {
        "missingStructure": sorted(name for name, present in required_paths.items() if not present),
        "invalidFrontmatter": sorted(set(invalid_frontmatter)),
        "duplicateIndexEntries": duplicates,
        "emptyDescriptions": [slug for slug, description, _ in entries if not description],
        "orphanPages": sorted(page_slugs - set(indexed_slugs)),
        "missingPages": sorted(set(indexed_slugs) - page_slugs),
        "symbolicLinks": inventory["symlinks"],
        "unreadableFiles": inventory["unreadableFiles"],
    }
    issue_count = sum(len(items) for items in problems.values())

    return {
        "totalPages": len(pages),
        "totalDailyLogs": len(daily),
        "deprecatedPages": len(deprecated),
        "deprecatedSlugs": deprecated,
        "indexTopics": len(entries),
        **problems,
        "todayEntries": len(
            re.findall(r"^### (?:Scratchpad|Session) — ", today_content, flags=re.MULTILINE)
        ),
        "scaleAlert": len(pages) > 200,
        "integrity": "healthy" if issue_count == 0 and state_health["valid"] else "attention",
        "issueCount": issue_count + int(not state_health["valid"]),
        "stateFile": state_health,
        "storage": inventory,
    }


def format_status_card(status: dict[str, Any]) -> str:
    state = status["state"]
    health = status["health"]
    initialized = bool(state.get("initialized")) and not health["missingStructure"]
    session = state.get("session") if isinstance(state.get("session"), dict) else {}
    if not initialized:
        badge = "○ Not initialized"
    elif health["integrity"] == "healthy":
        badge = "✓ Healthy"
    else:
        badge = f"△ Needs attention ({health['issueCount']})"

    session_label = "not started"
    if session.get("started"):
        session_label = "saved" if session.get("saved") else "active"
    storage = health["storage"]
    lines = [
        f"### EchoesVault · {badge}",
        "",
        "| Storage | Knowledge | Session |",
        "|---|---|---|",
        (
            f"| {format_bytes(int(storage['totalBytes']))} · {storage['totalFiles']} files "
            f"| {health['totalPages']} pages · {health['totalDailyLogs']} logs "
            f"| {session_label} |"
        ),
    ]
    if initialized and health["integrity"] == "healthy":
        lines.extend(["", "Integrity: index, structure, metadata, and local paths are consistent."])
    elif initialized:
        details = []
        labels = (
            ("missingStructure", "missing structure"),
            ("invalidFrontmatter", "invalid frontmatter"),
            ("duplicateIndexEntries", "duplicate index entries"),
            ("emptyDescriptions", "empty descriptions"),
            ("orphanPages", "orphan pages"),
            ("missingPages", "missing pages"),
            ("symbolicLinks", "symbolic links"),
            ("unreadableFiles", "unreadable files"),
        )
        for key, label in labels:
            if health[key]:
                details.append(f"{label}: {len(health[key])}")
        if not health["stateFile"]["valid"]:
            details.append("invalid runtime state")
        lines.extend(["", "Integrity: " + "; ".join(details) + "."])
    else:
        lines.extend(["", "Choose **Initialize or restore EchoesVault** to create local Markdown memory."])
    if health["scaleAlert"]:
        lines.extend(["", "> Scale alert: more than 200 pages; prefer targeted search."])
    lines.extend(
        [
            "",
            "Actions: **Initialize or restore** · **Show vault status** · **Save this session**",
        ]
    )
    return "\n".join(lines) + "\n"


def write_state(paths: dict[str, Path], state: dict[str, Any]) -> None:
    state["version"] = STATE_VERSION
    state["pluginVersion"] = PLUGIN_VERSION
    health = collect_health(paths)
    state["stats"] = {
        "totalPages": health["totalPages"],
        "totalDailyLogs": health["totalDailyLogs"],
        "deprecatedPages": health["deprecatedPages"],
    }
    atomic_write(paths["state"], json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def normalize_filename(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EchoesError("Page filename must be a non-empty string.")
    name = value.strip()
    if name.endswith(".md"):
        name = name[:-3]
    if not name or name in {".", ".."} or "/" in name or "\\" in name or ".." in name:
        raise EchoesError(f"Unsafe page filename: {value!r}")
    if name.startswith("."):
        raise EchoesError("Hidden page filenames are not allowed.")
    return f"{name}.md"


def validate_frontmatter(content: Any) -> str:
    if not isinstance(content, str) or not content.strip():
        raise EchoesError("Page content must be a non-empty string.")
    normalized = content.strip() + "\n"
    lines = normalized.splitlines()
    if not lines or lines[0] != "---":
        raise EchoesError("Every page must begin with YAML frontmatter.")
    try:
        closing = lines.index("---", 1)
    except ValueError as exc:
        raise EchoesError("YAML frontmatter is missing its closing '---'.") from exc
    if closing == 1:
        raise EchoesError("YAML frontmatter cannot be empty.")
    keys: set[str] = set()
    frontmatter_lines = lines[1:closing]
    for position, line in enumerate(frontmatter_lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if not match:
            continue
        has_inline_value = bool(match.group(2).strip())
        has_nested_value = False
        if not has_inline_value:
            for following in frontmatter_lines[position + 1 :]:
                if not following.strip() or following.lstrip().startswith("#"):
                    continue
                has_nested_value = following[0].isspace()
                break
        if has_inline_value or has_nested_value:
            keys.add(match.group(1))
    missing = [key for key in REQUIRED_FRONTMATTER if key not in keys]
    if missing:
        raise EchoesError(f"YAML frontmatter is missing required keys: {', '.join(missing)}")
    return normalized


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_payload(path_value: str) -> dict[str, Any]:
    try:
        if path_value == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(path_value).expanduser().read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise EchoesError(f"Cannot read JSON payload: {exc}") from exc
    if not isinstance(payload, dict):
        raise EchoesError("JSON payload must be an object.")
    return payload


def normalize_index_line(filename: str, description: Any) -> str:
    slug = Path(filename).stem
    if not isinstance(description, str) or not description.strip():
        raise EchoesError(f"A non-empty indexDescription is required for new page {filename}.")
    value = description.strip()
    match = INDEX_ENTRY_RE.match(value)
    if match:
        if match.group(1) != slug:
            raise EchoesError(
                f"Index link [[{match.group(1)}]] does not match page [[{slug}]]."
            )
        if not match.group(2).strip():
            raise EchoesError("Index description cannot be empty.")
        return value
    return f"- [[{slug}]]: {value}"


def prepare_page(
    paths: dict[str, Path], item: dict[str, Any], index_content: str
) -> tuple[Path, str, str]:
    filename = normalize_filename(item.get("filename"))
    content = validate_frontmatter(item.get("content"))
    page_path = paths["pages"] / filename
    if page_path.is_symlink():
        raise EchoesError(f"Refusing to read or replace a symbolic-link page: {filename}")
    existing = page_path.exists()
    slug = Path(filename).stem
    indexed = any(entry_slug == slug for entry_slug, _, _ in parse_index(index_content))

    if existing:
        expected = item.get("expectedSha256")
        if not isinstance(expected, str) or not expected:
            raise EchoesError(
                f"Updating {filename} requires expectedSha256 from the content read before writing."
            )
        current = page_path.read_text(encoding="utf-8")
        actual = sha256_text(current)
        if expected != actual:
            raise EchoesError(
                f"Concurrent change detected for {filename}: expected {expected}, found {actual}."
            )
        if not indexed:
            line = normalize_index_line(filename, item.get("indexDescription"))
            index_content = index_content.rstrip() + "\n" + line + "\n"
    else:
        line = normalize_index_line(filename, item.get("indexDescription"))
        if indexed:
            raise EchoesError(f"Index already links [[{slug}]], but the page file is missing.")
        index_content = index_content.rstrip() + "\n" + line + "\n"

    return page_path, content, index_content


def apply_index_updates(index_content: str, updates: Any) -> str:
    if updates is None:
        return index_content
    if not isinstance(updates, list):
        raise EchoesError("indexUpdates must be an array.")
    result = index_content
    for update in updates:
        if not isinstance(update, dict):
            raise EchoesError("Each index update must be an object.")
        old_line = update.get("oldLine")
        new_line = update.get("newLine")
        if not isinstance(old_line, str) or not isinstance(new_line, str):
            raise EchoesError("indexUpdates require string oldLine and newLine values.")
        count = result.splitlines().count(old_line)
        if count != 1:
            raise EchoesError(
                f"Index update oldLine must match exactly once; matched {count}: {old_line!r}"
            )
        result = result.replace(old_line, new_line, 1)
    return result


def validate_unique_index(index_content: str) -> None:
    slugs = [slug for slug, _, _ in parse_index(index_content)]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    if duplicates:
        raise EchoesError(f"Duplicate index entries are not allowed: {', '.join(duplicates)}")


def cmd_init(paths: dict[str, Path], _args: argparse.Namespace) -> dict[str, Any]:
    existed = paths["index"].exists()
    ensure_structure(paths)
    state = read_state(paths)
    state["initialized"] = True
    write_state(paths, state)
    return {
        "ok": True,
        "created": not existed,
        "vault": str(paths["vault"]),
        "index": str(paths["index"]),
        "state": state,
    }


def cmd_start(paths: dict[str, Path], args: argparse.Namespace) -> str:
    state = require_initialized(paths)
    recent_count = max(0, min(args.recent, 10))
    daily_files = sorted(markdown_files(paths["daily"]), key=lambda item: item.name, reverse=True)
    selected = daily_files[:recent_count]
    index_content = paths["index"].read_text(encoding="utf-8")
    sections = ["# EchoesVault session context", "", "## Index", "", index_content.rstrip()]
    sections.extend(["", f"## Recent daily logs ({len(selected)})"])
    if selected:
        for daily_file in selected:
            sections.extend(
                ["", f"### {daily_file.name}", "", daily_file.read_text(encoding="utf-8").rstrip()]
            )
    else:
        sections.extend(["", "No daily logs found."])
    health = collect_health(paths)
    if health["scaleAlert"]:
        sections.extend(
            [
                "",
                "> [!warning] SCALE ALERT",
                "> The vault exceeds 200 pages. Prefer targeted search over loading every page.",
            ]
        )
    state["session"]["started"] = True
    state["session"]["saved"] = False
    state["session"]["lastStart"] = timestamp()
    write_state(paths, state)
    return "\n".join(sections).rstrip() + "\n"


def cmd_status(paths: dict[str, Path], args: argparse.Namespace) -> Any:
    state = read_state(paths)
    health = collect_health(paths)
    state["stats"] = {
        "totalPages": health["totalPages"],
        "totalDailyLogs": health["totalDailyLogs"],
        "deprecatedPages": health["deprecatedPages"],
    }
    status = {
        "ok": True,
        "workspace": str(paths["workspace"]),
        "vault": str(paths["vault"]),
        "state": state,
        "health": health,
    }
    if args.format == "card":
        return format_status_card(status)
    return status


def cmd_search(paths: dict[str, Path], args: argparse.Namespace) -> dict[str, Any]:
    require_initialized(paths)
    query = args.query.strip()
    if not query:
        raise EchoesError("Search query cannot be empty.")
    folded = query.casefold()
    results = []
    limit = max(1, min(args.limit, 500))
    for page in markdown_files(paths["pages"]):
        for line_number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
            if folded in line.casefold():
                results.append(
                    {
                        "file": str(page.relative_to(paths["workspace"])),
                        "line": line_number,
                        "text": line.strip()[:300],
                    }
                )
                if len(results) >= limit:
                    return {"ok": True, "query": query, "truncated": True, "results": results}
    return {"ok": True, "query": query, "truncated": False, "results": results}


def cmd_append(paths: dict[str, Path], args: argparse.Namespace) -> dict[str, Any]:
    state = require_initialized(paths)
    payload = load_payload(args.payload)
    entry = payload.get("entry")
    if not isinstance(entry, str) or not entry.strip():
        raise EchoesError("Append payload requires a non-empty string field named 'entry'.")
    daily_file = paths["daily"] / f"{today()}.md"
    block = f"### Scratchpad — {timestamp()}\n\n{entry.strip()}\n\n"
    append_text(daily_file, block)
    write_state(paths, state)
    return {"ok": True, "dailyLog": str(daily_file), "kind": "scratchpad"}


def cmd_upsert(paths: dict[str, Path], args: argparse.Namespace) -> dict[str, Any]:
    state = require_initialized(paths)
    payload = load_payload(args.payload)
    index_content = paths["index"].read_text(encoding="utf-8")
    page_path, content, new_index = prepare_page(paths, payload, index_content)
    validate_unique_index(new_index)
    existed = page_path.exists()
    atomic_write(page_path, content)
    if new_index != index_content:
        atomic_write(paths["index"], new_index)
    write_state(paths, state)
    return {
        "ok": True,
        "action": "updated" if existed else "created",
        "page": str(page_path),
        "sha256": sha256_text(content),
        "indexChanged": new_index != index_content,
    }


def cmd_end(paths: dict[str, Path], args: argparse.Namespace) -> dict[str, Any]:
    if not args.confirm_explicit_user_end:
        raise EchoesError(
            "Final memory save requires --confirm-explicit-user-end from the echoes-end workflow."
        )
    state = require_initialized(paths)
    payload = load_payload(args.payload)
    summary = payload.get("dailySummary")
    if not isinstance(summary, str) or not summary.strip():
        raise EchoesError("End payload requires a non-empty dailySummary.")
    pages = payload.get("pages", [])
    if not isinstance(pages, list) or not all(isinstance(item, dict) for item in pages):
        raise EchoesError("End payload pages must be an array of objects.")

    index_content = paths["index"].read_text(encoding="utf-8")
    prepared: list[tuple[Path, str]] = []
    seen_paths: set[Path] = set()
    for item in pages:
        page_path, content, index_content = prepare_page(paths, item, index_content)
        if page_path in seen_paths:
            raise EchoesError(f"End payload contains duplicate page: {page_path.name}")
        seen_paths.add(page_path)
        prepared.append((page_path, content))
    index_content = apply_index_updates(index_content, payload.get("indexUpdates"))
    validate_unique_index(index_content)

    for page_path, content in prepared:
        atomic_write(page_path, content)
    atomic_write(paths["index"], index_content)
    daily_file = paths["daily"] / f"{today()}.md"
    block = f"### Session — {timestamp()}\n\n{summary.strip()}\n\n"
    append_text(daily_file, block)
    state["session"]["saved"] = True
    state["session"]["lastSave"] = timestamp()
    write_state(paths, state)
    return {
        "ok": True,
        "dailyLog": str(daily_file),
        "pagesWritten": len(prepared),
        "index": str(paths["index"]),
        "memorySaved": True,
    }


def cmd_hash(paths: dict[str, Path], args: argparse.Namespace) -> dict[str, Any]:
    require_initialized(paths)
    filename = normalize_filename(args.filename)
    page = paths["pages"] / filename
    if not page.is_file():
        raise EchoesError(f"Page does not exist: {filename}")
    content = page.read_text(encoding="utf-8")
    return {"ok": True, "page": str(page), "sha256": sha256_text(content)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        help="Project directory. Defaults to the current Git root, then the current directory.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create the vault idempotently.")
    start_parser = subparsers.add_parser("start", help="Restore index and recent daily logs.")
    start_parser.add_argument("--recent", type=int, default=3)
    status_parser = subparsers.add_parser(
        "status", help="Report state, metrics, storage size, and integrity."
    )
    status_parser.add_argument("--format", choices=("json", "card"), default="json")
    search_parser = subparsers.add_parser("search", help="Search page contents literally.")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=100)
    append_parser = subparsers.add_parser("append", help="Append a scratchpad entry from JSON.")
    append_parser.add_argument("--payload", default="-", help="JSON file path, or '-' for stdin.")
    upsert_parser = subparsers.add_parser("upsert", help="Create or safely update one page.")
    upsert_parser.add_argument("--payload", default="-", help="JSON file path, or '-' for stdin.")
    end_parser = subparsers.add_parser("end", help="Commit final session memory from JSON.")
    end_parser.add_argument("--payload", default="-", help="JSON file path, or '-' for stdin.")
    end_parser.add_argument("--confirm-explicit-user-end", action="store_true")
    hash_parser = subparsers.add_parser("hash", help="Hash a page for optimistic concurrency.")
    hash_parser.add_argument("filename")
    return parser


def emit(value: Any) -> None:
    if isinstance(value, str):
        sys.stdout.write(value)
        return
    sys.stdout.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        workspace = resolve_workspace(args.workspace)
        paths = vault_paths(workspace)
        commands = {
            "init": cmd_init,
            "start": cmd_start,
            "status": cmd_status,
            "search": cmd_search,
            "append": cmd_append,
            "upsert": cmd_upsert,
            "end": cmd_end,
            "hash": cmd_hash,
        }
        emit(commands[args.command](paths, args))
        return 0
    except EchoesError as exc:
        sys.stderr.write(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
