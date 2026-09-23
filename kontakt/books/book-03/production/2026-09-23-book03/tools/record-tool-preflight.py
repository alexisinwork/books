from pathlib import Path
import ast,hashlib,json,shutil,subprocess
root=Path(__file__).resolve().parents[6];run=Path(__file__).resolve().parent.parent
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=list((run/'tools').glob('*.py'))
for p in files:ast.parse(p.read_text(encoding='utf-8'))
report={'status':'syntax_validated_not_execution_or_prose_validation','tools':[{'path':p.relative_to(root).as_posix(),'sha256':sha(p)} for p in files]}
path=run/'tools-syntax-check.json';path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
provenance=run/'tool-provenance.json';items=json.loads(provenance.read_text(encoding='utf-8'));known={v['copy'] for v in items}
for name in ['import-terra-block.py','prepare-native-literary.py','verify-complete-phase.py']:
    old=root/'kontakt/books/book-02/production/2026-09-23-book02/tools'/name;new=run/'tools'/name
    if new.relative_to(root).as_posix() not in known:
        items.append({'source':old.relative_to(root).as_posix(),'source_sha256':sha(old),'copy':new.relative_to(root).as_posix(),'copy_sha256':sha(new),'adaptation':'Book3 phase and Desktop routing; chapter count inferred from full structure where applicable.'})
provenance.write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
for p in [*files,path,provenance]:
    d=desktop/p.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
print(json.dumps({'parsed_and_mirrored':len(files)}))
