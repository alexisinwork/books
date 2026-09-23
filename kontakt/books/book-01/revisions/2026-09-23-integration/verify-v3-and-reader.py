from pathlib import Path
import json,re,hashlib,shutil
r=Path.cwd();b=r/'kontakt/books/book-01/revisions';base=b/'2026-09-23-author-revision-v3'
source=base/'manuscript.md';raw=source.read_bytes();h=hashlib.sha256(raw).hexdigest()
assert h=='11a898f30d29ef3e8fcd0284cc77851861605e3c660c0a21b298a5c68010b5dc'
package=json.loads((b/'2026-09-23-integration/selected-historical-package.json').read_text(encoding='utf-8-sig'))
before=(b/'2026-09-23-author-revision-v2/manuscript.md').read_text(encoding='utf-8')
matches=list(re.finditer(r'(?m)^# .+? (\d+)\n',before))
parts={int(m.group(1)):before[m.start():matches[i+1].start() if i+1<len(matches) else len(before)] for i,m in enumerate(matches)}
applied=[]
for x in package['items']+package['root_additions']:
    if not x.get('applied_occurrences',0):continue
    ch=x['chapter'];old=x['exact_before'];new=x['exact_after'];count=parts[ch].count(old)
    assert count==x['applied_occurrences'],(x['id'],count,x['applied_occurrences'])
    parts[ch]=parts[ch].replace(old,new);applied.append(x['id'])
assert ''.join(parts.values()).encode('utf-8')==raw
def save(p,d):p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
save(b/'2026-09-23-integration/v3-root-replay.json',{'source_sha256':package['base']['sha256'],
    'output_sha256':h,'status':'exact_replay_passed','applied_changes':applied,
    'literary_quality':'not established by replay'})
check=base/'reader/render/render-check.json';d=json.loads(check.read_text(encoding='utf-8'))
assert d['pages']==96 and d['text_matches_docx_ignoring_layout_whitespace']
assert all(not x['blank'] and not x['out_of_bounds'] for x in d['page_checks'])
d['visual_review']={'status':'passed','reviewer':'root','scope':'All16contact sheets covering pages1–96 visually inspected; headings, paragraph flow, indentation, page bounds; no clipping/overlap/blank pages seen.',
                    'limitation':'Chromium docx-preview layout, not native Word; contact-sheet layout inspection is not prose reading.'}
save(check,d)
p=base/'reader/docx-check.json';d=json.loads(p.read_text(encoding='utf-8'))
d['render']={'status':'passed_preview_extraction_and_all96page_layout','report':'render/render-check.json',
             'report_sha256':hashlib.sha256(check.read_bytes()).hexdigest()};save(p,d)
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),b/'2026-09-23-integration/v3-root-replay.json',*base.rglob('*')]:
    if f.is_file() and '__pycache__' not in f.parts:
        dest=desktop/f.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
        assert dest.read_bytes()==f.read_bytes()
for directory in [Path('C:/Users/alexi/OneDrive/Desktop'),Path('C:/Users/alexi/Desktop')]:
    directory.mkdir(parents=True,exist_ok=True)
    for f in (base/'reader').glob('*.docx'):
        dest=directory/f.name
        assert not dest.exists() or dest.read_bytes()==f.read_bytes(),'Do not overwrite author-edited reader copy'
        shutil.copy2(f,dest);assert dest.read_bytes()==f.read_bytes()
print(json.dumps({'replay_changes':len(applied),'source_sha256':h,'reader_pages':96,'desktop_copies':'verified'}))
