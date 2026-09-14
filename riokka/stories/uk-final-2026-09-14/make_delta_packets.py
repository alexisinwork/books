#!/usr/bin/env python3
"""Bind final micro-edits to their full-story hashes and nearby source context."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return path.read_text().rstrip('\n').split('\n\n')
def save(path,value):
    with path.open('x',encoding='utf-8') as f:
        f.write(value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)+'\n')
for name in ('space-is-no-place-for-the-living','where-ducks-fly-in-winter'):
    story=BASE/'stories'/name
    old=read(story/'reviews-r2/full-target.uk.txt')
    uk=read(story/'uk.txt')
    ru=read(story/'SOURCE/ru.txt')
    assert len(old)==len(uk)==len(ru)
    changed=[i for i,(a,b) in enumerate(zip(old,uk)) if a!=b]
    indices=sorted({j for i in changed for j in range(max(0,i-2),min(len(uk),i+3))})
    out=story/'reviews-r3/delta'
    out.mkdir(parents=True,exist_ok=False)
    for filename,text in [('uk.txt',uk),('ru.txt',ru)]:
        save(out/filename,'\n\n'.join(text[i] for i in indices)+'\n')
    save(out/'coverage.json',{'prior_full_target_sha256':sha(story/'reviews-r2/full-target.uk.txt'),
         'final_full_target_sha256':sha(story/'uk.txt'),'changed_global_paragraphs':[i+1 for i in changed],
         'local_to_global':[i+1 for i in indices], 'unchanged_paragraphs':len(uk)-len(changed),
         'scope':'Only final changed paragraphs with +/-2 body paragraphs; gaps are deliberate, not narrative transitions.'})
    save(out/'context.md','# Scope\nThese are discontinuous context windows, not a continuous story. Local P numbers map to global numbers in this list: '+str([i+1 for i in indices])+'. Do not diagnose narrative jumps across gaps.\n\n'+(story/'CONTEXT.md').read_text())
    print(name,[i+1 for i in changed])
