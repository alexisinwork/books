"""Synchronize the verified working volume and author delivery; never promote canon."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;book=run.parents[1]
phase=run/'terra-final-v3';source=phase/'assembled/manuscript.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def rel(p):return p.relative_to(root).as_posix()
gate=read(run/'final-acceptance.json');assert gate['source_sha256']==sha(source) and gate['status']=='complete_corrected_working_volume'
changes=read(phase/'changes.json');state=read(phase/'observed-state.json');assembly=read(phase/'assembled/assembly.json')
assert len(state['chapters'])==36 and len(changes['patches'])==22
report=run/'final-astra-native-v1/REPORT.md';assert sha(report)==gate['astra_report_sha256']
write(phase/'end-state.observed.json',{'status':'observed_working_continuation_basis_not_canonical_promotion','source':rel(source),'source_sha256':sha(source),'final_scene_records':[c for c in state['chapters'] if c['chapter']>=31],'unresolved_boundaries':['U01 emergency mechanism','U02 old archive consent','U03 cause of external reserve and other candidate reserves','U04 exact financial balance','U05 Maya after the paid night'],'next_volume_limit':'No explanation of early reserve, mind reading, hidden traitor or restored professional rights is established. Friendship and registered inquiry are actual, separate outcomes.'})
write(phase/'dependency-sync.json',{'source_sha256':sha(source),'predecessor_sha256':changes['predecessor_sha256'],'working_revision_only':True,'synchronized':['36 chapter texts and complete assembly','41 scene states and82 literal proof quotes','events, time, knowledge, resources and open-dependency maps','paragraph anchors and reader extraction','exact before/after and implementation ledger','observed final state and inherited working proposals','book pointers, session, revision log, audit boundaries and delivery files'],'planned_registers':'Central planned projections retain planned status; this revision has its own observed records.','unchanged_canon':'No canonical master, character biography, future volume or original source silently changed.','promise_and_voice_verification':{'report':rel(report),'sha256':sha(report),'scope':'Full-volume final Astra reading against complete outline, scene cards and applied corrections.'}})
ledger=read(run/'reconciliation-v1/issue-ledger.json');by_issue={}
for p in changes['patches']:
    for issue in p['issue_ids']:by_issue.setdefault(issue,[]).append(p['id'])
for item in ledger['items']:
    item['implementation']={'status':'applied' if by_issue.get(item['id']) else 'context_preserved_or_metadata_checked','patches':by_issue.get(item['id'],[]),'basis':'Explicit bulk author instruction; no individual author vote inferred.'}
    item['verification']={'status':'verified_with_recorded_limits','source_sha256':sha(source),'evidence':[rel(report),rel(run/'final-acceptance.json')],'scope':'Final full reading plus exact patch/state/quote checks; original evidence remains bound to v2.'}
ledger.update(status='implemented_and_verified_working_revision',final_source_sha256=sha(source),original_ledger_sha256=sha(run/'reconciliation-v1/issue-ledger.json'))
write(phase/'implementation-ledger.json',ledger)
lines=['# Було — стало: другий том','',f'Попередній SHA: `{changes["predecessor_sha256"]}`.',f'Поточний SHA: `{sha(source)}`.','', 'Текст змін написала Terra після зведення Astra. Окремі авторські голоси не вигадані; правки виконані в межах загального доручення.','']
for p in changes['patches']:
    lines.extend([f'## {p["id"]} — глава {p["chapter"]}','', '**Було**','',p['before'],'','**Стало**','',p['after'],'',p['reason'],''])
(phase/'BEFORE-AFTER.md').write_text('\n'.join(lines),encoding='utf-8',newline='\n')
q=run/'QUESTIONS-AND-LIMITS-BOOK02.md'
q.write_text('# Контакт 2 — межі знання й необов’язкові питання автору\n\nПовна робоча редакція завершена. Наведені факти свідомо не вигадані; вони не блокують читання цього тому.\n\n1. Точний механізм аварійної допомоги з кінця тому 1 не визначений як універсальний ключ.\n2. Повна первісна згода у старому службовому архіві Майї не відновлена.\n3. Причина раннього резерву й перелік інших зарезервованих варіантів залишаються питанням фіналу.\n4. Точний залишок грошей Даля не встановлено.\n5. Обставини Майї після однієї оплаченої ночі не встановлені.\n\nВаші доповнення, якщо потрібні: \n\n\nРедакторські межі: Opus не повернув тексту через недоступність запуску; використано ваш виняток. Gemini Pro повідомив про стиснення ранніх частин контексту. Запитані моделі й клієнти записані, backend незалежно не атестований. Після зведення Terra внесла правки, Astra прочитала весь кінцевий текст. Це робоча редакція для автора, не затвердження до публікації.\n\nРедагування цієї копії на Desktop імпортується назад у Git тільки явною окремою дією.\n',encoding='utf-8',newline='\n')
meta=read(book/'book.json');meta.update(stage='working_revision_complete',audit_status='compatible_revision_verified_opus_availability_exception',current_writer='Terra; structure and rough Astra')
meta['draft_scope'].update(whole_book_written=True,whole_book_ready=True,current_prose_phase='terra_revised',readiness_scope='Complete corrected working volume, not publication or authorcanonical approval',phase_progress='production/2026-09-23-book02/final-acceptance.json')
meta['working_revision']={'path':source.relative_to(book).as_posix(),'sha256':sha(source),'format':'md','language':'uk','status':'complete_corrected_working_volume','observed_state':(phase/'observed-state.json').relative_to(book).as_posix()}
meta['working_volume']={'manifest':(phase/'assembled/assembly.json').relative_to(book).as_posix(),'chapters':36,'status':'complete_corrected_working_volume'};write(book/'book.json',meta)
meta['preserved_full_text_before_revision']=meta['active_full_text']
meta['active_full_text']={'path':source.relative_to(book).as_posix(),'sha256':sha(source),'chapters':36,'canonical_status':'working_not_author_approved'}
write(book/'book.json',meta)
progress=read(run/'progress.json')
for p in progress['phases']:p['status']='complete_with_recorded_opus_exception' if p['phase']=='independent_literary_reviews' else 'complete'
progress.update(final_source_sha256=sha(source),final_acceptance='final-acceptance.json',full_text_checkpoint_commit='31a393c',canonical_master_assigned=False);write(run/'progress.json',progress)
log=read(book/'revision-log.json');assert not any(x['id']=='kontakt-book02-final-20260923' for x in log['items'])
log['items'].append({'id':'kontakt-book02-final-20260923','reason':'Author workflow completed: Astra structure and all rough; Terra full prose; independent diagnoses; Astra reconciliation; Terra final correction; fresh full Astra check.','old_source':{'path':rel(run/'terra-full-v2/assembled/manuscript.md'),'sha256':changes['predecessor_sha256']},'new_source':{'path':rel(source),'sha256':sha(source)},'decision':'author_bulk_instruction_implemented_no_individual_votes','changes':rel(phase/'BEFORE-AFTER.md'),'affected_checks':rel(run/'final-acceptance.json'),'observed_state':rel(phase/'observed-state.json')});write(book/'revision-log.json',log)
issues=read(book/'audit/issues.json')
for item in issues['items']:
    if item['id'].startswith('KONTAKT-B02-20260923-U'):
        item['previous_verification']=item.get('verification');item['verification']={'source':rel(source),'source_sha256':sha(source),'scope':'All36 final chapters; boundary retained, unknown not used as established fact.','status':'passed_with_unresolved_boundary','evidence':rel(report)}
issues['current_working_review']={'ledger':rel(phase/'implementation-ledger.json'),'source_sha256':sha(source),'status':'completed_with_recorded_limits'};write(book/'audit/issues.json',issues)
session=f'''# Том 2 — завершена робоча редакція\n\nВиконано весь авторський порядок: повна структура Astra → всі 36 первинних глав Astra → повний текст Terra → незалежні діагнози → звірка Astra → фінальні правки Terra → повне заключне читання Astra.\n\nПоточний SHA: `{sha(source)}`. Усі 36 глав / 41 сцена; {len(source.read_text(encoding='utf-8').split())} слів. [Передача](production/2026-09-23-book02/DELIVERY.md). [Перевірки](production/2026-09-23-book02/final-acceptance.json).\n\n22 точні зміни прози; всі 45 пунктів зведення мають пояснення. Стан сцени, час, знання, ресурси й докази синхронізовані окремо від планових проєкцій. Старі джерела, native-відповіді й незмінні рецензії збережені. Master не призначений.\n\nTerra та обидві Gemini повернули повні звіти; Pro повідомив про стиснення частин 1–3. Opus недоступний: запит відхилено клієнтом, текст не прочитаний. Застосовано прямий авторський виняток. Не заявляються словникова, аудіо- чи людська бета-перевірки.\n\nU01–U05 залишаються обмеженими невідомими, не помилками, приховано розв’язаними моделлю. [Питання та межі](production/2026-09-23-book02/QUESTIONS-AND-LIMITS-BOOK02.md). DOCX і всі змінені матеріали передаються на Desktop разом із відповідною редакцією в Git.\n'''
archive=run/'session-before-final.md';assert not archive.exists();shutil.copy2(book/'session.md',archive);(book/'session.md').write_text(session,encoding='utf-8',newline='\n')
reader=list((phase/'assembled/reader').glob('*.docx'));assert len(reader)==1
delivery=f'''# Контакт 2 — Розфокус. Одноденки\n\nЗавершена повна робоча редакція: 36 глав, 41 сцена, {len(source.read_text(encoding='utf-8').split())} слів. SHA-256: `{sha(source)}`.\n\n- [Рукопис](terra-final-v3/assembled/manuscript.md).\n- [DOCX для читання](terra-final-v3/assembled/reader/{reader[0].name.replace(' ','%20')}).\n- [Було — стало](terra-final-v3/BEFORE-AFTER.md), [усі 45 пунктів](terra-final-v3/implementation-ledger.json).\n- [Зведення Astra](reconciliation-v1/reconciliation.md), [заключне читання](final-astra-native-v1/REPORT.md), [перевірки](final-acceptance.json).\n- [Межі й питання](QUESTIONS-AND-LIMITS-BOOK02.md).\n\nСтруктуру й усі чернетки підготувала Astra; повний текст та остаточні виправлення — Terra. Незалежні діагнози Terra й двох Gemini збережені на попередньому джерелі. Opus пропущений через фактичну недоступність за вашим дозволом; Pro мав стиснений контекст ранніх частин. Після правок виконано нове повне читання Astra.\n\nDOCX перевірено вилученням і переглядом усіх сторінок Chromium-прев’ю; це не native Word. Книга готова як завершена робоча редакція для автора, без мовчазного призначення каноном чи публікації.\n'''
(run/'DELIVERY.md').write_text(delivery,encoding='utf-8',newline='\n')
start=root/'kontakt/START_HERE.md';text=start.read_text(encoding='utf-8');start.write_text('# Контакт — завершені робочі редакції томів 1 і 2\n\n[Том 1: редакція й передача](books/book-01/revisions/2026-09-23-integration/DELIVERY.md). [Том 2: повний авторський цикл і передача](books/book-02/production/2026-09-23-book02/DELIVERY.md). Обидва томи мають DOCX, журнали змін, зафіксовані перевірки й копії на Desktop. Master не призначений.\n\n## Історія попередніх контрольних точок\n\n'+text,encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for area in [run]:
    for f in area.rglob('*'):
        if f.is_file() and '__pycache__' not in f.parts:
            d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d)
for f in [book/'book.json',book/'revision-log.json',book/'audit/issues.json',book/'session.md',start]:
    d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
for dest in [Path('C:/Users/alexi/Desktop'),Path('C:/Users/alexi/OneDrive/Desktop')]:
    for f in [reader[0],q]:shutil.copy2(f,dest/f.name)
print(json.dumps({'status':'working_volume_synchronized_and_mirrored','sha256':sha(source),'chapters':36,'patches':22}))
