# AI RUNBOOK

Цель: чтобы более простая модель исполняла архитектуру, а не перепридумывала роман.

## Постоянный контекст
Передавать:
1. `CONTEXT-CAPSULE.md`
2. `BOOK-01-ARCHITECTURE-LOCK.md`
3. `WORLD-MECHANICS.md`
4. `characters.planned.json`
5. `knowledge.planned.json`
6. `promises.planned.json`
7. `motifs.planned.json`
8. текущую SXX из `architecture.json`
9. summary предыдущей главы / state delta
10. действующий `voice.json` из repo

## Pipeline
1. `01-CHAPTERIZE-SEQUENCE.md` — только одна SXX.
2. `02-SCENE-CARDS.md` — для одной будущей главы.
3. `03-ARCH-CHECK.md` — gate.
4. `04-WRITE-CHAPTER.md` — одна глава, только после PASS.
5. `05-CONTINUITY.md`.
6. При необходимости `06-REVISE.md`.
7. После sequence — `07-SEQUENCE-RECONCILE.md`.
8. После S12 — `08-BOOK-RECONCILE.md`.

## Не делать
- не chapterize всю книгу одним запросом;
- не писать несколько глав за один запрос;
- не добавлять новый глобальный закон мира;
- не исправлять locked outcome ради красивой сцены;
- не давать модели весь repo без необходимости.

## Если данных не хватает
Возвращать `BLOCKED: <конкретный недостающий факт>`, а не выдумывать новый канон.
