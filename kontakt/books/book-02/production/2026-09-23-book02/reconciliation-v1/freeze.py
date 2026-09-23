from pathlib import Path
import hashlib,json,subprocess,sys
P=Path(__file__).resolve().parent;R=P.parent;ROOT=P.parents[5];L=R/'literary-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
source=R/'terra-full-v2/assembled/manuscript.md'
assert sha(source)=='e641f3b639f0c03578c51916c0434156c584ce8022f556d94e522bf7c653679d'
run_before=(L/'run.json').read_bytes();attempts=[]
for args in [['verify','--run',str(L)],['record','--run',str(L),'--role','reconciliation']]:
 command=[sys.executable,'-X','utf8',str(ROOT/'tools/editorial_ensemble.py'),*args]
 result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf-8')
 attempts.append(dict(command=command,exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
 assert (L/'run.json').read_bytes()==run_before,'Legacy command unexpectedly changed run'
save(P/'legacy-cli-validation.json',dict(status='incompatible_with_author_override',attempts=attempts,interpretation='Legacy CLI cannot represent author workflow: three locked independent reports plus expressly permitted failed Opus attempt, followed by nonblind Astra reconciliation. No fictitious fourth diagnosis or individual author vote created. Source/quote/schema checks passed separately.'))
run=rd(L/'run.json');run['reconciliation']=dict(path='../reconciliation-v1/reconciliation.md',status='locked',sha256=sha(P/'reconciliation.md'),scope='All36/1894 actual nonblind reading;45items;22unique paragraph patchdirections;20metadata updates',validation='../reconciliation-v1/validation.json')
run['issue_ledger_sha256']=sha(P/'issue-ledger.json');run['patch_plan_sha256']=sha(P/'PATCH-PLAN.json');save(L/'run.json',run)
ledger=rd(P/'issue-ledger.json');plan=rd(P/'PATCH-PLAN.json')
assert len({x['id'] for x in ledger['items']})==45
assert len(plan['patches'])==22 and len(plan['metadata_updates'])==20
for patch in plan['patches']:
 assert source.read_text(encoding='utf-8').count(patch['before'])==1
 assert all(i in {x['id'] for x in ledger['items']} for i in patch['issue_ids'])
for proof in rd(P/'sources-manifest.json')['files']:assert sha(ROOT/proof['path'])==proof['sha256']
files=sorted(f for f in P.rglob('*') if f.is_file() and f.name not in {'manifest.json','desktop-copy-manifest.json'})+[L/'run.json']
save(P/'manifest.json',dict(status='frozen',source_sha256=sha(source),phase='Astra nonblind full reconciliation before Terra final',coverage=dict(chapters=36,source_blocks=1894,ledger_items=45,unique_prose_targets=22,metadata_updates=20),limitations=['Opus invocation unavailable; three successful reports, not four.','Pro earlier parts compressed; Flash chronology and some prescriptions unreliable.','Requested Terra model recorded; contradictory self-description not backend attestation.','Individual author votes pending; compatible implementation covered by explicit bulk instruction.','No manuscript mutation; final revisions and final full reading remain future work.'],files=[dict(path=str(f.relative_to(ROOT)).replace('\\','/'),sha256=sha(f)) for f in files]))
print(json.dumps({f.name:sha(f) for f in [P/'reconciliation.md',P/'issue-ledger.json',P/'PATCH-PLAN.json',P/'manifest.json']},indent=2))
