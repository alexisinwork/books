"""Verify an entire rough phase after actual coordinator reading, never substitute for it."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[6]
run=Path(__file__).resolve().parent.parent
rough=run/'astra-rough-v1'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cards_path=run/'structure-v1/chapter-scene-cards.json'
cards=read(cards_path); count=max(s['chapter'] for s in cards['scenes'])
out=run/'rough-handoff-verification.json';assert not out.exists()
sources=sorted((rough/'chapters').glob('chapter-*.md'))
assert [p.name for p in sources]==[f'chapter-{n:02d}.md' for n in range(1,count+1)]
coverage={};records=sorted((run/'root-rough-reading').glob('*.json'))
for p in records:
    for item in read(p)['items']:
        n=item['chapter'];assert n not in coverage
        coverage[n]=item['sha256']
assert sorted(coverage)==list(range(1,count+1)), 'Actual full reading records missing'
for n,p in enumerate(sources,1):assert sha(p)==coverage[n],('Changed since reading',n)
assembly=read(rough/'assembled/assembly.json');source=rough/'assembled/manuscript.md';raw=source.read_bytes()
assert sha(source)==assembly['manuscript_sha256']
assert assembly['phase']=='astra_rough' and assembly['through_chapter']==count
for entry,p in zip(assembly['chapters'],sources,strict=True):
    assert entry['source_sha256']==sha(p)
    assert raw[entry['manuscript_byte_start']:entry['manuscript_byte_end_exclusive']]==p.read_bytes()
assert len(raw.decode('utf-8').rstrip('\n').split('\n\n'))==assembly['paragraphs']
observed=read(rough/'observed-state.json');assert len(observed['chapters'])==count
assert observed['source_cards_sha256']==sha(cards_path)
ids=[];quotes=0
for entry,p in zip(observed['chapters'],sources,strict=True):
    assert entry['sha256']==sha(p);text=p.read_text(encoding='utf-8')
    for scene in entry['observed']['scenes']:
        ids.append(scene['id']);assert scene.get('time_basis')
        assert len(scene['quotes'])>=2
        for quote in scene['quotes']:
            assert quote in text,(scene['id'],quote);quotes+=1
assert ids==[s['id'] for s in cards['scenes']]
for entry in read(rough/'manifest.json')['files']:
    assert sha(root/entry['path'])==entry['sha256'],('Stale manifest',entry['path'])
report={'status':'passed','source':source.relative_to(root).as_posix(),'source_sha256':sha(source),
 'chapters':count,'scenes':len(ids),'paragraphs':assembly['paragraphs'],'matched_quotes':quotes,
 'reading_records':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in records],
 'checks':['Complete ordered byte-exact assembly','Current hashes match all actual reading records','Every planned scene present in order','Every observed quotation literal','Frozen rough manifest matches'],
 'limits':['Mechanical verification cannot prove literary quality.','Rough prose is not the Terra full text or an independent editorial review.','Working decisions do not imply author canonical approval.']}
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for p in [out,Path(__file__).resolve()]:
    d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
print(json.dumps(report,ensure_ascii=False))
