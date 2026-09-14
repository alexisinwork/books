#!/usr/bin/env python3
"""Append complete source projections without replacing the earlier snapshots."""
from pathlib import Path
import hashlib
import json
import sys
from docx import Document

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE/'tools'))
import revise_docx_text as edit

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    folder = BASE/'stories/space-is-no-place-for-the-living'
    manifest = {'reason':'Two body paragraphs inside block content controls were absent from the old direct-paragraph projection. Frozen DOCX originals are unchanged.',
                'previous_direct_units':262, 'complete_units':264, 'added_complete_indices':[261,263],
                'old_to_complete':{str(n):n if n<=260 else n+1 if n==261 else n+2 for n in range(1,263)},
                'files':[]}
    for role in ('ru','desktop-uk'):
        source = folder/'SOURCE'/f'{role}.docx'
        output = folder/'SOURCE'/f'{role}.complete.txt'
        edit.extract(source,output)
        manifest['files'].append({'role':role,'path':str(output.relative_to(folder)),
                                  'sha256':sha(output),'source_docx_sha256':sha(source)})
    doc = Document(folder/'SOURCE/desktop-uk.docx')
    direct = {p._p for p in doc.paragraphs}
    old = iter(edit.read_projection(folder/'SOURCE/prepared-uk.txt'))
    values = [next(old) if p._p in direct else edit.marked_text(p)
              for p in edit.body_paragraphs(doc) if p.text.strip()]
    assert next(old,None) is None and len(values)==264
    output = folder/'SOURCE/prepared-uk.complete.txt'
    with output.open('x',encoding='utf-8') as f:
        f.write('\n\n'.join(values)+'\n')
    manifest['files'].append({'role':'prepared-uk','path':str(output.relative_to(folder)),
                              'sha256':sha(output),'original_prepared_sha256':sha(folder/'SOURCE/prepared-uk.txt'),
                              'note':'The two previously unprojected Russian paragraphs are inserted verbatim from the frozen desktop DOCX, not claimed as previously translated.'})
    with (folder/'complete-projection-manifest.json').open('x',encoding='utf-8') as f:
        json.dump(manifest,f,ensure_ascii=False,indent=2)
        f.write('\n')

if __name__=='__main__':
    main()
