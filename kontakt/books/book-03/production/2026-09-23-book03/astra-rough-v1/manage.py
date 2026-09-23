from pathlib import Path
import json,hashlib,re,shutil,sys
P=Path(__file__).resolve().parent;R=P.parent;ROOT=P.parents[5];S=R/'structure-v1/chapter-scene-cards.json';CS='ce1337fbc75adcc9b8a0893eb07aaf73fb353757a19d7df30967baca05a5613a'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
assert sha(S)==CS;cards=rd(S)
def mirror():
 bundle=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23');entries=[]
 for f in sorted(P.rglob('*')):
  if f.is_file() and f.name!='desktop-copy-manifest.json' and '__pycache__' not in f.parts:
   d=bundle/f.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d);entries.append(dict(path=str(f.relative_to(ROOT)).replace('\\','/'),sha256=sha(f)))
 out=P/'desktop-copy-manifest.json';save(out,dict(bundle=str(bundle),verified=True,files=entries));shutil.copy2(out,bundle/out.relative_to(ROOT))
cmd=sys.argv[1]
if cmd=='prepare':
 n=int(sys.argv[2]);idx=int(sys.argv[3]) if len(sys.argv)>3 else None
 selected=[s for s in cards['scenes'] if s['chapter']==n and (idx is None or s['id'].endswith(f'SC{idx:02}'))]
 print(json.dumps(dict(source_cards_sha256=CS,cards=selected),ensure_ascii=False,indent=2))
 if (P/'observed-state.json').exists():
  state=rd(P/'observed-state.json');print('CURRENT OBSERVED LAST CHAPTER');print(json.dumps(state['chapters'][-1],ensure_ascii=False,indent=2))
 prior=P/f'chapters/chapter-{n-1:02}.md'
 if prior.exists():print('PREVIOUS CHAPTER END\n'+'\n\n'.join(prior.read_text(encoding='utf-8').strip().split('\n\n')[-8:]))
 current=P/f'chapters/chapter-{n:02}.md'
 if current.exists():print('CURRENT CHAPTER WRITTEN END\n'+'\n\n'.join(current.read_text(encoding='utf-8').strip().split('\n\n')[-8:]))
elif cmd=='register':
 n=int(sys.argv[2]);f=P/f'chapters/chapter-{n:02}.md';text=f.read_text(encoding='utf-8');raw=f.read_bytes();assert b'\r' not in raw and text.startswith(f'# Розділ {n}\n\n');assert '\n\n\n' not in text
 note=rd(P/f'notes/chapter-{n:02}.json');expected=[s['id'] for s in cards['scenes'] if s['chapter']==n];assert [s['id'] for s in note['scenes']]==expected
 for s in note['scenes']:
  assert len(s['quotes'])>=2
  for q in s['quotes']:assert q in text,(n,q)
  assert s.get('time_basis') and all(k in s for k in ['events','knowledge','resources','open_dependencies'])
 state=rd(P/'observed-state.json') if (P/'observed-state.json').exists() else dict(status='in_progress_actual_rough',source_cards_sha256=CS,chapters=[])
 state['chapters']=[x for x in state['chapters'] if x['chapter']!=n]+[dict(chapter=n,sha256=sha(f),path=str(f.relative_to(ROOT)).replace('\\','/'),observed=dict(scenes=note['scenes']),word_count=len(text.split()),selfcheck=note.get('selfcheck','Local drafting check; no independentreview'))]
 state['chapters'].sort(key=lambda x:x['chapter']);save(P/'observed-state.json',state)
 notes=[rd(p) for p in sorted((P/'notes').glob('chapter-*.json'))]
 save(P/'proposals.json',dict(status='working_implementation_not_author_canon',items=[dict(chapter=x['chapter'],details=x.get('proposals',[]),status='proposed_in_actual_rough') for x in notes]))
 save(P/'continuity.json',dict(source_cards_sha256=CS,chapters=[dict(chapter=x['chapter'],notes=x.get('continuity',[])) for x in notes],unknowns=rd(R/'structure-v1/decisions-and-questions.json')['questions'],unknown_status_rule='Inherited unresolved entries retained; actual scene evidence of plannedU03answer recorded in chapterknowledge, not silently rewritten here.'))
 save(P/'progress.json',dict(phase='astra_rough',status='in_progress' if len(state['chapters'])<32 else 'all_chapters_written_pending_assembly_selfreview',completed_chapters=[x['chapter'] for x in state['chapters']],completed_scenes=sum(len(x['observed']['scenes']) for x in state['chapters']),expected_chapters=32,expected_scenes=41,source_cards_sha256=CS,word_count=sum(x['word_count'] for x in state['chapters'])))
 mirror();print(json.dumps(dict(chapter=n,sha256=sha(f),words=len(text.split()),registered_scenes=expected),ensure_ascii=False))
elif cmd=='snapshot':
 n=int(sys.argv[2]);f=P/f'chapters/chapter-{n:02}.md';dest=P/f'history/chapter-{n:02}/{sha(f)}.md';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
 if (P/f'notes/chapter-{n:02}.json').exists():shutil.copy2(P/f'notes/chapter-{n:02}.json',dest.with_suffix('.json'))
 log=rd(P/'revision-log.json') if (P/'revision-log.json').exists() else dict(items=[]);log['items'].append(dict(chapter=n,before_sha256=sha(f),preserved_path=str(dest.relative_to(ROOT)).replace('\\','/'),reason=' '.join(sys.argv[3:]),status='predecessor_preserved_before_local_edit'));save(P/'revision-log.json',log);mirror();print(str(dest))
elif cmd=='mirror':mirror()
