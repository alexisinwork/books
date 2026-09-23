"""Record an actual completed reading only when explicitly invoked after that reading."""
from pathlib import Path
import argparse,json,hashlib,shutil
p=argparse.ArgumentParser();p.add_argument('--phase',required=True);p.add_argument('--first',type=int,required=True);p.add_argument('--last',type=int,required=True);p.add_argument('--notes',required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
area='root-rough-reading' if a.phase.startswith('astra-rough') else 'root-terra-reading'
dest=run/area/f'chapters-{a.first:02d}-{a.last:02d}.json';assert not dest.exists()
items=[]
for n in range(a.first,a.last+1):
 f=run/a.phase/'chapters'/f'chapter-{n:02d}.md'
 items.append({'chapter':n,'path':f.relative_to(root).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'actual_reading':'Complete current chapter displayed and read by coordinator; not inferred from counters or a summary.'})
record={'status':'nonblind_coordinator_reading','phase':a.phase,'items':items,'notes':a.notes,'limits':'This is coordination reading; not an independent ensemble diagnosis or author approval.'}
dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [dest,Path(__file__).resolve()]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'record':dest.relative_to(root).as_posix(),'chapters':len(items)}))
