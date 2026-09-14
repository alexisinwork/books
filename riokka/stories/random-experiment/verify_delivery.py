#!/usr/bin/env python3
"""Recheck exact source/edition/copy integrity, never infer literary approval."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from build_edition import BASE, ROOT, sha, tr, write_new


def verify(out):
    if out.exists():
        raise ValueError("Use a new verification report")
    book = json.loads((BASE / "book.json").read_text())
    edition = BASE / book["current_edition"]
    release_dir = edition.parent
    release = json.loads((release_dir / "release.json").read_text())
    for key in ("source", "previous_uk"):
        assert sha(ROOT / book[key]["path"]) == book[key]["sha256"], key
    desktop = Path("/mnt/c/Users/alexi/Desktop/Sol")
    assert sha(desktop / "Случайный эксперимент.docx") == book["source"]["sha256"]
    assert sha(desktop / "Випадковий експеримент — українська версія.docx") == book["previous_uk"]["sha256"]
    target = edition / "ukrainian.txt"
    docx = edition / "Випадковий експеримент — українська редакція.docx"
    assert sha(target) == book["current_text_sha256"] == release["target_text_sha256"]
    assert sha(docx) == book["current_docx_sha256"] == release["target_docx_sha256"]
    texts = target.read_text(encoding="utf-8").splitlines()
    assert [p["text"] for p in tr.extract(docx)[0]] == texts
    ru = [p["text"] for p in tr.extract(ROOT / book["source"]["path"])[0]]
    old = [p["text"] for p in tr.extract(ROOT / book["previous_uk"]["path"])[0]]
    alignment = json.loads((edition / "alignment.json").read_text())
    assert len(texts) == len(ru) == len(old) == len(alignment["blocks"]) == 48
    for i, (a, b, c, row) in enumerate(zip(ru, old, texts, alignment["blocks"]), 1):
        assert (row["id"], row["source_p"], row["target_p"]) == (f"P{i:03}", i, i)
        assert (row["ru"], row["uk_before"], row["uk_after"]) == (a, b, c)
        assert row["source_text_sha256"] == tr.text_digest(a)
        assert row["target_text_sha256"] == tr.text_digest(c)
    with zipfile.ZipFile(ROOT / book["previous_uk"]["path"]) as before, zipfile.ZipFile(docx) as after:
        assert before.namelist() == after.namelist()
        assert all(before.read(n) == after.read(n) for n in before.namelist() if n != "word/document.xml")
    reviews = []
    for receipt in sorted(release_dir.glob("candidate-*/reviews/*/invocation.json")):
        record = json.loads(receipt.read_text())
        folder = receipt.parent
        assert sha(folder / "prompt.txt") == record["prompt_sha256"]
        snapshots = list(folder.glob("runner.py")) + list(folder.parent.glob("runner-v*.py"))
        assert any(sha(p) == record["runner_sha256"] for p in snapshots), str(receipt)
        for ref in record["references"]:
            assert sha(ROOT / ref["file"]) == ref["sha256"]
        candidate = folder.parent.parent
        assert sha(candidate / "ukrainian.txt") == record["target_sha256"]
        payload = (folder / "prompt.txt").read_text(encoding="utf-8")
        assert candidate.joinpath("ukrainian.txt").read_text(encoding="utf-8") in payload
        if record["role"] == "gemini_pro":
            assert record["source_sha256"] is None and not record["references"]
            assert "<SOURCE_TEXT>" not in payload and "<REFERENCE " not in payload
        else:
            assert sha(candidate / "ru-source.txt") == record["source_sha256"]
            assert candidate.joinpath("ru-source.txt").read_text(encoding="utf-8") in payload
        if "report_sha256" in record:
            assert sha(folder / "REPORT.md") == record["report_sha256"]
        reviews.append({"receipt": str(receipt.relative_to(BASE)), "status": record["status"], "requested_model": record["requested_model"], "client": record["client"]})
    copies = []
    for copy in release["desktop_copies"]:
        source, dest = release_dir / copy["source"], Path(copy["target"])
        assert sha(source) == sha(dest), str(dest)
        copies.append({"source": str(source.relative_to(BASE)), "target": str(dest), "sha256": sha(dest)})
    report = {"verified_at": datetime.now(timezone.utc).isoformat(), "verifier_sha256": sha(Path(__file__)),
              "target_text_sha256": sha(target), "target_docx_sha256": sha(docx), "source_files_unchanged": True,
              "desktop_originals_unchanged": True, "paragraphs_verified": 48, "changed_paragraphs": sum(a != b for a, b in zip(old, texts)),
              "alignment_and_docx_exact": True, "non_document_xml_parts_preserved": True,
              "copies": copies, "review_receipts_verified": reviews,
              "result": "integrity_checks_passed", "literary_approval": "not_established", "ensemble": "incomplete_opus_missing"}
    write_new(out, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    verify(parser.parse_args().out)
