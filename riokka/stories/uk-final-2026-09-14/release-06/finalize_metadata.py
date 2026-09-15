#!/usr/bin/env python3
"""Build source-bound release, review and revision metadata after verification."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent
STORY_REVIEW = {
    "history": ("reader.uk.txt", "reviews-r1", {"flash": "REQUIRES REVISION", "pro": "REQUIRES REVISION"}),
    "space-is-no-place-for-the-living": ("final.uk.txt", "reviews-r1", {"flash": "REQUIRES REVISION", "pro": "REQUIRES REVISION"}),
    "where-ducks-fly-in-winter": ("final.uk.txt", "reviews-r3", {"flash": "REQUIRES REVISION", "pro": "PASS"}),
}
RU_SOURCE_SHA = {
    "random-experiment": "ee72030d14bb42bfa714df38e4183d3be14cbeaeb4020a5e2c7d32936e3b4276",
    "history": "6af64dd30c956c89a5484445b7adb1332c31e3ae628f3fafcd523b97204c9022",
    "space-is-no-place-for-the-living": "3bec1f8468a199e445ed453c7b3e34061f1e83175119e1dc2f7e235293f3b0db",
    "where-ducks-fly-in-winter": "3cb15c55923e85db94b4e84ef5f75e58fc2f8e94a4a9a2a4e5c18cfd3d83bb19",
}


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def save(name: str, data: dict) -> None:
    (ROOT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    checks = json.loads((ROOT / "verification.json").read_text(encoding="utf-8"))
    if checks["status"] != "mechanical_and_visual_checks_passed" or checks["total_paragraphs"] != 711:
        raise ValueError("Current four-story verification has not passed")
    reviews = []
    for slug, (target_name, run, verdicts) in STORY_REVIEW.items():
        target = ROOT / slug / target_name
        target_sha = digest(target)
        for model_name, verdict in verdicts.items():
            folder = ROOT / slug / run / model_name
            invocation = json.loads((folder / "invocation.json").read_text(encoding="utf-8"))
            report = folder / "REPORT.md"
            body = report.read_text(encoding="utf-8")
            if (invocation["status"] != "report_returned_pending_manual_validation"
                    or invocation["target_sha256"] != target_sha
                    or f"Target SHA-256: {target_sha}" not in body
                    or not body.startswith("Status: final")
                    or invocation["report_sha256"] != digest(report)):
                raise ValueError(f"Invalid or stale model report: {folder}")
            init = invocation.get("client_init_metadata", [])
            observed_model = init[0].get("model") if init and isinstance(init[0], dict) else None
            reviews.append({"story": slug, "path": str(report.relative_to(ROOT)),
                            "report_sha256": digest(report), "target_sha256": target_sha,
                            "client": "agy", "requested_model": invocation["requested_model"],
                            "client_reported_model": observed_model,
                            "backend_independently_attested": False, "scope": "full target-only story",
                            "verdict": verdict, "manual_reconciliation": "REVIEW-RECONCILIATION.md"})
    review_index = {"current_release": "release-06", "current_model_reports": reviews,
                    "opus": "waived by author for this four-story editorial cycle; not run",
                    "prior_ducks_reports": "reviews-r1 and reviews-r2 are immutable history for archive/ducks-r1.uk.txt and ducks-r2.uk.txt",
                    "note": "Model verdicts are diagnostic, not author decisions or live-reader reactions."}
    save("review-index.json", review_index)
    stories = []
    revisions = []
    for row in checks["stories"]:
        slug = row["story"]
        title = row["title"]
        ru = PARENT / "stories" / slug / "SOURCE/ru.docx"
        if digest(ru) != RU_SOURCE_SHA[slug]:
            raise ValueError(f"Frozen RU source hash changed: {ru}")
        target = ROOT / "readers" / (title + ".docx")
        text = ROOT / slug / "reader.uk.txt"
        pdf = ROOT / slug / "render" / (title + ".pdf")
        if row["reader_docx_sha256"] != digest(target) or row["reader_text_sha256"] != digest(text) or row["pdf_sha256"] != digest(pdf):
            raise ValueError(f"Verification hashes stale: {slug}")
        alignment = json.loads((ROOT / slug / "alignment.json").read_text(encoding="utf-8"))
        edited = [item["p"] for item in alignment["items"] if item["desktop_uk_sha256"] != item["final_uk_sha256"]]
        if len(edited) != row["changes_from_desktop"]:
            raise ValueError(f"Desktop change ledger differs: {slug}")
        stories.append({**row, "reader_docx": str(target.relative_to(ROOT)),
                        "reader_text": str(text.relative_to(ROOT)), "pdf": str(pdf.relative_to(ROOT)),
                        "ru_source_docx_sha256": digest(ru), "edited_paragraphs_from_desktop": edited,
                        "desktop_source": "SOURCE/" + ("history-desktop-final.docx" if slug == "history" else "space-desktop-final.docx" if slug.startswith("space") else "ducks-desktop-final.docx") if slug != "random-experiment" else "release-05/readers/Випадковий експеримент.docx"})
        revisions.append({"story": slug, "old_desktop_source_sha256": row["source_docx_sha256"],
                          "previous_release_docx_sha256": alignment["previous_release_docx_sha256"],
                          "new_reader_docx_sha256": row["reader_docx_sha256"],
                          "new_reader_text_sha256": row["reader_text_sha256"],
                          "edited_paragraphs_from_desktop": edited,
                          "exact_comparisons": [f"{slug}/CHANGES-FROM-DESKTOP.md", f"{slug}/CHANGES-FROM-RELEASE-05.md"],
                          "decision_basis": "AUTHOR_INTENT.md and MEANING_LEDGER.json" if slug in {"space-is-no-place-for-the-living", "where-ducks-fly-in-winter"} else "Author-selected desktop DOCX imported unchanged" if slug == "history" else "Reused release-05 unchanged"})
    now = datetime.now(timezone.utc).isoformat()
    save("revision-log.json", {"run": "release-06", "created_utc": now, "scope": "four standalone Ukrainian stories", "entries": revisions,
                               "dependencies": ["stories/*/uk.txt", "stories/*/book.json", "riokka/stories/*/book.json", "CONTEXT.md", "audit/issues.json", "alignment.json", "DOCX/PDF", "desktop delivery"],
                               "old_versions_preserved": True})
    save("release.json", {"release": "release-06", "created_utc": now,
                          "role": "author-selected desktop final reading copy after answer import; UA_CANONICAL_MASTER not promoted",
                          "language": "uk", "stories": stories, "total_body_paragraphs": 711,
                          "author_intent_sha256": digest(ROOT / "AUTHOR_INTENT.md"),
                          "meaning_ledger_sha256": digest(ROOT / "MEANING_LEDGER.json"),
                          "verification_sha256": digest(ROOT / "verification.json"),
                          "review_index_sha256": digest(ROOT / "review-index.json"),
                          "questions_answered_sha256": digest(ROOT / "Питання до автора — відповіді.md"),
                          "source_originals_preserved": True, "previous_release": "release-05"})
    save("final-gate.json", {"status": "ready_for_author_reading_with_documented_open_editorial_issues",
                             "release": "release-06", "verification": "mechanical_and_visual_checks_passed",
                             "verified_file_sha256": {row["story"]: row["reader_docx_sha256"] for row in stories},
                             "literary_review": "six current full target-only Gemini reports returned; not all verdicts PASS",
                             "open_issue_ids": ["S-HOLE-PUSH-TRANSMISSION", "D-PAIN-RULE", "D-PRIVATE-FACULTY", "H-AUTHOR-FINAL-TARGET-ONLY"],
                             "publication_canon_promoted": False,
                             "opus": "not run under author waiver; no PASS claim", "language_tool": "not run", "audio_reading": "not run"})
    print("release-06 metadata built: four stories, six current model reports, 711 body paragraphs")


if __name__ == "__main__":
    main()
