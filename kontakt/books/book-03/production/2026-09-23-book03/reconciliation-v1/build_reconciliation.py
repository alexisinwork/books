from pathlib import Path
import json, hashlib, re, shutil, collections, subprocess

ROOT=Path(__file__).resolve().parents[6]
RUN=ROOT/'kontakt/books/book-03/production/2026-09-23-book03'
OUT=RUN/'reconciliation-v1'
DESK=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
SRC=RUN/'terra-full-v1/assembled/manuscript.md'
SHA='ab11580a6c9adcaa9a3af4696a4466979e38f6e138633e5230f802d675ff1c6b'
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def rel(p): return p.relative_to(ROOT).as_posix()
def write(name,data):
    p=OUT/name
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n' if not isinstance(data,str) else data.rstrip()+'\n',encoding='utf-8',newline='\n')
    q=DESK/p.relative_to(ROOT); q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,q)
assert h(SRC)==SHA
text=SRC.read_text(encoding='utf-8'); blocks=read(OUT/'source-blocks.json')['blocks']; by={int(x['id'][1:]):x for x in blocks}
cards=read(RUN/'structure-v1/chapter-scene-cards.json'); states=read(RUN/'terra-full-v1/observed-state.json')
issues=[]; patches=[]; metas=[]; checks=[]
def evidence(ps):
    return [dict(source=rel(SRC),source_sha256=SHA,chapter=by[p]['chapter'],paragraph=by[p]['id'],quote=by[p]['text']) for p in ps]
def issue(id,origins,ps,observation,decision,rationale,severity='minor',confidence='high',category='language'):
    row=dict(id=id,origins=origins.split('|'),severity=severity,confidence=confidence,category=category,observation=observation,evidence=evidence(ps),disposition=decision,rationale=rationale,author_decision='pending',implementation_authority='Existing explicit whole-book correction instruction; no individual author vote inferred',patch_ids=[],metadata_ids=[])
    issues.append(row); return row
def patch(row,p,direction,preserve='',dependencies=()):
    id=f'B03-P{len(patches)+1:03d}'; b=by[p]
    assert text.count(b['text'])==1,(p,text.count(b['text']))
    row['patch_ids'].append(id)
    patches.append(dict(id=id,issue_ids=[row['id']],chapter=b['chapter'],paragraph=b['id'],before=b['text'],direction=direction,preserve=preserve or 'Preserve scene outcome, point of view, established chronology and permissions.',dependencies=list(dependencies),source_sha256=SHA,implementation_status='compatible_bulk_authorized_for_native_Terra',after_author='native Terra; no final replacement authored by Astra'))
    return id
def add(id,origins,p,obs,direction,preserve='',severity='minor',category='language'):
    r=issue(id,origins,[p],obs,'compatible_correction',direction,severity,category=category); patch(r,p,direction,preserve); return r

# Source-bound actionable findings. Directions are editorial requirements, not final prose.
add('PRO-01','Pro final finding 1|Pro turn001 finding 1',102,'Громіздка форма погодженого часу зустрічі.','Name 19:20 naturally and unambiguously in Ukrainian; retain same evening and original appeal document request.')
r=add('FLASH-01','Flash final finding 1|Flash turn001 finding 1|root CH01–02',110,'Форма бахіл і залежні займенники; одночасно узгодження залишку часу.','Use the ordinary Ukrainian feminine form бахіла consistently with all modifiers and pronouns in this paragraph. Also render remaining time naturally with agreement (almost an hour remains). Preserve abandoned shoe-cover joke and upcoming 19:20 appointment.')
r2=issue('FLASH-02','Flash final finding 2|Flash turn001 finding 2',[110],'Лишалося майже годину: часова конструкція потребує узгодження.','compatible_correction','Correct together with FLASH-01 in the same paragraph.');r2['patch_ids']=r['patch_ids'].copy();patches[-1]['issue_ids'].append(r2['id'])
patch(r,147,'Apply the same feminine shoe-cover noun and agreement used in P00110; preserve apparent movement toward the drain.','Do not remove the callback joke.',[r['patch_ids'][0]])
patch(r,148,'Make the pronoun refer consistently to the feminine shoe cover from P00110/P00147; preserve Dal stepping around it, without inventing another object.','Only noun/pronoun agreement changes.',r['patch_ids'][:2])
add('ASTRA-01','Astra actual full reread',185,'Рядок допускає рух, але відсутність імені не доводить незнання моделі.','Limit the claim to what this displayed row says or omits; do not assert that the model did not know the man at the door. Preserve the distinction between matching action class and unknown particular motive.',category='knowledge',severity='moderate')
add('PRO-02','Pro final finding 2|Pro turn001 finding 2',188,'Неприродне керування в оповідачевому поясненні болю.','Render the emotional pain with natural personal dative or equivalent construction; preserve Dal accepting Osya’s deliberately awkward preceding phrase. Do not correct Osya’s own phrase into a lecture.')
add('ROOT-01','root CH03–04|Astra actual full reread',204,'Особливо від людини не має потрібної предикативної опори.','Restore the missing judgment about how Dal’s proposed reassurance would sound coming from him. Keep his self-irony and his repeated Thursday16:10 checking, not a new explanation of the reserve.',severity='moderate')
add('PRO-03','Pro final finding 3|Pro turn001 finding 3|root CH05–06',420,'Видача названа в сцені повернення тари.','Name the still-open receiving/return window for the empty containers, not issuing. Do not identify this morning window with the separate 17:00 deadline for returning the borrowed cart.','Arrival10:25; forecast09:40–10:00 missed; containers accepted; cart still due17.')
add('ROOT-02','root CH05–06',435,'Осіної: присвійна форма вибивається з послідовного Осин.','Use the same possessive stem Осин- used elsewhere for Osya; preserve the decision to keep the cart until after the colleague meeting.')
add('ROOT-03','root CH07–09',545,'Ремені буквально тягнуть плечі догори, хоча вага діє вниз.','Show Osya’s raised/tense shoulders or the straps pressing them with physically coherent wording. Preserve tiredness and the bag; do not add an injury.')
add('ROOT-04','root CH10–12',643,'На зло тут означає навмисну протидію, не предмет зло.','Write the intended adverb назло in the self-pickup motive. Preserve that Osya wanted personal responsibility, not merely spite.')
add('FLASH-04','Flash final finding 4|Flash turn002 finding 1',776,'Лоц заперечує істинність казки, а граматично наче сперечається з казкою.','Make the target of disagreement explicit: the claim that order has no effect. Preserve his acceptance of the right to choose an unpersonalized order and his measured voice; no universal normative claim about every use of заперечувати.')
add('FLASH-05','Flash final finding 5|Flash turn002 finding 2',893,'Злитий запис що з числівниковою групою.','Use natural separate temporal phrasing for every ten minutes; preserve Dal’s irritation and the bounded practical list.')
add('ASTRA-02','Astra actual full reread',961,'Осею є орудним після відмовляв, поряд із давальним Тарасові.','Use dative Осі parallel to Тарасові; preserve that Ballast did not send refusals and Dal himself declined both optional contacts.')
r=add('ROOT-05','root CH22–24|structure B03-CH22-SC01|Astra actual full reread',1091,'Зникло джерело модельної невизначеності; лишилася звичайна карта.','Restore a brief directly shown, narrowly permitted technical uncertainty/coverage field for this route, distinct from the ordinary transport map and weak communications. Osya chooses to show this limited field; no whole-file access and no new future branch content. Establish lower confidence from sparse/old model inputs as the reason for his interest.','Keep Thursday noon version, ordinary right to leave, no invisibility or guaranteed escape.',severity='moderate',category='missing_link')
dep=r['patch_ids'][0]
patch(r,1141,'Tie wider model uncertainty explicitly to the limited field seen before travel, not to slow map loading or phone signal. Preserve the concrete broken stairs and that uncertainty does not improve infrastructure.','No prediction-free zone, truck ride, compulsory rescue or future-page reading.',[dep])
add('ROOT-06','root CH22–24|Flash turn002 finding 3 (misread premise, valid local timing concern)',1107,'Відповідь Розклад втратила часову підготовку.','Add a concise practical condition to Dal’s agreement: this is a look with a return by available ordinary transport, whose timetable he has checked. The next Умова / Розклад exchange must answer that condition. No invented exact last bus at19:00; no claim they boarded the onward freight vehicle.','Osya freely agrees and may return earlier; no restriction on his travel rights.',severity='moderate',category='scene_causality')
add('ROOT-07','root CH22–24',1125,'Водій ковтає ціле яблуко замість шматка перед реплікою.','Name swallowing the bite/piece he was eating before speaking; preserve apple and driver’s ordinary work.')
add('ROOT-08','root CH25–27',1221,'Ося чує усмішку без названого звуку.','Make Osya notice the smile visually; preserve his brief answering smile and release of the buckle. Do not invent a loud laugh.')
add('ROOT-09','root CH25–27',1236,'У четвер попередній запит із понеділка названий учорашнім.','Refer to the earlier own-file request without yesterday; Monday request/Tuesday viewing remain unchanged. This Thursday paragraph prepares a new Friday appointment.',severity='moderate',category='chronology')
add('ROOT-10','root CH25–27|Astra actual full reread',1250,'Оповідач виключає всі невідомі входи моделі за обмеженим переліком.','Confine knowledge to the displayed input list and what Dal himself did not transmit. Do not assert complete model ignorance of all other facts or profiles. Retain known prior requests/readings and unknown private inputs.',severity='moderate',category='knowledge')
add('PRO-10','Pro final finding 10|Pro turn003 finding 2',1317,'Частина повернення тари входила не називає обсягу зобов’язання.','State that collecting/returning containers belongs to this agreed route only at addresses where explicitly listed; extra tasks need separate agreement. Do not invent a new tariff, free work, time allowance or wage change. Preserve08start and Monday-known pay.')
add('ROOT-11','root CH28–30',1354,'Вантаж береться назад, хоча вага не переходила до Даля.','Keep Dal steadying the bag while Osya tightens the strap; remove implied return of transferred weight. Continue walking at green. Do not invent a handoff.')
add('ROOT-12','root CH28–30|structure B03-CH29-SC02|Astra actual full reread',1370,'Новий вузький запит і видавання метаданих не отримали події перед CH31.','After Dal agrees to delete the temporary copy, show the two owners submitting their bounded requests for matching support metadata/executed actions, excluding future contents and private correspondence. Show reception registration and confirmation that the extracts will be available for their15:00 comparison. Keep the meeting in the reading room, not an invented booked face-to-face15:00 appointment with Lotz. Do not reveal values or budget inequality yet.','Separate originals and consents; Taras noon visit afterward; actual comparison onlyCH31.',severity='moderate',category='missing_link')
add('ROOT-13','root CH28–30',1398,'Третю не узгоджується з входом або дверима.','Have Taras ask about the third entrance with unambiguous matching noun/gender; preserve Osya’s following joke about guided tours around the building.')
add('ROOT-14','root CH31–32',1469,'Осе після показав: потрібен давальний відмінок Осі.','Use the established dative Осі. Keep showing the draft before sending.')
add('FLASH-07','Flash final finding 7|Flash turn003 finding 1|root CH31–32',1538,'Жодного може стосуватися номера, не непрочитаних сторінок.','Explicitly state that no remaining future page was opened. Keep the new registered query number saved; do not claim he never opened the query or delete it. Preserve final bread choice and unknown future.',severity='moderate',category='knowledge_language')

# Contextual adjudication of every other formal reviewer finding and root candidate.
preserved=[
('TERRA-01','Terra final finding 1',[565,566,382,512],'Підпис і п’ята можуть вимагати уточнення.','preserve_for_function','The explicit17:00 loan and17:30 return already establish the comparison. The short final signed deadline lands as self-indictment; adding a table tutorial weakens it.'),
('TERRA-02','Terra final finding 2',[417],'Набрав відмову може бути уточнено.','contextual_style_choice','Natural message metonymy after opening the offer; no ambiguity about actual refusal, not a formal refusal from an institution. Reviewer anchor416 corrected to417.'),
('TERRA-03','Terra final finding 3',[1457,1458,1462],'Рання професійна тінь для пояснення ліміту.','preserve_for_function','Profession is only one stated hypothesis; foreshadowing it as cause would overstate knowledge. Past status already matters inCH3/14. Actual budget difference is shown; its explanation is not.'),
('TERRA-04','Terra final finding 4',[1474,1513,1540],'Пізній гачок може відчуватися новою книжкою.','preserve_for_function','Human choices resolveCH27–30 before the locked Book4 question. Final ordinary action completes authorship while formula remains unknown; no added early budget lecture.'),
('FLASH-03','Flash final finding 3|Flash turn001 finding 3',[273],'Якщо б замість якби.','contextual_style_choice','Understandable conditional dialogue; no demonstrated error or damaged voice. Optional compression is not obligatory revision.'),
('FLASH-06','Flash final finding 6|Flash turn003 finding 2',[1258,1259,1246],'До вашого входу може означати вхід у кімнату або сеанс.','preserve_for_function','Adjacent paragraph explicitly distinguishes creation08 and viewingafter09; neither reading reverses order. No extra technical phrasing needed.'),
('FLASH-08','Flash final finding 8|Flash turn003 finding 3',[119],'Рената нібито випадковий релікт.','reviewer_misreading','Renata is established Book2 operator linked to the reserve. Not forwarding private evidence to her is meaningful restraint; no new cameo or false old profession.'),
('PRO-04','Pro final finding 4|Pro turn001 finding 4',[518,521,522,539],'Я поверну сусідам нібито нечіткий предмет.','preserve_for_function','Only substitute cart belongs to neighbors; loaded benches explicitly stay on it, address later supplied. A demonstrative gesture is optional, not missing causality.'),
('PRO-05','Pro final finding 5|Pro turn002 finding 1',[1116],'Абсолютна заборона пересадний для транспорту.','unsupported_normative_claim','No dictionary evidence supplied. Location/action clear. Do not turn a lexical preference into confirmed non-Ukrainian usage.'),
('PRO-06','Pro final finding 6|Pro turn002 finding 2',[1024],'Відхилився нібито означає лише ухилення вбік.','unsupported_normative_claim','Overly narrow unsupported definition. Leaning and knee striking table are intelligible; no new staging required.'),
('PRO-07','Pro final finding 7|Pro turn002 finding 3',[877],'Не робиться чеснотою → не стає.','contextual_style_choice','Conversational Tikhon statement keeps direct register; serious character need not sound maximally formal. No blanket change.'),
('PRO-08','Pro final finding 8|Pro turn002 finding 4',[1126,1134],'Щаблі → сходинки.','contextual_style_choice','Physical stairs already clear. Report itself labels taste; no mandatory normative verdict.'),
('PRO-09','Pro final finding 9|Pro turn003 finding 1',[1219,1220,1221],'Влучив повз нібито неможливий оксюморон.','preserve_for_function','Deliberate comic failure immediately paid by Osya telling the bag to just press. Preserve this joke; correct only the separate sensory error inP1221.'),
('FLASH-P1-04','Flash turn001 finding 4; dropped final',[300],'Родовий яких під запереченням.','already_correct','Provisional report admits legitimate genitive; final dropped it. Preserve negative scope.'),
('FLASH-P1-05','Flash turn001 finding 5; superseded turn002',[145,827,881],'Баласт припущений колишнім людським куратором.','reviewer_misreading_superseded','Later report correctly identifies software. Do not add suggested human biography; series carry already establishes service.'),
('FLASH-P2-03','Flash turn002 finding 3; dropped final',[1122,1134,1157,1164],'Нібито сіли у вантажівку без зворотного рейсу.','reviewer_misreading','They inspect the onward option but do not buy its ticket. Ordinary bus return occurs. Its invented19:00 deadline/forced overnight must not be imported. Actual timetable-joke omission separatelyROOT-06.'),
('ROOT-15','root CH01–02|Astra actual full reread',[81],'Пряма згадка художнього прийому вибивається з голосу.','optional_taste','One knowingly self-conscious dry aside can be read as Dal humor. Flag literary preference but do not mandate removal or police every metaphor.'),
('ROOT-16','root CH03–04',[281],'Дивлячись у неї: таблиця чи людина.','contextual_style_choice','He closes table to answer person; local referent recoverable. No causal defect.'),
('ROOT-17','root CH07–09',[500,512],'Перехід від рами до17:30 стислий.','preserve_for_function','Time gap is implicit, no contradictory clock. Consequence enacted by substitute cart and benches; no need fabricate an extra delay scene.'),
('ROOT-18','root CH10–12',[651,703,704,707],'Наступна зустріч перед відповіддю знайомого.','preserve_for_function','Prior Lotz appointment time remains knownP651. This need not name the as-yet-unconfirmed witness call. State must not invent its premature confirmation.'),
('ROOT-19','root CH16–18',[904,913,918,932],'Повтори запевнень/спина на спинці.','optional_taste','Procedural texture serves finite delegation; some assurances slightly explanatory but clauses do different work. No wholesale smoothing or elimination of rest required.'),
('ROOT-20','root CH25–27',[1215,1222,1223,1226,1231],'Порада поспати може привласнювати рішення.','preserve_for_function','Osya already chose no more travel, invited Dal, and retains Friday decision; Dal recognizes controlling wish and leaves. No forced care occurs.'),
('ROOT-21','root CH28–30',[1402,1403],'Річ зробила це сама — пояснений жарт.','optional_taste','Handle physically splits and recalls freed handle; self-explanatory comment is taste. Preserve CH1 suspicion/CH30 confirmation instead of rewriting payoff.'),
('ASTRA-03','Astra actual full reread',[1213],'Оповідач пояснює небажання повернути ремінь на плече.','contextual_style_choice','Close local inference from carrying posture, not consequential hidden diagnosis. No new plot fact depends on it; optional softening not required.'),
('SCAN-01','uk-naturalness-1.2 physical line827',[414],'Повтор назад.','preserve_for_function','Spatial direction is material: Osya persists north instead of turning back after slipping crate. Retain.'),
]
for id,ori,ps,obs,dec,why in preserved: issue(id,ori,ps,obs,dec,why)

# Review interpretations must be bounded even when offered as praise, not edits.
for id,origins,ps,obs,why in [
('REVIEW-C01','Flash final chronology|Flash turn002 chronology|Pro final chronology',[3,784,890,1190,1246,1439],'Неточні дні/дев’ять діб/четвер–понеділок.','Current timeline is FridayD0 to nextSaturdayD8: nine calendar dates, about eight elapsed days. CH13 is Monday, CH14Tuesday. Thu→Mon79h50 belongs to old reserve; Fri→Mon72h is final metadata horizon.'),
('REVIEW-C02','Flash turn002/003 and final budget interpretation',[1447,1457,1462,1513],'Муніципальна/класова формула ліміту нібито встановлена.','Municipal ownership and class formula are not stated. Broad risk matches, uncertainty only close, other variables unknown. External provenance is not moral value or proven mechanism.'),
('REVIEW-C03','Flash turn002/003 age language',[598,637,1212],'Ося названий підлітком.','Working implementation is autonomous adult courier; exact age/family unknown. Reader impression cannot rewrite status into dependent minor.'),
('REVIEW-C04','Flash final/turn002 comfort interpretation|Pro turn002 capitulation',[919,962,966,987],'День без жодних людських контактів/тотальна капітуляція.','Service recommendations ease actual work and rest; ordinary exchanges remain. Dal declines optional personal contact himself. Capitulation is interpretation, not a rights transfer.'),
('REVIEW-C05','Pro turn001/003 and final old profession interpretation',[224,245,800,808],'L1+B нібито колишня службова операція Даля.','Book2 community operation follows closure of professional rights; no job restoration. Selected rolling historical branches are not a single foretold lifelong script.'),
('REVIEW-C06','Pro turn002/003 positive calendar-control interpretation',[723,725,734,735],'Знайомого нібито запрограмували зустріти Осю.','Two voluntary windows, own errand and option not to come; known scheduling assistance does not establish hired actor or total control.'),
('REVIEW-C07','Terra/Flash/Pro general whole-volume praise',[204,1236,1370],'Заяви про бездоганну причинність не підтверджують відсутність помилок.','Actual reread identified local broken syntax, chronology and missing request. Praise remains reader evidence, never substitutes verification.'),
('REVIEW-C08','Flash preliminary unresolved questions|Pro preliminary unresolved questions',[345,797,1030,1122],'Проміжні питання про професію, Ренату, Тихона, прихисток і смерть на схилі.','Questions record developing reader expectations. Later reading/series carry answers some; no duty to stage danger, biography, cameo or final world explanation. Lost work slot is real, basic rights retained.')]:
    issue(id,origins,ps,obs,'review_interpretation_bounded',why,category='review_validation')

# Exact scalar metadata changes; no plan is silently promoted to an observed event.
def meta(ch,sc,field,after,direction,ps,depends=()):
    s=next(s for c in states['chapters'] if c['chapter']==ch for s in c['observed']['scenes'] if s['id']==sc)
    id=f'B03-M{len(metas)+1:03d}'
    metas.append(dict(id=id,chapter=ch,scene_id=sc,field=field,before=s[field],after=after,direction=direction,evidence=evidence(ps),dependencies=list(depends),source_state_sha256=h(RUN/'terra-full-v1/observed-state.json'),author_decision='pending',implementation_status='compatible_bulk_authorized_metadata_correction'))
    return id
def sid(ch,n=1): return f'B03-CH{ch:02d}-SC{n:02d}'
meta(1,sid(1,2),'events','Тарас передав Осине прохання за згодою; Даль дозволив передати контакт. Ося написав сам, Даль запропонував19:20, Ося підтвердив.','Keep agency of the actual time proposal, not Osya alone scheduling.',[102,103])
meta(11,sid(11,2),'events','Ося сам надіслав знайомому одне запитання про походження запропонованого часу. Вони пішли без відповіді.','Remove unshown separate Dal request; do not insert a new scene into prose just to preserve inherited metadata.',[691,694,703])
meta(11,sid(11,2),'resources','Одне добровільне повідомлення Оси; окремого зареєстрованого запиту Даля в цій сцені не показано.','Remove invented receipt.',[694,703])
meta(11,sid(11,2),'knowledge','Мовчання не доводить змови; відповідь знайомого ще невідома. Значення коду обговорено в межах попередньої сцени; нового запиту не зафіксовано.','No pending invented second response.',[684,685,701])
meta(12,sid(12),'resources','Повний календар не отримано; Ося зберігає обрізаний фрагмент і не пересилає його Далю. Даль зберіг адресу публічного архіву; його окреме збереження погоджених часових даних не показано.','Distinguish seeing from retaining copy.',[714,734,739])
meta(14,sid(14,2),'time_basis','Плановий D4 09:35–10:40; у прозі історичні уривки передують відкриттю поточної версії, точні години завершення не названі.','Remove unobserved before11 claim.',[820])
meta(15,sid(15),'time_basis','Плановий D4 11:00–12:00; у прозі Ося пішов перед відкриттям поточної версії, точна година не названа. Допомогу Тарасові о17:00 погоджено явно.','Plan clock not prose observation.',[820,840])
meta(15,sid(15),'events','Даль без Оси прочитав дозволену поточну гілку делегування з умовами й альтернативою; не розширював обсяг поза погодженим горизонтом, закрив файл і погодив допомогу Тарасові о17:00.','He does open current material; do not say no new pages at all.',[823,826,839,840])
meta(15,sid(15),'knowledge','Даль і присутній Лоц обговорюють поточну гілку; Ося її не бачить. Відомі умови втоми й альтернативи, не точний завтрашній розклад.','Only Dal is false if excluding present Lotz.',[827,828,832])
meta(16,sid(16),'time_basis','Плановий D4 17:00–18:00; обіцяна на17:00 допомога відбулася, фактичну хвилину початку не названо. Завтрашня можливість написати після16:00 названа прямо.','Separate fulfilled appointment from observed clock.',[846,868])
meta(17,sid(17),'time_basis','Плановий D5 07:00–08:30; сьома й строк07:00–22:00 названі прямо. Прихід до роботи на погоджену09:00 показаний без точної хвилини.','Do not claim explicitly before09.',[890,896,905])
meta(18,sid(18),'time_basis','Плановий D5 09:00–12:15; робота погоджена раніше на09:00, фактичний старт без годинника. Завершення до полудня названо прямо.','No false literal start clock.',[909,922])
meta(18,sid(18,2),'time_basis','Плановий D5 12:30–14:30; обід і відпочинок після завершення роботи до полудня. Точний початок і межа полудня для обіду не названі.','Do not turn plan into explicit after-noon proof.',[922,926,929])
meta(20,sid(20),'resources','Строковий мандат завершено; власні нотатки збережено. Базовий ручний режим лишився; home/mic були OFF увесь день, не вмикалися й не потребували відновлення.','No temporary home/mic activation implied by restored.',[998,999])
meta(21,sid(21),'knowledge','Підтверджені ранні варіанти й виконане підвищення видимості дворів. У виданому журналі немає точних реплік/чоловіка з термосом; це не доводить їх відсутності в усіх чужих закритих даних.','Clarify documentary absence versus global ignorance.',[1016,1019,1030])
meta(22,sid(22),'knowledge','Даль бачить лише добровільно показаний рядок і вузьку технічну оцінку невизначеності обраного напрямку. Її джерело — показане поле, не слабкий зв’язок. Невидимість не встановлена.','After ROOT-05 prose restoration, replace overcompressed inference.',[1091,1141],next(i for i in issues if i['id']=='ROOT-05')['patch_ids'])
meta(23,sid(23),'knowledge','Раніше показане поле повідомило нижчу впевненість через обмежені/несвіжі входи; огляд додає конкретний стан дороги. Повільне завантаження карти саме не вимірює невизначеності Predictariat і не дає невидимості.','Keep evidence sources separate.',[1137,1141],next(i for i in issues if i['id']=='ROOT-05')['patch_ids'])
meta(25,sid(25),'events','Ося сам відмовився від подальшої поїздки цього вечора без обіцянки суботнього рейсу; погодив зустріч завтра16:00. Даль пішов і зареєстрував ранковий власний перегляд.','Not a promise to decide by morning or proof he slept.',[1215,1217,1227,1238])
meta(29,sid(29),'time_basis','Плановий D8 08:00–09:45; початок рейсу погоджено раніше на08:00; фактична хвилина старту й завершення відрізка не названа.','Planned start not explicit scene clock.',[1339])
dep=next(i for i in issues if i['id']=='ROOT-12')['patch_ids']
meta(29,sid(29,2),'time_basis','Плановий D8 10:00–10:30; вони домовилися порівняти витяги о15:00, приймальня підтвердила їхню доступність для цього часу; опівденний візит до Тараса погоджено окремо.','After native correction only. Not a Lotz15appointment.',[1368,1370,1371],dep)
meta(29,sid(29,2),'events','Ося дозволив вузьке порівняння метаданих; обидва суб’єкти подали обмежені запити й отримали реєстрацію та підтвердження доступності витягів до15:00. Даль погодився видалити тимчасову копію; Ося поїхав далі сам.','Must be proved by new Terra prose before marking observed.',[1369,1370,1373],dep)
meta(29,sid(29,2),'resources','Нові дозволені метадані для порівняння, окрема реєстрація власних запитів та підтверджена доступність до15:00; приватний зміст і майбутні гілки виключено. Раніше надані уривки підлягають видаленню після завершення.','Replace fictional booked audit with actual requested limited extracts.',[1369,1370],dep)

registry=read(ROOT/'kontakt/books/book-03/audit/issues.json')
u03=next(x for x in registry['items'] if x['id']=='KONTAKT-B03-20260923-U03')
metas.append(dict(id=f'B03-M{len(metas)+1:03d}',chapter=4,scene_id=sid(4),target_file='kontakt/books/book-03/audit/issues.json',target_id=u03['id'],field='resolution_status',before=u03['resolution_status'],after='resolved',direction='Coordinator only: record limited documentary working resolution, not canonical approval or total model explanation. Add resolution_scope: Book3CH02 reply plusCH04 unused candidate records andCH05 limited interpretation establish multi-candidate reserve planning; no proof of private foreknowledge/staged revolt. Preserve former entry status in history and attach new exact final-source evidence. B03-U03 private inputs and B03-U01 budget formula remain unresolved.',evidence=evidence([245,251,260,265,267,328,330]),dependencies=[],author_decision='pending',implementation_status='compatible_bulk_authorized_working_registry_update'))

# Make metadata findings explicit in ledger without fake votes.
for m in metas:
    row=issue('META-'+m['id'][5:],'Astra state/prose reconciliation',[int(e['paragraph'][1:]) for e in m['evidence']],m['direction'],'metadata_correction',m['after'],'minor',category='metadata')
    row['metadata_ids']=[m['id']];m['issue_ids']=[row['id']]

for n,(ps,guard) in enumerate([
([245,265,328],'U03 new documentary candidate explanation only; retain unknown private inputs and noL2 authorization.'),
([382,419,512,565,566],'Container receiving window and borrowed cart17deadline are separate; preserve observed10:25/17:30.'),
([305,365,423,431,500],'Older errors stay errors after updates; rare branch does not prove calibration failure; control predates exposure.'),
([800,808,809],'Suspension18:01 then voluntary closure; rolling historic horizons, not lifelong exact forecast.'),
([881,894,896,922,966,998,999],'Ballast software, new15hourrecommendation session, home/micOFF throughout, manual sends/payments, real benefit and ordinary human contact.'),
([1030,1031,1050,1061],'Existing yard and bounded ranking evidence, no universal proof of nonintervention or hired actors.'),
([1122,1134,1157,1208],'No onward freight ticket or ride; no forced rescue/night outside; ordinary return bus.'),
([1246,1249,1261,1278,1284,1289,1445],'Friday08version before09exposure afterThursdayrequest; remainder stays unread through metadata.'),
([1317,1329,1349,1373],'Osya autonomously chooses/executes imperfect courier work, no apprenticeship, permanent job or Dal guardianship.'),
([40,1377,1381,1382,1408],'Plane suspected crack becomes found crack; preserve humor and material repair.'),
([1439,1447,1451,1457,1474,1484,1513],'SameFriday08versions and72hwindow/units/type; broad risk and close not identical uncertainty, known action differences, remaining confounders, limit≠spend, external lineage≠formula.'),
([1516,1522,1535,1538,1540],'Limited copies revoked/deleted, narrow permitted anonymous evidence retained; separatequerypending, conditionalpaidwork, breadchoice, R3only.')],1):
    checks.append(dict(id=f'B03-V{n:03d}',status='verified_on_input_preserve_and_recheck_final',direction=guard,evidence=evidence(ps),author_decision='pending'))

write('issue-ledger.json',dict(schema_version='book03-source-bound-reconciliation-1',status='final',source=rel(SRC),source_sha256=SHA,independence='Nonblind Astra reconciliation and full reread; not a fourth independent locked diagnosis',author_decision_policy='All pending; compatible implementation selected under existing author bulk instruction; preserve/no-change dispositions are editorial judgments, not author rejection.',issues=issues))
write('PATCH-PLAN.json',dict(schema_version='book03-native-terra-final-plan-1',status='final',source=rel(SRC),source_sha256=SHA,scope='All32/41; native Terra writes exact after text in a new version, never mutates source',patches=patches,metadata_updates=metas,no_change_verification_items=checks,global_guards=['Do not insert false reviewer explanations, human traitor, municipal/class budget cause, mind reading, total rights ban, emergency key or future Book4 formula.','No expansion by quota, no wholesale removal of dry humor/negation; no prose outside listed patch contexts absent source-grounded incompatibility.','After application refresh affected states/quotes/hashes and all assembly/anchors; metadata resolution must use actual final prose, not this plan as proof.','Freeze old reports, original source, structure and rough; all author_decision values remain pending.']))

chapter_notes=[
'Дощ, булочки й рубанок дають справжню дружню зустріч до окремого прохання; час19:20 локально уточнюється.',
'Проміжна відповідь ще не доказ причини; суботня видача одержана на сторінці. Збережено старий номер.',
'Осина робота/мова й обмежений дозвіл прожиті; обрив предиката й надмірне знання рядка виправляються.',
'Нові альтернативні резерви руйнують єдиний сценарій, не доводять повне незнання приватних даних.',
'Лоц має чергу, папір і конкретні перевірки; старі версії, горизонти й строки журналів розділені.',
'Монета спричиняє реальну зайву дорогу й втрату заробітку; промах не підмінено висновком про калібрування.',
'Колега відмовляється бути дослідом; рама, ліфт і ремонт міняють маршрут без інсценованої людини.',
'Півгодинне запізнення оплачено роботою з лавами, не лише провиною; фінальний підпис працює.',
'Власна компетентність кур’єра показана руками; старе місце втрачено, новий рейс лише пробний.',
'Змішані бажання й межа приватного контакту названі Осею; рання гордість самовивозом готує пізній удар.',
'Даль помиляється зі скасованим рядком і виправляється; добровільна відповідь ще невідома. Metadata вигадала другий запит.',
'Знайомий має власну справу й право образитися, календар обрізаний; допомога з оголошенням утримує живий двір.',
'Лоц має частково переконливі дані й невдалі випадки; запит Даля змінює ставки, не універсальна лекція.',
'Короткість не прибирає добровільного відкриття, тілесної реакції й окремого запрошення Оси до історії.',
'276слів достатньо для окремого удару поточної гілки; вихід і рукавичка не дозволяють сцені стати самим резюме.',
'Даль реально несе полиці, але просить понад домовлене; відмова Тараса веде до нового boundedзапиту Баласту.',
'Дозвіл короткий, перша користь прожита дорогою; не треба роздувати технічний контракт.',
'Дві сцени: реальна помилка цінника/оплата та справжній відпочинок, не штучна пастка.',
'Дві ненадіслані чернетки показують втрату необов’язкової близькості; побутові контакти прямо залишені.',
'Користь не спростована; добровільне непродовження повертає ціну очікування відповіді, expiryвидиме.',
'Документальний удар перевірено звичайним двором; люди не оголошені акторами, сором має адресата.',
'Ненадіслана відмова лишає вибір живим; треба повернути джерело uncertainty і часову опору жарту.',
'Дорога оглянута до незворотного кроку; слабкий зв’язок не доказ властивостей прогнозу. Вантажівкою не їдуть.',
'Даль визнає власну нечисту позицію, не дає лікувальної промови; місце на лаві важливіше готового висновку.',
'Пауза належить Осі, ніч позаPOV; календарна обмовка й нечутна усмішка потребують локального виправлення.',
'Сильний парадокс спирається на попередню версію, але narrator knowledge слід звузити до видимого inputlist.',
'Відмова прожита без катарсису й перевірки нового рейтингу; квитанції минулого збережені.',
'Осині умови й власне підтвердження роблять вибір конкретним; уточнити тільки обсяг повернення тари.',
'Доставка недосконала й виконана, Даль лишає маршрут; треба подія замовлення витягів перед фіналом.',
'Дружба виплачена ручкою й водою до нового гачка; попередня підозра тріщини правильно збережена.',
'Ліміт справді різний, але причина невідома; зіставлення обмежене, майбутній зміст не відкритий.',
'Доведено lineage, не формулу; відкликання кінцеве й вузьке. Звичайна купівля хліба завершуєR3безмагії.'
]
coverage=[]
for c in states['chapters']:
    ch=c['chapter']; bb=[b for b in blocks if b['chapter']==ch]
    coverage.append(dict(chapter=ch,chapter_sha256=c['sha256'],first=bb[0]['id'],last=bb[-1]['id'],blocks=len(bb),words=c['words'],status='actual_complete_untruncated_prose_read',assessment=chapter_notes[ch-1],scenes=[s['id'] for s in c['observed']['scenes']]))
write('full-reading-coverage.json',dict(status='complete',source_sha256=SHA,reader='Assigned Astra agent; actual nonblind literary/architectural reading, not tool scan',chapters=coverage,total_blocks=1540,total_chapters=32,total_scenes=41,unread=[],method='Displayed entire actual source in chapter ranges1–4,5–6,7–8,9–12,13–16,17–20,21–24,25–28,29–32. Truncated first5–6 call repeated; no credit for truncated output. Maps read via complete source cards and exact derivative equivalence plus separate nonduplicate fields. Prior rough is comparison, not substitute.',limitations='No fresh independent diagnosis claimed; report context limits recorded separately. All final changed prose still requires nativeTerra authorship and full final reread.'))

report_validation=[]
for role in ['terra','gemini_flash','gemini_pro','opus']:
    d=RUN/'literary-v1/results'/role; inv=read(d/'invocation.json'); log=d/('stdout.jsonl' if role=='terra' else 'stdout.ndjson')
    rows=[json.loads(l) for l in log.read_text(encoding='utf-8').splitlines() if l.strip()]
    steps=[x['step_update'] for x in rows if 'step_update' in x]; types=sorted(set(s['step_type'] for s in steps))
    errors=sorted(set(s['step_index'] for s in steps if s['step_type']=='error_message')); checkpoints=sorted(set(s['step_index'] for s in steps if s['step_type']=='checkpoint'))
    files=[dict(path=rel(f),sha256=h(f)) for f in sorted(d.glob('*.md')) if f.name=='REPORT.md' or f.name.startswith('turn-')]
    r=dict(role=role,requested_model=inv.get('requested_model',inv.get('model_requested')),actual_backend='not independently attested',invocation_sha256=h(d/'invocation.json'),trace_sha256=h(log),reports=files,result_events=sum(x.get('event')=='result' for x in rows),step_types=types,error_step_indices=errors,checkpoint_step_indices=checkpoints,report_texts_read='REPORT and all turn001–003 read; turn004 hash-identical to REPORT' if role.startswith('gemini') else ('full REPORT read' if role=='terra' else 'no report'))
    if role=='terra': r.update(item_types=[x.get('item',{}).get('type') for x in rows if x.get('type')=='item.completed'],coverage_limit='Full1540 supplied; no observed tools/compaction; claimed reading not independently proven. Group ranges approximate; finding2 cited416 actually417.')
    elif role=='gemini_pro': r.update(coverage_limit='Three source parts supplied, four reports returned. Checkpointstep3 after first completed result; final fails to disclose adequately. NOT an uncompacted full-context review. Claims verified individually against full source.')
    elif role=='gemini_flash': r.update(coverage_limit='Three source parts supplied, four reports, no checkpoint observed. Ranges approximate, chronology and travel/budget interpretations false; praise not proof. Ballast provisional human inference superseded.')
    else:r.update(coverage_limit='No reading established; author explicitly permits unavailableOpus skip. Four errors noted at stop-decision snapshot, seven in final preservedstream;0reports. Exact backend reason unknown; no inherited quota/invalid-model explanation.')
    if role.startswith('gemini'): assert h(d/'REPORT.md')==h(d/'turn-004.md')
    report_validation.append(r)
write('report-validation.json',dict(status='final',source_sha256=SHA,successful_locked_diagnoses=3,independent_opus_success=False,reports=report_validation,legacy_verify=dict(command='python -X utf8 tools/editorial_ensemble.py verify --run '+rel(RUN/'literary-v1'),exit_code=1,error="invalid run identity; required diagnosis report is missing; 'reader'",disposition='Legacy schema mismatch already disclosed by locked run; author whole-book workflow and unavailableOpus exception govern. No retrofit/no invented fourth report.'),quote_scope='Exact manuscript evidence for every ledger item and patch mechanically checked. Prose reports contain approximate ranges/ellipsis; not claiming every decorative quotation was exact. All actionable claims independently adjudicated, including superseded intermediate findings.'))

# Verify carry proofs against unchanged actual sources; preserve bounded previous reading scope.
carry=read(RUN/'structure-v1/carry-in-source-lock.json'); carrychecks=[]
for path,sha,proofs in [(carry['source'],carry['source_sha256'],carry['proofs']),(carry['book1_inherited']['source'],carry['book1_inherited']['source_sha256'],carry['book1_inherited']['proofs'])]:
    p=ROOT/path; assert h(p)==sha
    raw=p.read_text(encoding='utf-8'); chunks=re.split(r'(?=^# Розділ \d+\s*$)',raw,flags=re.M)
    for proof in proofs:
        matching=[s for s in chunks if re.match(r'# Розділ '+str(proof['chapter'])+r'\s*\n',s)]
        assert len(matching)==1 and proof['quote'] in matching[0],proof
        carrychecks.append(dict(source=path,source_sha256=sha,chapter=proof['chapter'],quote=proof['quote'],match='exact_in_correct_chapter'))
write('carry-proof-validation.json',dict(status='passed',proofs=carrychecks,reading_limit='Proofs and relevant carry read; this stage does not claim another full reread of Book1 or Book2. Earlier complete Book2finalCH1/29–36 carry reading preserved in source lock.'))

qv=[]
for i in issues:
    for e in i['evidence']:
        b=by[int(e['paragraph'][1:])];assert e['quote']==b['text'] and e['chapter']==b['chapter'];qv.append(dict(issue_id=i['id'],paragraph=e['paragraph'],chapter=e['chapter'],exact=True))
for p in patches: assert text.count(p['before'])==1
statequotes=[]
for c in states['chapters']:
    raw=(ROOT/c['path']).read_text(encoding='utf-8');assert h(ROOT/c['path'])==c['sha256']
    for s in c['observed']['scenes']:
        for q in s['quotes']:statequotes.append(dict(scene=s['id'],quote=q,exact_in_chapter=q in raw))
write('source-quote-validation.json',dict(status='passed' if all(x['exact_in_chapter'] for x in statequotes) else 'state_quote_mismatch',source_sha256=SHA,blocks=len(blocks),patches_unique=len(patches),ledger_evidence=qv,state_quotes=statequotes,anchors='P numbers are1-based double-newline nonempty source blocks including headings/titles. Mechanical language tool p uses physical lines including blanks; do not interchange.'))

# Preserve mechanical search output independently of literary reading.
scan=read(OUT/'naturalness-scan.json')
for x in scan['findings']: x.update(decision='retained_with_reason',reason='Spatial persistence on northern route; seeSCAN-01/P00414. No redundant-return blanket ban.')
scan['unresolved_signals']=0;scan['result']='all_signals_contextually_reviewed';write('naturalness-reviewed.json',scan)
qa=subprocess.run(['python','-X','utf8','tools/language_qa.py','--language','uk','--source',rel(SRC)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8');assert qa.returncode==0;write('language-qa.json',json.loads(qa.stdout))

print(json.dumps(dict(issues=len(issues),patches=len(patches),metadata=len(metas),checks=len(checks),state_quotes=len(statequotes),bad_state_quotes=[x for x in statequotes if not x['exact_in_chapter']],root=str(ROOT)),ensure_ascii=False))
