#!/usr/bin/env python3
"""Apply the recorded author answers to new, aligned Ukrainian working drafts.

This dated migration is intentionally single-use. It never rewrites a prior draft,
source, frozen input, or fixed review. Reader export and verification follow it.
"""
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "stories-ru-uk-pilot"
BATCH = PROJECT / "adaptation/author-answers-2026-09-14"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def ref(path):
    return {"path": rel(path), "sha256": sha(path)}


def write(path, data):
    assert not path.exists(), f"Refusing to overwrite {path}"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(data, encoding="utf-8")


def pnumber(block):
    return int(block["source_ids"][0].split("-p")[-1])


def main():
    plan = read(BATCH / "revision-plan.json")
    assert plan["author_answers_sha256"] == sha(ROOT / plan["author_answers"])
    created = datetime.now(timezone.utc).isoformat()
    for spec in plan["books"]:
        book = PROJECT / "books" / spec["book_id"]
        edition = book / "editions/uk"
        old = edition / spec["old_draft"]
        new = edition / spec["new_draft"]
        assert not new.exists(), new
        packet_old = edition / f"preparation/pilot/ready-v{spec['old_input_version']}"
        packet_new = edition / f"preparation/pilot/ready-v{spec['new_input_version']}"
        inputs_old = edition / f"INPUTS-V{spec['old_input_version']}.json"
        inputs_new = edition / f"INPUTS-V{spec['new_input_version']}.json"
        inputs = read(inputs_old)
        for item in inputs["inputs"]:
            assert sha(ROOT / item["path"]) == item["sha256"], item["path"]
        packet = read(packet_old / "packet.json")
        source = ROOT / packet["source"]["path"]
        assert sha(source) == packet["source"]["sha256"]
        source_data = read(packet_old / "source-segments.json")
        source_by_id = {x["id"]: x for x in source_data["segments"]}
        original = read(old / "translation.json")
        assert sha(packet_old / "source-segments.json") == original["source_segments_sha256"]
        assert sha(edition / "glossary.json") == original["glossary_sha256"]
        target = deepcopy(original)
        by_p = {pnumber(b): b for b in target["blocks"]}
        grouped = defaultdict(list)
        for change in spec["changes"]:
            block = by_p[change["p"]]
            assert sum(t.count(change["before"]) for t in block["target_paragraphs"]) == 1
            block["target_paragraphs"] = [t.replace(change["before"], change["after"])
                                            for t in block["target_paragraphs"]]
            grouped[change["p"]].append(change)
        for item in spec["preserved"]:
            if "text" in item:
                assert item["text"] in "\n".join(by_p[item["p"]]["target_paragraphs"])
        assert [b["source_ids"] for b in original["blocks"]] == [b["source_ids"] for b in target["blocks"]]
        assert [b.get("target_emphasis") for b in original["blocks"]] == [b.get("target_emphasis") for b in target["blocks"]]
        write(new / "translation.json", target)
        write(new / "target.uk.txt", "\n\n".join(t for b in target["blocks"] for t in b["target_paragraphs"]) + "\n")
        changes = []
        for before, after in zip(original["blocks"], target["blocks"]):
            if before == after:
                continue
            p = pnumber(before)
            assert p in grouped
            sources = [source_by_id[i] for i in before["source_ids"]]
            changes.append({"source_ids": before["source_ids"], "source_p": p,
                            "source_ru": "\n\n".join(s["text"] for s in sources),
                            "source_paragraph_sha256": [hashlib.sha256(s["text"].encode()).hexdigest() for s in sources],
                            "before": "\n\n".join(before["target_paragraphs"]),
                            "after": "\n\n".join(after["target_paragraphs"]),
                            "edits": grouped[p]})
        record = {"schema_version": 1, "book_id": spec["book_id"],
                  "from_version": spec["old_draft"], "to_version": spec["new_draft"],
                  "base_target_sha256": sha(old / "target.uk.txt"),
                  "result_target_sha256": sha(new / "target.uk.txt"),
                  "base_translation_sha256": sha(old / "translation.json"),
                  "result_translation_sha256": sha(new / "translation.json"),
                  "source": ref(source), "author_answers": ref(BATCH / "answers.json"),
                  "plan": ref(BATCH / "revision-plan.json"), "changes": changes,
                  "preserved": spec["preserved"],
                  "unchanged_blocks": len(original["blocks"]) - len(changes),
                  "prior_change_history": ref(old / "changes.json")}
        if "previous_title" in spec:
            record["title_change"] = {"before": spec["previous_title"], "after": spec["title"],
                                      **spec["title_decision"]}
        write(new / "changes.json", record)
        history = [ref(p) for p in sorted(old.rglob("*")) if p.is_file()]
        write(new / "prior-files.json", {"source": ref(source), "files": history,
                                         "policy": "All listed bytes must remain unchanged."})
        # Preserve the existing unit segmentation, rebuilding its target bytes.
        block_by_ids = {tuple(b["source_ids"]): b for b in target["blocks"]}
        for old_unit in sorted(old.glob("chapter-*.json")):
            unit = read(old_unit)
            unit["blocks"] = [block_by_ids[tuple(b["source_ids"])] for b in unit["blocks"]]
            write(new / old_unit.name, unit)
        if (old / "chunks").exists():
            for unit_dir in sorted((edition / "preparation/units").iterdir()):
                ids = {s["id"] for s in read(unit_dir / "source-segments.json")["segments"]}
                blocks = [b for b in target["blocks"] if set(b["source_ids"]) <= ids]
                assert sum(len(b["source_ids"]) for b in blocks) == len(ids)
                write(new / "chunks" / f"{unit_dir.name}.uk.txt",
                      "\n\n".join(t for b in blocks for t in b["target_paragraphs"]) + "\n")

        decision_file = edition / "decisions/2026-09-14-author-answers.json"
        decisions = {"schema_version": 1, "book_id": spec["book_id"], "created_at": created,
                     "authority": ref(BATCH / "answers.json"), "source": ref(source),
                     "scope": "UA_WORKING_EDITION only; RU source and cross-project canon unchanged",
                     "direct_author_choices": sorted({x["answer"] for x in spec["changes"] + spec["preserved"]
                                                       if x.get("answer") and x["answer"] != "ADDITIONAL"}),
                     "delegated_editorial_choices": [x for x in spec["changes"] if x["answer"] == "ADDITIONAL"],
                     "implementation": spec,
                     "author_approved_entire_uk_edition": False,
                     "attribution": "Exact author words are in authority. New Ukrainian formulations are the editor’s implementation; the author has not supplied or approved all of these exact sentences."}
        if "title_decision" in spec:
            decisions["direct_author_choices"].append("TITLE2")
        write(decision_file, decisions)
        vn = spec["new_input_version"]
        intent_file = edition / f"AUTHOR_INTENT-V{vn}-ANSWERS.md"
        lines = [f"# Решения автора: «{spec['title']}»", "", f"Источник SHA-256: `{sha(source)}`.", "",
                 "Ответы автора и разрешение выбрать логичные решения зафиксированы в `decisions/2026-09-14-author-answers.json`.",
                 "Этот слой имеет приоритет над прежними неподтверждёнными вариантами только в затронутых местах украинской рабочей редакции.",
                 "Русский мастер, исходные наблюдения и прежние зафиксированные отчёты остаются историческими источниками.", ""]
        if "title_decision" in spec:
            lines.extend([f"Автор выбрал название **{spec['title']}**.", ""])
        for x in spec["changes"]:
            lines.extend([f"- p{x['p']} ({x['answer']}): {x['reason']}"])
        lines.extend(["", "Сохранено по ответам автора:", ""])
        for x in spec["preserved"]:
            lines.append(f"- p{x['p']}: {x.get('reason', x.get('text', 'Без изменений.'))}")
        write(intent_file, "\n".join(lines) + "\n")
        meaning_file = edition / f"meaning-ledger-v{vn}-answers.json"
        write(meaning_file, {"schema_version": 1, "source": ref(source), "authority": ref(decision_file),
                             "scope": "Current Ukrainian edition overrides; not a replacement of source observations",
                             "changed_meaning_or_continuity": spec["changes"], "preserved": spec["preserved"]})
        glossary = {"schema_version": 1, "base_glossary": ref(edition / "glossary.json"),
                    "authority": ref(decision_file), "overrides": [],
                    "policy": "Only these entries supersede proposed base forms; no global replacement of unrelated words."}
        if spec["book_id"].endswith("reptiloids"):
            glossary["overrides"] = [{"status": "author_selected", "nominative": "Пелагія Гінеколаївна",
                                       "genitive": "Пелагії Гінеколаївни", "vocative": "Пелагіє Гінеколаївно"}]
        elif spec["book_id"].endswith("fair-killer"):
            glossary["overrides"] = [{"status": "author_selected", "scope": "story_title", "value": spec["title"]}]
        else:
            glossary["overrides"] = [{"status": "author_selected", "character": "Майкл Вайт", "rank": "підполковник"},
                                      {"status": "editorial_choice_under_delegation", "character": "Гаррі Арчер", "rank": "сержант"}]
        if (old / "glossary-addendum.json").exists():
            glossary["prior_addendum"] = ref(old / "glossary-addendum.json")
        write(new / "glossary-addendum.json", glossary)
        gold_file = edition / "GOLD_EXAMPLES/2026-09-14-author-answers.json"
        write(gold_file, {"schema_version": 1, "book_id": spec["book_id"], "source": ref(source),
                          "author_statements": ref(BATCH / "answers.json"),
                          "status": "author_intent_examples_with_editorial_uk_implementation",
                          "author_supplied_uk_prose_sample": False,
                          "examples": [{"source_ru": c["source_ru"], "ai_before": c["before"],
                                        "uk_after_editorial": c["after"], "source_ids": c["source_ids"],
                                        "answer_ids": sorted({x["answer"] for x in c["edits"]})} for c in changes],
                          "exact_existing_wording_retained_by_author": [x for x in spec["preserved"] if x.get("answer") == "Q2"]})
        additions = [BATCH / "answers.json", decision_file, intent_file, meaning_file,
                     new / "glossary-addendum.json", gold_file]
        packet_new.mkdir(parents=True)
        for name in ("source-segments.json", "source.ru.txt"):
            shutil.copy2(packet_old / name, packet_new / name)
        packet["inputs"] = inputs["inputs"] + [ref(p) for p in additions]
        packet["created_at"] = created
        packet["status"] = "prepared_with_author_answers_and_delegated_edits"
        packet["supersedes"] = ref(packet_old / "packet.json")
        packet["author_decision"] = rel(decision_file)
        write(packet_new / "packet.json", packet)
        inputs["inputs"] = packet["inputs"]
        inputs["packet"] = ref(packet_new / "packet.json")
        inputs["status"] = "frozen_for_author_answer_revision"
        inputs["supersedes_for_current_draft"] = ref(inputs_old)
        inputs["scope"] = "All previous frozen inputs plus explicit author answers and attributed editorial implementations"
        write(inputs_new, inputs)
        scene_states = read(book / "scenes.json")["items"]
        write(new / "continuity.json", {"schema_version": 1, "book_id": spec["book_id"],
              "target_sha256": sha(new / "target.uk.txt"), "source_sha256": sha(source),
              "authority": ref(decision_file), "context_read": spec["context_read"],
              "scene_entry_states": [{"id": s["id"], "state_before": s["input_state"],
                                       "source_result": s["result"]} for s in scene_states],
              "target_overrides": spec["changes"], "protected": spec["preserved"],
              "arithmetic": spec.get("arithmetic"),
              "knowledge_policy": "No early disclosure of later facts; quoted false accounts and character beliefs retain their attribution.",
              "source_registers": "Unchanged historical RU observations; target overrides are applied only in this linked UK layer."})
        md = [f"# Было — стало: «{spec['title']}»", "", f"{spec['old_draft']} → {spec['new_draft']}", "",
              f"До SHA-256: `{sha(old / 'target.uk.txt')}`.", f"После SHA-256: `{sha(new / 'target.uk.txt')}`.", "",
              "Основание — полный пакет ответов автора от 14 сентября 2026 года. Новые формулировки в делегированных местах выбраны редактором.", ""]
        if "title_change" in record:
            md.extend([f"Название: **{spec['previous_title']}** → **{spec['title']}**.", ""])
        for c in changes:
            md.extend([f"## p{c['source_p']}", "", "**Было**", "", c["before"], "", "**Стало**", "", c["after"], "",
                       "**Основание:** " + " ".join(x["reason"] for x in c["edits"]), ""])
        md.extend([f"Без изменений: {record['unchanged_blocks']} из {len(original['blocks'])} выровненных блоков.", "",
                   "Полная история предыдущей редакции остаётся в Git по пути: " + rel(old / "CHANGES.md") + "."])
        write(new / "CHANGES.md", "\n".join(md) + "\n")
        notes = [f"# Примечания к «{spec['title']}»", "", f"Текущая редакция: `{spec['new_draft']}`; SHA-256: `{sha(new / 'target.uk.txt')}`.", "",
                 "Полный перевод сохранён. «Было — стало» и changes.json содержат все изменения этой редакции.",
                 "Прямые решения автора отличаются в реестре от редакторских решений, принятых по его поручению.", ""]
        notes += [f"- p{x['p']}: {x['reason']}" for x in spec["changes"]]
        notes.extend(["", "Предыдущие примечания: " + rel(old / "ADAPTATION_NOTES.md") + ".", "",
                      "Новый проход проверяет авторские изменения и их зависимости. Полный независимый литературный цикл для этой версии ещё не завершён."])
        write(new / "ADAPTATION_NOTES.md", "\n".join(notes) + "\n")
        write(new / "REVIEW-RESOLUTIONS.json", {"schema_version": 1, **{k: v for k, v in record.items() if k != "changes"},
              "resolutions": [{"source_p": c["source_p"], "edits": c["edits"],
                               "status": "applied_under_author_instruction"} for c in changes],
              "scope": "Author-answer revision; no new independent reviewer findings fabricated or attributed."})
        for item in history:
            assert sha(ROOT / item["path"]) == item["sha256"]
        for item in inputs["inputs"]:
            assert sha(ROOT / item["path"]) == item["sha256"]
        write(new / "author-decision-check.json", {"schema_version": 1, "book_id": spec["book_id"],
              "target_sha256": sha(new / "target.uk.txt"), "translation_sha256": sha(new / "translation.json"),
              "result": "passed_exact_author_plan_application", "source_docx_unchanged": True,
              "previous_draft_files_unchanged": len(history), "frozen_inputs_verified": len(inputs["inputs"]),
              "inputs_manifest": ref(inputs_new), "exact_replacements": len(spec["changes"]),
              "changed_blocks": len(changes), "unchanged_blocks": record["unchanged_blocks"],
              "source_units": sum(len(b["source_ids"]) for b in target["blocks"]),
              "emphasis_metadata_unchanged": True, "preserved_decisions_checked": spec["preserved"],
              "arithmetic": spec.get("arithmetic"), "limits": "Exact application and local continuity check; not a full independent literary assessment."})
        print(spec["book_id"], spec["new_draft"], len(changes), "changed blocks;", len(inputs["inputs"]), "verified inputs")


if __name__ == "__main__":
    main()
