#!/usr/bin/env python3
"""Read-only, version-bound fiction snapshots. Standard library only."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
WORD = re.compile(r"[А-Яа-яЁёІіЇїЄєҐґA-Za-z0-9]+(?:[-’'ʼ][А-Яа-яЁёІіЇїЄєҐґA-Za-z0-9]+)*")
CHAPTER = r'(?i)^(?:#{1,6}\s+)?(?:Глава\s+|Розділ\s+|Chapter\s+|Пролог\b|Эпилог\b|Епілог\b|Prologue\b|Epilogue\b)'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_source(path, fmt):
    path = Path(path)
    zipped = zipfile.is_zipfile(path)
    if fmt == 'docx' and not zipped:
        raise ValueError('Expected real OOXML DOCX, received another byte format; do not promote a text copy silently.')
    if zipped and fmt != 'text':
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read('word/document.xml'))
            revisions = sum(len(root.findall('.//w:' + tag, NS)) for tag in
                            ['ins', 'del', 'moveFrom', 'moveTo'])
            if revisions:
                raise ValueError('Tracked revisions found; explicitly resolve the reading view before extraction.')
            body = root.find('w:body', NS)
            if body is None:
                raise ValueError('No document body found.')
            result = []
            for i, p in enumerate(body.findall('.//w:p', NS), 1):
                pieces = []
                for n in p.iter():
                    if n.tag == W + 't':
                        pieces.append(n.text or '')
                    elif n.tag == W + 'tab':
                        pieces.append('\t')
                    elif n.tag in (W + 'br', W + 'cr'):
                        pieces.append('\n')
                st = p.find('w:pPr/w:pStyle', NS)
                result.append({'p': i, 'text': ''.join(pieces),
                               'style': st.get(W + 'val', '') if st is not None else ''})
            flags = {tag: len(body.findall('.//w:' + tag, NS)) for tag in
                     ['tbl', 'drawing', 'txbxContent', 'footnoteReference', 'endnoteReference']}
            flags['excluded_parts'] = [n for n in z.namelist() if
                                       re.match(r'word/(?:header|footer|footnotes|endnotes|comments).*\.xml$', n)]
            if flags['txbxContent']:
                raise ValueError('Text boxes require a layout-aware reading order; inspect them before snapshotting.')
            return result, 'docx', flags
    if zipped:
        raise ValueError('Cannot decode a ZIP document as plain text.')
    if fmt == 'auto' and path.suffix.lower() == '.docx':
        raise ValueError('DOCX extension contains text bytes. Confirm a text copy explicitly with --format text.')
    lines = path.read_text(encoding='utf-8-sig').splitlines()
    return [{'p': i, 'text': t, 'style': ''} for i, t in enumerate(lines, 1)], 'text', {}


def metrics(paragraphs):
    texts = [p['text'] for p in paragraphs if p['text'].strip() and not p.get('is_heading')]
    tokens = WORD.findall('\n'.join(texts))
    segments = []
    for t in texts:
        segments.extend(len(WORD.findall(s)) for s in re.split(r'[.!?…]+', t) if WORD.search(s))
    counts = collections.Counter(w.lower().replace('ё', 'е') for w in tokens)
    return {'lexical_tokens': len(tokens), 'nonempty_body_paragraphs': len(texts),
            'punctuation_segments': len(segments),
            'mean_tokens_per_punctuation_segment': round(sum(segments) / len(segments), 2) if segments else None,
            'paragraphs_starting_with_dialogue_dash': sum(bool(re.match(r'^\s*[—–]\s', t)) for t in texts),
            'frequent_forms_min4chars': [[w, c] for w, c in counts.most_common() if len(w) >= 4][:35]}


def snapshot(args):
    source = Path(args.source).resolve()
    output = Path(args.out).resolve()
    if source == output:
        raise ValueError('Snapshot must not overwrite its source.')
    paragraphs, fmt, flags = read_source(source, args.format)
    pattern = re.compile(args.chapter_pattern)
    chapter_id = 0
    chapters = []
    for p in paragraphs:
        if pattern.search(p['text'].strip()):
            chapter_id += 1
            chapters.append({'chapter': chapter_id, 'title': p['text'], 'heading_p': p['p']})
            p['is_heading'] = True
        p['chapter'] = chapter_id
    data = {'schema_version': 1, 'project_id': args.project_id, 'book_id': args.book_id,
            'master': {'path': str(source), 'format': fmt, 'sha256': sha(source), 'authority': args.authority},
            'scope': 'document body; no layout, headers, footnotes, endnotes or comment review',
            'flags': flags, 'chapter_pattern': args.chapter_pattern, 'chapter_count': chapter_id,
            'paragraphs': paragraphs, 'chapters': chapters,
            'metrics': metrics([p for p in paragraphs if p['chapter'] > 0] if chapters else paragraphs),
            'metrics_method': 'Regex lexical tokens including numbers and short function words; punctuation-run segments, not linguistic sentences. No grade/quality score.'}
    for c in chapters:
        c['metrics'] = metrics([p for p in paragraphs if p['chapter'] == c['chapter']])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'out': str(output), 'sha256': data['master']['sha256'],
                      'chapters': chapter_id, 'metrics': data['metrics']}, ensure_ascii=False))


def guard(args):
    data = json.loads(Path(args.snapshot).read_text(encoding='utf-8'))
    if sha(args.source) != data['master']['sha256']:
        raise ValueError('SOURCE_HASH_CHANGED: anchors belong to a different manuscript revision.')
    anchors = json.loads(Path(args.anchors).read_text(encoding='utf-8'))
    paragraphs = {p['p']: p['text'] for p in data['paragraphs']}
    errors = []
    for i, a in enumerate(anchors, 1):
        quote = a.get('quote', '')
        count = paragraphs.get(a.get('p'), '').count(quote) if quote else 0
        if count != 1:
            errors.append({'anchor': i, 'p': a.get('p'), 'occurrences': count})
    print(json.dumps({'checked': len(anchors), 'errors': errors}, ensure_ascii=False))
    if errors:
        raise ValueError('Non-unique or absent exact anchors. Re-read the source.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    s = sub.add_parser('snapshot')
    s.add_argument('--source', required=True)
    s.add_argument('--format', choices=['auto', 'docx', 'text'], default='auto')
    s.add_argument('--project-id', required=True)
    s.add_argument('--book-id', required=True)
    s.add_argument('--authority', required=True)
    s.add_argument('--chapter-pattern', default=CHAPTER)
    s.add_argument('--out', required=True)
    g = sub.add_parser('guard')
    for key in ['source', 'snapshot', 'anchors']:
        g.add_argument('--' + key, required=True)
    args = p.parse_args()
    try:
        (snapshot if args.command == 'snapshot' else guard)(args)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
