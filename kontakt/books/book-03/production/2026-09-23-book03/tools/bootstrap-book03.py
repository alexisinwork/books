"""Record the authorized next-volume workflow and exact predecessor, preserving metadata."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;book=run.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
source=root/'kontakt/books/book-02/production/2026-09-23-book02/terra-final-v3/assembled/manuscript.md'
assert sha(source)=='07a68dad4276cd81e98f077796d17f56f3b21cdcef64f8231a71524d054a78f4'
archive=run/'bootstrap-before';archive.mkdir(exist_ok=False)
for name in ['book.json','session.md','NEXT-STEP.md']:
    shutil.copy2(book/name,archive/name)
meta=json.loads((book/'book.json').read_text(encoding='utf-8'))
meta.update(stage='full_architecture_in_progress',audit_status='full_scene_architecture_pending',active_workflow='../../series/WORKFLOW-2026-09-23-BOOK03.md',execution_entry='production/2026-09-23-book03/progress.json',current_writer='Astra structure and all rough; Terra full prose and final revision')
meta['draft_scope']={'prose_started':False,'whole_book_written':False,'whole_book_ready':False,'whole_series_ready':False}
meta['continuation_source']={'book_id':'book-02','path':source.relative_to(root).as_posix(),'sha256':sha(source),'status':'author_authorized_working_continuation_basis_not_canonical_promotion'}
write(book/'book.json',meta)
write(run/'progress.json',{'author_request':'том 3 погнали','workflow':'../../../../series/WORKFLOW-2026-09-23-BOOK03.md','predecessor_sha256':sha(source),'predecessor_commit':'a95bdf4068f795cdaac92294ea22473efc328c78','phases':[{'phase':name,'actor':actor,'status':'in_progress' if i==0 else 'not_started'} for i,(name,actor) in enumerate([('full_structure','Astra'),('all_rough_chapters','Astra'),('all_full_chapters','Terra'),('independent_literary_reviews','Fresh Terra; agy Gemini3.8Flash, Gemini3.1Pro, Opus if available'),('reconciliation_and_full_check','Astra'),('final_compatible_revision','Terra'),('final_full_reading_and_delivery','Astra and coordinator')])],'canonical_master_assigned':False})
(book/'session.md').write_text('# Том 3 — повна архітектура\n\nАвтор: «том 3 погнали». Продовжуємо підтверджений порядок Astra → Terra → редакторський ансамбль → Astra → Terra. Наразі розгортається весь макроплан у повну послідовність глав і сцен. Прози третього тому ще немає.\n\nФактичний вхід — виправлений том 2, SHA `'+sha(source)+'`. Стара планова нотатка про cache не підміняє фактичні витяги й межі знання Даля. [Прогрес](production/2026-09-23-book03/progress.json).\n\nПопередню сесію й метадані збережено у bootstrap-before. План і майбутній текст не підвищуються в канон автоматично.\n',encoding='utf-8',newline='\n')
(book/'NEXT-STEP.md').write_text('# Наступна дія — том 3\n\nПоточна фаза: завершити ВСЮ архітектуру Astra у production/2026-09-23-book03/structure-v1. Після перевірки — усі первинні чернетки Astra, потім повний текст Terra. Старе обмеження лише S01 збережене в bootstrap-before і замінене підтвердженим авторським порядком.\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [root/'kontakt/series/WORKFLOW-2026-09-23-BOOK03.md',book/'book.json',book/'session.md',book/'NEXT-STEP.md',run/'progress.json',Path(__file__).resolve(),*archive.iterdir()]:
    d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print(json.dumps({'status':'book03_architecture_started','predecessor_sha256':sha(source)}))
