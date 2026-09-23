from pathlib import Path
import sys,re,hashlib
p=Path(__file__).resolve().parent.parent/'terra-full-v2/assembled/manuscript.md'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='e641f3b639f0c03578c51916c0434156c584ce8022f556d94e522bf7c653679d'
first,last=map(int,sys.argv[1:3]);chapter=0
for n,t in enumerate(p.read_text(encoding='utf-8').strip().split('\n\n'),1):
 m=re.match(r'# Розділ (\d+)',t)
 if m:chapter=int(m.group(1))
 if first<=chapter<=last:print(f'[P{n:05d}] {t}\n')
