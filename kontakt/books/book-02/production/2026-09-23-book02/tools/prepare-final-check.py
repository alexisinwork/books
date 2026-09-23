"""Fresh Astra final full-text and architecture verification packet."""
from pathlib import Path
import json,hashlib,shutil,argparse
p=argparse.ArgumentParser();p.add_argument('--phase',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
assert not a.out.exists();refs=[]
def add(path,body=None):
    path=path.resolve();raw=path.read_bytes();refs.append({'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'text':body if body is not None else raw.decode('utf-8')})
source=a.phase/'assembled/manuscript.md';sha=hashlib.sha256(source.read_bytes()).hexdigest()
blocks=source.read_text(encoding='utf-8').rstrip('\n').split('\n\n')
for f in ['STYLE.md','BOOK_SYSTEM/CORE.md','BOOK_SYSTEM/LANGUAGES/uk/STYLE.md','BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md','kontakt/STYLE.md','kontakt/books/book-02/voice.json','kontakt/series/WORKFLOW-2026-09-23-REVISION-AND-BOOK02.md']:
    add(root/f)
for f in ['structure-v2/full-outline.md','structure-v2/chapter-scene-cards.json','structure-v2/carry-in-source-lock.json','reconciliation-v1/reconciliation.md','reconciliation-v1/issue-ledger.json','literary-v1/run.json']:
    add(run/f)
for f in ['changes.json','observed-state.json']:
    add(a.phase/f)
add(source,'\n\n'.join(f'[P{i:05d}] '+b for i,b in enumerate(blocks,1)))
intro=f'''You are requested model gpt-6-astra. Perform the FINAL COMPLETE READING of Kontakt Book2, all36 chapters / {len(blocks)} numbered blocks, source SHA256 {sha}. This is a post-revision full-volume verification, not a blind independent diagnosis. Terra has applied the compatible package after three independent literary reports (Opus actual unavailability exception). Earlier praise is not evidence. Read the ENTIRE final manuscript sequentially, including every paragraph and document insert, then compare architecture, actual states, source-bound reconciliation and applied changes. No tools, filesystem, browsing, agents or external sources. Root handles saving, mirrors and Git.

Check literary scene effectiveness, motivation, rhythm, voice distinctions, natural Ukrainian without unfounded purism, humour, temporal order, object/permission/resource continuity, who knows what and when, setup/payoff, unresolved boundaries and whole ending. Pay special attention to actual calendar (D0Monday->D9Wednesday; L1 only Monday00:00 toTuesday00:00; Tuesday12report), Ira deletion/consent/contact and own Sunday work arrangement, privateSaturday09:40/publicSunday20:10 versus externalThursday16:10 reservation, knowledge only acquired inCH35, table deliveries distinct, Taras friendship and ordinary Friday meeting, Nina death no invented guilt, Ballast manual/limited. No hiddenmole/L2activation/instantrescue/newcanon. Planned time is not actual prose clock. Character rhetoric may be inaccurate without narrator endorsing it.

Verify every applied prose correction and metadata update, both local context and dependent scenes. Check whether replacements introduce stiffness, new ambiguity or accidental fact changes. Don't reopen optional reviewer taste as mandatory without new source evidence. Do not change text. Report any actual remaining defect with exact final quote and paragraph ID, severity, reason and compatible direction for Terra. If none, say none found within actual reading, not mathematically flawless. Be candid about backend identity: CLI requested model is recorded by root; do not invent independent attestation.

Output REPORT in Ukrainian: exact target SHA; actual full reading ranges per chapter; unread or compressed ranges and limitations; whole architecture and literary conclusions with concrete anchors; correction/dependency check covering all applied patch IDs and metadata; any remaining findings with exact quotations; readiness of this corrected WORKING volume, not publication/authorcanonical approval. Do not claim dictionary, audio, human-reader or Word-render checks you did not perform. Finish the whole reading and report in this response, no plan-only answer.

'''
prompt=intro+'\n\n'.join('<SOURCE path='+json.dumps(r['path'],ensure_ascii=False)+' sha256='+r['sha256']+'>\n'+r['text']+'\n</SOURCE>' for r in refs)
a.out.mkdir(parents=True);(a.out/'prompt.md').write_text(prompt,encoding='utf-8',newline='\n')
(a.out/'packet.json').write_text(json.dumps({'model_requested':'gpt-6-astra','source_sha256':sha,'paragraphs':len(blocks),'prompt_bytes':len(prompt.encode()),'sources':[{k:v for k,v in r.items() if k!='text'} for r in refs]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),*a.out.iterdir()]:
    d=desktop/f.resolve().relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'source_sha256':sha,'paragraphs':len(blocks),'prompt_bytes':len(prompt.encode())}))
