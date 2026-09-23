"""Build an isolated Terra revision packet from the fixed whole-book diagnoses."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[6]
run=Path(__file__).resolve().parent.parent
out=run/'terra-final-packet-v1'
assert not out.exists()
refs=[]
def add(p):
    p=Path(p);p=p if p.is_absolute() else root/p
    raw=p.read_bytes();refs.append({'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode('utf-8')})
for p in ['AGENTS.md','STYLE.md','BOOK_SYSTEM/CORE.md','BOOK_SYSTEM/LANGUAGES/uk/STYLE.md','BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md','kontakt/AGENTS.md','kontakt/STYLE.md','kontakt/books/book-02/book.json','kontakt/books/book-02/voice.json','kontakt/books/book-02/characters.planned.json','kontakt/series/CANON-POLICY.md','kontakt/series/glossary.json','kontakt/series/WORKFLOW-2026-09-23-REVISION-AND-BOOK02.md','kontakt/guides/SCENE-EDITING.md','kontakt/skills/ru-book-revision/SKILL.md','kontakt/skills/ru-kontakt-series/SKILL.md']:
    add(p)
for p in ['structure-v2/full-outline.md','structure-v2/chapter-scene-cards.json','structure-v2/carry-in-source-lock.json','terra-full-v2/observed-state.json','terra-full-v2/assembled/manuscript.md','literary-v1/run.json','reconciliation-v1/reconciliation.md','reconciliation-v1/issue-ledger.json','reconciliation-v1/PATCH-PLAN.json']:
    add(run/p)
for role in ['terra','gemini_flash','gemini_pro']:
    add(run/'literary-v1/results'/role/'REPORT.md')
intro='''You are requested model gpt-5.6-terra, performing the AUTHOR-AUTHORIZED FINAL UKRAINIAN LITERARY REVISION of Kontakt book2. The author requested full structure Astra -> all rough Astra -> full text Terra -> independent literary reviews -> Astra reconciliation -> Terra final corrections. You are the final reviser, not an independent reviewer. Read the ENTIRE36-chapter full source, architecture, states, ALL three completed diagnoses and Astra reconciliation. Opus unavailable is handled in the run record per explicit author exception. Root handles filesystem, mirrors, Git and verification. Use NO tools, no external access, no subagents. Do not stop at a plan or offer.

Deliver ALL compatible corrections in PATCH-PLAN, composing the exact final Ukrainian prose yourself. Preserve voice, humour, causal sequence, knowledge timing, and unresolved canon. No new intrigue, no rearranged ending, no tightening merely for word count. Reviewer reports contain false positives: Astra reconciliation adjudicates them. Do not turn optional/noise findings into new changes. This is a separate working revision, not author canon. Bulk author authorization does not mean individual author votes. If a proposed correction cannot be made safely, explicitly explain the omission; otherwise finish it now. Read whole source before deciding every local change.

Return ONLY one valid JSON object, with no code fence and no extra prose:
{"reading_scope":"truthful coverage and limitations", "source_sha256":"e641f3b639f0c03578c51916c0434156c584ce8022f556d94e522bf7c653679d", "patches":[{"id":"plan patch ID","issue_ids":["..."],"chapter":N,"before":"exact UNIQUE literal substring from that source chapter","after":"your completed final replacement prose","reason":"why this solves the issue while preserving voice"}], "state_updates":[{"chapter":N,"scene_id":"exact scene ID","field":"time_basis|events|knowledge|resources|open_dependencies","before":"exact current state value, or JSON array for open_dependencies","after":"complete corrected state value, or JSON array for open_dependencies"}], "omissions":[], "verification_notes":"dependency checks and remaining boundaries"}.

Use exact source substrings and punctuation for before. A patch must occur once in its chapter; choose enough context. Patches must not overlap and must be listed in chapter order. Do not encode paragraph breaks as literal backslash+n text: valid JSON escapes decode to actual newlines. You may keep paragraph count; do not insert paragraph IDs into the novel. Handle all planned patches in ONE response. Include exact state updates where chronology or event description changes. State quotes are mechanically rebound by root and verified; don't invent new quotes. Return the complete JSON now after reading.

'''
prompt=intro+'\n\n'.join('<SOURCE path='+json.dumps(r['path'],ensure_ascii=False)+' sha256='+r['sha256']+'>\n'+r['text']+'\n</SOURCE>' for r in refs)
out.mkdir();(out/'prompt.md').write_text(prompt,encoding='utf-8',newline='\n')
(out/'packet.json').write_text(json.dumps({'role':'final_revision','requested_model':'gpt-5.6-terra','source_sha256':'e641f3b639f0c03578c51916c0434156c584ce8022f556d94e522bf7c653679d','prompt_bytes':len(prompt.encode()),'sources':[{k:v for k,v in r.items() if k!='text'} for r in refs]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),*out.iterdir()]:
    d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'prompt_bytes':len(prompt.encode()),'sources':len(refs)}))
