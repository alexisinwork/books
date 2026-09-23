"""Preserve draft metadata before bounded corrections; never edit chapter prose."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
changes=[]
for n in [9,28,29,32]:
 p=P/f'notes/chapter-{n:02}.json';before=sha(p);d=rd(p)
 dest=P/'history/metadata-before-final-scope'/f'chapter-{n:02}-{before}.json';dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 if n in [9,28]:
  # U04 means Dal's unknown permanent income, not Osya's trial route.
  for s in d['scenes']:s['open_dependencies']=[x for x in s['open_dependencies'] if x!='U04']
 if n==29:
  s=d['scenes'][1]
  s['events']=[x.replace('fullprofiletemporaryaccess','permitted-working-fragment temporary access') for x in s['events']]
  s['resources']=[x.replace('existingfullprofiletemporarilyuntilcompletion','previously permitted working fragments temporarily until completion') for x in s['resources']]
  d['continuity'].append('CH29 prose full-package wording is imprecise and assigned to Terra: CH03/32 actual scope is only permitted fragments/logs; private correspondence never granted.')
 if n==32:
  d['scenes'][0]['open_dependencies']=['U04','B03-U01','B03-U03']
  d['continuity'].append('U01/U02/U05/B03-U02 remain inherited global unknowns, not active dependencies of this final metadata scene.')
 save(p,d);changes.append(dict(chapter=n,before_sha256=before,after_sha256=sha(p),history_path=str(dest.relative_to(P)),scope='metadata_only_no_prose_change'))
 subprocess.run([sys.executable,'-X','utf8',str(P/'manage.py'),'register',str(n)],check=True)
save(P/'metadata-corrections.json',dict(status='completed',author_decision='not_an_author_vote',changes=changes))
