from pathlib import Path
import hashlib,json,re
p=Path(__file__).resolve().parent
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def read(f):return json.loads(f.read_text(encoding='utf-8'))
def save(n,x):(p/n).write_bytes((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
a=read(p/'assembled/assembly.json'); raw=(p/'assembled/manuscript.md').read_bytes();assert sha(p/'assembled/manuscript.md')==a['manuscript_sha256']
cards=read(p.parent/'structure-v2/chapter-scene-cards.json');expected={s['id'] for s in cards['scenes']};seen=[];chapters=[]
for r in a['chapters']:
 n=r['chapter'];f=p/'chapters'/f'chapter-{n:02}.md';b=f.read_bytes();t=b.decode('utf-8');o=read(p/'observations'/f'chapter-{n:02}.json')
 assert b'\r' not in b and '\n\n\n' not in t and t.startswith(f'# Розділ {n}\n')
 assert sha(f)==r['source_sha256'] and raw[r['manuscript_byte_start']:r['manuscript_byte_end_exclusive']]==b
 assert '\ufffd' not in t and '????' not in t
 for s in o['scenes']:
  seen.append(s['id'])
  for q in s['quotes']:assert q in t,(n,q)
 chapters.append(dict(chapter=n,sha256=sha(f),words=len(re.findall(r"[\w’'-]+",t)),scene_ids=[s['id'] for s in o['scenes']],review_basis='full individual chapter read during own drafting; final boundary reread; not independent cold reading',finding=o['self_review'],evidence=[q for s in o['scenes'] for q in s['quotes']]))
assert len(seen)==len(set(seen))==41 and set(seen)==expected
t=raw.decode('utf-8');assert t.count('**Журнал зовнішнього транспорту. Тижневий витяг.**')==1
assert '# Розділ 17\n\n> **Журнал' in t
save('mechanical-checks.json',dict(source_sha256=sha(p/'assembled/manuscript.md'),chapters=36,scene_records=41,exact_header_sequence=True,utf8_lf=True,single_blank_block_separators=True,assembled_chapter_byte_slices_identical=True,all_observed_quotes_verified=True,doc01_present_once_in_ch17_before_scene=True,frozen_cards_sha256=sha(p.parent/'structure-v2/chapter-scene-cards.json'),status='pass',limits='Mechanical success does not establish literary quality or independent full reading.'))
save('self-review.json',dict(source_sha256=sha(p/'assembled/manuscript.md'),scope='All36 chapters individually read while composing and source-card/state checked, all chapter boundaries reread after final normalization; targeted cross-check of hook CH14/17/18/35/36. No new continuous cold reading claimed.',chapters=chapters,limits=['This is a complete rough phase, not final-length Terra prose.','Many chapters are concise single-scene units; expand embodied action/voice in Terra without filler or new plot.','Local language issues listed separately remain for Terra.','No external literary ensemble run in this rough phase.','Time intervals in scene metadata are planned placement unless quoted explicitly; not all clocks stated in prose.','U01–U05 remain unresolved and nonblocking under source limits.']))
save('completion.json',dict(phase='astra_rough',status='complete_36_chapters_assembled_handoff_ready_not_master',chapters=36,scenes=41,words=sum(c['words'] for c in chapters),paragraphs=a['paragraphs'],manuscript_sha256=a['manuscript_sha256'],assembly_manifest_sha256=sha(p/'assembled/assembly.json'),source_cards_sha256=sha(p.parent/'structure-v2/chapter-scene-cards.json'),book1_carry_sha256='32d70ac6e9dc3c523ee7a8fcd38db28f26aa77d5cd1908fa19f8eeb51f61b89f',next_phase='Terra writes full prose for all36 chapters, then complete-volume literary ensemble; coordinator controls launch',author_canon_promoted=False,external_ensemble_run=False))
print(json.dumps(dict(chapters=36,scenes=41,words=sum(c['words'] for c in chapters),sha256=a['manuscript_sha256'])))
