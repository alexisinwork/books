"""Freeze exact reviewed chapters for a block audit or the final volume audit.

This verifies bytes and coverage, not literary quality or author acceptance.
"""
from pathlib import Path
import argparse, hashlib, json, re

p=argparse.ArgumentParser()
p.add_argument('--manifest',type=Path,required=True)
p.add_argument('--route',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--scope',choices=['block','volume'],required=True)
p.add_argument('--through',type=int,required=True)
a=p.parse_args()
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
manifest=read(a.manifest);route=read(a.route)
# Manifest lives at book/production/date/working-volume.json.
book=a.manifest.resolve().parents[2]
chapters=manifest['chapters'];assert [c['chapter'] for c in chapters]==list(range(1,len(chapters)+1))
assert 1<=a.through<=len(chapters),'Cannot assemble unwritten chapters'
if a.scope=='volume':
 expected=[c['chapter'] for c in route['chapters']]
 assert expected==list(range(1,a.through+1)), 'Full-volume scope requires all current route chapters'
 assert len(chapters)==a.through, 'Do not silently omit registered chapters'
parts=[];mapping=[];global_anchor=0;byte_offset=0
for c in chapters[:a.through]:
 source=(book/c['source']).resolve();source.relative_to(book)
 raw=source.read_bytes();assert sha(raw)==c['sha256'],f'Changed source: {source}'
 text=raw.decode('utf-8');assert '\r' not in text and not text.startswith('\ufeff'),'Expected frozen UTF-8 LF source'
 assert text.startswith(f"# Розділ {c['chapter']}\n"), 'Unexpected chapter title'
 assert raw.endswith(b'\n') and not raw.endswith(b'\n\n'),'Expected one final LF'
 # Retain every source byte; add only one LF separator between chapters.
 if parts:parts.append(b'\n');byte_offset+=1
 chapter_start=byte_offset;parts.append(raw);byte_offset+=len(raw)
 blocks=re.split(r'\n\s*\n',text.strip());anchors=[]
 for i,block in enumerate(blocks,1):
  global_anchor+=1;anchors.append({'global':f'P{global_anchor:05d}','chapter_anchor':f'P{i:04d}','text_sha256':sha(block.encode('utf-8'))})
 mapping.append({'chapter':c['chapter'],'source':c['source'],'source_sha256':c['sha256'],'source_bytes':len(raw),'manuscript_byte_start':chapter_start,'manuscript_byte_end_exclusive':byte_offset,'paragraphs':anchors})
combined=b''.join(parts)
for c in mapping:assert sha(combined[c['manuscript_byte_start']:c['manuscript_byte_end_exclusive']])==c['source_sha256']
assert not a.out.exists(),'Use a fresh immutable assembly directory'
a.out.mkdir(parents=True)
(a.out/'manuscript.md').write_bytes(combined)
record={'scope':a.scope,'status':'frozen_audit_source_not_master','global_audit':'not_run','through_chapter':a.through,'manuscript_sha256':sha(combined),'bytes':len(combined),'paragraphs':global_anchor,'input_manifest_sha256':sha(a.manifest.read_bytes()),'route_sha256':sha(a.route.read_bytes()),'assembly_rule':'Exact source bytes, in order, with one added LF separator between chapters','chapters':mapping}
(a.out/'assembly.json').write_bytes((json.dumps(record,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({k:v for k,v in record.items() if k!='chapters'},ensure_ascii=False))
