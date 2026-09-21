"""Import completed agy reports without rewriting source reports or locked diagnoses.

Mechanical provenance validation only. Read and assess every report separately.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess
p=argparse.ArgumentParser();p.add_argument('--draft',type=Path,required=True);p.add_argument('--run',type=Path,required=True);a=p.parse_args()
def sha(data):return hashlib.sha256(data).hexdigest()
rr=json.loads((a.run/'run.json').read_text(encoding='utf-8'))
assert rr['reports']['astra']['status']=='locked','Lock independent Astra diagnosis before peer import'
h=rr['source']['sha256'];source=Path(rr['source']['path']);assert sha(source.read_bytes())==h
for folder,role,name in [('opus','claude','claude-diagnosis.md'),('flash','gemini_flash','gemini-flash-diagnosis.md'),('pro','gemini','gemini-blind-read.md')]:
 assert rr['reports'][role]['status']!='locked','Never replace a locked report'
 d=a.draft/'checks'/folder;inv=json.loads((d/'invocation.json').read_text(encoding='utf-8'))
 assert inv['client']=='agy' and inv['exit_code']==0 and inv['target_sha256']==h
 assert set(inv['observed_step_types'])<={'agent_response','user_input'},'Tool use requires specific provenance review; do not import automatically'
 raw=(d/'REPORT.md').read_bytes();text=raw.decode('utf-8');assert h in text and len(text.strip())>=200
 assert inv['report_sha256']==sha(raw),'Raw report changed'
 if (d/'stdout.json').exists():
  assert not (d/'stdout.ndjson').exists();(d/'stdout.json').rename(d/'stdout.ndjson')
 header=f"# Independent report import\n\nRun ID: `{a.run.name}`\nSource SHA-256: `{h}`\nReader SHA-256: `{h}`\nRole: `{role}`\nModel: {inv['requested_model']} (requested selector; actual backend not independently attested)\nClient: agy; fresh isolated session; no peer reports supplied; observed user_input/agent_response only.\nStatus: final\nOriginal report SHA-256: `{sha(raw)}`\n\n---\n\n"
 (a.run/name).write_bytes(header.encode('utf-8')+raw)
 subprocess.run(['python','-X','utf8','tools/editorial_ensemble.py','record','--run',str(a.run),'--role',role],check=True)
print(json.dumps({'run':a.run.name,'source_sha256':h,'imported':3,'meaning':'Integrity only; content validation and reconciliation still required'}))
