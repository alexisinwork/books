#!/usr/bin/env python3
"""Collect reproducible structural and language signals for a selected DOCX master."""

from __future__ import annotations

import argparse
import bisect
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from zipfile import ZipFile

from docx import Document
from razdel import sentenize, tokenize


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def paragraph_for_offset(starts: list[int], paragraphs: list[dict], offset: int) -> dict:
    index = bisect.bisect_right(starts, offset) - 1
    return paragraphs[max(index, 0)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--projection", type=Path, required=True)
    parser.add_argument("--languagetool", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    master = args.master.resolve()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    paragraphs = snapshot["paragraphs"]
    projection = args.projection.read_text(encoding="utf-8")

    starts: list[int] = []
    offset = 0
    for paragraph in paragraphs:
        starts.append(offset)
        offset += len(paragraph["text"]) + 1
    if offset != len(projection):
        raise ValueError("Snapshot paragraphs do not reconstruct the projection exactly")

    chapter_stats: dict[int, dict] = {}
    for chapter in range(1, snapshot["chapter_count"] + 1):
        chapter_paragraphs = [p for p in paragraphs if p.get("chapter") == chapter]
        chapter_text = "\n".join(p["text"] for p in chapter_paragraphs)
        words = list(tokenize(chapter_text))
        sentences = list(sentenize(chapter_text))
        chapter_stats[chapter] = {
            "heading": next((p["text"] for p in chapter_paragraphs if p.get("is_heading")), None),
            "paragraphs": len(chapter_paragraphs),
            "nonempty_paragraphs": sum(bool(p["text"].strip()) for p in chapter_paragraphs),
            "lexical_tokens": sum(bool(re.search(r"[A-Za-zА-Яа-яЁё]", item.text)) for item in words),
            "sentences": len(sentences),
            "dialogue_paragraphs": sum(p["text"].lstrip().startswith("—") for p in chapter_paragraphs),
        }

    signal_patterns = {
        "double_space": re.compile(r" {2,}"),
        "missing_space_after_punctuation": re.compile(r"(?<=[А-Яа-яЁё]),(?=[А-Яа-яЁё])"),
        "space_before_punctuation": re.compile(r"[ \t]+[,.!?;:]"),
        "adjacent_repeated_word": re.compile(r"\b([А-Яа-яЁёA-Za-z]{2,})\s+\1\b", re.IGNORECASE),
        "editorial_marker": re.compile(r"\b(?:TODO|FIXME|UNRESOLVED|TBD)\b", re.IGNORECASE),
        "mixed_latin_cyrillic": re.compile(
            r"\b(?=[A-Za-zА-Яа-яЁё-]*[A-Za-z])(?=[A-Za-zА-Яа-яЁё-]*[А-Яа-яЁё])[A-Za-zА-Яа-яЁё-]+\b"
        ),
    }
    mechanical_signals: list[dict] = []
    for paragraph in paragraphs:
        for signal, pattern in signal_patterns.items():
            for match in pattern.finditer(paragraph["text"]):
                mechanical_signals.append(
                    {
                        "signal": signal,
                        "chapter": paragraph.get("chapter"),
                        "p": paragraph["p"],
                        "match": match.group(0),
                        "text": paragraph["text"],
                    }
                )

    document = Document(master)
    with ZipFile(master) as package:
        package_names = set(package.namelist())
        document_xml = package.read("word/document.xml").decode("utf-8")

    revision_tags = {
        tag: len(re.findall(fr"<w:{tag}\b", document_xml))
        for tag in ("ins", "del", "moveFrom", "moveTo", "commentRangeStart", "commentReference")
    }
    section_stats = []
    for number, section in enumerate(document.sections, 1):
        section_stats.append(
            {
                "section": number,
                "page_width_emu": section.page_width,
                "page_height_emu": section.page_height,
                "top_margin_emu": section.top_margin,
                "bottom_margin_emu": section.bottom_margin,
                "left_margin_emu": section.left_margin,
                "right_margin_emu": section.right_margin,
                "header_distance_emu": section.header_distance,
                "footer_distance_emu": section.footer_distance,
            }
        )

    lt_data = json.loads(args.languagetool.read_text(encoding="utf-8"))
    lt_matches = []
    for match in lt_data.get("matches", []):
        paragraph = paragraph_for_offset(starts, paragraphs, match["offset"])
        matched_text = projection[match["offset"] : match["offset"] + match["length"]]
        lt_matches.append(
            {
                "chapter": paragraph.get("chapter"),
                "p": paragraph["p"],
                "category": match["rule"]["category"]["id"],
                "rule": match["rule"]["id"],
                "matched_text": matched_text,
                "message": match["message"],
                "replacements": [item["value"] for item in match.get("replacements", [])[:5]],
            }
        )

    result = {
        "source": {
            "path": str(master),
            "sha256": sha256(master),
            "snapshot_sha256": sha256(args.snapshot),
            "projection_sha256": sha256(args.projection),
        },
        "coverage": {
            "chapters": snapshot["chapter_count"],
            "snapshot_paragraphs": len(paragraphs),
            "docx_paragraphs": len(document.paragraphs),
            "tables": len(document.tables),
            "sections": len(document.sections),
            "lexical_tokens": sum(item["lexical_tokens"] for item in chapter_stats.values()),
            "sentences": sum(item["sentences"] for item in chapter_stats.values()),
        },
        "docx": {
            "package_parts": len(package_names),
            "comments_part": "word/comments.xml" in package_names,
            "footnotes_part": "word/footnotes.xml" in package_names,
            "endnotes_part": "word/endnotes.xml" in package_names,
            "revision_tags": revision_tags,
            "sections": section_stats,
            "heading_paragraphs": [
                {"index": i, "style": p.style.name, "text": p.text}
                for i, p in enumerate(document.paragraphs, 1)
                if p.style.name.lower().startswith(("heading", "заголовок"))
            ],
        },
        "chapters": chapter_stats,
        "mechanical_signals": mechanical_signals,
        "languagetool": {
            "software": lt_data.get("software", {}),
            "warnings": lt_data.get("warnings", {}),
            "total": len(lt_matches),
            "categories": dict(Counter(item["category"] for item in lt_matches)),
            "rules": dict(Counter(item["rule"] for item in lt_matches)),
            "matches": lt_matches,
        },
        "limitations": [
            "Automated signals require manual review in literary context.",
            "DOCX structure inspection does not prove page layout quality.",
            "Headers, footers, notes, and comments are reported by package presence; their visual appearance is not rendered here.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
