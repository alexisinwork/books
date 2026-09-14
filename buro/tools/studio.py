#!/usr/bin/env python3
"""Portable book workspace tools; Python 3.10+, standard library only."""
import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=path.parent, delete=False) as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
        temp = Path(f.name)
    temp.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inside(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('Expected a nonempty relative path')
    root = Path(root).resolve()
    result = (root / relative).resolve()
    if not result.is_relative_to(root) or result == root:
        raise ValueError('Path escapes its project: ' + relative)
    return result


def slug(value):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
        raise ValueError('ID must use lowercase ASCII letters, numbers and internal hyphens')
    return value


def project(root):
    root = Path(root).resolve()
    return root, read(root / 'project.json')


def get_book(root, book_id):
    root, p = project(root)
    matches = [b for b in p['books'] if b['id'] == book_id]
    if len(matches) != 1:
        raise ValueError('Book ID is missing or not unique: ' + book_id)
    bp = inside(root, matches[0]['path'])
    return root, p, bp, read(bp / 'book.json')


def snapshot_module(root):
    path = root / 'skills/ru-book-auditor/scripts/book_snapshot.py'
    spec = importlib.util.spec_from_file_location('book_snapshot_local', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def checked_master(bp, book, allow_candidate=False):
    master = book['master']
    if master is None:
        raise ValueError('No master selected. Use set-master with an explicit reason.')
    if master['status'] != 'author_selected' and not allow_candidate:
        raise ValueError('Candidate source: select it explicitly or pass --allow-candidate for inventory.')
    path = inside(bp, master['path'])
    if digest(path) != master['sha256']:
        raise ValueError('SOURCE_HASH_CHANGED: select the new revision explicitly before using old anchors.')
    return path, master


def new_project(args):
    """Copy a clean reusable workspace; never inherit another series' live state."""
    root, source = project(args.root)
    pid = slug(args.id)
    out = Path(args.out).expanduser().resolve()
    if out.exists():
        raise ValueError('Project output already exists; no files were replaced.')
    if out.is_relative_to(root) or root.is_relative_to(out):
        raise ValueError('Project output and source must not contain one another.')
    if source.get('kind') != 'boilerplate' or source.get('books'):
        raise ValueError('new-project requires the clean default template, not an existing series.')
    if source.get('project_id') == pid:
        raise ValueError('Choose a new project ID, distinct from the template.')
    for rel, field in [('series/canon.json', 'facts'), ('series/glossary.json', 'items'),
                       ('profiles/author.json', 'traits')]:
        if read(root / rel).get(field):
            raise ValueError('Template contains live state: ' + rel)
    # IDs are unique among sibling projects; workspace_uid distinguishes independent copies.
    if out.parent.exists():
        for candidate in out.parent.glob('*/project.json'):
            if read(candidate).get('project_id') == pid:
                raise ValueError('A sibling project already uses this ID: ' + pid)
    names = ['AGENTS.md', 'STYLE.md', 'README.md', 'START_HERE.md', 'CHANGELOG.md', 'RIGHTS.md',
             '.gitignore', '.gitattributes', '.github', 'templates', 'profiles', 'series',
             'guides', 'tools', 'tests', 'skills', 'examples', 'integrations', 'methods']
    ignore = shutil.ignore_patterns('.git', '__pycache__', '*.pyc', '.DS_Store',
                                    '.openai-download-*', '*.openai-download-*')
    for name in names:
        src = root / name
        if src.is_symlink() or (src.is_dir() and any(p.is_symlink() for p in src.rglob('*'))):
            raise ValueError('Template symlinks are not copied: ' + name)
    out.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='project-stage-', dir=out.parent))
    try:
        for name in names:
            src, dst = root / name, staging / name
            if src.is_dir():
                shutil.copytree(src, dst, ignore=ignore)
            elif src.is_file():
                shutil.copy2(src, dst)
        system_ref = source.get('book_system')
        if system_ref:
            system_source = (root / system_ref).resolve()
            if not (system_source / 'README.md').is_file():
                raise ValueError('Missing shared book system: ' + str(system_source))
            if any(f.is_symlink() for f in system_source.rglob('*')):
                raise ValueError('Shared book system must not contain symlinks')
            shutil.copytree(system_source, staging / 'book-system',
                            ignore=shutil.ignore_patterns('audit', 'CHANGELOG-*', '__pycache__', '*.pyc'))
            # Carry executable helpers as well as prose rules into standalone copies.
            helper_source = system_source.parent / 'tools'
            helper_records = []
            for helper in ['literary_translation.py', 'language_qa.py', 'uk_naturalness.py',
                           'run_book_review.py', 'prepare_language_editions.py',
                           'literary_clients.py', 'literary_orchestrator.py']:
                origin = helper_source / helper
                if not origin.is_file():
                    raise ValueError('Missing language helper: ' + str(origin))
                shutil.copy2(origin, staging / 'tools' / helper)
                helper_records.append({'path': 'tools/' + helper, 'sha256': digest(origin)})
            shared_skills = system_source.parent / '.agents/skills'
            for skill in ['book-showrunner', 'book-language-review', 'literary-adaptation']:
                origin = shared_skills / skill
                if not (origin / 'SKILL.md').is_file() or any(p.is_symlink() for p in origin.rglob('*')):
                    raise ValueError('Missing or unsafe language skill: ' + str(origin))
                shutil.copytree(origin, staging / '.agents/skills' / skill, ignore=ignore)
            for document in staging.rglob('*.md'):
                if 'methods/history' in document.as_posix():
                    continue
                content = document.read_text(encoding='utf-8')
                if '../BOOK_SYSTEM' in content:
                    relative = Path(os.path.relpath(staging / 'book-system', document.parent)).as_posix()
                    content = content.replace('../../../BOOK_SYSTEM', relative).replace('../BOOK_SYSTEM', relative)
                    document.write_text(content, encoding='utf-8')
            write(staging / 'SYSTEM-SNAPSHOT.json', {
                'schema_version': 1, 'origin': str(system_source),
                'helpers': helper_records,
                'files': [{'path': f.relative_to(system_source).as_posix(), 'sha256': digest(f)}
                          for f in sorted(system_source.rglob('*')) if f.is_file()
                          and (staging / 'book-system' / f.relative_to(system_source)).is_file()],
                'policy': 'Versioned portable snapshot; no automatic updates of existing books.'})
        manifest = copy.deepcopy(source)
        manifest.update(project_id=pid, workspace_uid=str(uuid.uuid4()), title=args.title,
                        kind='book-project', books=[], optional_modules=[],
                        external={'github': None, 'google_drive': None, 'status': 'not_configured'})
        if system_ref:
            manifest['book_system'] = 'book-system'
        # Existing-book language registries are project state, never template canon.
        if isinstance(manifest.get('language_policy'), dict):
            manifest['language_policy'].pop('existing_books_registry', None)
        write(staging / 'project.json', manifest)
        for folder in ['series', 'templates/book']:
            for file in (staging / folder).rglob('*.json'):
                data = read(file)
                if isinstance(data, dict) and 'project_id' in data:
                    data['project_id'] = pid
                    write(file, data)
        (staging / 'books').mkdir()
        (staging / 'books/README.md').write_text(
            '# Книги проекта\n\nСоздавайте тома командой new-book; у каждого свой мастер и профиль.\n',
            encoding='utf-8')
        # This file is project-specific; the reusable workflow and original history stay intact.
        (staging / 'README.md').write_text(
            '# ' + args.title + '\n\nСамостоятельный книжный проект `' + pid + '`. '
            'Начните с раздела «Создать книгу» в START_HERE.md.\n\n'
            'Создан из чистого default. Рукописей, канона и ссылок на аккаунты других проектов нет. '
            'methods/history содержит только явно обозначенный исторический источник системы; '
            'его примеры не являются фактами этой книги.\n', encoding='utf-8')
        if out.exists():
            raise ValueError('Project output appeared during preparation; no files were replaced.')
        staging.rename(out)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return {'created': str(out), 'project_id': pid, 'workspace_uid': manifest['workspace_uid'],
            'books': 0, 'external_connections_reset': True, 'next_command': 'new-book'}


def new_book(args):
    root, p = project(args.root)
    bid = slug(args.id)
    preset = read(inside(root, 'profiles/' + slug(args.profile) + '.json'))
    dest = root / 'books' / bid
    if dest.exists() or any(b['id'] == bid for b in p['books']):
        raise ValueError('Book already exists; no files were replaced.')
    template = root / 'templates/book'
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='book-stage-', dir=dest.parent))
    installed = False
    try:
        shutil.copytree(template, staging, dirs_exist_ok=True)
        book = read(staging / 'book.json')
        book.update(project_id=p['project_id'], book_id=bid, title=args.title,
                    book_type=args.type, stage='idea', master=None)
        language = getattr(args, 'language', None) or p.get('language_policy', {}).get('default_new_original', 'uk')
        if language not in {'uk', 'en'}:
            raise ValueError('New original language must be uk or explicitly selected en')
        book.update(original_language=language, canonical_language=language, language_state='not_written',
                    legacy_sources=[], editions={language: {'role': 'canonical_original', 'status': 'not_started'}})
        if language == 'uk':
            book['editions']['en'] = {'role': 'derived_edition', 'source_language': 'uk', 'status': 'not_started'}
        write(staging / 'book.json', book)
        profile = copy.deepcopy(preset)
        profile.update(profile_id=bid + '-voice-v1', book_id=bid, status='proposed',
                       differentiation=args.differentiation, inherit_author_traits=[],
                       protected_examples=[], scene_overrides=[])
        write(staging / 'voice.json', profile)
        for f in staging.rglob('*.json'):
            if f.name in ('book.json', 'voice.json'):
                continue
            data = read(f)
            if isinstance(data, dict) and 'book_id' in data:
                data.update(book_id=bid, project_id=p['project_id'], source_sha256=None)
                write(f, data)
        (staging / 'brief.md').write_text('# ' + args.title + '\n\n' +
            (staging / 'brief.md').read_text(encoding='utf-8'), encoding='utf-8')
        staging.rename(dest)
        installed = True
        p['books'].append({'id': bid, 'path': 'books/' + bid})
        write(root / 'project.json', p)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if installed:
            shutil.rmtree(dest)
        raise
    return {'created': dest.relative_to(root).as_posix(), 'master': None, 'profile': profile['profile_id']}


def set_master(args):
    root, p, bp, book = get_book(args.root, args.book)
    path = inside(bp, args.path)
    mod = snapshot_module(root)
    _, fmt, flags = mod.read_source(path, args.format)
    if not args.reason.strip():
        raise ValueError('The source choice needs a reason.')
    previous = book.get('master')
    current = {'path': path.relative_to(bp).as_posix(), 'format': fmt, 'sha256': digest(path),
               'status': 'author_selected', 'authority': args.reason}
    current['language'] = (getattr(args, 'language', None) or (previous or {}).get('language')
                           or book.get('canonical_language') or book.get('original_language')
                           or p.get('language_policy', {}).get('legacy_existing_source', 'ru'))
    book['master'] = current
    logpath = bp / 'revision-log.json'
    log = read(logpath)
    log['items'].append({'action': 'select_master', 'previous': previous, 'current': current})
    write(logpath, log)
    write(bp / 'book.json', book)
    return {'master': current, 'refresh_required': ['derived', 'audit anchors', 'end-state evidence'], 'flags': flags}


def snapshot(args):
    root, p, bp, book = get_book(args.root, args.book)
    source, master = checked_master(bp, book, args.allow_candidate)
    mod = snapshot_module(root)
    output = bp / 'derived/snapshot.json'
    # The bundled reader preserves paragraph anchors; printed metrics are descriptive.
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        mod.snapshot(argparse.Namespace(source=str(source), format=master['format'],
            project_id=p['project_id'], book_id=book['book_id'], authority=master['authority'],
            chapter_pattern=mod.CHAPTER, out=str(output)))
    data = read(output)
    data['master']['path'] = source.relative_to(bp).as_posix()
    data['master']['status'] = master['status']
    write(output, data)
    # A clean text projection is useful for Git diff; it is never the editing master.
    (bp / 'derived/manuscript.txt').write_text('\n'.join(x['text'] for x in data['paragraphs']) + '\n', encoding='utf-8')
    return {'book': book['book_id'], 'sha256': master['sha256'], 'chapters': data['chapter_count'],
            'projection': 'derived/manuscript.txt', 'scope': data['scope']}


def compare(args):
    _, _, a_path, a = get_book(args.root, args.book_a)
    _, _, b_path, b = get_book(args.root, args.book_b)
    av, bv = read(a_path / 'voice.json'), read(b_path / 'voice.json')
    axes = sorted(set(av['axes']) | set(bv['axes']))
    rows = [{'axis': k, 'a': av['axes'].get(k), 'b': bv['axes'].get(k),
             'different': av['axes'].get(k) != bv['axes'].get(k)} for k in axes]
    return {'books': [a['book_id'], b['book_id']], 'axes': rows,
            'note': 'Configuration comparison only; similarity may be intentional. No literary uniqueness score.'}


def context(args):
    root, p, bp, book = get_book(args.root, args.book)
    if book['master'] is not None:
        checked_master(bp, book, args.allow_candidate)
    paths = ['book.json', 'brief.md', 'voice.json', 'session.md']
    if (bp / 'STYLE.md').is_file():
        paths.insert(3, 'STYLE.md')
    project_paths = ['STYLE.md']
    system_ref = p.get('book_system')
    system_note = ('Book system: ' + str((root / system_ref).resolve()) +
                   '; read CORE.md, WRITING.md and the target LANGUAGES style. ' if system_ref else '')
    pieces = ['# Контекст рабочей сессии', 'Задача: ' + args.task,
              'Книга: ' + book['book_id'], 'Включены только перечисленные файлы. Рукопись и канон надо читать по указанным путям.']
    pieces.append(system_note + 'New prose language: ' + book.get('original_language', p.get('language_policy', {}).get('default_new_original', 'uk')) +
                  '. Existing source language/status must be checked separately; never relabel a Russian manuscript as Ukrainian.')
    for rel in project_paths:
        pieces.extend(['\n## ' + rel, inside(root, rel).read_text(encoding='utf-8')])
    for rel in paths:
        text = inside(bp, rel).read_text(encoding='utf-8')
        pieces.extend(['\n## ' + (bp / rel).relative_to(root).as_posix(), text])
    pieces += ['\n## Прочитать до письма', '- AGENTS.md', '- guides/SCENE-EDITING.md']
    for rel in ['plan.md', 'characters.json', 'scenes.json', 'timeline.json',
                'knowledge.json', 'resources.json', 'promises.json', 'end-state.json', 'audit/issues.json']:
        pieces.append('- ' + (bp / rel).relative_to(root).as_posix())
    canon = (bp / book['canon']).resolve().relative_to(root).as_posix()
    pieces += ['- ' + canon + ' (только относящиеся к сцене факты)', '- series/glossary.json']
    for rel in ['series/CANON-POLICY.md', 'series/continuity-queue.json']:
        if (root / rel).is_file():
            pieces.append('- ' + rel)
    pieces += ['Сверьте состояние перед сценой и знания каждого участника; не переносите в них финал тома. '
               'Отсутствующий факт запишите в audit/issues.json книги с resolution_status: unresolved.',
               '\n## После правки',
               'Обновите все затронутые зависимости по guides/SCENE-EDITING.md, версии, извлечения и якоря. '
               'Выполните проверки прозы и технические проверки; запишите результат и открытые вопросы '
               'в revision-log.json и session.md книги.',
               'Не включены автоматически: другие тома, отзывы, полный текст, личные биографии и старые варианты.']
    if book['master']:
        pieces += ['Мастер: ' + (bp / book['master']['path']).relative_to(root).as_posix(),
                   'SHA-256: ' + book['master']['sha256']]
    out = inside(root, args.out)
    if out.exists():
        raise ValueError('Context output already exists; choose a new filename.')
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n\n'.join(pieces) + '\n', encoding='utf-8')
    return {'written': out.relative_to(root).as_posix(), 'included_files': paths,
            'project_files': project_paths}


def doctor(args):
    root, p = project(args.root)
    errors, warnings, ids, profiles = [], [], set(), set()
    voice_records = []
    if p.get('schema_version') != 1:
        errors.append('Unsupported project schema')
    try:
        slug(p['project_id'])
        for rel in ['series/canon.json', 'series/glossary.json']:
            record = read(root / rel)
            if record.get('project_id') != p['project_id']:
                errors.append(rel + ': project ID disagrees with project.json')
    except (ValueError, KeyError, OSError, TypeError) as e:
        errors.append('Project: ' + str(e))
    for entry in p['books']:
        try:
            if entry['id'] in ids:
                raise ValueError('Duplicate book ID')
            slug(entry['id'])
            ids.add(entry['id'])
            bp = inside(root, entry['path'])
            b, v = read(bp / 'book.json'), read(bp / 'voice.json')
            if b['book_id'] != entry['id'] or b['project_id'] != p['project_id']:
                raise ValueError('Manifest IDs disagree')
            if v['book_id'] != entry['id'] or v['profile_id'] in profiles:
                raise ValueError('Voice ID belongs to another book or is duplicated')
            profiles.add(v['profile_id'])
            voice_records.append((entry['id'], v))
            if v['status'] == 'proposed':
                warnings.append(entry['id'] + ': voice is a proposal')
            if b['master']:
                src, m = checked_master(bp, b, allow_candidate=True)
                if m['format'] == 'docx' and not zipfile.is_zipfile(src):
                    raise ValueError('Declared DOCX is not an OOXML ZIP file')
                if m['status'] != 'author_selected':
                    warnings.append(entry['id'] + ': source not confirmed final by author')
                snap = bp / 'derived/snapshot.json'
                if snap.exists() and read(snap)['master']['sha256'] != m['sha256']:
                    raise ValueError('Derived snapshot is stale')
            elif b['stage'] not in ['idea', 'planning']:
                warnings.append(entry['id'] + ': no selected master')
            for jf in bp.rglob('*.json'):
                data = read(jf)
                if isinstance(data, dict) and 'book_id' in data and data['book_id'] != entry['id']:
                    raise ValueError('Cross-book data: ' + str(jf.relative_to(bp)))
        except (ValueError, KeyError, OSError, TypeError) as e:
            errors.append(entry.get('id', '?') + ': ' + str(e))
    for i, (aid, av) in enumerate(voice_records):
        for bid, bv in voice_records[i + 1:]:
            if av['axes'] == bv['axes'] and 'distinct' in [av.get('differentiation'), bv.get('differentiation')]:
                warnings.append(aid + ' / ' + bid + ': distinct requested but voice settings are identical; review a prose sample or choose related.')
    return {'books': len(ids), 'errors': errors, 'warnings': warnings,
            'scope': 'File integrity, IDs and selected version; not prose quality, full canon or layout.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ['new-project', 'new-book', 'set-master', 'snapshot', 'compare-voices', 'context', 'doctor']:
        subp = sub.add_parser(name)
        subp.add_argument('--root', default='.')
        if name in ['set-master', 'snapshot', 'context']:
            subp.add_argument('--book', required=True)
        if name in ['snapshot', 'context']:
            subp.add_argument('--allow-candidate', action='store_true')
        if name == 'new-project':
            subp.add_argument('--id', required=True)
            subp.add_argument('--title', required=True)
            subp.add_argument('--out', required=True, help='New folder outside the clean template')
        elif name == 'new-book':
            subp.add_argument('--id', required=True)
            subp.add_argument('--title', required=True)
            subp.add_argument('--profile', default='custom')
            subp.add_argument('--language', choices=['uk', 'en'], help='Original language; defaults to project policy (uk)')
            subp.add_argument('--type', choices=['fiction', 'memoir', 'nonfiction'], default='fiction')
            subp.add_argument('--differentiation', choices=['distinct', 'related', 'unspecified'], default='unspecified')
        elif name == 'set-master':
            subp.add_argument('--path', required=True, help='Path relative to the book folder')
            subp.add_argument('--format', choices=['auto', 'docx', 'text'], default='auto')
            subp.add_argument('--reason', required=True)
            subp.add_argument('--language', choices=['uk', 'en', 'ru'], help='Actual language of this selected file')
        elif name == 'compare-voices':
            subp.add_argument('--book-a', required=True)
            subp.add_argument('--book-b', required=True)
        elif name == 'context':
            subp.add_argument('--task', required=True)
            subp.add_argument('--out', required=True, help='New output path relative to project root')
    args = parser.parse_args()
    functions = {'new-project': new_project, 'new-book': new_book, 'set-master': set_master, 'snapshot': snapshot,
                 'compare-voices': compare, 'context': context, 'doctor': doctor}
    try:
        result = functions[args.command](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get('errors') else 0
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
