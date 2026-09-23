import json,re,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
BOOK=ROOT/'kontakt/books/book-01'
SOURCE=BOOK/'revisions/2026-09-23-author-revision/manuscript.md'
text=SOURCE.read_text(encoding='utf-8-sig')
sha=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
items=json.loads((BOOK/'audit/issues.json').read_text(encoding='utf-8-sig'))['items']
parts=re.split(r'(?m)^# Розділ (\d+)\s*$',text)
chapters={int(parts[i]):[p.strip() for p in re.split(r'\n\s*\n',parts[i+1]) if p.strip()] for i in range(1,len(parts),2)}
def chapter(i):
 m=re.match(r'CH(\d+)',i['id'])
 return int(m[1]) if m else None
if __name__=='__main__':
 lo,hi=map(int,sys.argv[1:3])
 print('SHA',sha)
 for n in range(lo,hi+1):
  print('\nCHAPTER',n)
  ps=chapters[n]
  seen=set()
  for it in items:
   if chapter(it)!=n: continue
   print('\nID',it['id'],'OBS',it.get('observation'),'PROPOSED',it.get('proposed_change',''))
   for a in it.get('anchors',[]):
    q=a.get('quote','')
    matches=[j for j,p in enumerate(ps) if q and q in p]
    if not matches:
     tokens=q.split(); scores=[sum(t in p for t in tokens)/max(1,len(tokens)) for p in ps]
     if q and scores: matches=[max(range(len(ps)),key=lambda j:scores[j])]; print('FUZZY',q)
     else: print('NO QUOTE',a); continue
    for j in matches[:2]:
     for k in range(j,j+1):
      print(f'P{k+1:04d}',ps[k] if k not in seen else '[above]'); seen.add(k)
