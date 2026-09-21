"""Build the fixed review evidence package; never promote plans or modify prose."""
from pathlib import Path
import hashlib, json, re, shutil, subprocess, sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DOWNLOADS = Path("C:/Users/alexi/Downloads")
DESKTOP = Path("C:/Users/alexi/OneDrive/Desktop/KONTAKT-ARCHITECTURE-REVIEW-2026-09-21")
RUN = "kontakt-downloads-review-2026-09-21"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding="utf-8-sig"))
def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
def rel(p): return p.relative_to(ROOT).as_posix()
def book(n): return ROOT / f"kontakt/books/book-{n:02d}"
def sk(n): return DOWNLOADS / f"KONTAKT_BOOK_{n:02d}_CHAPTER_SKELETON_V1.md"
def lock(n): return book(n) / f"BOOK-{n:02d}-ARCHITECTURE-LOCK.md"
def anchor(p, needle):
    lines=p.read_text(encoding="utf-8-sig").splitlines()
    hits=[(i+1,line) for i,line in enumerate(lines) if needle in line]
    if not hits: raise ValueError(f"Missing evidence: {p}: {needle}")
    i,line=hits[0]
    source = (OUT/"sources"/p.name) if p.parent == DOWNLOADS else p
    return {"file":rel(source),"original_path":str(p),"sha256":sha(p),"line":i,"quote":line}

# Validate all evidence and audit schemas before writing audit registers.
specs=[
("01",[1],"major","text_conflict","Nina is available locally; the new plan incorrectly treats her history as missing.",
 "Use the existing former-partner/long-illness/self-companion history and Dal's safe-presence authorship; keep the early reveal limited.",
 [(sk(1),"В GitHub этого канона сейчас нет"),(lock(1),"Нина — бывшая партнёрша")],
 ["book-01 chapters 1,2,3,11,13,22-24","book-05 personal grief history"]),
("02",[1],"major","text_conflict","Book 1 moves the R1 transition and changes Maya's protected final action.",
 "Map early R1 breakthrough to later consolidation; retain independent departure unless explicitly revised.",
 [(sk(1),"R1 фиксируется как практическое состояние"),(sk(1),"Предлагаемая locked-выплата"),(lock(1),"### S04 — Присутствие / R1"),(lock(1),"выбирает нейтральное жильё")],
 ["book-01 chapters 9-11,26-33","book-01 timeline/knowledge/end-state"]),
("03",[2,3],"major","text_conflict","Relay restores the betrayal removed by the macro package and alters the evidence leading into Predictariat.",
 "Prefer the no-traitor version; keep advance-capacity evidence and the incomplete attention theory as separate causes.",
 [(sk(2),"Релей — человеческое предательство"),(lock(2),"Тайный предатель убран")],
 ["book-02 chapters 15,19-22,37-38","book-03 opening"]),
("04",[2],"major","text_conflict","Ira is replaced by Miron and Taras becomes the subject of civil-identity restoration.",
 "Choose and map the cast; preserve Taras's independent continuity work and test the ending against a repeated rescue structure.",
 [(sk(2),"Мирон** — рабочее имя"),(sk(2),"Его гражданская непрерывность восстановлена"),(lock(2),"Тарас показывает кейс Иры")],
 ["book-02 chapters 1-3,22,28-35","book-03 Taras carry-in"]),
("05",[2],"major","text_conflict","Emergency-message consequences of the outage are not reconciled with protected emergency/identity infrastructure.",
 "State exactly which ranking layer fails and keep emergency/identity service boundaries explicit.",
 [(sk(2),"аварийные и бытовые сообщения конкурируют"),(lock(2),"emergency/identity infrastructure")],
 ["book-02 outage mechanics and chapters 5,10,20-25"]),
("06",[3,4,5,6,7,8],"major","text_conflict","Osya's courier profession becomes repair apprenticeship without updating downstream carry-ins.",
 "Prefer retaining the desired courier route, or explicitly propagate the adopted profession through all later plans.",
 [(sk(3),"ученичество/работу в ремонтной мастерской"),(lock(4),"Ося жив, вернулся к желанной курьерской работе")],
 ["book-03 resolution","books 4-8 Osya work, access and logistics"]),
("07",[3],"major","missing_link","Book 3 starts a less-than-60-hour review clock on Day 1 but its main deadline resolves on Day 5.",
 "Give the first review an outcome and a documented later offer/extension, or revise the relative clock.",
 [(sk(3),"остаётся меньше 60 часов"),(sk(3),"## День 5"),(sk(3),"До 17:40 следующего дня")],
 ["book-03 chapters 5,11,27-30","book-03 timeline"]),
("08",[4],"major","missing_link","Book 4's new chapter skeleton is absent from the inspected Downloads directory.",
 "Obtain the intended new skeleton or explicitly retain the existing twelve-sequence plan; do not claim the missing plan was reviewed.",
 [(lock(4),"поглавная сетка намеренно не фиксируется")],
 ["book-04 chapter coverage","book-03 to book-04 and book-04 to book-05 handoffs"]),
("09",[4,5],"major","text_conflict","K-17 is a client in the repository; the new Book 5 opens with worker Lev without a mapped connection.",
 "Keep K-17's client-side evidence and introduce Lev as a distinct downstream worker, or explicitly revise Book 4.",
 [(lock(5),"K-17 был **клиентом**, а не carrier"),(sk(5),"Даль находит Льва в программе")],
 ["book-04 S12","book-05 chapters 1,17 and carry-in"]),
("10",[5,6],"major","text_conflict","Taras's death changes from delayed split-relay complication to fatal equipment-isolation injury.",
 "Choose one causal package. Prefer delayed loss editorially; if using hardware failure, specify power/cooling, protection and shutdown dependencies.",
 [(lock(5),"Через несколько часов у Тараса развивается"),(sk(5),"Перегруженный силовой/охлаждающий модуль выходит из строя")],
 ["book-05 chapters 9,15,19-21,24-34","book-06 grief carry-in","later memories of Taras"]),
("11",[5],"major","text_conflict","Dal's genuinely helpful voluntary relief session is replaced by stopping before the session.",
 "Prefer retaining the transparent, helpful session as experienced counterevidence to a simplistic rejection of relief.",
 [(lock(5),"Сессия реально помогает"),(sk(5),"Даль всё равно не запускает сессию")],
 ["book-05 chapters 22,28-30","Dal's relief/avoidance arc"]),
("12",[5,6,7],"major","missing_link","The new Book 5 ending points directly toward emergency origins and drops the concrete child-Guidance discovery.",
 "Restore the child-cohort clue before the Book 6 invitation, then the adult-framework clue before Book 7.",
 [(sk(5),"От чего мир пытались обезболить"),(lock(5),"distress prevention upstream / ontogenetic guidance"),(sk(6),"Даль приходит по приглашению Ждана")],
 ["book-05 chapter 35","book-06 opening and ending","book-07 opening"]),
("13",[6,7,8],"major","text_conflict","Marta becomes Mila's mother and Zhdan's co-designer partner; the established bereavement is not reconciled.",
 "Record the proposed family relationship explicitly and settle the older-son history before using it in prose.",
 [(sk(6),"Марта и Ждан — родители Милы"),(lock(6),"её старший сын-подросток погиб")],
 ["book-06 family chapters","books 7-8 family continuity"]),
("14",[6],"major","missing_link","The intimate parental conversation in Chapter 16 has no explicit route into Dal's first-person narration.",
 "Specify Dal's presence, later account or a permitted document; do not silently introduce another internal POV.",
 [(sk(6),"Ждан признаётся Марте"),(ROOT/"kontakt/series/PRE-DRAFT-LOCK-2026-09-19.md","Свободных сцен «без героя» нет")],
 ["book-06 chapter 16","other offstage-family scenes"]),
("15",[7,8],"major","text_conflict","A 72-hour review for Mila/Osya replaces Dal's independent twelve-day workshop decision; the long-term commitment becomes housing.",
 "Prefer the personal five-year workshop climax, independent of others' welfare; reconcile any ancillary review with existing assent rights.",
 [(sk(7),"Deadline: 72 часа"),(sk(7),"долгий договор на жильё"),(lock(7),"Проект НЕ зависит от его подписи"),(lock(7),"пятилетний long-horizon lease"),(lock(8),"Он подписал пятилетний договор мастерской")],
 ["book-07 entire climax","book-08 workshop/support-hub carry-in"]),
("16",[8],"major","text_conflict","Book 8 replaces the Varan family/Eva cast and detention-return plot with Kosta/Nika/M-17, and compresses war time and duration.",
 "Choose a complete edition, not an implicit rename. Prefer the connected family and longer timescale while considering the new triage tests.",
 [(lock(8),"девятом месяце войны"),(lock(8),"Илья возвращается после длительного удержания"),(sk(8),"Ян Коста, 31 год"),(sk(8),"основной сюжет романа занимает 9 суток")],
 ["book-08 characters, timeline, evidence/status, ending","book-07 to book-08 handoff"]),
("17",[8],"major","missing_link","M-17 is already in the Western hospital belt, but later transport stakes lack explicit origin, destination and clinical purpose.",
 "Specify the purpose and safety of each transfer; distinguish identification, transport and treatment urgency.",
 [(sk(8),"M-17 перевели через промежуточный медицинский конвой в Западный пояс"),(sk(8),"Появляется транспортное окно для Яна"),(sk(8),"День 9:** гл.28–36")],
 ["book-08 chapters 16-18,24-36","transport ledger","pilot/reform timescale"]),
("18",[1,2,3,4,5,6,7,8],"major","text_conflict","New skeletons require all-sequence scene cards before prose, while the runbook requires progressive sequence work; execution metadata remains stale.",
 "Use provisional whole-book maps and detail S01 first; synchronize selected planned sources and voice placeholders without presenting planned events as observed facts.",
 [(sk(1),"только после полного архитектурного gate"),(book(1)/"NEXT-STEP.md","Завершить S01 и лишь затем S02"),(book(1)/"voice.json",'\"tense\": \"Выбрать\"')],
 ["all books' working source pointers and planned states","Book 1 opening execution package"])
]
issues=[]
for num,books,severity,certainty,observation,proposal,refs,deps in specs:
    issues.append({"id":f"KONTAKT-REV-20260921-{num}","run_id":RUN,"category":"architecture",
        "severity":severity,"certainty":certainty,"book_ids":[f"book-{b:02d}" for b in books],
        "anchors":[anchor(p,n) for p,n in refs],"observation":observation,
        "reader_effect":"Unreconciled drafting inputs may change causality, identity, agency or reveal timing.",
        "proposed_change":proposal,"dependencies":deps,
        "verification":{"method":"source comparison","scope":"planning only","prose_review":"not_run"},
        "decision":"proposed","resolution_status":"unresolved"})
registers={}
for n in range(1,9):
    p=book(n)/"audit/issues.json"; data=read(p)
    assert isinstance(data["items"],list)
    assert not any(i.get("run_id")==RUN for i in data["items"]), "Run already recorded; do not duplicate or overwrite."
    registers[n]=(p,data)

(OUT/"sources").mkdir(exist_ok=True)
sources=[]
for p in sorted(DOWNLOADS.glob("*.md")):
    q=OUT/"sources"/p.name; shutil.copy2(p,q)
    assert sha(p)==sha(q)
    sources.append({"original_path":str(p),"snapshot":rel(q),"sha256":sha(p),"bytes":p.stat().st_size,
                    "coverage":"full_read","authority":"review_input_not_adopted"})
for n in range(1,9):
    for p in [lock(n),book(n)/"book.json"]:
        sources.append({"path":rel(p),"sha256":sha(p),"coverage":"full_read"})
for p in [ROOT/"kontakt/project.json",ROOT/"kontakt/START_HERE.md",
          ROOT/"kontakt/series/PRE-DRAFT-LOCK-2026-09-19.md",ROOT/"kontakt/series/CANON-POLICY.md",
          ROOT/"kontakt/series/continuity-queue.json",
          *[book(1)/f for f in ["WORLD-MECHANICS.md","voice.json","brief.md","session.md","timeline.planned.json",
                               "AI-RUNBOOK.md","QUALITY-GATES.md","NEXT-STEP.md","ai-prompts/02-SCENE-CARDS.md"]]]:
    sources.append({"path":rel(p),"sha256":sha(p),"coverage":"full_read_reference"})
write(OUT/"source-manifest.json",{"run_id":RUN,"sources":sources,"missing":["Downloads Book 04 chapter skeleton"],
    "scope":"Full seven chapter plans and eight macro lock documents; targeted supporting references. Other package files mechanically verified only."})
write(OUT/"decision-ledger.json",{"run_id":RUN,"status":"proposed_not_author_approved","items":issues})
for n,(p,data) in registers.items():
    additions=[i for i in issues if f"book-{n:02d}" in i["book_ids"]]
    data["items"].extend(additions)
    write(p,data)

counts=[]
for n in [1,2,3,5,6,7,8]:
    s=sk(n).read_text(encoding="utf-8-sig")
    nums=[int(x) for x in re.findall(r"^## Глава (\d+)\.",s,re.M)]
    assert nums==list(range(1,len(nums)+1))
    counts.append({"book":n,"chapters":len(nums),"consecutive":True})
hashes=[]
for m in sorted((ROOT/"kontakt/books").glob("book-*/pass01-manifest.json")):
    for item in read(m)["files"]:
        p=ROOT/"kontakt/books"/item["path"]
        actual=sha(p); assert actual==item["sha256"]
        hashes.append({"file":rel(p),"expected":item["sha256"],"actual":actual,"match":True,"coverage":"mechanical_only"})
proc=subprocess.run([sys.executable,"tools/studio.py","doctor"],cwd=ROOT/"kontakt",
                    capture_output=True,encoding="utf-8",check=True)
doctor=json.loads(proc.stdout); assert not doctor["errors"]
write(OUT/"verification.json",{"run_id":RUN,"chapter_checks":counts,"total_chapters":sum(x["chapters"] for x in counts),
    "package_entries_checked":len(hashes),"package_checks":hashes,"doctor":doctor,
    "issues_recorded":len(issues),"prose_review":"not_run","ensemble_review":"not_run",
    "source_originals_unchanged":all(sha(Path(s["original_path"]))==s["sha256"] for s in sources if "original_path" in s)})
# Copy every new review artifact and modified book register, retaining relative structure.
review_files=[p for p in OUT.rglob("*") if p.is_file()]
changed=[p for p,_ in registers.values()]
checks=[]
for p in review_files+changed:
    dest=DESKTOP/rel(p); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dest)
    assert sha(p)==sha(dest)
    checks.append({"source":rel(p),"desktop":str(dest),"sha256":sha(p),"match":True})
delivery={"run_id":RUN,"desktop_root":str(DESKTOP),"files":checks,
          "note":"This manifest excludes itself; its repository and desktop copies are checked after writing."}
write(OUT/"delivery-manifest.json",delivery)
dest=DESKTOP/rel(OUT/"delivery-manifest.json")
shutil.copy2(OUT/"delivery-manifest.json",dest)
assert sha(dest)==sha(OUT/"delivery-manifest.json")
print(json.dumps({"issues":len(issues),"chapters":sum(x["chapters"] for x in counts),
                  "package_hashes":len(hashes),"doctor_errors":doctor["errors"],
                  "desktop_files":len(checks)+1,"report":str(OUT/"REVIEW-AND-NEXT-STEP.md"),
                  "desktop_report":str(DESKTOP/rel(OUT/"REVIEW-AND-NEXT-STEP.md"))},ensure_ascii=False,indent=2))
