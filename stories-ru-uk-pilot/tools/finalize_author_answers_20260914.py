#!/usr/bin/env python3
"""Select the verified author-answer drafts and synchronize current registers."""
from decimal import Decimal
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


def write(path, data, current=False):
    if path.exists():
        assert current, path
        backup = BATCH / "previous-current-registers" / path.relative_to(PROJECT)
        assert not backup.exists(), "This dated finalizer is single-use"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(data, str):
        data = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(data, encoding="utf-8")


def main():
    plan = read(BATCH / "revision-plan.json")
    selection = {"schema_version": 1, "date": "2026-09-14",
                 "scope": "Full three-story Ukrainian working edition after author answers",
                 "author_answers": rel(BATCH / "answers.json"), "books": [],
                 "supersedes": "SELECTION-2026-09-14-v2.json"}
    resolved = {
        "story-01-reptiloids": {1: "Q1", 2: "Q3"},
        "story-02-fair-killer": {1: "Q4", 2: "Q5", 5: "ADDITIONAL", 6: "ADDITIONAL", 7: "ADDITIONAL"},
        "story-03-chaos-logic": {1: "Q6", 2: "ADDITIONAL", 3: "Q8", 7: "ADDITIONAL", 8: "Q7",
                                 10: "ADDITIONAL", 11: "ADDITIONAL", 12: "ADDITIONAL", 13: "ADDITIONAL",
                                 14: "ADDITIONAL", 15: "ADDITIONAL", 16: "ADDITIONAL"}}
    for spec in plan["books"]:
        book = PROJECT / "books" / spec["book_id"]
        edition = book / "editions/uk"
        draft = edition / spec["new_draft"]
        changes = read(draft / "changes.json")
        final = read(draft / "final-checks.json")
        assert final["target_sha256"] == sha(draft / "target.uk.txt") and not final["errors"]
        inputs = edition / f"INPUTS-V{spec['new_input_version']}.json"
        for item in read(inputs)["inputs"]:
            assert sha(ROOT / item["path"]) == item["sha256"]
        for item in read(draft / "prior-files.json")["files"]:
            assert sha(ROOT / item["path"]) == item["sha256"]
        decision = edition / "decisions/2026-09-14-author-answers.json"
        source = ROOT / changes["source"]["path"]
        target = read(draft / "translation.json")
        paragraphs = {int(b["source_ids"][0].split("-p")[-1]): "\n\n".join(b["target_paragraphs"]) for b in target["blocks"]}
        local = {"schema_version": 1, "book_id": spec["book_id"], "target_sha256": sha(draft / "target.uk.txt"),
                 "reviewer": "Astra/Codex coordinator; editor of these changes", "independent": False,
                 "coverage": spec["context_read"], "changed_blocks_reread": len(changes["changes"]),
                 "checks": ["All changed complete paragraphs reread after application against the stated author choices.",
                            "Characters retain scene-appropriate knowledge; no future revelation is used as an earlier entry state.",
                            "All source IDs, order, section boundaries and emphasis metadata retained.",
                            "Source originals, prior draft bytes and all current frozen input hashes verified."],
                 "result": "passed_local_revision_review", "remaining_full_release_gate": "open",
                 "limitations": "No new full bilingual or independent target-only model review. Prior Opus session limit and Gemini OAuth ineligibility remain unresolved; no fresh requests were claimed."}
        if spec["book_id"].endswith("reptiloids"):
            text = (draft / "target.uk.txt").read_text()
            assert not any(x in text for x in ["Пелагея", "Пелагеї", "Пелагеє", "Миколаївни"])
            assert "нічної зміни" in paragraphs[1]
            assert "заговори ваші яйцем по голові викачували" in paragraphs[17]
        if spec["book_id"].endswith("fair-killer"):
            assert paragraphs[5] == paragraphs[66]
            assert paragraphs[248] == "Один безгучний ляск пролунав у тиші…"
            assert "спробував знову запустити" in paragraphs[87]
            assert "останні слова" not in paragraphs[123]
            local["chikaioki_scope"] = "Rule and depicted capture now agree. No exact board position is supplied, so a complete move-by-move chess reconstruction is not asserted."
        if spec["book_id"].endswith("chaos-logic"):
            sea = Decimal(4589) / Decimal(20)
            destruction = (Decimal(4589) - Decimal(200)) / Decimal(20)
            assert sea == Decimal("229.45") and destruction == Decimal("219.45")
            assert sea - destruction == Decimal(10)
            assert "Якщо швидкість не зміниться" in paragraphs[143]
            assert "рівно три хвилини" not in paragraphs[144]
            assert "трьох лабораторій: хімічної, фізичної" in paragraphs[20]
            assert "на всіх чотирьох станціях" in paragraphs[310]
            assert "Жодні бажання не варті людського життя. Навіть благі." in paragraphs[324]
            assert "сказав полковник" not in (draft / "target.uk.txt").read_text()
            local["independent_arithmetic"] = {"method": "Decimal arithmetic from source values",
                                              "to_sea_seconds": str(sea), "to_200m_seconds": str(destruction),
                                              "rounding": "3:50 to sea; 3:40 to self-destruction, conditional on unchanged descent speed"}
        write(draft / "local-review.json", local)
        report = [f"# Локальная проверка: «{spec['title']}»", "", "Status: final",
                  f"Target SHA-256: {sha(draft / 'target.uk.txt')}", "",
                  "Проверяющий: Astra/Codex, редактор этого пакета. Проверка не независимая.", "",
                  f"Повторно прочитаны все {len(changes['changes'])} изменённых полных блоков; контекст: {spec['context_read']}", "",
                  "Принятые автором шутки, повторы и смысл финала сохранены. Точечные изменения согласованы с ближайшими сценами и исходными записями непрерывности.",
                  "Все 600 исходных единиц трёх рассказов остаются в полном переводе; охват этой языковой проверки ограничен изменениями и их зависимостями.", "",
                  "Механические проверки и оформление DOCX завершены. Новых полных отчётов Opus/Gemini нет; прежние отчёты остаются привязаны к своим версиям."]
        write(draft / "LOCAL-REVIEW.md", "\n".join(report) + "\n")
        assessment = edition / f"QA-ASSESSMENT-{spec['new_draft'].removeprefix('draft-')}.md"
        write(assessment, f"# Проверки: «{spec['title']}»\n\nТекущая версия: `{spec['new_draft']}`. Target SHA-256: `{sha(draft / 'target.uk.txt')}`.\n\n"
              f"Полный текст: {final['source_units']} исходных единиц; {final['pages']} страниц DOCX. Изменены {len(changes['changes'])} блоков по ответам автора. "
              f"Сохранность {len(read(inputs)['inputs'])} замороженных входов проверена отдельно от базовой проверки 15 входов.\n\n"
              "Astra повторно прочитала изменённые полные абзацы и их связи; это проверка собственных правок, не независимое новое чтение всего рассказа. "
              "Все страницы осмотрены на обзорных листах, выбранные страницы — в полном размере. Извлечение DOCX и PDF совпало с текущим переводом; выделения сохранены.\n\n"
              f"История независимых чтений: `QA-ASSESSMENT-{spec['old_draft'].removeprefix('draft-')}.md`. "
              "Ранее Opus полностью прочитал только первую версию «Рептилоїдів»; следующие запросы упёрлись в лимит сессии. "
              "Gemini Flash/Pro были отклонены настроенным OAuth-клиентом. В этом пакете новых ответов этих моделей нет.\n\n"
              "Статус: полная украинская рабочая редакция для чтения автором. Обязательный полный литературный выпускной цикл остаётся открытым. "
              "Весь украинский текст не назначен автором каноническим мастером.\n")
        manifest_path = book / "book.json"
        manifest = read(manifest_path)
        uk = manifest["editions"]["uk"]
        uk.update({"current_draft": spec["new_draft"], "title": spec["title"],
                   "target_path": f"editions/uk/{spec['new_draft']}/target.uk.txt",
                   "target_sha256": sha(draft / "target.uk.txt"),
                   "reader_path": f"editions/uk/{spec['new_draft']}/reader/{spec['title']} — українська версія.docx",
                   "quality_assessment": str(assessment.relative_to(book)),
                   "input_manifest": str(inputs.relative_to(book)),
                   "preparation_packet": f"editions/uk/preparation/pilot/ready-v{spec['new_input_version']}",
                   "continuity_path": f"editions/uk/{spec['new_draft']}/continuity.json",
                   "status": "author_answers_applied_working_edition", "author_canonical_approval": False,
                   "required_literary_release_gate": "open"})
        for old_key, new_key in [("target_file", "target_path"), ("reader_docx", "reader_path")]:
            if old_key in uk:
                uk[old_key] = uk[new_key]
        uk.setdefault("author_decisions", []).append(str(decision.relative_to(book)))
        write(manifest_path, manifest, current=True)
        issues = read(book / "audit/issues.json")
        for issue in issues["items"]:
            number = int(issue["id"].split("-src")[-1])
            if number in resolved[spec["book_id"]]:
                answer = resolved[spec["book_id"]][number]
                issue["resolution_status"] = "resolved"
                issue["resolution_scope"] = "Current Ukrainian working edition only; original Russian observation retained"
                issue["decision"] = {"status": "editorial_choice_under_author_delegation" if answer == "ADDITIONAL" else "accepted",
                                     "answer_id": answer, "path": rel(decision), "sha256": sha(decision)}
                issue["verification"] = {"result": "applied_or_preserved_as_directed", "target_path": rel(draft / "target.uk.txt"),
                                         "target_sha256": sha(draft / "target.uk.txt"), "check_path": rel(draft / "local-review.json"),
                                         "check_sha256": sha(draft / "local-review.json")}
            elif spec["book_id"].endswith("chaos-logic") and number == 9:
                issue["current_version_reverification"] = {"path": rel(draft / "local-review.json"), "sha256": sha(draft / "local-review.json"), "unchanged_author_meaning": True}
        write(book / "audit/issues.json", issues, current=True)
        log = read(book / "revision-log.json")
        log["items"].append({"id": "author-answers-2026-09-14", "reason": "Apply author answers and expressly delegated continuity edits",
             "old_source": {"path": f"editions/uk/{spec['old_draft']}/target.uk.txt", "sha256": changes["base_target_sha256"]},
             "new_source": {"path": uk["target_path"], "sha256": uk["target_sha256"], "role": "UA_WORKING_EDITION"},
             "changes": f"editions/uk/{spec['new_draft']}/changes.json", "decision": str(decision.relative_to(book)),
             "continuity": uk["continuity_path"], "verification": f"editions/uk/{spec['new_draft']}/local-review.json",
             "ru_source_registers": "Unchanged historical observations; UK facts and entry-state overrides are in the linked continuity layer.",
             "delivery": "../../delivery/2026-09-14-v3", "full_literary_release_gate": "open"})
        write(book / "revision-log.json", log, current=True)
        write(book / "session.md", f"# Текущая сессия\n\nПолный перевод «{spec['title']}»: `{spec['new_draft']}`. Ответы автора от 2026-09-14 применены.\n\n"
              f"Текст: `{uk['target_path']}`; SHA-256 `{uk['target_sha256']}`. Актуальные входы: `{uk['input_manifest']}`. "
              f"Состояние и изменения фактов UK: `{uk['continuity_path']}`.\n\n"
              "До следующей правки прочитайте текущие author decisions и addenda: неподтверждённые варианты базовых профилей в этих местах устарели. "
              "Русский источник и его регистры остаются отдельной исторической версией.\n\n"
              "Передача: `delivery/2026-09-14-v3`. DOCX и полное сравнение готовы; новые независимые литературные чтения пока не выполнены.\n", current=True)
        index_path = edition / "GOLD_EXAMPLES/index.json"
        index = read(index_path)
        index["items"].append({"path": "2026-09-14-author-answers.json", "sha256": sha(edition / "GOLD_EXAMPLES/2026-09-14-author-answers.json"),
                               "status": "author_intent_examples; new_UK_wording_is_editorial"})
        index["status"] = "contains_author_choices_and_attributed_editorial_implementations"
        write(index_path, index, current=True)
        selection["books"].append({"book_id": spec["book_id"], "draft": spec["new_draft"], "title": spec["title"],
                                   "docx_name": f"{spec['title']} — українська версія.docx", "target_sha256": uk["target_sha256"],
                                   "input_manifest": rel(inputs), "input_manifest_sha256": sha(inputs)})
        print(spec["book_id"], "selected; local review and current registers synchronized")
    write(PROJECT / "release/SELECTION-2026-09-14-v3.json", selection)
    project = read(PROJECT / "project.json")
    project["task_scope"].update({"status": "full_translations_revised_after_author_answers", "delivery": "delivery/2026-09-14-v3"})
    write(PROJECT / "project.json", project, current=True)
    for name in ["README.md", "START_HERE.md"]:
        path = PROJECT / name
        text = path.read_text().replace("delivery/2026-09-14-v2", "delivery/2026-09-14-v3").replace("Справедливий убивця", "Справедливий вбивця")
        text += "\nОтветы автора применены во всех трёх рабочих редакциях. Актуальный INPUTS-V2 у «Рептилоїдів» и «Справедливого вбивці», INPUTS-V3 у «Логіки хаосу»; точные пути указаны в book.json. "
        text += "Базовые INPUTS-V1 и профили сохранены, а принятые уточнения находятся в новых AUTHOR_INTENT, meaning-ledger и decisions. "
        text += "Полное сравнение и решения: [пакет ответов](adaptation/author-answers-2026-09-14/ANSWERS.md).\n"
        write(path, text, current=True)


if __name__ == "__main__":
    main()
