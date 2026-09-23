from pathlib import Path
import json,hashlib,shutil
p=Path(__file__).resolve().parent
log=json.loads((p/'revision-log.json').read_text(encoding='utf-8'))
changes={30:[('Завтра о дванадцятій. Зводимо підсумок','Сьогодні о дванадцятій. Зводимо підсумок'),('Прийдеш?','Прийдете?'),('чи бачив я оплески','чи бачив я оплески')],31:[('Ти вже пішов посеред включення.','Ви вже пішли посеред включення.'),('просити тебе між двома чужими справами','просити вас між двома чужими справами')]}
for n,repls in changes.items():
 f=p/'chapters'/f'chapter-{n:02}.md';h=p/'history'/f'chapter-{n:02}-before-calendar-register-clarity';h.mkdir(parents=True,exist_ok=True)
 if not (h/f.name).exists():shutil.copy2(f,h/f.name)
 old=(h/f.name).read_bytes();t=old.decode('utf-8')
 o=p/'observations'/f'chapter-{n:02}.json'
 if not (h/o.name).exists():shutil.copy2(o,h/o.name)
 for a,b in repls:
  assert a in t,a
  t=t.replace(a,b)
 f.write_text(t,encoding='utf-8')
 if n==30:
  d=json.loads(o.read_text(encoding='utf-8'));d['scenes'][0]['knowledge']=d['scenes'][0]['knowledge'].replace('завтра12','сьогодні (D8)12');o.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 next(v for v in log.values() if isinstance(v,list)).append(dict(chapter=n,reason='Calendar invitation after midnight means same Tuesday noon; retain established formal Vector/Dal address',before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),history=str(h.relative_to(p))))
(p/'revision-log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
