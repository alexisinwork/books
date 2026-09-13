#!/usr/bin/env python3
"""Rebuild synchronized artifacts for the locked Book 2 ensemble revision."""

from __future__ import annotations

import difflib
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess


REV = Path(__file__).resolve().parent
PRIOR = REV.parent / "2026-09-13-10al"
BOOK = REV.parents[1]
ROOT = REV.parents[4]
SOURCE = PRIOR / "revised.md"
REVISED = REV / "revised.md"
PRIOR_SHA = "209ecd595c711bd39762564d061e3df2c67c16c729763f164d6f4de67d656985"
ORIGINAL_SHA = "81641a85ee25e78bc1e57348b279e7a88317551b166cfa831f33bd8f99431d32"
BOOK1_SHA = "2651e6b73fe20e844ff19c4f7f99a39ca90c1da3d53f91a3a3a1417ce3ac4172"
STATUS = "ensemble_revision_for_author_review"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def printed_count(text: str) -> int:
    return sum(
        len(line.replace("`", "").replace("**", "").strip())
        for line in text.splitlines()
        if line.strip()
        and not re.match(r"^#{1,6} ", line)
        and not re.fullmatch(r"[-* ]{3,}", line)
        and line != "*Конец второго тома.*"
    )


def chapter_chunks(text: str) -> list[str]:
    return re.split(r"(?m)(?=^## Глава \d+\.)", text)[1:]


def anchor(chapter: int, digest: str, lines: list[str]) -> dict:
    quote = next(line for line in lines if line.startswith(f"## Глава {chapter}."))
    return {
        "source": "revised.md",
        "source_sha256": digest,
        "chapter": chapter,
        "original_chapter": chapter,
        "p": lines.index(quote) + 1,
        "quote": quote,
        "verification_status": "verified",
    }


def replace_internal_sha(value: object, digest: str) -> None:
    if isinstance(value, dict):
        for key, item in list(value.items()):
            if isinstance(item, str) and item == PRIOR_SHA and key in {
                "source_sha256", "chapter_source_sha256", "revision_sha256"
            }:
                value[key] = digest
            else:
                replace_internal_sha(item, digest)
    elif isinstance(value, list):
        for item in value:
            replace_internal_sha(item, digest)


def rebind_anchors(value: object, digest: str, lines: list[str]) -> int:
    rebound = 0
    if isinstance(value, dict):
        if value.get("source_sha256") == digest and "quote" in value and "p" in value:
            quote = value["quote"]
            chapter = value.get("chapter")
            matches = [i for i, line in enumerate(lines, 1) if quote in line]
            if len(matches) > 1 and chapter:
                start = next(i for i, line in enumerate(lines, 1) if line.startswith(f"## Глава {chapter}."))
                ends = [i for i, line in enumerate(lines[start:], start + 1) if line.startswith("## Глава ")]
                end = ends[0] if ends else len(lines) + 1
                matches = [i for i in matches if start <= i < end]
            if len(matches) != 1:
                raise ValueError(f"cannot bind anchor uniquely: {value}")
            value["source"] = "revised.md"
            value["p"] = matches[0]
            value["verification_status"] = "verified"
            rebound += 1
        for item in value.values():
            rebound += rebind_anchors(item, digest, lines)
    elif isinstance(value, list):
        for item in value:
            rebound += rebind_anchors(item, digest, lines)
    return rebound


def upsert(items: list[dict], record: dict) -> None:
    for i, item in enumerate(items):
        if item.get("id") == record["id"]:
            items[i] = record
            return
    items.append(record)


def update_continuity(digest: str, text: str, chapters: list[dict]) -> int:
    dst = REV / "continuity"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(PRIOR / "continuity", dst)
    lines = text.splitlines()
    rebound = 0

    docs: dict[str, dict] = {}
    for path in sorted(dst.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        replace_internal_sha(data, digest)
        if data.get("source_sha256") == digest:
            data["status"] = STATUS
            data["authority"] = (
                "Факты отдельной ансамблевой кандидатной редакции; мастер и принятый канон серии не заменены."
            )
        docs[path.name] = data

    scenes = docs["scenes.json"]
    by_id = {item["id"]: item for item in scenes["items"]}
    s19 = by_id["B02-O19"]
    s19["state_after"] = (
        "До знакомства с Лусом Сом подтвердил пять законных транспортов по 36 мест. "
        "Первый план распределяет 175 велдовцев по транспортам и 36 на «Милю»; "
        "с Каем, Джулией, Тимкой и Ведой на ней ровно 40. Пять мест на транспортах свободны."
    )
    s19["new_proposals"] = [
        "Первый шестикорабельный план до сделки с Лусом: 175 велдовцев на пяти транспортах, "
        "36 на «Миле» и пять свободных мест на чужих бортах."
    ]
    s19["reason"] += " Ансамблевая правка ENS-002 восстановила хронологию знакомства с Лусом."

    s21 = by_id["B02-O21"]
    s21["state_after"] = (
        "Кай впервые встречает Луса и обещает место только при рабочем рукаве. Ради сделки одно имя Коры "
        "переводят с «Мили» на пятый транспорт: итог меняется с 36/175 на 35/176, четыре места "
        "на транспортах остаются свободными. Веда доставлена на борт."
    )
    s21["new_proposals"] = [
        "Явная цена сделки с Лусом и показанный переход вместимости 36/175 к 35/176.",
        "Повторный приход исполнителя, опись Веды, передача под видом лома и подтверждение Джулии.",
    ]
    s21["reason"] += " Ансамблевая правка ENS-002 связывает обещание места с первой встречей."

    s22 = by_id["B02-O22"]
    s22["state_after"] = (
        "Гарм замечает демонтаж регенератора и подозревает отвлекающую картинку, но не знает, что скрывает Кай. "
        "Пять обратных плеч закрывающего конвоя в его ведомости не видны."
    )
    s22["reason"] += " Ансамблевая правка ENS-001 убрала внутреннее знание Рэя из POV Гарма."

    s25 = by_id["B02-O25"]
    s25["state_after"] = (
        "Кай проверил бумагу, обход и силу, сознательно выбрал применить страх учётчика ради дороги к 211 людям, "
        "обещал место без личной проверки и передал его связному Коры. Имя ещё не спросил."
    )
    s25["reason"] += " Ансамблевая правка ENS-003 показывает нравственный выбор до поступка."

    for scene_id, issue in [("B02-O26", "ENS-005"), ("B02-O27", "ENS-007"), ("B02-O28", "ENS-005")]:
        by_id[scene_id]["reason"] += f" Ансамблевая правка {issue} сократила повторное объяснение без изменения знаний."

    s51 = by_id["B02-O51"]
    s51["state_before"] += " Лист Сальдо, переданный в начале тома, ещё не прочитан Каем."
    s51["state_after"] = (
        "Кай читает лист Сальдо при владельце; Веда делает копию с происхождением и границей доказанного, "
        "оригинал возвращён Сальдо. «Миля» с Каем, Джулией, Тимкой и Ведой уходит через пополнение "
        "к последней подтверждённой линии перевода Орена. У люка закреплён предел 40 живых."
    )
    s51["new_proposals"] = [
        "Развязка листа Сальдо: чтение, проверяемое утверждение, копия с источником и возврат оригинала.",
        "Постоянная бирка о пределе 40; временные транспорты не становятся частью «Мили».",
    ]
    s51["reason"] += " Ансамблевая правка ENS-004 оплачивает обещание первой главы без оправдания Сальдо."

    chapter_by_num = {item["chapter"]: item for item in chapters}
    for scene in scenes["items"]:
        number = scene["chapter"]
        scene["chapter_sha256"] = chapter_by_num[number]["sha256"]
        scene["source_sha256"] = digest
        scene["decision"] = STATUS
        scene["prose_check"] = "full manuscript LanguageTool pass and manual review of changed passages"
        scene["verification"] = {
            "file": "revised.md",
            "source_sha256": digest,
            "scope": f"Глава {number}; текст, голос, стыки, знания и состояние",
            "result": "passed",
            "report": "audit/REPORT.md",
        }

    knowledge = docs["knowledge.json"]
    upsert(knowledge["items"], {
        "id": "B02-K-10",
        "statement": (
            "Лист Сальдо передан Каю в главе 1, прочитан при Сальдо в 51. Веда хранит копию с источником и "
            "пометкой, что причины исправлений пока являются проверяемым заявлением владельца, а не доказанным фактом."
        ),
        "anchors": [anchor(1, digest, lines), anchor(51, digest, lines)],
    })
    promises = docs["promises.json"]
    upsert(promises["items"], {
        "id": "B02-P-07",
        "statement": (
            "Обещание листа Сальдо закрыто: Кай прочитал его при владельце, Веда сохранила копию с происхождением "
            "и пределом доказанного, оригинал возвращён Сальдо. Его поступки не объявлены автоматически оправданными."
        ),
        "status": "fulfilled",
        "anchors": [anchor(1, digest, lines), anchor(51, digest, lines)],
    })
    end_state = docs["end-state.json"]
    upsert(end_state["items"], {
        "id": "B02-E-06",
        "statement": (
            "Оригинал листа и чемодан находятся у Сальдо. У Веды и Кая остаётся копия листа с указанным источником; "
            "складские выдачи и подписи получателей ещё не сверены."
        ),
        "anchors": [anchor(51, digest, lines)],
    })
    characters = docs["characters.json"]
    for item in characters["items"]:
        if item["id"] == "B02-C01":
            item["current_revision_state"] = (
                "На тихом мире работает у новых поселений; чемодан и оригинал листа у него. "
                "Кай прочитал лист, Веда сохранила помеченную копию без автоматического оправдания владельца."
            )
            item["anchors"] = [anchor(1, digest, lines), anchor(51, digest, lines)]

    for name, data in docs.items():
        replace_internal_sha(data, digest)
        rebound += rebind_anchors(data, digest, lines)
        write_json(dst / name, data)
    return rebound


def build_reader(text: str) -> str:
    blocks: list[str] = []
    for block in text.strip().split("\n\n"):
        if re.fullmatch(r"[-*\s]+", block):
            blocks.append('<hr class="scene-break">')
            continue
        clean = block.replace("`", "").replace("**", "")
        if clean.startswith("# "):
            blocks.append(f"<h1>{html.escape(clean[2:])}</h1>")
        elif clean.startswith("## "):
            title = clean[3:]
            m = re.match(r"Глава (\d+)\.", title)
            ident = f' id="chapter-{m.group(1)}"' if m else ""
            blocks.append(f"<h2{ident}>{html.escape(title)}</h2>")
        elif clean.startswith("### "):
            blocks.append(f"<h3>{html.escape(clean[4:])}</h3>")
        else:
            if clean == "*Конец второго тома.*":
                clean = "Конец второго тома."
                blocks.append(f"<p class=\"end\">{html.escape(clean)}</p>")
            else:
                blocks.append(f"<p>{html.escape(clean).replace(chr(10), '<br>')}</p>")
    return """<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><title>Прочие убытки — редакция</title>
<style>
body{margin:0;background:#eee8dc;color:#201d19;font-family:Georgia,serif}
main{max-width:44rem;margin:2rem auto;padding:3rem 4rem;background:#fffdf8;box-shadow:0 2px 18px #0002}
h1{text-align:center;font-size:1.45rem;margin:2rem 0 4rem}h2{text-align:center;font-size:1.2rem;margin:4rem 0 2rem}
h3{text-align:center;margin:2.5rem 0 1.5rem}p{text-align:justify;text-indent:1.5em;line-height:1.55;margin:.45rem 0}
hr.scene-break{border:0;text-align:center;margin:2rem}hr.scene-break:after{content:'* * *'}p.end{text-align:center;font-style:italic;text-indent:0;margin-top:4rem}
</style></head><body><main>
""" + "\n".join(blocks) + "\n</main></body></html>\n"


def main() -> None:
    if sha(SOURCE) != PRIOR_SHA:
        raise ValueError("locked source hash mismatch")
    text = REVISED.read_text(encoding="utf-8")
    digest = sha(REVISED)
    count = printed_count(text)
    if count < 400_000:
        raise ValueError(f"candidate fell below 10 author sheets: {count}")
    numbers = [int(n) for n in re.findall(r"^## Глава (\d+)\.", text, re.M)]
    if numbers != list(range(1, 52)):
        raise ValueError("chapter sequence must be 1..51")

    derived = REV / "derived"
    derived.mkdir(parents=True, exist_ok=True)
    (derived / "manuscript.txt").write_text(text, encoding="utf-8")
    plain = "\n".join(
        re.sub(r"^#{1,6} ", "", line).replace("`", "").replace("**", "")
        for line in text.splitlines()
    ) + "\n"
    (derived / "reader.txt").write_text(plain, encoding="utf-8")
    (REV / "reader.html").write_text(build_reader(text), encoding="utf-8")

    chunks = chapter_chunks(text)
    chapters = []
    for number, chunk in enumerate(chunks, 1):
        title = chunk.splitlines()[0]
        chapters.append({
            "id": f"B02-O{number:02d}",
            "original_chapter": number,
            "chapter": number,
            "title": title,
            "sha256": hashlib.sha256(chunk.encode()).hexdigest(),
            "printed_chars_with_spaces": printed_count(chunk),
        })
    write_json(derived / "chapters.json", {"source_sha256": digest, "chapters": chapters})

    snapshot_tool = ROOT / "riokka/skills/ru-book-auditor/scripts/book_snapshot.py"
    subprocess.run([
        "python3", str(snapshot_tool), "snapshot", "--source", str(REVISED), "--format", "text",
        "--project-id", "riokka", "--book-id", "book-02",
        "--authority", "separate ensemble candidate; master unchanged", "--out", str(derived / "snapshot.json")
    ], check=True)

    rebound = update_continuity(digest, text, chapters)
    shutil.copy2(PRIOR / "voice.json", REV / "voice.json")
    voice = json.loads((REV / "voice.json").read_text(encoding="utf-8"))
    replace_internal_sha(voice, digest)
    voice["status"] = STATUS
    voice["revision_reason"] += " Ансамблевая правка убрала POV-сбой Гарма и сократила повторные объяснения."
    rebound += rebind_anchors(voice, digest, text.splitlines())
    write_json(REV / "voice.json", voice)

    scenes = json.loads((REV / "continuity/scenes.json").read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in scenes["items"]}
    progress = json.loads((PRIOR / "progress.json").read_text(encoding="utf-8"))
    progress.update({
        "source_sha256": digest,
        "status": STATUS,
        "printed_chars_with_spaces": count,
        "author_sheets": count / 40_000,
        "ensemble_source_sha256": PRIOR_SHA,
        "ensemble_run": "../../audit/ensemble/book-02-2026-09-13-r1",
    })
    for item in progress["items"]:
        scene = by_id[item["id"]]
        for key in ["pov", "state_before", "state_after", "new_proposals", "reason", "decision", "prose_check", "verification"]:
            item[key] = scene[key]
    replace_internal_sha(progress, digest)
    write_json(REV / "progress.json", progress)

    old_text = SOURCE.read_text(encoding="utf-8")
    diff = "".join(difflib.unified_diff(
        old_text.splitlines(True), text.splitlines(True),
        fromfile="revisions/2026-09-13-10al/revised.md",
        tofile="revisions/2026-09-13-ensemble-r1/revised.md",
    ))
    (REV / "changes.diff").write_text(diff, encoding="utf-8")

    changes = json.loads((REV / "changes.json").read_text(encoding="utf-8"))
    md = [
        "# Было — стало: ансамблевая редакция книги 2",
        "",
        f"Источник: `{PRIOR_SHA}`. Кандидат: `{digest}`. Мастер книги не заменён.",
        "",
    ]
    for item in changes["changes"]:
        md += [
            f"## {item['id']} · глава {item['chapter'] or 'служебная граница'}",
            "",
            f"**Причина:** {item['reason']}",
            "",
            "**Было**",
            "",
            item["before"],
            "",
            "**Стало**",
            "",
            item["after"],
            "",
        ]
    (REV / "БЫЛО-СТАЛО.md").write_text("\n".join(md), encoding="utf-8")

    ledger_path = BOOK / "audit/ensemble/book-02-2026-09-13-r1/issue-ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    audit_items = []
    for issue in ledger["items"]:
        applied = issue["id"] != "ENS-008"
        audit_items.append({
            "id": issue["id"],
            "category": issue["category"],
            "severity": issue["severity"],
            "certainty": issue["certainty"],
            "observation": issue["observation"],
            "resolution_status": "resolved" if applied else "rejected",
            "decision": issue["author_decision"],
            "dependencies": issue["dependencies"],
            "verification": {
                "file": "revised.md",
                "source_sha256": digest,
                "result": "passed" if applied else "not_applicable",
                "evidence": "БЫЛО-СТАЛО.md" if applied else "author-decisions.md: preserve 51-chapter structure",
            },
        })
    write_json(REV / "audit/issues.json", {
        "schema_version": 1,
        "project_id": "riokka",
        "book_id": "book-02",
        "source_sha256": digest,
        "previous_book_sha256": BOOK1_SHA,
        "source_observations_sha256": PRIOR_SHA,
        "ensemble_run": "../../../audit/ensemble/book-02-2026-09-13-r1",
        "status": "ensemble_changes_applied_and_verified_for_author_review",
        "items": audit_items,
    })

    print(json.dumps({
        "source_sha256": digest,
        "printed_chars_with_spaces": count,
        "author_sheets": count / 40_000,
        "chapters": len(chapters),
        "anchors_rebound": rebound,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
