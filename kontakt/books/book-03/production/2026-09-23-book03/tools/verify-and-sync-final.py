"""Check native Terra patch application and synchronize the bounded working registry."""
from pathlib import Path
import argparse,json,hashlib,shutil,copy
p=argparse.ArgumentParser();p.add_argument('--phase',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=a.phase.resolve();book=run.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def rel(p):return p.relative_to(root).as_posix()
source=phase/'assembled/manuscript.md';h=sha(source);text=source.read_text(encoding='utf-8');blocks=text.rstrip('\n').split('\n\n')
plan=read(run/'reconciliation-v1/PATCH-PLAN.json');changes=read(phase/'changes.json');state=read(phase/'observed-state.json')
assert not (run/'final-patch-verification.json').exists()
assert changes['predecessor_sha256']==plan['source_sha256'] and not changes['omissions']
inv=read((root/changes['response']).parent/'invocation.json');assert inv['exit_code']==0 and inv['model_requested']=='gpt-5.6-terra' and inv['item_types']==['agent_message']
assert {p['id'] for p in changes['patches']}=={p['id'] for p in plan['patches']}
checks=[];expected={n:(run/f'terra-full-v1/chapters/chapter-{n:02d}.md').read_text(encoding='utf-8') for n in range(1,33)}
for patch in changes['patches']:
 original=next(p for p in plan['patches'] if p['id']==patch['id']);assert patch['before']==original['before'] and patch['chapter']==original['chapter'] and set(patch['issue_ids'])==set(original['issue_ids'])
 assert expected[patch['chapter']].count(patch['before'])==1;expected[patch['chapter']]=expected[patch['chapter']].replace(patch['before'],patch['after'],1)
 assert text.count(patch['after'])==1
 start=text.index(patch['after']);anchor=len(text[:start].split('\n\n'))
 checks.append({'id':patch['id'],'chapter':patch['chapter'],'final_start_paragraph':f'P{anchor:05d}','before_exact':True,'after_exact':True})
changed=[]
for n,value in expected.items():
 f=phase/f'chapters/chapter-{n:02d}.md';assert f.read_text(encoding='utf-8')==value,n
 if sha(f)!=sha(run/f'terra-full-v1/chapters/chapter-{n:02d}.md'):changed.append(n)
account=[];assert len(changes['state_updates'])==len(plan['metadata_updates'])==22
for item in plan['metadata_updates']:
 scene=next(s for c in state['chapters'] if c['chapter']==item['chapter'] for s in c['observed']['scenes'] if s['id']==item['scene_id'])
 updates=[u for u in changes['state_updates'] if u['scene_id']==item['scene_id'] and u['field']==item['field']];assert len(updates)==1
 u=updates[0];assert u['before']==item['before'] and scene[item['field']]==u['after']
 account.append({'id':item['id'],'scene_id':item['scene_id'],'field':item['field'],'actual_after':u['after'],'matches_proposed_after':u['after']==item['after'],'status':'applied_pending_final_full_reading'})
issues_path=book/'audit/issues.json';issues=read(issues_path);prior=phase/'global-registry-before.json';assert not prior.exists();shutil.copy2(issues_path,prior)
g=plan['global_registry_updates'][0];assert len(plan['global_registry_updates'])==1
item=next(x for x in issues['items'] if x['id']==g['target_id']);assert item[g['field']]==g['before'];old=copy.deepcopy(item)
proof=[]
for ev in g['evidence']:
 q=ev['quote'];matches=[i for i,b in enumerate(blocks,1) if q in b];assert len(matches)==1
 proof.append({'source':rel(source),'source_sha256':h,'chapter':ev['chapter'],'paragraph':f'P{matches[0]:05d}','quote':q})
item['history']=item.get('history',[])+[old];item['resolution_status']='resolved';item['resolution_scope']='Limited documentary explanation in this working edition only: multi-candidate capacity prepared before selection, including unused alternatives. Not full private-model-input knowledge, staged rebellion, budget formula or author canonical approval.'
item['implementation_basis']='Explicit continuation and bulk correction instruction; B03-M023; new documentary knowledge acquired in CH02/04/05.';item['anchors']=proof
for item in issues['items']:
 if item['id'].startswith('KONTAKT-B03-20260923-'):
  item['previous_verification']=item.get('verification');item['verification']={'source':rel(source),'source_sha256':h,'status':'pending_final_full_reading','scope':'Full32chapter working revision; source-bound Astra final check pending.'}
assert len([x for x in issues['items'] if x['id'].startswith('KONTAKT-B03-20260923-') and x['resolution_status']=='unresolved'])==7
write(issues_path,issues)
account.append({'id':g['id'],'target_id':g['target_id'],'status':'applied_limited_working_resolution_pending_final_check','evidence':proof})
write(phase/'metadata-plan-accounting.json',{'source_sha256':h,'plan_sha256':sha(run/'reconciliation-v1/PATCH-PLAN.json'),'items':account,'preservation_checks':plan['no_change_verification_items'],'preservation_status':'requires_fresh_final_Astra_reading'})
write(run/'final-patch-verification.json',{'status':'exact_native_patch_application_verified_not_literary_verdict','source_sha256':h,'predecessor_sha256':changes['predecessor_sha256'],'native_invocation_sha256':sha((root/changes['response']).parent/'invocation.json'),'patches':checks,'changed_chapters':changed,'unchanged_chapters':[n for n in range(1,33) if n not in changed],'no_unlisted_prose_changes':True,'state_updates':22,'global_updates':1,'packet_choice':'Unused packet-v1 preserved. Executed packet-v2 compacts JSON whitespace with parsed equality; no fields removed.'})
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),issues_path,run/'final-patch-verification.json',*[p for p in phase.rglob('*') if p.is_file()]]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d)
print(json.dumps({'source_sha256':h,'patches':len(checks),'changed_chapters':len(changed),'scene_updates':22,'global_updates':1,'state_wording_differences':[x['id'] for x in account if x.get('matches_proposed_after') is False]}))
