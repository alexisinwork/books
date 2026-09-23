"""Native Terra owns the one residual prose correction identified by full Astra reading."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;out=run/'terra-last-stitch-packet';assert not out.exists();out.mkdir()
source=run/'terra-final-v1/assembled/manuscript.md';h=hashlib.sha256(source.read_bytes()).hexdigest()
prompt=f'''Requested gpt-5.6-terra. Bounded final prose correction B03-FINAL-01 on Kontakt Book3 source SHA {h}. You receive CH28–31 and complete final Astra report, not the full novel. No tools, agents or new plot. The full final reading found exactly one mandatory residual: in CH29 after inserted «Він прибрав свій пристрій», the next «Потім написав Тарасові...» has an ambiguous unexpressed subject. Restore explicit first-person Dal as writer. Preserve all other words, address, reply, noon time and Osya autonomy. Return ONLY JSON, no fences: {{"source_sha256":"{h}","reading_scope":"truthful bounded scope","patches":[{{"id":"B03-FINAL-01","issue_ids":["B03-FINAL-01"],"chapter":29,"before":"EXACT COMPLETE unique target paragraph","after":"same paragraph with minimal explicit narrator subject","reason":"why"}}],"state_updates":[],"omissions":[],"verification_notes":"dependent-context check, no new full reading claimed"}}.
'''
for f in [root/'STYLE.md',root/'kontakt/STYLE.md',root/'BOOK_SYSTEM/LANGUAGES/uk/STYLE.md',root/'kontakt/books/book-03/voice.json',run/'final-astra-native-v1/REPORT.md',*[run/f'terra-final-v1/chapters/chapter-{n:02d}.md' for n in range(28,32)]]:
 prompt+='\n<SOURCE path='+json.dumps(f.relative_to(root).as_posix(),ensure_ascii=False)+'>\n'+f.read_text(encoding='utf-8')+'\n</SOURCE>\n'
(out/'prompt.md').write_text(prompt,encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),out/'prompt.md']:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'source_sha256':h,'prompt_bytes':len(prompt.encode())}))
