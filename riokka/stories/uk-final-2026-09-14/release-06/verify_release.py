#!/usr/bin/env python3
"""Check the four reader files and keep source-bound paragraph/change evidence."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import unicodedata

import fitz
from docx import Document
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "tools"))
from revise_docx_text import body_paragraphs, marked_text, plain  # noqa: E402

STORIES = [
    ("random-experiment", "Випадковий експеримент", None, 48),
    ("history", "Історія", "history-desktop-final.docx", 146),
    ("space-is-no-place-for-the-living", "Космос — не місце для живих", "space-desktop-final.docx", 264),
    ("where-ducks-fly-in-winter", "Куди відлітають качки взимку", "ducks-desktop-final.docx", 253),
]


def sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def normalize(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", value) if not c.isspace() and c != "\u00ad")


def paragraph_values(path: Path) -> list[str]:
    return [marked_text(p) for p in body_paragraphs(Document(path)) if p.text.strip()]


def write_changes(slug: str, label: str, before: list[str], after: list[str], source: Path, target: Path) -> int:
    if len(before) != len(after):
        raise ValueError(f"Non-1:1 paragraphs in {slug}: {len(before)} vs {len(after)}")
    changed = [(n, plain(a), plain(b)) for n, (a, b) in enumerate(zip(before, after), 1) if a != b]
    output = ROOT / slug / f"CHANGES-FROM-{label}.md"
    lines = [f"# Було — стало: {slug}, {label.lower()}", "",
             f"Було: `{source}` · SHA-256 `{sha(source)}`.",
             f"Стало: `{target}` · SHA-256 `{sha(target)}`.",
             f"Змінено абзаців: {len(changed)} з {len(after)}. Нумерація P відповідає повному непорожньому тілу DOCX.", ""]
    for number, old, new in changed:
        lines += [f"## P{number:03d}", "", "**Було**", "", old, "", "**Стало**", "", new, ""]
    output.write_text("\n".join(lines), encoding="utf-8")
    return len(changed)


def verify_pdf(slug: str, title: str, docx: Path, values: list[str]) -> dict:
    pdf = ROOT / slug / "render" / (title + ".pdf")
    document = Document(docx)
    top = document.sections[0].top_margin.pt
    bottom = document.sections[0].bottom_margin.pt
    pages = fitz.open(pdf)
    expected = "\n\n".join(plain(v) for v in values) + "\n"
    rendered = []
    page_checks = []
    for n, page in enumerate(pages, 1):
        body = page.get_text(clip=fitz.Rect(0, top - 2, page.rect.width, page.rect.height - bottom + 2))
        rendered.append(body)
        words = page.get_text("words")
        outside = [w for w in words if w[0] < 0 or w[1] < 0 or w[2] > page.rect.width or w[3] > page.rect.height]
        page_checks.append({"page": n, "body_blank": not body.strip(), "out_of_bounds_words": len(outside), "word_count": len(words)})
    equal = normalize(expected) == normalize("\n".join(rendered))
    if not equal or any(p["body_blank"] or p["out_of_bounds_words"] for p in page_checks):
        raise ValueError(f"PDF text/page check failed: {slug}")
    contacts = []
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    for start in range(0, len(pages), 12):
        selected = list(range(start, min(start + 12, len(pages))))
        sheet = Image.new("RGB", (1120, ((len(selected) + 3) // 4) * 385), "#bdbdbd")
        draw = ImageDraw.Draw(sheet)
        for slot, index in enumerate(selected):
            page = pages[index]
            pix = page.get_pixmap(matrix=fitz.Matrix(260 / page.rect.width, 260 / page.rect.width), alpha=False)
            image = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            x, y = slot % 4 * 280 + 8, slot // 4 * 385 + 24
            sheet.paste(image, (x, y))
            draw.text((x, y - 20), str(index + 1), font=font, fill="black")
        filename = f"contact-{selected[0]+1:03d}-{selected[-1]+1:03d}.png"
        sheet.save(ROOT / slug / "render" / filename)
        contacts.append(filename)
    (ROOT / slug / "render" / "pdf-extracted.txt").write_text("\n".join(rendered), encoding="utf-8")
    visual_path = ROOT / slug / "visual-review.json"
    visual_status = "pending_contact_sheet_inspection"
    if visual_path.exists():
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        if (visual.get("status") == "passed" and visual.get("docx_sha256") == sha(docx)
                and visual.get("pdf_sha256") == sha(pdf) and visual.get("pages") == len(pages)
                and sorted(visual.get("contacts", [])) == sorted(contacts)):
            visual_status = "passed"
        else:
            visual_status = "stale_or_incomplete"
    result = {"pdf": str(pdf.relative_to(ROOT)), "pdf_sha256": sha(pdf), "pages": len(pages),
              "body_text_equal_ignoring_layout_whitespace": equal, "page_checks": page_checks, "contacts": contacts,
              "visual_review": visual_status}
    (ROOT / slug / "render" / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    reports = []
    for slug, title, source_name, count in STORIES:
        target = ROOT / "readers" / (title + ".docx")
        values = paragraph_values(target)
        if len(values) != count:
            raise ValueError(f"Paragraph count changed in {slug}: {len(values)}")
        source = ROOT / "SOURCE" / source_name if source_name else ROOT.parent / "release-05/readers" / (title + ".docx")
        source_values = paragraph_values(source)
        if len(source_values) != count:
            raise ValueError(f"Source paragraph count changed in {slug}")
        desktop_changes = write_changes(slug, "DESKTOP", source_values, values, source, target)
        previous = ROOT.parent / "release-05/readers" / (title + ".docx")
        previous_values = paragraph_values(previous)
        previous_changes = write_changes(slug, "RELEASE-05", previous_values, values, previous, target)
        alignment = {"story": slug, "target_docx_sha256": sha(target), "desktop_source_sha256": sha(source),
                     "previous_release_docx_sha256": sha(previous), "mapping": "1:1 unchanged body paragraph order",
                     "items": [{"p": n, "desktop_uk_sha256": sha256(plain(a).encode()).hexdigest(),
                                "final_uk_sha256": sha256(plain(b).encode()).hexdigest(),
                                "previous_release_uk_sha256": sha256(plain(c).encode()).hexdigest()}
                               for n, (a, b, c) in enumerate(zip(source_values, values, previous_values), 1)]}
        (ROOT / slug / "alignment.json").write_text(json.dumps(alignment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        plain_text = "\n\n".join(plain(v) for v in values) + "\n"
        (ROOT / slug / "reader.uk.txt").write_text(plain_text, encoding="utf-8")
        pdf_report = verify_pdf(slug, title, target, values)
        reports.append({"story": slug, "title": title, "source_docx_sha256": sha(source),
                        "reader_docx_sha256": sha(target), "reader_text_sha256": sha(ROOT / slug / "reader.uk.txt"),
                        "paragraphs": count, "changes_from_desktop": desktop_changes,
                        "changes_from_release_05": previous_changes,
                        "pdf_pages": pdf_report["pages"], "pdf_sha256": pdf_report["pdf_sha256"],
                        "pdf_body_text_exact": True, "visual_review": pdf_report["visual_review"]})
    all_visual = all(item["visual_review"] == "passed" for item in reports)
    report = {"status": "mechanical_and_visual_checks_passed" if all_visual else "mechanical_checks_passed_visual_review_pending",
              "stories": reports,
              "total_paragraphs": sum(item[3] for item in STORIES), "source_unchanged": True}
    (ROOT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
