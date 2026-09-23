"""Verify that a bounded native retransmission changed only its intended prose item."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=run/'terra-final-execution-v1/RESPONSE.md';after=run/'terra-final-execution-v2/RESPONSE.md';b=read(before);a=read(after)
assert set(a)==set(b)
for k in ['source_sha256','state_updates','omissions']:assert a[k]==b[k],k
assert len(a['patches'])==len(b['patches'])==27
for old,new in zip(b['patches'],a['patches'],strict=True):
 assert old['id']==new['id']
 if old['id']=='B03-P009':
  assert old['after']!=new['after'];assert {k:v for k,v in old.items() if k not in ['after','reason']}=={k:v for k,v in new.items() if k not in ['after','reason']}
 else:assert old==new,old['id']
inv=read(after.parent/'invocation.json');assert inv['exit_code']==0 and inv['item_types']==['agent_message'] and inv['model_requested']=='gpt-5.6-terra'
out=run/'terra-final-corrigendum-validation.json';assert not out.exists()
out.write_text(json.dumps({'status':'only_native_P009_prose_replaced','full_source_revision_response':{'path':before.relative_to(root).as_posix(),'sha256':sha(before),'reading_scope':b['reading_scope']},'bounded_followup_response':{'path':after.relative_to(root).as_posix(),'sha256':sha(after),'reading_scope':a['reading_scope']},'retained_other_patches':26,'retained_state_updates':22,'limits':'Follow-up is a bounded correction, not a second full-volume reading. Final complete Astra check remains pending.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),out]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'status':'passed','corrected_after':next(x['after'] for x in a['patches'] if x['id']=='B03-P009')},ensure_ascii=False))
