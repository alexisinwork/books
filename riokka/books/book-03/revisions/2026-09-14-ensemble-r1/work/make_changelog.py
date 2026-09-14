import json, hashlib, re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
m={int(k):v for k,v in json.loads((R/'work/renumber.json').read_text())['old_to_new'].items()}
applied=json.loads((R/'work/applied.json').read_text())
after=json.loads((R/'work/applied-after-review.json').read_text())
ledger=json.loads((R.parents[1]/'audit/ensemble/book-03-2026-09-14-r1/issue-ledger.json').read_text())
titles={it['id']:it['observation'] for it in ledger['items']}
rewrites=[
 {'new_ch':4,'old':[4,5],'ids':['ENS-001','ENS-008'],'what':'Главы 4 «Где нет зазора» и 5 «Та, что всё по правилам» слиты в одну (≈64% прежнего объёма). Сняты повторные поправки Кая (покупка рабочего, «Сначала спросите Веду»); ограничение сети показано средой — панель за порогом спрашивает допуск у своего же рабочего. Сохранены: грузовой зал, «картинка / событие», Веда «Через меня заведём меня», оба дела Ясны (канистра, отозванное подозрение), договор на 12 ящиков, «У него есть комната? — Будет», храпящий сосед.'},
 {'new_ch':9,'old':[10],'ids':['ENS-001'],'what':'Глава «Соседний буй» сжата до зерна линии Б-6: кольцо ссылок, диспетчер, тепло, щелчки, буксир, техник («Чайник списали. Человек остался»), «бумага начинала заменять ответ», реплика Веды. Сняты расчёт хода «Мили» и повторные звонки.'},
 {'new_ch':29,'old':[30,31],'ids':['ENS-004','ENS-009','ENS-013'],'what':'Главы 30 «По сводке пустой» и 31 «Цена угла» слиты. Решение об отказе от осмотра сохранено почти полностью (сняты повторы самоанализа); из бывшей гл.31 оставлены: переписанное условие плана, «Ваше решение не нуждается в более крупном чужом преступлении», запись Джулии о несогласии, перезапись сообщения Тимке, ответ по ста девяти, отдельный лист Б-6 и сохранённое неотправленное предупреждение (первое из трёх появлений рефрена). Голос Ирмы стал короче и грубее: «Так и запишу: заказчик отказался. Сам».'},
 {'new_ch':45,'old':[47],'ids':['ENS-005','ENS-010','ENS-015'],'what':'Глава [Тихон] «Полуправда» сокращена до короткой версии (≈25%): Гордей и кодекс, «Не отдавайте Эсквайру всё, что Гордей для вас сделал», одна фраза об оставленных при свободных местах, обещание Джулии сказать о причале не по связи, имя Ильса в поиск. Полный рассказ перенесён в гл.54.'},
 {'new_ch':47,'old':[49],'ids':['ENS-007'],'what':'В главе «Одна дверь» цепочка из семи неудачных попыток сгущена до трёх (ключ в пазу, смятый футляр, сползший ремень) и слов Тихона «Не оставляйте на одном упоре без человека… Тут держат живой рукой, а не железом»; предупреждение Орена о связке с недоделанной подложкой встроено в одну реплику.'},
 {'new_ch':54,'old':[56],'ids':['ENS-005','ENS-015'],'what':'Глава «С какой стороны границы»: полный рассказ Тихона об Ильсе (перенесён из прежней гл.47, повторный пересказ устранён) и частичный ответ по решению автора — на причале Тихон не был, но позже Эсквайр сам сказал ему: «Там я впервые выбрал до выхода, а не на выходе. Один раз выберешь — дальше уже умеешь». Кого выбрал, не назвал; Тихон разделяет пересказ и догадку. Джулия: «Значит, та ночь — граница… А я с какой стороны?» — «Сказать может только он». — «Если жив».'},
]
out=['# Было — стало: ансамблевая редакция тома 3 от 14.09.2026','',
f"Прежняя редакция: `revisions/2026-09-13-expanded/revised.md`, SHA-256 `353360345b999d66f5e12b6a5fa2d871c4e7c4a9247414a265894e6439141cdd` (сохранена без изменений).",
f"Новая редакция: `revisions/2026-09-14-ensemble-r1/revised.md`, SHA-256 `{sha(R/'revised.md')}`.",
'Основание: решения автора по прогону `audit/ensemble/book-03-2026-09-14-r1` (`author-decisions.md`, реестр из 23 пунктов). Полный построчный diff — `changes.diff`; точные замены — `work/applied.json` и `work/applied-after-review.json`.','',
'Итог: 60 → 58 глав; 440 324 → '+str(json.loads((R/'progress.json').read_text())['printed_chars_with_spaces'])+' знаков с пробелами. Нумерация глав ниже — новая; соответствие старой в `work/renumber.json` (главы 1–4 не сдвинуты; прежние 6–30 → 5–29; прежние 32–60 → 30–58).','',
'## Пункты реестра','']
for it in ledger['items']:
    out.append(f"- **{it['id']}** — {it['observation']}")
out+=['','## Крупные переписывания','']
for rw in rewrites:
    out.append(f"### Гл. {rw['new_ch']} (прежние {', '.join(map(str,rw['old']))}) — {', '.join(rw['ids'])}")
    out.append(''); out.append(rw['what']); out.append('')
out+=['## Точечные правки по главам','']
rows=[]
for e in applied:
    rows.append((m[e['ch']], e['ch'], e['why'], e['old'], e['new']))
for e in after:
    rows.append((e['new_ch'], None, e['why'], e['old'], e['new']))
rows.sort(key=lambda r: r[0])
cur=None
def q(s):
    return '\n'.join('> '+l if l else '>' for l in s.split('\n'))
for ch, oldch, why, old, new in rows:
    if ch!=cur:
        out.append(f'### Глава {ch}'); out.append(''); cur=ch
    if len(old)>1800 and oldch==49:
        continue
    out.append(f'**{why}**' + (f' (прежняя гл. {oldch})' if oldch and oldch!=ch else ''))
    out.append(''); out.append('Было:'); out.append(''); out.append(q(old)); out.append('')
    out.append('Стало:'); out.append(''); out.append(q(new) if new else '> [удалено]'); out.append('')
(R/'БЫЛО-СТАЛО.md').write_text('\n'.join(out)+'\n')
changes={'source_sha256':sha(R/'revised.md'),'previous_sha256':'353360345b999d66f5e12b6a5fa2d871c4e7c4a9247414a265894e6439141cdd','run':'audit/ensemble/book-03-2026-09-14-r1',
 'rewrites':rewrites,'replacements':[{'new_chapter':r[0],'previous_chapter':r[1],'reason':r[2],'old':r[3],'new':r[4]} for r in rows],'diff':'changes.diff','renumber':'work/renumber.json'}
(R/'changes.json').write_text(json.dumps(changes,ensure_ascii=False,indent=1)+'\n')
print(len(rows), len('\n'.join(out)))
