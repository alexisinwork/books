#!/usr/bin/env python3
"""Verify recorded file hashes in a directory; later author edits can change them."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def verify(root, manifest_path):
    root = Path(root).resolve()
    relative_manifest = Path(manifest_path)
    if relative_manifest.is_absolute():
        raise ValueError('Manifest path must be relative to the project root.')
    target = (root / relative_manifest).resolve()
    if not target.is_relative_to(root):
        raise ValueError('Manifest path escapes the project.')
    manifest = json.loads(target.read_text(encoding='utf-8'))
    errors, seen = [], set()
    for item in manifest['files']:
        rel = Path(item['path'])
        path = (root / rel).resolve()
        if rel.is_absolute() or not path.is_relative_to(root) or not path.is_file():
            errors.append(item['path'] + ': missing or invalid path')
        elif item['path'] in seen:
            errors.append(item['path'] + ': duplicate manifest path')
        elif hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            errors.append(item['path'] + ': changed')
        seen.add(item['path'])
    return {'checked': len(manifest['files']), 'errors': errors,
            'scope': 'Listed files only; successful hashes do not certify literary analysis.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--manifest', default='CHECKSUMS.json')
    args = parser.parse_args()
    try:
        result = verify(args.root, args.manifest)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return int(bool(result['errors']))
    except (ValueError, OSError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
