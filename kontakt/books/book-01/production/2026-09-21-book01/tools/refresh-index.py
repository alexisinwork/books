"""Update FILES.json from the Git index, excluding unrelated unstaged work."""
from pathlib import Path
import json,subprocess
entries=[]
for rec in subprocess.check_output(['git','ls-files','-s','-z']).split(b'\0'):
 if not rec:continue
 meta,path=rec.split(b'\t',1);mode,oid,stage=meta.decode().split();p=path.decode('utf-8')
 assert stage=='0','Resolve index conflicts first'
 if p!='FILES.json':entries.append((p,oid))
sizes=subprocess.check_output(['git','cat-file','--batch-check=%(objectsize)'],input=('\n'.join(oid for p,oid in entries)+'\n').encode()).decode().splitlines()
assert len(sizes)==len(entries)
v={'count_excluding_this_index':len(entries),'scope':'Git-index delivery snapshot; unrelated unstaged and untracked work excluded.','files':[{'path':p,'bytes':int(size)} for (p,oid),size in zip(entries,sizes)]}
Path('FILES.json').write_bytes((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
subprocess.run(['git','add','--','FILES.json'],check=True)
print(json.dumps({'indexed_files':len(entries),'source':'Git index'}))
