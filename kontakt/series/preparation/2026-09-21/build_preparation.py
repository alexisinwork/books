"""Build a scoped, source-backed preparation package without drafting prose."""
from pathlib import Path
import json,hashlib,shutil,difflib,subprocess,sys
R=Path(__file__).resolve().parents[4]; P=R/'kontakt'; O=Path(__file__).resolve().parent
if (O/'verification.json').exists():
    raise SystemExit('This run is finalized. Use a new run directory; do not overwrite historical snapshots.')
RUN='kontakt-preparation-20260921'
changed=[]; before={}
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rd(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def rel(p): return p.relative_to(R).as_posix()
def save(p,text):
    if p.exists() and rel(p) not in before:
        q=O/'before'/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
        before[rel(p)]={'path':rel(q),'sha256':h(q)}
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
    if p not in changed: changed.append(p)
def js(p,x): save(p,json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def b(n): return P/f'books/book-{n:02d}'
def ref(p): return {'path':rel(p),'sha256':h(p)}
base=[]
for n in range(1,9):
    bp=b(n); a=rd(bp/'architecture.json')
    base.append({'book_id':f'book-{n:02d}','macro':ref(bp/f'BOOK-{n:02d}-ARCHITECTURE-LOCK.md'),
                 'architecture':ref(bp/'architecture.json'),'resonance':a['resonance'],
                 'planned_sources':{k:ref(bp/f'{k}.planned.json') for k in ['characters','knowledge','promises','timeline','motifs','end-state']},
                 'chapter_plan':ref(bp/'KONTAKT_BOOK_04_CHAPTER_SKELETON_V1.md') if n==4 else None,
                 'downloads_status':'historical_candidates_not_wholesale_adopted',
                 'prose_status':'not_written'})
assert all(rd(b(n)/'book.json')['master'] is None for n in range(1,9))
js(O/'baseline.json',{'run_id':RUN,'status':'working_preparation_authorized','author_instruction_raw':'вщ фдд іеузі иуащку іщд.еуккф цкшештп  1 вкфае срфзеук',
 'keyboard_decoding':'do all steps before sol.terra writing 1 draft chapter',
 'latest_instruction':'стоп - перед єтим всем добавь такой же архитектруний план дял 4 - добавь все в репу и запуш - потом при поомщи всего что ті указал и файлов архзитекрути продолжай',
 'interpretation':'Prepare recommended working route; first add Book 4 and push; do not draft prose in this task.',
 'not_an_author_quote':'Detailed editorial implementation remains attributed to the assistant, not rewritten as author intent.',
 'source_priority':['current author instructions','series PRE-DRAFT LOCK','book macro lock and planned registers','explicit scoped execution cards','Downloads candidates as comparison only'],
 'books':base,'first_publication_commit':'15a3cf4'})
resolutions={
'01':'Use existing Nina history and Dal-authored safe-presence template. Separate factual memory from later emotional acknowledgment.',
'02':'Retain S04 R1 and Maya independent accommodation; opening adopts only compatible Chapters 1–2.',
'03':'Retain no-traitor macro; predictive evidence remains advance response-capacity.',
'04':'Retain Ira and independent Taras continuity work; Miron/restoration alternatives are not active.',
'05':'Ranking outage preserves emergency/identity infrastructure.',
'06':'Osya remains courier in all eight-book working references.',
'07':'Use macro timeline D0–D8 and local 72-hour forecast windows; alternative 60-hour deadline is not active.',
'08':'Author-requested Book 4 plan created, checked and pushed as 30 chapters.',
'09':'K-17 is a client; Lev is not silently substituted or adopted.',
'10':'Retain delayed split-relay complication, not hardware sacrifice.',
'11':'Retain helpful consenting relief session actually received by Dal.',
'12':'Restore chain K-17 → affect-service → child cohorts/Guidance → adult emergency framework.',
'13':'Retain Zhdan father and Marta system architect/bereaved mother of her historical son; no new maternity of Mila.',
'14':'Candidate offstage parental scene is not active; all future scenes require Dal access or permitted document.',
'15':'Retain independent five-year workshop decision over twelve days, no Mila/Osya hostage clock.',
'16':'Retain Varan family/Eva, month nine and six-week story, detention-return tracing.',
'17':'M-17 transport plot excluded from active edition; no unresolved location dependency carried into this route.',
'18':'Progressive sequence work; selected scoped scene cards govern opening; global macro review does not equal all chapters draft-ready.'}
js(O/'resolutions.json',{'run_id':RUN,'status':'source_routing_applied','not_a_vote':True,
 'items':[{'issue_id':f'KONTAKT-REV-20260921-{k}','resolution':v,'scope':'active working route; alternatives preserved','decision':'applied','resolution_status':'resolved'} for k,v in resolutions.items()]})
handoff_notes=[
('R1','Maya independent; Dal deserter; Ballast assigned; no full grief healing.','Grey-zone life brings Taras/Ira/One-dayers.'),
('R2','Taras independent living connection; no traitor; advance capacity timestamp unexplained.','Taras network brings courier Osya; timestamps lead to Predictariat.'),
('R3','Osya chooses courier work; Dal stops reading; differing intervention budgets.','Edith appeal leads to Compatibility allocation.'),
('R4','Edith autonomous; Dal sponsor revoked; K-17 living client in Quiet contour.','Affect-service metadata traced client-side.'),
('R5','Taras irreversibly dead; Asta carrier; Dal accepts support without offload.','Child-cohort upstream prevention clue leads to Guidance/Mila.'),
('R6','Mila limited age autonomy/backstop; Zhdan father; Marta remains architect; grief continues.','Adult emergency framework ancestry leads to Tikhon/Overload.'),
('R7','Five-year workshop under real name; fixed address; Tikhon chooses comfort; Ballast on-request.','Month-nine wartime civilian repair hub; Varan family; integration without new rank.')]
js(O/'handoffs.json',{'run_id':RUN,'status':'reviewed_planned','items':[{'from':f'book-{i:02d}','to':f'book-{i+1:02d}','rank':x[0],'outgoing':x[1],'incoming':x[2],'result':'compatible','sources':[ref(b(i)/'end-state.planned.json'),ref(b(i+1)/f'BOOK-{i+1:02d}-ARCHITECTURE-LOCK.md')]} for i,x in enumerate(handoff_notes,1)]})
# Standard registers become clearly identified projections, not observed manuscript facts.
for n,entry in enumerate(base,1):
    bp=b(n); bid=f'book-{n:02d}'
    for k in ['characters','knowledge','promises','timeline','motifs','end-state']:
        src=bp/f'{k}.planned.json';data=rd(src)
        projection={'schema_version':1,'project_id':'kontakt-razlad','book_id':bid,'record_type':k,
          'status':'planned_projection','source_of_truth':src.name,'source_sha256':h(src),
          'update_rule':'Edit selected planned source, then regenerate projection; these are not observed prose facts.',
          'items':data.get('items',[]),'source_metadata':{key:val for key,val in data.items() if key not in ['items','book_id','project_id','schema_version']}}
        js(bp/f'{k}.json',projection)
    a=rd(bp/'architecture.json')
    js(bp/'scenes.json',{'schema_version':1,'project_id':'kontakt-razlad','book_id':bid,'status':'planned_macro_only',
       'source':entry['architecture'],'items':[{'id':f'{bid}-{s["id"]}','sequence_id':s['id'],'unit_type':'macro_sequence',
       'status':'planned_not_scene_ready','summary':s['title'],'decision':s.get('decision'),'cost':s.get('cost'),
       'next_cause':s.get('next_cause'),'detail_required_before_prose':True} for s in a['sequences']],
       'coverage':'12 macro sequences; local scene access/timing still required before writing later chapters'})
    resources=rd(bp/'resources.json');resources['status']='planned';resources['active_resonance']=a['resonance']
    resources['source']=entry['architecture'];resources['observation_status']='no_manuscript'
    js(bp/'resources.json',resources)
    book=rd(bp/'book.json'); book.update({'stage':'macro_reconciled','audit_status':'macro_reviewed_scene_gates_pending',
      'original_language':'uk','language':'uk','planning_baseline':'../../series/preparation/2026-09-21/baseline.json',
      'active_outline':{'path':f'BOOK-{n:02d}-ARCHITECTURE-LOCK.md','sha256':entry['macro']['sha256']},
      'planning_state':'planned_not_observed','execution_entry':'execution/HANDOFF-CH01.md' if n==1 else 'plan.md'})
    js(bp/'book.json',book)
    save(bp/'plan.md',f'# Рабочий план — {book["title"]}\n\nОснова: [макрокаркас](BOOK-{n:02d}-ARCHITECTURE-LOCK.md), SHA-256 {entry["macro"]["sha256"]}.\n\nСверка источников: [preparation](../../series/preparation/2026-09-21/README.md). Все события planned. Стандартные реестры — производные planned-файлов, не факты прозы. Старые 34 summaries архивированы.\n\n'+
      ('S01: две главы, шесть сцен в scenes.json. Для главы 1 читать [задание](execution/HANDOFF-CH01.md). Остальные последовательности требуют собственного gate.\n' if n==1 else
       ('Поглавная карта: [30 глав](KONTAKT_BOOK_04_CHAPTER_SKELETON_V1.md). Подробные карточки создавать по одной SXX.\n' if n==4 else 'Downloads chapterization сохранена в историческом пакете, не принята целиком. При детализации следовать выбранной macro sequence, не возвращать исключённые варианты.\n'))+
      '\nПорядок: карточки текущей главы → проверка причинности/знания/доступа → одна украинская глава → проверка и обновление фактических состояний → следующая глава.\n')
    save(bp/'brief.md',f'# {book["title"]}\n\nСтадия: согласованный рабочий макроплан; master отсутствует.\n\nАвторитетная постановка конфликта, цели, цены и финала: [BOOK-{n:02d}-ARCHITECTURE-LOCK.md](BOOK-{n:02d}-ARCHITECTURE-LOCK.md).\nРезонанс: {a["resonance"]["opening"]} → {a["resonance"]["closing"]}.\n\n[Входы и выходы](../../series/preparation/2026-09-21/handoffs.json) проверены по planned-источникам. Финал не является состоянием перед ранней сценой.\nПроза: украинский оригинал, первое лицо Даля, прошедшее время.\n')
    save(bp/'session.md',f'# Сессия подготовки 21.09.2026 — {bid}\n\nПрочитаны выбранный макрокаркас и относящиеся planned-реестры; источники зафиксированы в [baseline](../../series/preparation/2026-09-21/baseline.json).\nПроза не написана. Observed states отсутствуют.\n\nСледующий вход: '+('[HANDOFF-CH01](execution/HANDOFF-CH01.md); scope только глава 1.\n' if n==1 else '[plan.md](plan.md); детализировать только нужную последовательность перед её прозой.\n')+
      '\nСтарые AI-RUNBOOK/CONTEXT-CAPSULE/pass01-manifest сохранены как пакет происхождения. Актуальный scope и маршрутизация здесь и в book.json.\nОставшиеся вопросы дальних сцен не объявляются закрытыми литературным аудитом. Проверки: preparation/verification.json.\n')
    aud=rd(bp/'audit/issues.json')
    for issue in aud['items']:
        if issue['id'].startswith('KONTAKT-REV-20260921-'):
            key=issue['id'].rsplit('-',1)[1]
            issue['resolution_status']='resolved'
            issue['resolution']={'run_id':RUN,'basis':'Existing source priority and author-authorized preparation; incompatible candidates not active.',
                 'text':resolutions[key],'record':'../../series/preparation/2026-09-21/resolutions.json'}
            issue['implementation_status']='source_routing_applied'
            # Preserve original editorial proposal/decision; do not invent individual author votes.
    js(bp/'audit/issues.json',aud)
# Opening concrete cards: reversible details attributed to preparation, not author quotes.
cards=[]
def card(id,ch,time,place,people,entry,goal,obstacle,decision,result,cost,next,known,reveal,motifs):
    return {'id':id,'sequence_id':'S01','chapter':ch,'unit_type':'scene','status':'planned_execution',
      'pov':'Марк Даль','person':1,'tense':'past','language':'uk','time':time,'place':place,'characters_present':people,
      'entry':entry,'goal':goal,'obstacle':obstacle,'decision':decision,'result':result,'cost':cost,'next_cause':next,
      'knowledge_before':known,'knowledge_after':known+reveal,'reader_receives':reveal,'motifs':motifs,
      'resonance_before':'R0','resonance_after':'R0',
      'must_not_reveal':['full Nina backstory','Gor control/proxy history','Overload origin','later books'],
      'implementation_basis':'Compatible S01 macro and Downloads opening; local staging choices are planned by assistant under preparation authorization.'}
cards.append(card('B01-S01-C01-S01',1,'D0 morning; ordinary appointment','calibration room; one city, no named address',['Марк Даль','unnamed adult client','client companion via device'],
 'Dal still serves Lad; client arrives by appointment. Ballast not assigned.',
 'Налаштувати компаньйона, який заважає клієнтові завершити звичайну складну розмову.',
 'Заспокійлива відповідь знімає напруження, але не відповідає на конкретну претензію живого співрозмовника.',
 'Даль просить дозвіл на обмежену діагностику; змінює темп і момент підказки, не читаючи всю приватну переписку.',
 'Клієнт перевіряє налаштування на власному пристрої і каже, що тепер може відповісти. Полегшення справжнє.',
 'Даль задоволений працездатністю; ще не питає, якої розмови людина уникає.',
 'Клієнт дякує йому особисто, без технічного запиту.',
 ['Dal knows calibration craft','client controls permission','companion is software'],
 ['Lad helps with a real difficulty','Dal treats discomfort as an adjustable condition'],
 ['руки','затримка відповіді','занадто доречне тепло']))
cards.append(card('B01-S01-C01-S02',1,'D0 immediately after appointment','same calibration room',['Марк Даль','unnamed adult client'],
 'The practical problem eased; permission still does not grant further personal access.',
 'Закінчити зустріч і повернутися до робочого порядку.',
 'Особиста подяка вимагає відповіді від нього, а не від послуги.',
 'Він переводить розмову в рекомендацію і дивиться на екран раніше, ніж витримає паузу.',
 'Зустріч ввічливо закінчується; можливість прямого контакту не використана.',
 'Ремесло виявляється його захистом; без катарсису або нового рангу.',
 'Після роботи Даль повертається в контрольований домашній простір.',
 ['calibration completed','client gratitude is personally directed'],
 ['Dal evades gratitude with professional competence'],['погляд','незаповнена пауза']))
cards.append(card('B01-S01-C01-S03',1,'D0 evening; travel elided after clear time transition','Dal apartment',['Марк Даль','Gor message on professional private inbox'],
 'Dal at home after work; no Maya case accepted; no Ballast.',
 'Провести передбачуваний вечір без чужих вимог.',
 'Приходить запит Гора на розмову поза звичайним сервісним маршрутом.',
 'Даль читає повідомлення і погоджується лише вислухати запит; він ще не погоджується втручатися.',
 'Вечір має незаплановане продовження — зустріч із Гором.',
 'Його контрольований розклад уперше поступається справі без оформленої задачі.',
 'Глава 2 починається розмовою з Гором того ж вечора.',
 ['Dal still employed','no case accepted'],['Gor wants an unofficial consultation'],
 ['налаштоване тепло','тиша','повідомлення']))
cards.append(card('B01-S01-C02-S01',2,'D0 later evening; brief interval after message','private consultation room; same city',['Марк Даль','Гор'],
 'Dal agreed to hear the request only.',
 'Зрозуміти запит і відмовити, якщо він вимагає дії за Майю.',
 'Гор просить повернути її з глибокого супроводу і говорить так, ніби знає бажаний результат.',
 'Даль відмовляється від замовлення на зміну її стану без її дозволу.',
 'Контракт не прийнятий; Гор залишає лише технічний матеріал у межах окремого дозволу Майї.',
 'Даль втрачає просту оплачувану задачу; його рамка поки професійна, не зрілий моральний висновок.',
 'Він перевіряє межі дозволу перед переглядом матеріалу.',
 ['Gor claims partner needs help','Maya has not consented to intervention'],
 ['Gor requests an outcome; Maya permission to alter settings absent'],
 ['двері','межа доступу']))
cards.append(card('B01-S01-C02-S02',2,'D0 same consultation aftermath','Dal workstation',['Марк Даль','Gor-provided technical excerpt'],
 'No settings changed; a signed metadata-only diagnostic permission is presented.',
 'Перевірити, чи взагалі є допустима технічна задача.',
 'Матеріал обмежений; особистих розмов і доступу до керування немає.',
 'Даль перевіряє чинність і межі дозволу, читає лише структуру шаблону; впізнає власний старий safe-presence патерн.',
 'Знайомий шаблон пов’язує справу з його минулою роботою. Це його кодова структура, не голос або свідомість Ніни.',
 'Технічна відстороненість більше не переконлива для читача.',
 'Даль повертається до рішення після ночі, не запускаючи прихованих змін.',
 ['Dal knows his own older design','Nina facts are remembered, emotional responsibility defended'],
 ['profile uses derivative of Dal template','the recognition matters personally, why remains incomplete'],
 ['руки завмерли','збій звичного темпу']))
cards.append(card('B01-S01-C02-S03',2,'D1 morning','Dal workstation / authenticated request channel',['Марк Даль','Гор via reply','Майя via limited appointment consent'],
 'Dal has recognized template; Maya settings unchanged.',
 'Взятися за перевірку і назвати собі професійну причину.',
 'Замовлення Гора вимагає результату, на який Майя не погоджувалась.',
 'Даль погоджується лише на розмову й діагностику в погоджених межах; просить передати Майї запит на зустріч.',
 'Майя сама дозволяє одну зустріч: говорити й спостерігати, не міняти profile. Даль має початковий канал, не право рятувати.',
 'Він бере особисто важливу справу, приховуючи від себе мотив технічним інтересом.',
 'S02: Даль приходить до Майї в межах її дозволу; її власне пояснення ще попереду.',
 ['template connection','no intervention consent'],
 ['Maya grants one bounded meeting','Dal accepts a limited inquiry'],['власне повідомлення','умова']))
scene=rd(b(1)/'scenes.json');scene['status']='S01_scene_ready_remaining_macro';scene['items']=cards+[x for x in scene['items'] if x['sequence_id']!='S01'];scene['coverage']='6 scene cards, chapters 1–2; remaining 11 units are macro planning, not ready prose';js(b(1)/'scenes.json',scene)
js(b(1)/'execution/current-state.json',{'book_id':'book-01','status':'planned_before_first_scene','at':'B01-S01-C01-S01','observed_manuscript':None,
 'dal':{'resonance':'R0','job':'serves Lad as expert calibrator','visibility':'ordinary professional visibility; no episode-triggered escalation yet','Maya_case':'not_received','Ballast':'not_assigned'},
 'knowledge':{'Dal':['craft','Lad current interfaces','Nina death and own past actions as factual memory; emotional accountability defended'],
 'reader':[],'not_known_as_fact':['Gor control history','Maya own preference before meeting','Overload genesis','future ranks/outcomes']},
 'resources':{'client_data':'none until scoped permission','settings_write':'client permission only','Gor_proxy':'none at chapter opening','money':'ordinary job; no invented amount','travel':'local city'},
 'promises_open':[],'scene_source':ref(b(1)/'scenes.json')})
js(b(1)/'execution/local-decisions.json',{'status':'planned_local_realization_not_new_global_canon','author_samples':'awaiting_author_samples',
 'items':[{'id':'LD01','decision':'Unnamed adult client, no fixed biography; mundane relational friction, no acute medical crisis.'},
 {'id':'LD02','decision':'Functional calibration room and apartment; no new named city/institution.'},
 {'id':'LD03','decision':'Gor uses private professional inbox; confidentiality is ordinary channel scope, not invisibility from Lad.'},
 {'id':'LD04','decision':'Metadata-only Maya permission in Chapter 2; checked before viewing; no personal conversation export and no write permission.'},
 {'id':'LD05','decision':'Do not choose or imply a specific Nina keepsake in Chapter 1; use existing temperature/pause motifs. Exact M05 object remains a later local choice.'},
 {'id':'LD06','decision':'S01 spans D0–D1. Chapter 1 ends before Gor consultation; Chapter 2 ends after Maya appointment permission.'}]})
# Add stage-specific knowledge records without changing immutable macro source.
k=rd(b(1)/'knowledge.json');k['execution_detail_source']='scenes.json'
k['epistemic_clarification']={'Nina':'Dal has factual memory at entry. S08 means full emotional acknowledgment, not newly learning that Nina died. Reader receives hints only in S01/S05.'};js(b(1)/'knowledge.json',k)
t=rd(b(1)/'timeline.json');t['execution_detail_source']='scenes.json';t['S01']={'chapter_1':'D0 morning to evening','chapter_2':'D0 late evening to D1 morning','next_sequence':'D1 bounded Maya meeting'};js(b(1)/'timeline.json',t)
res=rd(b(1)/'resources.json');res['S01_access']={'client':'per-session scoped consent','Maya':'metadata-only then appointment only, no settings write','Ballast':'absent throughout S01','R':'R0 throughout S01'};js(b(1)/'resources.json',res)
voice=rd(b(1)/'voice.json');voice['calibration']={'status':'analytical_baseline_ready_sample_not_written','author_examples':'awaiting_author_samples','source':'execution/VOICE-CALIBRATION.md','scope':'first draft chapter 1'};voice['revision_reason']='Existing locked voice retained; analytical opening calibration added. No fictional sample or author example manufactured.';js(b(1)/'voice.json',voice)
save(b(1)/'execution/VOICE-CALIBRATION.md',"""# Голос першої глави: аналітична калібровка

Статус: робочі параметри до першої чернетки. Художнього sample немає. Авторських еталонів не надано.
Норма: BOOK_SYSTEM/LANGUAGES/uk/STYLE.md; індивідуальний профіль voice.json.

Даль помічає затримку відповіді, роботу рук, зміну голосу клієнта, зайву точність підтримки. Він пояснює собі дію професійно, але читач бачить ухилення від особистої відповіді.
Перше лице, минулий час. Розповідач не знає майбутнього результату справи і не коментує себе мовою терапевтичного звіту.
Короткі й середні фрази за дією; довша фраза може показати раціоналізацію. Після особистого збою — простіше. Квоти довжини, метафор і жартів відсутні.
Клієнт говорить про конкретну незручність своїми словами. Його компаньйон відповідає надто вчасно, але не стає карикатурою. У главі 1 це НЕ Баласт: він ще не призначений.
Гор з’являється лише повідомленням; його розгорнутий голос і умови замовлення — глава 2.
Гумор сухий і ситуативний. Не пояснювати власний жарт; не робити всіх персонажів однаково дотепними.
Нова проза одразу українська. Не перекладати російський план речення за реченням. Технічний термін допустимий там, де його справді вжив би Даль.
Критерій першої проби: читач відчуває і користь ремесла, і ціну захисту Даля, не отримавши прямої лекції про тему роману.
""")
save(b(1)/'execution/HANDOFF-CH01.md',"""# Завдання Sol/Terra: перша чернетка глави 1 «Контакту»

Пакет підготовлено 21.09.2026. Прозу в цій сесії не написано.
Це готове завдання для наступного дозволеного запуску; не команда запускати іншу модель зараз.

## Межі

Написати тільки главу 1 українською, від першої особи Марка Даля, у минулому часі.
Глава починається звичайним робочим калібруванням і закінчується повідомленням Гора та згодою Даля вислухати запит.
Зустріч із Гором, технічний слід старого шаблону, рішення взяти справу та дозвіл Майї на зустріч належать главі 2.
Не використовувати нерозгорнуті макропослідовності як готові сцени.
Жодного призначеного Баласта, переходу R1, завершеного горя, історії походження Ладу, пророцтва про війну або майбутні книги.

## Вхід

Даль — чинний вправний калібрувальник Ладу. Його робота справді допомагає людям. Професійний спосіб відповіді захищає його від близькості.
Справа Майї ще не прийшла. Особистого компаньйона Баласта ще немає.
Немає потреби пояснювати минуле Даля або називати Ніну в першій главі. Не вводити для неї вигаданий предмет, родинний факт чи спогад.
У клієнта власний програмний компаньйон. Налаштування змінюються лише після конкретного дозволу; чужу приватну переписку Даль безмежно не читає.

## Три сценічні задачі

1. Калібрування. Клієнтові заважає надто заспокійлива підказка під час складної звичайної розмови. Даль узгоджує межі діагностики й виправляє темп/момент відповіді. Клієнт сам перевіряє налаштування. Стало легше; це реальний успіх, а не викриття технології.
2. Подяка. Людина дякує особисто. Даль замінює відповідь професійною рекомендацією і повертається до екрана. Він ще не витримує прямого контакту. Немає прозріння про весь роман.
3. Вечір. Після виразного переходу часу Даль удома. Контрольований комфорт перериває приватний робочий запит Гора. Даль погоджується тільки вислухати; не бере ще замовлення і не втручається в життя Майї.

Повні goal/obstacle/decision/result/cost/next_cause: три записи chapter=1 у ../scenes.json.
Передсценічний стан: current-state.json. Локальні планові припущення: local-decisions.json.
Голос: VOICE-CALIBRATION.md та ../voice.json. Контрольні суми: ../../../series/preparation/2026-09-21/artifact-manifest.json.

## Виконання

Жива сцена важливіша за кількість пунктів. Без квоти слів, трьох однакових мінікульмінацій або обов’язкової метафори на абзац.
Показати користь процедури й нездатність Даля відповісти особисто через дію, без пояснення «ось моя травма».
Точні топоніми, нові глобальні правила, біографії клієнта та нові таємниці не потрібні.
Невелика оборотна предметна деталь допустима як виконання сцени; значущий новий канон занести окремою пропозицією, не підставляти мовчки.

## Вихід після майбутнього запуску

Окрема українська чернетка chapter-01.md зі статусом draft, не author_selected master.
Окремо: фактичні зміни стану, нові локальні деталі, незакриті питання; SHA-256 написаного файла.
Не переписувати плановий кінець книги як observed state. Перед главою 2 звірити фактичний кінець глави 1 з її карткою.
Перша чернетка стане й матеріалом перевірки голосу. Після неї потрібні незалежні проходи за REVIEW.md; не називати підготовку літературною перевіркою.
""")
# Update route documents, preserving package source files.
save(P/'series/CANON-POLICY.md',"""# Приоритет и границы источников

Текущая инструкция автора → PRE-DRAFT-LOCK-2026-09-19.md → выбранные BOOK-XX-ARCHITECTURE-LOCK.md и planned-реестры → scoped execution cards → исторические варианты.
Рабочий маршрут 21.09.2026: [preparation](preparation/2026-09-21/README.md). Он не меняет основные rules/макроисходы и не принимает Downloads целиком.
Все события остаются planned; рукописей нет. Изменения источников сохранены в before и журнале подготовки.
Количество и границы глав, локальная подача и обратимые детали могут уточняться при сохранении макрофункции. Ранги, POV, consent, исход Тараса/Тихона/Даля и этика войны не меняются молча.
Готовность главы 1 не означает готовность всех сцен серии. См. execution scope в book.json.
""")
contract=P/'series/ARCHITECTURE-PASS-01.md'
save(contract,"# Актуальный scope 21.09.2026\n\nМакропроход и межтомная сверка выполнены по пакетам; конкретный допуск к прозе — отдельно для каждой главы. Для текущего поручения готовится только первая глава: подробная S01, scoped gate и аналитическая калибровка голоса. Не требовать прозы-sample в задаче, которая заканчивается перед прозой. Полное завершение литературного цикла не заявлено.\n\nСм. [preparation](preparation/2026-09-21/README.md). Ниже сохранён исходный общий контракт; его полный gate применяется к полностью детализированному тому, не присваивается всей серии по одной главе.\n\n"+contract.read_text(encoding='utf-8-sig'))
save(P/'START_HERE.md',"""# Начать работу с «Разладом»

1. series/PRE-DRAFT-LOCK-2026-09-19.md — основные правила.
2. series/preparation/2026-09-21/README.md — текущая согласованная маршрутизация.
3. series/preparation/2026-09-21/baseline.json — выбранные файлы и SHA-256.
4. Выбранный book.json → plan.md → session.md; события planned, master=null.
5. Для первой главы: books/book-01/execution/HANDOFF-CH01.md.

Серия имеет восемь макрокаркасов. Том 4 дополнен 30-главным планом. Downloads-варианты сохранены отдельно и не имеют автоматического приоритета.
Текущий допуск после проверки: только глава 1 тома 1. S01 имеет шесть сцен в двух главах; перед главой 2 надо учесть фактический результат первой.
Новая проза украинская. В текущем поручении её не запускать: подготовить передачу Sol/Terra.
""")
# Narrow imported broad statements to the selected detailed source.
rp=P/'series/reveal-ladder.md';txt=rp.read_text(encoding='utf-8-sig');txt=txt.replace('сопротивление может обслуживаться системой; дискордантов больше','техническая аномалия заранее выделенной capacity; несколько объяснений остаются открыты').replace('нужность стала proxy управляемости; можно шепнуть аварийное происхождение метрик','coordination cost переиспользован как eligibility; внешний affect-service только в metadata')
save(rp,txt)
cp=P/'series/character-arcs.md';txt=cp.read_text(encoding='utf-8-sig').replace('Кн.7 — конкретная ставка будущего, не символ без личности.','Кн.7 — собственная траектория; режим Милы не зависит от подписи Даля под его договором.');save(cp,txt)
for n in range(1,9):
    bp=b(n)
    save(bp/'ARCHITECTURE-READINESS.md',f'# Готовность book-{n:02d}\n\nМакроплан выбран и сопоставлен с соседними томами. Реестры заполнены как planned projections; master отсутствует.\n'+
      ('S01: шесть сцен, две главы; конкретный допуск только глава 1, см. execution/ARCH-CHECK.md.\n' if n==1 else
       'Местные scene cards и отдельный gate до прозы этого тома ещё требуются. Не выдавать macro_reconciled за ready_for_draft всех глав.\n')+
      '\nТекущий проверенный scope: series/preparation/2026-09-21/verification.json. Opus/Gemini prose review: not_run.\n')
# Mark only scoped readiness; full-book claims remain false.
bk=rd(b(1)/'book.json');bk['stage']='ready_for_draft';bk['audit_status']='chapter_01_architecture_checked';bk['draft_scope']={'chapter':1,'sequence':'S01','whole_book_ready':False,'whole_series_ready':False,'prose_started':False,'execution':'execution/HANDOFF-CH01.md'};js(b(1)/'book.json',bk)
status={'schema_version':1,'project_id':'kontakt-razlad','pass_id':'architecture-pass-01','status':'macro_reconciled_scoped_opening_prepared','books':[{'book_id':f'book-{n:02d}','status':'ready_for_draft' if n==1 else 'macro_reconciled','architecture_pass':'macro_reviewed','scene_gate':'chapter_01_only' if n==1 else 'pending','master':None} for n in range(1,9)],'draft_gate':{'open_for':['book-01/chapter-01'],'all_other_chapters':'require_local_gate','prose_authoring_this_task':False}};js(P/'series/architecture-pass-01-status.json',status)
queue=rd(P/'series/continuity-queue.json');queue['preparation']=rel(O/'resolutions.json');queue['status']='selected_baseline_no_opening_blockers'
queue['items'] += [{'id':f'KONTAKT-REV-20260921-{k}','resolution_status':'resolved','status':'source_routing_applied','resolution':v,'source':'preparation/2026-09-21/resolutions.json'} for k,v in resolutions.items()]
js(P/'series/continuity-queue.json',queue)
# Future object choice remains explicit, while excluded from current scope.
aud=rd(b(1)/'audit/issues.json');aud['items'].append({'id':'B01-NINA-OBJECT-LATER','category':'motif','severity':'minor','certainty':'missing_link','decision':'proposed','resolution_status':'unresolved','observation':'Specific Nina keepsake M05 not selected. Chapter 1 explicitly excludes it; select and record before a later scene uses it.','dependencies':['book-01 M05 / later S05-S12'],'blocks_current_chapter':False});js(b(1)/'audit/issues.json',aud)
# Logs, tests and changes.
for n in range(1,9):
    lp=b(n)/'revision-log.json';log=rd(lp)
    log['items'].append({'id':RUN,'reason':'Author-authorized preparation after Book 4 publication','decision':'applied','old_source':'series/preparation/2026-09-21/before','new_source':'series/preparation/2026-09-21/baseline.json','changes':['Selected existing macro baseline','Archived legacy summaries and synchronized planned registers','Resolved active-route conflicts; preserved original review'],'affected_checks':['source integrity','handoff continuity','scope readiness'],'prose_changed':False});js(lp,log)
save(b(1)/'execution/ARCH-CHECK.md',"""# Архітектурний gate — глава 1

Статус: PASS для плану глави 1, не для художньої якості та не для всього тому.
Перевірив поточний архітектор у цій сесії; незалежний ансамбль не запускався.

- Чинне доручення завершується підготовкою до prose; текст не створено.
- Три картки C01 мають вхід, мету, опір, рішення, результат, ціну та причинний вихід.
- Перехід робота → подяка безпосередній; дім — після позначеного переходу часу.
- R0 зберігається в усій S01; ухилення від подяки не видане за R1.
- Програмний компаньйон клієнта не підмінений ще не призначеним Баластом.
- Клієнт сам дозволяє обмежене налаштування. У главі 1 немає доступу до Майї.
- Глава 2 має окремий read-only дозвіл Майї, а наступна зустріч не надає права міняти її profile.
- Знання Ніни не стерте: це захищена фактична пам’ять Даля; глибоке визнання вини пізніше не є новою інформацією про смерть.
- Особистий предмет Ніни не використовується до окремого вибору.
- Кінець глави 1 передає тільки запит Гора та згоду вислухати.
- Авторські українські еталони відсутні; голосова калібровка аналітична, без вигаданих цитат.
- Після реальної чернетки всі planned очікування звірити з observed текстом; оцінка літератури і мови тоді обов’язкова.
""")
checks=[]
for m in (P/'books').glob('book-*/pass01-manifest.json'):
    for x in rd(m)['files']:
        p=P/'books'/x['path'];assert h(p)==x['sha256'],str(p);checks.append(ref(p))
for n in range(1,9):
    for k in ['characters','knowledge','promises','timeline','motifs','end-state']:
        d=rd(b(n)/f'{k}.json');assert d['source_sha256']==h(b(n)/d['source_of_truth']);assert d['status']=='planned_projection'
    assert rd(b(n)/'book.json')['master'] is None
assert len(cards)==6 and len([x for x in cards if x['chapter']==1])==3
assert all(x['resonance_before']==x['resonance_after']=='R0' for x in cards)
assert all(x[k] for x in cards for k in ['goal','obstacle','decision','result','cost','next_cause','place','time','knowledge_before'])
assert all('Балласт' not in x['characters_present'] for x in cards)
doctor=subprocess.run([sys.executable,'tools/studio.py','doctor'],cwd=P,capture_output=True,encoding='utf-8',check=True);d=json.loads(doctor.stdout);assert not d['errors']
js(O/'verification.json',{'run_id':RUN,'package_hashes_checked':len(checks),'unchanged_package_files':checks,'planned_projections_checked':48,
 'handoffs_reviewed':7,'scene_cards':6,'chapter_01_cards':3,'current_gate':'PASS_architecture_chapter01_only','doctor':d,
 'source_selection':'reviewed','semantic_gate':'execution/ARCH-CHECK.md','prose':'not_written','voice_sample':'not_written',
 'independent_ensemble':'not_run','remaining':['Nina object before its later use','Book 4 numerical hearing details before its scene cards','local detail/gate for all later sequences'],
 'source_integrity_not_prose_quality':True})
# Record precise file versions and textual differences.
diffs=[]; records=[]
for p in list(changed):
    key=rel(p);old=before.get(key);oldtext=(R/old['path']).read_text(encoding='utf-8-sig') if old else ''
    newtext=p.read_text(encoding='utf-8-sig')
    records.append({'path':key,'before':old,'after_sha256':h(p),'change':'updated' if old else 'created'})
    diffs.extend(difflib.unified_diff(oldtext.splitlines(True),newtext.splitlines(True),fromfile=old['path'] if old else '/dev/null',tofile=key))
save(O/'changes.diff',''.join(diffs))
js(O/'changes.json',{'run_id':RUN,'files':records,'preserved_review':'2026-09-21-downloads-review unchanged','prose_changed':False})
save(O/'CHANGES.md','# Було — стало: підготовка\n\nБуло: макропакети співіснували з legacy scenes і суперечливими chapterization; статус підготовки не відображав виконаний огляд.\n\nСтало: одна вибрана робоча основа восьми томів; 48 planned-проєкцій; сім узгоджених переходів; S01 — дві глави і шість карток; вузький gate першої глави та завдання Sol/Terra.\n\nСтарі байти збережені в before/, точні SHA-256 — changes.json, повний текстовий diff — changes.diff. Вісім macro packages і первинний огляд не переписані. Проза не створювалася.\n')
artifacts=[p for p in changed if p.is_file()]+[O/'README.md',Path(__file__)]
js(O/'artifact-manifest.json',{'run_id':RUN,'files':[ref(p) for p in artifacts],'scope':'Preparation outputs; manifest excludes itself and later delivery index.'})
print(json.dumps({'changed_files':len(changed),'unchanged_macro_hashes':len(checks),'doctor_errors':d['errors'],'scene_cards':len(cards),'chapter01_gate':'PASS'},indent=2))

