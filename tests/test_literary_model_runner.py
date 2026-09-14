import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_SPEC = importlib.util.spec_from_file_location(
    "run_literary_model", ROOT / "tools/run_literary_model.py"
)
RUNNER = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader
MODULE_SPEC.loader.exec_module(RUNNER)


class LiteraryModelRunnerTests(unittest.TestCase):
    def test_large_agy_prompt_uses_only_absolute_temporary_input_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prompt = root / "role.md"
            target = root / "target.txt"
            large_input = root / "permitted manuscript.txt"
            prompt.write_text("Read the permitted manuscript completely.", encoding="utf-8")
            target.write_text("target", encoding="utf-8")
            large_input.write_text("Абзац дозволеного тексту.\n" * 6000, encoding="utf-8")
            out = root / "report"
            args = SimpleNamespace(
                out=out, input=[f"MANUSCRIPT={large_input}"], prompt=prompt,
                target=target, source=None, role="mocked-reader", client="agy",
                model="mock-model", effort="high", timeout="20m", timeout_seconds=10,
            )
            observed = {}

            def fake_run(command, *, input, text, cwd, capture_output, timeout):
                self.assertTrue(text)
                self.assertTrue(capture_output)
                self.assertEqual(10, timeout)
                self.assertIn("--dangerously-skip-permissions", command)
                cwd_path = Path(cwd).resolve()
                copies = list(cwd_path.glob("*.txt"))
                self.assertEqual(1, len(copies))
                copied = copies[0].resolve()
                self.assertTrue(copied.is_file())
                self.assertEqual(large_input.read_bytes(), copied.read_bytes())
                event = json.loads(input)
                effective_prompt = event["message"]["content"]
                self.assertIn(str(copied), effective_prompt)
                self.assertNotIn(str(large_input), effective_prompt)
                self.assertIn("Do not list, search, glob, or traverse any directory", effective_prompt)
                self.assertIn("do not look for a fallback copy", effective_prompt)
                observed["copied"] = str(copied)
                response = "Mocked literary report. " + ("Evidence sentence. " * 10)
                stdout = json.dumps({
                    "event": "result",
                    "result": {
                        "status": "SUCCESS", "response": response,
                        "conversation_id": "mock-conversation", "usage": {},
                        "denied_actions": [],
                    },
                }) + "\n"
                return SimpleNamespace(stdout=stdout, stderr="", returncode=0)

            with mock.patch.object(RUNNER.subprocess, "run", side_effect=fake_run) as process:
                RUNNER.run(args)
            process.assert_called_once()
            receipt = json.loads((out / "invocation.json").read_text(encoding="utf-8"))
            self.assertEqual("temporary_absolute_paths", receipt["input_delivery"])
            self.assertEqual(
                "prompt-restricted, filesystem isolation not guaranteed",
                receipt["isolation"],
            )
            self.assertEqual(observed["copied"], receipt["temporary_inputs"][0]["path"])
            self.assertTrue(Path(receipt["temporary_inputs"][0]["path"]).is_absolute())
            self.assertFalse(Path(receipt["temporary_inputs"][0]["path"]).exists())
            self.assertEqual("report_returned", receipt["status"])


if __name__ == "__main__":
    unittest.main()
