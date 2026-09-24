"""Build source-bound, full-rough authoring packets after the all-rough handoff."""
from pathlib import Path
import argparse,hashlib,json,re,shutil
p=argparse.ArgumentParser();p.add_argument('--first',type=int,required=True);p.add_argument('--last',type=int,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-full-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cards=json.loads((run/'structure-v1/chapter-scene-cards.json').read_text(encoding='utf-8'))
expected=max(s['chapter'] for s in cards['scenes']);assert 1<=a.first<=a.last<=expected
gate=json.loads((run/'rough-handoff-verification.json').read_text(encoding='utf-8'));assert gate['status']=='passed'
rough=run/'astra-rough-v1/assembled/manuscript.md';assert gate['source_sha256']==sha(rough)
out=phase/'packets'/f'chapters-{a.first:02d}-{a.last:02d}';assert not out.exists();refs=[]
def add(path,excerpt=None):
 path=Path(path);path=path if path.is_absolute() else root/path
 raw=path.read_bytes();body=raw.decode('utf-8') if excerpt is None else excerpt
 if excerpt is None and path.suffix=='.json':
  data=json.loads(body);body=json.dumps(data,ensure_ascii=False,separators=(',',':'));assert json.loads(body)==data
 refs.append({'path':path.relative_to(root).as_posix(),'sha256':sha(path),'supplied_text_sha256':hashlib.sha256(body.encode()).hexdigest(),'representation':'complete source, JSON whitespace compacted only' if excerpt is None else 'explicit excerpt; no claim of the omitted range','text':body})
for f in ['AGENTS.md','STYLE.md','BOOK_SYSTEM/CORE.md','BOOK_SYSTEM/LANGUAGES/uk/STYLE.md','BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md','kontakt/AGENTS.md','kontakt/STYLE.md','kontakt/project.json','kontakt/books/book-04/book.json','kontakt/books/book-04/brief.md','kontakt/books/book-04/voice.json','kontakt/books/book-04/characters.planned.json','kontakt/books/book-04/COMPATIBILITY-MECHANICS.md','kontakt/series/CANON-POLICY.md','kontakt/series/glossary.json','kontakt/skills/ru-book-writer/SKILL.md','kontakt/skills/ru-book-writer/references/drafting-contract.md','kontakt/skills/ru-kontakt-series/SKILL.md','kontakt/skills/ru-kontakt-series/references/series-guide.md','kontakt/series/WORKFLOW-2026-09-23-BOOK04.md']:
 add(f)
for f in sorted((run/'structure-v1').iterdir()):
 if f.suffix in ('.md','.json') and not any(x in f.name for x in ['manifest','source-inventory','reading','self-review']):add(f)
add(rough)
for n in ['observed-state.json','proposals.json','handoff-for-terra.md','self-review.md']:
 f=run/'astra-rough-v1'/n
 if f.exists():add(f)
add(run/'root-structure-gate.json');add(run/'rough-handoff-verification.json')
for f in sorted((run/'root-rough-reading').glob('*.json')):add(f)
prev=root/'kontakt/books/book-03/production/2026-09-23-book03/terra-final-v2/assembled/manuscript.md'
assert sha(prev)=='fa99f3a2667e4ad316ad4239e39c3f4887af09d5d45a5eeb2b1c04b385ad91a6'
text=prev.read_text(encoding='utf-8');match=re.search(r'(?m)^# Розділ 28$',text);assert match;add(prev,text[match.start():])
add(prev.parent.parent/'end-state.observed.json')
for n in range(max(1,a.first-2),a.first):add(phase/f'chapters/chapter-{n:02d}.md')
for area in [phase/'states',run/'root-terra-reading']:
 for f in sorted(area.glob('chapters-*.json')):add(f)
intro=f'''You are requested model gpt-5.6-terra. Write the COMPLETE Ukrainian literary text of Kontakt BOOK4, chapters {a.first} through {a.last}. All {expected} Astra rough chapters are complete and gated. Workflow: all structure -> all Astra rough -> ALL Terra full prose -> independent reviews -> Astra reconciliation -> Terra revision -> final full reading. This is full literary authoring, not a synopsis or plan.

Read all supplied architecture, entire rough, observed preceding states and the supplied Book3 final excerpt. Do not claim to read omitted Book3 chapters. Use NO tools, browsing or agents. Root handles files and subsequent reviews. No permissions question, offer to continue or partial chapter. Finish the entire assigned block.

Realize encounters and consequential choices in full: concrete action, resistance, tactics, distinct dialogue, place and body, transitions and emotional costs. Do not compress the rough or convert scenes into 'we discussed/checked'. No filler or word-count quotas. Dal first-person past, precise engineering attention and dry selfirony, simpler after impact. Edith has her own wants and difficult choices; Rem has legitimate finite staffing responsibility and personal rivalry; Taras and Osya keep ordinary obligations and refusals. Ballast remains useful care software, home/mic restrictions survive and any new delegation is bounded.

Book4 is institutional thriller, R3->R4 only. A compatibility score forecasts coordination cost/stability; converting it to eligibility is the disputed policy use. Do not make the metric secretly measure moral worth, arbitrarily lie or equal all private budget causes. The previous book establishes comparable uncertainty, not identical inputs; intervention limit is not money spent. Osya has chosen courier work and one paid trial, not permanent employment magically restored. His old excerpts are revoked; no ambient access. Dal's old profession was suspended then voluntarily closed; a new temporary sponsor certificate is not its restoration. Skills remain real.

Edith retains home through finite manual accommodation, with real coverage and costs for the queue, not secret talent/usefulness or score manipulation. K-17 remains a living client who chooses care under constrained options; no abduction, carrier status or guessed Book5 physics. Rem is not converted by a speech. Distinguish score, role, permissions and eligibility; withdrawal does not automatically annihilate every score or the signed independent residency decision. Documentary reader-ahead insert must be visibly marked, no other person's interiority; Dal only knows it after his own receipt. No Relay mechanism, residual pool, Overload, future Taras fate or R5. Respect each card's chronology, consent and source-of-knowledge boundaries without making prose a checklist.

Natural Ukrainian and working glossary inflections. No service commentary in the novel. Working local proposals remain separate from author canon. Preserve architecture but prose must live as scenes.

Response: each chapter starts exactly '# Розділ N', blank line, plain title, blank line, complete prose. One blank line between paragraphs; no outer fences or other markdown headings. After ALL chapters append <STATE_JSON> followed by one valid JSON object then </STATE_JSON> and nothing else.

Schema: {{"reading_scope":"truthful full supplied reading and limits","chapters":[{{"chapter":N,"observed":{{"scenes":[{{"id":"exact card ID","time_basis":"planned interval versus actual named clock","quotes":["short EXACT literal quote","second exact quote"],"events":"actual events","knowledge":"who learned what from which source and limits","resources":"actual permissions, objects, access and costs","open_dependencies":[]}}]}}}}],"new_proposals":[{{"detail":"new local working choice","chapters":[N],"status":"working_implementation_not_author_canon"}}],"handoff":"actual unfinished obligations without treating later scenes as happened"}}.

Include every card scene of this block once, in order. Quotes must match your own prose literally, not reconstructed around dialogue tags. Complete prose before metadata.
'''
prompt=intro+'\n\n'.join('<SOURCE path='+json.dumps(x['path'])+' sha256='+x['sha256']+' representation='+json.dumps(x['representation'])+'>\n'+x['text']+'\n</SOURCE>' for x in refs)
out.mkdir(parents=True);(out/'prompt.md').write_text(prompt,encoding='utf-8',newline='\n')
(out/'packet.json').write_text(json.dumps({'model_requested':'gpt-5.6-terra','first':a.first,'last':a.last,'chapters_expected':expected,'prompt_bytes':len(prompt.encode()),'sources':[{k:v for k,v in x.items() if k!='text'} for x in refs]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK04-2026-09-23')
for f in [Path(__file__).resolve(),*out.iterdir()]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'first':a.first,'last':a.last,'prompt_bytes':len(prompt.encode())}))
