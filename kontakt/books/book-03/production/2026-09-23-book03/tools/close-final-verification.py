"""Close checks only after root has read the fresh final report and found no mandatory residual."""
from pathlib import Path
import json,hashlib,re,shutil,copy
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-final-v2';book=run.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def rel(p):return p.relative_to(root).as_posix()
source=phase/'assembled/manuscript.md';h=sha(source);text=source.read_text(encoding='utf-8');blocks=text.rstrip('\n').split('\n\n');report=run/'final-astra-native-v2/REPORT.md';r=report.read_text(encoding='utf-8');inv=read(report.parent/'invocation.json')
assert not (run/'final-acceptance.json').exists()
assert h in r and inv['exit_code']==0 and inv['item_types']==['agent_message'] and inv['model_requested']=='gpt-6-astra'
assert len(blocks)==1550
starts=[i for i,b in enumerate(blocks,1) if b.startswith('# Розділ ')];coverage=[]
for n,(first,last) in enumerate(zip(starts,[x-1 for x in starts[1:]]+[len(blocks)]),1):
 assert f'P{first:05d}' in r and f'P{last:05d}' in r,(n,first,last)
 coverage.append({'chapter':n,'first':f'P{first:05d}','last':f'P{last:05d}'})
changes=read(phase/'changes.json');plan=read(run/'reconciliation-v1/PATCH-PLAN.json');assert len(changes['patches'])==28
for p in changes['patches']:assert p['id'] in r and text.count(p['after'])==1,p['id']
for p in plan['metadata_updates']+plan['global_registry_updates']+plan['no_change_verification_items']:assert p['id'] in r,p['id']
qa=read(run/'final-v2-language-qa.json');nat=read(run/'final-v2-naturalness-reviewed.json');tech=read(run/'final-v2-phase-technical-verification.json');visual=read(phase/'assembled/visual-review.json')
assert all(x['source_sha256']==h for x in [qa,nat,tech,visual]);assert not qa['findings'] and nat['unresolved_signals']==0 and tech['matched_state_quotes']==82 and visual['pages']==64
account=read(phase/'metadata-plan-accounting.json');assert account['source_sha256']==h
write(phase/'metadata-plan-accounting.before-final-check.json',account)
for item in account['items']:item.update(status='verified_against_final_prose',final_reading_report=rel(report),report_sha256=sha(report))
account['preservation_status']='all12_verified_in_complete_final_Astra_reading';account['final_reading_report']=rel(report);write(phase/'metadata-plan-accounting.json',account)
ledger=read(run/'reconciliation-v1/issue-ledger.json');ledger['original_ledger_sha256']=sha(run/'reconciliation-v1/issue-ledger.json');ledger['status']='implemented_and_verified_working_revision';ledger['final_source_sha256']=h
for item in ledger['issues']:
 assert item['author_decision']=='pending'
 item['implementation']={'status':'applied' if item['patch_ids'] or item['metadata_ids'] else 'preserved_with_recorded_source_based_reason','patches':item['patch_ids'],'metadata':item['metadata_ids'],'authority':'Explicit bulk instruction; no individual vote inferred.'}
 item['verification']={'status':'verified_with_recorded_limits','source_sha256':h,'report':rel(report),'report_sha256':sha(report)}
ledger['issues'].append({'id':'B03-FINAL-01','category':'local_narrative_subject','observation':'Inserted Osya action left subsequent Taras message without an explicit narrator subject.','author_decision':'pending','implementation':{'status':'applied','patches':['B03-FINAL-01'],'authority':'Explicit compatible revision instruction; native Terra supplied the sole word.'},'source_diagnosis':rel(run/'final-astra-native-v1/REPORT.md'),'verification':{'status':'verified_in_new_complete_final_reading','source_sha256':h,'report':rel(report),'report_sha256':sha(report)}});assert len(ledger['issues'])==82;write(phase/'implementation-ledger.json',ledger)
registry=book/'audit/issues.json';issues=read(registry);shutil.copy2(registry,phase/'global-registry-before-final-verification.json')
unknown=[]
for item in issues['items']:
 if item['id'].startswith('KONTAKT-B03-20260923-'):
  item['verification'].update(status='passed_with_recorded_boundaries',scope='All32chapters in current final Astra reading; unknown facts remain unknown.',report=rel(report),report_sha256=sha(report))
  if item['resolution_status']=='unresolved':unknown.append(item['id'])
assert len(unknown)==7;write(registry,issues)
validation={'status':'complete_final_report_read_and_source_checked','source_sha256':h,'report_sha256':sha(report),'native_invocation_sha256':sha(report.parent/'invocation.json'),'actual_root_report_reading':'Entire returned report read, including32chapter coverage,28patches,23metadata items,12guards,82issue accounting and final verdict.','chapters':coverage,'mandatory_prose_residuals_reported':0,'context':'Fresh native execution; no tools or compaction item observed; model coverage assertion corroborated by detailed source-bound report, not proof of infallibility.','limits':['No independent backend identity attestation.','No new whole-series reread, dictionary/audio/human-beta/nativeWord tests or author publication approval.']};write(run/'final-astra-validation.json',validation)
changed=[n for n in range(1,33) if sha(phase/f'chapters/chapter-{n:02d}.md')!=sha(run/f'terra-full-v1/chapters/chapter-{n:02d}.md')]
gate={'status':'complete_corrected_working_volume','source':rel(source),'source_sha256':h,'chapters':32,'scenes':41,'paragraphs':1550,'words':len(text.split()),'prose_patches':28,'changed_chapters':len(changed),'unchanged_chapters':32-len(changed),'base_reconciliation_issues':81,'final_additional_issue':1,'implemented_or_accounted_issues':82,'scene_state_updates':22,'global_registry_updates':1,'preservation_checks':12,'astra_report':rel(report),'astra_report_sha256':sha(report),'checks':{'phase_integrity':'final-v2-phase-technical-verification.json','exact_patch_application':'terra-final-v2/patch-verification.json','final_full_reading':'final-astra-validation.json','metadata_plan_accounting':'terra-final-v2/metadata-plan-accounting.json','language_patterns':'final-v2-language-qa.json','naturalness_patterns':'final-v2-naturalness-reviewed.json','reader':'terra-final-v2/assembled/visual-review.json','repository_and_sources':'pending_after_metadata_sync'},'reader_pages':64,'review_limitations':['Opus unavailable: no report, repeated error events; explicit author exception.','Gemini Pro checkpoint after first part; all intermediate reports reconciled.','Requested models recorded; backend not independently attested.'],'unresolved_nonblocking_boundaries':unknown,'canon_promoted':False,'publication_approved':False};write(run/'final-acceptance.json',gate)
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),registry,run/'final-astra-validation.json',run/'final-acceptance.json',*[p for p in phase.rglob('*') if p.is_file()]]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d)
print(json.dumps({'source_sha256':h,'chapters':32,'words':gate['words'],'patches':28,'issues':82,'status':gate['status']}))
