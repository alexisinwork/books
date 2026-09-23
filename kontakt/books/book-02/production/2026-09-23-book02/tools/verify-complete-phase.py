"""Verify a complete literary phase's source and state dependencies, not its quality."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

p = argparse.ArgumentParser()
p.add_argument('--phase-dir', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[6]
run = Path(__file__).resolve().parent.parent
phase = a.phase_dir.resolve()

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert not a.out.exists(), 'Use a new verification file; preserve previous evidence.'
assembly_path = phase / 'assembled/assembly.json'
assembly = read(assembly_path)
source = assembly_path.parent / 'manuscript.md'
raw = source.read_bytes()
assert sha(source) == assembly['manuscript_sha256']
assert assembly['phase'] in ('terra_full', 'terra_revised')
assert assembly['through_chapter'] == 36
assert b'\r' not in raw
text = raw.decode('utf-8')
assert '\ufffd' not in text and '????' not in text
assert len(text.rstrip('\n').split('\n\n')) == assembly['paragraphs']
assert re.findall(r'(?m)^# Розділ (\d+)$', text) == [str(n) for n in range(1, 37)]
files = sorted((phase / 'chapters').glob('chapter-*.md'))
assert [f.name for f in files] == [f'chapter-{n:02d}.md' for n in range(1, 37)]
for entry, f in zip(assembly['chapters'], files, strict=True):
    assert entry['source_sha256'] == sha(f)
    assert raw[entry['manuscript_byte_start']:entry['manuscript_byte_end_exclusive']] == f.read_bytes()

state = read(phase / 'observed-state.json')
assert len(state['chapters']) == 36
scene_ids = []
quotes = 0
for item, f in zip(state['chapters'], files, strict=True):
    assert item['sha256'] == sha(f), ('stale state', f.name)
    chapter_text = f.read_text(encoding='utf-8')
    for scene in item['observed']['scenes']:
        scene_ids.append(scene['id'])
        assert scene.get('time_basis'), ('clock basis missing', scene['id'])
        for quote in scene['quotes']:
            assert quote in chapter_text, ('quote mismatch', scene['id'], quote)
            quotes += 1
cards_path = run / 'structure-v2/chapter-scene-cards.json'
assert scene_ids == [scene['id'] for scene in read(cards_path)['scenes']]

rough = run / 'astra-rough-v1/chapters'
unchanged = [n for n, f in enumerate(files, 1)
             if f.read_text(encoding='utf-8').strip() == (rough / f.name).read_text(encoding='utf-8').strip()]
assert not unchanged, ('Entire rough chapters relabeled as full text; inspect intent', unchanged)
report = {
    'status': 'technical_phase_integrity_passed_not_literary_verdict',
    'source': source.relative_to(root).as_posix(),
    'source_sha256': sha(source), 'phase': assembly['phase'],
    'chapters': 36, 'scenes': len(scene_ids), 'paragraphs': assembly['paragraphs'],
    'matched_state_quotes': quotes,
    'structure_cards_sha256': sha(cards_path),
    'checks': ['Complete ordered UTF-8/LF source.', 'All chapter byte slices match the assembly.',
               'State hashes and quotes match their chapters.', 'All planned scene IDs retained in order.',
               'Every chapter differs from its rough predecessor.'],
    'limits': ['Different bytes do not establish literary development.',
               'Quotes and hashes do not establish a complete prose reading.',
               'Independent source-bound reviews and architecture reconciliation remain separate.',
               'No canonical promotion or author approval is inferred.']
}
a.out.parent.mkdir(parents=True, exist_ok=True)
a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
desktop = Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(), a.out.resolve()]:
    dest = desktop / f.relative_to(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(f, dest)
print(json.dumps({key: report[key] for key in ['status', 'source_sha256', 'chapters', 'scenes', 'matched_state_quotes']}))
