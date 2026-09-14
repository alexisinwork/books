#!/usr/bin/env python3
"""Export this 48-turn story without changing the source DOCX or its styling."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import literary_translation as tr


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path, data):
    with path.open("x", encoding="utf-8") as f:
        f.write(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def build(target, out):
    if out.exists():
        raise ValueError("Choose a new edition output; existing runs are immutable")
    book = json.loads((BASE / "book.json").read_text())
    sources = [ROOT / book[key]["path"] for key in ("source", "previous_uk")]
    for key, path in zip(("source", "previous_uk"), sources):
        if sha(path) != book[key]["sha256"]:
            raise ValueError("Source SHA changed: " + str(path))
    ru, old = [[p["text"] for p in tr.extract(p)[0]] for p in sources]
    new = target.read_text(encoding="utf-8").splitlines()
    if not len(ru) == len(old) == len(new) == 48 or any(not p.startswith("— ") for p in new):
        raise ValueError("Expected 48 nonempty, ordered dialogue paragraphs")
    if Counter(re.findall(r"\d+|\b[IVXLCDM]{2,}\b", "\n".join(ru))) != Counter(re.findall(r"\d+|\b[IVXLCDM]{2,}\b", "\n".join(new))):
        raise ValueError("Numerical anchors differ; semantic decision needed")
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(sources[1]) as source_zip:
        xml = source_zip.read("word/document.xml").decode("utf-8")
        tree = ET.fromstring(xml)
        paragraphs = tree.findall("w:body/w:p", ns)
        if len(paragraphs) != 48 or any(len(p.findall("w:r", ns)) != 1 or len(p.findall("w:r/w:t", ns)) != 1 for p in paragraphs):
            raise ValueError("Nonuniform inline styling needs a separate mapping; refusing to flatten it")
        texts = [p.find("w:r/w:t", ns).text or "" for p in paragraphs]
        if texts != old:
            raise ValueError("DOCX XML text differs from source projection")
        pattern = r"(<w:t\b[^>]*>)(.*?)(</w:t>)"
        if len(re.findall(pattern, xml, flags=re.S)) != 48:
            raise ValueError("Unsupported DOCX text topology")
        values = iter(new)
        revised = re.sub(pattern, lambda m: m[1] + escape(next(values)) + m[3], xml, flags=re.S)
        out.mkdir(parents=True)
        docx = out / "Випадковий експеримент — українська редакція.docx"
        with zipfile.ZipFile(docx, "x", compression=zipfile.ZIP_DEFLATED) as result_zip:
            for item in source_zip.infolist():
                result_zip.writestr(item, revised.encode("utf-8") if item.filename == "word/document.xml" else source_zip.read(item.filename))
    extracted = [p["text"] for p in tr.extract(docx)[0]]
    if extracted != new:
        raise ValueError("Saved DOCX does not match the revised text")
    with zipfile.ZipFile(sources[1]) as before_zip, zipfile.ZipFile(docx) as after_zip:
        assert before_zip.namelist() == after_zip.namelist()
        unchanged_parts = all(before_zip.read(n) == after_zip.read(n) for n in before_zip.namelist() if n != "word/document.xml")
    assert unchanged_parts
    clean = "\n".join(new) + "\n"
    write_new(out / "ukrainian.txt", clean)
    write_new(out / "ru-source.txt", "\n".join(ru) + "\n")
    write_new(out / "uk-before.txt", "\n".join(old) + "\n")
    rows = [{"id": f"P{i:03}", "source_p": i, "previous_target_p": i, "target_p": i,
             "ru": a, "uk_before": b, "uk_after": c,
             "source_text_sha256": tr.text_digest(a), "target_text_sha256": tr.text_digest(c)}
            for i, (a, b, c) in enumerate(zip(ru, old, new), 1)]
    changed = [row for row in rows if row["uk_before"] != row["uk_after"]]
    manifest = {"schema_version": 1, "source": book["source"], "previous_target": book["previous_uk"],
                "target_sha256": sha(out / "ukrainian.txt"), "docx_sha256": sha(docx),
                "coverage": "48/48 ordered turns; within-paragraph meaning still requires reading", "blocks": rows}
    write_new(out / "alignment.json", manifest)
    change_md = "# Було — стало\n\nRU та попередній UK збережені в SOURCE. Це редакторські рішення в межах поручення, не окреме схвалення автором кожного варіанта.\n\n"
    for row in changed:
        change_md += f"## {row['id']}\n\nБуло: {row['uk_before']}\n\nСтало: {row['uk_after']}\n\n"
    write_new(out / "БУЛО-СТАЛО.md", change_md)
    report = {"schema_version": 1, "source_ru_sha256": sha(sources[0]), "previous_uk_sha256": sha(sources[1]),
              "target_txt_sha256": sha(out / "ukrainian.txt"), "target_docx_sha256": sha(docx),
              "source_turns": 48, "target_turns": len(new), "changed_turns": len(changed),
              "docx_extraction_exact": extracted == new, "other_docx_parts_byte_preserved": unchanged_parts,
              "paragraph_styles_and_run_properties_preserved": True,
              "numeral_anchor_counts_match": True, "layout_render": "not_run", "independent_reviews": "not_run",
              "canonical_promotion": False, "generator_sha256": sha(Path(__file__))}
    write_new(out / "export-verification.json", report)
    print(json.dumps({"out": str(out), "changed_turns": len(changed), "docx": str(docx), "target_sha256": report["target_txt_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    build(args.target, args.out)
