"""Mechanical cross-check and record of the coordinator's completed structure reading."""
from pathlib import Path
import hashlib,json,re,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;book=run.parents[1];p=run/'structure-v1'
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
def read(x):return json.loads(x.read_text(encoding='utf-8'))
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
def mirror(x):
 d=desktop/x.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(x,d);assert sha(d)==sha(x)
def save(x,v):
 x.parent.mkdir(parents=True,exist_ok=True);x.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');mirror(x)
out=run/'root-structure-gate.json';assert not out.exists()
assert sha(p/'full-outline.md')=='ccddca57e4aef05788526b5d5cb9cad31eaf077b25701011c35f2b4ac700190c'
assert sha(p/'chapter-scene-cards.json')=='ce1337fbc75adcc9b8a0893eb07aaf73fb353757a19d7df30967baca05a5613a'
for entry in read(p/'manifest.json')['files']:assert sha(root/entry['path'])==entry['sha256']
cards=read(p/'chapter-scene-cards.json');scenes=cards['scenes'];byid={s['id']:s for s in scenes}
assert len(scenes)==len(byid)==41 and cards['chapter_count']==32
outline=(p/'full-outline.md').read_text(encoding='utf-8')
for s in scenes:
 for field in ['state_before','goal','obstacle','decision','events','cost','next_cause','resources_permissions','setup_payoff','execution_guard']:
  assert s[field] in outline,(s['id'],field)
 assert s['events']==s['result']
knowledge=read(p/'knowledge.planned.json')
for item in knowledge['items']:
 s=byid[item['first_scene']];assert item['basis']==s['events'];assert item['id']+': '+item['fact'] in '; '.join(s['knowledge_out'])
for item in read(p/'resources.planned.json')['scene_transitions']:
 s=byid[item['scene']]
 for a,b in [('before','state_before'),('resource_delta','resources_permissions'),('cost','cost')]:assert item[a]==s[b]
known={q['id'] for q in read(p/'carry-in-source-lock.json')['proofs']}|{'C04'};prev=None
for s in scenes:
 assert set(s['knowledge_in'])<=known,(s['id'],set(s['knowledge_in'])-known)
 known.update(x.split(':')[0] for x in s['knowledge_out'])
 assert s['state_before_source']['previous_planned_scene']==prev
 prev=s['id']
times=[]
for day in read(p/'timeline.planned.json')['days']:
 for event in day['events']:
  s=byid[event['scene']];assert event['event']==s['events'] and event['place']==s['place']
  assert day['day']==s['time']['day'] and event['start']==s['time']['start'] and event['end']==s['time']['end']
  times.append((int(day['day'][1:]),event['start'],event['end']))
for previous,current in zip(times,times[1:]):assert current[0]>previous[0] or current[1]>=previous[2]
lock=read(p/'carry-in-source-lock.json');source=root/lock['source'];assert sha(source)==lock['source_sha256'];text=source.read_text(encoding='utf-8');blocks=text.rstrip('\n').split('\n\n')
for proof in lock['proofs']:assert proof['quote'] in blocks[int(proof['anchor'][1:])-1]
old=lock['book1_inherited'];source1=root/old['source'];assert sha(source1)==old['source_sha256'];text1=source1.read_text(encoding='utf-8')
for proof in old['proofs']:assert proof['quote'] in text1
questions=read(p/'decisions-and-questions.json')['questions']
report={'status':'pass_for_complete_astra_rough_draft','reviewer':'root coordinator','chapters':32,'scenes':41,
 'actual_reading':'Entire full-outline read in five bounded untruncated ranges (1-260,261-520,521-780,781-1040,1041-end). Carry proofs, prediction cases, unresolved decisions, end state, voices, self-review and gates read. Knowledge inputs/outputs inspected; duplicate map fields cross-checked mechanically against the fully read scene outline. Earlier truncated bulk displays are not counted as reading.',
 'checks':{'all_outline_scene_fields_match_cards':True,'knowledge_dependencies_in_order':True,'resource_and_timeline_maps_match':True,'chronology_nonoverlap':True,'frozen_manifest_matches':True,'book2_scoped_quotes':len(lock['proofs']),'book1_inherited_quotes':len(old['proofs']),'rank':'R2 to R3 only','prediction':'Individual version/horizon/control; 79h50 reserve conditional; point misses distinguished from probability calibration.','agency':'Osya owns work and data; Taras own obligations; Ballast genuine comfort under bounded new mandate.','ending':'Human resolution precedes bounded unexplained budget asymmetry.'},
 'rough_execution_notes':['CH19 no meaningful friend contact is not literally zero human speech: CH18 has a shop owner. Avoid a contradictory absolute claim.','CH27 closure concerns future trajectory content; CH31 permitted resource metadata must not reopen unread behavioral pages.','Prefer the unambiguous vocative Emiliu/pane Emiliu in Ukrainian; do not mechanically copy questionable surname address from a planning table.','Keep chronology explicit where needed; scene placement is a proposed interval, not every minute a spoken fact.','Preserve concrete scene action and distinct voices; do not turn access metadata into repetitive dialogue.'],
 'limits':['Architecture gate does not establish prose quality.','Eight unknowns remain explicitly bounded; U03 is unresolved at entry with an on-page planned answer.','Working implementation does not invent author votes or assign a canonical master.'],
 'files':[{'path':f.relative_to(root).as_posix(),'sha256':sha(f)} for f in sorted(p.iterdir()) if f.is_file()],
 'next':'Astra writes ALL 32 actual rough chapters before Terra begins full literary text.'}
save(out,report)
issues_path=book/'audit/issues.json';issues=read(issues_path)
archive=run/'structure-gate-before';archive.mkdir(exist_ok=False)
for original in [issues_path,book/'book.json',book/'session.md',book/'NEXT-STEP.md',run/'progress.json']:
 dest=archive/('audit-issues.json' if original==issues_path else original.name);shutil.copy2(original,dest);mirror(dest)
for q in questions:
 issue_id='KONTAKT-B03-20260923-'+q['id'];assert not any(x['id']==issue_id for x in issues['items'])
 issues['items'].append({'id':issue_id,'category':'continuity_boundary','severity':'bounded_limit','certainty':'source_limit','observation':q['question'],'evidence_limit':q['basis'],'proposed_change':q['handling'],'dependencies':q['dependent_scenes'],'resolution_status':'unresolved','blocking':False,'decision':'not_individually_adjudicated_by_author','source':(p/'decisions-and-questions.json').relative_to(root).as_posix(),'verification':{'scope':'architecture only; no prose yet'}})
for item in issues['items']:
 if item['id']=='KONTAKT-REV-20260921-18':item['current_execution_override']={'basis':'Explicit continuing author workflow 2026-09-23','workflow':'../../series/WORKFLOW-2026-09-23-BOOK03.md','text':'Complete structure, ALL Astra rough, then Terra full prose; historical resolution preserved.'}
save(issues_path,issues)
progress=read(run/'progress.json');progress['phases'][0].update(status='complete',gate='root-structure-gate.json');progress['phases'][1]['status']='in_progress';progress['active_structure']='structure-v1';save(run/'progress.json',progress)
meta=read(book/'book.json');meta.update(stage='astra_full_book_rough_drafting',audit_status='whole_structure_gate_passed_prose_pending',active_structure={'path':'production/2026-09-23-book03/structure-v1/full-outline.md','sha256':sha(p/'full-outline.md')});save(book/'book.json',meta)
(book/'session.md').write_text('# Том 3 — усі первинні чернетки Astra\n\nПовна структура 32 глав / 41 сцена пройшла координаторську звірку. Активний пакет: [structure-v1](production/2026-09-23-book03/structure-v1/full-outline.md).\n\nAstra пише всі фактичні чернетки. Terra починає повний текст після окремої перевірки всього rough. Далі — незалежна редактура, звірка Astra, правки Terra, заключне читання й передача.\n\nВісім обмежених невідомих збережено в audit/issues.json; жодного canonical master не призначено. [Стан](production/2026-09-23-book03/progress.json).\n',encoding='utf-8',newline='\n');mirror(book/'session.md')
mirror(Path(__file__).resolve());print(json.dumps({'gate':report['status'],'chapters':32,'scenes':41,'unresolved':len(questions)}))
