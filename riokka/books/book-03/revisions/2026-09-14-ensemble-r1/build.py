#!/usr/bin/env python3
"""Assemble the 2026-09-14 ensemble revision of Book 3 from chapter files.

Binds per-chapter state notes to exact headings and writes derived extracts.
Literary quality is not certified by this script.
"""
import difflib, hashlib, json, re
from pathlib import Path

REV = Path(__file__).resolve().parent
BOOK = REV.parents[1]
PREV = REV.parent / '2026-09-13-expanded' / 'revised.md'
PREV_SHA = '353360345b999d66f5e12b6a5fa2d871c4e7c4a9247414a265894e6439141cdd'
ORIGINAL_SHA = '9c3e242da0d512b851531cf94c1941aae7eabb2f236ea19f409b6f139d0bf76d'
PARTS = {1: 'КУРС НА ИСТОЧНИК', 13: 'ГОРОД СВЕТА', 28: 'ЦЕНА УГЛА', 44: 'СВОД ИМЁН'}
COUNT = 58


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
    assert digest(PREV.read_bytes()) == PREV_SHA
    notes = json.loads((REV / 'continuity/notes.json').read_text())
    by_n = {r['chapter']: r for r in notes['items']}
    paths = sorted((REV / 'chapters').glob('[0-9][0-9].md'))
    assert [int(p.stem) for p in paths] == list(range(1, COUNT + 1))
    chunks, index, records = ['# КОНТРАКТНИК. КНИГА 3. «Холм Розмари»\n'], [], []
    for p in paths:
        n = int(p.stem)
        t = p.read_text().strip() + '\n'
        assert re.match(fr'^## Глава {n}\.', t), p
        if n in PARTS:
            chunks.append(f'# ЧАСТЬ {list(PARTS).index(n) + 1}. {PARTS[n]}\n')
        chunks.append(t)
        rec = dict(by_n[n])
        rec['file'] = f'chapters/{p.name}'
        rec['chapter_sha256'] = digest(p.read_bytes())
        rec['printed_chars_with_spaces'] = printed(t)
        records.append(rec)
        index.append({'chapter': n, 'title': t.splitlines()[0], 'sha256': rec['chapter_sha256'],
                      'printed_chars_with_spaces': rec['printed_chars_with_spaces'], 'file': rec['file']})
    full = '\n'.join(chunks)
    (REV / 'revised.md').write_text(full)
    sha = digest(full.encode())
    lines = full.splitlines()
    paragraphs, current = [], 0
    for i, line in enumerate(lines, 1):
        m = re.match(r'^## Глава (\d+)\.', line)
        if m:
            current = int(m[1])
        paragraphs.append({'p': i, 'chapter': current, 'text': line})
    for rec in records:
        head = next(x for x in paragraphs if x['chapter'] == rec['chapter'] and x['text'].startswith('## Глава'))
        rec['source_sha256'] = sha
        rec['anchor'] = {'source': 'revised.md', 'source_sha256': sha, 'chapter': rec['chapter'],
                         'p': head['p'], 'quote': head['text'], 'verification_status': 'exact_match'}
    save_json(REV / 'derived/snapshot.json', {'schema_version': 1, 'project_id': 'riokka', 'book_id': 'book-03',
        'master': {'path': 'revised.md', 'sha256': sha, 'status': 'ensemble_revision'},
        'chapter_count': COUNT, 'paragraphs': paragraphs})
    (REV / 'derived/manuscript.txt').write_text(full)
    plain = '\n'.join(re.sub(r'^#{1,6} ', '', l).replace('`', '').replace('*', '').strip()
                      for l in lines if l.strip() and l.strip() != '---') + '\n'
    (REV / 'derived/reader.txt').write_text(plain)
    save_json(REV / 'derived/chapters.json', {'source_sha256': sha, 'chapters': index})
    save_json(REV / 'continuity/scenes.json', {'source_sha256': sha, 'status': 'ensemble_revision_for_author_review', 'items': records})
    diff = ''.join(difflib.unified_diff(PREV.read_text().splitlines(True), full.splitlines(True),
                   fromfile='revisions/2026-09-13-expanded/revised.md', tofile='revisions/2026-09-14-ensemble-r1/revised.md'))
    (REV / 'changes.diff').write_text(diff)
    pc = printed(full)
    save_json(REV / 'progress.json', {'source_sha256': sha, 'previous_revision_sha256': PREV_SHA,
        'original_sha256': ORIGINAL_SHA, 'chapters': COUNT, 'printed_chars_with_spaces': pc,
        'author_sheets': pc / 40000, 'previous_printed_chars_with_spaces': printed(PREV.read_text())})
    print(json.dumps({'chapters': COUNT, 'printed_chars': pc, 'author_sheets': round(pc / 40000, 4),
                      'previous_printed': printed(PREV.read_text()), 'sha256': sha}, ensure_ascii=False))


if __name__ == '__main__':
    assemble()
