from pathlib import Path
import hashlib,json,re,shutil
p=Path(__file__).resolve().parent
changes=[]
for f in sorted((p/'chapters').glob('chapter-*.md')):
 old=f.read_bytes();s=old.decode('utf-8');t=re.sub(r'\n{3,}','\n\n',s.replace('\r\n','\n').replace('\r','\n')).rstrip()+'\n';new=t.encode('utf-8')
 assert re.sub(r'\s+','',s)==re.sub(r'\s+','',t)
 if old!=new:
  h=p/'history'/'before-lf-normalization'/f.name;h.parent.mkdir(parents=True,exist_ok=True);assert not h.exists();shutil.copy2(f,h);f.write_bytes(new)
  changes.append(dict(chapter=int(f.stem[-2:]),path=str(f.relative_to(p)),before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(new).hexdigest(),history=str(h.relative_to(p)),whitespace_only=True))
(p/'normalization-manifest.json').write_bytes((json.dumps(dict(scope='36 chapter files; UTF8 LF, exactly one blank line between blocks; no prose changes',changes=changes),ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps(dict(normalized=len(changes),all_36_checked=True)))
