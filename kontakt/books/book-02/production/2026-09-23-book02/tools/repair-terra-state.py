"""Document source-bound metadata repairs without changing native prose or raw responses."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, difflib
p=argparse.ArgumentParser()
p.add_argument('--run',type=Path,required=True)
p.add_argument('--apply',action='store_true')
p.add_argument('--quote-map',type=Path,help='Explicit coordinator-selected literal replacements as a JSON object')
a=p.parse_args()
raw_path=a.run/'RESPONSE.md'
raw=raw_path.read_text(encoding='utf-8')
prose, tail=raw.split('<STATE_JSON>')
state_text=tail.split('</STATE_JSON>')[0].strip()
repairs=[]
try:state=json.loads(state_text)
except json.JSONDecodeError:
    count=state_text.count('}]}}}')
    assert count>0, 'Unknown JSON problem; inspect manually.'
    state=json.loads(state_text.replace('}]}}}','}]}}'))
    repairs.append({'kind':'syntax','before':'}]}}}','after':'}]}}','occurrences':count,
                    'reason':'Extraneous chapter-object closing brace. Original response unchanged.'})
mapping=json.loads(a.quote_map.read_text(encoding='utf-8')) if a.quote_map else {}
matches=list(re.finditer(r'(?m)^# Розділ (\d+)\s*$',prose))
texts={int(m.group(1)):prose[m.start():matches[i+1].start() if i+1<len(matches) else len(prose)] for i,m in enumerate(matches)}
unresolved=[]
for chapter in state['chapters']:
    body=texts[chapter['chapter']]
    for scene in chapter['observed']['scenes']:
        for i,before in enumerate(scene['quotes']):
            after=mapping.get(before,before.strip(chr(34)))
            if after not in body and after.endswith('.') and after[:-1] in body:
                after=after[:-1]
            if after not in body:
                unresolved.append({'scene':scene['id'],'quote':before,
                                   'candidate_context':difflib.get_close_matches(after,body.split('\n\n'),n=1,cutoff=.15)})
            elif after!=before:
                scene['quotes'][i]=after
                repairs.append({'kind':'quote','scene':scene['id'],'before':before,'after':after,
                                'reason':'Coordinator documented literal source excerpt; no prose change.'})
if unresolved:
    print(json.dumps({'status':'manual_quote_selection_required','unresolved':unresolved},ensure_ascii=False,indent=2))
    raise SystemExit(2)
if not a.apply:
    print(json.dumps({'status':'ready_for_explicit_metadata_repair','repairs':repairs},ensure_ascii=False,indent=2))
    raise SystemExit(0)
out=a.run/'STATE-REPAIRED.json';log=a.run/'METADATA-REPAIR.json'
assert not out.exists() and not log.exists()
out.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
log.write_text(json.dumps({'source_response_sha256':sha(raw_path),'scope':'Metadata only; raw response and prose unchanged',
                          'repairs':repairs,'output_sha256':sha(out)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
root=Path(__file__).resolve().parents[6]
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),out.resolve(),log.resolve(),*([a.quote_map.resolve()] if a.quote_map else [])]:
    q=desktop/f.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,q)
print(json.dumps({'status':'metadata_repaired_prose_unchanged','repairs':len(repairs)}))
