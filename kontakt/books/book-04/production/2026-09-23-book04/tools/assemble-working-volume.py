"""Assemble a complete phase without silently accepting missing chapters."""
from pathlib import Path
import argparse,hashlib,json,re
p=argparse.ArgumentParser()
p.add_argument('--chapters',type=Path,required=True)
p.add_argument('--expected',type=int,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--phase',choices=['astra_rough','terra_full','terra_revised'],required=True)
a=p.parse_args()
files=sorted(a.chapters.glob('chapter-*.md'))
assert len(files)==a.expected,(len(files),a.expected)
chunks=[];items=[];offset=0
for n,f in enumerate(files,1):
    assert f.name==f'chapter-{n:02d}.md'
    raw=f.read_bytes();text=raw.decode('utf-8')
    assert re.match(rf'^# Розділ {n}\n',text),'Unexpected chapter heading '+str(f)
    assert len(re.findall(r'(?m)^# Розділ \d+',text))==1
    assert '\ufffd' not in text and '????' not in text
    separator=b'' if n==1 or chunks[-1].endswith(b'\n\n') else b'\n' if chunks[-1].endswith(b'\n') else b'\n\n'
    chunks.append(separator+raw)
    items.append({'chapter':n,'source':str(f.resolve()),'source_sha256':hashlib.sha256(raw).hexdigest(),
                  'source_bytes':len(raw),'separator_before_bytes':len(separator),
                  'manuscript_byte_start':offset+len(separator),'manuscript_byte_end_exclusive':offset+len(separator)+len(raw)})
    offset+=len(separator)+len(raw)
volume=b''.join(chunks)
a.out.mkdir(parents=True,exist_ok=True)
target=a.out/'manuscript.md'
assert not target.exists(),'Freeze each assembly; use a new directory for another source'
target.write_bytes(volume)
manifest={'scope':'volume','through_chapter':a.expected,'phase':a.phase,'status':'complete_phase_source_not_master',
          'manuscript_sha256':hashlib.sha256(volume).hexdigest(),'bytes':len(volume),
          'paragraphs':len(volume.decode('utf-8').rstrip('\n').split('\n\n')),'chapters':items,
          'literary_verification':'Not established by assembly; see source-bound reports.'}
(a.out/'assembly.json').write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({k:manifest[k] for k in ['phase','through_chapter','manuscript_sha256','bytes','paragraphs']}))
