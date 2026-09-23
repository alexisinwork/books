"""Verify frozen predecessor bytes before revising or delivering a later edition."""
from pathlib import Path
import argparse,json,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists()
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
for name in ['structure-v1','astra-rough-v1','terra-full-v1']:
 area=run/name;m=area/'manifest.json';data=json.loads(m.read_text(encoding='utf-8'));files=data['files']
 for item in files:
  f=(root/item['path']) if item['path'].startswith('kontakt/') else (area/item['path']);f.resolve().relative_to(area.resolve());assert sha(f)==item['sha256'],str(f)
 results.append({'phase':name,'manifest_sha256':sha(m),'files':len(files),'status':'unchanged'})
lr=run/'literary-v1';data=json.loads((lr/'run.json').read_text(encoding='utf-8'))
for role in ['terra','gemini_flash','gemini_pro']:
 item=data['reports'][role];f=lr/item['file'];assert sha(f)==item['sha256'],role
 results.append({'role':role,'report_sha256':sha(f),'status':'unchanged'})
report={'status':'frozen_predecessors_unchanged','checks':results,'limitation':'Byte identity only, not a literary verdict.'}
a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),a.out.resolve()]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps(report))
