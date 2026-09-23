"""Rebind only verified evidence after the exact one-word native follow-up."""
from pathlib import Path
import json,hashlib,shutil,copy
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-final-v2';old=run/'terra-final-v1';book=run.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def rel(p):return p.relative_to(root).as_posix()
source=phase/'assembled/manuscript.md';text=source.read_text(encoding='utf-8');h=sha(source);blocks=text.rstrip('\n').split('\n\n');changes=read(phase/'changes.json');checks=[]
for n in range(1,33):
 expected=(run/f'terra-full-v1/chapters/chapter-{n:02d}.md').read_text(encoding='utf-8')
 for p in [p for p in changes['patches'] if p['chapter']==n]:
  assert expected.count(p['before'])==1;expected=expected.replace(p['before'],p['after'],1)
  assert text.count(p['after'])==1;anchor=len(text[:text.index(p['after'])].split('\n\n'));checks.append({'id':p['id'],'chapter':n,'final_start_paragraph':f'P{anchor:05d}','after_exact':True})
 assert expected==(phase/f'chapters/chapter-{n:02d}.md').read_text(encoding='utf-8')
write(phase/'patch-verification.json',{'status':'all28_exact_native_patches_verified','source_sha256':h,'source_before_revision':changes['predecessor_sha256'],'parent_source_sha256':sha(old/'assembled/manuscript.md'),'patches':checks,'unlisted_prose_changes':False,'delta_from_last_complete_reading':'Only explicit narrator subject in CH29; paragraph count unchanged.','final_full_reading':'pending'})
registry=book/'audit/issues.json';prior=phase/'global-registry-before-residual.json';assert not prior.exists();shutil.copy2(registry,prior);issues=read(registry)
for item in issues['items']:
 if item['id'].startswith('KONTAKT-B03-20260923-'):
  item['verification']['source']=rel(source);item['verification']['source_sha256']=h
  if item['id']=='KONTAKT-B03-20260923-U03':
   ev=[]
   for a in item['anchors']:
    if a['paragraph']=='P00251':continue
    matches=[i for i,b in enumerate(blocks,1) if a['quote'] in b];assert len(matches)==1
    ev.append({**a,'source':rel(source),'source_sha256':h,'paragraph':f'P{matches[0]:05d}'})
   for i in [252,253]:ev.append({'source':rel(source),'source_sha256':h,'chapter':4,'paragraph':f'P{i:05d}','quote':blocks[i-1]})
   item['anchors']=ev
write(registry,issues)
account=read(old/'metadata-plan-accounting.json');account['source_sha256']=h;account['parent_accounting_sha256']=sha(old/'metadata-plan-accounting.json');account['residual_dependency']='B03-FINAL-01 explicitly names existing narrator action; scene observations remain identical, no new event or time.'
for item in account['items']:
 if item['id']=='B03-M023':item['evidence']=next(x['anchors'] for x in issues['items'] if x['id']=='KONTAKT-B03-20260923-U03')
write(phase/'metadata-plan-accounting.json',account)
meta_path=book/'book.json';shutil.copy2(meta_path,phase/'book-before-final-pointer.json');meta=read(meta_path);meta.setdefault('preserved_full_text_before_revision',copy.deepcopy(meta['active_full_text']));meta['active_full_text']={'path':source.relative_to(book).as_posix(),'sha256':h,'chapters':32,'canonical_status':'working_not_author_approved'};meta.update(stage='final_full_reading',audit_status='last_local_correction_applied_complete_recheck_running');assert meta['master'] is None;write(meta_path,meta)
progress=read(run/'progress.json');shutil.copy2(run/'progress.json',phase/'progress-before-final-check.json')
for item in progress['phases']:
 if item['phase'] in ['reconciliation_and_full_check','final_compatible_revision']:item['status']='complete'
 if item['phase']=='final_full_reading_and_delivery':item['status']='in_progress'
write(run/'progress.json',progress)
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),registry,meta_path,run/'progress.json',*[p for p in phase.rglob('*') if p.is_file()]]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'source_sha256':h,'patches':len(checks),'paragraphs':len(blocks),'active_working_pointer_updated':True}))
