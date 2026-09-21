# Начать работу с «Разладом»

## Текущая стадия

Серия: **8 книг, pre-draft locked, готова к первому архитектурному проходу**.  
Рукописей ещё нет. До завершения Architecture Pass 01 художественную прозу не писать.

## Порядок входа

1. `series/PRE-DRAFT-LOCK-2026-09-19.md` — главный authority.
2. `series/ARCHITECTURE-PASS-01.md` — контракт ближайшей работы.
3. `series/book-matrix.md` — различимость 8 томов и межтомная причинность.
4. `series/character-arcs.md` — сквозные персонажи.
5. `series/reveal-ladder.md` — лестница раскрытий.
6. `series/SOCIAL-PROBLEMS-MAP.md` — социальная проблема каждого тома.
7. Выбранный `books/book-XX/`: `book.json` → `brief.md` → `PRE-DRAFT-LOCK.md` → `ARCHITECTURE-READINESS.md` → `plan.md` → `voice.json`.

## Что делать сейчас

Первый проход — **архитектурный**, не литературный.

Для каждого тома:
- восстановить причинную цепь сцен из исторического костяка;
- уточнить `goal / obstacle / decision / result / cost / next_cause`;
- проверить внешнюю цель, внутреннюю арку, противодействие и кульминацию без привязки к одинаковым номерам глав;
- заполнить planned-уровень `characters.json`, `knowledge.json`, `promises.json`, `timeline.json`, `resources.json`, `end-state.json`;
- проверить вход тома = выход предыдущего;
- после каждого тома обновить `series/architecture-pass-01-status.json`.

**Только после статуса `ready_for_draft` разрешается писать главу 1.**

## Язык

Новая проза — украинский оригинал. Русские исходные планы — legacy/provenance и не переписываются.
