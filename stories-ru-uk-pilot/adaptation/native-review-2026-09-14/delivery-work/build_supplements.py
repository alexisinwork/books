#!/usr/bin/env python3
"""Add reader-facing audit materials to the unsealed v4 author package."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / 'stories-ru-uk-pilot'
TASK = PROJECT / 'adaptation/native-review-2026-09-14'
OUT = PROJECT / 'delivery/2026-09-14-v4'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        stream.write(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    assert OUT.is_dir() and not (OUT / 'CHECKSUMS.json').exists()
    provenance = []

    def copy(source, relative):
        target = OUT / relative
        assert not target.exists(), target
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert sha(source) == sha(target)
        provenance.append({'path': str(relative), 'origin': str(source.relative_to(ROOT)),
                           'origin_sha256': sha(source), 'transformation': 'byte-exact copy'})

    selection = json.loads((PROJECT / 'release/SELECTION-2026-09-14-v4.json').read_text())
    acceptance = json.loads((TASK / 'ROOT-REVIEW-ACCEPTANCE.json').read_text())
    for chosen, decision in zip(selection['books'], acceptance['books']):
        assert chosen['book_id'] == decision['book_id']
        book = PROJECT / 'books' / chosen['book_id']
        edition = book / 'editions/uk'
        draft = edition / chosen['draft']
        review_relative = Path('Матеріали перевірки') / chosen['title']
        final_run = 'final-target-only-astra-v7-r1' if chosen['book_id'].endswith('chaos-logic') else 'final-target-only-astra-r1'
        report_dir = edition / 'native-2026-09-14' / final_run
        for name in ('CHANGES.html', 'continuity.json'):
            copy(draft / name, review_relative / name)
        for source, name in [(report_dir / 'report.md', 'Незалежне читання.md'),
                             (report_dir / 'coverage.json', 'reading-coverage.json'),
                             (draft / 'reader/render/visual-review.json', 'visual-review.json'),
                             (draft / 'reader/render/verification.json', 'render-verification.json'),
                             (draft / 'reader' / Path(chosen['docx_name']).with_suffix('.export.json'), 'docx-export.json')]:
            copy(source, review_relative / name)
        # The assembler copied the repository assessment verbatim. Keep it and
        # derive a portable version with links that work inside the author package.
        portable = OUT / review_relative / 'Підсумки перевірки.md'
        prior = portable.read_text(encoding='utf-8')
        write_new(portable.with_name('Підсумки перевірки — репозиторний оригінал.md'), prior)
        changed = len(json.loads((draft / 'changes.json').read_text())['changes'])
        paragraphs = sum(len(b['target_paragraphs']) for b in json.loads((draft / 'translation.json').read_text())['blocks'])
        text = f'''# «{chosen['title']}»: підсумки перевірки

Повністю відредаговано український текст; змінено {changed} повних абзаців порівняно з попередньою переданою редакцією. Остаточне незалежне модельне читання охопило всі {paragraphs} непорожніх одиниць. Обов’язкових мовних правок після цього читання не залишилося. Висновок не є гарантією абсолютної безпомилковості.

- [Повний журнал «було — стало»](CHANGES.html)
- [Повне порівняння російського джерела й перекладу](<Порівняння RU–UK.html>)
- [Остаточне незалежне читання](<Незалежне читання.md>)
- [Технічна перевірка](final-checks.json)

Авторські рішення збережено. DOCX перевірено через витяг тексту та перегляд усіх сторінок. Текстовий SHA-256: `{chosen['target_sha256']}`.

Додатковий обов’язковий зовнішній цикл не завершено: Claude Code Opus не виконав нові проходи через ліміт, а сувору незалежність попередніх великих файлових запусків не підтверджено. Точні клієнти, версії та межі перевірки описано в `REVIEW-RESOLUTIONS.json`. Поточні повні читання Codex враховано окремо.
'''
        portable.write_text(text, encoding='utf-8')
        provenance.append({'path': str(portable.relative_to(OUT)),
                           'origin': str((edition / ('QA-ASSESSMENT-' + chosen['draft'].removeprefix('draft-') + '.md')).relative_to(ROOT)),
                           'origin_sha256': hashlib.sha256(prior.encode()).hexdigest(),
                           'sha256': sha(portable), 'transformation': 'Portable reader summary; original retained beside it.'})

    for relative in ('REPORT.md', 'reconciliation/RECONCILIATION.md', 'reconciliation/CHAOS-49-DISPOSITIONS.json',
                     'rules-work/REVIEW-CLAIM-VALIDATION.md', 'rules-work/LAST-PUNCTUATION-RULE.json',
                     'runner-work/ADDENDUM.md', 'desktop-import/import.json', 'desktop-import/desktop-vs-delivered.diff',
                     'ROOT-REVIEW-ACCEPTANCE.json', 'technical-validation.json'):
        copy(TASK / relative, Path('Матеріали перевірки/Загальний звіт') / relative)
    for relative in ('BOOK_SYSTEM/LANGUAGES/uk/STYLE.md', 'BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md',
                     '.agents/skills/book-language-review/SKILL.md', 'BOOK_SYSTEM/ADAPTATION/prompts/target-only-uk.md'):
        copy(ROOT / relative, Path('Правила української') / relative)
    copy(PROJECT / 'adaptation/author-answers-2026-09-14/ANSWERS.md', Path('ВІДПОВІДІ-АВТОРА.md'))
    copy(PROJECT / 'adaptation/author-answers-2026-09-14/answers.json', Path('answers.json'))

    questions = '''# Неоднозначности источника после языковой редакции

Все три украинских текста готовы для чтения. Предыдущие ответы уже применены; повторять их не нужно. Ниже только новые вопросы к событиям и устройству мира «Логіки хаосу». Они не останавливают передачу текста и не считаются языковыми ошибками. Номера p относятся к русскому исходному DOCX, SHA-256 `fe5afe9ca4937c3e02a9a6065f35a756cb4fe5618c749351c3cf0ee55254af5d`.

1. **p136, говорящий.** К Чарльзу обращается Гаррі или Вольф? Источник не называет собеседника однозначно, поэтому имя не добавлено.

   Ответ автора:

2. **p296–297, ведущий и генерал.** Ведущий передаёт слово Чарльзу, который отвечает «генерале». Кто именно ведёт разговор? В переводе новое имя и должность не назначены.

   Ответ автора:

3. **p144/p166, управление отсеком.** Сначала двигатель должны настроить на ручное управление, затем Гаррі говорит, что управлять невозможно и полёт ведёт автопилот. Это разные возможности управления, неисправность или противоречие черновика?

   Ответ автора:

4. **p15/p149/p150/p277, личные вещи.** Фраза о том, что личные вещи на борт не берут, соседствует с любимым браслетом Гаррі и вещами в жилом модуле. Правило касается только багажа, герой его преувеличивает или формулировку нужно уточнить?

   Ответ автора:

Мотив Рязанцева и возможная связь прошлого Ніки с дочерью Шенга оставлены недосказанными, как было указано ранее. Финальный выстрел «Справедливого вбивці» и шутка с яйцом не переоткрываются для обязательного исправления.

Этот файл — копия для ответов. После авторских изменений его следует явно импортировать и сравнить с Git-версией; дата файла сама по себе не делает ответы новым каноном.
'''
    write_new(TASK / 'ВОПРОСЫ-АВТОРУ.md', questions)
    copy(TASK / 'ВОПРОСЫ-АВТОРУ.md', Path('ВОПРОСЫ-АВТОРУ.md'))
    readme = '''# Три оповідання українською — редакція v4

Для читання відкрийте ці повні тексти:

- [Рептилоїди](<Рептилоїди — українська версія.docx>)
- [Справедливий вбивця](<Справедливий вбивця — українська версія.docx>)
- [Логіка хаосу](<Логіка хаосу — українська версія.docx>)

Перевірено літературну оповідь, живу розмовну мову, кальки, керування, пунктуацію, зрозумілість дії та відмінність голосів. Змінено 22, 87 і 160 повних абзаців відповідно. Кількість змінених абзаців охоплює всі види редактури, а не лише русизми. Авторські відповіді та впізнавані повтори збережено.

[Докладний підсумок](<Матеріали перевірки/Загальний звіт/REPORT.md>) пояснює, що виправлено й які правила вдосконалено. У папці кожного оповідання є повний журнал «було — стало», порівняння RU–UK та остаточне незалежне читання. Оновлені загальні правила зібрано в папці «Правила української».

Файли DOCX перевірено за текстом і виглядом усіх 105 сторінок. Фінальні незалежні модельні читання охопили всі три тексти. Нових обов’язкових мовних правок у них не зафіксовано. Зовнішній цикл Opus залишився незавершеним через ліміти; межі перевірок чесно описано у звітах.

[Додаткові питання](ВОПРОСЫ-АВТОРУ.md) стосуються чотирьох неоднозначностей джерела. Відповідати знову на вже узгоджені пункти не потрібно. Попередні [відповіді автора](ВІДПОВІДІ-АВТОРА.md) додано для довідки.

Цей пакет має окрему папку v4. Попередню настільну копію з авторською зміною збережено; її єдину текстову правку «Вставай вже» перенесено до нового тексту.
'''
    write_new(OUT / 'ПРОЧИТАЙТЕ.md', readme)
    write_new(OUT / 'PACKAGING-NOTES.json', {'schema_version': 1, 'status': 'reader_package_supplements',
                                          'note': 'Technical records retain repository-relative and original absolute provenance paths. Reader summaries use portable local links.',
                                          'files': provenance})
    checksums = {'schema_version': 1, 'scope': 'Every package file except this checksum index; includes technical and reading materials.',
                 'files': [{'path': str(p.relative_to(OUT)), 'sha256': sha(p), 'bytes': p.stat().st_size}
                           for p in sorted(OUT.rglob('*')) if p.is_file()]}
    write_new(OUT / 'CHECKSUMS.json', checksums)
    print(json.dumps({'files_excluding_index': len(checksums['files']), 'out': str(OUT)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
