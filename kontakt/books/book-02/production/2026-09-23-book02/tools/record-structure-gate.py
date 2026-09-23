"""Record the coordinator's reviewed whole-book structure gate; run after reading v2."""
from pathlib import Path
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[6]
BOOK = ROOT / 'kontakt/books/book-02'
RUN = BOOK / 'production/2026-09-23-book02'
STRUCTURE = RUN / 'structure-v2'
DESKTOP = Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    mirror(path)

def mirror(path):
    target = DESKTOP / path.relative_to(ROOT)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)

if __name__ == '__main__':
    cards = read(STRUCTURE / 'chapter-scene-cards.json')
    assert cards['chapter_count'] == 36 and cards['scene_count'] == 41
    assert len(cards['scenes']) == 41
    assert not (RUN / 'root-structure-gate.json').exists(), 'Gate already recorded; preserve it.'
    lock = read(STRUCTURE / 'carry-in-source-lock.json')
    assert sha(ROOT / lock['source']) == lock['source_sha256']
    gate = {
        'status': 'pass_for_complete_astra_rough_draft',
        'reviewer': 'root coordinator',
        'authority': 'Explicit author request: entire structure, all Astra rough chapters, then all Terra full chapters.',
        'review_scope': 'Complete 36-chapter/41-scene outline; documentary insert; character knowledge, timeline, resources, promises, end state, carry-in evidence and bounded corrections in structure-v2.',
        'files': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in sorted(STRUCTURE.iterdir()) if p.is_file()],
        'chapter_count': 36,
        'scene_count': 41,
        'checks': {
            'causal_chain': 'pass_at_plan_level',
            'book01_carry_in': 'bound_to_corrected_v4',
            'rank_and_reveal': 'R1 to R2 only; reader-ahead reserve clue from DOC01; Dal receives source in CH35',
            'time': 'D0-D6 preparation; exact D7 00:00 to D8 00:00 local experiment; D8-D9 aftermath',
            'agency': 'Ira determines her own aims; Vector complies with withdrawal; Lana and Taras retain independent work',
            'service_boundaries': 'local ranking only; direct addressing, emergency, identity and rights remain',
            'ending': 'friendship after ordinary work; no replacement universal network; reserve cause remains unknown'
        },
        'limits': ['Plan gate is not prose approval.', 'Implementation choices are reversible working details, not invented author votes or canonical promotion.', 'Five bounded unknowns remain recorded; none requires inventing a fact to draft this book.'],
        'next_phase': 'Astra writes actual rough prose of ALL 36 chapters before Terra begins full prose.'
    }
    save(RUN / 'root-structure-gate.json', gate)
    issues = read(BOOK / 'audit/issues.json')
    questions = read(STRUCTURE / 'decisions-and-questions.json')['unresolved']
    for q in questions:
        issue_id = 'KONTAKT-B02-20260923-' + q['id']
        assert not any(x['id'] == issue_id for x in issues['items'])
        issues['items'].append({
            'id': issue_id, 'category': 'continuity_boundary', 'severity': 'bounded_limit',
            'certainty': 'source_limit', 'observation': q['question'],
            'evidence_limit': q['evidence_limit'], 'proposed_change': q['handling'],
            'dependencies': q['dependent_places'], 'resolution_status': 'unresolved',
            'blocking': False, 'decision': 'not_individually_adjudicated_by_author',
            'source': (STRUCTURE / 'decisions-and-questions.json').relative_to(ROOT).as_posix(),
            'verification': {'scope': 'structure and source boundary; prose not yet written'}
        })
    for issue in issues['items']:
        if issue['id'] == 'KONTAKT-REV-20260921-18':
            issue['current_execution_override'] = {
                'basis': 'Explicit author request 2026-09-23',
                'workflow': '../../series/WORKFLOW-2026-09-23-REVISION-AND-BOOK02.md',
                'text': 'Historical progressive-sequence resolution preserved; current execution requires entire structure and all rough chapters before Terra full prose.'
            }
    save(BOOK / 'audit/issues.json', issues)
    progress = read(RUN / 'progress.json')
    progress['phases'][0]['status'] = 'complete'
    progress['phases'][0]['gate'] = 'root-structure-gate.json'
    progress['phases'][1]['status'] = 'in_progress'
    progress['active_structure'] = 'structure-v2'
    save(RUN / 'progress.json', progress)
    book = read(BOOK / 'book.json')
    book['stage'] = 'astra_full_book_rough_drafting'
    book['audit_status'] = 'whole_structure_gate_passed_prose_pending'
    book['active_structure'] = {'path': 'production/2026-09-23-book02/structure-v2/full-outline.md', 'sha256': sha(STRUCTURE / 'full-outline.md')}
    save(BOOK / 'book.json', book)
    session = BOOK / 'session.md'
    session.write_text('# Том 2 — усі первинні чернетки Astra\n\nПовна структура: 36 глав, 41 сцена; пройдено координаторську звірку. Активна версія: [structure-v2](production/2026-09-23-book02/structure-v2/full-outline.md).\n\nAstra пише фактичну прозу всіх первинних чернеток. Terra починає повний текст лише після завершення й перевірки всього цього етапу. Далі — чотири незалежні літературні діагнози, звірка Astra та підсумкова правка Terra. Opus можна пропустити лише за фактичної недоступності відповідно до доручення автора.\n\nОснова продовження: виправлений перший том v4, коміт 5728141. Це робочі редакції; master не призначено. П’ять обмежених невідомих збережено в audit/issues.json.\n\n[Поточний стан](production/2026-09-23-book02/progress.json).\n', encoding='utf-8', newline='\n')
    mirror(session)
    mirror(Path(__file__).resolve())
    print(json.dumps({'structure_gate': gate['status'], 'chapters': 36, 'scenes': 41, 'unknowns': len(questions)}))
