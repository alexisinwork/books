# ARCHITECTURE PASS 01 — серия «Разлад»

Статус: **prepared / not run**. Цель — превратить восемь locked outlines в причинно проверенную архитектуру до начала прозы.

## Не входит

Литературная редактура, line edit, написание сцен, корректура, маркетинговая подгонка длины.

## A. Серия целиком

1. Проверить `book-matrix.md`.
2. Проверить `character-arcs.md`.
3. Проверить `reveal-ladder.md`.
4. Проверить вход/выход каждой книги.
5. Проверить монотонность видимости и немонотонность художественной формы.
6. Доказать, что кн.7 — внутренний капстоун, а кн.8 — необходимый внешний экзамен, не DLC.

## B. Каждый том

Для каждого outline beat заполнить/подтвердить: `POV, place, time, goal, obstacle, decision, result, cost, next_cause, state_changes, knowledge_change`.

После этого сгруппировать сцены в главы по естественному ритму. Старые 34 номера — provenance.

## C. Персонажи

Заполнить planned `characters.json`: want, need/question, self-deception, pressure, choice, relationships. Каждый крупный персонаж хочет чего-то кроме «помочь/помешать Далю».

## D. Раскрытия

Заполнить `knowledge.json` и `promises.json`: истина мира → ложная/частичная модель Даля → источник → решение после reveal.

## E. Непрерывность

Заполнить `end-state.json` и минимальный `timeline.json`. Правило: `end-state book-N == admissible start-state book-N+1`.

## F. Социальная проблема

Каждый том обязан показать: система решает реальную проблему; цена системы реальна; простой обратный ответ тоже опасен.

## Gate ready_for_draft

Нет unresolved architecture-critical; цели физически исполнимы; повороты причинны; payoff отличается от соседних томов; вход/выход согласованы; reveal ladder не нарушена; `scenes.json` — причинная цепь, а не summaries; character/knowledge/promises/end-state заполнены; voice baseline locked.

После этого: `stage → ready_for_draft`, voice calibration sample, затем глава 1.
