from pathlib import Path
import hashlib,json,re,sys,shutil
P=Path(__file__).resolve().parent;RUN=P.parent;ROOT=P.parents[5]
SOURCE=RUN/'terra-full-v1/assembled/manuscript.md';SHA='ab11580a6c9adcaa9a3af4696a4466979e38f6e138633e5230f802d675ff1c6b'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SHA
blocks=SOURCE.read_text(encoding='utf-8').rstrip('\n').split('\n\n');assert len(blocks)==1540
items=[];chapter=0
for n,b in enumerate(blocks,1):
 m=re.match(r'^# Розділ (\d+)',b)
 if m:chapter=int(m.group(1))
 items.append(dict(id=f'P{n:05}',chapter=chapter,text=b))
if sys.argv[1]=='init':
 (P/'source-blocks.json').write_text(json.dumps(dict(source_sha256=SHA,blocks=items),ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 for f in P.iterdir():
  if f.is_file():
   d=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')/f.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
else:
 lo=int(sys.argv[1]);hi=int(sys.argv[2])
 for x in items:
  if lo<=x['chapter']<=hi:print(f"[{x['id']}] {x['text']}\n")
