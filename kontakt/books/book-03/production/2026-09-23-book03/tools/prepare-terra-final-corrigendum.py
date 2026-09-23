"""Prepare a bounded native Terra correction; preserve its earlier complete response."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;out=run/'terra-final-corrigendum-packet';assert not out.exists();out.mkdir()
previous=run/'terra-final-execution-v1/RESPONSE.md';data=json.loads(previous.read_text(encoding='utf-8'))
prompt='''Requested model gpt-5.6-terra. BOUNDED follow-up to the preserved full-volume Terra revision. No tools or agents. The author requires Terra to write all final prose. Return the COMPLETE previous JSON response with ONLY patch B03-P009.after and its reason corrected; every other patch, all before strings, source hash, all state_updates and omissions MUST remain byte-for-byte equal as decoded JSON values. Update reading_scope truthfully: this fresh pass receives the prior complete response plus CH06 and style, not the whole novel; full coverage belongs to the preceding recorded execution. Retain previous verification notes and append this bounded correction.

Issue: B03-P009 was intended to correct the possessive from the name Ося. The response introduced «Осинової зустрічі», which suggests an adjective Осиновий instead of the established name-derived possessive. Reconsider the natural Ukrainian construction in context; use a clear ordinary name/possessive construction without this questionable extension. Keep every other word/action/time in this patch unchanged. Do not rewrite any other patch or scene, and do not claim a fresh full-volume reread. Return only valid JSON, no fence.
'''
refs=[]
for f in [root/'STYLE.md',root/'kontakt/STYLE.md',root/'BOOK_SYSTEM/LANGUAGES/uk/STYLE.md',root/'kontakt/books/book-03/voice.json',run/'terra-full-v1/chapters/chapter-06.md',previous]:
 raw=f.read_bytes();refs.append({'path':f.relative_to(root).as_posix(),'sha256':hashlib.sha256(raw).hexdigest()});prompt+='\n<SOURCE path='+json.dumps(refs[-1]['path'])+'>\n'+raw.decode('utf-8')+'\n</SOURCE>\n'
(out/'prompt.md').write_text(prompt,encoding='utf-8',newline='\n');(out/'packet.json').write_text(json.dumps({'scope':'bounded follow-up P009; no fresh whole-volume reading','previous_response_sha256':hashlib.sha256(previous.read_bytes()).hexdigest(),'sources':refs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),*out.iterdir()]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'prompt_bytes':len(prompt.encode()),'scope':'P009 only; complete response retransmission for exact import'}))
