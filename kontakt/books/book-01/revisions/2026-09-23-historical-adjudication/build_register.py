import json,re,hashlib,collections,shutil
from pathlib import Path
from read_context import ROOT,BOOK,SOURCE,chapters,items,chapter,sha
OUT=Path(__file__).resolve().parent
EXPECTED='9c373211ae0ce40d7992efaf65b6b770cca8c837ef35f0736f25e08489dad0b3'
assert sha==EXPECTED
base={}
for name in ['decisions.json','decisions-09-16.json','decisions-17-24.json','decisions-25-30.json']:
 base.update(json.loads((OUT/name).read_text(encoding='utf-8')))
over=json.loads((OUT/'overrides.json').read_text(encoding='utf-8'))
special=json.loads((OUT/'decisions-special.json').read_text(encoding='utf-8'))
names={'A':'already_fixed','P':'preserve_context_or_taste','C':'compatible_concrete_correction','U':'dependent_unresolved'}
ref_over={
 'CH01-SOL-V1-ENS-002':[(1,120)],'CH02-SOL-V1-ENS-004':[(3,1),(3,3),(3,7)],
 'CH03-SOL-V1-ENS-001':[(3,13),(3,29),(3,53)],
 'CH03-SOL-V1-ENS-006':[(3,29)],
 'CH08-SOL-V1-ENS-009':[(8,67),(8,68),(8,69),(8,70)],
 'CH14-SOL-V1-ENS-009':[(14,18)],
 'CH17-SOL-V1-ENS-002':[(17,22),(17,23),(17,24),(17,26)],
 'CH17-SOL-V1-ENS-005':[(17,24)],'CH17-SOL-V1-ENS-008':[(17,23)],
 'CH27-SOL-V1-ENS-003':[(27,45)],'CH30-SOL-V1-ENS-004':[(30,41)],
 'CH30-SOL-V1-ENS-008':[(30,19)]
}
extra_replacements={
 'CH04-SOL-V1-ENS-002':[('зворотну калібровку','зворотне калібрування')],
 'CH27-SOL-V1-ENS-012':[('на вашій зупинці або о 18:38','після вашої зупинки або о 18:38')]
}
def evidence(n,p):
 return {'chapter':n,'anchor':f'CB{p:04d}','quote':chapters[n][p-1]}
regs=[]; patches=[]; errors=[]
for it in items:
 ident=it['id']; n=chapter(it); matches=[]; missing=[]
 if ident in special:
  sp=special[ident]; row=[sp['decision'],sp['rationale']]
  matches=[evidence(*ref) for ref in sp['evidence']]
 else:
  ens=[a for a in items if chapter(a)==n and '-ENS-' in a['id']]
  idx=[a['id'] for a in ens].index(ident)
  row=over.get(ident,base[str(n)][idx])
  for anchor in it.get('anchors',[]):
   if not isinstance(anchor,dict):continue
   q=anchor.get('quote','')
   found=[j+1 for j,p in enumerate(chapters[n]) if q and q in p]
   if found:
    old=re.search(r'P0*(\d+)',anchor.get('anchor',''))
    wanted=int(old[1])-1 if old else found[0]
    p=min(found,key=lambda x:abs(x-wanted)); matches.append(evidence(n,p))
   else:missing.append(anchor)
  matches.extend(evidence(*ref) for ref in ref_over.get(ident,[]))
 data={'id':ident,'decision':names[row[0]],'rationale':row[1],
       'current_source':str(SOURCE.relative_to(ROOT)).replace('\\','/'),'current_source_sha256':sha,
       'historical_observation':it.get('observation'),'historical_proposed_change':it.get('proposed_change'),
       'historical_resolution_status':it.get('resolution_status'),
       'author_approval':'not_assigned_by_this_adjudication',
       'chapter_dependency':it.get('dependencies',[]),
       'evidence_scope':'target-paragraph contextual adjudication; not a new complete sequential novel read',
       'current_evidence':list({(e['chapter'],e['anchor']):e for e in matches}.values()),
       'historical_anchors_not_found_exactly':missing,'proposed_exact_replacements':[]}
 if ident in special:
  data.update({k:v for k,v in special[ident].items() if k not in ['decision','rationale','evidence']})
 else:
  replacements=([tuple(row[2:4])] if len(row)>=4 else [])+extra_replacements.get(ident,[])
  for before,after in replacements:
   body='\n\n'.join(chapters[n]); count=body.count(before)
   if not count:errors.append({'id':ident,'missing_before':before});continue
   refs=[evidence(n,j+1) for j,p in enumerate(chapters[n]) if before in p or (before.strip() and before.strip() in p)]
   if not refs and '\n\n' in before:
    first=before.split('\n\n')[0];refs=[evidence(n,j+1) for j,p in enumerate(chapters[n]) if first in p]
   patch={'id':ident,'chapter':n,'source_sha256':sha,'before':before,'after':after,'occurrences_in_chapter':count,'apply_scope':'only named chapter; all listed occurrences','status':'proposed_compatible_not_applied','rationale':row[1],'current_evidence':refs}
   data['proposed_exact_replacements'].append(patch);patches.append(patch)
   data['current_evidence'].extend(e for e in refs if e not in data['current_evidence'])
 regs.append(data)
assert len(regs)==374 and len({r['id'] for r in regs})==374
original=BOOK/'production/2026-09-21-book01/readers/full-33-astra-v1/manuscript.md'
assert hashlib.sha256(original.read_bytes()).hexdigest()=='ea8726f18d1a00625d4a262ba03c54667fb6bd98365cd59063e51e41e372f29b'
summary=collections.Counter(r['decision'] for r in regs)
payload={'schema_version':1,'source_sha256':sha,'historical_source_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),
 'historical_registry_sha256':hashlib.sha256((BOOK/'audit/issues.json').read_bytes()).hexdigest(),
 'scope':'All 374 central historical issue entries individually adjudicated against targeted current contexts; no full sequential reread claim',
 'anchors':'CB = 1-based nonempty blank-line-delimited chapter-body block, heading excluded; block may contain multiple Markdown quote/table lines; not historical P numbering',
 'status':'editorial recommendations; no author decision, canon promotion or manuscript mutation',
 'counts':dict(summary),'items':regs}
def write(name,obj): (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
write('adjudication-all-374.json',payload)
# Deduplicate identical shared corrections while retaining the IDs.
dedup={}
for p in patches:
 key=(p['chapter'],p['before'],p['after'])
 if key not in dedup: dedup[key]={**p,'issue_ids':[p['id']]}
 elif p['id'] not in dedup[key]['issue_ids']:dedup[key]['issue_ids'].append(p['id'])
write('proposed-compatible-corrections.json',{'source_sha256':sha,'status':'proposed_not_applied; reconcile with parallel full-review package before use','corrections':list(dedup.values())})
write('validation.json',{'registry_ids':len(regs),'unique_ids':len(set(r['id'] for r in regs)),'counts':dict(summary),'exact_patch_records':len(patches),'deduplicated_patches':len(dedup),'patches_not_found':errors,'items_without_evidence':[r['id'] for r in regs if not r['current_evidence']], 'current_source_sha256_unchanged':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==sha})
print(json.dumps({'counts':dict(summary),'patches':len(dedup),'errors':errors,'without_evidence':[r['id'] for r in regs if not r['current_evidence']]},ensure_ascii=False,indent=2))
