#!/usr/bin/env python3
"""Freeze the coordinator's reviewed results; does not run models or approve canon."""
import argparse
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
PROJECT = TASK.parents[1]
ROOT = PROJECT.parent
CONFIG = [
    ('story-01-reptiloids', 'draft-v5', 'Рептилоїди', 'final-target-only-astra-r1', 'story-01-reptiloids.spec.json'),
    ('story-02-fair-killer', 'draft-v4', 'Справедливий вбивця', 'final-target-only-astra-r1', 'story-02-fair-killer.spec.json'),
    ('story-03-chaos-logic', 'draft-v7', 'Логіка хаосу', 'final-target-only-astra-v7-r1', 'story-03-chaos-logic-v7.spec.json'),
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def ref(path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': sha(path)}


def main(acceptance_path):
    accepted = {x['book_id']: x for x in read(acceptance_path)['books']}
    bindings = {x['book_id']: x['input_binding'] for x in read(TASK / 'pipeline-work/native-inputs/INPUT-BINDINGS.json')['books']}
    prepared = []
    for book_id, version, title, final_run, spec_name in CONFIG:
        edition = PROJECT / 'books' / book_id / 'editions/uk'
        draft = edition / version
        target = draft / 'target.uk.txt'
        report = edition / 'native-2026-09-14' / final_run / 'report.md'
        coverage = report.with_name('coverage.json')
        check = read(draft / 'final-checks.json')
        decision = accepted[book_id]
        assert decision['target_sha256'] == sha(target) == check['target_sha256']
        assert decision['report_sha256'] == sha(report)
        assert decision['coordinator_read_report'] is True
        assert decision['remaining_confirmed_language_defects'] == 0
        assert not check['errors']
        prior_assessment = edition / ('QA-ASSESSMENT-' + version.removeprefix('draft-') + '.md')
        if prior_assessment.exists():
            assert sha(prior_assessment) == decision['prior_qa_assessment_sha256']
        changes = read(draft / 'changes.json')
        translation = read(draft / 'translation.json')
        source_count = sum(len(x['source_ids']) for x in translation['blocks'])
        paragraph_count = sum(len(x['target_paragraphs']) for x in translation['blocks'])
        records = []
        native = edition / 'native-2026-09-14'
        for invocation in sorted(native.glob('reviews-*/**/invocation.json')):
            data = read(invocation)
            item = {'invocation': ref(invocation), 'client': data.get('client'),
                    'requested_model': data.get('requested_model'), 'status': data.get('status'),
                    'reviewed_target': data.get('target'),
                    'current_target_review': data.get('target', {}).get('sha256') == sha(target)}
            report_path = invocation.with_name('REPORT.md')
            if report_path.exists():
                item['report'] = ref(report_path)
            if data.get('input_delivery') == 'isolated_files':
                item['independence_validation'] = 'not_certified: file-mode runner did not enforce filesystem boundary; observations reconciled manually'
            elif data.get('status') == 'report_returned':
                item['independence_validation'] = 'fresh process with embedded permitted inputs; client receipt is not a proof of reading quality'
            else:
                item['independence_validation'] = 'incomplete run; does not count as a completed review'
            records.append(item)
        resolution = {
            'schema_version': 1, 'book_id': book_id, 'target': ref(target),
            'authority': 'Author explicitly commissioned full Ukrainian language revision and context-based rule updates.',
            'author_canonical_approval': False,
            'implementation_spec': ref(TASK / 'reconciliation' / spec_name),
            'complete_before_after': ref(draft / 'changes.json'),
            'reconciliation_reasoning': ref(TASK / 'reconciliation/RECONCILIATION.md'),
            'final_target_only_report': ref(report), 'final_reading_coverage': ref(coverage),
            'coordinator_assessment': decision,
            'external_runs': records,
            'mechanical_checks': ref(draft / 'final-checks.json'),
            'literary_release_gate': 'open',
            'gate_reason': 'Required Claude Code Opus runs unavailable/incomplete; agy Opus is a supplementary client, and earlier large external file-mode isolation was not certified. Final Codex target-only readings are documented separately.',
        }
        if book_id.endswith('chaos-logic'):
            resolution['sol_remaining_proposals'] = ref(TASK / 'reconciliation/CHAOS-49-DISPOSITIONS.json')
            resolution['desktop_import'] = ref(TASK / 'desktop-import/import.json')
            resolution['corrected_late_findings'] = ['TUK-V6-01: obsolete comma after ентузіазмом', 'TUK-V6-02: comma after particle все ж']
        assessment = f'''# Мовна перевірка: «{title}»

Повний український текст після докладної редактури: `{version}`. Змінено {len(changes['changes'])} повних абзаців порівняно з раніше переданою автору редакцією. Точні «було — стало» з причинами збережено в [{version}/CHANGES.md]({version}/CHANGES.md) та HTML.

Перевірено відповідність усіх {source_count} одиниць джерела; український текст має {paragraph_count} непорожніх абзаців. Останнє незалежне читання українського файла охопило його повністю, без джерела, канону та підказок про виправлення. Після зведення підтверджених мовних дефектів, що лишилися невиправленими, не зафіксовано. Це результат конкретних проходів, не гарантія абсолютної безпомилковості.

Новий [звіт читання](native-2026-09-14/{final_run}/report.md) прив’язаний до SHA-256 `{sha(target)}`. Технічний лічильник і SHA не замінюють читання. Повноту, форматування DOCX та відповідність витягнутого PDF перевірено окремо; {check['pages']} сторінок.

Авторські відповіді та важливі повтори збережено. Припущення про мотиви, фантастичну фізику та нерозкриті сюжетні зв’язки не перетворено на новий канон. Залишкові питання саме до джерела наведено в реєстрі книги; вони відокремлені від мовної коректури.

Повний обов’язковий зовнішній публікаційний допуск залишається відкритим: нові Claude Code Opus-проходи не завершилися через ліміти; додатковий Opus через agy не підміняє цей клієнт. Gemini Flash/Pro повернули звіти на попередніх кандидатах, однак сувору ізоляцію великих файлових запусків не підтверджено. Їхні спостереження перевірені координатором, а нові Codex target-only читання документовані окремо. Невдалий запуск не зарахований як перевірка.

Деталі зведення, справжні клієнти, хеші та обмеження: [{version}/REVIEW-RESOLUTIONS.json]({version}/REVIEW-RESOLUTIONS.json). Передається завершена робоча редакція для читання автора; статус канонічного затвердження не призначено моделями.
'''
        chosen = {'book_id': book_id, 'draft': version, 'title': title,
                  'docx_name': title + ' — українська версія.docx', 'target_sha256': sha(target),
                  'input_binding': bindings[book_id]}
        prepared.append((draft, edition, resolution, assessment, chosen, len(changes['changes'])))
    for draft, edition, resolution, assessment, chosen, count in prepared:
        write_new(draft / 'REVIEW-RESOLUTIONS.json', resolution)
        assessment_path = edition / ('QA-ASSESSMENT-' + chosen['draft'].removeprefix('draft-') + '.md')
        if assessment_path.exists():
            # This is a mutable coordinator summary, not an independent frozen report.
            # Preserve the metadata-stage text before incorporating final readings.
            write_new(TASK / 'metadata-work/coordinator-handoff' / chosen['book_id'] / assessment_path.name,
                      assessment_path.read_text(encoding='utf-8'))
            assessment_path.write_text(assessment, encoding='utf-8')
        else:
            write_new(assessment_path, assessment)
    selection = {'schema_version': 1, 'date': '2026-09-14',
                 'scope': 'Full three-story Ukrainian working edition after complete native-language revision',
                 'supersedes': 'SELECTION-2026-09-14-v3.json',
                 'author_answers': 'stories-ru-uk-pilot/adaptation/author-answers-2026-09-14/answers.json',
                 'books': [x[4] for x in prepared]}
    write_new(PROJECT / 'release/SELECTION-2026-09-14-v4.json', selection)
    overview = '''# Повна мовна редакція трьох оповідань

Перевірено й відредаговано всі три українські тексти, включно з діалогами, синтаксисом, керуванням, кальками, пунктуацією та функціональними повторами. Підтверджені автором рішення збережено. Російські оригінали не переписані.

| Текст | Редакція | Змінених повних абзаців | DOCX |
| --- | --- | ---: | ---: |
'''
    for draft, edition, resolution, assessment, chosen, count in prepared:
        pages = read(draft / 'final-checks.json')['pages']
        overview += f"| {chosen['title']} | {chosen['draft']} | {count} | {pages} стор. |\n"
    overview += '''
Усі 600 вихідних непорожніх одиниць збережено у відповідностях; українська версія має 604 абзаци, включно із заголовками та роздільниками. Розділення кількох коротких сцен у «Рептилоїдах» пояснює різницю. Нові незалежні модельні читання охопили кожен остаточний український файл повністю. Хеші, охоплення й межі незалежності наведено у звітах.

До загальних правил додано перевірку змістових ролей, керування після синонімічної заміни, наміру проти виконаної дії, межі репліки та дії, пунктуації після перебудови, розмовної функції й відмінності голосів. Перевірка словників захищає від вигаданих заборон: «кисть», «вичитувати кому» та інші нормативні вживання не вилучаються через російську схожість. Орієнтир правопису — офіційне видання 2026; літературна природність оцінюється окремо від написання слів.

Оновлено підрахунок охоплення: фізичні рядки, порожні рядки та прочитані абзаци більше не подаються як одна величина. Для великих зовнішніх запусків виправлено доставку точних файлів і чесно зазначено, що prompt-обмеження не є гарантією файлової ізоляції. Окремі frozen snapshots дозволяють відтворити перевірку без підміни старих входів новими правилами.

У «Логіці хаосу» з настільної копії явно імпортовано єдину авторську текстову зміну «Вставай вже». Сама змінена копія, порівняння й рішення збережені в Git.

Тексти й повні журнали готові для авторського читання. Повний обов’язковий зовнішній публікаційний допуск не заявляється: Opus через Claude Code не завершив нові перевірки через ліміт, а незалежність попередніх великих agy-запусків виявилася недостатньо підтвердженою. Невдалі запуски й попередні версії не видаються за перевірку остаточного тексту.

Докладне зведення: [reconciliation/RECONCILIATION.md](reconciliation/RECONCILIATION.md). Перевірені словникові аргументи: [rules-work/REVIEW-CLAIM-VALIDATION.md](rules-work/REVIEW-CLAIM-VALIDATION.md). Застосовані правки та всі журнали передаються до репозиторію разом із цією редакцією.
'''
    write_new(TASK / 'REPORT.md', overview)
    print(json.dumps({'selection': str(PROJECT / 'release/SELECTION-2026-09-14-v4.json'), 'changed_paragraphs': {x[4]['book_id']: x[5] for x in prepared}}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--acceptance', type=Path, required=True)
    main(parser.parse_args().acceptance)
