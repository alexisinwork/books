"""Record completed coordinator planning-source reading, not an unwritten-book verdict."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
names=['kontakt/AGENTS.md','kontakt/project.json','kontakt/START_HERE.md','kontakt/books/book-04/book.json','kontakt/books/book-04/BOOK-04-ARCHITECTURE-LOCK.md','kontakt/books/book-04/KONTAKT_BOOK_04_CHAPTER_SKELETON_V1.md','kontakt/books/book-04/COMPATIBILITY-MECHANICS.md','kontakt/books/book-04/PRE-DRAFT-LOCK.md','kontakt/books/book-04/voice.json','kontakt/books/book-04/brief.md','kontakt/books/book-04/CARRY-IN-FROM-BOOK-03.md','kontakt/books/book-04/characters.planned.json','kontakt/books/book-04/knowledge.planned.json','kontakt/books/book-04/timeline.planned.json','kontakt/books/book-04/audit/issues.json','STYLE.md','kontakt/STYLE.md','BOOK_SYSTEM/CORE.md','BOOK_SYSTEM/WRITING.md','BOOK_SYSTEM/LANGUAGES/uk/STYLE.md','BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md','kontakt/series/CANON-POLICY.md','kontakt/series/glossary.json']
# START_HERE/book.json were read before this run's bootstrap; retain those exact bytes.
overrides={n:run/'initial-before'/n for n in ['kontakt/START_HERE.md','kontakt/books/book-04/book.json']}
files=[]
for name in names:
 p=overrides.get(name,root/name)
 files.append({'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'complete planning/source document displayed and read; truncated ranges separately reread'})
data={'status':'initial_source_reading_complete_structure_gate_pending','reader':'root coordinator','files':files,'findings':['Actual Book3 source governs carry: comparable uncertainty, not identical private inputs; budget limit, not expenditure.','Osya revoked old excerpts; only a narrow anonymous comparison remains. New disclosures require new on-page permission.','A new temporary sponsor certificate cannot silently restore the suspended then voluntarily closed calibration profession.','Book4 supplement wording about already-known value criterion and destroyed score is superseded by actual predecessor and active macro constraints.','Edith outcome requires finite funding and independently valid residency; sponsor withdrawal must not void it.','K-17 remains a living care client; Book5 mechanism and worker identities are not disclosed.','Historical progressive/Sol workflow superseded by explicit all-structure/all-rough/Terra-full instruction.'],'limits':['No Book4 prose exists or has been reviewed.','Astra detailed structure is still being prepared; no gate inferred.','Legacy canon/master remains unselected.','These are coordinator notes, not an independent editorial diagnosis.']}
out=run/'initial-root-reading.json';assert not out.exists();out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK04-2026-09-23')
for p in [out,Path(__file__).resolve()]:
 d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
print(json.dumps({'sources':len(files),'status':data['status']}))
