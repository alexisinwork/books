"""Administrative source-grounded state synchronization after Terra's prose edits."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-final-v3'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
state=read(phase/'observed-state.json');changes=read(phase/'changes.json');assert 'coordinator_state_updates' not in changes
updates=[]
def update(n,field,after,quote):
    c=state['chapters'][n-1];s=c['observed']['scenes'][0]
    text=(phase/f'chapters/chapter-{n:02d}.md').read_text(encoding='utf-8');assert quote in text
    updates.append({'chapter':n,'scene_id':s['id'],'field':field,'before':s[field],'after':after,'quote':quote,'basis':'Coordinator synchronization to exact Terra-authored final prose; no additional prose revision.'});s[field]=after
update(18,'time_basis','Плановий D6 19:30–20:30; у прозі названо публікацію о 20:10, старт у понеділок о 00:00 і повернення у вівторок о 00:00.','Початок у понеділок о 00:00. Повернення у вівторок о 00:00.')
update(19,'time_basis','Плановий D6 23:40–D7 00:20; у прозі названо відлік до 00:00 та повернення у вівторок о 00:00, після понеділкового старту.','— У вівторок, нуль нуль.')
s=state['chapters'][28]['observed']['scenes'][0]
update(29,'resources',s['resources']+' Середовий пакунок стосується іншого столу, ніж завершена понеділкова передача. Даль прямо підтверджує Тарасові свою явку.', 'щодо окремого пакунка деталей для іншого столу.')
s=state['chapters'][29]['observed']['scenes'][0]
update(30,'events',s['events']+' Після закриття пункту Вектор запрошує Даля на підсумок сьогодні о дванадцятій — у той самий вівторок.', '— Сьогодні о дванадцятій. Зводимо підсумок, — сказав він. — Прийдете?')
s=state['chapters'][32]['observed']['scenes'][0]
update(33,'events',s['events']+' Середова видача деталей — окремий пакунок для іншого столу, не повтор понеділкової передачі в Лани.', 'Перший стосувався окремого пакунка деталей для іншого столу.')
changes['coordinator_state_updates']=updates;write(phase/'changes.json',changes);write(phase/'observed-state.json',state)
for field in ['time_basis','events','knowledge','resources']:
    write(phase/(field+'.observed.json'),{'status':'observed_working_revision_not_canon','basis':'observed-state.json','items':[{'chapter':c['chapter'],'chapter_sha256':c['sha256'],'scene_id':s['id'],'observation':s[field],'quotes':s['quotes'],'open_dependencies':s.get('open_dependencies',[])} for c in state['chapters'] for s in c['observed']['scenes']]})
write(phase/'coordinator-metadata-sync.json',{'prose_unchanged':True,'source_sha256':hashlib.sha256((phase/'assembled/manuscript.md').read_bytes()).hexdigest(),'updates':updates})
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),*phase.rglob('*')]:
    if f.is_file():
        d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'source_grounded_metadata_updates':len(updates),'prose_changed':False}))
