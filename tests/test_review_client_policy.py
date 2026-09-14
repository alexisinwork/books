import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import run_book_review as runner


class ClientPolicyTests(unittest.TestCase):
    def args(self, folder, **overrides):
        values = dict(out=Path(folder)/"review", role="gemini_pro", client="agy",
                      model="gemini-3.1-pro-high", source=None, context=[])
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_gemini_wrong_client_refused_before_any_run_or_read(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.args(folder, client="claude")
            with self.assertRaisesRegex(ValueError, "only through agy"):
                runner.run(args)
            self.assertFalse(args.out.exists())

    def test_mislabeled_role_cannot_bypass_gemini_client_rule(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.args(folder, role="opus", client="claude")
            with self.assertRaisesRegex(ValueError, "only through agy"):
                runner.run(args)

    def test_target_only_reader_rejects_source(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.args(folder, source=Path(folder)/"source.txt")
            with self.assertRaisesRegex(ValueError, "Target-only"):
                runner.run(args)

    def test_target_only_reader_rejects_context(self):
        with tempfile.TemporaryDirectory() as folder:
            args = self.args(folder, context=[Path(folder)/"notes.md"])
            with self.assertRaisesRegex(ValueError, "Target-only"):
                runner.run(args)

    def test_prompt_metadata_and_empty_success_are_not_a_review(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target, source, prompt = root/"uk.txt", root/"ru.txt", root/"rules.md"
            target.write_text("— Привіт.\n", encoding="utf-8")
            source.write_text("— Привет.\n", encoding="utf-8")
            prompt.write_text("Find material defects only.", encoding="utf-8")
            args = self.args(folder, role="gemini_flash", model="gemini-3.8-flash-high",
                             target=target, source=source, prompt=prompt)
            empty = SimpleNamespace(returncode=0, stdout=json.dumps({"status": "SUCCESS", "response": ""}), stderr="")
            with patch.object(runner.subprocess, "run", return_value=empty) as call:
                runner.run(args)
            self.assertEqual(call.call_args.args[0][0], "agy")
            self.assertIn(hashlib.sha256(source.read_bytes()).hexdigest(), (args.out/"prompt.txt").read_text())
            self.assertFalse((args.out/"REPORT.md").exists())
            self.assertEqual(json.loads((args.out/"invocation.json").read_text())["status"], "unavailable_or_incomplete")


if __name__ == "__main__":
    unittest.main()
