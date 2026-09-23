"""Prepare a source-complete Terra writing block; never a literary review."""
from pathlib import Path
import argparse, hashlib, json, re, shutil

p=argparse.ArgumentParser()
p.add_argument('--first', type=int, required=True)
p.add_argument('--last', type=int, required=True)
a=p.parse_args()
root=Path(__file__).resolve().parents[6]
run=Path(__file__).resolve().parent.parent
phase=run/'terra-full-v2'
out=phase/'packets'/f'chapters-{a.first:02d}-{a.last:02d}'
assert 1<=a.first<=a.last<=36 and not out.exists()
refs=[]
def add(path, text=None):
    f=root/path if not Path(path).is_absolute() else Path(path)
    raw=f.read_bytes()
    refs.append({'path':f.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode('utf-8') if text is None else text})
for path in ['AGENTS.md','STYLE.md','BOOK_SYSTEM/CORE.md','BOOK_SYSTEM/LANGUAGES/uk/STYLE.md',
             'BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md','kontakt/AGENTS.md','kontakt/STYLE.md',
             'kontakt/project.json','kontakt/books/book-02/book.json','kontakt/books/book-02/brief.md',
             'kontakt/books/book-02/voice.json','kontakt/books/book-02/characters.planned.json',
             'kontakt/series/CANON-POLICY.md','kontakt/series/canon.json','kontakt/series/glossary.json','kontakt/skills/ru-book-writer/SKILL.md',
             'kontakt/skills/ru-book-writer/references/drafting-contract.md',
             'kontakt/skills/ru-kontakt-series/SKILL.md','kontakt/skills/ru-kontakt-series/references/series-guide.md',
             'kontakt/series/WORKFLOW-2026-09-23-REVISION-AND-BOOK02.md']:
    add(path)
for name in ['full-outline.md','chapter-scene-cards.json','carry-in-source-lock.json','knowledge.planned.json',
             'resources.planned.json','promises.planned.json','timeline.planned.json','voices-and-glossary.md','decisions-and-questions.json']:
    add(run/'structure-v2'/name)
for name in ['assembled/manuscript.md','handoff-for-terra.md','terra-review-notes.json']:
    add(run/'astra-rough-v1'/name)
book1=root/'kontakt/books/book-01/revisions/2026-09-23-author-revision-v4/manuscript.md'
raw=book1.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='32d70ac6e9dc3c523ee7a8fcd38db28f26aa77d5cd1908fa19f8eeb51f61b89f'
text=raw.decode('utf-8')
match=re.search(r'(?m)^# .*31\b',text)
assert match
add(book1,text[match.start():])
for n in range(max(1,a.first-2),a.first):
    add(phase/'chapters'/f'chapter-{n:02d}.md')
for f in sorted((phase/'states').glob('*.json')):
    add(f)
intro=f'''You are Terra, requested model gpt-5.6-terra, writing the FULL UKRAINIAN LITERARY TEXT of Kontakt book2. This is AUTHORING, not a review, outline, progress report or summary. The author's explicit workflow: Astra full structure -> Astra all rough chapters -> Terra full prose of all chapters -> four independent literary diagnoses -> Astra reconciliation -> Terra final revision. Structure and all36 rough chapters are finished. This call writes the complete literary block CH{a.first:02d}–CH{a.last:02d}. Other blocks are coordinated separately; do not stop before completing this block.

Read ALL supplied architecture and the ENTIRE36-chapter rough before writing. Use the given chronological scene states, never the ending as early knowledge. The source book1 excerpt is the verified outgoing working version; the whole original is not supplied and you must not claim reading it. The previous full Terra chapters/states, if present, are binding continuity for this version. Do not reuse any failed shortened Terra-v1 attempt: none is a source here.

Use no tools, filesystem access, browsing, subagents or external files. All necessary source material is inline. Repository workflow instructions are context; root handles file writes, mirrors, Git and later reviews. They do not require you to end with a plan. Your final response MUST contain the completed prose itself, then the state record below, without introductions, apologies, offers to continue, word-count promises or status-only answers.

Write the scenes at full novel scale: embodied action, specific friction, changing tactics, distinct voices, emotional resistance and consequences. The rough is already concise; do not summarize or compress its scenes into a shorter retelling. Preserve the causal events and knowledge timing while developing lived scenes. You may cut redundant explanations, but cannot replace an enacted encounter by 'we checked/discussed/agreed'. Do not pad scenes with repeated permission checklists, generic atmosphere or morals. No numerical word quota; the unit is a fully realized scene. Important ordinary work must actually happen on the page. The last chapter of this block deserves the same care as the first.

Dal first person past tense; lively ensemble, engineering perception, dry domestic humour. Ukrainian idiomatic prose. No raw English 'relay': local ретранслятор/вузол, not legacy human Релей. Ballast manually invoked and limited to supplied information, home access remains off without disabling household safety sensors. Keep five unresolved questions unresolved. R1→R2 only; no mindreading or later-volume mechanisms. Do not make Ira endangered/rescued, Vector a secret agent, Lana a caricature, Taras an omniscient mentor. Characters can be mistaken; narratorial claims must reflect available evidence. New mundane details are working proposals, not author canon.

CH01 must make the planned interval after Book1 understandable without inventing an author-approved date; show actual parcel-checking error/correction and lost paid job. CH03 accounts for the different six examples without becoming a numbered report. Exact authorial rough corrections and later payoffs in the handoff must remain.

Response format: Each chapter begins exactly '# Розділ N', blank line, plain chapter title, blank line, complete prose. No other markdown headings. One blank line between prose paragraphs. Preserve DOC01 at the start of CH17 before its narrative; it belongs to the reader, not Dal's knowledge. After the LAST completed chapter only, append a line <STATE_JSON>, valid JSON, then </STATE_JSON>. This metadata is NOT part of the novel.

State JSON: {{"reading_scope":"truthful actual supplied reading and any unavailable ranges", "chapters":[{{"chapter":N,"observed":{{"scenes":[{{"id":"exact planned scene ID","time_basis":"planned interval versus clock actually named","quotes":["two short EXACT quotations from your new chapter"],"events":"actually enacted","knowledge":"what each participant now knows and through what source","resources":"actual changes and permissions","open_dependencies":[]}}]}}}}],"new_proposals":[{{"detail":"new working detail","chapters":[N],"status":"working_implementation_not_author_canon"}}],"handoff":"specific continuing obligations, not a plot summary"}}. Include every planned scene of this block exactly once in order; quotations must be literal in your own delivered prose. No claims of independent review or publication readiness.

For metadata, quotes are literal substrings: do not add quotation-mark wrappers inside JSON strings, do not move dialogue punctuation, and do not join speech across an intervening narrator tag. Validate JSON braces mentally: each chapter has exactly one observed object containing its scenes array. Preserve the prose separately from metadata.

<SOURCES>
'''
prompt=intro+'\n\n'.join('<SOURCE path='+json.dumps(r['path'],ensure_ascii=False)+' sha256='+r['sha256']+'>\n'+r['text']+'\n</SOURCE>' for r in refs)+'\n</SOURCES>\n\nNow deliver ALL full literary chapters '+str(a.first)+'–'+str(a.last)+' followed by their state JSON. Do not deliver a report about starting them.\n'
out.mkdir(parents=True)
(out/'prompt.md').write_text(prompt,encoding='utf-8',newline='\n')
manifest={'role':'authoring','model_requested':'gpt-5.6-terra','first':a.first,'last':a.last,'prompt_bytes':len(prompt.encode()),'sources':[{k:v for k,v in r.items() if k!='text'} for r in refs],'source_reading':'input delivery only; actual reading must be reported by writer'}
(out/'packet.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),*out.iterdir()]:
    q=desktop/f.relative_to(root);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,q)
print(json.dumps({k:manifest[k] for k in ['role','model_requested','first','last','prompt_bytes']}))
