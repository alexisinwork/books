# Независимая редакторская ревизия

Git хранит версии, канон, отчёты и решения. С 14 сентября 2026 новые прогоны используют схему 2: четыре обязательных диагноза на одном SHA-256. Старые прогоны схемы 1 сохраняются без переписывания истории. Язык задаётся проверяемым изданием; новые оригиналы — украинские, английские по прямому выбору автора.

| Роль / ключ | Исполнитель | Задача и изоляция |
|---|---|---|
| Главный редактор / `astra` | Astra, ChatGPT/Codex | Структура, причинность, арки, знания, числа, обещания. До фиксации не читать чужие отчёты. |
| Литературный редактор / `claude` | Claude Opus | Проза, сцены, темп, эмоция, голоса. Независимый диагноз без переписывания. |
| Проверка связей / `gemini_flash` | Gemini 3.8 Flash | Полнота охвата, повторения, голоса, терминология, callbacks и согласованность. Без чужих отчётов; каждый вывод с якорем. |
| Холодный читатель / `gemini` | Gemini 3.1 Pro | Только изолированная читательская версия и нейтральная инструкция; без канона, intent, исходника другой языковой версии и подсказок о правках. |

После четырёх зафиксированных отчётов Astra сводит замечания. Совпадение мнений — сигнал, не голосование за канон. Автор принимает, отклоняет, изменяет или откладывает пункты. Sol/Opus применяет только разрешённый совместимый пакет и синхронизирует зависимости. Новый текст получает новый прогон слепого чтения.

В отчётах записываются фактические модели и клиенты, объём чтения, непрочитанное и точные доказательства. Репозиторий не переключает личные подписки и модели автоматически. Отсутствующий Opus, Flash или Pro — `not_run`/`unavailable`, а не заменённый собственной имитацией независимый отчёт. Для адаптации см. отдельные [правила](BOOK_SYSTEM/REVIEW.md) и [инструменты](BOOK_SYSTEM/TOOLS.md): двуязычный reviewer дополнительно независим от основного адаптера.

## Структура прогона

Инструмент создаёт внутри книги:

```text
audit/ensemble/RUN_ID/
├── run.json
├── astra-diagnosis.md
├── claude-diagnosis.md
├── gemini-flash-diagnosis.md
├── gemini-blind-read.md
├── reconciliation.md
├── issue-ledger.json
├── author-decisions.md
└── verification.md
```

`run.json` фиксирует источник и состояние этапов. Зафиксированный отчёт получает SHA-256; последующее молчаливое изменение обнаруживает команда `verify`. Для исправленного отчёта создайте новый прогон либо явно начните заменяющий прогон.

## Один полный цикл

Все команды запускаются из корня репозитория. Идентификатор прогона должен быть уникальным и не содержать пробелов.

```bash
python3 tools/editorial_ensemble.py init \
  --project riokka \
  --book book-02 \
  --run-id book-02-2026-09-13-r1
```

Для украинской версии добавьте `--language uk`, для английской `--language en`; у старого RU-исходника — `--language ru`. Это язык фактического файла, не будущего перевода. `--source` не выбирает канонический мастер автоматически.

Если проверяется не версия из `book.json.working_revision` и не мастер, передайте точный путь через `--source`. Для DOCX отдельно передайте проверенную текстовую проекцию через `--reader-file`. Команда откажется продолжать при несовпадении заявленного и фактического хеша.

Первый независимый проход в ChatGPT/Codex:

```text
$ru-chief-editor
Выполни независимый полный диагноз по прогону book-02-2026-09-13-r1.
```

После заполнения `astra-diagnosis.md` установите в нём `Status: final` и зафиксируйте:

```bash
python3 tools/editorial_ensemble.py record \
  --run riokka/books/book-02/audit/ensemble/book-02-2026-09-13-r1 \
  --role astra
```

Независимый проход Claude Code:

```text
/ru-literary-editor book-02-2026-09-13-r1
```

Затем:

```bash
python3 tools/editorial_ensemble.py record \
  --run riokka/books/book-02/audit/ensemble/book-02-2026-09-13-r1 \
  --role claude
```

Независимо запустите Gemini 3.8 Flash по тому же файлу/SHA, без отчётов Astra/Opus/Pro. Заполните `gemini-flash-diagnosis.md` с картой покрытия, затем:

```bash
python3 tools/editorial_ensemble.py record --run PATH_TO_RUN --role gemini_flash
```

Для Gemini 3.1 Pro сначала создайте изолированную папку вне репозитория:

```bash
python3 tools/editorial_ensemble.py blind-pack \
  --run riokka/books/book-02/audit/ensemble/book-02-2026-09-13-r1
```

Перейдите в выведенный каталог, запустите `gemini`, при необходимости выполните `/skills reload`, затем вызовите `/ru-cold-reader`. Gemini сохраняет итог в `REPORT.md`. Импортируйте его, указав выведенный путь:

```bash
python3 tools/editorial_ensemble.py record \
  --run riokka/books/book-02/audit/ensemble/book-02-2026-09-13-r1 \
  --role gemini \
  --input /tmp/books-editorial-ensemble/book-02-2026-09-13-r1-gemini/REPORT.md
```

После четырёх зафиксированных диагнозов используйте `$ru-editorial-reconciler`, заполните `reconciliation.md` и `issue-ledger.json`, затем зафиксируйте сведение:

```bash
python3 tools/editorial_ensemble.py record --run PATH_TO_RUN --role reconciliation
```

Ответы автора записываются в `author-decisions.md` и в поля `author_decision` общего реестра. Пока хотя бы один пункт имеет статус `pending`, этап нельзя закрыть:

```bash
python3 tools/editorial_ensemble.py lock-decisions --run PATH_TO_RUN
```

После применения используйте `$ru-approved-revision`, заполните `verification.md`, выполните проверки проекта и зафиксируйте результат:

```bash
python3 tools/editorial_ensemble.py record --run PATH_TO_RUN --role verification
python3 tools/editorial_ensemble.py verify --run PATH_TO_RUN --require-complete
```

Повторное холодное чтение создаётся как новый прогон по новому SHA-256. В приглашении Gemini не называют исправленные главы, прежние замечания и ожидаемый результат.

## Что хранить в общем реестре

Каждый пункт `issue-ledger.json` содержит происхождение наблюдения, категорию, серьёзность, уверенность, точные места, эффект для читателя, доказательства, варианты изменения, зависимости, решение автора, состояние применения и проверку. Формы и допустимые значения описаны в `editorial/schemas/`.

Несколько моделей могут описывать одну проблему разными словами. При сведении создавайте один пункт и перечисляйте все исходные отчёты. Не объединяйте находки только по похожим словам, если у них разные причины или последствия.

## Обнаружение файлов инструментами

- Codex читает `AGENTS.md` и репозиторные навыки из `.agents/skills`.
- Claude Code читает `CLAUDE.md`; `.claude/skills` указывает на тот же набор навыков.
- Gemini вызывается только через `agy CLI` по постоянному решению автора. Инструкции и разрешённый пакет передаются явно в новую изолированную сессию; автоматическую загрузку навыков другого клиента не предполагать.

Документация механизмов: [Codex skills](https://developers.openai.com/codex/skills), [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md), [Claude Code memory](https://code.claude.com/docs/en/memory), [Claude Code skills](https://code.claude.com/docs/en/skills). Доступные команды и модели `agy` проверять через `agy --help` и `agy models`. Использование `gemini CLI`, включая fallback, запрещено; исторические журналы старых прогонов не переписываются.
