from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "echoes_vault.py"
SPEC = importlib.util.spec_from_file_location("echoes_vault", SCRIPT)
assert SPEC and SPEC.loader
echoes_vault = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(echoes_vault)


class EchoesVaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_cli(self, *args: str, stdin: dict | None = None) -> tuple[int, str, str]:
        old_stdin = sys.stdin
        stdout = io.StringIO()
        stderr = io.StringIO()
        if stdin is not None:
            sys.stdin = io.StringIO(json.dumps(stdin))
        try:
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = echoes_vault.main(["--workspace", str(self.workspace), *args])
        finally:
            sys.stdin = old_stdin
        return code, stdout.getvalue(), stderr.getvalue()

    def test_init_is_idempotent(self) -> None:
        code, output, _ = self.run_cli("init")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output)["created"])
        index = self.workspace / "EchoesVault" / "index.md"
        index.write_text(index.read_text() + "\nUser text\n", encoding="utf-8")
        code, output, _ = self.run_cli("init")
        self.assertEqual(code, 0)
        self.assertFalse(json.loads(output)["created"])
        self.assertIn("User text", index.read_text(encoding="utf-8"))

    def test_upsert_search_and_status(self) -> None:
        self.run_cli("init")
        page = {
            "filename": "auth-architecture.md",
            "content": (
                "---\ntype: architecture\nstack: [python]\nstatus: active\n---\n\n"
                "# Auth architecture\n\nJWT validation lives at the boundary.\n"
            ),
            "indexDescription": "Authentication boundaries and token flow.",
        }
        code, output, _ = self.run_cli("upsert", "--payload", "-", stdin=page)
        self.assertEqual(code, 0)
        result = json.loads(output)
        self.assertEqual(result["action"], "created")
        code, output, _ = self.run_cli("search", "jwt")
        self.assertEqual(code, 0)
        self.assertEqual(len(json.loads(output)["results"]), 1)
        code, output, _ = self.run_cli("status")
        status = json.loads(output)
        self.assertEqual(status["health"]["totalPages"], 1)
        self.assertEqual(status["health"]["indexTopics"], 1)
        self.assertEqual(status["health"]["orphanPages"], [])

    def test_status_reports_storage_integrity_and_card(self) -> None:
        self.run_cli("init")
        invalid_page = self.workspace / "EchoesVault" / "pages" / "broken.md"
        invalid_page.write_text("# Missing frontmatter\n", encoding="utf-8")
        asset = self.workspace / "EchoesVault" / "assets" / "sample.bin"
        asset.write_bytes(b"echoes")

        code, output, _ = self.run_cli("status")
        self.assertEqual(code, 0)
        status = json.loads(output)
        health = status["health"]
        self.assertGreaterEqual(health["storage"]["totalBytes"], len(b"echoes"))
        self.assertGreaterEqual(health["storage"]["totalFiles"], 3)
        self.assertEqual(health["invalidFrontmatter"], ["broken"])
        self.assertEqual(health["orphanPages"], ["broken"])
        self.assertEqual(health["integrity"], "attention")

        code, card, _ = self.run_cli("status", "--format", "card")
        self.assertEqual(code, 0)
        self.assertIn("EchoesVault", card)
        self.assertIn("Needs attention", card)
        self.assertIn("invalid frontmatter: 1", card)
        self.assertIn("orphan pages: 1", card)

    def test_uninitialized_status_card_is_actionable(self) -> None:
        code, card, _ = self.run_cli("status", "--format", "card")
        self.assertEqual(code, 0)
        self.assertIn("Not initialized", card)
        self.assertIn("Initialize or restore", card)

    def test_existing_page_requires_current_hash(self) -> None:
        self.run_cli("init")
        original = {
            "filename": "decision.md",
            "content": "---\ntype: decision\nstack: []\nstatus: active\n---\n\n# One\n",
            "indexDescription": "A decision.",
        }
        self.run_cli("upsert", "--payload", "-", stdin=original)
        changed = dict(original)
        changed["content"] = "---\ntype: decision\nstack: []\nstatus: active\n---\n\n# Two\n"
        code, _, error = self.run_cli("upsert", "--payload", "-", stdin=changed)
        self.assertEqual(code, 2)
        self.assertIn("expectedSha256", error)
        current = (self.workspace / "EchoesVault" / "pages" / "decision.md").read_text()
        changed["expectedSha256"] = echoes_vault.sha256_text(current)
        code, output, _ = self.run_cli("upsert", "--payload", "-", stdin=changed)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output)["action"], "updated")

    def test_rejects_unsafe_filename_and_invalid_frontmatter(self) -> None:
        self.run_cli("init")
        unsafe = {
            "filename": "../outside.md",
            "content": "---\ntype: note\nstack: []\nstatus: active\n---\n",
            "indexDescription": "Unsafe.",
        }
        code, _, _ = self.run_cli("upsert", "--payload", "-", stdin=unsafe)
        self.assertEqual(code, 2)
        invalid = {
            "filename": "invalid.md",
            "content": "# Missing metadata\n",
            "indexDescription": "Invalid.",
        }
        code, _, error = self.run_cli("upsert", "--payload", "-", stdin=invalid)
        self.assertEqual(code, 2)
        self.assertIn("frontmatter", error)

        empty_value = {
            "filename": "empty-value.md",
            "content": "---\ntype:\nstack: []\nstatus: active\n---\n",
            "indexDescription": "Invalid.",
        }
        code, _, error = self.run_cli("upsert", "--payload", "-", stdin=empty_value)
        self.assertEqual(code, 2)
        self.assertIn("type", error)

    def test_rejects_vault_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as outside_name:
            outside = Path(outside_name)
            (self.workspace / "EchoesVault").symlink_to(outside, target_is_directory=True)
            code, _, error = self.run_cli("init")
            self.assertEqual(code, 2)
            self.assertIn("escapes the workspace", error)

    def test_end_requires_explicit_confirmation(self) -> None:
        self.run_cli("init")
        payload = {"dailySummary": "- Completed tests.", "pages": [], "indexUpdates": []}
        code, _, error = self.run_cli("end", "--payload", "-", stdin=payload)
        self.assertEqual(code, 2)
        self.assertIn("confirm-explicit-user-end", error)
        code, output, _ = self.run_cli(
            "end", "--confirm-explicit-user-end", "--payload", "-", stdin=payload
        )
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output)["memorySaved"])
        daily_files = list((self.workspace / "EchoesVault" / "daily").glob("*.md"))
        self.assertEqual(len(daily_files), 1)
        self.assertIn("Completed tests", daily_files[0].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
