#!/usr/bin/env python3
"""Apply the bounded current-metadata update for the three pilot stories."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[3]
ROOT = PROJECT.parent
WORK = PROJECT / "adaptation/native-review-2026-09-14/metadata-work"
BEFORE = WORK / "before"


CONFIG = {
    "story-01-reptiloids": {
        "old": "draft-v4", "new": "draft-v5", "inputs": "INPUTS-V3.json",
        "ready": "ready-v3", "qa": "QA-ASSESSMENT-v5.md", "previous_qa": "QA-ASSESSMENT-v4.md",
        "title": "Рептилоїди", "reader": "Рептилоїди — українська версія.docx",
        "spec": "adaptation/native-review-2026-09-14/reconciliation/story-01-reptiloids.spec.json",
        "exact_override": {1: "Після довгої нічної зміни на фабриці"},
        "protected": [
            (17, "Та й заговори ваші яйцем по голові викачували! А вам і викачувати нема на чому!",
             "author-selected comic refrain"),
            (55, "Олег неквапно знімає маску", "final revelation about Oleg"),
            (55, "блиснувши жовтими очима", "reptiloid reveal remains explicit"),
        ],
    },
    "story-02-fair-killer": {
        "old": "draft-v3", "new": "draft-v4", "inputs": "INPUTS-V3.json",
        "ready": "ready-v3", "qa": "QA-ASSESSMENT-v4.md", "previous_qa": "QA-ASSESSMENT-v3.md",
        "title": "Справедливий вбивця", "reader": "Справедливий вбивця — українська версія.docx",
        "spec": "adaptation/native-review-2026-09-14/reconciliation/story-02-fair-killer.spec.json",
        "exact_override": {},
        "protected": [
            (5, "Один безгучний ляск пролунав у тиші кабінету.", "first acoustic-paradox refrain"),
            (66, "Один безгучний ляск пролунав у тиші кабінету.", "second acoustic-paradox refrain"),
            (248, "Один безгучний ляск пролунав у тиші…", "open-ending refrain"),
            (155, "А в мене точно не буде невинних жертв.", "Light's protected self-justification"),
            (246, "Років за десять я вже перестав так ретельно перевіряти жертв",
             "later admission that checks weakened"),
            (246, "кілька десятків добрих бізнесменів, політиків і журналістів усе-таки загинули від моєї руки",
             "later admission of innocent deaths"),
        ],
    },
    "story-03-chaos-logic": {
        "old": "draft-v4", "new": "draft-v7", "inputs": "INPUTS-V4.json",
        "ready": "ready-v4", "qa": "QA-ASSESSMENT-v7.md", "previous_qa": "QA-ASSESSMENT-v4.md",
        "title": "Логіка хаосу", "reader": "Логіка хаосу — українська версія.docx",
        "spec": "adaptation/native-review-2026-09-14/reconciliation/story-03-chaos-logic-v7.spec.json",
        "exact_override": {130: "статистичною ймовірністю"},
        "protected": [
            (5, "Вставай вже", "explicitly imported compatible author Desktop variant"),
            (38, "Мені лише 60 років.", "Wolff's factual age"),
            (143, "три хвилини й п’ятдесят секунд", "conditional time to sea"),
            (144, "трьох хвилин і сорока секунд", "rounded time to self-destruction"),
            (157, "А в душі мені ще й п’ятдесяти немає.", "age joke remains subjective"),
            (292, "Після сніданку нас відвели", "breakfast continuity correction p290–p292"),
            (308, "Його мотивів я не знав", "Ryazantsev's motive remains unknown"),
            (309, "загинула його донька", "Sheng's daughter remains unnamed and unlinked to Nika"),
            (314, "я можу цілком упевнено сказати вам, що це неможливо",
             "engineering rebuttal to Sheng's false account"),
            (324, "Жодні бажання не варті людського життя. Навіть благі.",
             "author-confirmed closing meaning"),
        ],
        "negative": [(309, "Ніка", "no invented identification of Sheng's daughter as Nika")],
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ref(path: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path)}


def pnum(source_id: str) -> int:
    return int(source_id.rsplit("-p", 1)[1])


def paragraph_map(translation: dict) -> dict[int, dict]:
    result = {}
    for block in translation["blocks"]:
        for source_id in block["source_ids"]:
            number = pnum(source_id)
            if number in result:
                raise AssertionError(f"duplicate paragraph number {number}")
            result[number] = block
    return result


def full_text(block: dict) -> str:
    return "\n\n".join(block["target_paragraphs"])


def exact_check(by_p: dict[int, dict], p: int, text: str, purpose: str, *, expected=1) -> dict:
    current = full_text(by_p[p])
    occurrences = current.count(text)
    assert occurrences == expected, (p, text, occurrences, expected)
    return {
        "p": p,
        "source_ids": by_p[p]["source_ids"],
        "purpose": purpose,
        "exact_text": text,
        "expected_occurrences": expected,
        "actual_occurrences": occurrences,
        "target_paragraph_sha256": [text_sha(x) for x in by_p[p]["target_paragraphs"]],
        "result": "passed",
    }


def build_continuity(book_id: str, cfg: dict) -> dict:
    edition = PROJECT / "books" / book_id / "editions/uk"
    old_dir, new_dir = edition / cfg["old"], edition / cfg["new"]
    predecessor_path = old_dir / "continuity.json"
    continuity = deepcopy(load(predecessor_path))
    translation_path = new_dir / "translation.json"
    target_path = new_dir / "target.uk.txt"
    translation = load(translation_path)
    rendered = "\n\n".join(
        paragraph for block in translation["blocks"] for paragraph in block["target_paragraphs"]
    ) + "\n"
    assert rendered == target_path.read_text(encoding="utf-8")
    by_p = paragraph_map(translation)
    continuity["current_draft"] = cfg["new"]
    continuity["target_sha256"] = sha(target_path)
    continuity["translation_sha256"] = sha(translation_path)
    continuity["predecessor"] = {
        **ref(predecessor_path),
        "draft": cfg["old"],
        "target_sha256": sha(old_dir / "target.uk.txt"),
    }
    spec_path = PROJECT / cfg["spec"]
    continuity["revision_basis"] = [
        {**ref(spec_path), "role": "reconciled_exact_language_edits"},
        {**ref(new_dir / "changes.json"), "role": "full_paragraph_change_record"},
        {**ref(edition / cfg["inputs"]), "role": "frozen_inputs"},
        {**ref(edition / "preparation/pilot" / cfg["ready"] / "packet.json"),
         "role": "frozen_preparation_packet"},
    ]
    if book_id == "story-03-chaos-logic":
        import_path = PROJECT / "adaptation/native-review-2026-09-14/desktop-import/import.json"
        v5 = edition / "draft-v5"
        v6 = edition / "draft-v6"
        continuity["revision_basis"].append({**ref(import_path), "role": "exact_desktop_import"})
        continuity["intermediate_drafts"] = [
            {
                "draft": "draft-v5",
                "target": ref(v5 / "target.uk.txt"),
                "translation": ref(v5 / "translation.json"),
                "changes": ref(v5 / "changes.json"),
                "continuity_created": False,
                "note": "Preserved native/reconciled intermediate revision.",
            },
            {
                "draft": "draft-v6",
                "target": ref(v6 / "target.uk.txt"),
                "translation": ref(v6 / "translation.json"),
                "changes": ref(v6 / "changes.json"),
                "continuity_created": False,
                "note": "Preserved intermediate with the compatible Desktop variant; final v7 adds only two independently confirmed punctuation fixes.",
            },
        ]

    anchor_checks = []
    for item in continuity.get("target_overrides", []):
        exact = cfg["exact_override"].get(item["p"], item["after"])
        status = "author_answer_applied" if str(item.get("answer", "")).startswith("Q") else "editorial_choice_under_author_delegation"
        check = exact_check(by_p, item["p"], exact, "current form of historical continuity override")
        check.update({
            "historical_after": item["after"],
            "authority_status": status,
            "semantic_obligation_preserved": True,
        })
        anchor_checks.append(check)
    continuity["current_anchor_checks"] = anchor_checks

    protected_checks = [
        exact_check(by_p, p, text, purpose) for p, text, purpose in cfg["protected"]
    ]
    for p, text, purpose in cfg.get("negative", []):
        protected_checks.append(exact_check(by_p, p, text, purpose, expected=0))
    emphasis_checks = []
    for block in translation["blocks"]:
        for emphasis in block.get("target_emphasis", []):
            paragraph = block["target_paragraphs"][emphasis["paragraph"]]
            assert paragraph.count(emphasis["text"]) == 1
            emphasis_checks.append({
                "source_ids": block["source_ids"],
                "paragraph": emphasis["paragraph"],
                "text": emphasis["text"],
                "format": {key: value for key, value in emphasis.items()
                           if key not in {"paragraph", "text"}},
                "actual_occurrences": 1,
                "result": "passed",
            })
    continuity["current_protected_checks"] = protected_checks
    continuity["current_target_emphasis_checks"] = emphasis_checks
    continuity["current_check_summary"] = {
        "target_sha256": sha(target_path),
        "historical_overrides_checked": len(anchor_checks),
        "protected_exact_checks": len(protected_checks),
        "target_emphasis_ranges_checked": len(emphasis_checks),
        "result": "passed",
        "scope": "Dependent continuity anchors only; not a new full structural diagnosis.",
    }
    if book_id == "story-03-chaos-logic":
        continuity["current_editorial_choices"] = [{
            "p": 292,
            "source_ids": by_p[292]["source_ids"],
            "before": "Після обіду нас відвели",
            "after": "Після сніданку нас відвели",
            "status": "editorial_choice_under_author_delegation",
            "author_canon_approved": False,
            "reason": "p290 announces breakfast, p291 depicts that meal, and p292 immediately follows it; the author had delegated logical local corrections.",
            "authority": ref(spec_path),
        }]
        continuity["desktop_author_variant"] = {
            "p": 5, "before": "Вставай уже", "after": "Вставай вже",
            "status": "explicitly_imported_compatible_author_variant",
            "canonical_approval_inferred": False,
            "authority": ref(PROJECT / "adaptation/native-review-2026-09-14/desktop-import/import.json"),
        }
        continuity["preserved_unresolved_source_issues"] = [
            "story-03-chaos-logic-src04",
            "story-03-chaos-logic-src05",
            "story-03-chaos-logic-src06",
        ]
    # source_registers is inherited byte-for-value from predecessor and deliberately untouched.
    return continuity


def source_anchor(segment: dict, source_path: Path, chapter: int, role: str | None = None) -> dict:
    item = {
        "path": str(source_path.relative_to(ROOT)),
        "sha256": sha(source_path),
        "format": "docx",
        "status": "author_selected",
        "role": "master_inventory",
        "language": "ru",
        "chapter": chapter,
        "p": pnum(segment["id"]),
        "source_id": segment["id"],
        "quote": segment["text"],
        "quote_ru": segment["text"],
        "paragraph_sha256": text_sha(segment["text"]),
    }
    if role:
        item["anchor_role"] = role
    return item


def append_chaos_issues(target_sha: str) -> None:
    book = PROJECT / "books/story-03-chaos-logic"
    issues_path = book / "audit/issues.json"
    issues = load(issues_path)
    if "current_verification" not in issues["fields"]:
        verification_index = issues["fields"].index("verification")
        issues["fields"].insert(verification_index + 1, "current_verification")
    existing_ids = {item["id"] for item in issues["items"]}
    for required in ("story-03-chaos-logic-src04", "story-03-chaos-logic-src05", "story-03-chaos-logic-src06"):
        assert required in existing_ids
        assert next(x for x in issues["items"] if x["id"] == required)["resolution_status"] == "unresolved"
    source_path = book / "sources/originals/Логика хаоса.docx"
    segments = load(book / "editions/uk/preparation/pilot/ready-v4/source-segments.json")["segments"]
    by_p = {pnum(item["id"]): item for item in segments}
    target_translation = load(book / "editions/uk/draft-v7/translation.json")
    target_by_p = paragraph_map(target_translation)

    def verification(paragraphs: list[int]) -> dict:
        return {
            "checked_target_path": "stories-ru-uk-pilot/books/story-03-chaos-logic/editions/uk/draft-v7/target.uk.txt",
            "checked_target_sha256": target_sha,
            "anchors": [{
                "p": p,
                "source_ids": target_by_p[p]["source_ids"],
                "target_paragraph_sha256": [text_sha(x) for x in target_by_p[p]["target_paragraphs"]],
            } for p in paragraphs],
            "result": "ambiguity_or_inconsistency_still_present; no prose change made",
        }

    definitions = [
        {
            "id": "story-03-chaos-logic-src17", "severity": "S2",
            "paragraphs": [133, 134, 135, 136, 137],
            "observation": "Реплика p136 обращена к Чарльзу, но говорящий не назван; по контексту им может быть Гарри или Вольф, и источник не позволяет выбрать одного без домысла.",
            "reader_effect": "Атрибуция меняет голос, знание и эмоциональную позицию персонажа.",
            "proposed_change": "Оставить реплику без новой атрибуции до решения автора.",
        },
        {
            "id": "story-03-chaos-logic-src18", "severity": "S2",
            "paragraphs": [296, 297],
            "observation": "Ведущий p296 передаёт слово Чарльзу, а Чарльз в p297 отвечает «генерале»; личность и ранее установленная роль ведущего не названы.",
            "reader_effect": "Самовольное имя или чин создали бы нового фактического участника сцены либо изменили ранг известного.",
            "proposed_change": "Не назначать ведущего и не менять обращение без авторского решения.",
        },
        {
            "id": "story-03-chaos-logic-src19", "severity": "S2",
            "paragraphs": [144, 166],
            "observation": "В p144 команда должна настроить двигатель на ручное управление отсеком, но в p166 Гарри утверждает, что возможности управлять нет и полёт ведёт автопилот.",
            "reader_effect": "Неясно, относятся ли фразы к разным системам/этапам или противоречат друг другу.",
            "proposed_change": "Сохранить обе формулы и не изобретать устройство управления станции.",
        },
        {
            "id": "story-03-chaos-logic-src20", "severity": "S2",
            "paragraphs": [15, 29, 149, 150, 277],
            "roles": {15: "bracelet introduced", 29: "supplied p29 checked; no bracelet/personal-item statement found",
                      149: "no-personal-items rule", 150: "scattered possessions onboard", 277: "bracelet still present"},
            "observation": "p149 утверждает, что личные вещи на борт не берут, однако p15 и p277 показывают любимый браслет Гарри, а p150 — разбросанные вещи на его кровати и столе. Указанный при постановке p29 проверен и этого наблюдения не содержит.",
            "reader_effect": "Неясно, является ли правило преувеличением рассказчика, касается только отдельных вещей или нарушено текстом.",
            "proposed_change": "Не удалять вещи и не уточнять правило без авторского решения.",
        },
    ]
    for definition in definitions:
        assert definition["id"] not in existing_ids
        roles = definition.pop("roles", {})
        paragraphs = definition.pop("paragraphs")
        entry = {
            "id": definition["id"],
            "status": "proposed",
            "resolution_status": "unresolved",
            "category": "source_ambiguity_or_inconsistency",
            "severity": definition.pop("severity"),
            "certainty": "observed_difference_not_authorial_intent",
            "anchors": [source_anchor(by_p[p], source_path,
                                      int(by_p[p]["id"].rsplit("-c", 1)[1].split("-p", 1)[0]),
                                      roles.get(p))
                        for p in paragraphs],
            **definition,
            "dependencies": [by_p[p]["id"] for p in paragraphs],
            "current_verification": verification(paragraphs),
            "decision": {"status": "unresolved", "author_answer_reopened": False},
            "resolution_scope": "Source observation retained; current Ukrainian working edition does not resolve it.",
        }
        issues["items"].append(entry)
    write_json(issues_path, issues)


def update_book(book_id: str, cfg: dict, target_sha: str) -> None:
    book_path = PROJECT / "books" / book_id / "book.json"
    data = load(book_path)
    data["stage"] = "full_native_revision_author_reading"
    data["audit_status"] = "full_native_revision_partial_external_ensemble"
    data["language_state"] = "uk_full_native_revision_working_edition"
    uk = data["editions"]["uk"]
    uk["status"] = "full_native_revision_working_edition"
    uk["current_draft"] = cfg["new"]
    for key in ("target_file", "target_path"):
        if key in uk:
            uk[key] = f"editions/uk/{cfg['new']}/target.uk.txt"
    for key in ("reader_docx", "reader_path"):
        if key in uk:
            uk[key] = f"editions/uk/{cfg['new']}/reader/{cfg['reader']}"
    uk["target_sha256"] = target_sha
    uk["quality_assessment"] = f"editions/uk/{cfg['qa']}"
    uk["input_manifest"] = f"editions/uk/{cfg['inputs']}"
    uk["preparation_packet"] = f"editions/uk/preparation/pilot/{cfg['ready']}"
    uk["continuity_path"] = f"editions/uk/{cfg['new']}/continuity.json"
    uk["required_literary_release_gate"] = "open"
    uk["author_canonical_approval"] = False
    uk["planned_delivery"] = "delivery/2026-09-14-v4"
    uk["delivery_status"] = "planned"
    write_json(book_path, data)


def update_session(book_id: str, cfg: dict, target_sha: str) -> None:
    path = PROJECT / "books" / book_id / "session.md"
    text = f"""# Текущая сессия

Полная native-редакция «{cfg['title']}»: `{cfg['new']}`. Это украинская рабочая редакция; авторское утверждение всего текста как канонического мастера не зафиксировано.

Текст: `editions/uk/{cfg['new']}/target.uk.txt`; SHA-256 `{target_sha}`. Актуальные входы: `editions/uk/{cfg['inputs']}` и `editions/uk/preparation/pilot/{cfg['ready']}`. Непрерывность и текущие защищённые проверки: `editions/uk/{cfg['new']}/continuity.json`. Оценка: `editions/uk/{cfg['qa']}`.

Авторские ответы сохранены. Русский источник и его регистры остаются отдельной исторической версией. Выпускной литературный gate открыт; внешний ансамбль завершён лишь частично.

Передача: `delivery/2026-09-14-v4` — **planned**, пока координатор не завершит сборку. Reader path: `editions/uk/{cfg['new']}/reader/{cfg['reader']}`.
"""
    path.write_text(text, encoding="utf-8")


def update_revision_log(book_id: str, cfg: dict, target_sha: str) -> None:
    path = PROJECT / "books" / book_id / "revision-log.json"
    data = load(path)
    edition = PROJECT / "books" / book_id / "editions/uk"
    item = {
        "id": f"full-native-language-revision-{cfg['new']}-2026-09-14",
        "reason": "Promote the fully read native-language candidate plus the reconciled exact edits without changing the RU source.",
        "old_source": {"path": f"editions/uk/{cfg['old']}/target.uk.txt",
                       "sha256": sha(edition / cfg["old"] / "target.uk.txt")},
        "new_source": {"path": f"editions/uk/{cfg['new']}/target.uk.txt",
                       "sha256": target_sha, "role": "UA_WORKING_EDITION"},
        "changes": f"editions/uk/{cfg['new']}/changes.json",
        "decision": cfg["spec"],
        "input_manifest": f"editions/uk/{cfg['inputs']}",
        "preparation_packet": f"editions/uk/preparation/pilot/{cfg['ready']}",
        "continuity": f"editions/uk/{cfg['new']}/continuity.json",
        "quality_assessment": f"editions/uk/{cfg['qa']}",
        "affected_checks": ["current continuity anchors", "author answers", "times and referents",
                            "protected refrains and target emphasis"],
        "audit_status": "full_native_revision_partial_external_ensemble",
        "language_status": "working_edition_not_author_canonical_master",
        "full_literary_release_gate": "open",
        "delivery": {"path": "../../delivery/2026-09-14-v4", "status": "planned"},
        "ru_source_registers": "Unchanged historical observations; current UK checks are in the linked continuity layer.",
    }
    if book_id == "story-03-chaos-logic":
        item["intermediate_sources"] = [
            {"path": "editions/uk/draft-v5/target.uk.txt",
             "sha256": sha(edition / "draft-v5/target.uk.txt"),
             "status": "preserved_intermediate_native_revision"},
            {"path": "editions/uk/draft-v6/target.uk.txt",
             "sha256": sha(edition / "draft-v6/target.uk.txt"),
             "status": "preserved_intermediate_desktop_variant"},
        ]
        item["desktop_import"] = ref(PROJECT / "adaptation/native-review-2026-09-14/desktop-import/import.json")
        item["meaning_change"] = {
            "p": 292, "status": "editorial_choice_under_author_delegation",
            "author_canon_approved": False,
            "change": "lunch -> breakfast to match p290–p292",
        }
    data["items"].append(item)
    write_json(path, data)


def write_qa(book_id: str, cfg: dict, target_sha: str, translation: dict, changes: dict) -> None:
    edition = PROJECT / "books" / book_id / "editions/uk"
    paragraphs = sum(len(block["target_paragraphs"]) for block in translation["blocks"])
    emphasis = sum(len(block.get("target_emphasis", [])) for block in translation["blocks"])
    continuity = load(edition / cfg["new"] / "continuity.json")
    text = f"""# Проверки: «{cfg['title']}»

Текущая версия: `{cfg['new']}`. Target SHA-256: `{target_sha}`. Translation SHA-256: `{sha(edition / cfg['new'] / 'translation.json')}`.

Полный текст: {len(translation['blocks'])} выровненных блоков, {paragraphs} целевых абзацев. Относительно доставленной базы изменено {len(changes['changes'])} полных целевых абзацев; полный журнал хранится в `{cfg['new']}/changes.json`.

Native-языковой проход охватил весь украинский текст. Reconciliation применил только точные зафиксированные edits. Это полный языковой self-review выбранного кандидата и частичный внешний ансамбль, а не новое независимое структурное обследование.

Зависимые continuity-проверки: {continuity['current_check_summary']['historical_overrides_checked']} исторических авторских/делегированных overrides, {continuity['current_check_summary']['protected_exact_checks']} точных защищённых проверок и {continuity['current_check_summary']['target_emphasis_ranges_checked']} диапазонов emphasis; результат `passed`. Source registers не переписывались.

Актуальные замороженные входы: `{cfg['inputs']}`; пакет: `preparation/pilot/{cfg['ready']}`. Историческая оценка предыдущей версии: `{cfg['previous_qa']}`. Механические final-checks и reader export ведутся отдельными файлами текущего draft и этой metadata-задачей не изменяются.

Статус: `full_native_revision_partial_external_ensemble`. Украинский текст остаётся рабочей редакцией, выпускной литературный gate открыт, авторское утверждение всего текста как канонического мастера не зафиксировано. `delivery/2026-09-14-v4` имеет статус planned до завершения сборки координатором.
"""
    (edition / cfg["qa"]).write_text(text, encoding="utf-8")


def verify_before_snapshot(selected: set[str]) -> None:
    manifest = load(BEFORE / "MANIFEST.json")
    for item in manifest["files"]:
        matching_books = [book_id for book_id in selected if f"books/{book_id}/" in item["path"]]
        if not matching_books:
            continue
        current = PROJECT / item["path"]
        before = BEFORE / item["path"]
        assert sha(before) == item["sha256"]
        assert sha(current) == item["sha256"], f"concurrent metadata change: {current}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--book", action="append", choices=sorted(CONFIG),
                        help="update one book; repeat as needed (default: all)")
    args = parser.parse_args()
    selected = set(args.book or CONFIG)
    verify_before_snapshot(selected)
    prose_before = {}
    for book_id, cfg in CONFIG.items():
        if book_id not in selected:
            continue
        edition = PROJECT / "books" / book_id / "editions/uk"
        draft = edition / cfg["new"]
        prose_before[book_id] = {
            name: sha(draft / name) for name in ("translation.json", "target.uk.txt", "changes.json")
        }
        continuity_path = draft / "continuity.json"
        qa_path = edition / cfg["qa"]
        assert not continuity_path.exists(), continuity_path
        assert not qa_path.exists(), qa_path
        continuity = build_continuity(book_id, cfg)
        write_json(continuity_path, continuity)
        target_sha = sha(draft / "target.uk.txt")
        if book_id == "story-03-chaos-logic":
            append_chaos_issues(target_sha)
        update_book(book_id, cfg, target_sha)
        update_session(book_id, cfg, target_sha)
        update_revision_log(book_id, cfg, target_sha)
        write_qa(book_id, cfg, target_sha, load(draft / "translation.json"), load(draft / "changes.json"))
    for book_id, cfg in CONFIG.items():
        if book_id not in selected:
            continue
        draft = PROJECT / "books" / book_id / "editions/uk" / cfg["new"]
        assert prose_before[book_id] == {
            name: sha(draft / name) for name in ("translation.json", "target.uk.txt", "changes.json")
        }
        write_json(WORK / f"prose-hashes-{book_id}.json", {
            "schema_version": 1,
            "result": "prose files unchanged by metadata update",
            "files": {book_id: prose_before[book_id]},
        })
    print("updated", ", ".join(
        f"{book_id}:{cfg['new']}" for book_id, cfg in CONFIG.items() if book_id in selected
    ))


if __name__ == "__main__":
    main()
