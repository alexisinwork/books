#!/usr/bin/env python3
"""Create immutable, scene-bounded QA packets; prove exact full-text coverage."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path, text):
    with path.open('x', encoding='utf-8') as f:
        f.write(text)

def main():
    for name in ('history', 'space-is-no-place-for-the-living', 'where-ducks-fly-in-winter'):
        story = BASE / 'stories' / name
        uk = (story / 'uk.txt').read_text().rstrip('\n').split('\n\n')
        ru = (story / 'SOURCE/ru.txt').read_text().rstrip('\n').split('\n\n')
        assert len(uk) == len(ru)
        start_indices = [i for i, p in enumerate(uk) if p.startswith('<b>') and p.endswith('</b>')]
        starts = sorted({0, *start_indices, len(uk)})
        scenes = [(a, b) for a, b in zip(starts, starts[1:])]
        groups = []
        for a, b in scenes:
            size = len(('\n\n'.join(uk[a:b]) + '\n\n'.join(ru[a:b])).encode('utf-8'))
            if size > 95000:
                raise ValueError(f'Scene too large: {name} {a}:{b}; split with an explicit semantic map')
            if groups and groups[-1][2] + size < 95000:
                groups[-1] = (groups[-1][0], b, groups[-1][2] + size)
            else:
                groups.append((a, b, size))
        root = story / 'reviews-r2'
        root.mkdir(exist_ok=False)
        write(root / 'full-target.uk.txt', '\n\n'.join(uk) + '\n')
        manifest = {'full_target_sha256': sha(story/'uk.txt'), 'full_source_sha256': sha(story/'SOURCE/ru.txt'),
                    'paragraph_count': len(uk), 'parts': [], 'rule': 'No paragraph omitted/duplicated/reordered; packet-local P0001 maps to global_start.'}
        context = (story / 'CONTEXT.md').read_text()
        if name == 'history':
            context = context.replace('Наташа', 'Наталка').replace('Наташі', 'Наталці')
            context += '\nНаталка — розмовна форма поточної української редакції; попередні українські імена не були окремо затверджені автором. Не нав\'язувати російську форму лише через її написання у RU.\n'
        for n, (a, b, size) in enumerate(groups, 1):
            part = root / f'part-{n:02d}'
            part.mkdir()
            for filename, values in (('uk.txt', uk), ('ru.txt', ru)):
                write(part/filename, '\n\n'.join(values[a:b])+'\n')
            local_context = f'# Scope metadata\nGlobal paragraphs {a+1}–{b} of {len(uk)}. Local P0001 = global P{a+1:04d}. This packet is not the whole story.\n\n'+context
            write(part/'context.md', local_context)
            manifest['parts'].append({'part': part.name, 'global_start': a+1, 'global_end': b, 'paragraphs': b-a,
                                      'uk_sha256': sha(part/'uk.txt'), 'ru_sha256': sha(part/'ru.txt'), 'bytes': size})
        assert [p for a,b,_ in groups for p in uk[a:b]] == uk
        assert [p for a,b,_ in groups for p in ru[a:b]] == ru
        write(root/'coverage.json', json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        print(name, [(a+1,b,size) for a,b,size in groups])

if __name__ == '__main__':
    main()
