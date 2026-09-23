"""Record coordinator-verified final revision and preserve historical proofs."""
from pathlib import Path
import json,hashlib,re,copy,difflib,shutil
r=Path.cwd();book=r/'kontakt/books/book-01';revs=book/'revisions';out=revs/'2026-09-23-author-revision-v4';integ=revs/'2026-09-23-integration'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
def md(p,s):p.write_bytes(s.encode('utf-8'))
source=out/'manuscript.md';sha=h(source);assert sha=='32d70ac6e9dc3c523ee7a8fcd38db28f26aa77d5cd1908fa19f8eeb51f61b89f'
v3=revs/'2026-09-23-author-revision-v3';old=(v3/'manuscript.md').read_text(encoding='utf-8');text=source.read_text(encoding='utf-8')
before='Це нічого не свідчило про те, для чого я їх використаю далі.'
after='Це нічого не говорило про те, для чого я їх використаю далі.'
assert old.count(before)==1 and old.replace(before,after)==text
report=revs/'2026-09-23-final-native-astra/REPORT.md';reporttext=report.read_text(encoding='utf-8')
assert h(report)=='2e407287250f33ab234d17f7abc04d1035e3b2f4f1f9f5a2b0cf064544017691'
coverage=[(int(c),int(a),int(b)) for c,a,b in re.findall(r'\| (\d+) \| P(\d+)–P(\d+) \|',reporttext)]
assert len(coverage)==33 and coverage[0][1]==1 and coverage[-1][2]==2327
assert all(coverage[i][2]+1==coverage[i+1][1] for i in range(32))
inv=read(report.parent/'invocation.json');assert inv['exit_code']==0 and inv['item_types']==['agent_message']
save(out/'final-verification.json',{'status':'compatible_revision_complete','source_sha256':sha,
    'full_read':{'report':str(report.relative_to(book)).replace('\\','/'),'report_sha256':h(report),
        'source_sha256':h(v3/'manuscript.md'),'model_requested':'gpt-6-astra','actual_backend':'not independently attested',
        'reported_reading':'All2327blocks,33chapters; complete input provided in fresh context; per-chapter ranges checked',
        'coverage':coverage,'independent_ensemble_rerun':False},
    'post_read_delta':{'before':before,'after':after,'chapter':17,'anchor':'P01337',
        'exact_one_sentence_replay':True,'root_context_read':'CH17 opening through archive reply; subject, tense, agency and future reference preserved',
        'new_full_reread':'not needed or claimed for one exact local language correction'},
    'report_correction':'CH30 11:46 is shown before closing dialogue, not an exact departure timestamp. Original report remains frozen.',
    'publication_approval':False,'audio_reading':'not_run','human_author_proof':'not_claimed'})

# Transfer proofs only after exact quote/block checks. The old374-ID report stays frozen.
hist=read(integ/'historical-final-dispositions.json');assert hist['final_source_sha256']==h(v3/'manuscript.md')
matches=list(re.finditer(r'(?m)^# .+? (\d+)\n',text))
chaptertexts={int(m.group(1)):text[m.end():matches[i+1].start() if i+1<len(matches) else len(text)] for i,m in enumerate(matches)}
blocks={c:[x for x in re.split(r'\n\s*\n',t.strip()) if x.strip()] for c,t in chaptertexts.items()}
current=copy.deepcopy(hist);current['prior_evidence_file']='historical-final-dispositions.json';current['prior_evidence_sha256']=h(integ/'historical-final-dispositions.json')
current['final_source']=str(source.relative_to(r)).replace('\\','/');current['final_source_sha256']=sha
changed_evidence=[];quotes=0
for x in current['items']:
    x['final_source']=current['final_source'];x['final_source_sha256']=sha
    for e in x['final_current_evidence']:
        q=e['quote'];newq=q.replace(before,after)
        block=blocks[e['chapter']][int(e['anchor'][2:])-1]
        # A bounded quote can contain only part of the corrected sentence.
        if newq not in block and 'не свідчило про те, для чого' in newq:
            newq=newq.replace('не свідчило про те, для чого','не говорило про те, для чого')
        assert newq in block,(x['id'],e['chapter'],e['anchor'])
        if q!=newq:changed_evidence.append({'id':x['id'],'before':q,'after':newq})
        e.update(quote=newq,quote_start_in_block=block.index(newq),block_sha256=hashlib.sha256(block.encode()).hexdigest(),source_sha256=sha,
                 relation='exact_checked_in_final_v4; inherited_context_decision_except_single_CH17_language_fix')
        quotes+=1
current['scope']='All374 source IDs retained; all813 boundedquotes and namedblocks exactly checked in v4. Context decisions inherited from lockedv3 adjudication; only CH17 language delta reread. Not a fresh813-context literary pass.'
current['v4_delta']={'old_source_sha256':h(v3/'manuscript.md'),'new_source_sha256':sha,'changed_evidence':changed_evidence,'quotes_verified':quotes}
save(integ/'historical-final-v4-evidence.json',current)
central=book/'audit/issues.json';archive=integ/'central-issues-before-integration.json'
registry=read(archive if archive.exists() else central)
assert {x['id'] for x in registry['items']}=={x['id'] for x in current['items']} and len(current['items'])==374
if not archive.exists():shutil.copy2(central,archive)
assert h(archive)==hist['central_registry_sha256']
lookup={x['id']:x for x in current['items']}
for x in registry['items']:
    item=lookup[x['id']]
    x['prior_revision_resolution_status']=x.get('resolution_status')
    limit=item['coordinator_status']=='retained_nonblocking_mechanic_or_evidence_limit'
    x['resolution_status']='unresolved' if limit else 'resolved'
    x['current_revision_verification']={'source':current['final_source'],'source_sha256':sha,
        'record':'../revisions/2026-09-23-integration/historical-final-v4-evidence.json','record_id':x['id'],
        'coordinator_status':item['coordinator_status'],'rationale':item['coordinator_rationale'],
        'author_individual_vote_assigned':False,'blocks_novel_completion':False,
        'status':'bounded_unknown_retained' if limit else 'resolved_for_current_working_revision'}
registry['current_revision']={'source_sha256':sha,'processed_ids':374,'resolved_for_current_revision':372,
    'nonblocking_bounded_unknowns':2,'old_anchors_preserved':True,'prior_registry':'../revisions/2026-09-23-integration/central-issues-before-integration.json'}
save(central,registry)

original=book/'production/2026-09-21-book01/readers/full-33-astra-v1/manuscript.md'
md(integ/'complete-revision.diff',''.join(difflib.unified_diff(original.read_text(encoding='utf-8').splitlines(keepends=True),text.splitlines(keepends=True),fromfile='full-33-astra-v1',tofile='author-revision-v4',n=3)))
oldstate=book/'production/2026-09-21-book01/observed-full-volume-end-state.json';olddata=read(oldstate)
state={'status':'observed_working_revision_not_canonical','source':str(source.relative_to(book)).replace('\\','/'),'source_sha256':sha,
    'historical_observed_states':{'path':str(oldstate.relative_to(book)).replace('\\','/'),'sha256':h(oldstate),'scope':'Historical chapter states retained; revised dependencies below and full final read govern current working text'},
    'day_numbering':'D0–D11; twelve numbered story days',
    'revision_dependencies':[
        'CH3two bags distinguished; CH4calibrationterms/limitedlog unchangedsemantics; CH5riskletterandconsent retained',
        'CH14and27 active servicecontrols versus logged allowedmandate; no backdoor or retroactive permission',
        'CH16and17 Maya repliesTOGor beforeconfirmation; refusalformula synced, archive limited to4records',
        'CH19morningreportalready sent, oneof2later finished, lastfinishedCH21',
        'CH22Maya practicallimitedreason plus refusaltoexplainMORE; noautomatictrust',
        'CH25localrefusalrepairwithmediationON exists; Maya choosesrequestwiderinformation notconsent; CH26same morning',
        'CH27opens18:30window; CH28Maya persistentOFFownchoice andvoiceSTOP05:42; utilities remain',
        'CH30clock11:46before closingdialogue; exactdeparturetimeunknown',
        'CH31nonattendance18:01suspension; CH32voluntaryprofessionalclose plusseparatepersonalexit; motivesremainquestionable',
        'CH33calibrationterm/spoonhandlealigned; nofinalstateeventchanged byv4grammar'],
    'final_observed_state':copy.deepcopy(olddata['final_observed_state']),
    'book02_entry_constraints':[
        'User authorized continuing from this revised working version; not canonical-master or publication approval.',
        'Dal R1; professional participation voluntarily CLOSED after suspension, not fugitive. Ordinary rights, messages, maps, personaldocuments remain.',
        'Personal linked contour exited. No independent emergencykey; automateddooradmissionOFF. Local sensorindicator seen, not fullfunctiontest. Keyadmission does not establish automaticcallrestoration.',
        'Ballast remainsassignedsoftware; finalcardclosed/micOFF. No autonomoushouseholdaccess. ManualemergencyHELP saved, no actualcall. InheritedoldmodulehintnotprovedDalauthorship.',
        'Nina deadformerpartnerafterlongillness; Dalalwaysknewdeath, didnotcauseit; briefbodilygriefnothealing. SpoononhomeTOWELnear cup.',
        'Maya independentneutralroomonepaidnight perownmessage; addresswithheld, notfollower. Furtherdays require newevents, no offscreeninventedreturnGor.',
        'Tikhon disagreeswithnonattendance, offersconditionalfutureprocedurehelp; noautomaticrestoration.',
        'Financialreserve notspecified; no assumedinstantdestitution. Book2newdetails require explicitdraftproposals/events.'
    ],'canon_promoted':False}
state['final_observed_state']['source']={'path':str((out/'chapters/chapter-33.md').relative_to(r)).replace('\\','/'),'sha256':h(out/'chapters/chapter-33.md')}
state['final_observed_state']['future_dependencies']=['ContinueBook2under2026-09-23orderedworkflow; preserve boundedcarry-in above.']
state['final_observed_state'].pop('preflight',None)
save(out/'observed-state.json',state)
save(out/'dependency-sync.json',{'source_sha256':sha,'working_revision':'book.json updated; master stays null',
    'scenes_knowledge_timeline_resources_promises':'Own revision dependencies and observedstate updated; root planned registers remain planned, historical observedstates preserved.',
    'characters_and_series_canon':'No biography/identity/R1 canon change; workingcarry explicitly selected by continuation instruction.',
    'derived':'Exact33chapter slices, assembly, ownanchors/DOCX/extraction rebuilt. Master-derived snapshot not applicable withnullmaster.',
    'evidence':'374currentdispositions plus20fullENS+6Astra; previous proofs immutable, exactv4quotechecks separate.',
    'versions':'All intermediatev1/v2/v3 plus preliminaryv3 sourcehistory preserved; complete original→v4diff available.',
    'reader':'FinalDOCX/render sourcebound; visualrecordseparate.',
    'release':'Working reader, not public edition; no release orcanonical promotion.'})

meta=read(book/'book.json');meta.update(stage='working_revision_complete',audit_status='compatible_revision_verified_opus_availability_exception',active_workflow='../../series/WORKFLOW-2026-09-23-REVISION-AND-BOOK02.md',current_writer='Terra (revision); source prose Sol and Astra')
meta['draft_scope'].update(whole_book_ready=True,whole_series_ready=False,whole_book_written=True,readiness_scope='Complete corrected working volume; publication/authorcanonical approval not implied')
meta['working_revision']={'path':str(source.relative_to(book)).replace('\\','/'),'sha256':sha,'format':'md','language':'uk','status':'revised_working_volume_author_requested_continuation_basis','scope':'whole_volume_33chapters','observed_state':str((out/'observed-state.json').relative_to(book)).replace('\\','/')}
meta['working_volume']={'manifest':str((out/'assembly.json').relative_to(book)).replace('\\','/'),'chapters':33,'status':'complete_corrected_working_volume'}
assert meta['master'] is None;save(book/'book.json',meta)
log=read(book/'revision-log.json');assert not any(x.get('id')=='book01-all-reviews-20260923-v4' for x in log['items'])
log['items'].append({'id':'book01-all-reviews-20260923-v4','reason':'Explicit author request: correct firstbookaccordingtoallreviews/questions andcontinuebook2',
    'decision':'compatible_coordinator_package_applied_under_bulk_authorization_not_individual_author_votes',
    'old_source':{'path':str(original.relative_to(book)).replace('\\','/'),'sha256':h(original)},'new_source':meta['working_revision'],
    'changes':'revisions/2026-09-23-integration/complete-revision.diff','decisions':'revisions/2026-09-23-integration/full-volume-dispositions.md',
    'historical_ids':'revisions/2026-09-23-integration/historical-final-v4-evidence.json','dependencies':str((out/'dependency-sync.json').relative_to(book)).replace('\\','/'),
    'verification':str((out/'final-verification.json').relative_to(book)).replace('\\','/'),'master_promoted':False})
save(book/'revision-log.json',log)
md(book/'session.md',f'''# Контакт 1 — сумісна редакція завершена\n\nУсі 33 глави виправлені за повнотомним ансамблем, шістьма питаннями Astra та поіменним розглядом 374 історичних ID. Поточна робоча редакція: [v4](revisions/2026-09-23-author-revision-v4/manuscript.md), SHA-256 `{sha}`. [Передача](revisions/2026-09-23-integration/DELIVERY.md).\n\nПовний повторний прохід Astra охопив 2327 блоків v3. Єдину локальну мовну поправку застосовано у v4, перевірено точний diff і контекст. Старі Terra, Gemini 3.8 Flash та Gemini 3.1 Pro залишаються повними діагнозами попереднього джерела; Opus був частковим через недоступність, із прямим дозволом автора на пропуск. Нових чотирьох повних проходів не заявлено.\n\n372 центральні питання закрито для цієї робочої редакції; два збережені як неблокирувальні межі знання про аварійний ключ і первинне історичне підтвердження. [Рішення](revisions/2026-09-23-integration/full-volume-dispositions.md) розрізняють виправлення, збережені стилеві вибори та хибні припущення рецензентів. Master не призначено; публічний випуск не затверджено.\n\nПродовження тому 2 дозволене поточним дорученням автора на базі [спостереженого стану](revisions/2026-09-23-author-revision-v4/observed-state.json). Порядок: вся структура → усі первинні чернетки Astra → усі повні глави Terra → незалежні літературні проходи → звірка → підсумкова редакція Terra.\n''')
for name in ['plan.md','brief.md']:
    p=book/name;s=p.read_text(encoding='utf-8-sig')
    md(p,'> Поточний стан 2026-09-23: усі 33 глави й сумісна редакція завершені; див. [session.md](session.md). Нижче збережено архітектурний план, не заміну фактам робочої v4.\n\n'+s)
md(integ/'DELIVERY.md',f'''# Контакт — перший том після редактури\n\nГотова повна робоча редакція 33 глав. SHA-256: `{sha}`.\n\n- [Рукопис](../2026-09-23-author-revision-v4/manuscript.md).\n- [DOCX для читання](../2026-09-23-author-revision-v4/reader/Контакт%20—%20том%201%20—%20підсумкова%20редакція%202026-09-23.docx).\n- [Повний diff](complete-revision.diff), [повнотомні рішення](full-volume-dispositions.md), [усі 374 ID](historical-final-v4-evidence.json).\n- [Заключна перевірка](../2026-09-23-author-revision-v4/final-verification.json), [стан для другого тому](../2026-09-23-author-revision-v4/observed-state.json).\n\nСкорочено дублікати без вилучення нових згод; прояснені вибір Майї, активні інструменти й межі мандата, локальна альтернатива ремонту, мотиви сумнівних рішень Даля. Виправлені конкретні мовні й предметні неузгодженості. Несумісні, повторні та недоведені пропозиції не додані до сюжету.\n\nДоступні три повні попередні літературні діагнози: Terra, Gemini 3.8 Flash, Gemini 3.1 Pro. Opus прочитав лише частину через429; застосовано авторський виняток. Після виправлень Astra прочитала весь том, потім перевірена одна фінальна мовна заміна. Це завершена робоча редакція для читання та продовження, а не оголошення авторського канону чи публічного випуску.\n''')
md(integ/'QUESTIONS-AND-LIMITS.md','''# Питання та збережені межі\n\nОбов’язкових нових відповідей автора для завершення цієї редакції немає. Поточне загальне доручення вже дозволило сумісні виправлення.\n\n1. Окремий аварійний ключ явно дає доступ через двері. Чи відновлює він автоматичний виклик, перший том не встановлює. Другий том не повинен додавати це мовчки.\n2. Первинний текст історичного підтвердження Майї відсутній у доступному архіві. Не можна робити з нього доказ повної поінформованості про всі пізніші наслідки.\n3. Канонічний master і публічний випуск автоматично не затверджені. Продовження другого тому й читательська копія цього не потребують.\n\nМісце для авторських приміток:\n\n\n''')
print(json.dumps({'source_sha256':sha,'ids':374,'quotes':quotes,'changed_evidence':len(changed_evidence),'status':'integrated_working_revision'},ensure_ascii=False))
