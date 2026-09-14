#!/usr/bin/env python3
"""Exact, single-occurrence replacements for the 2026-09-14 ensemble revision of Book 3.
Each edit is keyed by the ORIGINAL chapter number (file name before renumbering)."""
import json, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1]
LOG = R / 'work' / 'applied.json'

def apply(edits):
    log = json.loads(LOG.read_text()) if LOG.exists() else []
    done = {(e['ch'], e['old']) for e in log}
    for ch, old, new, why in edits:
        p = R / 'chapters' / f'{ch:02d}.md'
        t = p.read_text()
        if (ch, old) in done and old not in t:
            continue
        n = t.count(old)
        if n != 1:
            sys.exit(f'ch{ch}: expected 1 occurrence, found {n}: {old[:80]!r}')
        p.write_text(t.replace(old, new))
        log.append({'ch': ch, 'old': old, 'new': new, 'why': why})
    LOG.write_text(json.dumps(log, ensure_ascii=False, indent=1) + '\n')
    print('applied total', len(log))
