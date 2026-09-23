"""Fresh native Terra authoring execution; preserve the entire returned text and trace."""
import argparse, hashlib, json, subprocess, tempfile, time, shutil
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--prompt',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--model',required=True)
a=p.parse_args()
assert not a.out.exists(), 'Use a new immutable execution directory'
a.out.mkdir(parents=True)
payload=a.prompt.read_bytes()
(a.out/'prompt.md').write_bytes(payload)
response=(a.out/'RESPONSE.md').resolve()
command=['codex','exec','--ignore-user-config','--skip-git-repo-check','--ephemeral',
         '--sandbox','read-only','--model',a.model,'--json','--output-last-message',str(response),'-']
record={'role':'authoring','model_requested':a.model,'client':'codex exec',
        'actual_backend':'not independently attested','context':'fresh isolated cwd; only inline source material',
        'command':command,'prompt_sha256':hashlib.sha256(payload).hexdigest(),'status':'running'}
def save():
    (a.out/'invocation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
save()
started=time.monotonic()
with tempfile.TemporaryDirectory(prefix='kontakt-native-author-') as cwd:
    with (a.out/'stdout.jsonl').open('wb') as stdout,(a.out/'stderr.txt').open('wb') as stderr:
        process=subprocess.Popen(command,cwd=cwd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr)
        try:
            process.communicate(input=payload,timeout=3600)
            code=process.returncode
        except subprocess.TimeoutExpired:
            process.kill();process.communicate();code=124
events=[]
for line in (a.out/'stdout.jsonl').read_text(encoding='utf-8',errors='replace').splitlines():
    try:events.append(json.loads(line))
    except ValueError:pass
record.update(exit_code=code,seconds=round(time.monotonic()-started,2),
    status='returned_pending_manual_validation' if code==0 and response.exists() else 'unavailable_or_incomplete',
    thread_ids=[e.get('thread_id') for e in events if e.get('type')=='thread.started'],
    item_types=sorted({e.get('item',{}).get('type','unknown') for e in events if 'item' in e}),
    usage=[e['usage'] for e in events if 'usage' in e],
    response_sha256=hashlib.sha256(response.read_bytes()).hexdigest() if response.exists() else None,
    limitation='Transport/model request does not establish reading, literary quality or backend identity.')
save()
root=Path.cwd().resolve()
desktop=Path('C:/Users/alexi/OneDrive/Desktop/KONTAKT-REVISION-BOOK02-2026-09-23')
for f in [Path(__file__).resolve(),*a.out.resolve().rglob('*')]:
    if f.is_file():
        dest=desktop/f.relative_to(root);dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(f,dest);assert dest.read_bytes()==f.read_bytes()
print(json.dumps({k:record[k] for k in ['status','model_requested','exit_code','seconds','item_types']},ensure_ascii=False))
