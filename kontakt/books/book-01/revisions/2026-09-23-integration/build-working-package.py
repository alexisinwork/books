"""Derive an exact chapter map and mechanical checks; no literary verdict."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, sys

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
a = p.parse_args()
root = Path.cwd().resolve()
source = a.source.resolve()
base = source.parent
raw = source.read_bytes()
text = raw.decode('utf-8')
sha = hashlib.sha256(raw).hexdigest()
starts = list(re.finditer(r'(?m)^# .+? (\d+)\n', text))
assert [int(m.group(1)) for m in starts] == list(range(1, 34))
assert starts[0].start() == 0
chapters = []
offset = 0
for i, m in enumerate(starts):
    chunk = text[m.start():starts[i+1].start() if i+1 < len(starts) else len(text)].encode('utf-8')
    target = base / 'chapters' / f'chapter-{i+1:02d}.md'
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(chunk)
    chapters.append({'chapter': i+1, 'source': str(target.relative_to(base)).replace('\\','/'),
                     'source_sha256': hashlib.sha256(chunk).hexdigest(), 'source_bytes': len(chunk),
                     'manuscript_byte_start': offset, 'manuscript_byte_end_exclusive': offset+len(chunk)})
    offset += len(chunk)
assert b''.join((base / c['source']).read_bytes() for c in chapters) == raw
def save(path, data):
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
save(base/'assembly.json', {'scope':'volume', 'status':'revised_working_text_not_canonical_master',
    'through_chapter':33, 'manuscript_sha256':sha, 'bytes':len(raw),
    'paragraphs':len(text.rstrip('\n').split('\n\n')), 'assembly_rule':'Exact chapter slices concatenate byte for byte',
    'chapters':chapters})
sys.path.insert(0, str(root/'tools'))
import language_qa, uk_naturalness
save(base/'language-signals.json', language_qa.check(source,'uk'))
save(base/'naturalness-signals.json', uk_naturalness.check(source))
save(base/'mechanical-verification.json', {'source_sha256':sha, 'chapter_order':'1..33',
    'exact_chapter_reassembly':True, 'replacement_character_count':text.count('\ufffd'),
    'literal_four_question_marks':text.count('????'), 'remaining_calibrovka':len(re.findall('калібров',text)),
    'scope':'UTF-8, chapter order, exact bytes and configured language patterns only; no literary quality claim'})
desktop = Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(), *base.rglob('*')]:
    if f.is_file() and '__pycache__' not in f.parts:
        dest=desktop/f.relative_to(root)
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,dest)
        assert dest.read_bytes()==f.read_bytes()
print(json.dumps({'source_sha256':sha, 'chapters':len(chapters), 'assembly':'exact', 'base':str(base)},ensure_ascii=False))
