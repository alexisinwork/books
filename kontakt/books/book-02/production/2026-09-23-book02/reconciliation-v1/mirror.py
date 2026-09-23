from pathlib import Path
import shutil,hashlib,json
p=Path(__file__).resolve().parent;root=p.parents[5];bundle=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23');files=list(p.rglob('*'))
run=p.parent/'literary-v1/run.json'
if run.exists():files.append(run)
checks=[]
for f in files:
 if f.is_file() and f.name!='desktop-copy-manifest.json':
  dest=bundle/f.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);s=hashlib.sha256(f.read_bytes()).hexdigest();assert s==hashlib.sha256(dest.read_bytes()).hexdigest();checks.append(dict(path=str(f.relative_to(root)),sha256=s,verified=True))
out=p/'desktop-copy-manifest.json';out.write_bytes((json.dumps(dict(bundle=str(bundle),files=checks),ensure_ascii=False,indent=2)+'\n').encode('utf-8'));shutil.copy2(out,bundle/out.relative_to(root))
print(len(checks))
