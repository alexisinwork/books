"""Copy the staged Kontakt change set into a new, verified Desktop bundle."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path
p=argparse.ArgumentParser(); p.add_argument('--bundle',required=True); p.add_argument('--manifest',type=Path,required=True); args=p.parse_args()
r=Path.cwd().resolve(); desktop=Path('C:/Users/alexi/OneDrive/Desktop').resolve()
dest=(desktop/args.bundle).resolve(); dest.relative_to(desktop)
assert dest!=desktop and not dest.exists(),'Use a fresh checkpoint folder; never overwrite author copies'
assert not args.manifest.exists(),'Delivery records are immutable'
raw=subprocess.check_output(['git','diff','--cached','--name-only','--diff-filter=ACMRT','-z'])
paths=[s.decode('utf-8') for s in raw.split(b'\0') if s]
assert all(s.startswith('kontakt/') or s=='FILES.json' for s in paths),'Unrelated staged work; stop without copying'
items=[]
for s in paths:
 f=r/s; content=f.read_bytes(); staged=subprocess.check_output(['git','show',':'+s]); assert content==staged,'Staged bytes differ: '+s
 out=dest/s; out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(f,out); assert out.read_bytes()==content
 items.append({'path':s,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)})
report={'bundle':str(dest),'scope':'staged Kontakt changes and root delivery index; no promotion of Desktop edits','files':items,'verification':'disk == staged blob == Desktop bytes','manifest_self_excluded':True}
args.manifest.parent.mkdir(parents=True,exist_ok=True); args.manifest.write_bytes((json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
out=dest/args.manifest.resolve().relative_to(r); out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(args.manifest,out); assert out.read_bytes()==args.manifest.read_bytes()
print(json.dumps({'copied':len(items),'bundle':str(dest)},ensure_ascii=False))
