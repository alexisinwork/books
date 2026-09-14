import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
TOOL = REPO / "tools" / "editorial_ensemble.py"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EditorialEnsembleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(REPO / "editorial", self.root / "editorial")
        shutil.copytree(REPO / ".agents", self.root / ".agents")
        (self.root / ".claude").mkdir()
        (self.root / ".claude" / "skills").symlink_to("../.agents/skills")

        project = self.root / "sample"
        tric = project / "books" / "book-01"
        tric.mkdir(parents=True)
        manuscript = tric / "manuscript.md"
        manuscript.write_text("# Книга\n\n## Глава 1\n\nГерой открыл дверь.\n", encoding="utf-8")
        source_sha = digest(manuscript)
        (project / "project.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "project_id": "sample",
                    "books": [{"id": "book-01", "path": "books/book-01"}],
                }
            ),
            encoding="utf-8",
        )
        (tric / "book.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "project_id": "sample",
                    "book_id": "book-01",
                    "working_revision": {
                        "path": "manuscript.md",
                        "sha256": source_sha,
                        "status": "candidate",
                        "authority": "test",
                    },
                }
            ),
            encoding="utf-8",
        )
        self.run_rel = "sample/books/book-01/audit/ensemble/test-run"
        self.run_dir = self.root / self.run_rel

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *args, check=True):
        return subprocess.run(
            [sys.executable, str(TOOL), "--root", str(self.root), *args],
            text=True,
            capture_output=True,
            check=check,
        )

    def final_report(self, role):
        run = json.loads((self.run_dir / "run.json").read_text(encoding="utf-8"))
        body = (
            f"# Test report\n\nRun ID: `test-run`\n"
            f"Source SHA-256: `{run['source']['sha256']}`\n"
            f"Role: `{role}`\nStatus: final\n"
            + ("Model: test-model\nClient: test-client\n" if role != "author" else "")
            + "\n"
            + "Evidence from the complete declared scope. " * 20
            + "\n"
        )
        filename = (
            "author-decisions.md"
            if role == "author"
            else run["reports"][role]["file"]
        )
        (self.run_dir / filename).write_text(body, encoding="utf-8")

    def test_full_empty_issue_cycle_and_tamper_detection(self):
        created = self.call(
            "init",
            "--project",
            "sample",
            "--book",
            "book-01",
            "--run-id",
            "test-run",
        )
        self.assertEqual(json.loads(created.stdout)["status"], "prepared")

        packet = self.root.parent / (self.root.name + "-blind")
        try:
            packed = self.call(
                "blind-pack", "--run", self.run_rel, "--out", str(packet)
            )
            packed_data = json.loads(packed.stdout)
            self.assertEqual(
                packed_data["reader_sha256"],
                json.loads((self.run_dir / "run.json").read_text())["reader"]["sha256"],
            )
            self.assertTrue((packet / ".gemini/skills/ru-cold-reader/SKILL.md").is_file())

            for role in ("astra", "claude", "gemini_flash", "gemini"):
                self.final_report(role)
                self.call("record", "--run", self.run_rel, "--role", role)

            run = json.loads((self.run_dir / "run.json").read_text())
            self.assertEqual(run["status"], "diagnoses_complete")

            self.final_report("reconciliation")
            self.call("record", "--run", self.run_rel, "--role", "reconciliation")

            self.final_report("author")
            decisions = self.run_dir / "author-decisions.md"
            decisions.write_text(
                decisions.read_text(encoding="utf-8") + "\nDecision: no_changes\n",
                encoding="utf-8",
            )
            self.call("lock-decisions", "--run", self.run_rel)

            self.final_report("verification")
            self.call("record", "--run", self.run_rel, "--role", "verification")
            verified = self.call(
                "verify", "--run", self.run_rel, "--require-complete"
            )
            self.assertEqual(json.loads(verified.stdout)["result"], "passed")

            astra = self.run_dir / "astra-diagnosis.md"
            astra.write_text(astra.read_text(encoding="utf-8") + "changed\n", encoding="utf-8")
            failed = self.call("verify", "--run", self.run_rel, check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("locked report changed", failed.stdout)
        finally:
            shutil.rmtree(packet, ignore_errors=True)

    def test_declared_source_hash_mismatch_stops_init(self):
        source = self.root / "sample/books/book-01/manuscript.md"
        source.write_text(source.read_text(encoding="utf-8") + "change", encoding="utf-8")
        failed = self.call(
            "init",
            "--project",
            "sample",
            "--book",
            "book-01",
            "--run-id",
            "bad-hash",
            check=False,
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("Source hash mismatch", failed.stdout)

    def test_flash_is_required_for_new_runs_and_old_schema_keeps_three_roles(self):
        self.call("init", "--project", "sample", "--book", "book-01", "--run-id", "test-run", "--language", "uk")
        for role in ("astra", "claude", "gemini"):
            self.final_report(role)
            self.call("record", "--run", self.run_rel, "--role", role)
        run_file = self.run_dir / "run.json"
        run = json.loads(run_file.read_text())
        self.assertEqual(run["language"], "uk")
        self.assertNotEqual(run["status"], "diagnoses_complete")
        self.final_report("reconciliation")
        self.assertNotEqual(self.call("record", "--run", self.run_rel, "--role", "reconciliation", check=False).returncode, 0)
        # Historical-schema fixture, not a migration of a real locked run.
        run["schema_version"] = 1
        run.pop("required_diagnoses")
        run.pop("language")
        run["reports"].pop("gemini_flash")
        run_file.write_text(json.dumps(run))
        self.call("record", "--run", self.run_rel, "--role", "reconciliation")
        self.assertEqual(json.loads(self.call("verify", "--run", self.run_rel).stdout)["result"], "passed")


if __name__ == "__main__":
    unittest.main()
