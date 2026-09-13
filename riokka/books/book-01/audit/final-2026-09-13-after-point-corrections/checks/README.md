# Проверки финального мастера

Все артефакты в этом каталоге относятся к DOCX SHA-256 `2651e6b73fe20e844ff19c4f7f99a39ca90c1da3d53f91a3a3a1417ce3ac4172`.

| Проверка | Результат | Артефакт |
|---|---|---|
| Snapshot кандидата | 42 главы, 1247 абзацев | `candidate-snapshot.json` |
| Чистая проекция | полный текст | `candidate-manuscript.txt` |
| Точные якоря | 47/47, ошибок 0 | `verification-anchors.json`, `anchor-guard.json` |
| Якоря состояния | 40/40, ошибок 0 | `state-anchor-guard.json` |
| Таймер, люди, ресурсы | расхождений 0 | `continuity-signals.json` |
| Механика и LanguageTool | 0 механических; 777 сырых LT-сигналов | `automated-audit.json`, `languagetool.json` |
| DOCX и PDF | 250 страниц, пустых 0, текст совпадает | `structure-and-render.json`, `../render/final/` |
| Назначение мастера | выполнено | `set-master.json`, `master-snapshot.json` |
| Тесты инструментов | 12/12 | `tests.stdout.txt`, `tests.stderr.txt` |
| Целостность оригиналов | 30/30, ошибок 0 | `verify-sources.json` |
| Согласованность проекта | `studio.py doctor`, ошибок 0 | `doctor.json` |
| Синхронизация Windows Desktop | побайтное совпадение с мастером | `desktop-sync.json` |

Сырые сигналы LanguageTool не являются списком ошибок. Имена, термины мира и литературные конструкции проверялись в полном контексте; подтверждённые места исправлены до финального прогона.
