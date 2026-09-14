#!/usr/bin/env python3
"""Assemble authored chapters and bind their hand-written states to exact text.

This script does not perform or certify a literary review.
"""
import argparse
import difflib
import hashlib
import html
import json
from pathlib import Path
import re

REV = Path(__file__).resolve().parent
BOOK = REV.parents[1]
PARTS = {1: 'КУРС НА ИСТОЧНИК', 14: 'ГОРОД СВЕТА', 29: 'ЦЕНА УГЛА', 46: 'СВОД ИМЁН'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def printed(text):
    return sum(len(re.sub(r'[`*]', '', x).strip()) for x in text.splitlines()
               if x.strip() and not x.startswith('#') and x.strip() != '---'
               and x.strip() != '*Конец третьего тома.*')


def assemble():
    plan = json.loads((REV / 'revision_plan.json').read_text())
    source = BOOK / 'manuscript/master.md'
    assert digest(source.read_bytes()) == plan['original_sha256']
    notes = json.loads((REV / 'continuity/notes.json').read_text())
    by_n = {r['chapter']: r for r in notes['items']}
    paths = sorted((REV / 'chapters').glob('[0-9][0-9].md'))
    numbers = [int(p.stem) for p in paths]
    assert numbers == list(range(1, len(paths) + 1)), numbers
    chunks, index, records = ['# КОНТРАКТНИК. КНИГА 3. «Холм Розмари»\n'], [], []
    for n, p in zip(numbers, paths):
        t = p.read_text().strip() + '\n'
        assert re.match(fr'^## Глава {n}\.', t), p
        assert n in by_n, f'Missing state for chapter {n}'
        if n in PARTS:
            chunks.append(f'# ЧАСТЬ {list(PARTS).index(n) + 1}. {PARTS[n]}\n')
        chunks.append(t)
        rec = dict(by_n[n])
        rec['file'] = f'chapters/{p.name}'
        rec['chapter_sha256'] = digest(p.read_bytes())
        rec['printed_chars_with_spaces'] = printed(t)
        records.append(rec)
        index.append({'chapter': n, 'title': t.splitlines()[0], 'sha256': rec['chapter_sha256'],
                      'printed_chars_with_spaces': printed(t), 'file': rec['file']})
    full = '\n'.join(chunks)
    target = 'revised.md' if len(paths) == 60 else 'draft-in-progress.md'
    (REV / target).write_text(full)
    sha = digest(full.encode())
    paragraphs = []
    current = 0
    for p, line in enumerate(full.splitlines(), 1):
        match = re.match(r'^## Глава (\d+)\.', line)
        if match:
            current = int(match[1])
        paragraphs.append({'p': p, 'chapter': current, 'text': line})
    for rec in records:
        source_p = next(p for p in paragraphs if p['chapter'] == rec['chapter'] and p['text'].startswith('## Глава'))
        rec['source_sha256'] = sha
        rec['anchor'] = {'p': source_p['p'], 'quote': source_p['text'], 'source_sha256': sha,
                         'source': target, 'verification_status': 'exact_match'}
    save_json(REV / 'derived/snapshot.json', {'schema_version': 1, 'project_id': 'riokka', 'book_id': 'book-03',
        'master': {'path': target, 'sha256': sha, 'status': 'editorial_revision'},
        'chapter_count': len(paths), 'paragraphs': paragraphs})
    (REV / 'derived/manuscript.txt').write_text(full)
    plain = '\n'.join(re.sub(r'^#{1,6} ', '', line).replace('`', '').replace('*', '').strip()
                      for line in full.splitlines() if line.strip() and line.strip() != '---') + '\n'
    (REV / 'derived/reader.txt').write_text(plain)
    save_json(REV / 'derived/chapters.json', {'source_sha256': sha, 'chapters': index})
    save_json(REV / 'continuity/scenes.json', {'source_sha256': sha, 'status': 'editorial_revision', 'items': records})
    review_path = REV / 'audit/review-status.json'
    review = json.loads(review_path.read_text()) if review_path.exists() else {}
    review_current = review.get('source_sha256') == sha
    save_json(REV / 'progress.json', {'source_sha256': sha, 'original_sha256': plan['original_sha256'],
        'previous_book_sha256': plan['previous_book_sha256'], 'file': target,
        'chapters_written': len(paths), 'printed_chars_with_spaces': printed(full),
        'author_sheets': printed(full) / 40000, 'items': records,
        'full_review': review.get('result') if review_current else 'pending_current_version',
        'status': 'editorial_revision_for_author_review' if review_current else 'in_progress'})
    change = ''.join(difflib.unified_diff(source.read_text().splitlines(True), full.splitlines(True),
        fromfile='manuscript/master.md', tofile=target))
    (REV / 'changes.diff').write_text(change)
    print(json.dumps({'file': target, 'chapters': len(paths), 'printed_chars': printed(full),
                      'author_sheets': printed(full)/40000, 'sha256': sha}, ensure_ascii=False))


if __name__ == '__main__':
    assemble()
