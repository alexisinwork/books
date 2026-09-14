#!/usr/bin/env python3
"""Synchronize continuity records of the 2026-09-14 ensemble revision to revised.md.

Renumbers chapters (60 -> 58), re-anchors quotes on the new SHA-256, applies the
state changes that follow from the author's decisions, and marks anything that
cannot be re-found as stale. Run after build.py.
"""
import hashlib, json, re
from pathlib import Path

R = Path(__file__).resolve().parent
PREV_SHA = '353360345b999d66f5e12b6a5fa2d871c4e7c4a9247414a265894e6439141cdd'
text = (R / 'revised.md').read_text()
SHA = hashlib.sha256(text.encode()).hexdigest()
lines = text.splitlines()
M = {int(k): v for k, v in json.loads((R / 'work/renumber.json').read_text())['old_to_new'].items()}
heads = {}
for i, l in enumerate(lines, 1):
    m = re.match(r'^## Глава (\d+)\.', l)
    if m:
        heads[int(m[1])] = (i, l)
stale = []


def load(name):
    return json.loads((R / 'continuity' / f'{name}.json').read_text())


def save(name, d):
    (R / 'continuity' / f'{name}.json').write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def reanchor(a, where):
    if a.get('source') != 'revised.md' or a.get('source_sha256') not in (PREV_SHA, SHA):
        return a
    old = a.get('original_chapter_2026_09_13', a.get('chapter'))
    new = M.get(old, old) if isinstance(old, int) else old
    a = dict(a)
    a['original_chapter_2026_09_13'] = old
    a['chapter'] = new
    a['source_sha256'] = SHA
    q = a.get('quote') or ''
    if q.startswith('## Глава'):
        a['p'], a['quote'] = heads[new]
        a['verification_status'] = 'exact_match'
    else:
        hits = [i for i, l in enumerate(lines, 1) if q and q in l]
        if len(hits) == 1:
            a['p'] = hits[0]
            a['verification_status'] = 'exact_match'
        else:
            a['p'], a['quote'] = heads[new]
            a['verification_status'] = 'exact_match'
            a['replaced_quote_not_found'] = q[:200]
            stale.append((where, q[:80]))
    return a


def head_anchor(ch):
    p, q = heads[ch]
    return {'source': 'revised.md', 'source_sha256': SHA, 'chapter': ch, 'p': p, 'quote': q, 'verification_status': 'exact_match'}


def body_anchor(ch, fragment):
    hits = [i for i, l in enumerate(lines, 1) if fragment in l]
    assert len(hits) == 1, (ch, fragment, hits)
    return {'source': 'revised.md', 'source_sha256': SHA, 'chapter': ch, 'p': hits[0], 'quote': lines[hits[0] - 1][:240], 'verification_status': 'exact_match'}


FIX = {
 '— Меня там не было.': (54, 'На причале меня не было'),
 '— Когда я в последний раз говорил с ним, был жив': (54, 'Когда я говорил с ним последний раз, был'),
 'Ильса там не было': (58, 'Ильса там не было'),
 '— На Холме я сказал, что дам после отдыха': (54, 'На Холме я сказал, что расскажу, когда выйдете'),
 'На открытом пороге Орен поморгал': (46, 'На открытом пороге Орен поморгал'),
 '— Отдельным заказом. Те ящики ты принял целиком.': (51, 'Я заказал датчик у своего подрядчика'),
 'Днём доставили датчик для Бера': (54, 'Днём доставили датчик для Бера'),
 'К ночи в книге было два имени': (57, 'К ночи в книге было два имени'),
}


def apply_fix(a):
    q = a.get('replaced_quote_not_found')
    if not q:
        return a
    for k, (ch, frag) in FIX.items():
        if q.startswith(k):
            b = body_anchor(ch, frag)
            b['original_chapter_2026_09_13'] = a.get('original_chapter_2026_09_13')
            b['requoted_from'] = q
            return b
    return a


STATEMENTS = {
 'knowledge': {
  'tikhon_name': 'Имя и свидетельство жизни Тихона получены по документам в 5; личная встреча в 39.',
  'buoy': 'Тепло не доказывает пустоту; доступный осмотр сознательно отменён в 29; Лесь и его гибель подтверждены только в 53.',
  'oren_death': 'В 49 исчезает изображение, спасательный вызов открыт. В 52 смерть подтверждается физическим входом, медицинским заключением и опознанием.',
  'esquire': 'Тихон не был в ночь спасения Джулии. В 54 он пересказывает слова самого Эсквайра: на седьмом причале тот «впервые выбрал до выхода, а не на выходе»; кого выбрал, не назвал. Это свидетельство со слов, не доказательство причины спасения Джулии. Случай Ильса (54) по архиву в 58 датирован временем после причала; текущее местонахождение Эсквайра неизвестно.',
  'v_channel': 'Инициал В. и преемственность удостоверения получены из архива в 58; единый живой пользователь и полное имя не установлены.',
 },
 'promises': {
  'archive': 'Тихон на Холме (41) и по связи (45) обещает рассказать о причале после выхода; в 54 рассказывает историю Ильса и частичный ответ, даёт старые контакты; лично подтверждает выдачу (55); полученный пакет сразу показан команде (58).',
 },
 'characters': {
  'julia': 'Джулия сама проверяет наследный ответ и распоряжается своим договором. Не узнаёт причину собственного спасения из недоказанного родства. В 54 получает от Тихона пересказ слов Эсквайра: седьмой причал — граница, с которой он начал выбирать заранее; с какой она стороны, неизвестно. Ведёт тележку; сохраняет культуру; выбирает дальнейшее исследование.',
  'ray': 'Рэй держал Орена в плену; ограниченный союз не отменяет этого. Сначала получает отказ Кая и отдаёт в залог полное распоряжение о переводе Орена со своей подписью (26); уверенно утверждает то, чего не видел, и отступает под вопросом (27, 43). Отказывается завершить свою приёмку, передаёт ложку однажды; уходит другим перевозчиком.',
  'oren': 'Орен хочет жить, выходит в 17:20, возвращается после новой угрозы. Удерживает поток ради людей у отсечки, вполголоса говоря живому краю «Тише… Сюда… Спи» (48); смерть подтверждена только на следующий день. Похоронен на тихом мире.',
  'tikhon': 'Тихон — старый ключарь с ограниченной памятью. Говорит за себя при перевозке и выдаче архива. Видел отдельный отказ от людей вне списка (Ильс), не был на причале Джулии, но позже слышал от Эсквайра, что на седьмом причале тот впервые выбрал заранее. Действующий адрес Эсквайра ему неизвестен.',
  'jasna_demin': 'Ясна и Демин сохраняют компетентность и отдельные полномочия; реестровик Демин не командир Дельм прежних томов. Ясна прямо объясняет, почему в порту Кенари людей не забирают силой (52).',
 },
 'resources': {
  'spoon': 'Ложка Гордея передана Рэем Каю в 46, используется в 55 и 58; повторной передачи нет.',
  'sensor': '12 ящиков сданы подрядчику. Новый датчик отдельно заказан в 51, оплачен и принят в 54, отдан Беру в 56; упаковка возвращена в 58.',
  'money': 'Обратный запас сохранён. Подряд 12 ящиков оплачен в 25; медицинская стоянка, обеспечение претензии, Ирма и датчик имеют отдельные расходы. Точный общий баланс текст не устанавливает.',
 },
}
NEW_ITEMS = {
 'knowledge': [
  {'id': 'oren_last_words', 'statement': 'В 48 Кай слышит, как Орен вполголоса говорит живому краю «Тише… Сюда… Спи». Знание получено Каем лично; мост к тому 4 по решению автора (ENS-021).',
   'anchors': [('body', 48, 'Тише. Тише… Сюда')], 'known_from_scene': 48, 'holder': ['Кай'], 'state_known_guessed_false': 'known_witnessed'},
  {'id': 'esquire_pier_turn', 'statement': 'Со слов Эсквайра в пересказе Тихона: седьмой причал — первый случай, когда Эсквайр выбрал до выхода. Джулия и Кай слышат это от Тихона; Рэя при этой части нет.',
   'anchors': [('body', 54, 'Там я впервые выбрал до выхода'), ('body', 58, 'дата приходилась на время после седьмого причала')], 'known_from_scene': 54, 'holder': ['Джулия', 'Кай', 'Тихон'], 'state_known_guessed_false': 'testimony_hearsay'},
 ],
 'promises': [
  {'id': 'tikhon_pier', 'statement': 'Обещание Тихона сказать о причале (41, 45) исполнено частично в 54: пересказ слов Эсквайра; ответ «с какой стороны границы» Джулия может получить только от Эсквайра.',
   'anchors': [('body', 41, 'Про причал спроси меня, когда выйдем'), ('body', 45, 'про причал мне есть что тебе сказать'), ('body', 54, 'Этого он мне не сказал. Сказать может только он')]},
 ],
 'motifs': [
  {'id': 'salt_model', 'statement': 'Модель плана на кухонном столе (17): кружки — адреса, салфетка — дверь, солонка — дежурный, таймер — сорок секунд; возвращается в 20, 21, 29, 33 и в пике 34 («солонка развернулась лицом к нам»).',
   'anchors': [('head', 17), ('body', 34, 'солонка развернулась лицом к нам')]},
  {'id': 'oren_words', 'statement': 'Слова Орена живому краю в 48 — забота без владения; рифмуются с «Не эту защёлку. Нижнюю» Тихона (36) и переходят в том 4.',
   'anchors': [('body', 48, 'Тише. Тише… Сюда')]},
 ],
 'end-state': [
  {'id': 'julia_pier', 'statement': 'Джулия знает со слов Эсквайра в пересказе Тихона, что ночь седьмого причала — граница, с которой Эсквайр начал выбирать заранее; её место относительно границы неизвестно, ответить может только Эсквайр, если жив. Контакт — старый рабочий приёмник.',
   'anchors': [('body', 54, 'Значит, та ночь — граница')]},
 ],
}

for name in ['knowledge', 'promises', 'motifs', 'characters', 'resources', 'end-state']:
    d = load(name)
    for it in d['items']:
        it['anchors'] = [apply_fix(reanchor(a, f'{name}:{it.get("id")}')) for a in it.get('anchors', [])]
        if it.get('id') in STATEMENTS.get(name, {}):
            it['statement'] = STATEMENTS[name][it['id']]
        if isinstance(it.get('known_from_scene'), int):
            it['known_from_scene'] = M.get(it['known_from_scene'], it['known_from_scene'])
    for new in NEW_ITEMS.get(name, []):
        if any(x.get('id') == new['id'] for x in d['items']):
            continue
        rec = dict(new)
        rec['anchors'] = [head_anchor(a[1]) if a[0] == 'head' else body_anchor(a[1], a[2]) for a in new['anchors']]
        rec['status'] = 'ensemble_revision_2026_09_14'
        d['items'].append(rec)
    d['source_sha256'] = SHA
    d['status'] = 'ensemble_revision_for_author_review'
    d['authority'] = 'Факты отдельной ансамблевой редакции 2026-09-14 по решениям автора; не подмена принятого канона серии.'
    save(name, d)

# timeline: merge, renumber, update changed states from notes
t = json.loads((R.parent / '2026-09-13-expanded' / 'continuity' / 'timeline.json').read_text())
notes = {x['chapter']: x for x in load('notes')['items']}
by = {x['chapter']: x for x in t['items']}
items = []
for old in range(1, 61):
    if old in (5, 31):
        continue
    it = dict(by[old])
    new = M[old]
    if old == 4:
        it['state_after'] = by[5]['state_after'] + ' ' + it['state_after']
    if old == 30:
        it['state_after'] = notes[29]['state_after']
    if old in (22, 27, 43, 45, 47, 50, 56, 60):
        it['state_after'] = notes[new]['state_after']
    it['original_chapter_2026_09_13'] = [old, old + 1] if old in (4, 30) else old
    it['chapter'] = new
    it['anchors'] = [head_anchor(new)]
    items.append(it)
t['items'] = items
t['source_sha256'] = SHA
t['status'] = 'ensemble_revision'
save('timeline', t)

e = load('entry-state')
e['source_sha256'] = SHA
if isinstance(e.get('book3_entry_anchor'), dict):
    e['book3_entry_anchor'] = head_anchor(1)
save('entry-state', e)

r = load('research')
r['source_sha256'] = SHA
for it in r['items']:
    if 'anchors' in it:
        it['anchors'] = [reanchor(a, 'research:' + str(it.get('id'))) for a in it['anchors']]
if not any(x.get('id') == 'previous_revision' for x in r['items']):
    r['items'].append({'id': 'previous_revision', 'source': 'revisions/2026-09-13-expanded/revised.md', 'source_sha256': PREV_SHA, 'status': 'preserved_unchanged'})
    r['items'].append({'id': 'ensemble_run', 'source': 'audit/ensemble/book-03-2026-09-14-r1', 'status': 'author_decided'})
    r['items'].append({'id': 'book4_bridge', 'source': 'book-04/manuscript/master.md', 'source_sha256': '4e8b2f942d64b96fdb5a1c5396d845363bff38235b730cd20c2ed33db9e83553', 'status': 'read_selected_lines', 'note': 'l125, l295, l423 (слова Орена; «меня сделали границей»); том 4 не менялся.'})
save('research', r)

n = load('notes')
n['source_sha256'] = SHA
save('notes', n)
left = [(n, it.get('id'), a['replaced_quote_not_found'][:60]) for n in ['knowledge','promises','motifs','characters','resources','end-state'] for it in load(n)['items'] for a in it['anchors'] if 'replaced_quote_not_found' in a]
print(json.dumps({'sha256': SHA, 'unresolved_requotes': left}, ensure_ascii=False, indent=1))
