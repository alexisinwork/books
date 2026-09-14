#!/usr/bin/env python3
"""Read-only uk/en/ru language signals. No automatic rewriting or quality score."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "default/skills/ru-book-auditor/scripts/book_snapshot.py"
if not SNAPSHOT_PATH.is_file():
    SNAPSHOT_PATH = ROOT / "skills/ru-book-auditor/scripts/book_snapshot.py"
SPEC = importlib.util.spec_from_file_location("language_snapshot", SNAPSHOT_PATH)
SNAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAP)


def source_coverage(paragraphs, fmt):
    """Describe extraction and pattern scanning, never infer that prose was read.

    Keep blank units in the legacy count and anchor numbering. In plain text,
    ``p`` is a physical line, which need not be a literary paragraph.
    """
    total = len(paragraphs)
    nonempty = sum(bool(p["text"].strip()) for p in paragraphs)
    return {
        "source_units": total,  # Compatibility alias; includes blank units.
        "source_units_including_blank": total,
        "nonempty_source_units": nonempty,
        "blank_source_units": total - nonempty,
        "source_unit_kind": "physical_text_line" if fmt == "text" else "docx_body_paragraph",
        "anchor_numbering": "p is 1-based and includes blank units; existing offsets are unchanged",
        "mechanical_coverage": {
            "scope": "configured_patterns_in_extracted_body_only",
            "scanned_source_units": total,
            "scanned_nonempty_source_units": nonempty,
        },
        "reading_coverage": {
            "status": "not_assessed_by_this_tool",
            "reviewed_nonempty_source_units": None,
        },
    }


def check(source, language, exceptions=None):
    source = Path(source)
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    paragraphs, fmt, flags = SNAP.read_source(source, "auto")
    exclusions = []
    if exceptions:
        data = json.loads(Path(exceptions).read_text(encoding="utf-8"))
        if data.get("source_sha256") != sha:
            raise ValueError("Language exceptions belong to another source hash")
        exclusions = data.get("items", [])
        for item in exclusions:
            if not all(item.get(key) for key in ("rule", "p", "quote", "reason")):
                raise ValueError("Every exception needs rule, p, exact quote and reason")
            if item["p"] > len(paragraphs) or item["p"] < 1 or item["quote"] not in paragraphs[item["p"] - 1]["text"]:
                raise ValueError("Language exception anchor is absent")
    rules = [("mixed_alphabet", r"[A-Za-zА-Яа-яЁёІіЇїЄєҐґ]+", "Mixed Latin/Cyrillic token: inspect names and intentional notation.")]
    if language == "uk":
        rules += [("russian_specific_letter", r"[ЫыЭэЁёЪъ]", "Inspect source-language residue or intentional quotation."),
                  ("possible_calque", r"(?i)(?<![\w’'ʼ])(?:прийма[\w’'ʼ]*\s+участь|на\s+протязі|являється)(?![\w’'ʼ])", "Context-dependent usage signal, not an automatic error.")]
    elif language == "en":
        rules += [("cyrillic_in_english", r"[А-Яа-яЁёІіЇїЄєҐґ]+", "Inspect untranslated material or intentional quotation.")]
    findings, excluded = [], []
    for paragraph in paragraphs:
        for rule, pattern, note in rules:
            for match in re.finditer(pattern, paragraph["text"]):
                value = match.group()
                if rule == "mixed_alphabet" and not (re.search("[A-Za-z]", value) and re.search("[А-Яа-яЁёІіЇїЄєҐґ]", value)):
                    continue
                entry = {"rule": rule, "p": paragraph["p"], "quote": value, "note": note}
                exception = next((item for item in exclusions if item["rule"] == rule and item["p"] == paragraph["p"]
                                  and item["quote"] == value), None)
                (excluded if exception else findings).append({**entry, **({"reason": exception["reason"]} if exception else {})})
    return {"source": str(source), "source_sha256": sha, "language": language, "format": fmt,
            "scope": "All extracted body units; no layout or linguistic proof of naturalness", "extraction_flags": flags,
            **source_coverage(paragraphs, fmt),
            "lexical_tokens": sum(len(SNAP.WORD.findall(p["text"])) for p in paragraphs),
            "result": "signals_found" if findings else "no_configured_signals", "findings": findings,
            "documented_exceptions": excluded, "literary_review": "not_run", "grammar_check": "not_run"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--language", choices=["uk", "en", "ru"], required=True)
    parser.add_argument("--exceptions", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        result = check(args.source, args.language, args.exceptions)
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            with args.out.open("x", encoding="utf-8") as output:
                output.write(text)
        print(text, end="")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
