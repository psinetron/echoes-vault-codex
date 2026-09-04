from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PLUGIN_ROOT = Path(__file__).parents[1]
HOOK = PLUGIN_ROOT / "hooks" / "session_start.py"
CLI = PLUGIN_ROOT / "scripts" / "echoes_vault.py"


class SessionStartHookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        subprocess.run(
            [sys.executable, str(CLI), "--workspace", str(self.workspace), "init"],
            check=True,
            capture_output=True,
            text=True,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_hook(self, *args: str) -> dict:
        environment = dict(os.environ)
        environment["PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        result = subprocess.run(
            [sys.executable, str(HOOK), *args],
            input=json.dumps({"cwd": str(self.workspace)}),
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )
        return json.loads(result.stdout)

    def test_visible_session_start_requests_one_status_card(self) -> None:
        output = self.run_hook("--card")
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertTrue(output["suppressOutput"])
        self.assertIn("show the following Markdown status card exactly once", context)
        self.assertIn("### EchoesVault · ✓ Healthy", context)

    def test_compaction_context_does_not_repeat_card(self) -> None:
        output = self.run_hook()
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertNotIn("show the following Markdown status card", context)
        self.assertNotIn("### EchoesVault", context)

    def test_session_start_reports_missing_files_without_repairing_them(self) -> None:
        index = self.workspace / "EchoesVault" / "index.md"
        protocol = self.workspace / "EchoesVault" / "AGENT_PROTOCOL.md"
        runtime = self.workspace / ".echoes-vault" / "echoes_vault.py"
        index.unlink()
        protocol.unlink()
        runtime.unlink()
        output = self.run_hook("--card")
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertFalse(index.exists())
        self.assertFalse(protocol.exists())
        self.assertFalse(runtime.exists())
        self.assertIn("### EchoesVault · △ Needs attention", context)

    def test_session_start_does_not_change_tracked_files(self) -> None:
        subprocess.run(
            ["git", "-C", str(self.workspace), "init", "-b", "main"],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "-C", str(self.workspace), "config", "user.name", "Echoes Test"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.workspace), "config", "user.email", "echoes@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.workspace), "add", "-A"], check=True
        )
        subprocess.run(
            ["git", "-C", str(self.workspace), "commit", "-m", "init"],
            check=True,
            capture_output=True,
            text=True,
        )
        before = subprocess.run(
            ["git", "-C", str(self.workspace), "status", "--porcelain=v1"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.run_hook("--card")
        after = subprocess.run(
            ["git", "-C", str(self.workspace), "status", "--porcelain=v1"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual(after, before)

    def test_uninitialized_workspace_is_completely_silent(self) -> None:
        with tempfile.TemporaryDirectory() as workspace_name:
            environment = dict(os.environ)
            environment["PLUGIN_ROOT"] = str(PLUGIN_ROOT)
            result = subprocess.run(
                [sys.executable, str(HOOK), "--card"],
                input=json.dumps({"cwd": workspace_name}),
                check=True,
                capture_output=True,
                text=True,
                env=environment,
            )
        output = json.loads(result.stdout)
        self.assertEqual(output, {"continue": True, "suppressOutput": True})


if __name__ == "__main__":
    unittest.main()
