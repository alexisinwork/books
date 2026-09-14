Созданы новые независимые контексты: INPUTS-V3/ready-v3 для «Рептилоїдів» и «Справедливого вбивці», INPUTS-V4/ready-v4 для «Логіки хаосу». Точные пути и SHA для последующей selection находятся в [INPUT-BINDINGS.json](INPUT-BINDINGS.json); полный отчёт — [CREATED-INPUTS.json](CREATED-INPUTS.json).

Каждый пакет содержит побайтные снимки всех прежних mutable inputs и семи дополнительных входов: NATURALNESS, book-language-review, literary-adaptation, STYLE проекта, CORE, TASK и target-only-uk. Получилось 28/28/32 снимка; отдельный хешируемый SNAPSHOT.json включён в inputs, поэтому активных входов 29/29/33. Все активные input paths направлены в собственный ready/context. origin_path, origin_sha256, previous_frozen_sha256 и сведения о выбранной копии сохраняют происхождение.

NATURALNESS взят из точной выбранной копии 3f890bec3cbdce3a15e8ef72614d02108aa2370cd2ce217e76dc7a80817fae2e, target-only prompt — af360b8de52fc2bd50bbd569839eaf00935575da25d0bfc389319072fb50a330. Выбор после обнаруженной параллельной смены и его основание записаны в [SELECTED-RULES-V2.json](SELECTED-RULES-V2.json); ADDITIONAL-RULES не переписан. Дальнейшая смена live-файлов не изменит эти снимки.

Старое несоответствие UK STYLE зафиксировано в origin_changes как переход к текущим правилам по поручению на новый полный native-проход. Старые manifest/packet сохраняют прежние байты и SHA. Source-segments и RU reader скопированы побайтно; источник и инвентарь оригинала сохранены. Glossary-снимки имеют прежние SHA из translation.json.

verify_packet и все input/source/hash проверки прошли сначала во временной копии без live mutable origins, затем в опубликованных пакетах. Сверены 54/236/310 исходных сегментов. Все 37 защищённых файлов остались неизменны: book.json, старые manifest/packet, оригиналы, инвентари, старые target/translation, glossary и модельные runner-инструменты. Временные проверочные копии удалены после успешной публикации.

Текущие указатели, редакции и читательские файлы эта операция не меняла. Новые пакеты — редакторский контекст, а не слепой читательский пакет и не подтверждение качества прозы. Модели, экспорт, новые финальные QA и доставка не запускались.
