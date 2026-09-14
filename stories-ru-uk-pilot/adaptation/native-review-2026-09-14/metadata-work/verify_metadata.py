#!/usr/bin/env python3
"""Verify and record the bounded three-story metadata update."""

import difflib
import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[3]
ROOT = PROJECT.parent
WORK = PROJECT / "adaptation/native-review-2026-09-14/metadata-work"
BEFORE = WORK / "before"
CONFIG = {
    "story-01-reptiloids": ("draft-v4", "draft-v5", "INPUTS-V3.json", "ready-v3", "QA-ASSESSMENT-v5.md"),
    "story-02-fair-killer": ("draft-v3", "draft-v4", "INPUTS-V3.json", "ready-v3", "QA-ASSESSMENT-v4.md"),
    "story-03-chaos-logic": ("draft-v4", "draft-v7", "INPUTS-V4.json", "ready-v4", "QA-ASSESSMENT-v7.md"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    checks = []
    before_manifest = load(BEFORE / "MANIFEST.json")
    for item in before_manifest["files"]:
        assert sha(BEFORE / item["path"]) == item["sha256"]
    checks.append({"check": "before_snapshot", "result": "passed", "files": len(before_manifest["files"])})

    diff_paths = []
    for book_id, (old, new, inputs, ready, qa) in CONFIG.items():
        book_dir = PROJECT / "books" / book_id
        edition = book_dir / "editions/uk"
        draft = edition / new
        prose_record = load(WORK / f"prose-hashes-{book_id}.json")["files"][book_id]
        current_prose = {name: sha(draft / name) for name in prose_record}
        assert current_prose == prose_record
        translation = load(draft / "translation.json")
        rendered = "\n\n".join(
            paragraph for block in translation["blocks"] for paragraph in block["target_paragraphs"]
        ) + "\n"
        assert rendered == (draft / "target.uk.txt").read_text(encoding="utf-8")
        continuity = load(draft / "continuity.json")
        predecessor = edition / old / "continuity.json"
        assert continuity["predecessor"]["sha256"] == sha(predecessor)
        assert continuity["source_registers"] == load(predecessor)["source_registers"]
        assert continuity["target_sha256"] == current_prose["target.uk.txt"]
        assert continuity["translation_sha256"] == current_prose["translation.json"]
        assert continuity["current_check_summary"]["result"] == "passed"
        assert all(item["result"] == "passed" for item in continuity["current_anchor_checks"])
        assert all(item["result"] == "passed" for item in continuity["current_protected_checks"])
        assert all(item["result"] == "passed" for item in continuity["current_target_emphasis_checks"])

        book = load(book_dir / "book.json")
        uk = book["editions"]["uk"]
        assert book["audit_status"] == "full_native_revision_partial_external_ensemble"
        assert book["language_state"] == "uk_full_native_revision_working_edition"
        assert uk["current_draft"] == new
        assert uk["target_sha256"] == current_prose["target.uk.txt"]
        assert uk["input_manifest"] == f"editions/uk/{inputs}"
        assert uk["preparation_packet"] == f"editions/uk/preparation/pilot/{ready}"
        assert uk["quality_assessment"] == f"editions/uk/{qa}"
        assert uk["continuity_path"] == f"editions/uk/{new}/continuity.json"
        assert uk["required_literary_release_gate"] == "open"
        assert uk["author_canonical_approval"] is False
        assert uk["planned_delivery"] == "delivery/2026-09-14-v4"
        assert uk["delivery_status"] == "planned"
        assert (edition / inputs).is_file()
        assert (edition / "preparation/pilot" / ready / "packet.json").is_file()
        session = (book_dir / "session.md").read_text(encoding="utf-8")
        assert new in session and current_prose["target.uk.txt"] in session
        assert "planned" in session and "gate открыт" in session
        assessment = (edition / qa).read_text(encoding="utf-8")
        assert new in assessment and current_prose["target.uk.txt"] in assessment
        assert "full_native_revision_partial_external_ensemble" in assessment
        assert "gate открыт" in assessment
        revision = load(book_dir / "revision-log.json")
        assert revision["items"][-1]["new_source"]["sha256"] == current_prose["target.uk.txt"]
        assert revision["items"][-1]["delivery"]["status"] == "planned"
        checks.append({
            "check": book_id,
            "result": "passed",
            "draft": new,
            "prose_sha256": current_prose,
            "continuity_sha256": sha(draft / "continuity.json"),
            "qa_assessment_sha256": sha(edition / qa),
            "anchor_checks": continuity["current_check_summary"],
        })
        for rel in ("book.json", "session.md", "revision-log.json"):
            diff_paths.append((BEFORE / "books" / book_id / rel, book_dir / rel))
        diff_paths.extend([
            (None, draft / "continuity.json"),
            (None, edition / qa),
        ])

    old_issues = load(BEFORE / "books/story-03-chaos-logic/audit/issues.json")
    new_issues_path = PROJECT / "books/story-03-chaos-logic/audit/issues.json"
    new_issues = load(new_issues_path)
    assert "current_verification" in new_issues["fields"]
    assert new_issues["items"][:len(old_issues["items"])] == old_issues["items"]
    added = new_issues["items"][len(old_issues["items"]):]
    assert [item["id"] for item in added] == [
        "story-03-chaos-logic-src17", "story-03-chaos-logic-src18",
        "story-03-chaos-logic-src19", "story-03-chaos-logic-src20",
    ]
    assert all(item["resolution_status"] == "unresolved" for item in added)
    existing = {item["id"]: item for item in new_issues["items"]}
    assert all(existing[item]["resolution_status"] == "unresolved" for item in (
        "story-03-chaos-logic-src04", "story-03-chaos-logic-src05", "story-03-chaos-logic-src06"
    ))
    p29 = next(anchor for anchor in added[-1]["anchors"] if anchor["p"] == 29)
    assert p29["anchor_role"].startswith("supplied p29 checked")
    checks.append({
        "check": "chaos_issue_history_and_new_unresolved",
        "result": "passed",
        "historical_entries_unchanged": len(old_issues["items"]),
        "new_unresolved_ids": [item["id"] for item in added],
        "p29_recorded_as_checked_non_supporting_anchor": True,
    })
    diff_paths.append((BEFORE / "books/story-03-chaos-logic/audit/issues.json", new_issues_path))

    diff_lines = []
    for before, after in diff_paths:
        old_lines = [] if before is None else before.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = after.read_text(encoding="utf-8").splitlines(keepends=True)
        old_label = "/dev/null" if before is None else str(before.relative_to(PROJECT))
        new_label = str(after.relative_to(PROJECT))
        diff_lines.extend(difflib.unified_diff(old_lines, new_lines, fromfile=old_label, tofile=new_label))
    (WORK / "DIFF.patch").write_text("".join(diff_lines), encoding="utf-8")
    checks_doc = {
        "schema_version": 1,
        "scope": "bounded current metadata and continuity; no prose edit",
        "result": "passed",
        "checks": checks,
        "diff": {"path": str((WORK / "DIFF.patch").relative_to(ROOT)),
                 "sha256": sha(WORK / "DIFF.patch")},
        "limits": "Dependent anchors only; no new full structural diagnosis. Reader exports, selection, final-checks and frozen packets were not modified by this task.",
    }
    (WORK / "CHECKS.json").write_text(
        json.dumps(checks_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"result": "passed", "checks": len(checks),
                      "diff_sha256": checks_doc["diff"]["sha256"]}))


if __name__ == "__main__":
    main()
