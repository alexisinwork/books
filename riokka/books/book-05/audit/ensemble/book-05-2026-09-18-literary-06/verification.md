# Перевірка застосованої редакції

Run ID: `book-05-2026-09-18-literary-06`
Source SHA-256: `838a424268fa7c044bc5eb3adc30118dbe208f0ce48c90f6ea78e0debe9acd28`
Role: `verification`
Model: Claude Opus 5 (`claude-opus-5`)
Client: Claude Code subagent (навичка `ru-approved-revision`). Перевірку виконує та сама модель, що вносила правки, — це не незалежна вичитка.
Status: final

## Застосовані рішення

41 пункт реєстру застосовано (accepted 29 + modified 12), 5 відхилено з поясненням (ENS-037, 038, 042, 043, 044); ENS-045 — відповіді без зміни тексту. Детально: `issue-ledger.json` (implementation / verification кожного пункту), `revisions/2026-09-18-literary-07/edits.json` (112 правок з ENS-ID, розділом, рядком майстра, було/стало, підставою), `БУЛО-СТАЛО.md`, `changes.diff`. Делеговані авторські питання Q1–Q9 — `author-questions-answered.md`.

Розділи з правками: 1–6, 11–18, 20, 21, 23, 24, 26–28, 30, 31, 33–37, 39–41, 43–49, Кода II, Фінал, титул.

## Нова версія

- `riokka/books/book-05/revisions/2026-09-18-literary-07/Riokka_5_UK_literary_07.txt` — SHA-256 `79dfd767c6fdbfa2bb1071a3afe966e32555ffd57714bfe8e26aae8fae545655`, 3585 абзаців.
- `…/Riokka_5_UK_literary_07.docx` — SHA-256 `0b00a186f60290de2ed6aae95e53123c988540ec1c281cb697b96b8d37ccdc8a`.
- Статус: робоча редакція-кандидат. Попередня версія не змінювалась і лишається на місці: `editions/uk/canonical-2026-09-17/manuscript.txt` (`838a4242…`), `manuscript/master.docx` (`2288c57f…`, перевірено після запису — хеш той самий).

## Неперервність і похідні файли

- Канон перевірено для змінених місць: RIOKKA-LAD-SVITLOYAR і RIOKKA-WILD-TRANSMISSION-LIMITS (розд. 47), RIOKKA-POLYA-IS-TEIS-DAUGHTER (фінал не змінювався в цій частині), RIOKKA-WILD-SPREAD-SCALE (не зачеплено); т. 0 canonical-2026-09-18 і т. 3 final — історія Ільса (розд. 48); т. 4 end-state ES-06/ES-11/ES-13, promises P-06, motifs M-01/M-05 — розд. 35, 37, 41, фінал.
- Нове знання героїв з’являється через подію: Кай — схожість почерків (розд. 35, Веда кладе записи поруч); Кай — Верин знав про Ільса (розд. 48, лист Верина); Джулія — Ведина таблиця (Кода II, спільний пакет справи).
- **Не оновлено** (поза межами доручення, робить оператор): `book.json`, `revision-log.json`, `session.md`, `knowledge.json`, `promises.json`, `motifs.json`, `scenes.json`, `derived/`, `editions/`. Якорі інших записів, що посилаються на рядки майстра після р. 5415, для редакції 07 зсунуті — мають статус `stale` до перепривʼязки.

## Проза й механічні перевірки

- Перечитано в контексті всі змінені абзаци та стики: розд. 35 (нова сцена), 37, 40–41, 48, Кода II, фінал; решта — точкові заміни, перевірені в межах абзацу.
- `python tools/language_qa.py --source …/Riokka_5_UK_literary_07.txt --language uk --out …/language-qa.json` → `no_configured_signals`, 0 знахідок, 3585 непорожніх одиниць, 68 962 токени.
- `python tools/uk_naturalness.py --source …/Riokka_5_UK_literary_07.txt --out …/audit-uk-naturalness.json` → `no_unresolved_configured_signals`, 0 знахідок (ruleset uk-naturalness-1.2).
- grep-звірка `edits.json` ↔ TXT: 112/112 — кожне «стало» присутнє, кожне «було» відсутнє у зміненому абзаці (`grep-verification.txt`; для одного загального підрядка «— сказав нарешті.» зафіксовано, що він лишився лише у двох свідомо не змінених діалогах).
- Реєстр перевірено вручну проти `editorial/schemas/issue-ledger.schema.json` (обовʼязкові поля й enum): 0 помилок (`jsonschema` у середовищі немає).
- LanguageTool / Vale не запускались (недоступні). Інструменти не засвідчують літературної якості.

## DOCX

- `tools/revise_docx_text.py extract` майстра = TXT майстра побайтно (перевірено до правок).
- Структура: 10 абзаців видалено, 4 клоновано з `pPr` сусіднього абзацу (scratch-скрипт на функціях `revise_docx_text.py`) → проміжний шаблон `b0beb6d40b7b1d371579767be6536f1c4220ed7ed881fc503d23aa01292f9b82`; `apply --expected-template-sha256 b0beb6d4…` → вбудована перевірка тексту пройдена, `template_unchanged=true`; повторний `extract` → `cmp` з TXT: збіг (3585/3585).
- Візуальний рендер не виконано (немає Word/LibreOffice).

## Залишкові питання

- Q1–Q9 — делеговані рішення, чекають перегляду автора (особливо Q1: Верин знав, що Ільс живий).
- Астра `unavailable`; для редакції 07 потрібен новий прогін із новим SHA і нове сліпе читання без згадки про правки.
- Синхронізація файлів неперервності та `book.json` — за оператором; `editorial_ensemble.py record` не запускався, коміту й копій на робочий стіл не робилось (за дорученням).
