"""Execute a prepared multipart review through agy, preserving every response.

Never treats transport success as proof of full literary reading. A human/model
coordinator must validate every range, quote, cross-part conclusion and limitation.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,tempfile,time
p=argparse.ArgumentParser();p.add_argument('--packet',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
def sha(v):return hashlib.sha256(v).hexdigest()
def put(path,value):path.write_bytes((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
packet=json.loads((a.packet/'packet.json').read_text(encoding='utf-8'));payload=(a.packet/'input.ndjson').read_bytes()
assert packet['client']=='agy' and packet['status']=='prepared_not_executed'
assert sha(payload)==packet['input_sha256'],'Prepared input changed'
assert sha(Path(packet['target']).read_bytes())==packet['target_sha256'],'Target source changed'
assert packet['role']!='gemini_pro' or not packet['references'],'Pro context prohibited'
messages=[json.loads(line) for line in payload.decode('utf-8').splitlines()]
assert len(messages)==packet['input_events']==packet['expected_result_events']
assert not a.out.exists(),'Use a fresh immutable result directory';a.out.mkdir(parents=True)
(a.out/'packet.json').write_bytes((a.packet/'packet.json').read_bytes())
(a.out/'input.ndjson').write_bytes(payload)
(a.out/'runner.py').write_bytes(Path(__file__).read_bytes())
limit=660*len(messages)
command=['agy','--new-project','--model',packet['requested_model'],'--mode','plan','--sandbox','--input-format','stream-json','--output-format','stream-json','--print-timeout',f'{limit}s']
record={'status':'running','role':packet['role'],'client':'agy','requested_model':packet['requested_model'],'target_sha256':packet['target_sha256'],'scope':packet['scope'],'through_chapter':packet['through_chapter'],'input_sha256':packet['input_sha256'],'expected_result_events':len(messages),'command':command,'isolation':'Fresh temporary directory and new project; no tools or peer reports allowed; prepared references only','actual_backend':'not independently attested','timeout_seconds':limit}
put(a.out/'invocation.json',record);started=time.monotonic()
with tempfile.TemporaryDirectory(prefix='kontakt-independent-volume-reader-') as cwd:
 with (a.out/'stdout.ndjson').open('wb') as stdout, (a.out/'stderr.txt').open('wb') as stderr:
  process=subprocess.Popen(command,cwd=cwd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr)
  try:process.communicate(input=payload,timeout=limit);code=process.returncode
  except subprocess.TimeoutExpired:process.kill();process.communicate();code=124
events=[];invalid_lines=0
for line in (a.out/'stdout.ndjson').read_text(encoding='utf-8',errors='replace').splitlines():
 try:events.append(json.loads(line))
 except ValueError:invalid_lines+=1
results=[e['result'] for e in events if isinstance(e,dict) and e.get('event')=='result' and isinstance(e.get('result'),dict)]
steps=sorted({e.get('step_update',{}).get('step_type','unknown') for e in events if isinstance(e,dict) and e.get('event')=='step_update'})
responses=[]
for i,result in enumerate(results,1):
 text=result.get('response') or result.get('result') or '';text=text if isinstance(text,str) else ''
 name=f'turn-{i:03d}.md';(a.out/name).write_bytes((text+'\n').encode('utf-8'))
 responses.append({'turn':i,'file':name,'sha256':sha((a.out/name).read_bytes()),'characters':len(text),'provided_range':packet['parts'][i-1] if i<=len(packet['parts']) else 'final request','reported_coverage':'requires_manual_validation'})
final=(results[-1].get('response') or results[-1].get('result') or '') if results else ''
# A context checkpoint is transport compaction, not a repository/tool action.
# Its presence remains explicit and still requires manual coverage adjudication.
record['context_checkpoint_observed']='checkpoint' in steps
valid=(code==0 and len(results)==len(messages) and isinstance(final,str) and len(final.strip())>=200 and packet['target_sha256'] in final and set(steps)<={'user_input','agent_response','checkpoint'} and all(not r.get('is_error') and r.get('status')!='ERROR' for r in results))
if valid:
 (a.out/'REPORT.md').write_bytes((final+'\n').encode('utf-8'));record['report_sha256']=sha((a.out/'REPORT.md').read_bytes())
record.update(status='report_returned_pending_manual_coverage_validation' if valid else 'unavailable_or_incomplete',exit_code=code,seconds=round(time.monotonic()-started,2),result_events=len(results),invalid_stdout_lines=invalid_lines,observed_step_types=steps,client_init_metadata=[e['init'] for e in events if isinstance(e,dict) and e.get('event')=='init' and 'init' in e],responses=responses,scope_limit='Complete input delivery and report return are not proof of full reading; inspect all turn reports, unread/compacted context and final cross-part analysis before importing.')
put(a.out/'invocation.json',record)
print(json.dumps({k:record[k] for k in ['status','role','requested_model','exit_code','seconds','result_events']}))
