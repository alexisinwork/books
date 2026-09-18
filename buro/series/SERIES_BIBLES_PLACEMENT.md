# Куда положить новые смысловые библии

Ничего из этих файлов не нужно помещать в `BOOK_SYSTEM`: `BOOK_SYSTEM` остаётся общей методологией написания, аудита, версий и адаптации.

Рекомендуемая структура:

```text
riokka/
  series/
    essence.md                    ← RIOKKA_SERIES_ESSENCE.md

buro/
  series/
    essence.md                    ← BURO_SERIES_ESSENCE.md
    world-bible.md                ← BURO_WORLD_BIBLE.md
    character-arcs.md             ← BURO_CHARACTER_ARCS.md
    themes-and-intent.md          ← BURO_THEMES_AND_INTENT.md
    distinctiveness.md            ← BURO_DISTINCTIVENESS_ANTI_RIOKKA.md
    revision-blueprint.md         ← BURO_REVISION_BLUEPRINT.md
```

## Что эти документы НЕ заменяют

Оставить существующими отдельными источниками:

- `series/canon.json` — только конкретные утверждённые факты канона;
- `series/CANON-POLICY.md` — приоритет источников;
- `series/intent.md` — история замысла и текущие открытые решения;
- `series/engine.md` — рабочий сюжетный двигатель Buro;
- `series/book-matrix.md` — различие подачи томов;
- `books/*/characters.json`, `end-state.json`, `timeline.json` — конкретное состояние каждого тома.

## Рекомендуемая роль новых файлов

- `essence.md` — читать первым перед любой большой новой сценой, переписью тома или созданием продолжения.
- `world-bible.md` — физика и институты; предложения постепенно переносить в `canon.json` только после утверждения.
- `character-arcs.md` — психологическая причинность и независимость героев.
- `themes-and-intent.md` — смысловая проверка: что серия говорит и чего случайно говорить не должна.
- `distinctiveness.md` — обязательная проверка на повтор Riokka.
- `revision-blueprint.md` — одноразовый/итеративный маршрут нынешней большой переработки трилогии.

## Статусы

В новых Buro-файлах намеренно используются формулировки «установлено», «вывод», «предлагаемая фиксация». Не переносить `proposed` в канон без отдельного решения автора.
