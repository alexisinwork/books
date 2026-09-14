from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
WORK = HERE.parent
FIXTURES = HERE / "fixtures"
MODULE_SPEC = importlib.util.spec_from_file_location(
    "promote_native_candidate", WORK / "promote_native_candidate.py"
)
PROMOTER = importlib.util.module_from_spec(MODULE_SPEC)
assert MODULE_SPEC.loader
MODULE_SPEC.loader.exec_module(PROMOTER)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PromotionTests(unittest.TestCase):
    def make_spec(
        self, root: Path, *, candidate: Path | None = None,
        candidate_changes: Path | None = None, edits=None,
    ) -> Path:
        candidate = candidate or FIXTURES / "candidate" / "translation.json"
        candidate_changes = candidate_changes or FIXTURES / "candidate" / "changes.json"
        edition = root / "edition"
        edition.mkdir(exist_ok=True)
        base = edition / "base-draft"
        if not base.exists():
            shutil.copytree(FIXTURES / "base-draft", base)
        spec = {
            "book_id": "fixture-story",
            "base_draft": str(base),
            "candidate_translation": str(candidate),
            "candidate_changes": str(candidate_changes),
            "translation_units": str(FIXTURES / "TRANSLATION_UNITS.json"),
            "new_draft": str(edition / "new-draft"),
            "record_root": str(WORK),
            "expected_sha256": {
                "base_translation": sha(base / "translation.json"),
                "base_target": sha(base / "target.uk.txt"),
                "candidate_translation": sha(candidate),
                "candidate_changes": sha(candidate_changes),
            },
            "edits": edits if edits is not None else [
                {
                    "source_ids": ["fixture-c000-p000002"],
                    "before": "сірий",
                    "after": "темний",
                    "reason": "Уточнено колір.",
                    "review_id": "review-01",
                },
                {
                    "source_ids": ["fixture-c000-p000002"],
                    "before": "темний камінь",
                    "after": "темний валун",
                    "reason": "Послідовно уточнено предмет.",
                    "review_id": "review-02",
                },
            ],
        }
        path = root / "spec.json"
        path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def test_builds_complete_new_draft_and_full_paragraph_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = self.make_spec(root)
            copied_base = root / "edition" / "base-draft"
            base_hashes_before = {
                path.relative_to(copied_base): sha(path)
                for path in copied_base.rglob("*") if path.is_file()
            }
            output = PROMOTER.promote(spec)
            expected = {
                "translation.json", "target.uk.txt", "changes.json", "CHANGES.md",
                "CHANGES.html", "ADAPTATION_NOTES.md", "alignment.json",
                "prior-files.json", "glossary-addendum.json", "chunks",
            }
            self.assertEqual(expected, {path.name for path in output.iterdir()})
            result = json.loads((output / "translation.json").read_text(encoding="utf-8"))
            self.assertEqual(
                "Другий абзац має темний валун.",
                result["blocks"][1]["target_paragraphs"][1],
            )
            base = json.loads(
                (FIXTURES / "base-draft" / "translation.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                base["blocks"][0]["target_emphasis"],
                result["blocks"][0]["target_emphasis"],
            )
            changes = json.loads((output / "changes.json").read_text(encoding="utf-8"))["changes"]
            self.assertEqual(2, len(changes))
            self.assertEqual("Старий кандидатський вислів.", changes[0]["before"])
            self.assertEqual("Природний кандидатський вислів.", changes[0]["after"])
            self.assertEqual("Другий абзац має сірий камінь.", changes[1]["before"])
            self.assertEqual("Другий абзац має темний валун.", changes[1]["after"])
            self.assertEqual(
                ["review-01", "review-02"],
                [reason["review_id"] for reason in changes[1]["reasons"]],
            )
            self.assertEqual(
                (FIXTURES / "base-draft" / "glossary-addendum.json").read_bytes(),
                (output / "glossary-addendum.json").read_bytes(),
            )
            self.assertEqual(2, len(list((output / "chunks").glob("u*.uk.txt"))))
            self.assertIn("Природний кандидатський вислів.", (output / "chunks/u02.uk.txt").read_text())
            self.assertIn("Старий кандидатський вислів.", (output / "CHANGES.html").read_text())
            self.assertEqual(
                base_hashes_before,
                {path.relative_to(copied_base): sha(path)
                 for path in copied_base.rglob("*") if path.is_file()},
            )

    def test_rejects_non_unique_replacement_without_creating_draft(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            edit = [{
                "source_ids": ["fixture-c000-p000002"],
                "before": "и", "after": "X", "reason": "fixture", "review_id": "r1",
            }]
            spec = self.make_spec(root, edits=edit)
            with self.assertRaisesRegex(PROMOTER.PromotionError, "exactly once"):
                PROMOTER.promote(spec)
            self.assertFalse((root / "edition" / "new-draft").exists())

    def test_replays_nested_edits_and_preserves_each_partial_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = FIXTURES / "candidate-nested"
            output = PROMOTER.promote(self.make_spec(
                root, candidate=directory / "translation.json",
                candidate_changes=directory / "changes.json", edits=[],
            ))
            changes = json.loads((output / "changes.json").read_text())["changes"]
            self.assertEqual(1, len(changes))
            candidate_reasons = [
                reason for reason in changes[0]["reasons"] if reason["origin"] == "candidate"
            ]
            self.assertEqual(
                [
                    "Перша причина окремої часткової правки.",
                    "Друга причина окремої часткової правки.",
                ],
                [reason["reason"] for reason in candidate_reasons],
            )
            self.assertEqual([0, 1], [reason["partial_index"] for reason in candidate_reasons])

    def test_replays_entries_schema_and_preserves_reason(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = FIXTURES / "candidate-entries"
            output = PROMOTER.promote(self.make_spec(
                root, candidate=directory / "translation.json",
                candidate_changes=directory / "changes.json", edits=[],
            ))
            reason = json.loads((output / "changes.json").read_text())["changes"][0]["reasons"][0]
            self.assertEqual("entries", reason["ledger_section"])
            self.assertEqual("Причина з масиву entries збережена.", reason["reason"])

    def test_rejects_changed_protected_emphasis(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = json.loads(
                (FIXTURES / "candidate" / "translation.json").read_text(encoding="utf-8")
            )
            candidate["blocks"][0]["target_emphasis"][0]["italic"] = False
            candidate_path = root / "bad-candidate.json"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            spec = self.make_spec(root, candidate=candidate_path, edits=[])
            with self.assertRaisesRegex(PROMOTER.PromotionError, "target_emphasis"):
                PROMOTER.promote(spec)
            self.assertFalse((root / "edition" / "new-draft").exists())

    def test_rejects_changed_target_paragraph_structure(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = json.loads(
                (FIXTURES / "candidate" / "translation.json").read_text(encoding="utf-8")
            )
            candidate["blocks"][1]["target_paragraphs"] = [
                "Природний кандидатський вислів. Другий абзац має сірий камінь."
            ]
            candidate_path = root / "bad-structure.json"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            spec = self.make_spec(root, candidate=candidate_path, edits=[])
            with self.assertRaisesRegex(PROMOTER.PromotionError, "target_paragraphs structure"):
                PROMOTER.promote(spec)
            self.assertFalse((root / "edition" / "new-draft").exists())

    def test_refuses_existing_destination(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = self.make_spec(root)
            (root / "edition" / "new-draft").mkdir()
            with self.assertRaisesRegex(PROMOTER.PromotionError, "overwrite"):
                PROMOTER.promote(spec)


if __name__ == "__main__":
    unittest.main()
