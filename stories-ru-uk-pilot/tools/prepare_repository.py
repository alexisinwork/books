#!/usr/bin/env python3
"""Copy four existing project folders into a new repository working directory.

No network or account writes. Original file bytes are copied unchanged. Python 3.10+.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile


def prepare(args):
    sources = {name: Path(getattr(args, name)).resolve()
               for name in ['default', 'buro', 'kontakt', 'riokka']}
    out = Path(args.out).resolve()
    if out.exists():
        raise ValueError('Output already exists; choose a new folder.')
    ids = set()
    for name, src in sources.items():
        if not (src / 'project.json').is_file():
            raise ValueError('Missing project.json: ' + str(src))
        if out.is_relative_to(src) or src.is_relative_to(out):
            raise ValueError('Output and source trees must not contain one another.')
        if any(p.is_symlink() for p in src.rglob('*')):
            raise ValueError('Source symlinks need explicit handling before copying: ' + name)
        manifest = json.loads((src / 'project.json').read_text(encoding='utf-8'))
        if manifest['project_id'] in ids:
            raise ValueError('Project IDs must be different across all four folders.')
        ids.add(manifest['project_id'])
        if name == 'default' and (manifest.get('books') or manifest.get('kind') != 'boilerplate'):
            raise ValueError('Use a clean default template with no existing books.')
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='repository-stage-', dir=out.parent))
    ignore = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.DS_Store',
                                    '.openai-download-*', '*.openai-download-*')
    try:
        for name, src in sources.items():
            shutil.copytree(src, staging / name, ignore=ignore)
        (staging / '.github/workflows').mkdir(parents=True)
        shutil.copy2(sources['default'] / 'integrations/combined-validate.yml',
                     staging / '.github/workflows/validate.yml')
        for name in ['.gitignore', '.gitattributes']:
            shutil.copy2(sources['default'] / name, staging / name)
        (staging / 'README.md').write_text('''# Писательская мастерская

Четыре самостоятельные папки: default — чистый шаблон; buro, kontakt, riokka — проекты серий. Начните со START_HERE.md выбранного проекта. Книги размещены в его books/.

Для нового мира используйте default/tools/studio.py new-project; для нового тома — tools/studio.py new-book из папки серии. Профили, канон и состояния книг разделены по проектам.

Каталог подготовлен локально. Он сам не создаёт репозиторий в GitHub или папки в Drive. Для размещения и ежедневной работы см. default/guides/DRIVE-AND-GITHUB.md. Не назначайте весь репозиторий шаблоном: он содержит авторские рукописи.
''', encoding='utf-8')
        if out.exists():
            raise ValueError('Output appeared during preparation; no files were replaced.')
        staging.rename(out)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return {'prepared': str(out), 'folders': list(sources), 'github_created': False,
            'intended_visibility': 'private'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['default', 'buro', 'kontakt', 'riokka', 'out']:
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
