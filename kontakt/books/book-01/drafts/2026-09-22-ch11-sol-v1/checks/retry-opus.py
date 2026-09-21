"""One scheduled retry after the provider-reported quota reset; never changes prose."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, subprocess, sys, time
root=Path(__file__).resolve().parents[6]
# Resolve by repository marker rather than relying on the caller working directory.
while not (root/'tools/run_book_review.py').is_file():
    assert root.parent != root, 'Repository root not found'
    root=root.parent
draft=root/'kontakt/books/book-01/drafts/2026-09-22-ch11-sol-v1'
source=draft/'chapter-11.md'
expected='73576e800293e0184210e055aec9e9c9a5f46762f60f95aff23fa9ac669e0319'
deadline=datetime(2026,9,22,0,9,0,tzinfo=timezone.utc)
print('Waiting for provider reset until '+deadline.isoformat(),flush=True)
while True:
    remaining=(deadline-datetime.now(timezone.utc)).total_seconds()
    if remaining<=0:break
    time.sleep(min(30,remaining))
assert hashlib.sha256(source.read_bytes()).hexdigest()==expected,'Frozen source changed'
out=draft/'checks/opus'
assert not out.exists(),'Never overwrite or duplicate a review attempt'
args=[sys.executable,'-X','utf8','tools/run_book_review.py','--client','agy','--role','opus','--model','claude-opus-4-6-thinking','--target',str(source),'--prompt',str(draft/'checks/prompts/opus.md'),'--context','kontakt/books/book-01/voice.json','--context','kontakt/books/book-01/execution/HANDOFF-CH11.md','--context','BOOK_SYSTEM/LANGUAGES/uk/STYLE.md','--out',str(out)]
print('Starting the same required Opus selector on the same frozen source',flush=True)
raise SystemExit(subprocess.run(args,cwd=root).returncode)
