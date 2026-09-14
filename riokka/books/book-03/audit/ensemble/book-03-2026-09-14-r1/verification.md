# Проверка применённой редакции

Run ID: `book-03-2026-09-14-r1`
Source SHA-256: `353360345b999d66f5e12b6a5fa2d871c4e7c4a9247414a265894e6439141cdd`
Role: `verification`
Model: Claude Opus 5 (`claude-opus-5[1m]`)
Client: Claude Code 2.1.270
Status: final

## Применённые решения

Все 23 пункта реестра (20 accepted, 3 modified) применены в отдельной редакции; rejected и deferred нет. Файлы глав указаны в новой нумерации (58 глав).

- `ENS-001` (accepted): 01–03, 04 (слияние 4+5), 05–12
- `ENS-002` (accepted): 13
- `ENS-003` (accepted): 20, 21
- `ENS-004` (accepted): 28, 29 (слияние 30+31), 30, 31, 32, 33
- `ENS-005` (accepted): 45, 46, 54
- `ENS-006` (accepted): 17, 20, 21, 33, 34, 36
- `ENS-007` (accepted): 43, 46, 47, 48
- `ENS-008` (accepted): 04, 18
- `ENS-009` (accepted): 07, 21, 22, 23, 27, 29, 30, 41, 43, 52, 53
- `ENS-010` (accepted): 10, 38, 45
- `ENS-011` (accepted): 01, 02, 03, 07, 08, 11, 12, 18, 19, 37, 39, 42, 57, 58
- `ENS-012` (accepted): 36, 37
- `ENS-013` (accepted): 21, 29
- `ENS-014` (modified): 52
- `ENS-015` (modified): 41, 45, 54, 58
- `ENS-016` (accepted): 26, 27
- `ENS-017` (accepted): 51, 52
- `ENS-018` (accepted): 42
- `ENS-019` (accepted): 10, 11, 15, 16, 23, 52
- `ENS-020` (accepted): 01, 05, 16, 20, 35
- `ENS-021` (modified): 48, 49
- `ENS-022` (accepted): 31, 56
- `ENS-023` (accepted): 43, 58

Состояние прогона до применения: у Astra и сведения стоял `locked` без SHA-256 — хеши записаны как `integrity_repair` в `run.json` без изменения содержимого (у Astra заголовок по-прежнему `Status: draft`). Сведение оставило реестр пустым; реестр составлен на этапе применения из сведения и трёх отчётов. Решения автора записаны дословно в `author-decisions.md` и зафиксированы `lock-decisions`.

## Новая версия

- Путь: `riokka/books/book-03/revisions/2026-09-14-ensemble-r1/revised.md`
- SHA-256: `02aef0016f9664531be1115d95b78eb0c255e52fd09f550b2c7f84f2c9dce4e8`
- Статус: `ensemble_revision_for_author_review`, `author_selected: false`; `book.json.working_revision` указывает на неё, прежняя сохранена в `previous_working_revision`.
- Объём: 58 глав, 417487 знаков с пробелами (10.4372 а.л.); прежняя — 60 глав, 440 324.
- Архив: прежняя редакция `revisions/2026-09-13-expanded/revised.md` (SHA `35336034…`) не изменялась; хеши её 60 глав — `revisions/2026-09-14-ensemble-r1/archive/base.json`. Мастер `manuscript/master.md` и `sources/originals` не менялись.

## Непрерывность и производные файлы

- `continuity/notes.json`, `scenes.json`, `timeline.json` перенумерованы (60 → 58; слияния 4+5 и 30+31), затронутые состояния обновлены; `knowledge`, `promises`, `motifs`, `characters`, `resources`, `end-state`, `research`, `entry-state` перепривязаны к новому SHA: 254 якоря, несовпадений 0. Новые записи: `esquire_pier_turn`, `oren_last_words`, `tikhon_pier`, `salt_model`, `oren_words`, `julia_pier`.
- `derived/manuscript.txt`, `derived/reader.txt`, `derived/snapshot.json`, `derived/chapters.json`, `derived/docx-extracted.txt`, `reader.html`, `changes.diff`, `changes.json`, `БЫЛО-СТАЛО.md`, `progress.json`, `release.json`, `voice.json` (scene_overrides).
- Книга: `book.json`, `README.md`, `session.md`, `revision-log.json` (B03-ENSEMBLE-R1-2026-09-14), `audit/issues.json` (B03-ENS-BOOK4-BASIS, unresolved); серия: `series/continuity-queue.json` (BOOK03-ENSEMBLE-R1-TRANSITION). Том 4 не менялся.

## Проза и механические проверки

- Перечитывание в контексте каждой замены: `revisions/2026-09-14-ensemble-r1/audit/reread-sheet.md`; стыки переписанных глав прочитаны; после чтения исправлены 6 мест (`work/applied-after-review.json`). Полное повторное чтение всех 58 глав подряд не выполнялось.
- `java -jar LanguageTool-6.6/languagetool-commandline.jar -l ru-RU --json revised.md` (локальный JRE): 634 срабатывания против 657 у прежней редакции; в изменённых строках 84, из них по существу 4 → 3 исправлены, остальные — имена собственные.
- Счётчики фигур: `audit/prose-metrics.json`.
- `python3 build.py` (сборка и привязка), `python3 sync_continuity.py` (без неразрешённых цитат), `python3 riokka/tools/studio.py doctor` — errors: []; `python3 riokka/tools/verify_sources.py` — 30 исходников, errors: [].

## DOCX или другой читательский файл

- `Риокка — Книга 3 — Холм Розмари — ансамблевая редакция.docx`, SHA-256 `b7bf2fdbeb2d9917dcde022b0bc82762b81b6e9b8a9fe82b45d854ee9b1d6c05`; PDF-рендер Writer 26.2 (частный распакованный LibreOffice), SHA-256 `1e524b57b0c48c3709506f9b75624956adc6181e6dd0fc9e4e1127742139e8c2`, 205 страниц.
- `export_reader.py`: абзацы DOCX совпадают с рукописью (3766), текст PDF совпадает без учёта пробелов, номера страниц в колонтитуле верны, выходов за поля и пустых страниц нет, все 58 глав найдены.
- Осмотрены изображения: контактный лист 141–160 и страница 146 (заголовки части и главы, поля, колонтитул, короткая гл. 45).
- Копия на рабочем столе: `C:\Users\alexi\Desktop\Риокка — Книга 3 — ансамблевая редакция 2026-09-14` (DOCX, PDF, «Было — стало», вопросы, README), хеши сверены — `audit/desktop-files.json`.

## Остаточные вопросы

- B03-ENS-BOOK4-BASIS (unresolved): основой тома 4 записана прежняя редакция; переход на новую — решение автора. Там же расхождения «всошло само, везде» и «на холме».
- ENS-022: названия гл. 31 и 56 сохранены как мостовые, вынесены автору.
- Новый слепой прогон Gemini по SHA `02aef001…` не выполнялся; нужен новый run-id и пакет без списка правок.
- Чтение вслух не выполнялось; полный аудит чисел и хронологии всей книги не повторялся.
