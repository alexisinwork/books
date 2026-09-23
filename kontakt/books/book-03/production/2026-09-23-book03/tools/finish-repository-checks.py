"""Run final structural/source checks, freeze the completed phase, and mirror the package."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent;phase=run/'terra-final-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
def rel(p):return p.relative_to(root).as_posix()
out=run/'final-repository-checks.json';assert not out.exists();checks=[]
for args in [['tools/studio.py','doctor'],['tools/verify_sources.py']]:
 result=subprocess.run([sys.executable,'-X','utf8',*args],cwd=root/'kontakt',capture_output=True,text=True,encoding='utf-8');checks.append({'command':['python','-X','utf8',*args],'cwd':'kontakt','exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr});assert result.returncode==0,result.stdout+result.stderr
write(out,{'status':'structural_and_original_source_checks_passed','source_sha256':sha(phase/'assembled/manuscript.md'),'checks':checks,'limits':'Doctor is not prose verification; intentional null masters remain warnings. Originals verification does not promote the working text.'})
gate_path=run/'final-acceptance.json';shutil.copy2(gate_path,run/'final-acceptance.before-repository-check.json');gate=json.loads(gate_path.read_text(encoding='utf-8'));gate['checks']['repository_and_sources']='final-repository-checks.json';gate['repository_check_sha256']=sha(out);write(gate_path,gate)
manifest=phase/'manifest.json';assert not manifest.exists()
write(manifest,{'status':'frozen_complete_corrected_working_volume_not_canon','source_sha256':sha(phase/'assembled/manuscript.md'),'final_acceptance':rel(gate_path),'final_acceptance_sha256':sha(gate_path),'files':[{'path':f.relative_to(phase).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size} for f in sorted(phase.rglob('*')) if f.is_file() and '__pycache__' not in f.parts]})
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [Path(__file__).resolve(),out,gate_path,run/'final-acceptance.before-repository-check.json',manifest]:
 d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);assert sha(f)==sha(d)
print(json.dumps({'checks':[{'command':x['command'],'exit_code':x['exit_code']} for x in checks],'manifest_sha256':sha(manifest)}))
