"""Register this draft without replacing planned registers or promoting a master."""
from pathlib import Path
import json, hashlib, shutil, difflib

d=Path(__file__).resolve().parent.parent
r=d.parents[4]; b=d.parents[1]; project=b.parents[1]
run=b/'audit/ensemble/ch01-20260921-sol-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(r).as_posix()
def put(p,x):p.write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
changes=[]
def update(p,x):
    q=d/'metadata-before'/p.relative_to(r)
    if q.exists():raise RuntimeError('This synchronization has already run: '+str(q))
    q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
    old=p.read_text(encoding='utf-8-sig')
    if isinstance(x,str):p.write_bytes(x.encode('utf-8'))
    else:put(p,x)
    changes.append({'path':rel(p),'before':{'path':rel(q),'sha256':sha(q)},'after_sha256':sha(p),'diff':''.join(difflib.unified_diff(old.splitlines(True),p.read_text(encoding='utf-8').splitlines(True),fromfile=rel(q),tofile=rel(p)))})
source=d/'chapter-01.md'; digest=sha(source)
assert read(run/'run.json')['source']['sha256']==digest
state={'book_id':'book-01','status':'observed_in_unapproved_draft','source':{'path':'chapter-01.md','sha256':digest},'scope':'chapter 1 only; no accepted master',
 'scenes':[
  {'id':'B01-S01-C01-S01','anchors':'P0002–P0093','events':['Client describes repeated premature support prompts.','Client grants limited metadata and diagnostic-feature access, denies conversation/audio/contacts.','Client chooses and confirms request-driven support.','Three tests: silence, another attempt, then one invoked and rejected hint.','Client shows test summary; a successful setting, not proof of healed relationships.']},
  {'id':'B01-S01-C01-S02','anchors':'P0094–P0117','events':['Client thanks Mark personally.','Dal turns the screen and repeats advice.','Client leaves; Dal chooses observation-needed in service form.']},
  {'id':'B01-S01-C01-S03','anchors':'P0119–end','events':['D0 evening at apartment.','Verified sender Gor requests private consultation today, sends no third-party data.','Dal leaves standard refusal unsent, replies only that he can listen today.']}],
 'timeline':{'opening':'D0 working appointment','closing':'D0 evening; Gor meeting still future','travel':'work-to-home elided with explicit evening transition','next_chapter':'Gor consultation later D0; recheck actual closing before drafting'},
 'characters':{'Dal':'skilled employed calibrator; personal thanks evaded','client':'unnamed adult man, own device; relationship partner and problem specifics not established','Gor':'message sender only; motives inferred by Dal, not verified'},
 'knowledge':{'Dal_gains':['Client-reported avoidance pattern, permitted telemetry and observed test result.','Gor wants a private conversation today.'],'reader_gains':['Calibration can genuinely help.','Dal avoids direct personal acknowledgment.'],'not_yet_revealed':['Maya identity and case','Nina backstory','Gor proxy control','Ballast','later ranks and origin of Lad'],'interpretation_not_fact':['Dal infers careful wording means Gor knows access boundaries.']},
 'resources':{'resonance':'R0, unchanged','employment':'unchanged','Ballast':'not assigned','client_access':'temporary limited grants revoked by scene end; test summary voluntarily shown','Maya_access':'none','case_contract':'none','location':'Dal at home'},
 'promises':{'opened':['What does Gor want?','Will Dal answer a person outside his professional deflection?'],'prepared_only':['P05 direct contact vulnerability','P06 gap between technical success and emotional connection','P07 official professional status'],'not_opened':['Maya safe-presence pattern','Nina object']},
 'motifs':['hands and device edge','waiting for an answer','screen as refuge','controlled warmth','door'],
 'end_state':{'scope':'chapter, not book finale','Dal':'at home, has agreed only to listen today','reader_has_seen_case_acceptance':False},
 'canon_proposals':{'status':'draft-local only','items':['unnamed adult client and three preceding conversations','on-device test and request-support gesture','calibration-room and home details','private verified professional inbox without case creation','tomorrow schedule with an opening after 16:00'],'authority':'Sol scene realization under author writing instruction, not historical/author-approved canon'}}
put(d/'observed-state.json',state)
book=read(b/'book.json');book.update(stage='drafting',audit_status='chapter_01_draft_reviewed_pending_author',working_revision={'path':source.relative_to(b).as_posix(),'sha256':digest,'format':'md','language':'uk','status':'draft_not_author_selected','scope':'chapter 1','observed_state':(d/'observed-state.json').relative_to(b).as_posix(),'review_run':run.relative_to(b).as_posix()});book['draft_scope']['prose_started']=True;book['execution_entry']=(d/'README.md').relative_to(b).as_posix();update(b/'book.json',book)
update(b/'session.md',f'''# Перша чернетка глави 1 — 21.09.2026

Авторське «lfdfq» («давай») дозволило наступний крок — одну українську главу. Виконавець: gpt-5.6-sol.
Текст: [{source.name}]({source.relative_to(b).as_posix()}), SHA-256 `{digest}`.
Мастер не вибраний. Стандартні planned-реєстри збережені; фактичні стани цього варіанта — [observed-state.json]({(d/'observed-state.json').relative_to(b).as_posix()}).
Прочитані входи й хеші: input-manifest.json у каталозі чернетки. Чернетка, журнал, похідні файли й перевірки зібрані в тому самому каталозі.
Незалежні звіти: [{run.name}]({run.relative_to(b).as_posix()}/run.json). Редакторські пропозиції не затверджуються голосуванням.
Даль наприкінці вдома, погодився лише вислухати Гора сьогодні. Майї ще немає в тексті, Баласт не призначений, R0 збережено.
Перед главою 2 звірити цей фактичний вихід із її картками. Саму главу 2 в поточному дорученні не написано.
''')
for name in ['plan.md','brief.md']:
    p=b/name;update(p,p.read_text(encoding='utf-8-sig')+f'\n## Фактичний чернетковий поступ\n\nГлава 1 написана як окремий неутверджений варіант. [Текст і стан]({d.relative_to(b).as_posix()}/README.md). Решта плану не є подіями готової прози.\n')
p=project/'START_HERE.md';update(p,f'''# Поточна робота з «Контактом»

Перша українська чернетка глави 1 написана Sol за дорученням автора від 21.09.2026.
Вхід: [чернетка й перевірки]({d.relative_to(project).as_posix()}/README.md).
У book-01/book.json зареєстрована working_revision; master залишається null.
Для продовження читати фактичний observed-state.json цієї версії, потім картки глави 2.
База архітектури: series/PRE-DRAFT-LOCK-2026-09-19.md та series/preparation/2026-09-21/README.md.
Усі вісім макропланів збережені. Нові деталі першої чернетки не стали автоматично каноном.
''')
p=project/'project.json';v=read(p);v['source_policy']='planning_and_unapproved_drafts';update(p,v)
p=project/'series/CANON-POLICY.md';s=p.read_text(encoding='utf-8-sig').replace('Все события остаются planned; рукописей нет.','Архитектурные события остаются planned. Создан отдельный неутверждённый черновик главы 1; его observed-состояния привязаны к working_revision тома 1 и не заменяют принятый канон.');update(p,s)
p=project/'series/architecture-pass-01-status.json';v=read(p);v['current_draft']={'book_id':'book-01','chapter':1,'path':rel(source),'sha256':digest,'status':'unapproved_draft','whole_book_written':False};v['books'][0]['status']='chapter_01_drafted';v['draft_gate']['prose_authoring_this_task']=True;update(p,v)
p=b/'audit/issues.json';v=read(p)
for issue in read(run/'issue-ledger.json')['items']:
    v['items'].append({'id':'CH01-SOL-V1-'+issue['id'],'category':issue['category'],'severity':issue['severity'],'certainty':issue['certainty'],'observation':issue['observation'],'anchors':issue['locations'],'dependencies':issue['dependencies'],'decision':'proposed','resolution_status':'unresolved','source_sha256':digest,'review_run':run.relative_to(b).as_posix(),'author_decision':'pending','scope':'draft only; no applied revision or canon claim'})
update(p,v)
p=b/'revision-log.json';v=read(p);v['items'].append({'id':'ch01-20260921-sol-v1','reason':'Author said давай to offered first Ukrainian draft chapter','decision':'applied_to_draft_only','old_source':None,'new_source':{'path':source.relative_to(b).as_posix(),'sha256':digest},'scope':'three chapter-1 scene cards','changes':['New Ukrainian first-person chapter','Preflight continuity corrections before frozen review','Separate observed state, no canonical promotion','DOCX and independent reports'],'dependencies':{'planned_registers':'unchanged; candidate states in draft directory','chapter_2':'use observed-state.json before its own gate','master_snapshot':'not applicable; master=null','legacy_sources':'unchanged'},'verification':{'run':run.relative_to(b).as_posix(),'release_ready':False}});update(p,v)
put(d/'metadata-changes.json',{'files':[{k:v for k,v in x.items() if k!='diff'} for x in changes]})
(d/'metadata-changes.diff').write_bytes(''.join(x['diff'] for x in changes).encode('utf-8'))
print(json.dumps({'updated_metadata_files':len(changes),'source_sha256':digest},ensure_ascii=False))
