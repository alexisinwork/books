# Начать работу с Контактом

1. Выберите books/book-01…book-07. Прочитайте её brief.md, plan.md, voice.json, session.md.
2. Откройте series/CANON-POLICY.md, continuity-queue.json и костяк нужного тома.
3. Разверните сцену, зафиксируйте допущения; после написания выберите мастер.

```sh
python tools/studio.py doctor
python tools/studio.py context --book book-01 --task "Развернуть первую сцену Контакта" --out sessions/book-01-start.md
```

Общая методика применена в guides/SYSTEM-APPLICATION.md. Редактура Риокки и отзыв брата не являются отзывом на эту серию.
