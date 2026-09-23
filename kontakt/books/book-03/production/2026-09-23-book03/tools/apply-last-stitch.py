"""Apply only the native Terra residual patch, preserving every predecessor."""
from pathlib import Path
import json,hashlib,shutil,difflib,copy,re
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;old=run/'terra-final-v1';phase=run/'terra-final-v2';assert not phase.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def rel(p):return p.relative_to(root).as_posix()
response=run/'terra-final-execution-v3/RESPONSE.md';data=read(response);inv=read(response.parent/'invocation.json')
assert inv['exit_code']==0 and inv['item_types']==['agent_message'] and inv['model_requested']=='gpt-5.6-terra'
assert data['source_sha256']==sha(old/'assembled/manuscript.md') and not data['omissions'] and not data['state_updates'] and len(data['patches'])==1
p=data['patches'][0];assert p['id']=='B03-FINAL-01' and p['chapter']==29
before=(old/'chapters/chapter-29.md').read_text(encoding='utf-8');assert before.count(p['before'])==1
assert p['after'].split()==p['before'].split()[:1]+['я']+p['before'].split()[1:],'Only the explicit narrator subject was authorized here'
phase.mkdir();(phase/'chapters').mkdir();state=read(old/'observed-state.json')
for n in range(1,33):
 f=old/f'chapters/chapter-{n:02d}.md';target=phase/f'chapters/chapter-{n:02d}.md';text=f.read_text(encoding='utf-8')
 if n==29:text=text.replace(p['before'],p['after'],1)
 target.write_text(text,encoding='utf-8',newline='\n');c=state['chapters'][n-1];c.update(path=rel(target),sha256=sha(target),words=len(text.split()))
 for scene in c['observed']['scenes']:
  for q in scene['quotes']:assert q in text
write(phase/'observed-state.json',state)
changes=read(old/'changes.json');changes['patches'].append(p);changes['parent_revision']={'source':rel(old/'assembled/manuscript.md'),'sha256':data['source_sha256'],'changes_sha256':sha(old/'changes.json')};changes['residual_native_response']={'path':rel(response),'sha256':sha(response),'reading_scope':data['reading_scope']};changes['residual_issue']={'id':'B03-FINAL-01','source_report':rel(run/'final-astra-native-v1/REPORT.md'),'sha256':sha(run/'final-astra-native-v1/REPORT.md'),'scope':'One newly ambiguous subject after B03-P024; Terra added only explicit narrator subject.'};write(phase/'changes.json',changes)
for field in ['time_basis','events','knowledge','resources']:
 write(phase/(field+'.observed.json'),{'status':'observed_working_revision_not_canon','basis':'observed-state.json','items':[{'chapter':c['chapter'],'chapter_sha256':c['sha256'],'scene_id':s['id'],'observation':s[field],'quotes':s['quotes'],'open_dependencies':s.get('open_dependencies',[])} for c in state['chapters'] for s in c['observed']['scenes']]})
for name in ['inherited-working-proposals.json','global-registry-before.json']:shutil.copy2(old/name,phase/name)
diff=[]
for n in range(1,33):
 f=f'chapter-{n:02d}.md';a=(run/'terra-full-v1/chapters'/f).read_text(encoding='utf-8');b=(phase/'chapters'/f).read_text(encoding='utf-8');diff.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='terra-full-v1/'+f,tofile='terra-final-v2/'+f))
(phase/'before-after.diff').write_text(''.join(diff),encoding='utf-8',newline='\n')
report=run/'final-astra-native-v1/REPORT.md';r=report.read_text(encoding='utf-8');blocks=(old/'assembled/manuscript.md').read_text(encoding='utf-8').rstrip('\n').split('\n\n');assert data['source_sha256'] in r
starts=[i for i,b in enumerate(blocks,1) if b.startswith('# Розділ ')];coverage=[]
for n,(first,last) in enumerate(zip(starts,[x-1 for x in starts[1:]]+[len(blocks)]),1):
 assert f'| {n:02d} | P{first:05d}–P{last:05d} |' in r;coverage.append({'chapter':n,'first':first,'last':last})
write(run/'final-astra-v1-validation.json',{'status':'complete_full_reading_with_one_residual_not_final_acceptance','source_sha256':data['source_sha256'],'report_sha256':sha(report),'actual_root_report_reading':'Entire report read in two untruncated outputs; all32ranges matched source; all27patch rows,23metadata rows,12guards,81issue accounting and residual finding read.','coverage':coverage,'residual':'B03-FINAL-01','no_compaction_or_tools_observed':read(report.parent/'invocation.json')['item_types']==['agent_message'],'followup':'New native Terra patch, new version and another final complete Astra reading.'})
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),run/'final-astra-v1-validation.json',*[x for x in phase.rglob('*') if x.is_file()]]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'phase':'terra-final-v2','total_patches':28,'residual_change':'one explicit narrator subject','unchanged_from_v1_chapters':31}))
