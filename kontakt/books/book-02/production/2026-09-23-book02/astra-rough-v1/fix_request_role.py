from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent;f=p/'chapters/chapter-31.md';o=p/'observations/chapter-31.json';h=p/'history/chapter-31-before-request-role-fix';h.mkdir(parents=True,exist_ok=True)
assert not (h/f.name).exists()
shutil.copy2(f,h/f.name);shutil.copy2(o,h/o.name);old=f.read_bytes();t=old.decode('utf-8');a='пропонувала саме те, що шукали';assert t.count(a)==1;t=t.replace(a,'просила саме ті деталі, які згодом приніс відвідувач');f.write_text(t,encoding='utf-8')
d=json.loads(o.read_text(encoding='utf-8'));d['scenes'][0]['knowledge']+=' Технічний витяг тут — локальний підсумок операції, не первинний зовнішній журнал резерву CH35.';o.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
lf=p/'revision-log.json';log=json.loads(lf.read_text(encoding='utf-8'));log['items'].append(dict(chapter=31,reason='Root caught request/offer reversal against CH23; retain old post as request for hardware',before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),history=str(h.relative_to(p))));lf.write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
