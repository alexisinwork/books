"""Freeze actual reviewed reports with explicit transport and interpretive limits."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;area=run/'literary-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
data=read(area/'run.json');assert data['status']=='independent_reviews_running';target=data['source']['sha256'];assert sha(root/data['source']['path'])==target
archive=area/'run-before-lock.json';assert not archive.exists();shutil.copy2(area/'run.json',archive)
checks={}
for role in ['terra','gemini_flash','gemini_pro']:
 result=area/'results'/role;inv=read(result/'invocation.json');report=result/'REPORT.md'
 assert inv['exit_code']==0 and target in report.read_text(encoding='utf-8')
 item={'source_sha256':target,'report_sha256':sha(report),'coordinator_reading':'Complete final report read; for both Gemini all three part reports also read.','status':'accepted_as_editorial_input_with_limits','actual_backend':'not independently attested'}
 if role=='terra':
  assert set(inv['item_types'])<={'agent_message','reasoning'}
  item.update(coverage='Report claims all P00001-P01540 with exact last paragraph; grouped chapter table has off-by-one chapter boundaries. Full source supplied; no tool use or compaction event observed.',anchor_limits='Quote Nabraw vidmovu attributed to P00416 is in P00417; source text must be rebound, not report mutated.',interpretation_limits='Claim that less support is not established conflates proved allocation difference with unproved human value. Earlier professional-status foreshadow suggestion is not an established cause.')
 else:
  assert inv['result_events']==4 and set(inv['observed_step_types'])<={'user_input','agent_response','checkpoint'}
  ev=[json.loads(x) for x in (result/'stdout.ndjson').read_text(encoding='utf-8').splitlines() if x.strip()]
  seen=0;points={}
  for e in ev:
   if e.get('event')=='result':seen+=1
   step=e.get('step_update',{})
   if step.get('step_type')=='checkpoint':points[step.get('step_index')]=seen
  item.update(coverage='All three full target ranges delivered and separately reported read, plus final report through P01540. Chapter labels and some anchor boundaries drift; source anchors take precedence.',context_checkpoints=[{'step_index':i,'completed_result_events_before_checkpoint':n} for i,n in points.items()],compaction_limit='Checkpoint observed; final report does not adequately disclose compressed earlier context. Per-part reports are preserved and must also be reconciled.' if points else 'No checkpoint event observed; final report claims no lost or compressed text.')
  if role=='gemini_flash':item['interpretation_limits']=['CH13 is Monday, not Tuesday. Nine calendar dates are not nine elapsed24h days.','No onward freight ride was taken; no fixed19 return or forced overnight established.','Ballast does not sever all human ties; ordinary exchanges and deliberate optional choices remain.','Municipality/class causation and human-value formula are not established by budget difference. Osya is adult.','Renata is inherited Book2 figure, not proved draft relic. Part1 guess that Ballast is human is superseded.','Do not claim normative dictionary verification; quoted replacements can alter meaning, especially final unopened pages.']
  else:item['interpretation_limits']=['Whole plot is Friday to following Saturday, not Thursday to Monday; historical timestamp windows are separate.','Cart17 return and morning container acceptance are different deadlines; do not merge them.','Absolute lexical claims about peresadnyi, vidkhylyvsia, shchabli lack dictionary verification; evaluate context.','Do not turn intentional verbal humour into invented Russian-source calque.','Return-container task scope is not automatically an established extra pay or time promise.','Dal chosen reading limit is not factual capitulation to an omniscient machine.']
 checks[role]=item
 data['reports'][role]={'role':role,'file':'results/'+role+'/REPORT.md','status':'locked','sha256':sha(report),'validation_status':item['status']}
opus=area/'results/opus';inv=read(opus/'invocation.json');assert inv['result_events']==0 and 'error_message' in inv['observed_step_types']
write(opus/'coordinator-stop-record.json',{'status':'stopped_after_repeated_error_events_without_report','source_sha256':target,'requested_model':'claude-opus-4-6-thinking','client':'agy','observed_error_steps':4,'result_events':0,'reading_established':False,'token_use':'not established by returned stream','action':'After inspecting process12792 and its only agy child5116 with exact requested model, stopped only child5116. Runner finalized preserved stdout, stderr and invocation.','reason_limit':'Stream exposes error_message step types but no diagnostic reason; do not invent quota or invalid-selection cause from a prior run.','author_basis':'Explicit permission to skip unavailable Opus, preserved in WORKFLOW-2026-09-23-BOOK03.md.'})
data['exceptions']=[{'role':'opus','status':'unavailable_author_exception','reading_established':False,'reason':'Four error_message steps, zero returned reports; process stopped by coordinator after repeated errors. Exact backend cause not exposed.','evidence':'results/opus/coordinator-stop-record.json','evidence_sha256':sha(opus/'coordinator-stop-record.json')}]
data['reports']['opus']['status']='unavailable_author_exception';data['effective_locked_diagnoses']=['terra','gemini_flash','gemini_pro'];data['status']='diagnoses_locked_ready_for_astra_reconciliation'
write(area/'coverage-validation.json',{'source_sha256':target,'reports':checks,'limits':'Input delivery and model assertions are not independent proof of perfect reading or literary quality. Reports immutable; all proposed changes require source-bound reconciliation.'})
write(area/'run.json',data)
progress=read(run/'progress.json')
for item in progress['phases']:
 if item['phase']=='independent_literary_reviews':item.update(status='complete_with_documented_opus_exception',run='literary-v1/run.json')
 if item['phase']=='reconciliation_and_full_check':item['status']='in_progress'
write(run/'progress.json',progress)
reader=run/'terra-reader';render=read(reader/'reader/render/render-check.json')
assert render['pages']==70 and render['text_matches_docx_ignoring_layout_whitespace']
write(reader/'visual-review.json',{'status':'working_reader_reviewed_final_layout_pending_revision','source_sha256':target,'pdf_sha256':render['pdf_sha256'],'pages':70,'actual_visual_coverage':'All12contact sheets viewed, covering pages1-70.','observations':['No clipping or blank page found. Chapter starts and body style consistent.','Several short chapter-tail pages, notably18,35,41,48,56,60,67, should be improved in final reader after prose revision.'],'renderer':'docx-preview/Chromium, not native Word'})
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
files=[Path(__file__).resolve(),run/'progress.json',*[f for f in area.rglob('*') if f.is_file()],*[f for f in reader.rglob('*') if f.is_file()],*run.glob('terra-full-*.json')]
for p in files:
 d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d);assert sha(d)==sha(p)
print(json.dumps({'locked':data['effective_locked_diagnoses'],'opus':'unavailable_no_reading','source_sha256':target,'context_checkpoints_pro':checks['gemini_pro']['context_checkpoints']}))
