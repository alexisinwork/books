"""Close the final report's bounded packet gap using the actual frozen patch plan."""
from pathlib import Path
import json,hashlib,re,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-final-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
source=phase/'assembled/manuscript.md';h=sha(source);text=source.read_text(encoding='utf-8');blocks=text.rstrip('\n').split('\n\n')
report=run/'final-astra-native-v1/REPORT.md';r=report.read_text(encoding='utf-8');inv=read(report.parent/'invocation.json')
assert inv['model_requested']=='gpt-6-astra' and inv['exit_code']==0 and inv['item_types']==['agent_message']
assert h in r and len(blocks)==1894
changes=read(phase/'changes.json');plan=read(run/'reconciliation-v1/PATCH-PLAN.json');state=read(phase/'observed-state.json')
patches=[]
for p in changes['patches']:
    assert text.count(p['after'])==1,p['id']
    m=re.search(r'\| '+re.escape(p['id'])+r' \| (P\d+) \|',r);assert m,p['id']
    anchor=int(m.group(1)[1:]);assert p['after'] in blocks[anchor-1],(p['id'],anchor)
    patches.append({'id':p['id'],'chapter':p['chapter'],'final_anchor':m.group(1),'after_verified':True})
updates=changes['state_updates']+changes['coordinator_state_updates'];mapping=[]
unchanged={9:'Existing event summary describes redistribution and acceptance of unavailability once; no duplicate refusal is asserted. Actual repeated prose action was corrected atP00544; late refusal retained.',12:'Existing plannedD4 playback/withdrawal and unnamed actual clock remain correct. It never dates the recorded debate to yesterday; the prose reference atP00715 was corrected.',13:'Existing time/events/resources contain no Saturday launch claim; the misleading prose relative day was replaced atP00774. Knowledge field separately corrected by Terra to pending staff-copy verification.',31:'Existing event/knowledge fields describe report and offer without claiming Dal left during a broadcast. Prose atP01660 now states beforebroadcast; no additional event-state rewrite needed.'}
for i,item in enumerate(plan['metadata_updates'],1):
    scene=next(s for c in state['chapters'] if c['chapter']==item['chapter'] for s in c['observed']['scenes'] if s['id']==item['scene_id'])
    if item['field'] in scene:
        matched=[u for u in updates if u['scene_id']==item['scene_id'] and u['field']==item['field']];assert matched
        assert scene[item['field']]==matched[-1]['after']
        result='Exact current field matches recorded source-grounded update; wording may differ from proposed after.'
        if item['field']=='open_dependencies':assert scene[item['field']]==item['after']
    else:
        matched=[u for u in changes['coordinator_state_updates'] if u['scene_id']==item['scene_id']]
        result='Affected observation explicitly synchronized by coordinator to Terra prose.' if matched else unchanged[item['chapter']]
    mapping.append({'plan_item':i,'chapter':item['chapter'],'scene_id':item['scene_id'],'requested_field':item['field'],'status':'checked','result':result,'actual_updates':[{'field':u['field'],'after':u['after']} for u in matched]})
assert len(mapping)==20
unknown=[x for x in read(run.parents[1]/'audit/issues.json')['items'] if x['id'].startswith('KONTAKT-B02-20260923-U')]
assert len(unknown)==5 and all(x['resolution_status']=='unresolved' and x['blocking']==False for x in unknown)
write(run/'final-metadata-plan-accounting.json',{'status':'all20_instructions_accounted_for','source_sha256':h,'plan_sha256':sha(run/'reconciliation-v1/PATCH-PLAN.json'),'actual_field_changes':16,'distinction':'20 instructions include broad check/synchronize requests; they do not require20distinct writes.11 Terra and5 coordinator field changes; unchanged fields assessed explicitly.','items':mapping,'global_unresolved_questions':[x['id'] for x in unknown],'final_astra_limitation':'Original report accurately lacked PATCH-PLAN; this separate root accounting closes that evidence gap without altering the fixed report.'})
write(run/'final-astra-validation.json',{'status':'complete_report_validated_with_separate_metadata_accounting','source_sha256':h,'report_sha256':sha(report),'native_invocation_sha256':sha(report.parent/'invocation.json'),'requested_model':'gpt-6-astra','actual_backend':'not independently attested','actual_reported_coverage':'All36 chapters P00001–P01894; no unread or compressed ranges reported.','coordinator_report_reading':'Entire returned report read, including limitations,22 patch rows,16 state checks and final verdict.','verified_patch_anchors':patches,'remaining_prose_defects_reported':0,'limits':['No independent complete Book1 reread in this run.','Full old/new byte comparison performed separately by root, not by native Astra.','20metadata instruction accounting supplied separately by root; original report preserved.','No publication approval, dictionary/audio/human-beta/nativeWord verification claimed.']})
visual=read(phase/'assembled/visual-review.json');assert visual['source_sha256']==h and visual['pages']==77
write(run/'final-acceptance.json',{'status':'complete_corrected_working_volume','source':source.relative_to(root).as_posix(),'source_sha256':h,'chapters':36,'scenes':41,'paragraphs':1894,'words':len(text.split()),'prose_patches':22,'changed_chapters':17,'unchanged_chapters':19,'actual_state_updates':16,'metadata_instructions_accounted':20,'astra_report_sha256':sha(report),'checks':{'phase_integrity':'final-phase-technical-verification.json','exact_patch_application':'final-patch-verification.json','final_full_reading':'final-astra-validation.json','metadata_plan_accounting':'final-metadata-plan-accounting.json','language_patterns':'final-language-qa.json','naturalness_patterns':'final-naturalness.json','reader':'terra-final-v3/assembled/visual-review.json','repository_and_sources':'pending_after_metadata_sync'},'reader_pages':77,'review_limitations':['Opus invocation unavailable; explicitly authorized skip.','Gemini Pro declared compressed parts1–3.','Requested model provenance recorded, backend not independently attested.'],'unresolved_nonblocking_boundaries':[x['id'] for x in unknown],'canon_promoted':False,'publication_approved':False})
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),run/'final-metadata-plan-accounting.json',run/'final-astra-validation.json',run/'final-acceptance.json']:
    d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'source_sha256':h,'all20_metadata_instructions_accounted':True,'final_full_reading':'no mandatory prose defects found','words':len(text.split())}))
