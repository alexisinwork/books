"""Validate and freeze only this rough package; coordinator gate is separate."""
from pathlib import Path
import hashlib,json,subprocess,sys
P=Path(__file__).resolve().parent;RUN=P.parent;ROOT=P.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def rel(p):return p.relative_to(ROOT).as_posix()
cards=rd(RUN/'structure-v1/chapter-scene-cards.json');state=rd(P/'observed-state.json');a=rd(P/'assembled/assembly.json');volume=P/'assembled/manuscript.md';raw=volume.read_bytes()
assert sha(volume)=='eabf64d0421e741d67ad770f5c831e98f55ff1a30e87c76b28fba43f3390a579'==a['manuscript_sha256']
assert state['source_cards_sha256']==sha(RUN/'structure-v1/chapter-scene-cards.json')
assert len(state['chapters'])==32 and len(cards['scenes'])==41
ids=[];quotes=0;reading=[]
questions=rd(RUN/'structure-v1/decisions-and-questions.json')['questions'];validids={q['id'] for q in questions}
for n,(ch,ass) in enumerate(zip(state['chapters'],a['chapters'],strict=True),1):
 f=P/f'chapters/chapter-{n:02}.md';b=f.read_bytes();t=b.decode('utf-8')
 assert ch['chapter']==n and ch['sha256']==sha(f)==ass['source_sha256']
 assert raw[ass['manuscript_byte_start']:ass['manuscript_byte_end_exclusive']]==b
 assert b'\r' not in b and t.startswith(f'# Розділ {n}\n\n') and '\n\n\n' not in t
 assert '\ufffd' not in t and '????' not in t
 for s in ch['observed']['scenes']:
  ids.append(s['id']);assert s['time_basis']
  assert len(s['quotes'])>=2
  for q in s['quotes']:assert q in t;(None);quotes+=1
  assert set(s['open_dependencies'])<=validids
 reading.append(dict(chapter=n,path=rel(f),sha256=sha(f),scope='Complete prose read during direct Astra composition and local scene review; whole-book final causal/state comparison',additional_final_file_reread=n<=6,scene_ids=[s['id'] for s in ch['observed']['scenes']],selfcheck=ch['selfcheck']))
assert ids==[s['id'] for s in cards['scenes']]
rootread={}
for p in sorted((RUN/'root-rough-reading').glob('*.json')):
 for x in rd(p)['items']:assert x['chapter'] not in rootread;rootread[x['chapter']]=x['sha256']
assert len(rootread)==32
for ch in state['chapters']:assert rootread[ch['chapter']]==ch['sha256']
sources=[RUN/'root-structure-gate.json',RUN/'structure-v1/chapter-scene-cards.json',RUN/'structure-v1/full-outline.md',RUN/'structure-v1/carry-in-source-lock.json',RUN/'structure-v1/source-inventory.json',RUN/'structure-v1/decisions-and-questions.json',RUN/'structure-v1/manifest.json',ROOT/'kontakt/series/WORKFLOW-2026-09-23-BOOK03.md',ROOT/'kontakt/books/book-02/production/2026-09-23-book02/terra-final-v3/assembled/manuscript.md',ROOT/'kontakt/books/book-01/revisions/2026-09-23-author-revision-v4/manuscript.md']
assert sha(sources[-2])=='07a68dad4276cd81e98f077796d17f56f3b21cdcef64f8231a71524d054a78f4'
assert sha(sources[-1])=='32d70ac6e9dc3c523ee7a8fcd38db28f26aa77d5cd1908fa19f8eeb51f61b89f'
save(P/'source-manifest.json',dict(status='source_bound_working_continuation_not_canon_promotion',sources=[dict(path=rel(p),sha256=sha(p)) for p in sources],reading_scope='Architecture/source inventory carries earlier actual source readings; current final check reread rough1–6 and all rough composition/state records, not a new full Book1/2 reread.'))
save(P/'reading-coverage.json',dict(status='complete_self_review_not_independent',source_sha256=sha(volume),chapters=reading,limits=['No fresh isolated second full-volume diagnosis claimed.','Root separate complete32 reading records checked by hash, not substituted for prose quality.']))
u3=next(x for x in questions if x['id']=='U03')
save(P/'unknowns-observed.json',dict(status='working_rough_only',inherited_questions_preserved=True,items=[dict(id='U03',entry_status='unresolved',resolution_status='resolved',resolution_scope='Limited working-prose explanation of candidate capacity only, not total private-input provenance or canonical promotion',chapter=4,source_sha256=state['chapters'][3]['sha256'],quotes=['Кілька первинних кандидатних резервів підтверджено. Невикористані знято.','Тут резерв зовнішньої місткості. Він не надає місцевого допуску на зміну режиму.'],remaining_limit='Unknown complete private inputs and all other interventions B03-U03 remain unresolved')]+[dict(q,observed_status='unresolved_retained') for q in questions if q['id']!='U03']))
state['status']='complete_frozen_astra_rough_not_master';save(P/'observed-state.json',state)
progress=rd(P/'progress.json');progress.update(status='complete_frozen',source_sha256=sha(volume),assembly='assembled/manuscript.md',self_review='self-review.md',handoff='handoff-for-terra.md');save(P/'progress.json',progress)
save(P/'validation.json',dict(status='passed',source_sha256=sha(volume),chapters=32,scenes=len(ids),literal_quotes=quotes,words=sum(x['word_count'] for x in state['chapters']),blocks=a['paragraphs'],checks=['UTF8 LF exact32headings','Ordered32 byte-identical assembly','All41 source scene IDs in order','All82 literal quotes chapter-scoped','All state hashes current','Dependency IDs exist and unrelated final shorthand corrected','All32 coordinator reading hashes unchanged','Book1v4/Book2final source hashes verified'],limits=['Technical checks do not establish literary quality','Concrete language/physical/calendar corrections remain assigned to Terra','Working proposals are not individual author votes']))
excluded={'manifest.json','desktop-copy-manifest.json'}
files=[dict(path=rel(p),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(P.rglob('*')) if p.is_file() and p.name not in excluded and '__pycache__' not in p.parts]
save(P/'manifest.json',dict(status='frozen_complete_astra_rough_not_master',source_sha256=sha(volume),chapters=32,scenes=41,files=files,exclusions=['This manifest excludes itself','desktop-copy-manifest.json is derived mirror proof outside frozen inventory to avoid recursive hashes'],no_prose_mutation_during_finalization=True))
subprocess.run([sys.executable,'-X','utf8',str(P/'manage.py'),'mirror'],check=True)
mirror=rd(P/'desktop-copy-manifest.json');bundle=Path(mirror['bundle'])
for p in P.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts:assert sha(p)==sha(bundle/p.relative_to(ROOT))
for x in rd(P/'manifest.json')['files']:assert sha(ROOT/x['path'])==x['sha256']
print(json.dumps(dict(status='frozen',source_sha256=sha(volume),manifest_sha256=sha(P/'manifest.json'),files=len(files),chapters=32,scenes=41,quotes=quotes,mirror_verified=True)))
