#!/usr/bin/env python3
"""Reproducible mechanical assembly; prose lives in editable chapter files."""
from pathlib import Path
import hashlib
import json
import re
import difflib
import shutil

R = Path(__file__).resolve().parent
B = R.parent.parent
SOURCE_SHA = '4e8b2f942d64b96fdb5a1c5396d845363bff38235b730cd20c2ed33db9e83553'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')

def plain(s):
    return re.sub(r'^#{1,6} ', '', s).replace('`', '').replace('*', '').strip()

def run():
    source = B / 'manuscript/master.md'
    assert sha(source) == SOURCE_SHA
    archive = R / 'archive'
    archive.mkdir(exist_ok=True)
    old = archive / 'book04-before.md'
    if not old.exists():
        shutil.copyfile(source, old)
    assert sha(old) == SOURCE_SHA
    chapters = R / 'chapters'
    chapters.mkdir(exist_ok=True)
    if not list(chapters.glob('*.md')):
        pieces = re.split(r'(?m)(?=^## (?:Глава |Эпилог ))', source.read_text())[1:]
        for n, piece in enumerate(pieces, 1):
            piece = re.sub(r'(?m)^# (?:ЭПИЛОГ|КОНЕЦ ТОМА 4)\s*$', '', piece).strip()
            piece = re.sub(r'\n---\s*$', '', piece).strip()
            (chapters / f'{n:03}.md').write_text(piece + '\n')
    out = ['# КОНТРАКТНИК. КНИГА 4. «Почерк без имени»']
    records = []
    for n, p in enumerate(sorted(chapters.glob('*.md')), 1):
        replacement = R / 'replacements' / p.name
        if replacement.exists():
            p = replacement
        piece = p.read_text().strip()
        if not piece:
            continue
        first, body = piece.split('\n', 1)
        title = re.sub(r'^## (?:Глава \d+\.|Эпилог [IVX]+\.)\s*', '', first)
        heading = f'## Глава {len(records) + 1}. {title}'
        content = heading + '\n' + body
        records.append({'chapter': len(records) + 1, 'key': p.stem, 'title': title,
                        'chapter_file': str(p.relative_to(R)), 'chapter_sha256': sha(p),
                        'printed_characters': sum(len(plain(x)) for x in content.splitlines() if x.strip())})
        out.append(content)
    out.append('*Конец четвёртого тома*')
    text = '\n\n'.join(out) + '\n'
    target = R / 'revised.md'
    target.write_text(text)
    digest = sha(target)
    lines = text.splitlines()
    starts = [(i + 1, s) for i, s in enumerate(lines) if s.startswith('## Глава ')]
    for row, (line, heading) in zip(records, starts):
        row['anchors'] = [{'source': 'revised.md', 'source_sha256': digest, 'line': line,
                           'quote': heading, 'verification_status': 'exact_match'}]
    printed = [plain(x) for x in lines if x.strip() and x.strip() != '---']
    derived = R / 'derived'
    derived.mkdir(exist_ok=True)
    (derived / 'manuscript.txt').write_text(text)
    (derived / 'reader.txt').write_text('\n'.join(printed) + '\n')
    chars = sum(map(len, printed))
    save(derived / 'chapters.json', {'source_sha256': digest, 'items': records})
    save(derived / 'snapshot.json', {'source': 'revised.md', 'source_sha256': digest,
        'printed_characters_with_spaces': chars, 'authors_sheets': chars / 40000,
        'count_method': 'Sum of printed paragraph lengths including spaces and headings; no markup or line separators',
        'chapters': len(records), 'status': 'working_revision'})
    (R / 'changes.diff').write_text(''.join(difflib.unified_diff(old.read_text().splitlines(True),
        text.splitlines(True), fromfile='archive/book04-before.md', tofile='revised.md')))
    save(R / 'progress.json', {'stage': 'drafting', 'source_sha256': digest,
        'chapters': len(records), 'printed_characters': chars, 'authors_sheets': chars / 40000,
        'target_range': [440000, 480000]})
    print(json.dumps({'chapters': len(records), 'characters': chars, 'sheets': chars/40000}, ensure_ascii=False))

if __name__ == '__main__':
    run()
