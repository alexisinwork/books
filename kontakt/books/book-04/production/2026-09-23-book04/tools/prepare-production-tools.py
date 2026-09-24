"""Copy parameterized transport/integrity helpers with explicit predecessor provenance."""
from pathlib import Path
import ast,hashlib,json,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
source=root/'kontakt/books/book-03/production/2026-09-23-book03/tools'
names=['run-native-author.py','run-native-review.py','import-terra-block.py','assemble-working-volume.py','verify-complete-phase.py','record-reading.py']
items=[]
for name in names:
 p=source/name;dest=run/'tools'/name;assert not dest.exists()
 raw=p.read_text(encoding='utf-8');new=raw.replace('KONTAKT-BOOK03-2026-09-23','KONTAKT-BOOK04-2026-09-23')
 ast.parse(new);dest.write_text(new,encoding='utf-8',newline='\n')
 items.append({'source':p.relative_to(root).as_posix(),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'path':dest.relative_to(root).as_posix(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'change':'Desktop target changed; source/schema arguments remain dynamic. No literary verification performed.'})
record=run/'tool-provenance.json';record.write_text(json.dumps({'items':items,'validation':'All copied helpers parsed as Python; execution awaits relevant phases.'},indent=2)+'\n',encoding='utf-8')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK04-2026-09-23')
for p in [record,Path(__file__).resolve(),*[run/'tools'/n for n in names]]:
 d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
print(json.dumps({'copied':len(items),'syntax':'passed'}))
