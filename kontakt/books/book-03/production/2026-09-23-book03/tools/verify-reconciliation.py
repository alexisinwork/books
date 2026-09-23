"""Validate the frozen, actually read reconciliation before sending it to Terra."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;area=run/'reconciliation-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=run/'terra-full-v1/assembled/manuscript.md';text=source.read_text(encoding='utf-8');blocks=text.rstrip('\n').split('\n\n');h=sha(source)
manifest=read(area/'manifest.json')
for item in manifest['files']:
 f=root/item['path'] if item['path'].startswith('kontakt/') else area/item['path'];f.resolve().relative_to(area.resolve());assert sha(f)==item['sha256'],str(f)
plan=read(area/'PATCH-PLAN.json');ledger=read(area/'issue-ledger.json');assert plan['source_sha256']==ledger['source_sha256']==h
assert len(plan['patches'])==27 and len(ledger['issues'])==81
assert all(i['author_decision']=='pending' for i in ledger['issues'])
intervals=[]
for item in plan['patches']:
 b=item['before'];assert text.count(b)==1 and b==blocks[int(item['paragraph'][1:])-1],item['id']
 pos=text.index(b);assert not any(pos<end and pos+len(b)>start for start,end in intervals);intervals.append((pos,pos+len(b)))
state=read(run/'terra-full-v1/observed-state.json');global_items=plan['global_registry_updates']
for item in plan['metadata_updates']:
 if item['field']=='resolution_status':global_items.append(item);continue
 scene=next(s for c in state['chapters'] if c['chapter']==item['chapter'] for s in c['observed']['scenes'] if s['id']==item['scene_id']);assert scene[item['field']]==item['before'],item['id']
assert len(global_items)==1 and len(plan['metadata_updates'])==22 and len(plan['no_change_verification_items'])==12
out=run/'root-reconciliation-gate.json';assert not out.exists()
out.write_text(json.dumps({'status':'frozen_reconciliation_verified_for_native_terra','source_sha256':h,'manifest_sha256':sha(area/'manifest.json'),'patches':27,'issues':81,'scene_metadata_corrections':22,'global_registry_correction':1,'preservation_checks':12,'actual_root_reading':'Entire reconciliation and handoff; all81issue observations/dispositions/rationales; all27literal before/directions; all23metadata before/after/directions;12preservation directions; full report-validation. Original full source and independent reports read in earlier recorded root passes.','authority':'Explicit bulk instruction, no individual author votes or canonical promotion.','limits':'Source/quote correspondence is mechanical; literary judgments remain source-bound readings with recorded review limitations.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),out]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'status':'passed','patches':27,'metadata':23,'guards':12}))
