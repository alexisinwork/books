#!/usr/bin/env python3
"""Read-only, source-bound Ukrainian naturalness signals, not a grammar verdict."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

from language_qa import SNAP

RULESET_VERSION = "uk-naturalness-1"
BOUNDARY = r"[\w’'ʼ]"
RULES = [
    ("ru_lexical_residue", "lexicon", r"(?:наверно|вообще|конечно|получається|понятно)",
     "Перевірити іншомовний залишок; цитата, діалект або навмисна риса потребує точкового пояснення."),
    ("age_idiom_echo", "idiom", r"(?:тридцятник\s+стукнув|стукнуло\s+тридцять)",
     "Перевірити природність вікової ідіоми; зберегти вік і його приблизність, не міняти факти."),
    ("literal_profanity", "register", r"твою\s+(?:ж\s+)?(?:матір|мать)",
     "Оцінити формулу лайки: адресат, грубість, голос; не додавати діалект або сильнішу лайку автоматично."),
    ("time_na_dvori", "orthography_in_context",
     r"(?:[ivxlcdm\d]+\s+(?:століття|вік)\s+на\s+дворі|на\s+дворі\s+[ivxlcdm\d]+\s+(?:століття|вік))",
     "Якщо йдеться про час, перевірити прислівник надворі; буквальний двір не є цією помилкою."),
    ("technical_dialogue_collocation", "collocation", r"габаритн(?:ий|а|е)\s+виявил(?:ася|ося)|габаритний\s+виявився",
     "Технічне слово не заборонене. Оцінити, чи пасує це сполучення голосу й контексту."),
    ("back_redundancy", "repetition", r"повернул(?:ася|ося|ися|и|ась|ось)|повернув(?:ся|сь)?",
     "Перевірити функцію назад: зайве дублювання, просторовий напрям чи навмисне посилення."),
    ("cognition_root_echo", "repetition", r"розумн[\w’'ʼ]*\s+дум[\w’'ʼ]*[^.!?\n]{0,70}\bрозумом",
     "Спільнокореневий повтор: перевірити жарт/характер/акцент; не вилучати за частотою."),
    ("artist_meme_echo", "idiom", r"художника\s+(?:кожен|кожний)\s+образити\s+може",
     "Оцінити роль творчої натури й комічної формули. Не забороняти слово художник загалом."),
    ("source_formula_echo", "idiom", r"(?:по\s+крайній\s+мірі|в\s+кінці\s+кінців)",
     "Контекстна перевірка усталеної формули, не автоматичний нормативний вирок."),
]


def check(source, resolutions=None):
    source = Path(source)
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    paragraphs, fmt, flags = SNAP.read_source(source, "auto")
    findings = []
    for paragraph in paragraphs:
        value = paragraph["text"]
        for rule, category, pattern, note in RULES:
            if rule == "back_redundancy":
                pattern = "(?:" + pattern + r")\s+(?:б\s+)?назад"
            expression = r"(?<!" + BOUNDARY + ")(?:" + pattern + r")(?!" + BOUNDARY + ")"
            for match in re.finditer(expression, value, re.IGNORECASE):
                findings.append({"rule": rule, "category": category, "p": paragraph["p"],
                                 "start": match.start(), "end": match.end(), "quote": match.group(),
                                 "context": value, "note": note, "decision": "unresolved"})
    findings.sort(key=lambda f: (f["p"], f["start"], f["rule"]))
    lookup = {(f["rule"], f["p"], f["start"], f["quote"]): f for f in findings}
    if resolutions:
        data = json.loads(Path(resolutions).read_text(encoding="utf-8"))
        if data.get("source_sha256") != sha:
            raise ValueError("Resolutions belong to another source hash")
        seen = set()
        for item in data.get("items", []):
            if type(item.get("p")) is not int or type(item.get("start")) is not int:
                raise ValueError("Resolution needs integer paragraph and start offset")
            key = (item.get("rule"), item["p"], item["start"], item.get("quote"))
            if key in seen or key not in lookup:
                raise ValueError("Duplicate or absent exact signal anchor")
            seen.add(key)
            if item.get("decision") not in {"retained_with_reason", "unresolved"} or not str(item.get("reason", "")).strip():
                raise ValueError("A surviving signal needs a reason and retained_with_reason/unresolved decision")
            lookup[key].update(decision=item["decision"], reason=item["reason"])
    unresolved = sum(f["decision"] == "unresolved" for f in findings)
    return {"schema_version": 1, "ruleset": RULESET_VERSION, "source": str(source),
            "source_sha256": sha, "language": "uk", "format": fmt,
            "source_units": len(paragraphs), "extraction_flags": flags,
            "scope": "All extracted body units; selected contextual patterns only, no semantic proof or layout review.",
            "findings": findings, "unresolved_signals": unresolved,
            "result": "signals_require_review" if unresolved else "no_unresolved_configured_signals",
            "grammar_check": "not_run", "literary_quality": "not_established", "automatic_rewriting": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--resolutions", type=Path)
    parser.add_argument("--require-reviewed", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.source, args.resolutions)
        output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8") as stream:
                stream.write(output)
        print(output, end="")
        return 1 if args.require_reviewed and result["unresolved_signals"] else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
