#!/usr/bin/env python3
"""One-time synchronization of the completed Book 3 editorial pass.

The dated records below describe this pass, not future author revisions.
"""
import difflib
import hashlib
import json
from pathlib import Path
import re
import build

R = Path(__file__).resolve().parent
B = R.parents[1]
SERIES = B.parents[1] / 'series'


def read(p):
    return json.loads(p.read_text())


def write(p, data):
    build.save_json(p, data)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def upsert(items, item):
    for i, old in enumerate(items):
        if old.get('id') == item['id']:
            items[i] = item
            return
    items.append(item)


def run():
    if (R / 'release.json').exists():
        raise SystemExit('This pass is already exported. Preserve it and create a new revision for later edits.')
    original = B / 'manuscript/master.md'
    plan = read(R / 'revision_plan.json')
    assert sha(original) == plan['original_sha256']
    notes = read(R / 'continuity/notes.json')
    notes['status'] = 'editorial_revision_for_author_review'
    by = {x['chapter']: x for x in notes['items']}
    corrections = {
        2: {'state_after': 'Назначение — Розмари; до церемонии двенадцать суток с небольшим. Манос ищет живого ключаря. Путь через тихий мир занимает чуть больше суток, на семь часов дольше прямого.'},
        4: {'state_before': 'На борту трое. В Кенари никто ещё не вошёл. До церемонии одиннадцать суток.'},
        6: {'state_after': 'Тихон жив в последней точке, требует поддержки; два пленника на разных бортах идут к Холму в один день. Носилки подготовлены. Число 70 получено Джулией недавно, причина приказа не доказана.'},
        7: {'state_after': 'Известны раздельные функции панели, привода и ручного обхода. Проверка подлинника назначена на следующее утро. Кай знает только сказанное при нём.'},
        10: {'state_after': 'Слабое тепло, неоднозначные щелчки, старый незакрытый договор; факт присутствия человека не установлен. Снос через девять суток в день церемонии. Осмотр не подтверждён.'},
        46: {'place': 'Ядро; южный медицинский выход; тележка, 17:04–17:18'},
        47: {'place': 'Миля; ограниченное воспоминание, 17:18–около 17:21; конец разговора перекрывается с началом 48'},
        50: {'place': 'Проём камеры, 17:30–17:33'},
        51: {'place': 'Закрытое ядро; южный выход; Миля, после 17:33',
             'state_before': 'После закрытия створки в 17:33 Орен жив за дверью. Команда снаружи, Тихон и Веда на Миле. В 17:34 нижняя отсечка завершена; в 17:37 команда у южной двери.'},
    }
    for n, patch in corrections.items():
        by[n].update(patch)
    by[3]['new_details'] = ['Второй накопитель воды; ремонт прокладки; исправление двойной хозяйственной записи уже доставленного велдовского ребёнка', 'Тимка временно остаётся у Сати и сохраняет семью на Миле; обычный росток остаётся в грунте.']
    by[12]['state_after'] = 'Нормальная подача восстанавливается за 11 секунд. Жалоба Тимки на защёлку помогает взрослым сформулировать гипотезу. Буксировщик внутрь Б-6 не вошёл. Из-за дополнительного акта ответ по въезду перенесён на следующий вечер.'
    by[15]['state_after'] += ' Камеру охлаждения ранее спустили из южной садовой приёмной; старая верхняя связь сохранилась. Это основание адресации в главе 36.'
    by[18]['new_details'] = ['Две чаши с равной начальной температурой и независимыми датчиками; нагрев одной даёт проверяемое расхождение.', 'Записанному Тимке по ошибке отвечает уставший Кай, не Дживс.']
    by[37]['state_after'] = by[37]['state_after'].replace('порез ладони', 'порез правой ладони об кромку шкафа')
    by[45]['state_after'] += ' Иста сначала принимает два лотка, затем отдельно согласует третью ёмкость. Тихон завершает настройку в 17:04.'
    by[48]['state_after'] = by[48]['state_after'].replace('все трое', 'все четверо')
    by[49]['state_after'] += ' Один работник прижат рукоятью, второй держит её; продолжение управления требуется для освобождения обоих.'
    by[52]['new_details'] += ['Портовый сканер физически проведён от открытой рампы к койке. На стоянке врач сначала осматривает Тихона, затем Кая и Рэя.']
    by[53]['state_after'] += ' Датчика на борту нет; начат отдельный заказ у знакомого подрядчика. Доставленные ему 12 ящиков полностью принадлежат получателю.'
    by[55]['new_details'] += ['Ирма впервые показана по видеосвязи; до этого Кай слышал только голос. Личную карточку запрашивает руководитель расследующей бригады, не Веда от имени чужого ведомства.']
    by[56]['state_after'] += ' Датчик принят после сверки маркировки и оплачен отдельно. Дрозд ссылается на уже полученный в 23 результат.'
    by[57]['state_after'] += ' После ужина Тихон лично подтверждает выдачу архивной приёмки и перечень получателей; архив подтверждает качество записи, выдача ещё ожидается.'
    by[58]['new_details'] += ['Обычный росток остаётся в грядке у низкой стены, как в готовом томе 2; перенос в горшок исключён.', 'Полученный в 56 датчик фактически передан Беру.']
    by[60]['state_after'] += ' Упаковка датчика возвращена Каю со схемой и номером партии, копия сохранена у Бера.'
    for n, x in by.items():
        x['verification'] = 'editorial_reread_recorded; semantic_scope_in_audit'
        x['review_evidence'] = 'audit/reading-notes.md' if n <= 48 else 'audit/continuation-review.md'
    write(R / 'continuity/notes.json', notes)
    build.assemble()
    digest = sha(R / 'revised.md')
    full = (R / 'revised.md').read_text()
    lines = full.splitlines()
    scenes = read(R / 'continuity/scenes.json')['items']
    starts = {x['chapter']: x['anchor']['p'] for x in scenes}

    def anchor(n, needle=None):
        start = starts[n]
        end = starts.get(n + 1, len(lines) + 1)
        if needle is None:
            p = start
        else:
            matches = [i for i in range(start, end) if needle in lines[i - 1]]
            assert len(matches) == 1, (n, needle, matches)
            p = matches[0]
        return {'source': 'revised.md', 'source_sha256': digest, 'chapter': n, 'p': p,
                'quote': lines[p - 1], 'verification_status': 'exact_match'}

    def records(name, items):
        out = []
        for key, claim, citations, extra in items:
            out.append({'id': key, 'statement': claim,
                        'anchors': [anchor(n, q) for n, q in citations], **extra})
        write(R / f'continuity/{name}.json', {'schema_version': 1, 'book_id': 'book-03',
              'source_sha256': digest, 'status': 'editorial_revision_for_author_review',
              'authority': 'Факты отдельной редакции; не подмена принятого канона серии.', 'items': out})

    records('characters', [
        ('kai', 'Кай: ограниченное первое лицо; отменяет доступную проверку Б-6; помогает вывезти Тихона, пытается спасти Орена; после смерти Леся признаёт конкретный отказ. Правая ладонь порезана, левая ушиблена; один удар не излечён за сцену.', [(30, None), (37, 'Правая ладонь'), (51, 'Я ударил'), (55, 'Указал, что у меня'), (59, 'Ты написал')], {'voice': 'Практическая ирония; самопроверка через действие.'}),
        ('julia', 'Джулия сама проверяет наследный ответ и распоряжается своим договором. Не узнаёт причину собственного спасения из недоказанного родства. Ведёт тележку; сохраняет культуру; выбирает дальнейшее исследование.', [(11, None), (23, None), (51, 'Веду я'), (56, 'Не обязательно по тому маршруту')], {'voice': 'Сдержанная личная речь, самостоятельные вопросы.'}),
        ('veda', 'Веда ограничена своим архивным участком, признаёт собственную подмену. Сохраняет доказательства без объявления всех бед одним известным приказом.', [(13, None), (21, None), (52, 'Я слишком долго сводила'), (54, 'Я использовала его время')], {'voice': 'Источник, предел, конкретная поправка.'}),
        ('ray', 'Рэй держал Орена в плену; ограниченный союз не отменяет этого. Отказывается завершить свою приёмку, передаёт ложку однажды; уходит другим перевозчиком.', [(34, None), (42, None), (48, None), (60, 'Брат пожал осторожно')], {'voice': 'Короткая предметная речь; признание без самооправдания.'}),
        ('oren', 'Орен хочет жить, выходит в 17:20, возвращается после новой угрозы. Удерживает поток ради людей у отсечки; смерть подтверждена только на следующий день. Похоронен на тихом мире.', [(48, 'Усталый старик'), (50, 'Я остаюсь до отсечения'), (54, 'Орена нашли'), (58, 'Орена похоронили')], {}),
        ('tikhon', 'Тихон — старый ключарь с ограниченной памятью. Говорит за себя при перевозке и выдаче архива. Видел отдельный отказ от людей вне списка, не был на причале Джулии. Действующий адрес Эсквайра ему неизвестен.', [(40, None), (52, 'Назад в рабочую камеру'), (56, 'Меня там не было'), (57, 'Я ещё здесь'), (60, 'Сати разрешила дальнейший путь')], {}),
        ('timka', 'Тимка — шестилетний ребёнок из семьи Кая; временно у Сати, к финалу снова на Миле. Помогает с книгой и вещами, не проектирует боевую операцию и не принимает нравственный отчёт взрослых.', [(3, None), (58, 'Он прижался с другой стороны'), (59, 'Это другое место'), (60, 'Тимка собирался лететь')], {}),
        ('jasna_demin', 'Ясна и Демин сохраняют компетентность и отдельные полномочия; реестровик Демин не командир Дельм прежних томов.', [(13, 'Старший реестровик'), (26, None), (54, 'Ясна уточнила'), (54, 'Демин отдельно приложил')], {}),
        ('ber_ista', 'Бер добровольно остаётся наладчиком на тихом мире; Иста принимает ограниченные пробы и организует нижнюю отсечку, сохраняя собственную ответственность.', [(3, None), (45, 'Иста согласилась'), (51, 'Оба вышли'), (58, 'Бер помог нам')], {}),
    ])
    records('knowledge', [
        ('tikhon_name', 'Имя и свидетельство жизни Тихона получены по документам; личная встреча в 41.', [(6, None), (41, None)], {'known_from_scene': 6, 'holder': ['Кай', 'Джулия', 'Веда'], 'state_known_guessed_false': 'known_with_source_limits'}),
        ('julias_panel', 'Конкретная проба подтверждает наследную связь; привод и назначение требуют отдельного доступа.', [(11, None), (43, 'если раздел закроют')], {'known_from_scene': 11, 'state_known_guessed_false': 'known_limited_test'}),
        ('buoy', 'Тепло не доказывает пустоту; Лесь и его гибель подтверждены только в 55.', [(10, None), (30, None), (55, 'Идентификатор, найденный при теле')], {'known_from_scene': 55, 'earlier_state': 'unresolved_presence'}),
        ('oren_death', 'В 51 исчезает изображение, спасательный вызов открыт. В 54 смерть подтверждается физическим входом, медицинским заключением и опознанием.', [(51, 'Вызов оставался открытым'), (54, 'Орена нашли')], {'known_from_scene': 54, 'earlier_state': 'alive_last_seen; rescue_pending'}),
        ('esquire', 'Тихон не был в ночь спасения Джулии. Его воспоминание о двух пустых местах проверено архивом отдельно; текущее местонахождение Эсквайра неизвестно.', [(56, 'Меня там не было'), (56, 'Сейчас не знаю'), (60, 'Ильса там не было')], {'known_from_scene': 56, 'state_known_guessed_false': 'limited_testimony'}),
        ('v_channel', 'Инициал В. и преемственность удостоверения получены из архива в 60; единый живой пользователь и полное имя не установлены.', [(60, 'Внешний согласующий'), (60, 'Подтверждается преемственность')], {'known_from_scene': 60, 'holder': ['Кай', 'Джулия', 'Веда', 'Рэй', 'Тихон', 'Дживс'], 'state_known_guessed_false': 'known_channel_identity_unresolved'}),
        ('danek', 'Данек Ров подтверждён как один из 109 связкой трёх документов, номером свода и материалами семьи.', [(59, 'Третьим документом'), (59, 'Написал: «Данек Ров»')], {'known_from_scene': 59, 'earlier_state': '109_names_unknown'}),
    ])
    records('resources', [
        ('capacity', 'На Миле максимум 40 живых. В начале четверо, с Бером пятеро; после высадки Бера и Тимки трое. После Холма пятеро; к финалу Рэй сменён Тимкой, снова пятеро.', [(1, None), (3, None), (35, 'бирку сорока'), (51, 'На корабле было пятеро'), (60, 'На борту было пятеро')], {'unit': 'live_people', 'final_count': 5}),
        ('sample_carriers', 'Три ручные ёмкости на Миле и три отдельно согласованные порции у Исты. Финал: один устойчивый и слабый образцы на тихом мире, второй устойчивый на Миле; малая доля Исты перевезена другому питомнику.', [(45, 'Третью тоже могу принять'), (52, 'Три живые ёмкости'), (60, 'На тихом мире один устойчивый'), (60, 'Её довёз обычный садовый транспорт')], {'unit': 'separate_sample_containers'}),
        ('spoon', 'Ложка Гордея передана Рэем Каю в 48, используется в 57 и 60; повторной передачи нет.', [(48, None), (57, 'Я ел деревянной ложкой'), (60, 'Ложку положил на её место')], {}),
        ('sensor', '12 ящиков сданы подрядчику. Новый датчик отдельно заказан в 53, оплачен и принят в 56, отдан Беру в 58; упаковка возвращена в 60.', [(53, 'Отдельным заказом'), (56, 'Днём доставили датчик'), (58, 'Тот, что обещали'), (60, 'Бер вернул пустую упаковку')], {'ownership': 'purchased_for_ber'}),
        ('ordinary_plant', 'Обычный подарок Орена остаётся в грунте у низкой стены. Новый материал содержится отдельно; прежняя прариокка не восстановлена.', [(3, 'Маленький Оренов подарок'), (58, 'Обычный Оренов росток оставался'), (60, 'Новый лист Оренова ростка')], {}),
        ('names', 'В исходных 109 местах записан Данек, 108 пусты. Лесь на добавленном листе. Ильс и работник из угрозы Орену не объявлены погибшими.', [(59, 'Без имени оставалось сто восемь'), (59, 'К ночи в книге было два имени'), (60, 'У меня оставались запросы')], {'original_places': 109, 'original_names': 1, 'original_unknown': 108, 'additional_names': 1}),
        ('money', 'Обратный запас сохранён. Подряд 12 ящиков оплачен в 26; медицинская стоянка, обеспечение претензии, Ирма и датчик имеют отдельные расходы. Точный общий баланс текст не устанавливает.', [(26, 'Деньги за двенадцать ящиков'), (54, 'Я перечислил её'), (55, 'К вечеру пришёл счёт'), (56, 'оплатил отдельный счёт')], {'verification_limit': 'qualitative_balance; no_invented_currency_total'}),
    ])
    records('promises', [
        ('rescue', 'Поиск Орена приводит к попытке спасти двух людей. Тихон вывезен; смерть Орена имеет последствия и погребение.', [(1, None), (46, None), (54, None), (58, 'Орена похоронили')], {'status': 'paid_off_with_loss'}),
        ('neighbour_check', 'Принятый урок проверки соседнего участка нарушен сознательным отказом, а не забыт. Финальный малый заказ снова проверяется.', [(10, None), (30, None), (55, None), (60, 'Я проверил соседний участок')], {'status': 'changed_by_consequence'}),
        ('family', 'Обещание Тимке вернуться исполнено. Ребёнок возвращается на Милю.', [(3, None), (24, None), (58, None), (60, 'Тимка собирался лететь')], {'status': 'paid_off'}),
        ('archive', 'Тихон даёт старые контакты после отдыха; лично подтверждает выдачу; полученный пакет сразу показан команде.', [(47, None), (56, 'Сейчас даю'), (57, 'Архив принял запись'), (60, 'Когда Дживс открыл архивный пакет')], {'status': 'paid_off_new_search_open'}),
        ('danek_location', 'Жене Данека обещано искать место передачи погибшего и присылать сведения.', [(59, 'место, куда передали погибших'), (60, 'Данекова последняя передача')], {'status': 'open_for_next_book'}),
        ('ruka', 'Служебный канал и буква В. дают проверяемый намёк; имя Руки остаётся открытым вопросом серии.', [(60, 'Внешний согласующий'), (60, 'До лица, имени и места')], {'status': 'intentional_open_plot'}),
    ])
    records('motifs', [
        ('spoon', 'Наследство и спор братьев → добровольная передача → обычная еда → Тимкина каша.', [(34, None), (48, None), (57, None), (60, 'Она не горячая')], {}),
        ('book', 'Пустые места → отдельное дело Леся → первое подтверждённое имя и продолжающийся поиск.', [(3, None), (31, None), (55, None), (59, None)], {}),
        ('light', 'Наблюдающая городская сеть → местные живые реакции → свет продолжающих работать садов.', [(4, None), (38, None), (51, 'В нижних садах шёл полив'), (54, 'нижние сады были освещены')], {}),
        ('working_hands', 'Ремонт Бера, повреждённые руки Кая, помощь при еде и самостоятельная работа Тихона.', [(3, None), (37, 'Правая ладонь'), (52, None), (57, 'Я ещё здесь')], {}),
    ])
    end = [
        ('crew', by[60]['state_after'], [(60, 'На борту было пятеро')], {'carry_to_next_book': True}),
        ('oren', 'Орен погиб и похоронен на тихом мире; поиск родных остаётся открыт, место доступно через сохранённый канал.', [(54, 'Орен умер.'), (58, 'Ответа от родных ещё не было')], {'carry_to_next_book': True}),
        ('material', 'Постепенное распространение на физических носителях; несколько держателей, неполная устойчивость, никаких подтверждённых чудесных лечений.', [(60, 'Её довёз обычный садовый транспорт'), (60, 'На тихом мире один устойчивый')], {'carry_to_next_book': True}),
        ('names', 'Данек — 1 из 109, Лесь отдельно. 108 исходных имён, место передачи Данека, Ильс, работник из угрозы Орену требуют поиска.', [(59, 'К ночи в книге было два имени'), (60, 'У меня оставались запросы')], {'carry_to_next_book': True}),
        ('ruka', 'Буква В. и цепочка согласования известны всем участникам сверки; полная личность не доказана, контакт Эсквайра старый.', [(60, 'Внешний согласующий'), (60, 'Подтверждается преемственность')], {'carry_to_next_book': True}),
        ('liability', 'Разбирательство Кенари открыто, связь и обеспечение сохранены; Рэй отбыл законно известным перевозчиком.', [(54, 'Нам назначили повторный сеанс'), (60, 'отметку о незавершённом разбирательстве')], {'carry_to_next_book': True}),
    ]
    records('end-state', end)

    days = {n: 'D-12' for n in [1, 2]}
    for ns, day in [(range(3, 6), -11), (range(6, 10), -10), (range(10, 13), -9), (range(13, 15), -8), ([15], -7), ([16], -6), (range(17, 21), -5), ([21], -4), ([22, 23], -3), ([24, 25], -2), (range(26, 33), -1), (range(33, 54), 0), ([54], 1), ([55], 2), ([56], 3), ([57], 4)]:
        for n in ns:
            days[n] = f'D{day:+}' if day else 'D0'
    for n in [58, 59, 60]:
        days[n] = 'После перелёта D+4; местные дни посадки, погребения и следующих проверок'
    clocks = {29: '21:00 накануне; 19 ч до Тихона', 35: '16:00 / 16:06 / 16:12', 36: '16:12; неверная адресация 39 с', 39: 'около 16:30', 40: 'воспоминание перекрывается с ожиданием двери', 41: '16:38', 44: '16:52, до закрытия 38 мин', 45: '16:52–17:04', 46: '17:04–17:18; передача 17:12', 47: '17:18–около 17:21; воспоминание, короткая речь по связи', 48: '17:20–17:25', 49: '17:25–17:30', 50: '17:30–17:33', 51: '17:34 отсечка, 17:37 южный выход', 52: 'после возврата; требование 17:31 ретроспективно; перелёт 18 мин', 53: 'первая ночь; на тихом мире утро'}
    write(R / 'continuity/timeline.json', {'source_sha256': digest, 'reference': 'D0 — день церемонии на Риокке; сутки перелёта включают переход 2→3→4.', 'status': 'editorial_revision', 'items': [
        {'chapter': n, 'time': days[n], 'clock_or_overlap': clocks.get(n), 'state_before': by[n]['state_before'], 'state_after': by[n]['state_after'], 'anchors': [anchor(n)]} for n in range(1, 61)]})

    # The newer Book 2 is identified by its manifest, not by file date.
    prev_b = B.parent / 'book-02'
    prev_manifest = read(prev_b / 'book.json')
    prev = prev_manifest['working_revision']
    prev_file = prev_b / prev['path']
    assert sha(prev_file) == prev['sha256']
    prev_lines = prev_file.read_text().splitlines()
    prior_entry = read(prev_file.parent / 'continuity/end-state.json')
    for item in prior_entry['items']:
        for a in item.get('anchors', []):
            assert a['source_sha256'] == prev['sha256']
            assert a['quote'] in prev_lines[a['p'] - 1], a
    book1 = B.parent / 'book-01/manuscript/master.docx'
    assert sha(book1) == '2651e6b73fe20e844ff19c4f7f99a39ca90c1da3d53f91a3a3a1417ce3ac4172'
    write(R / 'continuity/entry-state.json', {'source_sha256': digest, 'base_previous_book_sha256': plan['previous_book_sha256'],
        'checked_previous_book': {'path': str(prev_file.relative_to(B.parent)), 'sha256': prev['sha256'], 'status': prev['status']},
        'book1_sha256': sha(book1), 'verification': 'Book 2 final-state anchors exact; selected ending and transition passages read; Book 1 hash and inherited transition records checked, not whole Book 1 reread.',
        'preserved_book2_end_state': prior_entry['items'], 'book3_entry': by[1]['state_before'],
        'book3_entry_anchor': anchor(1), 'transition_changes': ['Обычный росток сохранён в грунте в 58/60.', 'Другие проверенные конечные состояния редакций 10al и ensemble-r1 совместимы со входом тома 3.']})
    write(R / 'continuity/research.json', {'source_sha256': digest, 'items': [
        {'id': 'original', 'source': 'manuscript/master.md', 'source_sha256': sha(original), 'status': 'unchanged_candidate'},
        {'id': 'previous_book', 'source': str(prev_file), 'source_sha256': prev['sha256'], 'scope': 'Final-state anchors and ending; no independent full Book 2 audit claimed.'},
        {'id': 'ruka_limit', 'question': 'Полное имя Руки и нынешний пользователь согласующего канала', 'resolution_status': 'unresolved', 'scope': 'intentional_series_mystery', 'anchors': [anchor(60, 'Подтверждается преемственность')]},
    ]})

    review_path = R / 'audit/review-status.json'
    if review_path.exists() and read(review_path).get('source_sha256') != digest:
        raise RuntimeError('Text changed after review lock; create a new review record.')
    write(review_path, {'source_sha256': digest, 'file': 'revised.md', 'result': 'editorial_review_completed_with_stated_limits',
        'status': 'for_author_proofreading', 'coverage': {'chapter_review': '60/60 cumulative', 'inherited_full_chapter_reading': '1–48, recorded in reading-notes.md before continuation',
        'current_full_chapter_reading': '49–60', 'current_delta_reading': 'all saved corrections to 1–48 against pre-audit.md',
        'whole_book_structural_pass': 'all 60 scene states; causal and temporal chains; targeted confirming text'},
        'limits': ['Не независимая бета и не новый ансамблевый аудит.', 'Не повторное сплошное чтение всех трёх романов в этой сессии.', 'Аудиопрослушивание не выполнялось.', 'Четвёртая книга требует отдельной адаптации входа.'],
        'documents': ['audit/reading-notes.md', 'audit/continuation-review.md', 'audit/REPORT.md'], 'render_status': 'see audit/render/verification.json'})
    build.assemble()
    progress = read(R / 'progress.json')
    plan.update({'status': 'editorial_revision_for_author_review', 'current_sha256': digest,
                 'transition_checked_previous_book_sha256': prev['sha256']})
    write(R / 'revision_plan.json', plan)

    changes = []
    original_text = original.read_text()
    old_ch = re.split(r'(?m)(?=^## Глава \d+\.)', original_text)[1:]
    for s in scenes:
        n = s['chapter']
        changes.append({'chapter': n, 'reason': s['decision'], 'result': s['state_after'],
            'new_editorial_details': s['new_details'], 'dependencies': s['dependencies'],
            'old_source_sha256': sha(original), 'new_source_sha256': digest,
            'new_chapter_sha256': s['chapter_sha256'], 'anchor': anchor(n), 'exact_changes': 'changes.diff',
            'status': 'applied_editorial_not_promoted_to_canon'})
    write(R / 'changes.json', {'source': 'manuscript/master.md', 'source_sha256': sha(original), 'revision_sha256': digest,
        'items': changes, 'continuation_changes': 'audit/resume-changes.json', 'pre_audit': {'file': 'pre-audit.md', 'sha256': sha(R / 'pre-audit.md')}})
    (R / 'audit/proofread.diff').write_text(''.join(difflib.unified_diff((R / 'pre-audit.md').read_text().splitlines(True), full.splitlines(True), fromfile='pre-audit.md', tofile='revised.md')))
    (R / 'audit/resume.diff').write_text(''.join(difflib.unified_diff((R / 'archive/resumed-before-final-review.md').read_text().splitlines(True), full.splitlines(True), fromfile='archive/resumed-before-final-review.md', tofile='revised.md')))
    human = ['# Было — стало: «Холм Розмари»', '', f'Исходник: `{sha(original)}`. Новая редакция: `{digest}`.', '',
        'Все 60 глав развиты в отдельной редакции. Полный точный [diff](changes.diff), [журнал продолжения с дословными заменами](audit/resume-changes.json) и [правки повторного чтения](audit/proofread.diff) сохранены рядом.', '',
        'Это применённые редакторские решения в пределах поручения переписать том; они не объявляют рабочую редакцию принятым каноном.', '']
    for x in changes:
        n = x['chapter']
        human += [f'## Глава {n}', '', f"Изменение: {x['reason']}", '', f"Результат: {x['result']}", '',
                  'Зависимости: ' + ', '.join(map(str, x['dependencies'])) + '.', '']
    human += ['## Дословные изменения при возобновлении', '']
    for x in read(R / 'audit/resume-changes.json')['items']:
        human += [f"### Глава {x['chapter']}: {x['reason']}", '', '**Было**', '', x['old'], '', '**Стало**', '', x['new'] or '(Удалено.)', '']
    (R / 'БЫЛО-СТАЛО.md').write_text('\n'.join(human))

    issues = read(B / 'audit/issues.json')
    for issue in issues['items']:
        if issue['id'] == 'B03-DRAFT-CONTINUITY':
            issue.update({'status': 'applied', 'resolution_status': 'resolved', 'resolved_in_revision': digest,
                'verification': {'file': 'revisions/2026-09-13-expanded/revised.md', 'source_sha256': digest,
                'scope': 'Отдельная редакция 1–60; исходный кандидат сохранён без правки', 'result': 'passed_with_reported_scope',
                'report': 'revisions/2026-09-13-expanded/audit/REPORT.md', 'remaining_questions': ['Адаптация входа книги 4 — отдельная будущая задача.']}})
    upsert(issues['items'], {'id': 'B03-TO-B04', 'status': 'proposed', 'resolution_status': 'unresolved', 'severity': 'major',
        'certainty': 'requires_future_reconciliation', 'observation': 'При продолжении книги 4 сверить вход с этой отдельной редакцией: Тихон уже выдал сведения, буква В. известна всей команде, материал переносится постепенно, Данек — 1 из 109, Лесь отдельно.',
        'dependencies': ['book-04 entry', 'book-04 knowledge', 'book-04 names', 'book-04 material'], 'source_sha256': digest,
        'anchors': [anchor(60)], 'verification': {'result': 'not_run', 'scope': 'Перепись четвёртого тома в текущую задачу не входит.'}})
    upsert(issues['items'], {'id': 'B03-OPEN-STORY-FACTS', 'status': 'proposed', 'resolution_status': 'unresolved', 'severity': 'informational',
        'certainty': 'intentional_open_plot', 'observation': 'Полная личность Руки, текущий адрес Эсквайра, судьбы Ильса и работника из угрозы Орену, место передачи Данека не установлены. Это открытые линии серии, не факты для молчаливого достраивания.',
        'dependencies': ['chapters 56–60', 'book-04', 'book-05'], 'source_sha256': digest, 'anchors': [anchor(60, 'У меня оставались запросы')],
        'verification': {'file': 'revisions/2026-09-13-expanded/revised.md', 'source_sha256': digest, 'scope': 'Границы знания в 56–60', 'result': 'passed', 'remaining_questions': ['Сохранённые сюжетные неизвестные.']}})
    issues['working_revision_audit'] = {'path': 'revisions/2026-09-13-expanded/audit/REPORT.md', 'status': 'editorial_review_completed', 'source_sha256': digest,
        'open_issue_ids': ['B03-TO-B04', 'B03-OPEN-STORY-FACTS'], 'blocking_current_volume_issues': []}
    write(B / 'audit/issues.json', issues)
    write(R / 'audit/issues.json', {'source_sha256': digest, 'items': issues['items'], 'scope': 'Отдельная редакция; открытые линии серии не превращены в доказанные факты.'})
    queue = read(SERIES / 'continuity-queue.json')
    upsert(queue['items'], {'id': 'BOOK03-EXPANDED-HANDOFF', 'book_id': 'book-03', 'status': 'editorial_revision_for_author_review',
        'resolution_status': 'unresolved', 'source_sha256': digest, 'task': 'Для книги 4 использовать явную сверку с новым концом книги 3 после авторской вычитки.',
        'issue_ids': ['B03-TO-B04', 'B03-OPEN-STORY-FACTS'], 'end_state': '../books/book-03/revisions/2026-09-13-expanded/continuity/end-state.json', 'dependencies': ['book-04', 'book-05']})
    write(SERIES / 'continuity-queue.json', queue)
    book = read(B / 'book.json')
    book.update({'stage': 'proofreading_ready', 'audit_status': 'editorial_revision_reviewed_with_stated_limits', 'working_revision': {
        'path': 'revisions/2026-09-13-expanded/revised.md', 'format': 'text', 'sha256': digest,
        'source_sha256': sha(original), 'status': 'editorial_revision_for_author_review', 'author_selected': False,
        'continuity': 'revisions/2026-09-13-expanded/continuity', 'change_log': 'revisions/2026-09-13-expanded/БЫЛО-СТАЛО.md',
        'audit': 'revisions/2026-09-13-expanded/audit/REPORT.md', 'printed_chars_with_spaces': progress['printed_chars_with_spaces'], 'author_sheets': progress['author_sheets']}})
    write(B / 'book.json', book)
    log = read(B / 'revision-log.json')
    upsert(log['items'], {'id': 'B03-EXPANDED-2026-09-13', 'reason': 'Порученная перепись до 11–12 авторских листов; продолжение прерванной вычитки и сборка полного тома.',
        'old_source': {'path': 'manuscript/master.md', 'sha256': sha(original)},
        'new_source': {'path': 'revisions/2026-09-13-expanded/revised.md', 'sha256': digest}, 'changes': 'revisions/2026-09-13-expanded/changes.json',
        'exact_diff': 'revisions/2026-09-13-expanded/changes.diff', 'continuity': 'revisions/2026-09-13-expanded/continuity',
        'decision': 'applied_separate_editorial_revision', 'affected_checks': ['prose', 'continuity', 'transition', 'snapshot', 'DOCX extraction', 'render'],
        'untouched_dependencies': {'master_and_series_canon': 'Автор не назначал новую редакцию окончательным мастером.', 'book-04_manuscript': 'Зависимости внесены в очередь следующего тома.'}})
    write(B / 'revision-log.json', log)
    print(json.dumps({'sha256': digest, 'chars': progress['printed_chars_with_spaces'], 'sheets': progress['author_sheets']}, ensure_ascii=False))


if __name__ == '__main__':
    run()
