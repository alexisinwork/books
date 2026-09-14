#!/usr/bin/env python3
"""Preserve the targeted editorial comparison, with checked source anchors.

This is a record of a human-readable editorial pass, not an automatic diagnosis
and not an independent ensemble report. It never changes manuscript text.
"""
import hashlib
import json
from pathlib import Path
import re

R = Path(__file__).resolve().parent
ROOT = R.parents[4]
B3 = R.parents[1]
B4 = B3.parent / 'book-04'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


SOURCES = {
    'b3': (R / 'revised.md', '353360345b999d66f5e12b6a5fa2d871c4e7c4a9247414a265894e6439141cdd'),
    'b3-original': (B3 / 'manuscript/master.md', '9c3e242da0d512b851531cf94c1941aae7eabb2f236ea19f409b6f139d0bf76d'),
    'b4': (B4 / 'manuscript/master.md', '4e8b2f942d64b96fdb5a1c5396d845363bff38235b730cd20c2ed33db9e83553'),
    'b5': (B3.parent / 'book-05/manuscript/master.md', '07d5cfcb5f9b1e74c139ef00a2bc15b579631cc33cba8c536f2b651325234fda'),
    'bible': (ROOT / 'riokka/methods/originals/SERIES-BIBLE-Контрактник-Риокка.md', 'ecd988da99feeb574e5a787dbcc96dc523f7bd1d34559255891642dcf56d20bc'),
}
docs = {}
for key, (path, expected) in SOURCES.items():
    assert sha(path) == expected, (key, 'source changed; recheck comparison')
    ch = 0
    rows = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        m = re.match(r'^## Глава (\d+)\.', line)
        if m:
            ch = int(m[1])
        rows.append({'source': str(path.relative_to(ROOT)), 'source_sha256': expected,
                     'chapter': ch, 'line': n, 'quote': line, 'verification_status': 'exact_match'})
    docs[key] = rows


def anchor(key, ch, needle):
    found = [r for r in docs[key] if r['chapter'] == ch and needle in r['quote']]
    assert len(found) == 1, (key, ch, needle, len(found))
    return dict(found[0])


def issue(num, title, observation, proposed, deps, before, after, certainty='text_conflict'):
    return {'id': f'B34-{num:02}', 'category': 'cross_volume_continuity', 'title': title,
            'status': 'proposed', 'resolution_status': 'unresolved', 'severity': 'major',
            'certainty': certainty, 'observation': observation, 'proposed_change': proposed,
            'dependencies': deps, 'anchors': before + after,
            'author_decision': 'pending', 'application_status': 'not_applied',
            'verification': {'result': 'conflict_or_ambiguity_confirmed',
                             'scope': 'Целевая сверка перехода, не полный аудит книги 4.'}}


issues = [
    issue(1, 'Масштаб и способ распространения риокки',
          'Том 3 заканчивается несколькими физически вынесенными образцами и медленными пробами. Том 4 начинается с самопроизвольных всходов по всей обитаемой с одной ночи и уже исчезнувшей монополии. Показанного моста между этими состояниями нет.',
          'В редакции тома 4 показать цепи доставки, сроки, локальные успехи и пределы действия. Охоту на умеющих работать с материалом можно сохранить: она не требует мгновенного появления травы на всех мирах.',
          ['book-04 chapters 1–4', 'book-04 propagation and economy', 'book-04 hope ledger 55, 58, 61'],
          [anchor('b3', 52, 'Три живые ёмкости'), anchor('b3', 52, 'время, три номера'), anchor('b3', 58, 'Земля не спешила')],
          [anchor('b4', 1, 'С той ночи всошло'), anchor('b4', 2, 'она у всех')]),
    issue(2, 'Данек исчезает из книги имён',
          'В финале тома 3 два имени: Данек — первое из 109, Лесь — на отдельном листе. В начале и главе 11 тома 4 опять одно имя. Поздний итог «Лесь, Лад» не должен стирать Данека.',
          'Сохранить две категории: из 109 установлен Данек, 108 ещё ищут; личные потери Кая сначала Лесь, затем Лесь и Лад. При прежнем событии с Ладом всех названных в книге станет три, а не два. Продолжить запрос о месте передачи Данека.',
          ['book-04 chapters 1, 10, 11', 'book-04 chapters 55, 58, 61', 'names and open queries'],
          [anchor('b3', 59, 'К ночи в книге было два имени'), anchor('b3', 59, 'Без имени оставалось сто восемь')],
          [anchor('b4', 1, 'В ней теперь стояло одно имя'), anchor('b4', 11, 'Было одно — стало одно'), anchor('b4', 55, 'ПРОЧИЕ УБЫТКИ: 2')]),
    issue(3, 'Джулии приписано не полученное свидетельство',
          'В томе 3 Тихон не устанавливает, почему Эсквайр выбрал девочку у седьмого причала. В главе 10 тома 4 Джулия вспоминает его категорическое объяснение, будто её сделали границей. Мнение и доказанное прошлое смешаны.',
          'Оставить Джулии её собственную гипотезу и самостоятельный поиск. Если нужен новый факт — показать новый источник. Не отменять открытое обсуждение её цели в конце тома 3 ради повторной тайны.',
          ['book-04 chapters 10, 18, 52', 'Julia knowledge and departure motivation'],
          [anchor('b3', 56, 'Это не отвечает, зачем он выбрал меня'), anchor('b3', 60, 'не присоединяя к своей ночи')],
          [anchor('b4', 10, 'Потому что Тихон на холме сказал мне ту правду')]),
    issue(4, 'Тихон и Рэй снова придерживают уже обещанные сведения',
          'В главе 56 тома 3 Тихон отвечает: прежний контакт был жив, нынешнее состояние неизвестно; выдаёт способ связи и помогает запросить архив. Том 4 вспоминает отсутствие ответа и намеренное воспитательное молчание. Новые сомнения допустимы, стирание состоявшегося разговора — нет.',
          'Переписать повторные задержки как новые препятствия: проверка нового адреса, неполный документ, противоречащие свидетельства. Старый контакт и известные ограничения должны оставаться общими. Новая тайна Рэя требует причины, совместимой с его обещанием делиться.',
          ['book-04 chapters 2, 4, 15, 27, 49–51, 57', 'Tikhon and Ray knowledge'],
          [anchor('b3', 56, 'Когда я в последний раз говорил с ним'), anchor('b3', 56, 'Сейчас даю')],
          [anchor('b4', 15, 'Помнишь, мы с тобой спрашивали Тихона'), anchor('b4', 27, 'Вторую половину я придержал')]),
    issue(5, 'Архивная буква превращается в новый росчерк',
          'В томе 3 «В.» получена всей командой из архивной записи и преемственности сертификата. В томе 4 это пойманная на долю секунды буква, впервые показанная Тихону, затем улика нажима пера. Цифровая преемственность не доказывает почерк, личность пользователя или участие Весты на Холме.',
          'Сохранить уже общий архивный факт. Для сравнения почерка ввести отдельный реальный рукописный образец и способ его получения. Не приписывать Каю наблюдение Весты на Холме: в редакции тома 3 такой встречи нет. Личность Руки и внешний учитель остаются гипотезами до новых доказательств.',
          ['book-04 chapters 2, 4, 15, 27, 48–51', 'Ruka identity evidence', 'Vesta retrospective'],
          [anchor('b3', 60, 'Внешний согласующий был указан'), anchor('b3', 60, 'Подтверждается преемственность'), anchor('b3', 60, 'Я сам его не видел')],
          [anchor('b4', 27, 'Контрактник прислал мне'), anchor('b4', 51, 'совпадают по почерку'), anchor('b4', 4, 'под ладонями Весты')]),
    issue(6, 'Календарь и «первое поколение»',
          'Том 4 начинает второй месяц после Холма, в главе 15 вспоминает Холм полгода назад, в главе 51 — год обучения у Тихона. Переходы времени нужно обосновать в едином маршруте. Веста моложе двадцати и названа выросшей на диком, якобы заговорившей на нём раньше людского; «родилась, считай, в ночь рассеяния» допускает метафору, но соседние утверждения читаются как биография.',
          'Составить календарь четвёртого тома с явными промежутками и возрастами. Уточнить, что именно означает поколение Весты, откуда её ранний опыт. Не добавлять задним числом годы в финал тома 3; не назначать новую биографию без решения автора.',
          ['book-04 chapters 1, 2, 7, 15, 34, 51', 'Vesta biography', 'Timka age', 'route timeline'],
          [anchor('b3', 60, 'На борту было пятеро')],
          [anchor('b4', 2, 'второй месяц'), anchor('b4', 15, 'полгода тому'), anchor('b4', 51, 'за этот год'), anchor('b4', 7, 'родился, считай')],
          certainty='calendar_conflict_and_biographical_ambiguity'),
]

oren4 = [dict(r) for r in docs['b4'] if re.search(r'\bОрен[а-я]*\b', r['quote'])]
oren5 = [dict(r) for r in docs['b5'] if re.search(r'\bОрен[а-я]*\b', r['quote'])]
assert len(oren4) == 11 and not oren5
oren = {'id': 'B34-OREN', 'resolution_status': 'resolved', 'result': 'death_is_consistent',
        'decision_basis': 'Сохранение уже написанной судьбы; не новое решение убить персонажа.',
        'conclusion': 'Орен погибает и в исходном томе 3. Том 4 прямо вспоминает его смерть и посмертную роль. Оснований возвращать живым по проверенным материалам не найдено.',
        'limits': 'Отсутствие упоминаний в кандидате тома 5 не доказывает отсутствия неизвестного авторского плана. Старая библия описывает Орена живым в состоянии после тома 1, не после тома 3.',
        'anchors': [anchor('b3-original', 51, 'Орен умер'), anchor('b3', 54, 'Орен умер.'), anchor('b3', 58, 'Орена похоронили')],
        'all_book4_passages': oren4, 'book4_name_occurrences': 14, 'book5_name_occurrences': len(oren5)}
report = {'date': '2026-09-14', 'kind': 'targeted_cross_volume_review',
          'source_sha256': SOURCES['b3'][1],
          'sources': [{'id': k, 'path': str(p.relative_to(ROOT)), 'sha256': h} for k, (p, h) in SOURCES.items()],
          'scope': 'Конец новой редакции 3; подтверждение смерти в старом 3; поиск по полному 4 и чтение всех 11 фрагментов с именем Орена (14 словоупотреблений); целевое чтение входа, знаний, календаря и поздних сводок 4. По 5 — поиск имени. Не сплошной независимый аудит 4–5.',
          'oren': oren, 'items': issues,
          'manuscript_changes_from_this_comparison': [],
          'ensemble': {'book3_ready_to_submit': True, 'joint_compatibility_passed': False,
                       'independent_reports_completed': False,
                       'unresolved_ids': [x['id'] for x in issues]}}
save(R / 'audit/transition-book4.json', report)

md = ['# Стык томов 3–4 и судьба Орена', '',
      'Проверка от 14 сентября 2026. **Смерть Орена согласуется с продолжением. Полностью согласованным стык томов назвать нельзя: осталось шесть групп расхождений.**', '',
      '## Орен', '', oren['conclusion'], '',
      'В исходном третьем томе смерть названа в главе 51. В новой редакции попытки спасения развёрнуты в главах 49–51, медицинское подтверждение дано в 54, погребение — в 58. Орен хочет жить, успевает выйти и возвращается из-за конкретной угрозы работникам; его не оставляют умирать без попыток помочь.', '',
      'В четвёртом томе проверены все 11 фрагментов с именем Орена (14 словоупотреблений). Самые прямые подтверждения: глава 34 — «когда умирал»; глава 42 — противопоставление живой надежды посмертной; глава 58 — «Орен спас культивар собой». Его дальнейшая роль — память, переданное умение и последствия поступка. Это не обещание его возвращения живым.', '',
      oren['limits'], '',
      'Менять развязку Орена для совместимости с существующим четвёртым томом не требуется. Воскрешение было бы отдельным авторским изменением сюжета.', '',
      '## Что требует согласования', '']
for x in issues:
    md.extend([f"### {x['id']}. {x['title']}", '', x['observation'], '', '**Предложение для следующей редакции:** ' + x['proposed_change'], '',
               '**Проверенные места:** ' + '; '.join(f"{a['source'].split('/')[2]}, гл. {a['chapter']}, строка {a['line']}" for a in x['anchors']) + '.', '',
               'Статус: `proposed`; `resolution_status: unresolved`. Правки тома 4 не применялись.', ''])
md.extend(['## Готовность к ансамблю', '',
           'Третий том собран целиком и готов быть источником нового независимого аудита. Это означает готовность передать текст редакторам, а не положительный итог ещё не проведённого ансамбля. Для совместного чтения серии использовать зафиксированные версии и сохранить перечисленные вопросы о четвёртом томе.', '',
           'Этот отчёт сделан при завершении редакции. Он не подменяет независимый структурный диагноз Codex, литературный отчёт Claude или холодное чтение Gemini. Будущие независимые проходы не должны заранее читать эти выводы; Gemini получает только читательский текст и нейтральную форму.', '',
           '## Источники и охват', '', report['scope'], '',
           '| Файл от корня репозитория | SHA-256 |', '|---|---|'])
for item in report['sources']:
    md.append(f"| `{item['path']}` | `{item['sha256']}` |")
md.extend(['', 'Точные цитаты, все упоминания Орена, зависимые главы и статусы сохранены в [transition-book4.json](transition-book4.json). После изменения любого исходника эту сверку нужно проверить заново.', ''])
(R / 'audit/TRANSITION-BOOK-4.md').write_text('\n'.join(md))

b4audit = json.loads((B4 / 'audit/issues.json').read_text())
b4audit['items'] = [x for x in b4audit['items'] if not x['id'].startswith('B34-')] + issues
b4audit['targeted_transition_review'] = {'file': '../book-03/revisions/2026-09-13-expanded/audit/TRANSITION-BOOK-4.md',
                                      'source_sha256': SOURCES['b4'][1], 'previous_book_sha256': SOURCES['b3'][1]}
save(B4 / 'audit/issues.json', b4audit)
b3audit = json.loads((B3 / 'audit/issues.json').read_text())
item = next(x for x in b3audit['items'] if x['id'] == 'B03-TO-B04')
item.update({'certainty': 'confirmed_cross_volume_conflicts',
             'observation': 'Сверка выполнена: смерть Орена совместима; шесть групп расхождений по материалу, именам, знаниям Джулии, сведениям Тихона и Рэя, источнику инициала и календарю остаются в томе 4.',
             'verification': {'result': 'failed_compatibility', 'scope': report['scope'],
                              'report': 'revisions/2026-09-13-expanded/audit/TRANSITION-BOOK-4.md',
                              'compared_book4_sha256': SOURCES['b4'][1], 'remaining_questions': [x['id'] for x in issues]}})
save(B3 / 'audit/issues.json', b3audit)
queue_path = ROOT / 'riokka/series/continuity-queue.json'
queue = json.loads(queue_path.read_text())
handoff = next(x for x in queue['items'] if x['id'] == 'BOOK03-EXPANDED-HANDOFF')
handoff.update({'task': 'Сверка 3→4 выполнена; сохранить смерть Орена. Согласовать шесть групп выявленных расхождений при редактуре 4.',
                'comparison': '../books/book-03/revisions/2026-09-13-expanded/audit/TRANSITION-BOOK-4.md',
                'compared_book4_sha256': SOURCES['b4'][1],
                'issue_ids': ['B03-TO-B04', 'B03-OPEN-STORY-FACTS'] + [x['id'] for x in issues]})
save(queue_path, queue)
print(json.dumps({'oren': oren['result'], 'book4_passages': len(oren4), 'book4_name_occurrences': 14, 'unresolved_groups': len(issues)}, ensure_ascii=False))
