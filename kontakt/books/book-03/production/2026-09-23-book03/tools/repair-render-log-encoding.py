"""Preserve the historical PowerShell UTF-16 log and expose an equivalent UTF-8 JSON."""
from pathlib import Path
import json, hashlib, shutil
root=Path(__file__).resolve().parents[6]
run=Path(__file__).resolve().parent.parent
p=run/'terra-reader/render-check-output.json'
old=p.read_bytes()
assert old.startswith(bytes([255,254]))
backup=p.with_suffix('.json.utf16-original')
assert not backup.exists()
backup.write_bytes(old)
data=json.loads(old.decode('utf-16'))
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert json.loads(p.read_text(encoding='utf-8'))==data
record=run/'render-log-encoding-corrigendum.json'
record.write_text(json.dumps({'reason':'PowerShell redirected the historical render stdout as UTF-16; repository doctor requires UTF-8 JSON. Parsed content is unchanged. Historical delivery manifest remains immutable and identifies the preserved original bytes.','original_path':str(p.relative_to(root)),'preserved_original':str(backup.relative_to(root)),'original_sha256':hashlib.sha256(old).hexdigest(),'utf8_sha256':hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+'\n',encoding='utf-8')
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-BOOK03-2026-09-23')
for f in [p,backup,record,Path(__file__).resolve()]:
    d=desktop/f.relative_to(root);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d)
print('Preserved original bytes; equivalent UTF-8 log and provenance mirrored.')
