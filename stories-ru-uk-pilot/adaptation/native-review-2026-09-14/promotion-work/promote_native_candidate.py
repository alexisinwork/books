#!/usr/bin/env python3
"""Promote one reviewed UK candidate into a new, traceable draft.

The command is deliberately narrow: it reads one JSON spec, validates every input
and edit, then atomically creates one previously absent draft directory. It never
updates book manifests, review state, QA state, exports, or an existing draft.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from copy import deepcopy
import difflib
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Iterable


class PromotionError(ValueError):
    """A spec or input violates a promotion invariant."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PromotionError(f"Cannot read JSON {path}: {exc}") from exc


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def resolve_path(spec_dir: Path, value: str, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise PromotionError(f"{label} must be a nonempty path string")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = spec_dir / path
    return path.resolve()


def require_file(path: Path, label: str) -> None:
    if not path.is_file():
        raise PromotionError(f"{label} is not a file: {path}")


def require_sha(path: Path, expected: Any, label: str) -> None:
    if not isinstance(expected, str) or len(expected) != 64:
        raise PromotionError(f"Missing or malformed expected SHA-256 for {label}")
    actual = sha256(path)
    if actual != expected.lower():
        raise PromotionError(
            f"SHA-256 mismatch for {label}: expected {expected.lower()}, got {actual}"
        )


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def target_text(translation: dict[str, Any]) -> str:
    return "\n\n".join(
        paragraph
        for block in translation["blocks"]
        for paragraph in block["target_paragraphs"]
    ) + "\n"


def id_key(block: dict[str, Any]) -> tuple[str, ...]:
    ids = block.get("source_ids")
    if not isinstance(ids, list) or not ids or not all(isinstance(x, str) and x for x in ids):
        raise PromotionError("Every translation block needs nonempty string source_ids")
    return tuple(ids)


def validate_translation_shape(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, dict) or not isinstance(value.get("blocks"), list):
        raise PromotionError(f"{label} must be an object with a blocks array")
    blocks = value["blocks"]
    seen: set[str] = set()
    for block_index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise PromotionError(f"{label} block {block_index} is not an object")
        ids = id_key(block)
        for source_id in ids:
            if source_id in seen:
                raise PromotionError(f"Duplicate source ID in {label}: {source_id}")
            seen.add(source_id)
        paragraphs = block.get("target_paragraphs")
        if not isinstance(paragraphs, list) or not paragraphs or not all(
            isinstance(x, str) for x in paragraphs
        ):
            raise PromotionError(
                f"{label} block {block_index} needs nonempty string target_paragraphs"
            )
    return blocks


def emphasis_signature(block: dict[str, Any]) -> tuple[bool, Any]:
    return "target_emphasis" in block, block.get("target_emphasis")


def validate_emphasis(blocks: Iterable[dict[str, Any]], label: str) -> None:
    for block_index, block in enumerate(blocks):
        if "target_emphasis" not in block:
            continue
        emphasis = block["target_emphasis"]
        if not isinstance(emphasis, list):
            raise PromotionError(f"{label} block {block_index}: target_emphasis is not a list")
        for item_index, item in enumerate(emphasis):
            if not isinstance(item, dict):
                raise PromotionError(
                    f"{label} block {block_index}: emphasis {item_index} is not an object"
                )
            paragraph = item.get("paragraph")
            marked = item.get("text")
            if not isinstance(paragraph, int) or not 0 <= paragraph < len(block["target_paragraphs"]):
                raise PromotionError(
                    f"{label} block {block_index}: emphasis paragraph is out of range"
                )
            if not isinstance(marked, str) or not marked:
                raise PromotionError(f"{label} block {block_index}: emphasis text is empty")
            if marked not in block["target_paragraphs"][paragraph]:
                raise PromotionError(
                    f"{label} block {block_index}: protected emphasis text is absent"
                )


def validate_candidate(base: dict[str, Any], candidate: dict[str, Any]) -> None:
    base_blocks = validate_translation_shape(base, "base translation")
    candidate_blocks = validate_translation_shape(candidate, "candidate translation")
    if set(base) != set(candidate):
        raise PromotionError("Candidate changes translation metadata keys")
    for key in base:
        if key != "blocks" and base[key] != candidate[key]:
            raise PromotionError(f"Candidate changes protected translation metadata {key!r}")
    if len(base_blocks) != len(candidate_blocks):
        raise PromotionError("Candidate changes the number of translation blocks")
    for index, (old, new) in enumerate(zip(base_blocks, candidate_blocks)):
        if id_key(old) != id_key(new):
            raise PromotionError(f"Candidate changes source IDs or block order at block {index}")
        if len(old["target_paragraphs"]) != len(new["target_paragraphs"]):
            raise PromotionError(f"Candidate changes target_paragraphs structure at block {index}")
        if emphasis_signature(old) != emphasis_signature(new):
            raise PromotionError(f"Candidate changes protected target_emphasis at block {index}")
        if set(old) != set(new):
            raise PromotionError(f"Candidate changes block metadata keys at block {index}")
        for key in old:
            if key != "target_paragraphs" and old[key] != new[key]:
                raise PromotionError(f"Candidate changes protected block metadata {key!r} at block {index}")
    validate_emphasis(base_blocks, "base translation")
    validate_emphasis(candidate_blocks, "candidate translation")


def load_candidate_reasons(
    path: Path,
    block_by_ids: dict[tuple[str, ...], int],
    base_blocks: list[dict[str, Any]],
    candidate_blocks: list[dict[str, Any]],
) -> tuple[dict[tuple[int, int], list[dict[str, Any]]], dict[str, Any]]:
    ledger = load_json(path)
    if not isinstance(ledger, dict):
        raise PromotionError("Candidate changes file must be a JSON object")
    section = "changes" if "changes" in ledger else "entries" if "entries" in ledger else None
    records = ledger.get(section) if section else None
    if not isinstance(records, list):
        raise PromotionError("Candidate changes file must contain a changes or entries array")
    reasons: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    replayed = deepcopy(base_blocks)
    for record_index, record in enumerate(records):
        if not isinstance(record, dict):
            raise PromotionError(f"Candidate change {record_index} is not an object")
        ids = record.get("source_ids")
        key = tuple(ids) if isinstance(ids, list) else ()
        if key not in block_by_ids:
            raise PromotionError(f"Candidate change {record_index} names no exact translation block")
        block_index = block_by_ids[key]
        paragraphs = replayed[block_index]["target_paragraphs"]
        nested = record.get("edits")
        if nested is not None:
            if not isinstance(nested, list) or not nested:
                raise PromotionError(f"Candidate change {record_index} has malformed edits")
            group_before = record.get("before")
            if not isinstance(group_before, list) or group_before != paragraphs:
                raise PromotionError(
                    f"Candidate change {record_index} full before does not match replay state"
                )
            partials = nested
        else:
            partials = [record]
        for partial_index, partial in enumerate(partials):
            if not isinstance(partial, dict):
                raise PromotionError(
                    f"Candidate change {record_index} partial {partial_index} is not an object"
                )
            before = partial.get("before")
            after = partial.get("after")
            reason = partial.get("reason")
            if not isinstance(before, str) or not before:
                raise PromotionError(
                    f"Candidate change {record_index} partial {partial_index} has invalid before"
                )
            if not isinstance(after, str) or before == after:
                raise PromotionError(
                    f"Candidate change {record_index} partial {partial_index} has invalid after"
                )
            if not isinstance(reason, str) or not reason.strip():
                raise PromotionError(
                    f"Candidate change {record_index} partial {partial_index} has empty reason"
                )
            count = sum(occurrence_count(paragraph, before) for paragraph in paragraphs)
            if count != 1:
                raise PromotionError(
                    f"Candidate change {record_index} partial {partial_index} before must occur "
                    f"exactly once in ledger order; got {count}"
                )
            paragraph_index = next(
                index for index, paragraph in enumerate(paragraphs) if before in paragraph
            )
            paragraphs[paragraph_index] = paragraphs[paragraph_index].replace(before, after, 1)
            reason_record = {
                "origin": "candidate",
                "ledger_section": section,
                "ledger_index": record_index,
                "partial_index": partial_index,
                "before": before,
                "after": after,
                "reason": reason,
            }
            change_id = partial.get("id", record.get("id"))
            category = partial.get("category", record.get("category"))
            source_quote = partial.get("source_quote", record.get("source_quote"))
            if change_id:
                reason_record["change_id"] = change_id
            if category:
                reason_record["category"] = category
            if source_quote:
                reason_record["source_quote"] = source_quote
            reasons[(block_index, paragraph_index)].append(reason_record)
        if nested is not None:
            group_after = record.get("after")
            if not isinstance(group_after, list) or group_after != paragraphs:
                raise PromotionError(
                    f"Candidate change {record_index} full after does not match replayed partial edits"
                )
    for block_index, (replayed_block, candidate_block) in enumerate(
        zip(replayed, candidate_blocks)
    ):
        if replayed_block["target_paragraphs"] != candidate_block["target_paragraphs"]:
            raise PromotionError(
                f"Candidate ledger does not exactly reproduce candidate block {block_index}"
            )
    return reasons, ledger


def occurrence_count(haystack: str, needle: str) -> int:
    """Count all start positions, including overlapping occurrences."""
    count = 0
    start = 0
    while True:
        position = haystack.find(needle, start)
        if position < 0:
            return count
        count += 1
        start = position + 1


def apply_exact_edits(
    candidate: dict[str, Any],
    edits: Any,
    block_by_ids: dict[tuple[str, ...], int],
) -> tuple[dict[str, Any], dict[tuple[int, int], list[dict[str, Any]]]]:
    if not isinstance(edits, list):
        raise PromotionError("edits must be an array")
    result = deepcopy(candidate)
    reasons: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for edit_index, edit in enumerate(edits):
        if not isinstance(edit, dict):
            raise PromotionError(f"Edit {edit_index} is not an object")
        required = ("source_ids", "before", "after", "reason", "review_id")
        missing = [key for key in required if key not in edit]
        if missing:
            raise PromotionError(f"Edit {edit_index} lacks: {', '.join(missing)}")
        key = tuple(edit["source_ids"]) if isinstance(edit["source_ids"], list) else ()
        if key not in block_by_ids:
            raise PromotionError(f"Edit {edit_index} names no exact translation block")
        before, after = edit["before"], edit["after"]
        if not isinstance(before, str) or not before:
            raise PromotionError(f"Edit {edit_index} has an empty/non-string before")
        if not isinstance(after, str) or before == after:
            raise PromotionError(f"Edit {edit_index} has an invalid after")
        if not isinstance(edit["reason"], str) or not edit["reason"].strip():
            raise PromotionError(f"Edit {edit_index} has an empty reason")
        if not isinstance(edit["review_id"], str) or not edit["review_id"].strip():
            raise PromotionError(f"Edit {edit_index} has an empty review_id")
        block_index = block_by_ids[key]
        paragraphs = result["blocks"][block_index]["target_paragraphs"]
        count = sum(occurrence_count(paragraph, before) for paragraph in paragraphs)
        if count != 1:
            raise PromotionError(
                f"Edit {edit_index} before text must occur exactly once at application time; got {count}"
            )
        paragraph_index = next(index for index, paragraph in enumerate(paragraphs) if before in paragraph)
        paragraphs[paragraph_index] = paragraphs[paragraph_index].replace(before, after, 1)
        reasons[(block_index, paragraph_index)].append(
            {
                "origin": "review_edit",
                "review_id": edit["review_id"],
                "reason": edit["reason"],
                "before": before,
                "after": after,
            }
        )
    return result, reasons


def validate_units(
    units_data: Any, blocks: list[dict[str, Any]], book_id: str
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    if not isinstance(units_data, dict) or not isinstance(units_data.get("units"), list):
        raise PromotionError("TRANSLATION_UNITS must contain a units array")
    if units_data.get("book_id") not in (None, book_id):
        raise PromotionError("TRANSLATION_UNITS book_id does not match spec")
    units = units_data["units"]
    flat_translation = [source_id for block in blocks for source_id in id_key(block)]
    flat_units: list[str] = []
    source_to_unit: dict[str, str] = {}
    unit_ids: set[str] = set()
    for unit_index, unit in enumerate(units, 1):
        if not isinstance(unit, dict) or not isinstance(unit.get("source_ids"), list):
            raise PromotionError(f"Translation unit {unit_index} is malformed")
        unit_id = unit.get("id")
        if not isinstance(unit_id, str) or not unit_id or unit_id in unit_ids:
            raise PromotionError(f"Translation unit {unit_index} has an invalid/duplicate id")
        unit_ids.add(unit_id)
        for source_id in unit["source_ids"]:
            if not isinstance(source_id, str) or source_id in source_to_unit:
                raise PromotionError(f"Duplicate/invalid source ID in units: {source_id!r}")
            source_to_unit[source_id] = unit_id
            flat_units.append(source_id)
    if flat_units != flat_translation:
        raise PromotionError("TRANSLATION_UNITS source IDs do not exactly match translation order")
    for block in blocks:
        containing = {source_to_unit[source_id] for source_id in id_key(block)}
        if len(containing) != 1:
            raise PromotionError("A translation block crosses translation-unit boundaries")
    return units, source_to_unit


def collect_reasons(
    block_index: int,
    paragraph_index: int,
    candidate_reasons: dict[tuple[int, int | None], list[dict[str, Any]]],
    edit_reasons: dict[tuple[int, int], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    raw = (
        candidate_reasons.get((block_index, paragraph_index), [])
        + candidate_reasons.get((block_index, None), [])
        + edit_reasons.get((block_index, paragraph_index), [])
    )
    unique: list[dict[str, Any]] = []
    fingerprints: set[str] = set()
    for reason in raw:
        fingerprint = json.dumps(reason, ensure_ascii=False, sort_keys=True)
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            unique.append(reason)
    return unique


def build_changes(
    base: dict[str, Any],
    result: dict[str, Any],
    candidate_reasons: dict[tuple[int, int | None], list[dict[str, Any]]],
    edit_reasons: dict[tuple[int, int], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for block_index, (old_block, new_block) in enumerate(zip(base["blocks"], result["blocks"])):
        for paragraph_index, (before, after) in enumerate(
            zip(old_block["target_paragraphs"], new_block["target_paragraphs"])
        ):
            if before == after:
                continue
            reasons = collect_reasons(
                block_index, paragraph_index, candidate_reasons, edit_reasons
            )
            if not reasons:
                raise PromotionError(
                    f"Changed block {block_index}, paragraph {paragraph_index} has no recorded reason"
                )
            changes.append(
                {
                    "source_ids": old_block["source_ids"],
                    "block_index": block_index,
                    "target_paragraph_index": paragraph_index,
                    "before": before,
                    "after": after,
                    "before_sha256": text_sha256(before),
                    "after_sha256": text_sha256(after),
                    "reason": " ".join(item["reason"] for item in reasons),
                    "reasons": reasons,
                }
            )
    return changes


def display_path(path: Path, record_root: Path) -> str:
    try:
        return path.relative_to(record_root).as_posix()
    except ValueError:
        return str(path)


def file_ref(path: Path, record_root: Path) -> dict[str, str]:
    return {"path": display_path(path, record_root), "sha256": sha256(path)}


def render_markdown(
    book_id: str, base_name: str, new_name: str, base_sha: str, result_sha: str,
    changes: list[dict[str, Any]], unchanged: int,
) -> str:
    lines = [
        f"# Было — стало: {book_id}", "", f"`{base_name}` → `{new_name}`", "",
        f"До SHA-256: `{base_sha}`.", f"После SHA-256: `{result_sha}`.", "",
    ]
    for number, change in enumerate(changes, 1):
        ids = ", ".join(change["source_ids"])
        lines.extend([
            f"## {number}. {ids} · target paragraph {change['target_paragraph_index']}", "",
            "**Было**", "", change["before"], "", "**Стало**", "", change["after"], "",
            "**Основание:** " + change["reason"], "",
        ])
    lines.append(f"Без изменений: {unchanged} выровненных целевых абзацев.")
    lines.append("")
    return "\n".join(lines)


def render_html(
    book_id: str, base_name: str, new_name: str, changes: list[dict[str, Any]]
) -> str:
    differ = difflib.HtmlDiff(tabsize=4, wrapcolumn=100)
    sections = []
    for number, change in enumerate(changes, 1):
        ids = ", ".join(change["source_ids"])
        table = differ.make_table(
            change["before"].splitlines() or [""],
            change["after"].splitlines() or [""],
            fromdesc="Было", todesc="Стало", context=False, numlines=0,
        )
        sections.append(
            f"<section><h2>{number}. {html.escape(ids)} · target paragraph "
            f"{change['target_paragraph_index']}</h2>"
            f"<details><summary>Дословные полные абзацы</summary>"
            f"<h3>Было</h3><pre>{html.escape(change['before'])}</pre>"
            f"<h3>Стало</h3><pre>{html.escape(change['after'])}</pre></details>{table}"
            f"<p><strong>Основание:</strong> {html.escape(change['reason'])}</p></section>"
        )
    return """<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Exact draft diff</title>
<style>
body{font-family:system-ui,sans-serif;max-width:1400px;margin:2rem auto;padding:0 1rem}
table.diff{width:100%;table-layout:fixed;border-collapse:collapse;margin-bottom:1rem}
.diff_header{background:#eee}.diff_next{display:none}td{vertical-align:top;padding:.25rem;overflow-wrap:anywhere}
.diff_add{background:#d9f7d9}.diff_sub{background:#ffdada}.diff_chg{background:#fff2a8}
</style></head><body>""" + (
        f"<h1>{html.escape(book_id)}</h1><p><code>{html.escape(base_name)}</code> → "
        f"<code>{html.escape(new_name)}</code></p>" + "".join(sections) + "</body></html>\n"
    )


def promote(spec_path: Path) -> Path:
    spec_path = spec_path.resolve()
    spec_dir = spec_path.parent
    spec = load_json(spec_path)
    if not isinstance(spec, dict):
        raise PromotionError("Spec must be a JSON object")
    book_id = spec.get("book_id")
    if not isinstance(book_id, str) or not book_id:
        raise PromotionError("book_id must be a nonempty string")
    base_dir = resolve_path(spec_dir, spec.get("base_draft"), "base_draft")
    new_dir = resolve_path(spec_dir, spec.get("new_draft"), "new_draft")
    candidate_path = resolve_path(
        spec_dir, spec.get("candidate_translation"), "candidate_translation"
    )
    candidate_changes_path = resolve_path(
        spec_dir,
        spec.get("candidate_changes", str(candidate_path.parent / "changes.json")),
        "candidate_changes",
    )
    units_path = resolve_path(
        spec_dir,
        spec.get("translation_units", str(base_dir.parent / "TRANSLATION_UNITS.json")),
        "translation_units",
    )
    record_root = resolve_path(spec_dir, spec.get("record_root", str(spec_dir)), "record_root")
    if not base_dir.is_dir():
        raise PromotionError(f"base_draft is not a directory: {base_dir}")
    if new_dir.exists():
        raise PromotionError(f"Refusing to overwrite existing new_draft: {new_dir}")
    if new_dir.parent != base_dir.parent:
        raise PromotionError("new_draft must be a new sibling of base_draft")
    base_translation_path = base_dir / "translation.json"
    base_target_path = base_dir / "target.uk.txt"
    for path, label in (
        (base_translation_path, "base translation"), (base_target_path, "base target"),
        (candidate_path, "candidate translation"),
        (candidate_changes_path, "candidate changes"), (units_path, "translation units"),
    ):
        require_file(path, label)
    expected = spec.get("expected_sha256")
    if not isinstance(expected, dict):
        raise PromotionError("expected_sha256 must be an object")
    require_sha(base_translation_path, expected.get("base_translation"), "base translation")
    require_sha(base_target_path, expected.get("base_target"), "base target")
    require_sha(candidate_path, expected.get("candidate_translation"), "candidate translation")
    if "candidate_changes" in expected:
        require_sha(candidate_changes_path, expected["candidate_changes"], "candidate changes")

    base = load_json(base_translation_path)
    candidate = load_json(candidate_path)
    validate_candidate(base, candidate)
    if target_text(base) != base_target_path.read_text(encoding="utf-8"):
        raise PromotionError("Base target.uk.txt is not the exact rendering of base translation.json")
    base_blocks = base["blocks"]
    candidate_blocks = candidate["blocks"]
    block_by_ids = {id_key(block): index for index, block in enumerate(base_blocks)}
    candidate_reasons, candidate_ledger = load_candidate_reasons(
        candidate_changes_path, block_by_ids, base_blocks, candidate_blocks
    )
    if isinstance(candidate_ledger, dict) and candidate_ledger.get("book_id") not in (None, book_id):
        raise PromotionError("Candidate changes book_id does not match spec")
    candidate_changed_blocks = {
        index for index, (old, new) in enumerate(zip(base_blocks, candidate_blocks))
        if old["target_paragraphs"] != new["target_paragraphs"]
    }
    reasoned_blocks = {index for index, _ in candidate_reasons}
    missing_reason_blocks = sorted(candidate_changed_blocks - reasoned_blocks)
    if missing_reason_blocks:
        raise PromotionError(
            "Candidate changes lack reasons for changed blocks: "
            + ", ".join(map(str, missing_reason_blocks))
        )
    stale_reason_blocks = sorted(reasoned_blocks - candidate_changed_blocks)
    if stale_reason_blocks:
        raise PromotionError(
            "Candidate changes ledger records unchanged blocks: "
            + ", ".join(map(str, stale_reason_blocks))
        )
    result, edit_reasons = apply_exact_edits(candidate, spec.get("edits", []), block_by_ids)
    validate_candidate(base, result)
    units_data = load_json(units_path)
    units, source_to_unit = validate_units(units_data, result["blocks"], book_id)
    changes = build_changes(base, result, candidate_reasons, edit_reasons)
    result_target = target_text(result)

    total_paragraphs = sum(len(block["target_paragraphs"]) for block in base_blocks)
    unchanged = total_paragraphs - len(changes)
    base_files = sorted(path for path in base_dir.rglob("*") if path.is_file())
    base_refs = [file_ref(path, record_root) for path in base_files]
    input_hashes = {
        "base_translation": sha256(base_translation_path),
        "base_target": sha256(base_target_path),
        "candidate_translation": sha256(candidate_path),
        "candidate_changes": sha256(candidate_changes_path),
        "translation_units": sha256(units_path),
        "spec": sha256(spec_path),
    }

    if not new_dir.parent.is_dir():
        raise PromotionError("Parent edition directory for new_draft does not exist")
    temp_dir = Path(tempfile.mkdtemp(prefix=f".{new_dir.name}.tmp-", dir=new_dir.parent))
    try:
        (temp_dir / "chunks").mkdir()
        (temp_dir / "translation.json").write_bytes(json_bytes(result))
        (temp_dir / "target.uk.txt").write_text(result_target, encoding="utf-8")
        result_hashes = {
            "translation": sha256(temp_dir / "translation.json"),
            "target": sha256(temp_dir / "target.uk.txt"),
        }
        changes_doc = {
            "schema_version": 1,
            "book_id": book_id,
            "from_version": base_dir.name,
            "to_version": new_dir.name,
            "input_sha256": input_hashes,
            "result_sha256": result_hashes,
            "candidate_change_ledger": {
                "path": display_path(candidate_changes_path, record_root),
                "sha256": input_hashes["candidate_changes"],
                "schema_version": candidate_ledger.get("schema_version")
                if isinstance(candidate_ledger, dict) else None,
            },
            "changes": changes,
            "unchanged_target_paragraphs": unchanged,
            "protected_target_emphasis_unchanged": True,
        }
        (temp_dir / "changes.json").write_bytes(json_bytes(changes_doc))
        (temp_dir / "CHANGES.md").write_text(
            render_markdown(
                book_id, base_dir.name, new_dir.name, input_hashes["base_target"],
                result_hashes["target"], changes, unchanged,
            ), encoding="utf-8"
        )
        (temp_dir / "CHANGES.html").write_text(
            render_html(book_id, base_dir.name, new_dir.name, changes), encoding="utf-8"
        )
        notes = [
            f"# Примечания к редакции {new_dir.name}", "",
            f"Книга: `{book_id}`.",
            f"Доставленная база: `{display_path(base_dir, record_root)}`; target SHA-256: `{input_hashes['base_target']}`.",
            f"Проверенный кандидат: `{display_path(candidate_path, record_root)}`; translation SHA-256: `{input_hashes['candidate_translation']}`.",
            f"Итоговый target SHA-256: `{result_hashes['target']}`.", "",
            f"Полных изменённых целевых абзацев: {len(changes)}; неизменённых: {unchanged}.",
            "Причины сведены из журнала кандидата и точечных review edits в spec.",
            "Source IDs, порядок блоков, структура target_paragraphs и protected target_emphasis проверены.",
            "Этот пакет фиксирует сборку редакции; он не присваивает статусы QA, отбора или авторского утверждения.", "",
        ]
        (temp_dir / "ADAPTATION_NOTES.md").write_text("\n".join(notes), encoding="utf-8")

        paragraph_cursor = 0
        alignment_blocks = []
        for block_index, block in enumerate(result["blocks"]):
            paragraph_indexes = list(
                range(paragraph_cursor, paragraph_cursor + len(block["target_paragraphs"]))
            )
            paragraph_cursor += len(block["target_paragraphs"])
            alignment_blocks.append({
                "block_index": block_index,
                "source_ids": block["source_ids"],
                "translation_unit": source_to_unit[block["source_ids"][0]],
                "target_paragraph_indexes": paragraph_indexes,
                "target_paragraph_sha256": [text_sha256(x) for x in block["target_paragraphs"]],
                **({"target_emphasis": block["target_emphasis"]} if "target_emphasis" in block else {}),
            })
        alignment = {
            "schema_version": 1, "book_id": book_id,
            "translation_sha256": result_hashes["translation"],
            "target_sha256": result_hashes["target"],
            "translation_units_sha256": input_hashes["translation_units"],
            "block_count": len(result["blocks"]), "target_paragraph_count": paragraph_cursor,
            "blocks": alignment_blocks,
        }
        (temp_dir / "alignment.json").write_bytes(json_bytes(alignment))

        result_blocks_by_index = {index: block for index, block in enumerate(result["blocks"])}
        source_to_block = {
            source_id: index
            for index, block in result_blocks_by_index.items()
            for source_id in block["source_ids"]
        }
        unit_records = []
        for unit_number, unit in enumerate(units, 1):
            block_indexes: list[int] = []
            for source_id in unit["source_ids"]:
                block_index = source_to_block[source_id]
                if not block_indexes or block_indexes[-1] != block_index:
                    block_indexes.append(block_index)
            reproduced_ids = [
                source_id for index in block_indexes
                for source_id in result_blocks_by_index[index]["source_ids"]
            ]
            if reproduced_ids != unit["source_ids"]:
                raise PromotionError(f"Cannot assemble translation unit {unit['id']} by whole blocks")
            chunk_text = "\n\n".join(
                paragraph for index in block_indexes
                for paragraph in result_blocks_by_index[index]["target_paragraphs"]
            ) + "\n"
            chunk_name = f"u{unit_number:02d}.uk.txt"
            chunk_path = temp_dir / "chunks" / chunk_name
            chunk_path.write_text(chunk_text, encoding="utf-8")
            unit_records.append({
                "unit_id": unit["id"], "file": f"chunks/{chunk_name}",
                "source_ids": unit["source_ids"], "sha256": sha256(chunk_path),
            })
        alignment["units"] = unit_records
        (temp_dir / "alignment.json").write_bytes(json_bytes(alignment))

        prior = {
            "schema_version": 1,
            "base_draft": display_path(base_dir, record_root),
            "base_translation_sha256": input_hashes["base_translation"],
            "base_target_sha256": input_hashes["base_target"],
            "files": base_refs,
            "policy": "All listed base-draft bytes were verified before promotion and must remain unchanged.",
        }
        (temp_dir / "prior-files.json").write_bytes(json_bytes(prior))
        glossary_path = base_dir / "glossary-addendum.json"
        if glossary_path.exists():
            require_file(glossary_path, "base glossary addendum")
            shutil.copyfile(glossary_path, temp_dir / "glossary-addendum.json")

        # Detect concurrent/stale changes immediately before publishing the directory.
        for ref, path in zip(base_refs, base_files):
            if sha256(path) != ref["sha256"]:
                raise PromotionError(f"Base file changed during promotion: {path}")
        if sha256(candidate_path) != input_hashes["candidate_translation"]:
            raise PromotionError("Candidate translation changed during promotion")
        if sha256(candidate_changes_path) != input_hashes["candidate_changes"]:
            raise PromotionError("Candidate changes ledger changed during promotion")
        if new_dir.exists():
            raise PromotionError(f"new_draft appeared during promotion: {new_dir}")
        os.rename(temp_dir, new_dir)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return new_dir


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="one-story promotion spec JSON")
    args = parser.parse_args(argv)
    try:
        result = promote(args.spec)
    except PromotionError as exc:
        print(f"promotion failed: {exc}", file=sys.stderr)
        return 2
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
