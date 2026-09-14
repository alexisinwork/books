# Семь постоянных файлов и доказательства

Пути ниже относятся к конкретному изданию, например `books/book-01/editions/uk/`. Служебные MD удобны автору; JSON ведёт проверяемые записи. Они не являются двумя конкурирующими реестрами: в MD указывается машинный источник, а новые решения переносятся явно и с журналом.

| Файл | Содержание и запрещённое смешение |
|---|---|
| `BOOK_BIBLE.md` | События, ограничения, состояния, арки, время; факты отделены от планов. В начале источник/SHA и реальный охват чтения. |
| `AUTHOR_INTENT.md` | Только явные слова автора и их датированное происхождение. ID, сцены, момент доступа читателя, что сохранить, что не раскрывать. Модельные догадки идут в ledger. |
| `UA_STYLE_GUIDE.md` / `EN_STYLE_GUIDE.md` | Целевой язык, регистр, персонажные исключения, действующие правила и их статус, ссылка на общий языковой слой и локальные эталоны. |
| `GLOSSARY_RU_UA.md` / `GLOSSARY_UA_EN.md` / `GLOSSARY_RU_EN.md` | Читаемая карта имён, терминов, склонения, обращений, коротких форм, регистра и вариантов; `glossary.json` — машинный реестр. |
| `CHARACTER_VOICES.md` | Отбор внимания, прямота, словарь, длина/связность реплик, юмор, ошибки речи, отношения и изменения по сценам. Точный пример и предел наблюдения. |
| `MEANING_LEDGER.md` | Читаемое представление `meaning-ledger.json`: функция, setup/payoff, допустимое чтение и запрет преждевременного раскрытия; гипотезы отмечены. |
| `DECISION_LOG.md` | Решение автора, причина, альтернативы, зависимости, затронутые файлы и старый/новый SHA; обычная языковая правка отделена от смены смысла. |

## Смысловая запись

`meaning-ledger.json`: `schema_version`, `book_id`, `source`, `coverage`, `items`.

Пункт: `id`, `type` (`fact`, `causality`, `ambiguity`, `foreshadowing`, `callback`, `humour`, `wordplay`, `metaphor`, `voice`, `intentional_error`, `cultural_reference`), `evidence_kind` (`text_observation`, `model_hypothesis`, `author_statement`), `anchors`, `function`, `must_preserve`, `reader_may_infer`, `reader_must_not_infer_yet`, `setup_ids`, `payoff_ids`, `dependencies`, `resolution_status`, `author_decision`, `target_status`, `target_anchors`, `verification`.

Якорь: `path`, `sha256`, `chapter`, `p`, `quote`, при необходимости границы сцены. Каждый путь относится к корню репозитория. Подтверждение полной цитаты — до изменения её источника. После нового хеша затронутый пункт становится `stale`.

`target_status`: `pending`, `drafted`, `reviewed`, `author_approved`, `stale`. `resolution_status`: `unresolved` или `resolved`; это не статус авторского принятия. Неизвестный payoff остаётся null, а не выдуманной главой.

## Глоссарий

Запись: `id`, `source_form`, `source_pattern`, `target_language`, `preferred`, `allowed_forms`, `forbidden_forms`, `type`, `context_rule`, `status` (`proposed`, `locked`, `rejected`, `deferred`), `author_decision`, `anchors`, `first_appearance`, `dependencies`.

Для украинского включить допустимое склонение и кличные формы. Для английского — артикль, краткое название и регистр. Слова разного смысла не объединять одной глобальной заменой. Предложенный вариант нельзя машинно применять как `locked`. Новая повторяющаяся форма получает решение, единичная контекстная форма — обоснованный локальный выбор.

## Карта соответствия и QA

`translation.json`: `schema_version`, `source_language`, `target_language`, `source_sha256`, `source_segments_sha256`, `glossary_sha256`, `blocks`.

Блок: `source_ids` (порядок исходных единиц), `target_paragraphs` (непустые строки), `alignment_reason` для любого разделения/объединения. Нельзя пропускать или дублировать исходный ID. Заголовок главы и границы глав не объединяются с прозой. Такая карта проверяет покрытие единиц; она не доказывает, что внутри абзаца не потеряна фраза.

QA-пункт: `id`, `severity` S1–S4, `certainty`, `source_anchor`, `target_anchor`, `lost_or_changed_function`, `why_it_matters`, `minimal_correction`, `meaning_ids`, `dependencies`, `author_decision`, `implementation`, `verification`. Числа «preserved X/Y» считаются только по явно рассмотренным пунктам, не по размеру всего файла.

## Эталоны и решения

`GOLD_EXAMPLES/index.json` хранит реальные source / AI draft / author final с тремя хешами, функцией, причиной выбора и областью применимости. Категории: narration, dialogue, humour, action, introspection. Пока авторских примеров нет, каталог отмечен `awaiting_author_samples`; пустой файл не называется эталоном.

Основной адаптационный промпт фиксируется на книгу. Улучшаются профиль, глоссарий и реальные примеры; смена самого контракта требует новой версии и проверки уже написанных зависимостей. Количество терминов или примеров не является квотой готовности.
