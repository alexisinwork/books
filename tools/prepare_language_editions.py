#!/usr/bin/env python3
"""Create preparation files for existing legacy books, without translating prose."""
import argparse
import json
from pathlib import Path
import sys

import literary_translation as lt


def build(root, project, inventory, preparation, books, preparation_id):
    root = Path(root).resolve()
    project_path = lt.contained(root, project)
    source_inventory = lt.read(inventory)
    system = (project_path / lt.read(project_path / "project.json")["book_system"]).resolve()
    templates = system / "ADAPTATION/templates"
    prep_ref = Path(preparation).resolve().relative_to(root).as_posix()
    plan = []
    for book_id in books:
        if not __import__("re").fullmatch(r"[a-z0-9-]+", preparation_id):
            raise ValueError("Invalid preparation ID")
        book = next(b for b in source_inventory["books"] if b["book_id"] == book_id)
        source = book["inventory_source"]
        lt.checked(root, source)
        for target, route in [("uk", "ru-uk"), ("en", "uk-en")]:
            dest = project_path / "books" / book_id / "editions" / target / preparation_id
            if dest.exists():
                raise ValueError(f"Preparation exists: {dest}")
            plan.append((book, source, target, route, dest))
    outputs = []
    for book, source, target, route, dest in plan:
        uk = target == "uk"
        eligible = uk and book["pilot_eligible"]
        source_status = ("author_selected_ru_basis; translation not started" if eligible else
                         "candidate_ru_reference; final translation source requires author selection" if uk else
                         "awaiting_author_approved_ua_canonical_master")
        values = {"TITLE": book["title_ru"], "BOOK_ID": book["book_id"], "ROUTE": route,
                  "SOURCE_PATH": source["path"] if uk else "UA_CANONICAL_MASTER: not yet created",
                  "SOURCE_SHA": source["sha256"] if uk else "not_available",
                  "SOURCE_STATUS": source_status, "PREPARATION": prep_ref, "TARGET_LANGUAGE": target,
                  "LANGUAGE_STYLE": system.relative_to(root).as_posix() + f"/LANGUAGES/{target}/STYLE.md"}
        for name in ["BOOK_BIBLE", "AUTHOR_INTENT", "STYLE_GUIDE", "GLOSSARY", "CHARACTER_VOICES", "MEANING_LEDGER", "DECISION_LOG"]:
            text = (templates / (name + ".md")).read_text(encoding="utf-8")
            for key, value in values.items():
                text = text.replace("{{" + key + "}}", value)
            filename = ("UA_STYLE_GUIDE" if uk else "EN_STYLE_GUIDE") if name == "STYLE_GUIDE" else (
                       "GLOSSARY_RU_UA" if uk else "GLOSSARY_UA_EN") if name == "GLOSSARY" else name
            lt.write_new(dest / (filename + ".md"), text)
        lt.write_new(dest / "edition.json", {"schema_version": 1, "book_id": book["book_id"],
                     "route": route, "target_language": target, "status": "prepared_not_translated",
                     "source_status": source_status, "source": source if uk else None,
                     "legacy_ru_reference": source, "canonical_master": None, "primary_adapter": None,
                     "author_selected_translation_source": False,
                     "english_locale": "en-US", "meaning_extraction": "not_run", "models_called": [],
                     "input_inventory": lt.reference(root, inventory)})
        lt.write_new(dest / "SOURCE/source-reference.json", {"role": "RU_SOURCE_MASTER" if eligible else "candidate_reference" if uk else "awaiting_UA_CANONICAL_MASTER",
                     "source": source if uk else None, "legacy_reference": source,
                     "preservation": "Original bytes remain at the referenced path; freeze an immutable copy before adaptation. Never overwrite sources/originals."})
        lt.write_new(dest / "meaning-ledger.json", {"schema_version": 1, "book_id": book["book_id"],
                     "source": source if uk else None, "coverage": "not_started; selective seed in preparation/adaptation-ledger.json", "items": []})
        lt.write_new(dest / "glossary.json", {"schema_version": 1, "book_id": book["book_id"],
                     "source_language": "ru" if uk else "uk", "target_language": target,
                     "status": "awaiting_source_and_term_decisions", "seed_reference": prep_ref + "/glossary.json", "entries": []})
        lt.write_new(dest / "GOLD_EXAMPLES/index.json", {"schema_version": 1, "book_id": book["book_id"],
                     "status": "awaiting_author_samples", "categories": ["narration", "dialogue", "humour", "action", "introspection"], "examples": []})
        issue_id = book["book_id"].upper() + ("-UK-SOURCE" if uk else "-EN-SOURCE")
        issues = [] if eligible else [{"id": issue_id, "status": "proposed", "resolution_status": "unresolved",
                     "certainty": "missing_link", "observation": source_status,
                     "anchors": [], "dependencies": ["all target chapters", "glossary locking", "meaning-ledger target anchors", "publication"],
                     "author_decision": None, "verification": {"status": "not_run"}}]
        lt.write_new(dest / "audit/issues.json", {"schema_version": 1, "book_id": book["book_id"],
                     "source_sha256": source["sha256"] if uk else None, "items": issues})
        lt.write_new(dest / "audit/status.json", {"schema_version": 1, "book_id": book["book_id"],
                     "preparation": "created", "translation": "not_started", "bilingual_qa": "not_run",
                     "opus": "not_run", "gemini_flash": "not_run", "gemini_pro": "not_run", "astra": "not_run",
                     "human_read": "not_run", "docx": "not_created", "render": "not_run", "canonical_promotion": "not_performed"})
        outputs.append(dest.relative_to(root).as_posix())
    return {"result": "prepared_not_translated", "editions": outputs}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--project", required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--books", nargs="+", required=True)
    parser.add_argument("--preparation-id", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.root, args.project, args.inventory, args.preparation, args.books, args.preparation_id), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
