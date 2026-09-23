"""Record completed authoring, preserving the review target and its predecessors."""
from pathlib import Path
import hashlib, json, shutil, difflib
root = Path(__file__).resolve().parents[6]
run = Path(__file__).resolve().parent.parent
phase = run / 'terra-full-v2'
desktop = Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')
source = phase / 'assembled/manuscript.md'
assert sha(source) == 'e641f3b639f0c03578c51916c0434156c584ce8022f556d94e522bf7c653679d'
record = run/'root-terra-reading/chapters-31-36-native.json'
assert not record.exists()
write(record, {'status':'nonblind_coordinator_reading','source_sha256':sha(source),
 'items':[{'chapter':n,'source':(phase/f'chapters/chapter-{n:02d}.md').relative_to(root).as_posix(),'sha256':sha(phase/f'chapters/chapter-{n:02d}.md'),'actual_reading':'Complete chapter read by coordinator; CH35 and CH36 separately re-read after an earlier truncated combined display.'} for n in range(31,37)],
 'findings':[{'id':'ROOT-TERRA-14','chapter':31,'category':'temporal referent / character rhetoric','confidence':'medium','quote':'Ви вже пішли посеред включення.','finding':'CH26 Dal declined before broadcast began. Vector may be exaggerating, but literal timing is inconsistent.','compatible_direction':'Consider refused broadcast at last minute rather than left during broadcast; preserve professional cost.'}],
 'observations':['CH33 Wednesday: table parts delivered; adapter responsibility transferred to Taras for Thursday. Clarify distinction from Monday table delivery only if needed.','CH34 friendship invitation and Nina memory do not become rescue or healing; Ballast receives typed request only.','CH35 Dal obtains primary creation time, distinguishes extraction time and asks about unknown other reserves; local confirmation has bounded scope.','CH36 compares zone, route version, three timestamps and local orders; multiple ordinary hypotheses remain open. Friday meeting stays friendship rather than a recruitment pretext.'],
 'limits':'Coordination reading, not a fourth independent literary report. Findings await Astra reconciliation.'})
p=read(phase/'progress.json'); p.update(status='complete_source_frozen_pending_final_revision',source_sha256=sha(source),literary_review='Fresh Terra and both agy Gemini reports returned; Opus incomplete. Validation and Astra reconciliation in progress.'); write(phase/'progress.json',p)
p=read(run/'progress.json')
p['phases'][2].update(status='complete',source_sha256=sha(source),gate='terra-full-v2-technical-verification.json')
p['phases'][3]['status']='reports_returned_pending_validation'
p['phases'][4]['status']='in_progress'
write(run/'progress.json',p)
book=run.parents[1]/'book.json'; p=read(book)
p.update(stage='full_text_editorial_reconciliation',audit_status='full_terra_written_independent_reports_validation_in_progress')
p['draft_scope']['whole_book_written']=True
p['active_full_text']={'path':source.relative_to(book.parent).as_posix(),'sha256':sha(source),'chapters':36,'canonical_status':'working_not_author_approved'}
write(book,p)
diff=[]
for n in range(1,37):
    name=f'chapter-{n:02d}.md'
    a=run/'astra-rough-v1/chapters'/name; b=phase/'chapters'/name
    diff.extend(difflib.unified_diff(a.read_text(encoding='utf-8').splitlines(True),b.read_text(encoding='utf-8').splitlines(True),fromfile='astra-rough-v1/'+name,tofile='terra-full-v2/'+name))
(phase/'rough-to-full.diff').write_text(''.join(diff),encoding='utf-8',newline='\n')
write(phase/'authoring-completion.json',{'status':'full_literary_source_complete_not_final','source_sha256':sha(source),'chapters':36,'scenes':41,'words':24525,'paragraphs':1894,'model_requested':'gpt-5.6-terra','execution':'Six independent native codex exec sessions; complete architecture and all rough prose plus prior full-text states supplied. Original responses and metadata-only repairs preserved.','backend_attestation':'Requested CLI model recorded; backend identity not independently attested.','previous_incomplete_attempt':'../terra-full-v1/ATTEMPT-STATUS.json','predecessor_sha256':'a0e9936025cfd786299c8a62f929a706982a22a1cff9576aad7934e548029c13','technical_gate':'../terra-full-v2-technical-verification.json','root_reading':'../root-terra-reading/*-native.json','known_pending_issues':'Calendar, duplicate action, local typo and referents recorded in coordinator notes; all await source-bound reconciliation.','unresolved_canon':'Book audit/issues.json U01–U05 retained; no silent canonical promotion.'})
write(phase/'manifest.json',{'status':'frozen_full_source_before_final_revision','source_sha256':sha(source),'files':[{'path':f.relative_to(phase).as_posix(),'sha256':sha(f)} for f in sorted(phase.rglob('*')) if f.is_file() and f.name!='manifest.json']})
reader=run/'terra-reader'; reader.mkdir(exist_ok=False); shutil.copy2(source,reader/'manuscript.md')
for area in [phase,run/'literary-v1',run/'review-prompts',run/'root-terra-reading',reader]:
    for f in area.rglob('*'):
        if f.is_file():
            dest=desktop/f.relative_to(root); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(f,dest)
for f in [book,run/'progress.json',Path(__file__).resolve(),run/'terra-full-v2-technical-verification.json']:
    dest=desktop/f.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
print(json.dumps({'status':'full_source_frozen_and_mirrored','sha256':sha(source)}))
