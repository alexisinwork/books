"""Freeze the completed full text only after source checks and real reading records."""
from pathlib import Path
import hashlib,json,shutil,difflib
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-full-v1';book=run.parents[1]
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
source=phase/'assembled/manuscript.md';assembly=read(phase/'assembled/assembly.json');assert sha(source)==assembly['manuscript_sha256'] and assembly['through_chapter']==32
gate=read(run/'terra-full-v1-technical-verification.json');assert gate['status']=='technical_phase_integrity_passed_not_literary_verdict' and gate['source_sha256']==sha(source)
coverage={}
for p in sorted((run/'root-terra-reading').glob('*.json')):
 record=read(p);assert record['phase']=='terra-full-v1'
 for item in record['items']:
  n=item['chapter'];assert n not in coverage;assert sha(phase/f'chapters/chapter-{n:02d}.md')==item['sha256'];coverage[n]=item
assert sorted(coverage)==list(range(1,33))
assert not (phase/'manifest.json').exists();archive=run/'full-gate-before';assert not archive.exists();archive.mkdir()
central=[book/'book.json',book/'session.md',book/'NEXT-STEP.md',run/'progress.json',root/'kontakt/START_HERE.md']
for p in central:shutil.copy2(p,archive/p.name)
progress=read(phase/'progress.json');progress.update(status='complete_source_frozen_pending_independent_review',source_sha256=sha(source),literary_review='Fresh independent diagnoses pending.');write(phase/'progress.json',progress)
data=read(run/'progress.json')
for item in data['phases']:
 if item['phase']=='all_full_chapters':item.update(status='complete',source_sha256=sha(source),gate='terra-full-v1-technical-verification.json')
 if item['phase']=='independent_literary_reviews':item['status']='in_progress'
write(run/'progress.json',data)
data=read(book/'book.json');data.update(stage='independent_literary_review',audit_status='full_terra_text_frozen_reviews_pending');data['draft_scope']['whole_book_written']=True
data['active_full_text']={'path':source.relative_to(book).as_posix(),'sha256':sha(source),'chapters':32,'canonical_status':'working_not_author_approved'};write(book/'book.json',data)
body='# Том 3 — незалежна літературна перевірка\n\nПовна структура, усі первинні чернетки Astra і всі 32 літературні глави Terra завершені. [Повний текст](production/2026-09-23-book03/terra-full-v1/assembled/manuscript.md) зафіксовано після координаторського читання й технічної перевірки.\n\nПоточна фаза: незалежні Terra, Gemini 3.8 Flash, Gemini 3.1 Pro та Opus при доступності. Далі Astra звіряє висновки з архітектурою, Terra вносить сумісні правки, проводиться повне заключне читання. Готовність і канонічний master ще не оголошено. [Прогрес](production/2026-09-23-book03/progress.json).\n'
for p in [book/'session.md',book/'NEXT-STEP.md']:p.write_text(body,encoding='utf-8',newline='\n')
p=root/'kontakt/START_HERE.md';text=p.read_text(encoding='utf-8');old='Усі 32 первинні глави Astra завершені й пройшли перевірку передачі; Terra пише повний літературний текст.';assert old in text
p.write_text(text.replace(old,'Усі 32 первинні глави Astra та всі 32 літературні глави Terra завершені; почалася незалежна літературна перевірка.',1),encoding='utf-8',newline='\n')
diff=[]
for n in range(1,33):
 name=f'chapter-{n:02d}.md';old=run/'astra-rough-v1/chapters'/name;new=phase/'chapters'/name
 diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8').splitlines(True),new.read_text(encoding='utf-8').splitlines(True),fromfile='astra-rough-v1/'+name,tofile='terra-full-v1/'+name))
(phase/'rough-to-full.diff').write_text(''.join(diff),encoding='utf-8',newline='\n')
write(phase/'authoring-completion.json',{'status':'full_source_complete_not_final','source_sha256':sha(source),'chapters':32,'scenes':41,'words':progress['words'],'paragraphs':assembly['paragraphs'],'model_requested':'gpt-5.6-terra','actual_backend':'not independently attested','execution':'Fresh native authoring blocks; all rough and architecture supplied; execution traces preserved.','predecessor_sha256':sha(run/'astra-rough-v1/assembled/manuscript.md'),'root_reading':'../root-terra-reading/*.json','technical_gate':'../terra-full-v1-technical-verification.json','limits':'Mechanical provenance and coordinator reading do not substitute for independent reviews, reconciliation, final revision or author canon.'})
write(phase/'manifest.json',{'status':'frozen_full_source_before_final_revision','source_sha256':sha(source),'files':[{'path':f.relative_to(phase).as_posix(),'sha256':sha(f)} for f in sorted(phase.rglob('*')) if f.is_file() and f.name!='manifest.json']})
reader=run/'terra-reader';reader.mkdir(exist_ok=False);shutil.copy2(source,reader/'manuscript.md')
for p in [Path(__file__).resolve(),*central,*archive.iterdir(),reader/'manuscript.md',*phase.rglob('*')]:
 if p.is_file():
  d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d);assert sha(d)==sha(p)
print(json.dumps({'status':'full_source_frozen','source_sha256':sha(source),'words':progress['words']}))
