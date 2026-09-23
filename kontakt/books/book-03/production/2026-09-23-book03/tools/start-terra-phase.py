"""Advance central metadata only after the complete rough handoff gate."""
from pathlib import Path
import json, hashlib, shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
book=run.parent.parent; desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
gate=read(run/'rough-handoff-verification.json');assert gate['status']=='passed'
source=root/gate['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==gate['source_sha256']
archive=run/'rough-gate-before';assert not archive.exists();archive.mkdir()
targets=[book/'book.json',book/'session.md',book/'NEXT-STEP.md',run/'progress.json',root/'kontakt/START_HERE.md']
for p in targets: shutil.copy2(p,archive/p.name)
data=read(book/'book.json');data.update(stage='terra_full_book_writing',audit_status='complete_astra_rough_gate_passed_full_text_pending')
data['draft_scope']['prose_started']=True
data['active_rough']={'path':source.relative_to(book).as_posix(),'sha256':gate['source_sha256'],'chapters':gate['chapters'],'scenes':gate['scenes']}
write(book/'book.json',data)
progress=read(run/'progress.json')
for item in progress['phases']:
 if item['phase']=='all_rough_chapters':item.update(status='complete',gate='rough-handoff-verification.json',source_sha256=gate['source_sha256'])
 if item['phase']=='all_full_chapters':item.update(status='in_progress',path='terra-full-v1/progress.json')
write(run/'progress.json',progress)
body='# Том 3 — повний літературний текст Terra\n\nУсі 32 первинні глави Astra / 41 сцена завершені, повністю прочитані координатором і пройшли перевірку передачі. [Чернетка](production/2026-09-23-book03/astra-rough-v1/assembled/manuscript.md) лишається окремим попередником. Terra пише повний текст усіх глав за всією архітектурою і чернеткою.\n\nПісля повної збірки — незалежні діагнози, звірка Astra, сумісні правки Terra й повне заключне читання. Master не призначено. [Стан](production/2026-09-23-book03/progress.json).\n'
for p in [book/'session.md',book/'NEXT-STEP.md']:p.write_text(body,encoding='utf-8',newline='\n')
p=root/'kontakt/START_HERE.md';text=p.read_text(encoding='utf-8');old='Astra пише всі первинні чернетки перед повним текстом Terra.';assert old in text
p.write_text(text.replace(old,'Усі 32 первинні глави Astra завершені й пройшли перевірку передачі; Terra пише повний літературний текст.',1),encoding='utf-8',newline='\n')
for p in [Path(__file__).resolve(),*targets,*archive.iterdir()]:
 d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
print(json.dumps({'stage':'terra_full_book_writing','rough_sha256':gate['source_sha256']}))
