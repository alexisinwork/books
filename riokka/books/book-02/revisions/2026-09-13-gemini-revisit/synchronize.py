#!/usr/bin/env python3
"""Rebuild this candidate's exports and revalidate its precise evidence anchors."""
from pathlib import Path
import copy
import difflib
import hashlib
import html
import json
import re
import subprocess

REV = Path(__file__).resolve().parent
BOOK = REV.parents[1]
ROOT = REV.parents[4]
SOURCE = REV / 'source/revised.md'
SOURCE_SHA = 'b169ba5b2b53b97e8044f7107c628bff95131df6c88b00d49fea6bb9dbd390da'
BOOK1_SHA = '2651e6b73fe20e844ff19c4f7f99a39ca90c1da3d53f91a3a3a1417ce3ac4172'
CHANGED = [13, 14, 24, 32]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, data):
    p.parent.mkdir(exist_ok=True, parents=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def printed_count(text):
    return sum(len(s.replace('`', '').replace('**', '').strip()) for s in text.splitlines()
               if s.strip() and not re.match(r'^#{1,6} ', s)
               and not re.fullmatch(r'[-* ]{3,}', s) and s != '*Конец второго тома.*')


def chunks(text):
    return re.split(r'(?m)(?=^## Глава \d+\.)', text)[1:]


def main():
    assert sha(SOURCE) == SOURCE_SHA
    b1path = ROOT / 'riokka/books/book-01/manuscript/master.docx'
    assert sha(b1path) == BOOK1_SHA
    old = SOURCE.read_text(encoding='utf-8')
    text = (REV/'revised.md').read_text(encoding='utf-8')
    digest = sha(REV/'revised.md')
    old_chunks, new_chunks = chunks(old), chunks(text)
    assert len(new_chunks) == 51
    assert [n for n, (a,b) in enumerate(zip(old_chunks,new_chunks),1) if a != b] == CHANGED
    count = printed_count(text)
    assert count >= 400000
    lines, oldlines = text.splitlines(), old.splitlines()
    chapter_for_line = {}
    num = 0
    for p,line in enumerate(lines,1):
        m = re.match(r'^## Глава (\d+)\.',line)
        if m: num = int(m[1])
        chapter_for_line[p] = num
    rebound, foreign = 0, 0

    def anchor(chapter, quote=None):
        if quote is None: quote = new_chunks[chapter-1].splitlines()[0]
        matches = [p for p,s in enumerate(lines,1) if quote in s and chapter_for_line[p] == chapter]
        assert len(matches) == 1, (chapter,quote,matches)
        return dict(source='revised.md',source_sha256=digest,chapter=chapter,p=matches[0],
                    quote=quote,verification_status='verified')

    def rebind(value):
        nonlocal rebound, foreign
        if isinstance(value, dict):
            if 'quote' in value and 'p' in value and value.get('source_sha256') == SOURCE_SHA:
                q = value['quote']
                assert any(q in s for s in oldlines), ('missing source evidence',q)
                matches=[p for p,s in enumerate(lines,1) if q in s]
                if len(matches)>1:
                    matches=[p for p in matches if chapter_for_line[p]==value.get('chapter')]
                assert len(matches)==1, ('evidence needs manual revision',q,matches)
                value.update(source='revised.md',source_sha256=digest,p=matches[0],verification_status='verified')
                rebound += 1
            elif 'quote' in value and 'p' in value:
                foreign += 1
            for k,v in list(value.items()):
                if k == 'source_sha256' and v == SOURCE_SHA:
                    value[k] = digest
                else: rebind(v)
        elif isinstance(value,list):
            for v in value: rebind(v)

    chapters=[dict(chapter=n,title=c.splitlines()[0],sha256=hashlib.sha256(c.encode()).hexdigest(),
                   printed_chars_with_spaces=printed_count(c)) for n,c in enumerate(new_chunks,1)]
    for p in sorted((REV/'source/continuity').glob('*.json'))+[REV/'source/voice.json']:
        data=json.loads(p.read_text())
        rebind(data)
        data['source_sha256']=digest
        data['status']='author_followup_candidate'
        if p.name=='scenes.json':
            for s in data['items']:
                n=s['chapter'];s['chapter_sha256']=chapters[n-1]['sha256']
                s['verification']={'file':'revised.md','source_sha256':digest,
                    'result':'not_run' if n in CHANGED else 'passed',
                    'scope':'Changed chapter: contextual prose review pending' if n in CHANGED else 'Text byte-identical to preserved source; evidence anchors revalidated. No new full prose audit.',
                    'report':'audit/REPORT.md'}
                if n in CHANGED:
                    s['previous_prose_check']=s.get('prose_check')
                    s['prose_check']='author_followup_context_review_pending'
                if n==13: s['presentation_note']='Ретроспектива разделена на этапы; значение спорных прав на товар раскрыто обычными словами. Знание Маноса остаётся скрыто от Кая до главы 36.'
                if n==14: s['presentation_note']='Гарм прямо связывает запрет оборота с невозможностью отпустить выкупленного человека; право на опись и демонтаж остаётся прежним.'
                if n==24: s['presentation_note']='Недосып виден по плывущим строкам и навязчивой проверке; Джулия подтверждает расчёт. Состояние 35/176 после Луса сохранено.'
                if n==32: s['state_after']+=' Проверка уложилась в шесть минут, назначенные Каем; шаги сверху слышны ему, личность и маршрут идущих не установлены. Колесо тележки развёрнуто вручную, щуп закреплён петлёй.'
        if p.name=='timeline.json':
            data['items'].append(dict(id='B02-T-GR32',statement='Глава 32: Кай сам отвёл шесть минут на проверку и возвращение к рукаву. Отсчёт Дживса 4→2→1; возвращение до истечения срока. Это локальный бюджет времени, не новый срок транзита и не время горения слухача.',anchors=[anchor(32,'— Шесть минут, Дживс.')]))
        if p.name=='knowledge.json':
            data['items'].append(dict(id='B02-K-GR32',statement='Кай сам слышит шаги над лазом; Дживс ведёт назначенный таймер по существующей связи. Ни один не получает подтверждённого знания о числе, маршруте или принадлежности идущих. Выход проверен Каем ногами.',known_from_scene=32,anchors=[anchor(32,'Над головой загремели подошвы')]))
        if p.name=='resources.json':
            data['items'].append(dict(id='B02-R-GR32',statement='Существующий щуп Вешника использован для крепежа лаза; существующая тележка отодвинута после поворота заевшего колеса и оставлена с зазором. Щуп сохранён, петля надета у верхнего створа. Новых средств взлома не добавлено.',anchors=[anchor(32,'Я опустился на колено'),anchor(32,'У верхнего створа я закрепил щуп')]))
        if p.name=='motifs.json':
            data['items'].append(dict(id='B02-M-GR24',statement='Повторный счёт в 24: боязнь пропустить человека проявляется через сбой внимания и движение пальца; сведения о вместимости не меняются.',anchors=[anchor(24,'Я посчитал ещё раз, ведя ногтем')]))
        if p.name=='characters.json':
            timka=next(x for x in data['items'] if x.get('names')==['Тимка'])
            timka['age_verification']={'age_years':6,'resolution_status':'resolved','report':'audit/TIMKA-AGE.md','previous_book_sha256':BOOK1_SHA,'basis':'Прямые утверждения в главах 16 и 42 авторского мастера; шестилетний возраст прямо повторён в книге 2 спустя месяц. Дата рождения не установлена и не выдумана.'}
        if p.name=='voice.json':
            data['revision_reason']='Прямое поручение автора: паузы в 13–14, физическая усталость в 24, ограниченное время в 32. Общий голос сохранён.'
            data['scene_overrides'] += [dict(chapter=n,scope='Подача дополнительной авторской правки',decision='author_approved',anchors=[anchor(n)]) for n in [14,24,32]]
        dest=REV/'voice.json' if p.name=='voice.json' else REV/'continuity'/p.name
        write(dest,data)

    derived=REV/'derived';derived.mkdir(exist_ok=True)
    (derived/'manuscript.txt').write_text(text,encoding='utf-8')
    plain='\n'.join(re.sub(r'^#{1,6} ','',s).replace('`','').replace('**','') for s in lines)+'\n'
    plain=plain.replace('*Конец второго тома.*','Конец второго тома.')
    (derived/'reader.txt').write_text(plain,encoding='utf-8')
    write(derived/'chapters.json',dict(source_sha256=digest,chapters=chapters))
    subprocess.run(['python3',str(ROOT/'riokka/skills/ru-book-auditor/scripts/book_snapshot.py'),'snapshot',
        '--source',str(REV/'revised.md'),'--format','text','--project-id','riokka','--book-id','book-02',
        '--authority','Author-approved targeted followup; separate candidate','--out',str(derived/'snapshot.json')],check=True)
    blocks=[]
    for block in text.strip().split('\n\n'):
        if re.fullmatch(r'[-*\s]+',block): blocks.append('<hr>');continue
        clean=block.replace('`','').replace('**','')
        m=re.match(r'^(#{1,3}) (.*)',clean,re.S)
        tag='h'+str(len(m[1])) if m else 'p'
        clean=m[2] if m else clean
        if clean=='*Конец второго тома.*': clean='Конец второго тома.'
        ident=''
        if tag=='h2': ident=' id="chapter-'+re.search(r'Глава (\d+)',clean)[1]+'"'
        blocks.append(f'<{tag}{ident}>'+html.escape(clean).replace('\n','<br>')+f'</{tag}>')
    header='<!doctype html><html lang="ru"><meta charset="utf-8"><title>Прочие убытки</title><style>body{background:#eee8dc;color:#201d19;font-family:Georgia,serif}main{max-width:44rem;margin:2rem auto;padding:3rem;background:#fffdf8}h1,h2,h3{text-align:center;margin:3rem 0 2rem}p{line-height:1.55;text-align:justify;text-indent:1.5em}hr{margin:2rem}</style><main>\n'
    (REV/'reader.html').write_text(header+'\n'.join(blocks)+'\n</main></html>\n',encoding='utf-8')
    diff=''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile='source/revised.md',tofile='revised.md'))
    (REV/'changes.diff').write_text(diff,encoding='utf-8')
    changes=json.loads((REV/'changes.json').read_text())
    changes['source_path']='source/revised.md';write(REV/'changes.json',changes)
    md=['# Было — стало: книга 2 после рекомендаций Gemini','',f'Источник: `{SOURCE_SHA}`. Новая редакция: `{digest}`.','',f'{count:,} печатных знаков с пробелами; {count/40000:.5f} авторского листа. Изменены только главы 13, 14, 24, 32.','']
    for x in changes['changes']:
        md += [f"## {x['id']} · глава {x['chapter']}",'',x['reason'],'','**Было**','',x['before'],'','**Стало**','',x['after'],'']
    md += ['## GR-04 · возраст Тимки','','Подтверждены шесть лет по авторскому мастеру книги 1; возраст в рукописи не менялся. Доказательства: [проверка возраста](audit/TIMKA-AGE.md).','']
    (REV/'БЫЛО-СТАЛО.md').write_text('\n'.join(md),encoding='utf-8')
    write(REV/'progress.json',dict(source_sha256=digest,source_before_sha256=SOURCE_SHA,changed_chapters=CHANGED,
        printed_chars_with_spaces=count,author_sheets=count/40000,chapters=51,anchors_rebound=rebound,
        external_anchors_preserved=foreign,unchanged_chapters_verified=47,status='checks_in_progress'))
    print(json.dumps(dict(sha256=digest,printed_chars=count,anchors_rebound=rebound),ensure_ascii=False))


if __name__=='__main__': main()
