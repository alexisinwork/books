"""Register a reviewed chapter, preserving exact metadata before snapshots."""
from pathlib import Path
import argparse,hashlib,json,shutil,difflib
p=argparse.ArgumentParser();p.add_argument('--chapter',type=int,required=True);p.add_argument('--draft',type=Path,required=True);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
r=Path.cwd().resolve();b=r/'kontakt/books/book-01';project=r/'kontakt';d=a.draft.resolve();run=a.run.resolve();prod=b/'production/2026-09-21-book01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(r).as_posix()
def put(p,v):p.write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
changes=[]
def update(p,v):
 before=d/'metadata-before'/p.relative_to(r);assert not before.exists(),'Already registered: '+str(p)
 old=p.read_bytes() if p.exists() else None
 if old is not None:before.parent.mkdir(parents=True,exist_ok=True);before.write_bytes(old)
 if isinstance(v,str):p.write_bytes(v.encode('utf-8'))
 else:put(p,v)
 changes.append({'path':rel(p),'before':None if old is None else {'path':rel(before),'sha256':sha(before)},'after_sha256':sha(p),'diff':''.join(difflib.unified_diff((old or b'').decode('utf-8-sig').splitlines(True),p.read_text(encoding='utf-8').splitlines(True),fromfile=rel(before),tofile=rel(p)))})
source=d/f'chapter-{a.chapter:02d}.md';h=sha(source);rr=read(run/'run.json');assert rr['source']['sha256']==h
assert all(rr['reports'][role]['status']=='locked' for role in [*rr['required_diagnoses'],'reconciliation'])
assert read(d/'checks/verification.json')['source_sha256']==h
assert read(d/'observed-state.json')['source']['sha256']==h
chapter={'chapter':a.chapter,'source':source.relative_to(b).as_posix(),'sha256':h,'observed_state':(d/'observed-state.json').relative_to(b).as_posix(),'review_run':run.relative_to(b).as_posix(),'status':'reviewed_working_draft_not_canonical'}
progress=read(prod/'progress.json');assert a.chapter==max(x['chapter'] for x in progress['completed_chapters'])+1
progress['completed_chapters'].append(chapter);progress.update(current_chapter=a.chapter+1,current_stage='prepare_next_scene_handoff');update(prod/'progress.json',progress)
volume={'book_id':'book-01','status':'working_draft_collection_not_master','chapter_count':a.chapter,'chapters':progress['completed_chapters'],'global_audit':'not_run','assembly_rule':'join exact chapter source files in ascending chapter order; verify each hash first'};update(prod/'working-volume.json',volume)
book=read(b/'book.json');book.update(stage='drafting',audit_status=f'chapter_{a.chapter:02d}_reviewed_volume_in_progress',execution_entry='production/2026-09-21-book01/progress.json',working_volume={'manifest':'production/2026-09-21-book01/working-volume.json','chapters':a.chapter,'status':'in_progress_not_master'},working_revision={'path':chapter['source'],'sha256':h,'format':'md','language':'uk','status':'draft_not_author_selected','scope':f'chapter {a.chapter}; complete collection in working_volume','observed_state':chapter['observed_state'],'review_run':chapter['review_run']});book['draft_scope']={'chapter':a.chapter,'whole_book_ready':False,'whole_series_ready':False,'prose_started':True,'execution':f'execution/HANDOFF-CH{a.chapter:02d}.md'};update(b/'book.json',book)
update(b/'session.md',f"# Том 1: написання по главі\n\nПоточне доручення: завершити том 1 з перевірками кожної глави, потім повний аудит. Див. production/2026-09-21-book01/authorization.md.\n\nГлави 1–{a.chapter} написані й мають чотири діагнози та зведення. Остання: [{source.name}]({chapter['source']}), SHA-256 `{h}`. Фактичний стан: [{d.name}]({chapter['observed_state']}). Планові реєстри збережені; master=null.\n\nДалі: глава {a.chapter+1}, перед письмом окрема звірка стану й handoff. Точний прогрес і версії: [реєстр](production/2026-09-21-book01/progress.json). Відкриті редакторські пропозиції не визнані авторськими рішеннями. Повного аудиту тому ще немає.\n")
update(project/'START_HERE.md',f"# Контакт: том 1 у роботі\n\nАвтор доручив завершити український том 1 по главі з усіма перевірками, потім виконати повний аудит.\n\nГотові чернетки глав 1–{a.chapter}; далі глава {a.chapter+1}. [Поточний прогрес](books/book-01/production/2026-09-21-book01/progress.json). [Робочий маршрут](books/book-01/production/2026-09-21-book01/CHAPTER-ROUTE.md). [Остання глава й перевірки]({d.relative_to(project).as_posix()}/README.md).\n\nMaster не призначено. Для продовження спочатку читати фактичний observed-state останньої глави, потім scoped handoff. Макроархітектура восьми книг збережена; плани не стали подіями рукопису.\n")
for name in ['plan.md','brief.md']:
 f=b/name;update(f,f.read_text(encoding='utf-8-sig')+f'\n## Поступ після глави {a.chapter}\n\nЧернетки 1–{a.chapter}: production/2026-09-21-book01/working-volume.json. Наступна глава {a.chapter+1}; факт і план розділені.\n')
f=b/'audit/issues.json';v=read(f)
for issue in read(run/'issue-ledger.json')['items']:
 v['items'].append({'id':f'CH{a.chapter:02d}-SOL-V1-'+issue['id'],'category':issue['category'],'severity':issue['severity'],'certainty':issue['certainty'],'observation':issue['observation'],'anchors':issue['locations'],'dependencies':issue['dependencies'],'decision':'proposed','resolution_status':'unresolved','source_sha256':h,'review_run':chapter['review_run'],'author_decision':'pending','scope':'draft only; editorial proposal not applied'})
update(f,v)
f=b/'revision-log.json';v=read(f);v['items'].append({'id':run.name,'reason':'Author authorized completion of volume one chapter at a time with checks','decision':'applied_to_draft_only','old_source':None,'new_source':{'path':chapter['source'],'sha256':h},'preflight_history':(d/'preflight-changes.diff').relative_to(b).as_posix(),'observed_state':chapter['observed_state'],'dependencies':{'planned_registers':'unchanged; actual candidate states separate','master_snapshot':'not applicable, master null','next_chapter':a.chapter+1},'verification':{'run':chapter['review_run'],'record':(d/'checks/verification.json').relative_to(b).as_posix(),'release_ready':False}});update(f,v)
put(d/'metadata-changes.json',{'files':[{k:v for k,v in x.items() if k!='diff'} for x in changes]});(d/'metadata-changes.diff').write_bytes(''.join(x['diff'] for x in changes).encode('utf-8'))
print(json.dumps({'chapter':a.chapter,'metadata_files':len(changes),'sha256':h},ensure_ascii=False))
