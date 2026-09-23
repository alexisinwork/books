"""Import completed native Terra prose verbatim after validating chapter/state coverage."""
from pathlib import Path
import argparse, hashlib, json, re, shutil
p=argparse.ArgumentParser()
p.add_argument('--first',type=int,required=True)
p.add_argument('--last',type=int,required=True)
p.add_argument('--state-override',type=Path,help='Explicitly documented mechanical metadata repair; original response remains immutable.')
a=p.parse_args()
root=Path(__file__).resolve().parents[6]
run=Path(__file__).resolve().parent.parent
phase=run/'terra-full-v2'
name=f'chapters-{a.first:02d}-{a.last:02d}'
execution=phase/'runs'/name
def read(f):return json.loads(f.read_text(encoding='utf-8'))
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
inv=read(execution/'invocation.json')
assert inv['exit_code']==0 and inv['status']=='returned_pending_manual_validation'
assert set(inv['item_types'])<= {'agent_message','reasoning'}, inv['item_types']
response=execution/'RESPONSE.md'
assert sha(response)==inv['response_sha256']
text=response.read_text(encoding='utf-8')
assert text.count('<STATE_JSON>')==1 and text.count('</STATE_JSON>')==1
prose, tail=text.split('<STATE_JSON>')
json_text, after=tail.split('</STATE_JSON>')
assert not after.strip()
state=read(a.state_override) if a.state_override else json.loads(json_text.strip())
matches=list(re.finditer(r'(?m)^# Розділ (\d+)\s*$',prose))
assert [int(m.group(1)) for m in matches]==list(range(a.first,a.last+1))
assert not prose[:matches[0].start()].strip()
assert [x['chapter'] for x in state['chapters']]==list(range(a.first,a.last+1))
cards_path=run/'structure-v2/chapter-scene-cards.json'
cards=read(cards_path)
expected=[s['id'] for s in cards['scenes'] if a.first<=s['chapter']<=a.last]
actual=[s['id'] for c in state['chapters'] for s in c['observed']['scenes']]
assert actual==expected,(actual,expected)
payload=[]
for index,(match,item) in enumerate(zip(matches,state['chapters'],strict=True)):
    end=matches[index+1].start() if index+1<len(matches) else len(prose)
    chapter=prose[match.start():end].strip()+'\n'
    assert '\ufffd' not in chapter and '????' not in chapter
    for scene in item['observed']['scenes']:
        assert scene.get('time_basis')
        assert len(scene['quotes'])>=2
        for quote in scene['quotes']:
            assert quote in chapter,(scene['id'],quote)
    dest=phase/'chapters'/f'chapter-{item["chapter"]:02d}.md'
    assert not dest.exists(),('Do not overwrite a prior chapter',dest)
    payload.append((dest,chapter,item))
state_dest=phase/'states'/(name+'.json')
assert not state_dest.exists()
for dest,chapter,item in payload:
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(chapter,encoding='utf-8',newline='\n')
    item.update(path=dest.relative_to(root).as_posix(),sha256=sha(dest),words=len(chapter.split()))
state.update(source_response_sha256=sha(response),execution=execution.relative_to(root).as_posix(),
             model_requested='gpt-5.6-terra',actual_backend='not independently attested',
             status='imported_source_and_quotes_verified_literary_quality_pending')
state_dest.parent.mkdir(parents=True,exist_ok=True)
state_dest.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
states=[read(f) for f in sorted((phase/'states').glob('chapters-*.json'))]
chapters=[c for s in states for c in s['chapters']]
assert [c['chapter'] for c in chapters]==list(range(1,a.last+1))
outputs={
    'observed-state.json':{'status':'observed_working_text_not_canon','source_cards_sha256':sha(cards_path),'chapters':chapters},
    'proposals.json':{'status':'working_implementation_not_author_canon','items':[v for s in states for v in s.get('new_proposals',[])]},
    'progress.json':{'phase':'terra_full','model_requested':'gpt-5.6-terra','chapters_done':a.last,'chapters_expected':36,
                     'words':sum(c['words'] for c in chapters),'status':'all_chapters_written_pending_assembly' if a.last==36 else 'in_progress',
                     'literary_review':'Independent four-role review pending full assembly.'}}
for filename,value in outputs.items():
    (phase/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),state_dest,*[x[0] for x in payload],*[phase/k for k in outputs]]:
    q=desktop/f.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,q)
    assert sha(q)==sha(f)
print(json.dumps(outputs['progress.json']))
