# Promotion of a reviewed native candidate

`promote_native_candidate.py` збирає один перевірений український кандидат у новий draft. Інструмент не змінює доставлену базу, рукопис кандидата, `book.json`, audit/session/selection/QA-статуси й не створює читачевих експортів.

Запуск:

```bash
python3 promote_native_candidate.py path/to/spec.json
```

Усі відносні шляхи в spec відлічуються від каталогу самого spec. `new_draft` має бути ще не створеним сусідом `base_draft`; результат спочатку повністю збирається в тимчасовому сусідньому каталозі й лише після повторної перевірки вхідних хешів атомарно отримує задане ім’я.

Обов’язкові поля spec:

- `book_id` — ID одного оповідання;
- `base_draft` — каталог доставленої бази з `translation.json` і `target.uk.txt`;
- `candidate_translation` — повний кандидатський `translation.json`;
- `new_draft` — новий каталог, якого ще немає;
- `expected_sha256.base_translation`, `.base_target`, `.candidate_translation` — закріплені SHA-256;
- `edits` — масив точних послідовних замін із `source_ids`, `before`, `after`, `reason`, `review_id`.

`candidate_changes` можна не вказувати: тоді береться `changes.json` поруч із кандидатським перекладом. Його SHA можна і варто закріпити як `expected_sha256.candidate_changes`. `translation_units` за замовчуванням шукається як `TRANSLATION_UNITS.json` у батьківському каталозі base draft. `record_root` визначає корінь для шляхів у provenance-файлах і за замовчуванням дорівнює каталогу spec.

Кандидатський журнал може містити partial-записи у `changes[]`, згруповані partial-записи у `changes[].edits[]` або partial-записи у `entries[]`. Кожен кандидатський блок, що відрізняється від бази, повинен мати щонайменше одну причину. Інструмент послідовно відтворює журнал від базового тексту й вимагає точного збігу з повним кандидатом; для груп додатково звіряє повні масиви `before`/`after`. Причина, partial `before`/`after` і позиція кожної запису зберігаються окремо.

Причини кандидата та spec `edits` потрапляють у новий `changes.json`; `before` і `after` на рівні підсумкової зміни там завжди є повними цільовими абзацами відносно доставленої бази. Якщо кілька edits стосуються одного абзацу, вони виконуються в порядку spec, і кожний `before` мусить трапитися рівно один раз саме на своєму кроці.

Перед записом інструмент перевіряє:

- хеші базового `translation.json`, базового `target.uk.txt` і кандидата;
- точне відтворення базового `target.uk.txt` із базового translation;
- незмінні source IDs, їх порядок, кількість блоків і кількість `target_paragraphs` у кожному блоці;
- повну незмінність метаданих блоків, зокрема `target_emphasis`, а також присутність кожного захищеного тексту у вказаному абзаці;
- одноразовість кожної заміни;
- повне й одноразове покриття source IDs усіма `TRANSLATION_UNITS` без перетину блоком межі unit;
- наявність причини для кожного повного зміненого абзацу.

Новий draft містить тільки повний `translation.json`, `target.uk.txt`, `changes.json`, `CHANGES.md`, `CHANGES.html`, `ADAPTATION_NOTES.md`, `alignment.json`, усі `chunks/uNN.uk.txt`, `prior-files.json` і байтову копію базового `glossary-addendum.json`, якщо він був у базі. `CHANGES.html` використовує внутрішньорядковий diff Python `difflib`, а обидва журнали зберігають повні абзаци.

[`spec.example.json`](spec.example.json) є виконуваним прикладом на безпечних fixtures. Він створить `tests/fixtures/example-output` лише якщо його явно запустити; каталог треба видалити перед повтором.

Тести:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```
