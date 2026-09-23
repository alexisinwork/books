"""Validate a finished Astra phase against the coordinator's actual reading records."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[6]
RUN = ROOT / 'kontakt/books/book-02/production/2026-09-23-book02'
ROUGH = RUN / 'astra-rough-v1'

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

if __name__ == '__main__':
    out = RUN / 'rough-handoff-verification.json'
    assert not out.exists(), 'Preserve the existing verification; use a new run for corrections.'
    sources = sorted((ROUGH / 'chapters').glob('chapter-*.md'))
    assert [p.name for p in sources] == [f'chapter-{n:02d}.md' for n in range(1, 37)]
    coverage = {
        1: '168d50a39cbed73d58783f71b45961fc218ca0c98af96822faf029f350895397',
        2: 'b016d68ac40b9d293ec61f20c18eb12d2052860e40622ba6edf2a320120ad794'
    }
    read_records = sorted((RUN / 'root-rough-reading').glob('*.json'))
    for p in read_records:
        for item in read(p)['items']:
            n = item['chapter']
            assert n not in coverage, ('duplicate reading record', n)
            coverage[n] = item['sha256']
    assert sorted(coverage) == list(range(1, 37)), 'Actual complete coordinator reading still missing.'
    for n, p in enumerate(sources, 1):
        assert sha(p) == coverage[n], ('Source changed after recorded reading', n)
    assembly_path = ROUGH / 'assembled/assembly.json'
    assembly = read(assembly_path)
    target = assembly_path.parent / 'manuscript.md'
    volume = target.read_bytes()
    assert sha(target) == assembly['manuscript_sha256']
    assert assembly['phase'] == 'astra_rough' and assembly['through_chapter'] == 36
    for entry, p in zip(assembly['chapters'], sources, strict=True):
        assert entry['source_sha256'] == sha(p)
        assert volume[entry['manuscript_byte_start']:entry['manuscript_byte_end_exclusive']] == p.read_bytes()
    assert len(volume.decode('utf-8').rstrip('\n').split('\n\n')) == assembly['paragraphs']
    observed = read(ROUGH / 'observed-state.json')
    assert len(observed['chapters']) == 36
    scene_ids = []
    quote_count = 0
    for entry, p in zip(observed['chapters'], sources, strict=True):
        assert entry['sha256'] == sha(p)
        text = p.read_text(encoding='utf-8')
        for scene in entry['observed']['scenes']:
            scene_ids.append(scene['id'])
            assert scene.get('time_basis'), ('missing planned/observed clock distinction', scene['id'])
            for quote in scene['quotes']:
                assert quote in text, (scene['id'], quote)
                quote_count += 1
    cards_path = RUN / 'structure-v2/chapter-scene-cards.json'
    cards = read(cards_path)
    assert observed['source_cards_sha256'] == sha(cards_path)
    assert scene_ids == [s['id'] for s in cards['scenes']], 'Scene coverage changed; needs explicit adjudication.'
    for entry in read(ROUGH / 'manifest.json')['files']:
        assert sha(ROOT / entry['path']) == entry['sha256'], ('stale rough manifest', entry['path'])
    report = {
        'status': 'technical_handoff_passed_with_separate_actual_reading_records',
        'target': target.relative_to(ROOT).as_posix(), 'target_sha256': sha(target),
        'chapters': 36, 'scenes': len(scene_ids), 'paragraphs': assembly['paragraphs'],
        'observed_quotes_matched': quote_count,
        'reading_records': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in sorted((RUN / 'root-rough-reading').iterdir()) if p.is_file()],
        'checks': ['All chapter files exactly included in frozen assembly.', 'Current chapter hashes match the coordinator actual-reading records.', 'Observed quotes match their chapter sources.', 'All planned scene IDs are accounted for in order.', 'Planned clock placement has an explicit basis.', 'Frozen rough artifact manifest matches files.'],
        'limits': ['This script verifies recorded coverage, not literary quality.', 'Astra rough prose is not the complete Terra literary text.', 'Known local language and precision notes remain in the Terra handoff.', 'Independent ensemble has not yet reviewed a full Terra manuscript.', 'No author canonical promotion or publication approval is inferred.']
    }
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    desktop = Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
    for p in [out, Path(__file__).resolve()]:
        q = desktop / p.relative_to(ROOT)
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)
    print(json.dumps({k: report[k] for k in ['status', 'chapters', 'scenes', 'observed_quotes_matched', 'target_sha256']}))
