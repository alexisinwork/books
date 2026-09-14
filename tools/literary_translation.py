#!/usr/bin/env python3
"""Prepare source-bound literary translations; never call a model or translate prose.

Python 3.10+, standard library. All paths inside JSON are repository-relative,
except filenames inside self-contained packets/runs. Outputs refuse overwrite.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = REPO / "default/skills/ru-book-auditor/scripts/book_snapshot.py"
if not SNAPSHOT_PATH.is_file():
    SNAPSHOT_PATH = REPO / "skills/ru-book-auditor/scripts/book_snapshot.py"
SPEC = importlib.util.spec_from_file_location(
    "translation_snapshot", SNAPSHOT_PATH)
SNAP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SNAP)
WORD = SNAP.WORD
SHA = re.compile(r"[0-9a-f]{64}")
ROLES = {"bilingual", "opus", "gemini_flash", "gemini_pro", "reconciliation", "human"}


def now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")


def contained(root, relative):
    root = Path(root).resolve()
    raw = Path(relative)
    result = (root / raw).resolve()
    if raw.is_absolute() or not result.is_relative_to(root) or result == root:
        raise ValueError(f"Path escapes root: {relative}")
    return result


def reference(root, path):
    path = Path(path).resolve()
    return {"path": path.relative_to(Path(root).resolve()).as_posix(), "sha256": digest(path)}


def checked(root, ref):
    path = contained(root, ref["path"])
    if not SHA.fullmatch(ref.get("sha256", "")) or digest(path) != ref["sha256"]:
        raise ValueError(f"SOURCE_HASH_CHANGED: {ref['path']}")
    return path


def extract(path, fmt="auto"):
    paragraphs, actual_format, flags = SNAP.read_source(path, fmt)
    chapter, chapters = 0, []
    for item in paragraphs:
        if re.search(SNAP.CHAPTER, item["text"].strip()):
            chapter += 1
            chapters.append({"chapter": chapter, "heading_p": item["p"], "title_ru": item["text"]})
            item["is_heading"] = True
        item["chapter"] = chapter
        item["text_sha256"] = text_digest(item["text"])
    if actual_format == "docx":
        # Keep inline emphasis as evidence; paragraph IDs remain identical to the
        # existing workspace extractor. The original DOCX is still authoritative.
        with zipfile.ZipFile(path) as archive:
            xml = ET.fromstring(archive.read("word/document.xml"))
        xml_paragraphs = xml.find("w:body", SNAP.NS).findall(".//w:p", SNAP.NS)
        for item, xml_p in zip(paragraphs, xml_paragraphs):
            runs = []
            for run in xml_p.findall(".//w:r", SNAP.NS):
                value = "".join((n.text or "") if n.tag == SNAP.W + "t" else
                                "\t" if n.tag == SNAP.W + "tab" else "\n"
                                for n in run.iter()
                                if n.tag in {SNAP.W + k for k in ("t", "tab", "br", "cr")})
                props = run.find("w:rPr", SNAP.NS)
                traits = {}
                if props is not None:
                    for tag in ("b", "i", "smallCaps", "caps", "vertAlign", "rStyle"):
                        node = props.find("w:" + tag, SNAP.NS)
                        if node is not None:
                            traits[tag] = node.get(SNAP.W + "val", "true")
                if value:
                    runs.append({"text": value, "formatting": traits})
            if any(run["formatting"] for run in runs):
                item["inline_runs"] = runs
    return paragraphs, chapters, flags, actual_format


def source_data(root, source):
    path = checked(root, source)
    return extract(path, source.get("format", "auto"))[0]


def inventory(root, project, out):
    if Path(out).exists():
        raise ValueError("Inventory exists; choose a new snapshot path")
    project_path = contained(root, project)
    project_json = read(project_path / "project.json")
    books = []
    for entry in project_json["books"]:
        book_path = contained(project_path, entry["path"])
        book_file = book_path / "book.json"
        book = read(book_file)
        master = book.get("master")
        if not master or not master.get("path"):
            continue
        path = contained(book_path, master["path"])
        if digest(path) != master["sha256"]:
            raise ValueError(f"Declared master hash mismatch: {path}")
        paragraphs, chapters, flags, fmt = extract(path, master.get("format", "auto"))
        # Master is always the inventory basis. A newer candidate is not promoted.
        basis = {**reference(root, path), "format": fmt, "status": master["status"],
                 "authority": master.get("authority"), "role": "master_inventory",
                 "language": master.get("language", project_json.get("language_policy", {}).get("legacy_existing_source", "ru"))}
        related = []
        for field in ("working_revision", "previous_working_revision"):
            revision = book.get(field)
            if not revision or not revision.get("path"):
                continue
            revision_path = contained(book_path, revision["path"])
            actual = digest(revision_path)
            related.append({**reference(root, revision_path), "role": field,
                            "declared_sha256": revision.get("sha256"),
                            "hash_matches": actual == revision.get("sha256"),
                            "status": revision.get("status"),
                            "author_selected": revision.get("author_selected", False)})
        # Chapter 0 is real source text before the first heading, or the entire
        # body of an unchaptered story. Do not omit it from source word counts.
        body = [p for p in paragraphs if not p.get("is_heading")]
        manifest_copy = Path(out).parent / "source-manifests" / (entry["id"] + ".json")
        write_new(manifest_copy, book_file.read_text(encoding="utf-8"))
        books.append({"book_id": entry["id"], "title_ru": book["title"],
                      "live_book_manifest_at_inventory": reference(root, book_file),
                      "book_manifest": reference(root, manifest_copy), "inventory_source": basis,
                      "pilot_eligible": master["status"] == "author_selected",
                      "translation_source_selected": False,
                      "related_versions": related, "extraction_flags": flags,
                      "chapters": chapters, "chapter_count": len(chapters),
                      "source_units_including_blank": len(paragraphs),
                      "nonempty_source_units": sum(bool(p["text"].strip()) for p in paragraphs),
                      "ru_lexical_tokens_body": sum(len(WORD.findall(p["text"])) for p in body),
                      "voice_source": reference(root, contained(book_path, book["voice"]))})
    data = {"schema_version": 1, "project_id": project_json["project_id"],
            "created_at": now(), "status": "preparation_only", "books": books,
            "coverage": "Mechanical inventory of all registered masters; no full literary reading. "
                        "Markdown source units are physical lines, DOCX units are body paragraphs. "
                        "Chapter numbers are ordinal positions, not parsed display labels.",
            "word_count_method": "Regex lexical tokens, including digits; estimates, not linguistic word counts."}
    write_new(out, data)
    return {"books": len(books), "out": str(out), "result": "prepared_not_translated"}


def annotate_glossary(root, inventory_file, glossary_file, out):
    data = read(glossary_file)
    books = read(inventory_file)["books"]
    sources = [(book, source_data(root, book["inventory_source"])) for book in books]
    for term in data["entries"]:
        pattern = re.compile(term.get("source_pattern", term.get("ru_pattern", "")), re.IGNORECASE)
        occurrences, anchors = [], []
        for book, paragraphs in sources:
            matches = [p for p in paragraphs if pattern.search(p["text"])]
            if not matches:
                continue
            occurrences.append({"book_id": book["book_id"],
                                "source_sha256": book["inventory_source"]["sha256"],
                                "source_units": [p["p"] for p in matches],
                                "chapters": sorted({p["chapter"] for p in matches}),
                                "matched_units": len(matches)})
            # First explicit mention per book. Curated voice/adaptation evidence
            # lives separately and is read in its narrative context.
            p = matches[0]
            match = pattern.search(p["text"])
            start, end = max(0, match.start() - 90), min(len(p["text"]), match.end() + 150)
            anchors.append({"book_id": book["book_id"], **book["inventory_source"],
                            "p": p["p"], "chapter": p["chapter"],
                            "quote_ru": p["text"][start:end], "paragraph_sha256": p["text_sha256"]})
        term["occurrences"] = occurrences
        term["anchors"] = anchors
        term["source_evidence_status"] = "located_not_full_semantic_audit" if anchors else "not_located"
    data["inventory"] = reference(root, inventory_file)
    data["coverage"] = "Curated seed terms located across six registered masters. Not an exhaustive entity audit."
    write_new(out, data)
    return {"entries": len(data["entries"]),
            "not_located": [t["id"] for t in data["entries"] if not t["anchors"]], "out": str(out)}


def prepare(root, inventory_file, book_id, chapters, out, inputs, target_language="uk"):
    if Path(out).exists():
        raise ValueError("Packet output exists; choose a new preparation ID")
    if target_language not in {"uk", "en"}:
        raise ValueError("Target language must be uk or en")
    book = next(b for b in read(inventory_file)["books"] if b["book_id"] == book_id)
    checked(root, book["book_manifest"])
    if not book["pilot_eligible"]:
        raise ValueError("This inventory master is not author-selected; explicitly select its source first")
    source = book["inventory_source"]
    paragraphs = source_data(root, source)
    flags = book["extraction_flags"]
    if any(flags.get(k) for k in ("tbl", "drawing", "txbxContent", "footnoteReference", "endnoteReference")):
        raise ValueError("Non-prose DOCX structures need an explicit extraction plan before packet creation")
    selection = sorted(set(chapters))
    if selection != list(chapters) or not selection or selection[0] < 0:
        raise ValueError("Chapters must be nonnegative, unique and in reading order; 0 selects unheaded text")
    if not set(selection).issubset({p["chapter"] for p in paragraphs}):
        raise ValueError("Requested chapter absent")
    segments = []
    for p in paragraphs:
        if p["chapter"] not in selection or not p["text"].strip():
            continue
        segments.append({"id": f"{book_id}-c{p['chapter']:03d}-p{p['p']:06d}", **p})
    refs = [reference(root, path) for path in inputs]
    # Validate all inputs and extraction before creating any packet files.
    out = Path(out)
    out.mkdir(parents=True)
    write_new(out / "source-segments.json", {"schema_version": 1, "source": source, "segments": segments})
    reader_name = "source." + source.get("language", "ru") + ".txt"
    write_new(out / reader_name, "\n\n".join(p["text"] for p in segments) + "\n")
    packet = {"schema_version": 1, "book_id": book_id, "status": "prepared_not_translated",
              "source": source, "source_language": source.get("language", "ru"),
              "target_language": target_language,
              "book_manifest": book["book_manifest"], "chapters": selection,
              "source_segments_sha256": digest(out / "source-segments.json"),
              "source_reader_file": reader_name,
              "source_reader_sha256": digest(out / reader_name), "inputs": refs,
              "source_segment_count": len(segments),
              "ru_lexical_tokens": sum(len(WORD.findall(p["text"])) for p in segments),
              "extraction_scope": "Nonempty source body units in selected chapters; blank layout units omitted. "
                                  "DOCX inline run emphasis retained in segment records; layout not rendered.",
              "created_at": now()}
    write_new(out / "packet.json", packet)
    return {"out": str(out), "source_segments": len(segments), "status": packet["status"]}


def verify_packet(root, packet_dir):
    packet_dir = Path(packet_dir)
    packet = read(packet_dir / "packet.json")
    checked(root, packet["source"])
    checked(root, packet["book_manifest"])
    for ref in packet["inputs"]:
        checked(root, ref)
    for name, key in (("source-segments.json", "source_segments_sha256"),
                      (packet.get("source_reader_file", "source.ru.txt"), "source_reader_sha256")):
        if digest(contained(packet_dir, name)) != packet[key]:
            raise ValueError(f"Packet projection changed: {name}")
    data = read(packet_dir / "source-segments.json")
    if data["source"] != packet["source"]:
        raise ValueError("Packet source reference disagrees")
    expected = source_data(root, packet["source"])
    expected = [p for p in expected if p["chapter"] in packet["chapters"] and p["text"].strip()]
    actual = data["segments"]
    if len(expected) != len(actual):
        raise ValueError("Projection coverage mismatch")
    for original, segment in zip(expected, actual):
        wanted = {"id": f"{packet['book_id']}-c{original['chapter']:03d}-p{original['p']:06d}", **original}
        if segment != wanted:
            raise ValueError(f"Projection differs from source: p{original['p']}")
    if contained(packet_dir, packet.get("source_reader_file", "source.ru.txt")).read_text(encoding="utf-8") != "\n\n".join(p["text"] for p in actual) + "\n":
        raise ValueError("Reader projection differs from segments")
    return packet, actual


def target_matches(form, text):
    normalized = text.replace("’", "'")
    pattern = r"(?<!\w)" + re.escape(form.replace("’", "'")) + r"(?!\w)"
    return bool(re.search(pattern, normalized, re.IGNORECASE))


def check_translation(root, packet_dir, translation_file, glossary_file):
    packet, source = verify_packet(root, packet_dir)
    data = read(translation_file)
    glossary = read(glossary_file)
    errors, warnings = [], []
    if data.get("schema_version") != 1:
        errors.append("Unsupported translation schema")
    for key in ("source_segments_sha256",):
        if data.get(key) != packet[key]:
            errors.append("Translation bound to another source projection")
    if data.get("source_sha256") != packet["source"]["sha256"]:
        errors.append("Translation bound to another source manuscript")
    if data.get("glossary_sha256") != digest(glossary_file):
        errors.append("Translation bound to another glossary")
    target_language = packet["target_language"]
    if data.get("target_language") != target_language or data.get("source_language") != packet["source_language"]:
        errors.append("Translation language pair disagrees with packet")
    blocks = data.get("blocks")
    if not isinstance(blocks, list):
        raise ValueError("Translation must have a blocks array")
    by_id = {p["id"]: p for p in source}
    expected_ids = list(by_id)
    seen, english = [], []
    for index, block in enumerate(blocks, 1):
        label = f"block {index}"
        ids, targets = block.get("source_ids"), block.get("target_paragraphs")
        if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
            errors.append(f"{label}: nonempty source_ids required")
            continue
        seen.extend(ids)
        if any(i not in by_id for i in ids):
            errors.append(f"{label}: unknown source ID")
            continue
        if not isinstance(targets, list) or not targets or not all(isinstance(t, str) and t.strip() for t in targets):
            errors.append(f"{label}: empty/invalid target")
            continue
        english.extend(targets)
        originals = [by_id[i] for i in ids]
        if len({p["chapter"] for p in originals}) > 1:
            errors.append(f"{label}: alignment crosses chapter boundary")
        if any(p.get("is_heading") for p in originals) and (len(ids) != 1 or len(targets) != 1):
            errors.append(f"{label}: chapter heading must map separately")
        if (len(ids) != 1 or len(targets) != 1) and not str(block.get("alignment_reason", "")).strip():
            errors.append(f"{label}: split/merge needs an alignment_reason")
        ru, en = "\n".join(p["text"] for p in originals), "\n".join(targets)
        if target_language == "en" and re.search(r"[А-Яа-яЁёІіЇїЄєҐґ]", en):
            errors.append(f"{label}: Cyrillic remains in English")
        if target_language == "uk" and re.search(r"[ЫыЭэЁёЪъ]", en):
            warnings.append({"kind": "russian_specific_letters", "block": index})
        ru_words, en_words = len(WORD.findall(ru)), len(WORD.findall(en))
        if ru_words >= 12 and (en_words / ru_words < 0.55 or en_words / ru_words > 2.2):
            warnings.append({"kind": "length_ratio", "block": index, "ratio": round(en_words / ru_words, 3)})
        if Counter(re.findall(r"\d+(?:[.,:]\d+)*", ru)) != Counter(re.findall(r"\d+(?:[.,:]\d+)*", en)):
            warnings.append({"kind": "numerals", "block": index,
                             "note": "Digit-only signal; spelled numbers, decimal conventions and conversions require reading."})
        for term in glossary.get("entries", []):
            if not re.search(term.get("source_pattern", term.get("ru_pattern", "")), ru, re.IGNORECASE):
                continue
            accepted = term.get("preferred", term.get("preferred_en")) if term.get("status") in {"locked", "accepted"} else None
            forms = ([accepted] if accepted else []) + (term.get("allowed_forms", term.get("allowed_en", [])) if accepted else [])
            if accepted and not any(target_matches(form, en) for form in forms):
                errors.append(f"{label}: accepted term absent: {term['id']}")
            if not accepted:
                warnings.append({"kind": "unresolved_term", "block": index, "term_id": term["id"]})
            if accepted and any(target_matches(form, en) for form in term.get("forbidden_forms", term.get("forbidden_en", []))):
                errors.append(f"{label}: forbidden variant: {term['id']}")
    if seen != expected_ids:
        missing = sorted(set(expected_ids) - set(seen))
        duplicates = [key for key, count in Counter(seen).items() if count > 1]
        errors.append(f"Source coverage/order mismatch; missing={missing}; duplicates={duplicates}")
    duplicates_en = [t for t, count in Counter(english).items() if count > 1 and len(WORD.findall(t)) > 8]
    if duplicates_en:
        warnings.append({"kind": "repeated_target", "paragraphs": duplicates_en})
    return {"result": "failed" if errors else "mechanically_checked", "errors": errors, "warnings": warnings,
            "source_sha256": packet["source"]["sha256"], "translation_sha256": digest(translation_file),
            "glossary_sha256": digest(glossary_file), "source_segments": len(source),
            "target_paragraphs": len(english), "semantic_review": "not_run", "literary_review": "not_run",
            "limitation": "ID coverage cannot prove semantic completeness, naturalness or reader interest."}


def freeze(root, packet_dir, translation_file, glossary_file, out, model, client):
    if Path(out).exists():
        raise ValueError("Run exists; use a new run ID")
    report = check_translation(root, packet_dir, translation_file, glossary_file)
    if report["errors"]:
        raise ValueError("Cannot freeze structurally invalid translation: " + "; ".join(report["errors"]))
    data = read(translation_file)
    english = "\n\n".join(t for b in data["blocks"] for t in b["target_paragraphs"]) + "\n"
    packet = read(Path(packet_dir) / "packet.json")
    out = Path(out)
    out.mkdir(parents=True)
    shutil.copyfile(translation_file, out / "translation.json")
    target_name = "english.txt" if packet["target_language"] == "en" else "ukrainian.txt"
    write_new(out / target_name, english)
    write_new(out / "mechanical-check.json", report)
    write_new(out / "run.json", {"schema_version": 1, "created_at": now(), "status": "awaiting_reviews",
                                "packet": reference(root, Path(packet_dir) / "packet.json"),
                                "source": packet["source"], "glossary": reference(root, glossary_file),
                                "translation_sha256": digest(out / "translation.json"),
                                "target_language": packet["target_language"], "target_file": target_name,
                                "target_sha256": digest(out / target_name),
                                "mechanical_check_sha256": digest(out / "mechanical-check.json"),
                                "translator": {"model": model, "client": client}, "reports": {}})
    return {"run": str(out), "status": "awaiting_reviews", "warnings": len(report["warnings"])}


def verify_run(root, run_dir):
    run_dir = Path(run_dir)
    run = read(run_dir / "run.json")
    packet_file = checked(root, run["packet"])
    verify_packet(root, packet_file.parent)
    checked(root, run["source"])
    checked(root, run["glossary"])
    for filename, field in (("translation.json", "translation_sha256"), (run["target_file"], "target_sha256"),
                            ("mechanical-check.json", "mechanical_check_sha256")):
        if digest(run_dir / filename) != run[field]:
            raise ValueError(f"Frozen run changed: {filename}")
    for role, report in run["reports"].items():
        if digest(contained(run_dir, report["file"])) != report["sha256"]:
            raise ValueError(f"Locked report changed: {role}")
    return run


def blind_pack(root, run_dir, prompt_file, out=None):
    run_dir = Path(run_dir)
    run = verify_run(root, run_dir)
    prompt = Path(prompt_file).read_text(encoding="utf-8")
    if run["target_language"] == "en" and re.search(r"[А-Яа-яЁёІіЇїЄєҐґ]", prompt):
        raise ValueError("Blind reader prompt must be English-only")
    if out:
        out = Path(out).resolve()
        if out.is_relative_to(Path(root).resolve()) or Path(root).resolve().is_relative_to(out):
            raise ValueError("Blind packet must be outside the repository")
        if out.exists():
            raise ValueError("Blind packet output already exists")
        out.mkdir(parents=True)
    else:
        out = Path(tempfile.mkdtemp(prefix="books-en-blind-"))
    shutil.copyfile(run_dir / run["target_file"], out / run["target_file"])
    write_new(out / "READ-ME.md", prompt)
    write_new(out / "REPORT.md", f"# Reading report\n\nStatus: draft\nTarget SHA-256: {run['target_sha256']}\n\n")
    return {"out": str(out), "target_sha256": run["target_sha256"],
            "contents": [run["target_file"], "READ-ME.md", "REPORT.md"],
            "instruction": "Start a new reader session in this directory with only these files."}


def record(root, run_dir, role, report_file, model, client):
    run_dir = Path(run_dir)
    run = verify_run(root, run_dir)
    if role not in ROLES or role in run["reports"]:
        raise ValueError("Unknown or already locked role; use a new run for replacement")
    if role == "reconciliation" and not {"bilingual", "opus", "gemini_flash", "gemini_pro"}.issubset(run["reports"]):
        raise ValueError("Reconciliation requires bilingual QA plus Opus, Gemini Flash and Gemini Pro reports")
    report = Path(report_file).read_text(encoding="utf-8")
    if not re.search(r"(?m)^Status:\s*final\s*$", report) or not re.search(
            r"(?m)^Target SHA-256:\s*" + run["target_sha256"] + r"\s*$", report):
        raise ValueError("Report needs Status: final and exact Target SHA-256 metadata")
    body = "\n".join(line for line in report.splitlines()
                     if not line.startswith(("#", "Status:", "Target SHA-256:")))
    if len(body.strip()) < 120:
        raise ValueError("Report contains no substantive review")
    target = run_dir / "reports" / (role + ".md")
    write_new(target, report)
    run["reports"][role] = {"file": f"reports/{role}.md", "sha256": digest(target),
                            "model": model, "client": client, "recorded_at": now()}
    # run.json is mutable bookkeeping; source, translations and reports are frozen.
    temp = run_dir / "run.json.pending"
    write_new(temp, run)
    temp.replace(run_dir / "run.json")
    return {"role": role, "status": "locked", "sha256": digest(target)}


def verify_preparation(root, package):
    package = Path(package)
    sources = read(package / "sources.json")
    for book in sources["books"]:
        checked(root, book["book_manifest"])
        checked(root, book["inventory_source"])
        checked(root, book["voice_source"])
        # Related candidates are historical inventory observations, not chosen
        # translation inputs. They may continue evolving in another work session.
    paragraphs = {book["inventory_source"]["path"]: {p["p"]: p for p in source_data(root, book["inventory_source"])}
                  for book in sources["books"]}
    glossary = read(package / "glossary.json")
    checked(root, glossary["inventory"])
    ids = [t["id"] for t in glossary["entries"]]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate glossary IDs")
    anchors_checked = 0
    for document in [glossary, read(package / "voices.json"), read(package / "adaptation-ledger.json")]:
        for entry in document["entries"]:
            if entry.get("status") in {"accepted", "locked"} and not entry.get("author_decision"):
                raise ValueError(f"Accepted decision without author evidence: {entry['id']}")
            for anchor in entry.get("anchors", []):
                checked(root, anchor)
                table = paragraphs.get(anchor["path"])
                if table is None:
                    table = {p["p"]: p for p in source_data(root, anchor)}
                    paragraphs[anchor["path"]] = table
                p = table[anchor["p"]]
                if anchor["quote_ru"] not in p["text"] or p["chapter"] != anchor["chapter"]:
                    raise ValueError(f"Invalid evidence: {entry['id']}")
                if anchor.get("paragraph_sha256") and p["text_sha256"] != anchor["paragraph_sha256"]:
                    raise ValueError(f"Paragraph evidence changed: {entry['id']}")
                anchors_checked += 1
    for packet_file in sorted((package / "pilot").glob("*/packet.json")):
        verify_packet(root, packet_file.parent)
    return {"result": "passed_preparation_checks", "books": len(sources["books"]),
            "glossary_entries": len(ids), "anchors_checked": anchors_checked,
            "translated_prose": "not_created", "semantic_translation_review": "not_run",
            "reader_response": "not_run", "full_series_entity_audit": "not_run"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=REPO)
    subs = parser.add_subparsers(dest="command", required=True)
    inv = subs.add_parser("inventory")
    inv.add_argument("--project", required=True)
    inv.add_argument("--out", type=Path, required=True)
    ann = subs.add_parser("annotate-glossary")
    for name in ("inventory", "glossary", "out"):
        ann.add_argument("--" + name, type=Path, required=True)
    prep = subs.add_parser("prepare")
    prep.add_argument("--inventory", type=Path, required=True)
    prep.add_argument("--book", required=True)
    prep.add_argument("--chapters", nargs="+", type=int, required=True,
                      help="Source chapter ordinals; 0 selects text before the first heading or an unchaptered story")
    prep.add_argument("--input", type=Path, action="append", default=[])
    prep.add_argument("--target-language", choices=["uk", "en"], default="uk")
    prep.add_argument("--out", type=Path, required=True)
    check = subs.add_parser("check")
    freeze_p = subs.add_parser("freeze")
    for cmd in (check, freeze_p):
        for name in ("packet", "translation", "glossary"):
            cmd.add_argument("--" + name, type=Path, required=True)
    freeze_p.add_argument("--out", type=Path, required=True)
    freeze_p.add_argument("--model", required=True)
    freeze_p.add_argument("--client", required=True)
    blind = subs.add_parser("blind-pack")
    blind.add_argument("--run", type=Path, required=True)
    blind.add_argument("--prompt", type=Path, required=True)
    blind.add_argument("--out", type=Path)
    rec = subs.add_parser("record")
    rec.add_argument("--run", type=Path, required=True)
    rec.add_argument("--role", choices=sorted(ROLES), required=True)
    rec.add_argument("--report", type=Path, required=True)
    rec.add_argument("--model", required=True)
    rec.add_argument("--client", required=True)
    verify = subs.add_parser("verify-run")
    verify.add_argument("--run", type=Path, required=True)
    vp = subs.add_parser("verify-preparation")
    vp.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "inventory":
            result = inventory(args.root, args.project, args.out)
        elif args.command == "annotate-glossary":
            result = annotate_glossary(args.root, args.inventory, args.glossary, args.out)
        elif args.command == "prepare":
            result = prepare(args.root, args.inventory, args.book, args.chapters, args.out, args.input, args.target_language)
        elif args.command == "check":
            result = check_translation(args.root, args.packet, args.translation, args.glossary)
        elif args.command == "freeze":
            result = freeze(args.root, args.packet, args.translation, args.glossary, args.out, args.model, args.client)
        elif args.command == "blind-pack":
            result = blind_pack(args.root, args.run, args.prompt, args.out)
        elif args.command == "record":
            result = record(args.root, args.run, args.role, args.report, args.model, args.client)
        elif args.command == "verify-run":
            verify_run(args.root, args.run)
            result = {"result": "passed_integrity_checks", "literary_quality": "not_established"}
        else:
            result = verify_preparation(args.root, args.package)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("errors") else 0
    except (OSError, ValueError, KeyError, TypeError, StopIteration, zipfile.BadZipFile, ET.ParseError) as exc:
        print(json.dumps({"result": "failed", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
