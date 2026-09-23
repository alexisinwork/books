"""Prepare an isolated complete-text literary packet; this does not run a review."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

p = argparse.ArgumentParser()
p.add_argument('--assembly', type=Path, required=True)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--model', required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[6]
source = a.assembly.parent / 'manuscript.md'
raw = source.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
assembly = json.loads(a.assembly.read_text(encoding='utf-8'))
assert sha == assembly['manuscript_sha256']
blocks = raw.decode('utf-8').rstrip('\n').split('\n\n')
assert len(blocks) == assembly['paragraphs']
chapters = []
for n, text in enumerate(blocks, 1):
    match = re.match(r'^# Розділ (\d+)\b', text)
    if match:
        if chapters:
            chapters[-1]['last_paragraph'] = n - 1
        chapters.append({'chapter': int(match.group(1)), 'first_paragraph': n})
assert [x['chapter'] for x in chapters] == list(range(1, assembly['through_chapter'] + 1))
chapters[-1]['last_paragraph'] = len(blocks)
neutral = Path(__file__).resolve().parent.parent / 'review-prompts/literary-neutral.md'
prompt = neutral.read_text(encoding='utf-8')
prompt += '\n\nRequested model: ' + a.model + '\nTarget SHA-256: ' + sha
prompt += '\nScope: completed full working text, chapters 1–' + str(assembly['through_chapter'])
prompt += '\nGlobal paragraph blocks: ' + str(len(blocks))
prompt += '\nChapter ranges (delivery map, not a claim of reading):\n' + json.dumps(chapters, ensure_ascii=False)
prompt += '\n\n<TARGET>\n' + '\n\n'.join(f'[P{n:05d}]\n{text}' for n, text in enumerate(blocks, 1)) + '\n</TARGET>\n'
assert not a.out.exists(), 'Freeze each packet in a new directory.'
a.out.mkdir(parents=True)
(a.out / 'prompt.md').write_text(prompt, encoding='utf-8', newline='\n')
manifest = {
    'status': 'prepared_not_executed', 'model_requested': a.model,
    'target': str(source.resolve()), 'target_sha256': sha,
    'prompt_sha256': hashlib.sha256((a.out / 'prompt.md').read_bytes()).hexdigest(),
    'prompt_bytes': len((a.out / 'prompt.md').read_bytes()),
    'paragraphs': len(blocks), 'chapters': chapters,
    'references': [], 'reading_coverage': 'not_assessed_by_packet_preparation'
}
(a.out / 'packet.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
desktop = Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for item in [Path(__file__).resolve(), *(f.resolve() for f in a.out.iterdir())]:
    target = desktop / item.relative_to(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(item, target)
print(json.dumps({k: manifest[k] for k in ['status', 'paragraphs', 'prompt_bytes', 'target_sha256']}))
