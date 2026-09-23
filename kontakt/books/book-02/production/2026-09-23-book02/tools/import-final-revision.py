"""Import exact Terra-authored replacements into a new, source-bound revision."""
from pathlib import Path
import argparse,json,hashlib,difflib,copy,shutil
p=argparse.ArgumentParser();p.add_argument('--response',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--quote-map',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;old=run/'terra-full-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
raw=a.response.read_text(encoding='utf-8').strip()
if raw.startswith('```json') and raw.endswith('```'):raw=raw[7:-3].strip()
data=json.loads(raw)
assert data['source_sha256']==sha(old/'assembled/manuscript.md')
assert not a.out.exists(),'Preserve existing revisions'
texts={n:(old/f'chapters/chapter-{n:02d}.md').read_text(encoding='utf-8') for n in range(1,37)}
initial=copy.deepcopy(texts);changes=[];ids=set()
for patch in data['patches']:
    n=patch['chapter'];before=patch['before'];after=patch['after']
    assert patch['id'] not in ids;ids.add(patch['id'])
    assert before and before!=after and texts[n].count(before)==1,(patch['id'],texts[n].count(before))
    assert '\ufffd' not in after and '????' not in after
    texts[n]=texts[n].replace(before,after,1);changes.append(patch)
state=read(old/'observed-state.json')
for change in data.get('state_updates',[]):
    scene=next(s for c in state['chapters'] if c['chapter']==change['chapter'] for s in c['observed']['scenes'] if s['id']==change['scene_id'])
    assert scene[change['field']]==change['before'],change
    scene[change['field']]=change['after']
quote_map=read(a.quote_map) if a.quote_map else {}
quote_changes=[];missing=[]
for c in state['chapters']:
    n=c['chapter']
    for scene in c['observed']['scenes']:
        for i,q in enumerate(scene['quotes']):
            if q not in texts[n]:
                replacement=quote_map.get(q)
                if replacement and replacement in texts[n]:
                    scene['quotes'][i]=replacement;quote_changes.append({'scene':scene['id'],'before':q,'after':replacement,'basis':'Literal final-text evidence selected for the same observation; not a reissued review.'})
                else:missing.append({'chapter':n,'scene':scene['id'],'quote':q})
if missing:raise ValueError(json.dumps({'missing_quotes':missing},ensure_ascii=False))
a.out.mkdir(parents=True);(a.out/'chapters').mkdir()
diff=[]
for n,text in texts.items():
    name=f'chapter-{n:02d}.md';f=a.out/'chapters'/name;f.write_text(text,encoding='utf-8',newline='\n')
    c=state['chapters'][n-1];c.update(path=f.resolve().relative_to(root).as_posix(),sha256=sha(f),words=len(text.split()))
    diff.extend(difflib.unified_diff(initial[n].splitlines(True),text.splitlines(True),fromfile='terra-full-v2/'+name,tofile=a.out.name+'/'+name))
state.update(predecessor_sha256=data['source_sha256'],revision_basis='Bulk author-authorized compatible corrections; all original state quotations checked against final chapter source.')
write(a.out/'observed-state.json',state)
write(a.out/'changes.json',{'predecessor_sha256':data['source_sha256'],'model_requested':'gpt-5.6-terra','response':a.response.resolve().relative_to(root).as_posix(),'response_sha256':sha(a.response),'patches':changes,'state_updates':data.get('state_updates',[]),'quote_rebindings':quote_changes,'omissions':data.get('omissions',[]),'reading_scope':data.get('reading_scope'),'verification_notes':data.get('verification_notes')})
(a.out/'before-after.diff').write_text(''.join(diff),encoding='utf-8',newline='\n')
for field in ['time_basis','events','knowledge','resources']:
    write(a.out/(field+'.observed.json'),{'status':'observed_working_revision_not_canon','basis':'observed-state.json','items':[{'chapter':c['chapter'],'chapter_sha256':c['sha256'],'scene_id':s['id'],'observation':s[field],'quotes':s['quotes'],'open_dependencies':s.get('open_dependencies',[])} for c in state['chapters'] for s in c['observed']['scenes']]})
shutil.copy2(old/'proposals.json',a.out/'inherited-working-proposals.json')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),*a.out.rglob('*')]:
    if f.is_file():
        d=desktop/f.resolve().relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'patches':len(changes),'changed_chapters':sum(texts[n]!=initial[n] for n in texts),'state_updates':len(data.get('state_updates',[]))}))
