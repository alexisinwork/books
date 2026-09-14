#!/usr/bin/env python3
"""Build exact RU/old-UK/new-UK paragraph alignment and before/after artifacts."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nonempty_paragraphs(path: Path) -> list[str]:
    value = path.read_text(encoding="utf-8")
    if not value.endswith("\n"):
        raise ValueError(f"Projection must end with a newline: {path}")
    return [paragraph for paragraph in value.rstrip("\n").split("\n\n") if paragraph.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--source-docx-path", required=True)
    parser.add_argument("--source-docx-sha256", required=True)
    parser.add_argument("--previous-docx-path", required=True)
    parser.add_argument("--previous-docx-sha256", required=True)
    parser.add_argument("--target-docx", type=Path)
    parser.add_argument("--glossary", type=Path)
    args = parser.parse_args()

    source = nonempty_paragraphs(args.source)
    previous = nonempty_paragraphs(args.previous)
    target = nonempty_paragraphs(args.target)
    if not (len(source) == len(previous) == len(target)):
        raise SystemExit(
            f"Paragraph mismatch: source={len(source)}, previous={len(previous)}, target={len(target)}"
        )

    args.out.mkdir(parents=True, exist_ok=True)
    changed = [index for index, pair in enumerate(zip(previous, target), start=1) if pair[0] != pair[1]]

    source_segments_sha = sha256(args.source)
    previous_segments_sha = sha256(args.previous)
    target_sha = sha256(args.target)
    glossary_sha = sha256(args.glossary) if args.glossary else None

    blocks = []
    alignment_blocks = []
    for index, (ru, before, after) in enumerate(zip(source, previous, target), start=1):
        paragraph_id = f"P{index:03d}"
        blocks.append(
            {
                "source_ids": [paragraph_id],
                "target_paragraphs": [after],
                "alignment_reason": "one-to-one nonempty body-paragraph projection",
            }
        )
        alignment_blocks.append(
            {
                "id": paragraph_id,
                "source_ru": ru,
                "uk_before": before,
                "uk_after": after,
                "changed_from_previous": before != after,
                "sha256": {
                    "source_ru": hashlib.sha256(ru.encode("utf-8")).hexdigest(),
                    "uk_before": hashlib.sha256(before.encode("utf-8")).hexdigest(),
                    "uk_after": hashlib.sha256(after.encode("utf-8")).hexdigest(),
                },
            }
        )

    translation = {
        "schema_version": 1,
        "source_language": "ru",
        "target_language": "uk",
        "source_sha256": args.source_docx_sha256,
        "source_segments_sha256": source_segments_sha,
        "glossary_sha256": glossary_sha,
        "target_sha256": target_sha,
        "coverage": {
            "source_units": len(source),
            "target_units": len(target),
            "status": "complete_exact_once_in_order",
        },
        "blocks": blocks,
    }
    (args.out / "translation.json").write_text(
        json.dumps(translation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    target_docx = None
    if args.target_docx:
        if not args.target_docx.is_file():
            raise SystemExit(f"Target DOCX not found: {args.target_docx}")
        target_docx = {
            "document_path": str(args.target_docx),
            "document_sha256": sha256(args.target_docx),
        }

    alignment = {
        "schema_version": 1,
        "title": args.title,
        "status": "working_revision_for_author_review",
        "source": {
            "document_path": args.source_docx_path,
            "document_sha256": args.source_docx_sha256,
            "projection_path": str(args.source),
            "projection_sha256": source_segments_sha,
        },
        "previous_uk": {
            "document_path": args.previous_docx_path,
            "document_sha256": args.previous_docx_sha256,
            "projection_path": str(args.previous),
            "projection_sha256": previous_segments_sha,
        },
        "target_uk": {
            "projection_path": str(args.target),
            "projection_sha256": target_sha,
            "document": target_docx,
        },
        "coverage": {
            "paragraphs": len(source),
            "changed_from_previous": len(changed),
            "mapping": "one_to_one_nonempty_body_paragraphs",
        },
        "blocks": alignment_blocks,
    }
    (args.out / "alignment.json").write_text(
        json.dumps(alignment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    before_lines = [line + "\n" for line in previous]
    after_lines = [line + "\n" for line in target]
    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=str(args.previous),
        tofile=str(args.target),
    )
    (args.out / "changes.diff").write_text("".join(diff), encoding="utf-8")

    md = [
        f"# Було — стало: {args.title}",
        "",
        f"Попередній UK: `{previous_segments_sha}`.",
        "",
        f"Нова робоча редакція: `{target_sha}`.",
        "",
        f"Змінено {len(changed)} з {len(target)} непорожніх абзаців. Нижче наведено всі змінені абзаци; повний машинний diff збережено в `changes.diff`.",
        "",
    ]
    for index in changed:
        md.extend(
            [
                f"## P{index:03d}",
                "",
                "Було:",
                "",
                "> " + previous[index - 1].replace("\n", "\n> "),
                "",
                "Стало:",
                "",
                "> " + target[index - 1].replace("\n", "\n> "),
                "",
            ]
        )
    (args.out / "БУЛО-СТАЛО.md").write_text("\n".join(md).rstrip() + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "out": str(args.out),
                "paragraphs": len(target),
                "changed": len(changed),
                "target_sha256": target_sha,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
