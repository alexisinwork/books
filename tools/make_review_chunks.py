#!/usr/bin/env python3
"""Create exact, globally numbered paragraph slices for isolated bilingual review."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paragraphs(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").rstrip("\n").split("\n\n")


def parse_ranges(value: str, total: int) -> list[tuple[int, int]]:
    result: list[tuple[int, int]] = []
    for raw in value.split(","):
        start, end = (int(part) for part in raw.split("-", 1))
        if not (1 <= start <= end <= total):
            raise ValueError(f"Invalid range {raw!r} for {total} paragraphs")
        result.append((start, end))
    covered = [number for start, end in result for number in range(start, end + 1)]
    if covered != list(range(1, total + 1)):
        raise ValueError("Ranges must cover every paragraph exactly once and in order")
    return result


def numbered(items: list[str], start: int, end: int) -> str:
    return "\n\n".join(
        f"P{number:03d}\t{items[number - 1]}" for number in range(start, end + 1)
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--ranges", required=True, help="Comma-separated inclusive ranges")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.out.exists():
        raise ValueError(f"Output directory already exists: {args.out}")
    source = paragraphs(args.source)
    target = paragraphs(args.target)
    if len(source) != len(target):
        raise ValueError(f"Paragraph mismatch: source={len(source)}, target={len(target)}")
    ranges = parse_ranges(args.ranges, len(target))
    args.out.mkdir(parents=True)
    parts = []
    for index, (start, end) in enumerate(ranges, 1):
        part = args.out / f"part-{index:02d}"
        part.mkdir()
        source_path = part / "source.ru.txt"
        target_path = part / "target.uk.txt"
        source_path.write_text(numbered(source, start, end), encoding="utf-8")
        target_path.write_text(numbered(target, start, end), encoding="utf-8")
        parts.append({
            "part": part.name,
            "global_start": start,
            "global_end": end,
            "paragraphs": end - start + 1,
            "source_sha256": sha256(source_path),
            "target_sha256": sha256(target_path),
        })
    manifest = {
        "source": {"path": str(args.source), "sha256": sha256(args.source)},
        "target": {"path": str(args.target), "sha256": sha256(args.target)},
        "paragraphs": len(target),
        "coverage": "complete_exact_once_in_order",
        "parts": parts,
    }
    (args.out / "coverage.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
