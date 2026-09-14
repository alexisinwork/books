import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import uk_naturalness as qa
import language_qa


class NaturalnessTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / "text.txt"

    def text(self, value):
        self.source.write_text(value, encoding="utf-8")
        return qa.check(self.source)

    def test_known_risks_are_contextual_and_never_rewritten(self):
        content = "Тридцятник стукнув!\nТвою ж матір!\nГабаритний виявився.\n"
        result = self.text(content)
        self.assertEqual({f["rule"] for f in result["findings"]},
                         {"age_idiom_echo", "literal_profanity", "technical_dialogue_collocation"})
        self.assertEqual(self.source.read_text(), content)
        self.assertFalse(result["automatic_rewriting"])
        self.assertEqual(result["grammar_check"], "not_run")

    def test_native_forms_and_intentional_register_are_not_blanket_banned(self):
        result = self.text("Треба б знайти. Вона іржала, а він читав мораль.\n"
                           "Художник створив колесо для інсталяції. Габаритний вантаж.\n"
                           "Він з'являється. Вона з’являється. Воно зʼявляється.\n"
                           "Полуниця в процесі переходу в корисні елементи.\n")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["literary_quality"], "not_established")

    def test_time_and_literal_yard_differ(self):
        result = self.text("XXVII століття на дворі!\nНа дворі росте трава.\nНадворі XXVII століття!\n")
        self.assertEqual([(f["p"], f["rule"]) for f in result["findings"]], [(1, "time_na_dvori")])

    def test_praised_but_questionable_collocation_still_gets_reviewed(self):
        result = self.text("Мені цього вистачає поза очі.\nВона говорила поза очі.\nМені з головою вистачає.\n")
        self.assertEqual([(f["p"], f["rule"]) for f in result["findings"]], [(1, "enough_poza_ochi")])

    def test_gaze_instrument_signal_keeps_the_exact_context_and_never_rewrites(self):
        content = ("Чоловіки перезирнулися. Першим зняв маску Андрій, "
                   "глянувши на нього своїми золотавими тонкими зіницями.\n")
        result = self.text(content)
        self.assertEqual(len(result["findings"]), 1)
        finding = result["findings"][0]
        self.assertEqual(finding["rule"], "pupils_as_gaze_instrument")
        self.assertEqual(finding["quote"], "глянувши на нього своїми золотавими тонкими зіницями")
        self.assertEqual(finding["context"], content.rstrip("\n"))
        self.assertEqual(content[finding["start"]:finding["end"]], finding["quote"])
        self.assertEqual(finding["decision"], "unresolved")
        self.assertEqual(self.source.read_text(), content)

    def test_gaze_signal_does_not_ban_pupils_metonymy_slang_or_abstract_nouns(self):
        result = self.text("Він глянув на кота з вузькими зіницями.\n"
                           "Уже дві пари вертикальних зіниць дивилися на веселуна.\n"
                           "Він глянув своїми втомленими очима.\n"
                           "Він глянув на двері. Своїми зіницями він займався пізніше.\n"
                           "Тут коїться якась дичина. Мисливець приніс дичину.\n"
                           "Усі погляди зосередилися на гостеві. Я ціную твою щирість.\n")
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["literary_quality"], "not_established")

    def test_intentional_gaze_image_can_be_retained_at_its_exact_anchor(self):
        result = self.text("Він глянув на нас своїми вузькими зіницями.\n")
        path, _ = self.resolution(result)
        reviewed = qa.check(self.source, path)
        self.assertEqual(reviewed["unresolved_signals"], 0)
        self.assertEqual(reviewed["findings"][0]["decision"], "retained_with_reason")
        self.assertEqual(reviewed["literary_quality"], "not_established")

    def test_repetition_context_and_boundaries(self):
        result = self.text("Вона повернулася б назад. Він повернувся назад.\n"
                           "До таких розумних думок ти ще розумом не доріс.\n"
                           "Переповернуласяназад. Розумом не доріс.\n")
        self.assertEqual([f["rule"] for f in result["findings"]],
                         ["back_redundancy", "back_redundancy", "cognition_root_echo"])

    def resolution(self, result):
        f = result["findings"][0]
        data = {"source_sha256": result["source_sha256"], "items": [
            {k: f[k] for k in ("rule", "p", "start", "quote")}]}
        data["items"][0].update(decision="retained_with_reason", reason="Intentional quoted speech in this scene")
        path = Path(self.folder.name) / "resolutions.json"
        path.write_text(json.dumps(data, ensure_ascii=False))
        return path, data

    def test_exact_local_exception_does_not_hide_second_occurrence(self):
        result = self.text("Твою ж матір! Твою ж матір!\n")
        path, _ = self.resolution(result)
        reviewed = qa.check(self.source, path)
        self.assertEqual(reviewed["unresolved_signals"], 1)

    def test_stale_exception_is_refused(self):
        result = self.text("Твою ж матір!\n")
        path, _ = self.resolution(result)
        self.source.write_text("Твою ж матір! Інша редакція.\n")
        with self.assertRaisesRegex(ValueError, "another source hash"):
            qa.check(self.source, path)

    def test_missing_and_duplicate_anchors_are_refused(self):
        result = self.text("Твою ж матір!\n")
        path, data = self.resolution(result)
        data["items"].append(dict(data["items"][0]))
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): qa.check(self.source, path)
        data["items"] = [data["items"][0]]
        data["items"][0]["quote"] = "not in text"
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): qa.check(self.source, path)

    def test_surviving_signal_cannot_be_marked_fixed(self):
        result = self.text("Твою ж матір!\n")
        path, data = self.resolution(result)
        data["items"][0]["decision"] = "fixed"
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): qa.check(self.source, path)

    def test_cli_gate_and_report_overwrite_protection(self):
        result = self.text("Твою ж матір!\n")
        out = Path(self.folder.name) / "report.json"
        cmd = [sys.executable, str(ROOT / "tools/uk_naturalness.py"), "--source", str(self.source),
               "--require-reviewed", "--out", str(out)]
        run = subprocess.run(cmd, capture_output=True)
        self.assertEqual(run.returncode, 1)
        original = out.read_bytes()
        self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 2)
        self.assertEqual(out.read_bytes(), original)


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / "text.txt"

    def reports(self):
        return [qa.check(self.source), language_qa.check(self.source, "uk")]

    def test_blank_lines_are_explicit_and_do_not_renumber_existing_anchors(self):
        content = "\ufeffТиша.\r\n\r\n \t\r\nТвою ж матір! Твою ж матір!\r\n"
        self.source.write_bytes(content.encode("utf-8"))
        original = self.source.read_bytes()
        for report in self.reports():
            with self.subTest(tool=report.get("ruleset", "language_qa")):
                self.assertEqual(report["source_units"], 4)
                self.assertEqual(report["source_units_including_blank"], 4)
                self.assertEqual(report["nonempty_source_units"], 2)
                self.assertEqual(report["blank_source_units"], 2)
                self.assertEqual(report["source_unit_kind"], "physical_text_line")
                self.assertEqual(report["mechanical_coverage"]["scanned_nonempty_source_units"], 2)
                self.assertEqual(report["reading_coverage"]["status"], "not_assessed_by_this_tool")
                self.assertIsNone(report["reading_coverage"]["reviewed_nonempty_source_units"])
                self.assertEqual(report["source_sha256"], hashlib.sha256(original).hexdigest())
        result = qa.check(self.source)
        self.assertEqual([f["p"] for f in result["findings"]], [4, 4])
        first, second = result["findings"]
        self.assertEqual(first["start"], 0)
        self.assertEqual(second["start"], len("Твою ж матір! "))
        resolutions = Path(self.folder.name) / "resolutions.json"
        resolutions.write_text(json.dumps({"source_sha256": result["source_sha256"], "items": [
            {**{k: first[k] for k in ("rule", "p", "start", "quote")},
             "decision": "retained_with_reason", "reason": "Intentional first occurrence"}]}))
        reviewed = qa.check(self.source, resolutions)
        self.assertEqual(reviewed["unresolved_signals"], 1)
        self.assertEqual(reviewed["findings"][1]["start"], second["start"])
        self.assertEqual(self.source.read_bytes(), original)

    def test_empty_and_whitespace_only_inputs_do_not_become_read_prose(self):
        for content, units in [("", 0), ("\n \t\n", 2)]:
            self.source.write_text(content, encoding="utf-8")
            for report in self.reports():
                with self.subTest(content=content, tool=report.get("ruleset", "language_qa")):
                    self.assertEqual(report["source_units"], units)
                    self.assertEqual(report["blank_source_units"], units)
                    self.assertEqual(report["nonempty_source_units"], 0)
                    self.assertIsNone(report["reading_coverage"]["reviewed_nonempty_source_units"])
                    self.assertEqual(report["grammar_check"], "not_run")

    def test_plain_text_hard_wraps_are_lines_and_not_invented_paragraphs(self):
        self.source.write_text("Речення триває\nна наступному рядку.\n", encoding="utf-8")
        for report in self.reports():
            self.assertEqual(report["source_unit_kind"], "physical_text_line")
            self.assertEqual(report["nonempty_source_units"], 2)
            self.assertNotIn("target_paragraphs", report)

    def test_docx_has_its_own_unit_kind_and_keeps_extraction_limits(self):
        self.source = self.source.with_suffix(".docx")
        document = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                    '<w:body><w:p><w:r><w:t>Тиша.</w:t></w:r></w:p><w:p/>'
                    '<w:p><w:r><w:t xml:space="preserve"> </w:t></w:r></w:p>'
                    '<w:p><w:r><w:t>Твою ж матір!</w:t><w:footnoteReference w:id="1"/>'
                    '</w:r></w:p></w:body></w:document>')
        with zipfile.ZipFile(self.source, "w") as archive:
            archive.writestr("word/document.xml", document)
            archive.writestr("word/footnotes.xml", "<footnotes/>")
        for report in self.reports():
            self.assertEqual(report["source_units"], 4)
            self.assertEqual(report["nonempty_source_units"], 2)
            self.assertEqual(report["source_unit_kind"], "docx_body_paragraph")
            self.assertEqual(report["extraction_flags"]["excluded_parts"], ["word/footnotes.xml"])
            self.assertEqual(report["reading_coverage"]["status"], "not_assessed_by_this_tool")
        self.assertEqual(qa.check(self.source)["findings"][0]["p"], 4)

    def test_legacy_language_exception_survives_blank_unit_accounting(self):
        self.source.write_text("Тиша.\n\nЁжик.\n", encoding="utf-8")
        report = language_qa.check(self.source, "uk")
        self.assertEqual(report["findings"][0]["p"], 3)
        exceptions = Path(self.folder.name) / "exceptions.json"
        exceptions.write_text(json.dumps({"source_sha256": report["source_sha256"], "items": [
            {"rule": "russian_specific_letter", "p": 3, "quote": "Ё", "reason": "Exact quoted name"}]}))
        reviewed = language_qa.check(self.source, "uk", exceptions)
        self.assertEqual(reviewed["findings"], [])
        self.assertEqual(reviewed["documented_exceptions"][0]["p"], 3)
        self.assertEqual(reviewed["nonempty_source_units"], 2)

    def test_resolving_all_signals_does_not_claim_full_reading(self):
        self.source.write_text("Твою ж матір!\n", encoding="utf-8")
        report = qa.check(self.source)
        finding = report["findings"][0]
        resolutions = Path(self.folder.name) / "resolutions.json"
        resolutions.write_text(json.dumps({"source_sha256": report["source_sha256"], "items": [
            {**{k: finding[k] for k in ("rule", "p", "start", "quote")},
             "decision": "retained_with_reason", "reason": "Intentional quoted speech"}],
            "reading_coverage": {"status": "complete", "reviewed_nonempty_source_units": 1}}))
        reviewed = qa.check(self.source, resolutions)
        self.assertEqual(reviewed["unresolved_signals"], 0)
        self.assertEqual(reviewed["reading_coverage"]["status"], "not_assessed_by_this_tool")
        self.assertIsNone(reviewed["reading_coverage"]["reviewed_nonempty_source_units"])
        self.assertEqual(reviewed["literary_quality"], "not_established")

    def test_zero_signal_cli_gate_is_not_a_reading_gate(self):
        self.source.write_text("Він мовчав.\n\nВона теж.\n", encoding="utf-8")
        command = [sys.executable, str(ROOT / "tools/uk_naturalness.py"), "--source", str(self.source),
                   "--require-reviewed"]
        run = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["nonempty_source_units"], 2)
        self.assertEqual(report["reading_coverage"]["status"], "not_assessed_by_this_tool")
        self.assertIsNone(report["reading_coverage"]["reviewed_nonempty_source_units"])


if __name__ == "__main__":
    unittest.main()
