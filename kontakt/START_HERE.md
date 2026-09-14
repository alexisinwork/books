# Начать работу с Контактом

1. Выберите books/book-01…book-07. Прочитайте её brief.md, plan.md, voice.json, session.md.
2. Откройте series/CANON-POLICY.md, continuity-queue.json и костяк нужного тома.
3. Разверните сцену, зафиксируйте допущения; после написания выберите мастер.

```sh
python tools/studio.py doctor
python tools/studio.py context --book book-01 --task "Развернуть первую сцену Контакта" --out sessions/book-01-start.md
```

Общая методика применена в guides/SYSTEM-APPLICATION.md. Редактура Риокки и отзыв брата не являются отзывом на эту серию.

## Украинский оригинал и языковые издания

Новый рабочий процесс: [BOOK_SYSTEM](../BOOK_SYSTEM/README.md), путь также задан в `project.json.book_system`. Новая книга создаётся на украинском; `new-book --language en` — явный английский оригинал. Русские файлы остаются историческими источниками. Для Риокки 1–3 сначала RU→UK, затем после авторского утверждения UK→EN; прямой RU→EN — отдельный зеркальный маршрут. Рукописи в ходе настройки системы не переводились. Литературный цикл требует Opus + Gemini 3.8 Flash + Gemini 3.1 Pro.
