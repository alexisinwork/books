import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('studio', ROOT / 'tools/studio.py')
studio = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(studio)


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ['templates', 'profiles', 'skills', 'series']:
            shutil.copytree(ROOT / name, self.root / name)
        studio.write(self.root / 'project.json', {'schema_version': 1, 'project_id': 'trial', 'books': []})
        for name in ['canon', 'glossary']:
            path = self.root / 'series' / (name + '.json')
            data = studio.read(path); data['project_id'] = 'trial'; studio.write(path, data)

    def tearDown(self):
        self.tmp.cleanup()

    def new(self, name='first', profile='custom'):
        return studio.new_book(argparse.Namespace(root=self.root, id=name, title=name,
            profile=profile, type='fiction', differentiation='unspecified'))

    def master(self, name='first'):
        p = self.root / 'books' / name / 'manuscript/master.md'
        p.write_text('# Глава 1\n\nОн спрятал письмо.\n', encoding='utf-8')
        return studio.set_master(argparse.Namespace(root=self.root, book=name,
            path='manuscript/master.md', format='text', reason='Chosen for this trial'))

    def test_clean_creation_and_independent_voice(self):
        self.new('first', 'intimate-lyrical')
        self.new('second', 'intimate-lyrical')
        _, p, bp, b = studio.get_book(self.root, 'second')
        self.assertIsNone(b['master'])
        self.assertEqual(b['project_id'], 'trial')
        a = studio.read(self.root / 'books/first/voice.json')
        v = studio.read(bp / 'voice.json')
        self.assertNotEqual(a['profile_id'], v['profile_id'])
        self.assertEqual(a['axes'], v['axes'])  # Intentional similarity remains allowed.
        preset = studio.read(self.root / 'profiles/intimate-lyrical.json')
        preset['axes']['pov'] = 'A later preset change'
        studio.write(self.root / 'profiles/intimate-lyrical.json', preset)
        self.assertEqual(studio.read(bp / 'voice.json'), v)
        self.assertEqual(studio.read(bp / 'knowledge.json')['items'], [])

    def test_refuses_overwrite_and_path_escape(self):
        self.new()
        self.master()
        bp = self.root / 'books/first'
        before = (bp / 'book.json').read_bytes()
        with self.assertRaises(ValueError):
            self.new()
        self.assertEqual((bp / 'book.json').read_bytes(), before)
        with self.assertRaises(ValueError):
            studio.inside(self.root, '../outside')
        with self.assertRaises(ValueError):
            self.new('../other')

    def test_hash_guard_prevents_stale_evidence(self):
        self.new()
        self.master()
        args = argparse.Namespace(root=self.root, book='first', allow_candidate=False)
        studio.snapshot(args)
        bp = self.root / 'books/first'
        d = studio.read(bp / 'derived/snapshot.json')
        self.assertEqual(d['master']['path'], 'manuscript/master.md')
        (bp / 'manuscript/master.md').write_text('Совсем другая версия.', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'SOURCE_HASH_CHANGED'):
            studio.snapshot(args)
        self.assertTrue(studio.doctor(argparse.Namespace(root=self.root))['errors'])

    def test_fake_docx_requires_explicit_text_choice(self):
        self.new()
        path = self.root / 'books/first/manuscript/fake.docx'
        path.write_text('Это обычный текст.', encoding='utf-8')
        args = argparse.Namespace(root=self.root, book='first', path='manuscript/fake.docx',
            format='docx', reason='Trial')
        with self.assertRaises(ValueError):
            studio.set_master(args)
        self.assertIsNone(studio.get_book(self.root, 'first')[3]['master'])

    def test_context_is_scoped_and_does_not_overwrite(self):
        self.new('first')
        self.new('second')
        secret = 'СЕКРЕТ-ДРУГОГО-ТОМА'
        (self.root / 'books/second/brief.md').write_text(secret, encoding='utf-8')
        args = argparse.Namespace(root=self.root, book='first', allow_candidate=False,
            task='Write next scene', out='sessions/context.md')
        studio.context(args)
        self.assertNotIn(secret, (self.root / args.out).read_text(encoding='utf-8'))
        with self.assertRaises(ValueError):
            studio.context(args)

    def test_candidate_is_not_silently_author_selected(self):
        self.new()
        self.master()
        _, _, bp, b = studio.get_book(self.root, 'first')
        b['master']['status'] = 'candidate'
        studio.write(bp / 'book.json', b)
        args = argparse.Namespace(root=self.root, book='first', allow_candidate=False)
        with self.assertRaisesRegex(ValueError, 'Candidate source'):
            studio.snapshot(args)
        args.allow_candidate = True
        studio.snapshot(args)
        self.assertEqual(studio.read(bp / 'derived/snapshot.json')['master']['status'], 'candidate')

    def test_differentiation_warns_only_when_requested(self):
        self.new('first')
        self.new('second')
        args = argparse.Namespace(root=self.root)
        self.assertFalse(any('identical' in x for x in studio.doctor(args)['warnings']))

        vp = self.root / 'books/second/voice.json'
        v = studio.read(vp)
        v['differentiation'] = 'distinct'
        studio.write(vp, v)
        result = studio.doctor(args)
        self.assertTrue(any('identical' in x for x in result['warnings']))
        self.assertEqual(result['errors'], [])
        v['differentiation'] = 'related'
        studio.write(vp, v)
        self.assertFalse(any('identical' in x for x in studio.doctor(args)['warnings']))

    def test_new_book_rolls_back_after_manifest_failure(self):
        original_write = studio.write
        def broken_write(path, data):
            if Path(path) == self.root / 'project.json':
                raise OSError('simulated manifest failure')
            return original_write(path, data)
        with patch.object(studio, 'write', side_effect=broken_write):
            with self.assertRaises(OSError):
                self.new('rolled-back')
        self.assertFalse((self.root / 'books/rolled-back').exists())
        self.assertEqual(studio.read(self.root / 'project.json')['books'], [])


class ProjectCreationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.template = self.base / 'default'
        shutil.copytree(ROOT, self.template, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        # The test is reusable in a series copy without treating that series as a template.
        shutil.rmtree(self.template / 'books', ignore_errors=True)
        studio.write(self.template / 'project.json', {
            'schema_version': 1, 'project_id': 'default-test', 'kind': 'boilerplate', 'books': [],
            'external': {'github': 'stale-account', 'google_drive': 'stale-folder'}})
        studio.write(self.template / 'series/canon.json', {'project_id': 'default-test', 'facts': []})
        studio.write(self.template / 'series/glossary.json', {'project_id': 'default-test', 'items': []})
        studio.write(self.template / 'profiles/author.json', {'traits': []})

    def tearDown(self):
        self.tmp.cleanup()

    def args(self, pid='new-world', out='new-world'):
        return argparse.Namespace(root=self.template, id=pid, title='Новый мир', out=self.base / out)

    def test_new_project_resets_connections_and_book_state(self):
        result = studio.new_project(self.args())
        target = self.base / 'new-world'
        data = studio.read(target / 'project.json')
        self.assertEqual(data['books'], [])
        self.assertIsNone(data['external']['github'])
        self.assertIsNone(data['external']['google_drive'])
        self.assertEqual(studio.read(target / 'series/canon.json')['project_id'], 'new-world')
        self.assertTrue(result['workspace_uid'])
        self.assertEqual((target / 'tools/studio.py').read_bytes(), (self.template / 'tools/studio.py').read_bytes())
        with self.assertRaises(ValueError):
            studio.new_project(self.args())
        with self.assertRaisesRegex(ValueError, 'sibling'):
            studio.new_project(self.args(out='different-folder'))

    def test_live_canon_is_not_copied_as_clean_template(self):
        studio.write(self.template / 'series/canon.json', {'facts': [{'secret': 'other-world'}]})
        with self.assertRaisesRegex(ValueError, 'live state'):
            studio.new_project(self.args())
        self.assertFalse((self.base / 'new-world').exists())

    def test_new_project_refuses_symlink_and_unsafe_nesting(self):
        with self.assertRaises(ValueError):
            studio.new_project(self.args(out='default/nested'))
        (self.template / 'profiles/external-link').symlink_to(self.base / 'outside')
        with self.assertRaisesRegex(ValueError, 'symlinks'):
            studio.new_project(self.args())



if __name__ == '__main__':
    unittest.main()
