#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json

BASE=Path(__file__).resolve().parent
story=BASE/'stories/space-is-no-place-for-the-living'
out=story/'reviews-r4/ending'
out.mkdir(parents=True,exist_ok=False)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,s):
    with p.open('x',encoding='utf-8') as f: f.write(s)
for language,src in [('ru',story/'SOURCE/ru.complete.txt'),('uk',story/'uk.txt')]:
    values=src.read_text().rstrip('\n').split('\n\n')
    assert len(values)==264
    save(out/f'{language}.txt','\n\n'.join(values[244:])+'\n')
save(out/'coverage.json',json.dumps({'complete_global_indices':list(range(245,265)),
    'full_source_sha256':sha(story/'SOURCE/ru.complete.txt'),
    'final_full_target_sha256':sha(story/'uk.txt'),
    'scope':'Continuous final 20 paragraphs. Includes all four Смоулі spellings and both paragraphs previously hidden in body content controls.'},ensure_ascii=False,indent=2)+'\n')
save(out/'context.md','# Scope\nThe continuous ending of a science-fiction story. Local paragraphs 1–20 map to complete global 245–264. This is an excerpt, not a complete story; do not invent missing earlier scenes. Assess fidelity and natural Ukrainian without rewriting the fictional technology. The editor has author-delegated permission for local corrections.\n')
