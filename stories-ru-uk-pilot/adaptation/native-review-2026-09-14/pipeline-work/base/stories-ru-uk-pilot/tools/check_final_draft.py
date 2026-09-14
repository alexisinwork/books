#!/usr/bin/env python3
"""Verify full coverage, immutable inputs and a reader DOCX for one pilot draft."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[2]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(book_id, version):
    edition = ROOT / "stories-ru-uk-pilot/books" / book_id / "editions/uk"
    draft = edition / version
    out = draft / "final-checks.json"
    assert not out.exists(), "Existing checks are immutable"
    tool = module("final_literary_translation", ROOT / "tools/literary_translation.py")
    language = module("final_language_qa", ROOT / "tools/language_qa.py")
    technical = tool.check_translation(ROOT, edition / "preparation/pilot/ready-v1",
                                       draft / "translation.json", edition / "glossary.json")
    linguistic = language.check(draft / "target.uk.txt", "uk")
    assert not technical["errors"]
    assert not linguistic["findings"], "Document legitimate exceptions before final assembly"
    data = read(draft / "translation.json")
    target = draft / "target.uk.txt"
    paragraphs = [t for b in data["blocks"] for t in b["target_paragraphs"]]
    assert target.read_text() == "\n\n".join(paragraphs) + "\n"
    inputs = read(edition / "INPUTS-V1.json")
    for item in inputs["inputs"]:
        assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
    docx_files = list((draft / "reader").glob("*.docx"))
    assert len(docx_files) == 1
    docx = docx_files[0]
    visible = [p for p in Document(docx).paragraphs if p.text.strip()]
    assert [p.text for p in visible] == paragraphs
    emphasis = []
    cursor = 0
    for block in data["blocks"]:
        for item in block.get("target_emphasis", []):
            p = visible[cursor + item.get("paragraph", 0)]
            start = p.text.index(item["text"])
            end = start + len(item["text"])
            offset = 0
            for run in p.runs:
                if offset < end and offset + len(run.text) > start:
                    for prop in ("bold", "italic"):
                        if prop in item:
                            assert getattr(run, prop) is item[prop]
                offset += len(run.text)
            emphasis.append({"source_ids": block["source_ids"], "exact_span_present_and_formatted": True})
        cursor += len(block["target_paragraphs"])
    render = read(draft / "reader/render/verification.json")
    visual = read(draft / "reader/render/visual-review.json")
    assert render["docx_sha256"] == visual["docx_sha256"] == sha(docx)
    assert render["pdf_text_exact_ignoring_layout_whitespace"] and visual["result"] == "passed"
    assert all(not p["blank"] and p["out_of_page_bounds"] == 0 for p in render["page_checks"])
    report = {"book_id": book_id, "draft": version, "target_sha256": sha(target),
              "source_sha256": data["source_sha256"], "translation_sha256": sha(draft / "translation.json"),
              "result": "passed_mechanical_delivery_checks", "errors": [],
              "source_units": sum(len(b["source_ids"]) for b in data["blocks"]),
              "target_paragraphs": len(paragraphs), "frozen_inputs_verified": len(inputs["inputs"]),
              "alignment_and_hash_check": technical, "language_signals": linguistic,
              "warning_kinds": dict(Counter(x["kind"] for x in technical.get("warnings", []))),
              "inline_emphasis": emphasis, "docx_sha256": sha(docx), "pages": render["pages"],
              "docx_text_exact": True, "pdf_text_exact_ignoring_layout_whitespace": True,
              "visual_review_sha256": sha(draft / "reader/render/visual-review.json"),
              "tools": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in
                        [ROOT / "tools/literary_translation.py", ROOT / "tools/language_qa.py", Path(__file__).resolve()]],
              "literary_release_gate": "open; see edition QA assessment; hashes do not prove prose quality"}
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"book_id": book_id, "draft": version, "errors": [], "source_units": report["source_units"], "pages": report["pages"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", required=True)
    parser.add_argument("--draft", required=True)
    args = parser.parse_args()
    check(args.book, args.draft)
