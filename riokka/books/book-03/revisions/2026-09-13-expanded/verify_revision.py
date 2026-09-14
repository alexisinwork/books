#!/usr/bin/env python3
"""Verify the exact delivered artifacts; literary quality is not inferred here."""
import difflib
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import unicodedata
from docx import Document
import fitz
import build

R = Path(__file__).resolve().parent
B = R.parents[1]
PROJECT = B.parents[1]
ROOT = PROJECT.parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def save(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKC', s) if not c.isspace() and c != '\u00ad')


def verify():
    source = R / 'revised.md'
    digest = sha(source)
    text = source.read_text()
    assert digest == read(R / 'audit/review-status.json')['source_sha256']
    plan = read(R / 'revision_plan.json')
    original = B / 'manuscript/master.md'
    assert sha(original) == plan['original_sha256']
    assert sha(R / 'pre-audit.md') == read(R / 'changes.json')['pre_audit']['sha256']
    archived = read(R / 'archive/resumed-before-final-review.json')
    assert sha(R / archived['file']) == archived['sha256']
    assert [int(x) for x in re.findall(r'^## Глава (\d+)\.', text, re.M)] == list(range(1, 61))
    chapters = sorted((R / 'chapters').glob('[0-9][0-9].md'))
    assert len(chapters) == 60
    assembled = ['# КОНТРАКТНИК. КНИГА 3. «Холм Розмари»\n']
    index = read(R / 'derived/chapters.json')
    assert index['source_sha256'] == digest
    for n, path in enumerate(chapters, 1):
        if n in build.PARTS:
            assembled.append(f'# ЧАСТЬ {list(build.PARTS).index(n) + 1}. {build.PARTS[n]}\n')
        assembled.append(path.read_text().strip() + '\n')
        row = index['chapters'][n - 1]
        assert row['chapter'] == n and sha(path) == row['sha256']
        assert build.printed(path.read_text()) == row['printed_chars_with_spaces']
    assert '\n'.join(assembled) == text
    assert (R / 'derived/manuscript.txt').read_text() == text
    snapshot = read(R / 'derived/snapshot.json')
    assert snapshot['master']['sha256'] == digest
    assert [p['text'] for p in snapshot['paragraphs']] == text.splitlines()
    assert [p['p'] for p in snapshot['paragraphs']] == list(range(1, len(text.splitlines()) + 1))
    progress = read(R / 'progress.json')
    assert build.printed(text) == progress['printed_chars_with_spaces'] == 440324
    assert progress['author_sheets'] == 11.0081
    assert read(B / 'book.json')['working_revision']['sha256'] == digest
    assert read(R / 'continuity/scenes.json')['items'] == progress['items']
    for p in (R / 'continuity').glob('*.json'):
        assert read(p)['source_sha256'] == digest, p

    # Reconstruct the continued pass from its saved input and exact changes.
    replay = (R / archived['file']).read_text()
    edits = read(R / 'audit/resume-changes.json')['items']
    for e in edits:
        start = re.search(fr'^## Глава {e["chapter"]}\.', replay, re.M).start()
        next_ch = re.search(r'^## Глава \d+\.', replay[start + 1:], re.M)
        end = start + 1 + next_ch.start() if next_ch else len(replay)
        section = replay[start:end]
        assert section.count(e['old']) == 1, ('ambiguous journal entry', e['chapter'], e['old'])
        replay = replay[:start] + section.replace(e['old'], e['new'], 1) + replay[end:]
    assert replay == text, 'Saved exact changes do not reconstruct current text'
    for old, diff, fromfile in [(original, 'changes.diff', 'manuscript/master.md'),
                                (R / 'pre-audit.md', 'audit/proofread.diff', None),
                                (R / archived['file'], 'audit/resume.diff', None)]:
        stored = (R / diff).read_text()
        assert stored.startswith('--- ') and '\n+++ ' in stored
        # Compare the actual hunks, allowing the historical path labels.
        calculated = ''.join(difflib.unified_diff(old.read_text().splitlines(True), text.splitlines(True)))
        assert stored.splitlines(True)[2:] == calculated.splitlines(True)[2:], diff

    # Resolve every quoted anchor against its own version, including Book 2.
    paths_by_sha = {digest: source, sha(original): original}
    transition = read(R / 'audit/transition-book4.json')
    for s in transition['sources']:
        path = ROOT / s['path']
        assert sha(path) == s['sha256'], s['path']
        paths_by_sha[s['sha256']] = path
    entry = read(R / 'continuity/entry-state.json')
    prior = entry['checked_previous_book']
    prior_path = R / prior['preserved_snapshot']
    assert sha(prior_path) == prior['sha256'], 'Compared Book 2 snapshot changed'
    paths_by_sha[prior['sha256']] = prior_path
    cache = {h: p.read_text().splitlines() for h, p in paths_by_sha.items()}
    anchor_count = 0

    def walk(value, inherited=None):
        nonlocal anchor_count
        if isinstance(value, list):
            for v in value:
                walk(v, inherited)
        elif isinstance(value, dict):
            own = value.get('source_sha256') or inherited
            if 'quote' in value and ('chapter' in value or 'p' in value or 'line' in value):
                assert own in cache, ('unknown source for anchor', own, value)
                lines = cache[own]
                location = value.get('p', value.get('line'))
                quote = value['quote']
                if location:
                    assert quote in lines[location - 1], (own, location, quote)
                    if value.get('chapter'):
                        preceding = '\n'.join(lines[:location])
                        known = re.findall(r'^## Глава (\d+)\.', preceding, re.M)
                        assert known and int(known[-1]) == value['chapter'], value
                else:
                    start = next(i for i, l in enumerate(lines) if re.match(fr'^## Глава {value["chapter"]}\.', l))
                    end = next((i for i in range(start + 1, len(lines)) if re.match(r'^## Глава \d+\.', lines[i])), len(lines))
                    assert quote in '\n'.join(lines[start:end]), value
                anchor_count += 1
            for k, v in value.items():
                if isinstance(v, (dict, list)):
                    walk(v, own)

    anchor_files = list((R / 'continuity').glob('*.json')) + [R / 'progress.json', R / 'changes.json', R / 'audit/issues.json', R / 'audit/transition-book4.json', B / 'audit/issues.json']
    for p in anchor_files:
        walk(read(p))

    # Verify the DOCX and HTML reader projection independently of exporters.
    manifest = read(R / 'release.json')
    docx = R / manifest['docx']
    expected = [re.sub(r'^#{1,6} ', '', line).replace('`', '').replace('*', '').strip()
                for line in text.splitlines() if line.strip() and line.strip() != '---']
    paragraphs = [p.text for p in Document(docx).paragraphs if p.text.strip()]
    assert paragraphs == expected
    assert (R / 'derived/docx-extracted.txt').read_text().splitlines() == expected
    assert (R / 'derived/reader.txt').read_text().splitlines() == expected

    class ReaderHTML(HTMLParser):
        def __init__(self):
            super().__init__()
            self.body = False
            self.values = []
        def handle_starttag(self, tag, attrs):
            if tag == 'body':
                self.body = True
        def handle_data(self, data):
            if self.body and data.strip():
                self.values.append(data)
    parser = ReaderHTML()
    parser.feed((R / 'reader.html').read_text())
    assert parser.values == expected
    rendered = read(R / 'audit/render/verification.json')
    assert rendered['source_sha256'] == digest
    assert sha(docx) == manifest['docx_sha256'] == rendered['docx_sha256']
    pdf = R / manifest['pdf']
    assert sha(pdf) == manifest['pdf_sha256'] == rendered['pdf_sha256']
    with fitz.open(pdf) as pages:
        assert len(pages) == rendered['page_count'] == 217
        content = []
        for i, page in enumerate(pages):
            words = page.get_text('words')
            assert [w[4] for w in words if w[1] >= page.rect.height - 55] == [str(i + 1)]
            assert not [w for w in words if w[1] < page.rect.height - 55 < w[3]]
            content.append(page.get_text(clip=fitz.Rect(0, 0, page.rect.width, page.rect.height - 55)))
        assert norm('\n'.join(content)) == norm('\n'.join(expected))
    assert rendered['visual_review']['result'] == 'passed'
    assert not any(p['out_of_bounds'] or p['blank_body'] for p in rendered['all_page_bounds'])

    json_files = list(B.rglob('*.json')) + [PROJECT / 'series/continuity-queue.json', B.parent / 'book-04/audit/issues.json']
    for path in json_files:
        read(path)
    reports = []
    for command, filename in [(['python3', 'tools/studio.py', 'doctor'], 'doctor.json'),
                               (['python3', 'tools/verify_sources.py'], 'sources.json')]:
        proc = subprocess.run(command, cwd=PROJECT, capture_output=True, text=True, check=True)
        payload = json.loads(proc.stdout)
        assert not payload['errors'], payload
        save(R / 'audit' / filename, payload)
        reports.append({'command': ' '.join(command), 'cwd': 'riokka', 'file': f'audit/{filename}', 'result': 'passed',
                        'warnings': payload.get('warnings', [])})
    result = {'date': '2026-09-14', 'file': 'revised.md', 'source_sha256': digest,
              'result': 'passed', 'scope': 'Сборка, история правок, точные якоря, производные файлы, извлечение и целостность. Не оценка литературного качества.',
              'chapters': len(chapters), 'printed_chars_with_spaces': build.printed(text), 'author_sheets': 11.0081,
              'exact_anchors_checked': anchor_count, 'continued_changes_replayed': len(edits),
              'json_files_parsed': len(json_files), 'docx_paragraphs_exact': len(expected), 'pdf_pages': 217,
              'original_preserved': True, 'archive_preserved': True, 'derived_texts_exact': True,
              'cross_volume_result': 'Oren consistent; six unresolved groups in Book 4',
              'prose_review': 'audit/REPORT.md; cumulative 1–60, stated limits',
              'commands': reports,
              'remaining_questions': ['B34-01…06: согласование с томом 4.', 'B03-OPEN-STORY-FACTS: открытые сюжетные факты.', 'Авторская вычитка; новый независимый ансамбль не проводился.']}
    save(R / 'audit/technical-verification.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ['commands', 'remaining_questions']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    verify()
