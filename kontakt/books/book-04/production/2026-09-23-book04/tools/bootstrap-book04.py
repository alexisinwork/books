"""Record the author-authorized transition without promoting a planned or working master."""
from pathlib import Path
import hashlib,json,shutil
root=Path(__file__).resolve().parents[6]
run=Path(__file__).resolve().parent.parent
book=run.parent.parent
before=run/'initial-before';assert not before.exists();before.mkdir(parents=True)
paths=[book/'book.json',book/'session.md',book/'NEXT-STEP.md',root/'kontakt/START_HERE.md']
for f in paths:
 d=before/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
workflow='../../series/WORKFLOW-2026-09-23-BOOK04.md'
d=json.loads((book/'book.json').read_text(encoding='utf-8'));d.update(stage='detailed_structure_in_progress',audit_status='book04_full_workflow_in_progress',active_workflow=workflow);write(book/'book.json',d)
write(run/'progress.json',{'book_id':'book-04','status':'astra_full_structure_in_progress','workflow':workflow,'structure':'in_progress','all_rough_drafts':'not_started','terra_full_prose':'not_started','independent_reviews':'not_started','astra_reconciliation':'not_started','terra_final_revision':'not_started','final_full_reading':'not_started','delivery':'not_started','master':None,'predecessor':{'path':'kontakt/books/book-03/production/2026-09-23-book03/terra-final-v2/assembled/manuscript.md','sha256':'fa99f3a2667e4ad316ad4239e39c3f4887af09d5d45a5eeb2b1c04b385ad91a6','commit':'b1d849735c3da40542f109c186fb7c5b187c3d37'}})
session='# Контакт 4 — повна структура Astra\n\nАвтор доручив після завершення третього тому виконати четвертий за тією самою схемою. [Порядок роботи]('+workflow+'). Третій том завершено й відправлено: `b1d8497`.\n\nЗараз Astra звіряє весь макрокаркас і створює повну детальну структуру з фактичного фіналу третього тому. Проза четвертого тому ще не написана; planned-реєстри не є свідченням подій. Master не призначено. [Прогрес](production/2026-09-23-book04/progress.json).\n'
(book/'session.md').write_text(session,encoding='utf-8',newline='\n')
(book/'NEXT-STEP.md').write_text('# Наступний етап\n\nЗавершити й перевірити всю структуру Astra; після координаторської звірки написати всі первинні чернетки Astra, потім передати весь том Terra. [Чинний порядок]('+workflow+'). Старий поетапний маршрут у plan.md збережено як історію підготовки.\n',encoding='utf-8',newline='\n')
start=root/'kontakt/START_HERE.md';old=start.read_text(encoding='utf-8');start.write_text('# Контакт — том 4 у роботі\n\nТоми 1–3 завершені як робочі редакції. Автор доручив продовжити четвертий за тією самою схемою. [Порядок](series/WORKFLOW-2026-09-23-BOOK04.md) · [Прогрес](books/book-04/production/2026-09-23-book04/progress.json).\n\n## Попередня контрольна точка\n\n'+old,encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK04-2026-09-23')
for f in [*paths,run/'progress.json',root/'kontakt/series/WORKFLOW-2026-09-23-BOOK04.md',Path(__file__).resolve(),*[f for f in before.rglob('*') if f.is_file()]]:
 dest=desktop/f.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);assert f.read_bytes()==dest.read_bytes()
print('Book4 workflow and initial state recorded and mirrored.')
