#!/usr/bin/env python3
"""Build an immutable author reading package from explicitly selected drafts."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "stories-ru-uk-pilot"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main(selection_path, out):
    selection = read(selection_path)
    if out.exists():
        raise ValueError("Choose a new delivery directory")
    books = []
    for chosen in selection["books"]:
        book = PROJECT / "books" / chosen["book_id"]
        edition = book / "editions/uk"
        draft = edition / chosen["draft"]
        target = draft / "target.uk.txt"
        translation = draft / "translation.json"
        data = read(translation)
        packet = edition / "preparation/pilot/ready-v1"
        source = read(packet / "source-segments.json")
        source_docx = ROOT / source["source"]["path"]
        assert sha(source_docx) == data["source_sha256"] == source["source"]["sha256"]
        assert sha(packet / "source-segments.json") == data["source_segments_sha256"]
        assert sha(edition / "glossary.json") == data["glossary_sha256"]
        assert sha(target) == chosen["target_sha256"]
        assert target.read_text() == "\n\n".join(t for b in data["blocks"] for t in b["target_paragraphs"]) + "\n"
        assert [s["id"] for s in source["segments"]] == [i for b in data["blocks"] for i in b["source_ids"]]
        inputs = read(edition / "INPUTS-V1.json")
        for item in inputs["inputs"]:
            assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
        docx = draft / "reader" / chosen["docx_name"]
        export = read(docx.with_suffix(".export.json"))
        render = read(draft / "reader/render/verification.json")
        visual = read(draft / "reader/render/visual-review.json")
        assert sha(docx) == export["docx_sha256"] == visual["docx_sha256"]
        assert export["docx_text_exact"] and visual["result"] == "passed"
        assert export["translation_sha256"] == sha(translation)
        assert render["docx_sha256"] == sha(docx)
        assert render["pdf_text_exact_ignoring_layout_whitespace"]
        checks = read(draft / "final-checks.json")
        assert checks["target_sha256"] == sha(target) and not checks["errors"]
        books.append((chosen, book, draft, source, data, docx, render))
    out.mkdir(parents=True)
    records = []
    for chosen, book, draft, source, data, docx, render in books:
        shutil.copy2(docx, out / docx.name)
        review = out / "Матеріали перевірки" / chosen["title"]
        review.mkdir(parents=True)
        for name in ["target.uk.txt", "translation.json", "ADAPTATION_NOTES.md", "CHANGES.md", "changes.json", "REVIEW-RESOLUTIONS.json", "glossary-addendum.json", "final-checks.json"]:
            path = draft / name
            if path.exists():
                shutil.copy2(path, review / name)
        assessment = book / "editions/uk" / ("QA-ASSESSMENT-" + chosen["draft"].removeprefix("draft-") + ".md")
        if assessment.exists():
            shutil.copy2(assessment, review / "Підсумки перевірки.md")
        by_id = {x["id"]: x for x in source["segments"]}
        rows = []
        for block in data["blocks"]:
            originals = [by_id[i] for i in block["source_ids"]]
            location = ", ".join("p" + str(x["p"]) for x in originals)
            left = "".join("<p>" + html.escape(x["text"]) + "</p>" for x in originals)
            right = "".join("<p>" + html.escape(t) + "</p>" for t in block["target_paragraphs"])
            rows.append(f'<tr><th>{location}</th><td lang="ru">{left}</td><td lang="uk">{right}</td></tr>')
        page = '<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        page += '<title>' + html.escape(chosen["title"]) + ' — порівняння</title>'
        page += '<style>body{font:18px/1.6 Georgia,serif;max-width:1500px;margin:2rem auto;padding:0 1rem;color:#202020}table{border-collapse:collapse;width:100%;table-layout:fixed}th,td{vertical-align:top;border:1px solid #ccc;padding:.7rem}th:first-child{width:3.7rem;font:12px/1.5 sans-serif}td p{margin:0 0 .8rem;white-space:pre-wrap}thead{font-family:sans-serif;background:#f1f3f5}@media print{body{font-size:11pt;margin:0}tr{break-inside:avoid}}</style>'
        page += '<h1>' + html.escape(chosen["title"]) + '</h1><p>Повний російський оригінал і робочий український переклад. Номери позначають абзаци вихідного DOCX.</p>'
        page += '<table><thead><tr><th>Абзац</th><th>Оригінал</th><th>Український переклад</th></tr></thead><tbody>' + "".join(rows) + '</tbody></table></html>\n'
        (review / "Порівняння RU–UK.html").write_text(page, encoding="utf-8")
        records.append({**chosen, "docx_sha256": sha(docx), "source_sha256": data["source_sha256"],
                        "source_units": len(source["segments"]), "target_paragraphs": sum(len(b["target_paragraphs"]) for b in data["blocks"]),
                        "original_path": str(docx.relative_to(ROOT)), "delivered_docx": docx.name})
    manifest = {"schema_version": 1, "status": "complete_working_translations_for_author_reading",
                "required_literary_release_gate": "open", "canonical_approval": False,
                "selection_sha256": sha(selection_path), "books": records}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"out": str(out), "books": len(records), "source_units": sum(r["source_units"] for r in records)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    main(args.selection, args.out)
