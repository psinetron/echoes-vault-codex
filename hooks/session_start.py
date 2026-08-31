#!/usr/bin/env python3
"""Provide EchoesVault context and optionally request a one-time status card."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def resolve_workspace(value: str) -> Path:
    candidate = Path(value).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(candidate), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
        return Path(result.stdout.strip()).resolve()
    except (FileNotFoundError, subprocess.SubprocessError):
        return candidate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--card",
        action="store_true",
        help="Ask Codex to show the current status card once in its first response.",
    )
    return parser


def render_card(workspace: Path) -> str:
    plugin_root = Path(os.environ.get("PLUGIN_ROOT") or Path(__file__).parents[1]).resolve()
    script = plugin_root / "scripts" / "echoes_vault.py"
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--workspace",
                str(workspace),
                "status",
                "--format",
                "card",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=8,
        )
        return result.stdout.strip()
    except (FileNotFoundError, subprocess.SubprocessError):
        return "### EchoesVault · △ Status unavailable"


def vault_is_initialized(workspace: Path) -> bool:
    index = workspace / "EchoesVault" / "index.md"
    marker = workspace / "EchoesVault" / ".echoes-vault.json"
    return (
        (marker.is_file() and not marker.is_symlink())
        or (index.is_file() and not index.is_symlink())
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        event = {}
    workspace = resolve_workspace(event.get("cwd") or os.getcwd())
    if not vault_is_initialized(workspace):
        json.dump({"continue": True, "suppressOutput": True}, sys.stdout)
        sys.stdout.write("\n")
        return 0

    card = render_card(workspace)
    context = (
        "EchoesVault is available. Do not initialize, restore, or finalize memory unless the user "
        "explicitly requests the corresponding action. Use $echoes-vault for targeted operations."
    )
    if args.card:
        context += (
            " At the very beginning of your first user-facing response after this SessionStart, "
            "show the following Markdown status card exactly once, then answer the user's request. "
            "Do not describe the hook or claim that the card is a persistent sidebar.\n\n"
            f"{card}"
        )
    output = {
        "continue": True,
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        },
    }
    json.dump(output, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
