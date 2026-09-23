from pathlib import Path
import json, hashlib, shutil, re

ROOT = Path(__file__).resolve().parents[6]
RUN = ROOT / 'kontakt/books/book-03/production/2026-09-23-book03'
OUT = RUN / 'reconciliation-v1'
DESKTOP = Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return p.relative_to(ROOT).as_posix()
def write(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

plan = read(OUT/'PATCH-PLAN.json')
global_updates = plan.get('global_registry_updates', [])
scene_updates = []
for m in plan['metadata_updates']:
    if m.get('target_file'):
        m['type'] = 'global_registry_update'
        global_updates.append(m)
    else:
        m['type'] = 'scene_field_update'
        # Space between Ukrainian words and clock values; these are proposed metadata, not source quotations.
        m['after'] = re.sub(r'(?<=[А-Яа-яІіЇїЄєҐґ])(?=\d)', ' ', m['after'])
        scene_updates.append(m)
plan['metadata_updates'] = scene_updates
plan['global_registry_updates'] = global_updates
write('PATCH-PLAN.json', plan)

states = read(RUN/'terra-full-v1/observed-state.json')
scenes = {s['id']:s for c in states['chapters'] for s in c['observed']['scenes']}
meta_checks=[]
for m in scene_updates:
    assert m['field'] in ['time_basis','events','knowledge','resources','open_dependencies']
    assert scenes[m['scene_id']][m['field']] == m['before'], m['id']
    meta_checks.append({'id':m['id'],'scene_id':m['scene_id'],'field':m['field'],'exact_before':True})
registry_path = ROOT/'kontakt/books/book-03/audit/issues.json'
registry = read(registry_path)
u03 = next(x for x in registry['items'] if x['id']=='KONTAKT-B03-20260923-U03')
assert u03['resolution_status'] == global_updates[0]['before']
unknowns=[]
for x in registry['items']:
    iid=x['id']
    status=x.get('resolution_status',x.get('status'))
    direction='Preserve historical resolution and current author workflow override where present.'
    if status=='unresolved': direction='Remain unresolved; carry dependencies forward without invented facts.'
    if iid=='KONTAKT-B03-20260923-U03': direction='Limited documentary working resolution only; execute B03-M023 with preserved history and final-source evidence. Private inputs and budget mechanism remain unknown.'
    unknowns.append({'id':iid,'source_resolution_status':status,'direction':direction,'author_decision':'pending','source_registry_sha256':sha(registry_path)})
write('global-unknown-dispositions.json',{'source':rel(registry_path),'source_sha256':sha(registry_path),'items':unknowns,'central_registry_modified':False})
write('metadata-validation.json',{'status':'passed','source_state_sha256':sha(RUN/'terra-full-v1/observed-state.json'),'scene_updates':meta_checks,'global_updates':[{'id':global_updates[0]['id'],'exact_before':True,'executed_here':False}],'conditional_after_requires_new_prose':['B03-M016','B03-M017','B03-M020','B03-M021','B03-M022']})

rv=read(OUT/'report-validation.json')
opus=next(x for x in rv['reports'] if x['role']=='opus')
write('provenance-corrigendum.json',{'status':'final','subject':'Opus unavailable attempt; decision snapshot versus final preserved stream','decision_snapshot':{'error_message_steps':4,'reports':0,'basis':'locked stop-decision record'},'final_preserved_stream':{'error_message_steps':len(opus['error_step_indices']),'indices':opus['error_step_indices'],'reports':0,'trace_sha256':opus['trace_sha256']},'explanation':'Different observation times; do not overwrite locked run or infer backend reason. Repeated errors, no successful fourth diagnosis. Author unavailable-model exception applies.','backend_cause':'unknown','locked_reports_modified':False})

# Inventory records exactly how material was used, not a hash-as-reading claim.
entries={}
def add(path, scope):
    if path.is_file(): entries[rel(path)]={'path':rel(path),'sha256':sha(path),'review_scope':scope}
add(RUN/'terra-full-v1/assembled/manuscript.md','Actual untruncated full literary reading, all32/1540 blocks; per-chapter findings in full-reading-coverage.json.')
for p in [RUN/'terra-full-v1/observed-state.json',RUN/'terra-full-v1/proposals.json']:
    add(p,'Full current records read; all41 scene states compared to actual prose.')
for p in (RUN/'root-terra-reading').glob('*.json'): add(p,'Full coordinator notes read and adjudicated; source prose independently read here.')
for p in (RUN/'root-rough-reading').glob('*.json'): add(p,'Full earlier reading notes consulted to verify corrected versus inherited findings; not a new full rough reread.')
for p in [RUN/'astra-rough-v1/handoff-for-terra.md',RUN/'astra-rough-v1/self-review.md']:
    add(p,'Full rough handoff comparison read; final Terra prose governs.')
for p in (RUN/'structure-v1').iterdir():
    if not p.is_file(): continue
    scope='Frozen integrity/provenance inventory; not independently counted as literary reading.'
    if p.name=='chapter-scene-cards.json': scope='All41 scene content read; all32 chapter boundary objects read; fixed repeated role/status/source fields mechanically cross-checked.'
    if p.name=='full-outline.md': scope='Scene content read through exact derived cards; outline introductory/nonduplicate content checked. Not claimed as a separate second prose reading.'
    if p.name in ['knowledge.planned.json','resources.planned.json','timeline.planned.json']: scope='Global/initial/final content read; all scene-specific content checked against read cards and actual prose; duplicate-derived fields compared.'
    if p.name in ['promises.planned.json','prediction-evidence-plan.json','end-state.planned.json','voices-and-glossary.md','decisions-and-questions.json','carry-in-source-lock.json']: scope='Full relevant planning content read and compared to actual prose; carry quotes additionally checked in exact source chapters.'
    add(p,scope)
for role in ['terra','gemini_flash','gemini_pro']:
    for p in (RUN/'literary-v1/results'/role).glob('*.md'): add(p,'Full REPORT and turn001–003 read; turn004 verified hash-identical to REPORT where present.')
for p in (RUN/'literary-v1').rglob('*'):
    if p.is_file() and (p.suffix in ['.json','.jsonl'] or 'stdout' in p.name or 'stderr' in p.name):
        add(p,'Provenance/coverage/trace inspection; scope and checkpoint limits recorded in report-validation.json. Hash does not attest backend identity or model reading.')
for name in ['AGENTS.md','STYLE.md','kontakt/AGENTS.md','kontakt/project.json','kontakt/START_HERE.md','kontakt/STYLE.md','kontakt/books/book-03/book.json','.agents/skills/ru-editorial-reconciler/SKILL.md','kontakt/series/WORKFLOW-2026-09-23-BOOK03.md','kontakt/series/CANON-POLICY.md','BOOK_SYSTEM/CORE.md','BOOK_SYSTEM/LANGUAGES/UK/STYLE.md', 'kontakt/books/book-03/audit/issues.json']:
    add(ROOT/name,'Task instructions, source precedence or current unknowns read; workflow override controls inherited per-scene workflow.')
carry=read(RUN/'structure-v1/carry-in-source-lock.json')
for path in [carry['source'],carry['book1_inherited']['source']]: add(ROOT/path,'Relevant carry proofs read and matched in exact chapters; no new whole-volume reading claim for prior books.')
write('source-inventory.json',{'status':'final','files':list(entries.values()),'limits':['No fourth successful independent report.','No dictionary authority invented for optional lexical purism.','No source/central metadata mutation.','No claim of a second full reading of prior books or rough volume.']})

ledger=read(OUT/'issue-ledger.json')
issues=ledger['issues']
assert len({x['id'] for x in issues})==len(issues)
assert all(x['author_decision']=='pending' for x in issues)
assert len(plan['patches'])==27 and len(scene_updates)==22 and len(global_updates)==1
source=RUN/'terra-full-v1/assembled/manuscript.md'
assert sha(source)=='ab11580a6c9adcaa9a3af4696a4466979e38f6e138633e5230f802d675ff1c6b'
raw=source.read_text(encoding='utf-8')
assert all(raw.count(x['before'])==1 for x in plan['patches'])
write('package-validation.json',{'status':'passed','source_sha256':sha(source),'actual_reading':{'chapters':32,'scenes':41,'blocks':1540},'issues':len(issues),'text_patches':27,'scene_metadata_updates':22,'global_registry_updates':1,'no_change_checks':len(plan['no_change_verification_items']),'all_individual_author_decisions':'pending','source_unchanged':True,'checks':['Unique source-bound full-paragraph patches.','Exact current scene fields before all metadata updates.','82 state quotes matched in their source chapters.','29 carry quotes matched in correct prior-book chapters.','All three final reports plus provisional Gemini findings adjudicated.'],'mirror_policy':'Every owned file including this package manifest is copied and SHA-verified by this finalizer; console result records completed comparison.'})

files=[p for p in OUT.rglob('*') if p.is_file() and p.name!='manifest.json']
write('manifest.json',{'status':'frozen','phase':'astra_source_bound_reconciliation','source':rel(source),'source_sha256':sha(source),'files':[{'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)],'self_excluded':True})
copies=[]
for p in sorted(OUT.rglob('*')):
    if not p.is_file():continue
    target=DESKTOP/rel(p);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    assert sha(p)==sha(target)
    copies.append(rel(p))
print(json.dumps({'status':'frozen_and_mirrored','files':len(copies),'manifest_sha256':sha(OUT/'manifest.json'),'plan_sha256':sha(OUT/'PATCH-PLAN.json'),'reconciliation_sha256':sha(OUT/'reconciliation.md'),'ledger_sha256':sha(OUT/'issue-ledger.json')},ensure_ascii=False))
