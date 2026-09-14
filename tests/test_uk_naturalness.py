import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import uk_naturalness as qa


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


if __name__ == "__main__":
    unittest.main()
