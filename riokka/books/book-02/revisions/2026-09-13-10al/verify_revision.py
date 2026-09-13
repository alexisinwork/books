#!/usr/bin/env python3
"""Check this revision's files and exact anchors; does not certify literary quality."""
import difflib
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re

REV = Path(__file__).resolve().parent
ROOT = REV.parents[4]
BOOK = REV.parents[1]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def printed_count(text):
    return sum(len(line.replace('`', '').replace('**', '').strip()) for line in text.splitlines()
               if line.strip() and not re.match(r'^#{1,6} ', line)
               and not re.fullmatch(r'[-* ]{3,}', line) and line != '*Конец второго тома.*')


class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_main = False
        self.blocks = []
        self.current = None
        self.ids = []

    def handle_starttag(self, tag, attrs):
        if tag == 'main':
            self.in_main = True
        if self.in_main and tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self.current = []
        if tag == 'h2':
            self.ids.append(dict(attrs).get('id'))
        if self.in_main and tag == 'br' and self.current is not None:
            self.current.append('\n')

    def handle_data(self, data):
        if self.in_main and self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'] and self.current is not None:
            self.blocks.append(''.join(self.current))
            self.current = None
        if tag == 'main':
            self.in_main = False


def main():
    source = BOOK / 'manuscript/master.md'
    revised = REV / 'revised.md'
    text = revised.read_text()
    digest = sha(revised)
    progress = json.loads((REV / 'progress.json').read_text())
    assert progress['source_sha256'] == digest
    assert sha(source) == progress['original_sha256']
    assert sha(ROOT / 'riokka/books/book-01/manuscript/master.docx') == progress['previous_book_sha256']
    assert printed_count(text) == progress['printed_chars_with_spaces'] >= 400000
    assert [int(n) for n in re.findall(r'^## Глава (\d+)\.', text, re.M)] == list(range(1, 52))
    assert len(progress['items']) == 51
    assert not re.search(r'\b(?:TODO|FIXME|UNRESOLVED|TBD|Джулиий|Кей)\b', text)
    diff = ''.join(difflib.unified_diff(source.read_text().splitlines(True), text.splitlines(True),
        fromfile='manuscript/master.md', tofile='revisions/2026-09-13-10al/revised.md'))
    assert diff == (REV / 'changes.diff').read_text()
    snapshot = json.loads((REV / 'derived/snapshot.json').read_text())
    assert snapshot['master']['sha256'] == digest and snapshot['chapter_count'] == 51
    assert '\n'.join(p['text'] for p in snapshot['paragraphs']) + '\n' == text
    assert (REV / 'derived/manuscript.txt').read_text() == text
    plain = '\n'.join(re.sub(r'^#{1,6} ', '', line).replace('`', '').replace('**', '') for line in text.splitlines()) + '\n'
    assert (REV / 'derived/reader.txt').read_text() == plain
    anchors_checked = 0
    by_line = {p['p']: p['text'] for p in snapshot['paragraphs']}
    b1 = json.loads((ROOT / 'riokka/books/book-01/derived/snapshot.json').read_text())
    b1_lines = {p['p']: p['text'] for p in b1['paragraphs']}

    def walk(value):
        nonlocal anchors_checked
        if isinstance(value, dict):
            if 'quote' in value and 'p' in value and 'source_sha256' in value:
                if value['source_sha256'] == digest:
                    assert by_line[value['p']].count(value['quote']) == 1, value
                    anchors_checked += 1
                elif value['source_sha256'] == progress['previous_book_sha256']:
                    assert b1_lines[value['p']].count(value['quote']) == 1, value
                    anchors_checked += 1
            for v in value.values():
                walk(v)
        elif isinstance(value, list):
            for v in value:
                walk(v)

    json_files = list(REV.rglob('*.json'))
    for path in json_files:
        walk(json.loads(path.read_text()))
    parsed = Reader()
    parsed.feed((REV / 'reader.html').read_text())
    expected = []
    for block in text.strip().split('\n\n'):
        if re.fullmatch(r'[-*\s]+', block):
            continue
        b = re.sub(r'^#{1,6} ', '', block).replace('`', '').replace('**', '')
        expected.append('Конец второго тома.' if b == '*Конец второго тома.*' else b)
    assert parsed.blocks == expected, 'HTML reading text differs'
    assert parsed.ids == [f'chapter-{n}' for n in range(1, 52)]
    book = json.loads((BOOK / 'book.json').read_text())
    assert book['working_revision']['sha256'] == digest
    assert book['master']['sha256'] == sha(source)
    scenes = json.loads((REV / 'continuity/scenes.json').read_text())
    by_id = {item['id']: item for item in scenes['items']}
    assert len(by_id) == len(progress['items']) == 51
    for item in progress['items']:
        for key in ['pov', 'state_before', 'state_after', 'new_proposals', 'reason']:
            assert item[key] == by_id[item['id']][key], (item['id'], key)
    changes = json.loads((REV / 'changes.json').read_text())
    for item in changes['items']:
        assert item['reason'] == by_id[item['id']]['reason']
    issues = json.loads((REV / 'audit/issues.json').read_text())
    unresolved = [item['id'] for item in issues['items'] if item['resolution_status'] == 'unresolved']
    release = json.loads((REV / 'release.json').read_text())
    assert release['remaining_decisions'] == unresolved
    for item in release['files']:
        assert sha(REV / item['file']) == item['sha256']
    root_issues = json.loads((BOOK / 'audit/issues.json').read_text())
    assert root_issues['working_revision_audit']['open_issue_ids'] == unresolved
    # Detect stale chapter hashes using canonical slices of the saved manuscript.
    chunks = re.split(r'(?m)(?=^## Глава \d+\.)', text)[1:]
    index = json.loads((REV / 'derived/chapters.json').read_text())
    for chunk, chapter in zip(chunks, index['chapters']):
        assert hashlib.sha256(chunk.encode()).hexdigest() == chapter['sha256']
        assert printed_count(chunk) == chapter['printed_chars_with_spaces']
    result = {'source_sha256': digest, 'printed_chars_with_spaces': printed_count(text),
              'author_sheets': printed_count(text) / 40000, 'chapters': 51,
              'json_files': len(json_files), 'exact_anchors_checked': anchors_checked,
              'diff': 'passed', 'source_integrity': 'passed', 'text_exports': 'passed',
              'chapter_hashes': 'passed', 'metadata_dependencies': 'passed',
              'unresolved_issues': unresolved, 'literary_quality': 'not assessed by this script'}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
