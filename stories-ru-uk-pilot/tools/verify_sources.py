#!/usr/bin/env python3
"""Verify verbatim sources, plus lossless omnibus splits when supplied."""
import hashlib,json
from pathlib import Path
import argparse

def check(root):
 root=Path(root).resolve(); candidates=[root/'sources/source-manifest.json',root/'source-manifest.json']
 manifest=next((p for p in candidates if p.exists()),None)
 if manifest is None:return {'checked':0,'errors':[],'scope':'No source manifest in this clean project.'}
 data=json.loads(manifest.read_text(encoding='utf8'));entries=data.get('files',data.get('sources',[]));errors=[]
 def content(rel):
  p=(root/rel).resolve()
  if not p.is_relative_to(root) or not p.is_file():raise ValueError('Invalid source path: '+rel)
  return p.read_bytes()
 for e in entries:
  rel=e.get('archive_path',e.get('path'))
  try:
   raw=content(rel)
   if hashlib.sha256(raw).hexdigest()!=e['sha256']:errors.append(rel+': hash changed')
   if len(raw)!=e['bytes']:errors.append(rel+': size changed')
  except (OSError,ValueError,KeyError) as ex:errors.append(str(ex))
 split=root/'sources/omnibus-split.json'
 reconstructed=False
 if split.exists():
  s=json.loads(split.read_text(encoding='utf8'))
  try:
   joined=b''.join(content(e['path']) for e in s['segments'])
   reconstructed=joined==content(s['source_path'])
   if not reconstructed:errors.append('Omnibus reconstruction differs from original bytes')
  except (OSError,ValueError,KeyError) as ex:errors.append(str(ex))
 return {'checked':len(entries),'errors':errors,'omnibus_reconstructed':reconstructed,'scope':'Original bytes only; not proof of literary quality or full reading.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default=str(Path(__file__).resolve().parents[1]));r=check(p.parse_args().root);print(json.dumps(r,ensure_ascii=False,indent=2));raise SystemExit(bool(r['errors']))
