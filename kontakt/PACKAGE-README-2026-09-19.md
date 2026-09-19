# Kontakt pre-draft lock package

Подготовлено 19.09.2026.

Почему это ZIP, а не commit: подключённый GitHub App вернул `403 Resource not accessible by integration` на `create_file`, `create_branch` и Git Data write. Чтение репозитория работало, запись — нет.

Содержимое:
- `kontakt/series/PRE-DRAFT-LOCK-2026-09-19.md` — главный authority-файл.
- `kontakt/series/SOCIAL-PROBLEMS-MAP.md` — социальная проблема каждого из 8 томов.
- `kontakt/series/WAR-UKRAINE-RESEARCH-2026.md` — исследовательская рамка книги 8.
- `kontakt/series/series-engine.md` — новая 8-книжная макроспина.
- `kontakt/series/canon.json` — locked facts.
- `kontakt/series/continuity-queue.json` — блокеры закрыты.
- `kontakt/books/book-01...07/PRE-DRAFT-LOCK.md` — покнижные дополнения.
- `kontakt/books/book-08/` — новый том «Поимённо»: `book.json`, `brief.md`, `plan.md`, `voice.json`.

Рекомендуемый commit после выдачи write-доступа:
`feat(kontakt): lock 8-book architecture and add war capstone`
