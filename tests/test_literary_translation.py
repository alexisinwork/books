import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("translation", ROOT / "tools/literary_translation.py")
T = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(T)


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        book = self.root / "sample/books/book-01"
        book.mkdir(parents=True)
        self.source = book / "source.md"
        T.write_new(self.source, "## Глава 1\n\nКай открыл дверь.\nОн увидел 12 звёзд.\n\n## Глава 2\n\nОн закрыл дверь.\n")
        T.write_new(book / "voice.json", {})
        T.write_new(book / "book.json", {"book_id": "book-01", "title": "Test", "voice": "voice.json",
            "master": {"path": "source.md", "sha256": T.digest(self.source), "format": "text", "status": "author_selected"}})
        T.write_new(self.root / "sample/project.json", {"project_id": "sample", "books": [{"id": "book-01", "path": "books/book-01"}]})
        self.inventory = self.root / "sources.json"
        T.inventory(self.root, "sample", self.inventory)
        self.glossary = self.root / "glossary.json"
        T.write_new(self.glossary, {"entries": [{"id": "kai", "source_pattern": "Кай", "preferred": "Кай",
                  "allowed_forms": ["Каю"], "status": "locked", "author_decision": "Synthetic fixture only"}]})
        self.packet = self.root / "packet"
        T.prepare(self.root, self.inventory, "book-01", [1], self.packet, [self.glossary], "uk")
        self.meta, self.segments = T.verify_packet(self.root, self.packet)
        self.translation = self.root / "draft.json"
        self.data = {"schema_version": 1, "source_language": "ru", "target_language": "uk",
                     "source_sha256": T.digest(self.source),
                     "source_segments_sha256": self.meta["source_segments_sha256"],
                     "glossary_sha256": T.digest(self.glossary),
                     "blocks": [{"source_ids": [s["id"]], "target_paragraphs": [target]}
                                for s, target in zip(self.segments, ["Розділ 1", "Кай відчинив двері.", "Він побачив 12 зірок."])]}

    def tearDown(self):
        self.temp.cleanup()

    def save(self, data=None):
        self.translation.write_text(json.dumps(data or self.data, ensure_ascii=False), encoding="utf-8")

    def check(self):
        self.save()
        return T.check_translation(self.root, self.packet, self.translation, self.glossary)

    def test_preparation_preserves_source_and_creates_no_target(self):
        self.assertEqual(T.digest(self.source), self.meta["source"]["sha256"])
        self.assertEqual(sorted(p.name for p in self.packet.iterdir()), ["packet.json", "source-segments.json", "source.ru.txt"])
        self.assertEqual(self.check()["errors"], [])

    def test_split_and_merge_preserve_coverage(self):
        self.data["blocks"][1:] = [{"source_ids": [s["id"] for s in self.segments[1:]],
            "target_paragraphs": ["Кай відчинив двері. Він побачив 12 зірок."], "alignment_reason": "same scene beat"}]
        self.assertEqual(self.check()["errors"], [])
        self.data["blocks"][1]["target_paragraphs"] = ["Кай відчинив двері.", "Він побачив 12 зірок."]
        self.assertEqual(self.check()["errors"], [])
        del self.data["blocks"][1]["alignment_reason"]
        self.assertTrue(self.check()["errors"])

    def test_omission_duplicate_and_reordering_fail(self):
        for operation in [lambda b: b.pop(), lambda b: b.append(copy.deepcopy(b[-1])), lambda b: b.reverse()]:
            original = copy.deepcopy(self.data)
            operation(self.data["blocks"])
            self.assertTrue(self.check()["errors"])
            self.data = original

    def test_wrong_source_projection_and_empty_target_fail(self):
        self.data["source_segments_sha256"] = "0" * 64
        self.assertTrue(self.check()["errors"])
        self.data["source_segments_sha256"] = self.meta["source_segments_sha256"]
        self.data["blocks"][1]["target_paragraphs"] = [""]
        self.assertTrue(self.check()["errors"])

    def test_heading_merge_fails(self):
        self.data["blocks"] = [{"source_ids": [s["id"] for s in self.segments],
                               "target_paragraphs": ["Розділ 1. Кай побачив 12 зірок."], "alignment_reason": "invalid heading merge"}]
        self.assertTrue(any("heading" in e for e in self.check()["errors"]))

    def test_locked_term_and_numerals(self):
        self.data["blocks"][1]["target_paragraphs"] = ["Інша людина відчинила двері."]
        self.assertTrue(any("term absent" in e for e in self.check()["errors"]))
        self.data["blocks"][1]["target_paragraphs"] = ["Кай відчинив двері."]
        self.data["blocks"][2]["target_paragraphs"] = ["Він побачив 13 зірок."]
        result = self.check()
        self.assertEqual(result["errors"], [])
        self.assertTrue(any(w["kind"] == "numerals" for w in result["warnings"]))
        self.assertEqual(result["semantic_review"], "not_run")

    def test_changed_source_and_packet_are_detected(self):
        self.source.write_text("changed", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_CHANGED"):
            T.verify_packet(self.root, self.packet)

    def test_refuses_existing_packet_and_path_escape(self):
        with self.assertRaises(ValueError):
            T.prepare(self.root, self.inventory, "book-01", [1], self.packet, [], "uk")
        with self.assertRaises(ValueError):
            T.contained(self.root, "../outside")

    def test_target_language_pair_checked(self):
        self.data["target_language"] = "en"
        self.assertTrue(self.check()["errors"])

    def test_uk_to_en_uses_uk_source_and_checks_english(self):
        self.source.write_text("## Розділ 1\nКай відчинив двері.\nВін побачив 12 зірок.\n", encoding="utf-8")
        manifest_file = self.source.parent / "book.json"
        manifest = T.read(manifest_file)
        manifest["master"].update(language="uk", sha256=T.digest(self.source))
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
        inventory_file = self.root / "english-prep/sources.json"
        T.inventory(self.root, "sample", inventory_file)
        glossary = self.root / "english-glossary.json"
        T.write_new(glossary, {"entries": [{"id": "kai", "source_pattern": "Кай", "preferred": "Kai",
                    "status": "locked", "author_decision": "Synthetic fixture only"}]})
        packet_dir = self.root / "english-prep/packet"
        T.prepare(self.root, inventory_file, "book-01", [1], packet_dir, [glossary], "en")
        packet, segments = T.verify_packet(self.root, packet_dir)
        self.assertEqual(packet["source_reader_file"], "source.uk.txt")
        self.assertEqual(packet["source_language"], "uk")
        translated = self.root / "english.json"
        data = {"schema_version": 1, "source_language": "uk", "target_language": "en",
                "source_sha256": packet["source"]["sha256"], "source_segments_sha256": packet["source_segments_sha256"],
                "glossary_sha256": T.digest(glossary), "blocks": [
                    {"source_ids": [s["id"]], "target_paragraphs": [t]} for s, t in zip(segments,
                    ["Chapter 1", "Kai opened the door.", "He saw 12 stars."])]}
        T.write_new(translated, data)
        self.assertEqual(T.check_translation(self.root, packet_dir, translated, glossary)["errors"], [])
        run = self.root / "english-run"
        T.freeze(self.root, packet_dir, translated, glossary, run, "test-adapter", "test")
        self.assertEqual(T.verify_run(self.root, run)["target_file"], "english.txt")
        data["blocks"][1]["target_paragraphs"] = ["Кай opened the door."]
        translated.write_text(json.dumps(data), encoding="utf-8")
        self.assertTrue(T.check_translation(self.root, packet_dir, translated, glossary)["errors"])

    def test_unchaptered_story_is_complete_without_invented_heading(self):
        self.source.write_text("Кай открыл дверь.\nОн увидел 12 звёзд.\n", encoding="utf-8")
        book_file = self.source.parent / "book.json"
        book = T.read(book_file)
        book["master"]["sha256"] = T.digest(self.source)
        book_file.write_text(json.dumps(book), encoding="utf-8")
        inventory_file = self.root / "unchaptered" / "sources.json"
        T.inventory(self.root, "sample", inventory_file)
        inventory_book = T.read(inventory_file)["books"][0]
        self.assertEqual(inventory_book["chapter_count"], 0)
        self.assertGreater(inventory_book["ru_lexical_tokens_body"], 0)
        packet_dir = self.root / "unchaptered" / "packet"
        T.prepare(self.root, inventory_file, "book-01", [0], packet_dir, [self.glossary], "uk")
        packet, segments = T.verify_packet(self.root, packet_dir)
        self.assertEqual(packet["chapters"], [0])
        self.assertEqual([p["text"] for p in segments], ["Кай открыл дверь.", "Он увидел 12 звёзд."])
        self.assertTrue(all(p["chapter"] == 0 and not p.get("is_heading") for p in segments))
        self.assertEqual(T.digest(self.source), packet["source"]["sha256"])
        self.data.update(source_sha256=T.digest(self.source),
                         source_segments_sha256=packet["source_segments_sha256"],
                         blocks=[{"source_ids": [s["id"]], "target_paragraphs": [t]}
                                 for s, t in zip(segments, ["Кай відчинив двері.", "Він побачив 12 зірок."])])
        self.save()
        self.assertEqual(T.check_translation(self.root, packet_dir, self.translation, self.glossary)["errors"], [])

    def test_negative_chapter_refused_before_packet_creation(self):
        output = self.root / "invalid-negative"
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            T.prepare(self.root, self.inventory, "book-01", [-1], output, [], "uk")
        self.assertFalse(output.exists())

    def test_freeze_blind_isolation_and_report_lock(self):
        self.save()
        run = self.root / "run"
        T.freeze(self.root, self.packet, self.translation, self.glossary, run, "test-adapter", "test")
        prompt = self.root / "prompt.md"
        T.write_new(prompt, "Читайте лише наданий текст.")
        with tempfile.TemporaryDirectory() as external:
            out = Path(external) / "blind"
            T.blind_pack(self.root, run, prompt, out)
            self.assertEqual(sorted(p.name for p in out.iterdir()), ["READ-ME.md", "REPORT.md", "ukrainian.txt"])
            self.assertEqual(T.digest(out / "ukrainian.txt"), T.digest(run / "ukrainian.txt"))
            report = out / "REPORT.md"
            report.write_text("Status: final\nTarget SHA-256: " + T.digest(run / "ukrainian.txt") +
                              "\n" + "Concrete observation in the declared reading scope. " * 6)
            T.record(self.root, run, "gemini_pro", report, "test-reader", "test")
            with self.assertRaises(ValueError):
                T.record(self.root, run, "gemini_pro", report, "test-reader", "test")
            with self.assertRaisesRegex(ValueError, "bilingual QA"):
                T.record(self.root, run, "reconciliation", report, "test", "test")
        (run / "reports/gemini_pro.md").write_text("tampered")
        with self.assertRaisesRegex(ValueError, "Locked report"):
            T.verify_run(self.root, run)


if __name__ == "__main__":
    unittest.main()
