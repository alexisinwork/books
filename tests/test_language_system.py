import argparse
import importlib.util
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class LanguageSystemTests(unittest.TestCase):
    def test_standalone_project_carries_language_system_and_helpers(self):
        studio = module("portable_studio_test", ROOT / "default/tools/studio.py")
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "new-project"
            studio.new_project(argparse.Namespace(root=ROOT / "default", id="language-portability-test",
                               title="Test", out=dest))
            manifest = studio.read(dest / "project.json")
            self.assertEqual(manifest["book_system"], "book-system")
            self.assertTrue((dest / "book-system/ADAPTATION/prompts/adapter.md").is_file())
            self.assertNotIn("../BOOK_SYSTEM", (dest / "AGENTS.md").read_text())
            for skill in ["book-showrunner", "book-language-review", "literary-adaptation"]:
                copied = dest / ".agents/skills" / skill / "SKILL.md"
                self.assertTrue(copied.is_file())
                self.assertIn("../../../book-system/", copied.read_text())
                self.assertNotIn("../../../../../book-system", copied.read_text())
            snapshot = studio.read(dest / "SYSTEM-SNAPSHOT.json")
            self.assertFalse((dest / "book-system/audit").exists())
            self.assertFalse((dest / "book-system/CHANGELOG-2026-09-14.md").exists())
            for record in snapshot["files"]:
                self.assertEqual(studio.digest(dest / "book-system" / record["path"]), record["sha256"])
            self.assertTrue((dest / "book-system/ORCHESTRATION.md").is_file())
            helper_paths = {record["path"] for record in snapshot["helpers"]}
            self.assertTrue({"tools/literary_clients.py", "tools/literary_orchestrator.py"} <= helper_paths)
            for record in snapshot["helpers"]:
                self.assertEqual(studio.digest(dest / record["path"]), record["sha256"])
                result = subprocess.run([sys.executable, str(dest / record["path"]), "--help"],
                                        capture_output=True, text=True, cwd=dest)
                self.assertEqual(result.returncode, 0, result.stderr)
            for book_id, language in [("uk-original", None), ("en-original", "en")]:
                studio.new_book(argparse.Namespace(root=dest, id=book_id, title=book_id, profile="custom",
                                type="fiction", differentiation="unspecified", language=language))
                book = studio.read(dest / "books" / book_id / "book.json")
                self.assertEqual(book["original_language"], language or "uk")
                self.assertEqual(book["canonical_language"], language or "uk")
                self.assertIsNone(book["master"])

    def test_ukrainian_letters_apostrophes_and_english_headings(self):
        snapshot = module("snapshot_uk_test", ROOT / "default/skills/ru-book-auditor/scripts/book_snapshot.py")
        self.assertEqual(snapshot.WORD.findall("Їжак ґанок сім'я п’ять обʼєкт"), ["Їжак", "ґанок", "сім'я", "п’ять", "обʼєкт"])
        import re
        for title in ["## Розділ перший", "Епілог", "CHAPTER 1", "Prologue", "Глава 1"]:
            self.assertTrue(re.search(snapshot.CHAPTER, title), title)

    def test_language_signals_do_not_claim_full_grammar_review(self):
        qa = module("qa_test", ROOT / "tools/language_qa.py")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.md"
            path.write_text("Їжак вийшов на ґанок.\nЁжик и мiсто.\n", encoding="utf-8")
            result = qa.check(path, "uk")
            self.assertEqual(result["grammar_check"], "not_run")
            self.assertEqual({f["rule"] for f in result["findings"]}, {"mixed_alphabet", "russian_specific_letter"})

    def test_calque_signal_respects_ukrainian_apostrophes(self):
        qa = module("qa_apostrophe_test", ROOT / "tools/language_qa.py")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.md"
            path.write_text("Він з'являється. Вона з’являється. Воно зʼявляється.\n"
                            "Це являється прикладом. Він приймає участь.\n", encoding="utf-8")
            result = qa.check(path, "uk")
            self.assertEqual([(f["p"], f["quote"]) for f in result["findings"]],
                             [(2, "являється"), (2, "приймає участь")])


if __name__ == "__main__":
    unittest.main()
