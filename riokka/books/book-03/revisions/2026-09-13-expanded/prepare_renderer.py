#!/usr/bin/env python3
"""Unpack the distribution's Writer packages into a private temporary directory.

No system installation or privileged command is performed.
"""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import sys
import urllib.request

def relocate(root):
    count = 0
    for p in root.rglob('*'):
        if not p.is_symlink():
            continue
        dest = os.readlink(p)
        local = root / dest.lstrip('/')
        if dest.startswith('/') and local.exists():
            p.unlink()
            p.symlink_to(os.path.relpath(local, p.parent))
            count += 1
    print(json.dumps({'relocated_private_package_links': count}), flush=True)

def configure_private(root):
    # The distribution's postinst normally copies this default via ucf.
    default = root / 'usr/lib/libreoffice/share/.registry/main.xcd'
    configured = root / 'etc/libreoffice/registry/main.xcd'
    configured.parent.mkdir(parents=True, exist_ok=True)
    if not configured.exists():
        shutil.copy2(default, configured)
    fundamental = root / 'usr/lib/libreoffice/program/fundamentalrc'
    value = fundamental.read_text().replace('BRAND_BASE_DIR=file:///usr/lib/libreoffice',
        'BRAND_BASE_DIR=' + (root / 'usr/lib/libreoffice').as_uri())
    fundamental.write_text(value)
    # Debian's split UNO libraries resolve their ini beside libuno_sal.
    program = root / 'usr/lib/libreoffice/program'
    uno_ini = root / 'usr/lib/x86_64-linux-gnu/unorc'
    uno_ini.write_text((program / 'unorc').read_text().replace('${ORIGIN}', program.as_uri()))

if '--relocate-existing' in sys.argv:
    manifest = json.loads((Path(__file__).resolve().parent / 'renderer-local.json').read_text())
    configure_private(Path(manifest['root']))
    relocate(Path(manifest['root']))
    sys.exit(0)

target = Path(tempfile.mkdtemp(prefix='riokka-render-'))
packages = target / 'packages'
packages.mkdir()
root = target / 'root'
root.mkdir()
result = subprocess.run(['apt-get', '--print-uris', '--yes', '--download-only', '--no-install-recommends',
    '-o', 'Debug::NoLocking=true', 'install', 'libreoffice-writer'], capture_output=True, text=True, check=True)
entries = re.findall(r"^'(https?://[^']+)' (\S+) (\d+) MD5Sum:([0-9a-f]+)$", result.stdout, re.M)
assert entries
print(json.dumps({'directory': str(target), 'packages': len(entries)}, ensure_ascii=False), flush=True)

def fetch(entry):
    url, name, size, md5 = entry
    assert '/' not in name and name.endswith('.deb')
    url = re.sub(r'^http://(archive\.ubuntu\.com|security\.ubuntu\.com)/', r'https://\1/', url)
    data = urllib.request.urlopen(url, timeout=90).read()
    assert len(data) == int(size), name
    assert hashlib.md5(data).hexdigest() == md5, name
    p = packages / name
    p.write_bytes(data)
    return p

with ThreadPoolExecutor(max_workers=6) as pool:
    downloaded = list(pool.map(fetch, entries))
for p in downloaded:
    subprocess.run(['dpkg-deb', '-x', str(p), str(root)], check=True)
configure_private(root)
relocate(root)
manifest = {'root': str(root), 'packages': [p.name for p in downloaded]}
(Path(__file__).resolve().parent / 'renderer-local.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest), flush=True)
