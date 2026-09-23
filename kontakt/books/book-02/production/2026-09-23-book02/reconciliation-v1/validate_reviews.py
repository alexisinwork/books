from pathlib import Path
import json,re,hashlib,collections
P=Path(__file__).resolve().parent;R=P.parent;ROOT=P.parents[5];L=R/'literary-v1';S=R/'terra-full-v2/assembled/manuscript.md';SHA='e641f3b639f0c03578c51916c0434156c584ce8022f556d94e522bf7c653679d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
assert sha(S)==SHA;paras=S.read_text(encoding='utf-8').strip().split('\n\n')
def anchored(text,tag):
 body=text.split('<'+tag+'>',1)[1].split('</'+tag+'>',1)[0].strip()
 matches=list(re.finditer(r'(?m)^\[P(\d{5})\]\n',body));out=[]
 for k,m in enumerate(matches):
  n=int(m[1]);part=body[m.end():matches[k+1].start() if k+1<len(matches) else len(body)].strip();assert part==paras[n-1],(n,part[:50],paras[n-1][:50]);out.append(n)
 return out
reviews=[];locked=[]
for role in ['terra','gemini_flash','gemini_pro']:
 d=L/'results'/role;inv=rd(d/'invocation.json');report=d/'REPORT.md';delivered=[];provided=[]
 if role=='terra':
  delivered=anchored((d/'prompt.md').read_text(encoding='utf-8'),'TARGET');trace=[json.loads(x) for x in (d/'stdout.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()];types=[x.get('item',{}).get('type') for x in trace if x.get('type')=='item.completed'];assert types==['agent_message'];checkpoints=[];model=inv['model_requested'];context='Single full inline input. Report claims no compression; no tool item or checkpoint in native trace. Model self-description GPT5 contradicts requested gpt-5.6-terra and is not backend attestation.'
 else:
  events=[json.loads(x) for x in (d/'input.ndjson').read_text(encoding='utf-8').splitlines() if x.strip()]
  for e in events:
   text='\n'.join(c.get('text','') for c in e['message']['content'])
   if '<TARGET_PART>' in text:
    got=anchored(text,'TARGET_PART');delivered+=got;provided.append([got[0],got[-1]])
  trace=[json.loads(x) for x in (d/'stdout.ndjson').read_text(encoding='utf-8').splitlines() if x.strip()];types=sorted({x.get('step_update',{}).get('step_type') for x in trace if x.get('event')=='step_update'});checkpoints=[x['step_update'] for x in trace if x.get('step_update',{}).get('step_type')=='checkpoint'];model=inv['requested_model'];context='No checkpoint observed; final report claims no lost/compacted context. This is a model claim, not proof of perfect retention.' if role=='gemini_flash' else 'Checkpoint events observed; turn4 and final disclose compression of parts1–3. Final synthesis therefore did not retain all earlier verbatim context. Never label uncompacted full-context review.'
 assert delivered==list(range(1,1895)),role
 assert sha(report)==inv['report_sha256']
 reports= [dict(file=str(f.relative_to(ROOT)).replace('\\','/'),sha256=sha(f)) for f in sorted(d.glob('turn-*.md'))]
 entry=dict(role=role,status='locked_with_validation_limits',requested_model=model,actual_backend='not_independently_attested',report_sha256=sha(report),report=str(report.relative_to(ROOT)).replace('\\','/'),invocation_sha256=sha(d/'invocation.json'),input_coverage=dict(all1894_exact_source_blocks_verified=True,ranges=provided or [[1,1894]]),reading_claim='Reports claim sequential reading throughP01894 with no unread text; delivery validation is not cognitive attestation.',context=context,checkpoint_events=len(checkpoints),observed_step_or_item_types=types,tools_observed=False,interim_reports=reports,quote_validation='Every actionable/facultative finding is mapped to an actual source paragraph in issue-ledger; final-table and praise prose not exhaustively quote-certified.')
 reviews.append(entry);locked.append(dict(role=role,file=str(report.relative_to(L)).replace('\\','/'),status='locked',sha256=sha(report),validation_status='accepted_as_editorial_input_with_limits'))
op=L/'results/opus';oi=rd(op/'invocation.json');stdout=(op/'stdout.ndjson').read_text(encoding='utf-8');assert 'invalid model selection' in stdout and '"num_turns":0' in stdout
opus=dict(role='opus',status='unavailable_author_exception',requested_model=oi['requested_model'],client='agy',evidence_files=[dict(path=str(f.relative_to(ROOT)),sha256=sha(f)) for f in [op/'invocation.json',op/'stderr.txt',op/'stdout.ndjson',op/'turn-001.md']],actual_reading_established=False,actual_input_tokens=0,actual_turns=0,reason='Execution rejected invalid model selection; empty result, no report. Root separately reports same identifier advertised by model list; this does not make failed invocation available.',policy_basis='series/WORKFLOW-2026-09-23-REVISION-AND-BOOK02.md preserves explicit author permission to skip unavailable Opus; no substitute client/model silently used.')
errors=[dict(role='gemini_flash',claim='Seven days from Thursday to next Wednesday/Friday; chronology flawless',finding='Incorrect: narrative prep D0Monday–D6Sunday, operationD7Monday→D8Tuesday, aftermathD9Wednesday; Friday is futuremeeting. Missed relative-dayerrorsCH12/18/19/30.'),dict(role='gemini_flash',claim='Chapter range table exact',finding='Approximate e.g CH17 claimsP943–985, actualP943–984; CH18 starts985not986; prose quoted findings must use actual map.'),dict(role='terra',claim='Only typo; no causality/timeissues',finding='Scopeclaimdoesnotestablishfindingcompleteness; actual duplicateCH9 and calendarerrorsconfirmed.'),dict(role='gemini_pro',claim='Tableowner returns to confirm completedtable',finding='False payoff: CH33 P01743 says iffinished; onlyreceiptconfirmed. Do notimport invented completion.'),dict(role='gemini_pro',claim='Leakedvideo / immediatelyremoved / Ira simplyworking',finding='Source shows authorizedoldoutsidecopy and renewedrepost; Vectorfirstasksdelaythencomplies; Iraexplicitlydisablednotificationsafterrecognition. Flattened summaries notcanon.'),dict(role='gemini_flash',claim='Тарас ends in vowel; threeц; mandatory genitive or dative ending',finding='Overconfident descriptions not source-supported. DispositionsENS021/022/025 preserve contextualvariants.'),dict(role='all',claim='Perfect/ready for publication/PASS approved',finding='Model opinion only; no authorapproval, publicationauthorization or factualqualitycertificate. Reportsfrozen, correctiveassessmenthere.')]
save(P/'review-validation.json',dict(status='complete_with_explicit_limits',source_sha256=SHA,reviews=reviews,opus=opus,known_report_errors=errors,coverage_table_limit='Actual chapter ranges in actual-paragraph-map.json supersede approximate reviewer tables; no exhaustive audit of every praise sentence claimed.',tooling_limit='Initial editorial_ensemble.py verify failed: run.json did not exist. Current author-specific 4attempts/3reports+Opus exception/Astra reconciliation policy cannot be represented faithfully by fixed legacy schema2 or3; separate custom validation rather than invented independent Astra/Opus report.'))
run=dict(schema_version='author-workflow-2026-09-23',run_id='book02-literary-v1',project_id='kontakt',book_id='book-02',language='uk',status='reconciled_awaiting_terra_final',source=dict(path=str(S.relative_to(ROOT)).replace('\\','/'),sha256=SHA,chapters=36,blocks=1894),required_diagnoses=['terra','gemini_flash','gemini_pro','opus'],effective_locked_diagnoses=['terra','gemini_flash','gemini_pro'],review_policy_basis='Explicit author workflow: isolated Terra +Flash+Pro+Opus attempt, author exception for unavailableOpus; Astra full reconciliation is nonblind and not an invented fourth independent diagnosis.',reports={x['role']:x for x in locked},exceptions=[opus],reconciliation=dict(path='../reconciliation-v1/reconciliation.md',status='final_pending_manifest_lock'),issue_ledger='../reconciliation-v1/issue-ledger.json',patch_plan='../reconciliation-v1/PATCH-PLAN.json',individual_author_decisions='pending; separate bulk compatible implementation authorized',legacy_cli_compatible=False)
save(L/'run.json',run)
# Source-bound proof validation, including current Book1 carry fragments, not a new Book1 whole-volume read.
carry=rd(R/'structure-v2/carry-in-source-lock.json');b1=ROOT/carry['source'];assert sha(b1)==carry['source_sha256'];b1text=b1.read_text(encoding='utf-8')
for proof in carry['proofs']:assert proof['quote'] in b1text
ledger=rd(P/'issue-ledger.json');plan=rd(P/'PATCH-PLAN.json')
for item in ledger['items']:
 assert item['author_decision']['status']=='pending'
 for x in item['locations']:assert x['quote']==paras[int(x['anchor'][1:])-1]
targets=[]
for patch in plan['patches']:
 before=patch['before']
 assert S.read_text(encoding='utf-8').count(before)==1
 assert before==paras[int(patch['anchor'][1:])-1]
 targets.append(patch['anchor'])
assert len(targets)==len(set(targets))
try:
 import jsonschema
 jsonschema.validate(ledger,rd(ROOT/'editorial/schemas/issue-ledger.schema.json'));schema='pass'
except ImportError:
 def check(value, spec, path='$'):
  kinds={'object':dict,'array':list,'string':str,'integer':int,'null':type(None)}
  if 'type' in spec:
   allowed=spec['type'] if isinstance(spec['type'],list) else [spec['type']]
   assert any(isinstance(value,kinds[k]) for k in allowed),(path,'type')
  if 'const' in spec:assert value==spec['const'],(path,'const')
  if 'enum' in spec:assert value in spec['enum'],(path,'enum')
  if isinstance(value,dict):
   assert all(k in value for k in spec.get('required',[])),(path,'required')
   for k,v in value.items():
    if k in spec.get('properties',{}):check(v,spec['properties'][k],path+'.'+k)
  if isinstance(value,list):
   assert len(value)>=spec.get('minItems',0),(path,'minItems')
   if spec.get('uniqueItems'):assert len({json.dumps(v,sort_keys=True) for v in value})==len(value),(path,'uniqueItems')
   for i,v in enumerate(value):check(v,spec.get('items',{}),path+f'[{i}]')
  if isinstance(value,str):
   assert len(value)>=spec.get('minLength',0),(path,'minLength')
   if 'pattern' in spec:assert re.search(spec['pattern'],value),(path,'pattern')
 check(ledger,rd(ROOT/'editorial/schemas/issue-ledger.schema.json'))
 schema='pass: direct recursive validation of every keyword used by repository ledger schema; jsonschema package unavailable'
sources=[S,R/'structure-v2/full-outline.md',R/'structure-v2/chapter-scene-cards.json',R/'structure-v2/carry-in-source-lock.json',R/'structure-v2/decisions-and-questions.json',R/'astra-rough-v1/assembled/manuscript.md',b1,ROOT/'kontakt/series/WORKFLOW-2026-09-23-REVISION-AND-BOOK02.md']
sources += list((R/'root-terra-reading').glob('*.json'))+list((R/'terra-full-v2/states').glob('*.json'))
save(P/'sources-manifest.json',dict(source_scope='Book2 full36 actual read; structure and rough known from preceding construction and compared for dependencies; Book1 current hash +11 carryquotes verified, not all33 newly reread; fixed reviewer outputs inreview-validation.',files=[dict(path=str(f.relative_to(ROOT)).replace('\\','/'),sha256=sha(f)) for f in sources]))
save(P/'validation.json',dict(status='pass',source_sha256=SHA,source_unchanged=True,full_book2_actual_reading_blocks=1894,chapters=36,issue_ledger_items=len(ledger['items']),patches=len(plan['patches']),all_patch_before_unique=True,no_patch_overlap=True,all_ledger_quotes_actual_source=True,all_review_inputs_match_source=True,all_report_hashes_match_invocation=True,book1_carry_quote_matches=len(carry['proofs']),ledger_schema=schema,author_votes_invented=False,remaining='Native Terra final replacements, new source/state derivation and final complete verification not done by reconciliation.'))
print(json.dumps(dict(status='pass',reviews=3,opus='unavailable_with_author_exception',issues=len(ledger['items']),patches=len(plan['patches']),schema=schema)))
