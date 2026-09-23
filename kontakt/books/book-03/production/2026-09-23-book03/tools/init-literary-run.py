"""Register the explicit author workflow without inventing completed diagnoses."""
from pathlib import Path
import json,hashlib,shutil
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;area=run/'literary-v1';dest=area/'run.json';assert not dest.exists()
source=run/'terra-full-v1/assembled/manuscript.md';sha=hashlib.sha256(source.read_bytes()).hexdigest();assembly=json.loads((source.parent/'assembly.json').read_text(encoding='utf-8'));assert sha==assembly['manuscript_sha256']
roles=['terra','gemini_flash','gemini_pro','opus']
data={'schema_version':'author-workflow-2026-09-23','run_id':'book03-literary-v1','project_id':'kontakt','book_id':'book-03','language':'uk','status':'independent_reviews_running','source':{'path':source.relative_to(root).as_posix(),'sha256':sha,'chapters':32,'blocks':assembly['paragraphs']},'required_diagnoses':roles,'effective_locked_diagnoses':[],'review_policy_basis':'Explicit author workflow: isolated Terra + agy Flash + agy Pro + Opus attempt. Author permits unavailable Opus to be skipped with actual evidence. Astra later reconciliation is nonblind, not a fabricated fourth independent diagnosis.','reports':{role:{'role':role,'file':'results/'+role+'/REPORT.md','status':'pending_execution_and_coverage_validation'} for role in roles},'exceptions':[],'reconciliation':{'path':'../reconciliation-v1/reconciliation.md','status':'not_started'},'issue_ledger':'../reconciliation-v1/issue-ledger.json','patch_plan':'../reconciliation-v1/PATCH-PLAN.json','individual_author_decisions':'pending; separate bulk compatible implementation authorized','legacy_cli_compatible':False}
dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for p in [Path(__file__).resolve(),dest,*[f for f in (area/'packets').rglob('*') if f.is_file()],*[f for f in (run/'terra-reader').rglob('*') if f.is_file()],run/'terra-full-language-qa.json',run/'terra-full-naturalness.json']:
 d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
for p in (run/'terra-reader/reader').glob('*.docx'):
 for d in [Path('C:/Users/alexi/OneDrive/Desktop'),Path('C:/Users/alexi/Desktop')]:
  target=d/p.name;assert not target.exists();shutil.copy2(p,target)
print(json.dumps({'status':data['status'],'source_sha256':sha}))
