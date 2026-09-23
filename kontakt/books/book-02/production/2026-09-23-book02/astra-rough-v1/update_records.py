from pathlib import Path
import hashlib,json,re,shutil
P=Path(__file__).resolve().parent
ROOT=P.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cards=P.parent/'structure-v2/chapter-scene-cards.json'
assert sha(cards)=='59ae0cfc999909ba81af42f59d47c4140942c7b454eb18591aaeba0074ee66f6'
records=[];proposals=[]
for f in sorted((P/'chapters').glob('chapter-*.md')):
    n=int(f.stem.split('-')[1]);t=f.read_text(encoding='utf-8');assert t.startswith(f'# Розділ {n}\n')
    o=P/'observations'/f'chapter-{n:02d}.json';d=json.loads(o.read_text(encoding='utf-8'))
    for s in d['scenes']:
        s.setdefault('time_basis','planned placement; exact scene interval not stated in prose; explicit clock facts only where quoted separately')
        for q in s['quotes']:assert q in t,(n,q)
    o.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    records.append(dict(chapter=n,path=str(f.relative_to(ROOT)).replace('\\','/'),sha256=sha(f),words=len(re.findall(r"[\w’'-]+",t)),observed=d))
    proposals.extend(dict(chapter=n,detail=x,status='working_implementation_not_author_statement') for x in d.get('working_details',[]))
assert [r['chapter'] for r in records]==list(range(1,len(records)+1))
save('observed-state.json',dict(status='observed_in_rough_only',source_cards_sha256=sha(cards),chapters=records))
save('proposals.json',dict(status='working_details_not_author_canon',items=proposals,unresolved_inherited='structure-v2/decisions-and-questions.json U01–U05 remain unresolved; no silent answers.'))
save('progress.json',dict(phase='astra_rough',chapters_done=len(records),chapters_expected=36,words=sum(r['words'] for r in records),last_chapter=records[-1]['chapter'] if records else None,status='in_progress' if len(records)<36 else 'complete_assembled_handoff_ready_not_master' if (P/'completion.json').exists() else 'all_chapters_written_pending_assembly_and_handoff',prose_review='own drafting/context review only; external ensemble not_run'))
files=[p for p in P.rglob('*') if p.is_file() and p.name not in ['manifest.json','desktop-copy-manifest.json']]
save('manifest.json',dict(phase='astra_rough',files=[dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=sha(p)) for p in sorted(files)]))
bundle=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23');dst=bundle/P.relative_to(ROOT)
copied=[]
for f in P.rglob('*'):
    if f.is_file() and f.name!='desktop-copy-manifest.json':
        target=dst/f.relative_to(P);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);assert sha(f)==sha(target)
        copied.append(dict(path=str(f.relative_to(ROOT)).replace('\\','/'),sha256=sha(f),copy_verified=True))
save('desktop-copy-manifest.json',dict(bundle=str(bundle),files=copied));shutil.copy2(P/'desktop-copy-manifest.json',dst/'desktop-copy-manifest.json')
print(json.dumps(dict(chapters=len(records),words=sum(r['words'] for r in records),last_sha256=records[-1]['sha256'] if records else None,mirrored=True)))
