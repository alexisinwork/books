#!/usr/bin/env python3
"""Verify archived synthetic-run evidence without contacting models or live origins."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def at(base, relative):
    path = (base / relative).resolve()
    assert path.is_relative_to(base.resolve()), relative
    return path


def check(name):
    campaign = BASE / name
    state = read(campaign / 'state.json')
    manifest = read(campaign / 'manifest.json')
    assert digest(campaign / 'manifest.json') == state['manifest_sha256']
    count = 1
    for file, expected in state['runtime_sha256'].items():
        assert digest(campaign / 'runtime' / file) == expected
        count += 1
    for job in manifest['jobs']:
        for item in [job['prompt'], *job['inputs']]:
            if 'from_job' not in item:
                assert digest(at(campaign, item['snapshot'])) == item['sha256']
                count += 1
        current = state['jobs'][job['id']]
        for attempt in current['attempts']:
            for item in attempt.get('artifacts', []):
                assert digest(at(campaign, item['path'])) == item['sha256'], item['path']
                count += 1
        if current['status'] in {'accepted', 'needs_review'}:
            assert digest(at(campaign, current['response_path'])) == current['response_sha256']
        if current['status'] == 'accepted':
            path = at(campaign, current['validation_path'])
            assert digest(path) == current['validation_sha256']
            assessment = read(path)
            assert assessment['response_sha256'] == current['response_sha256']
            assert assessment['author_canonical_approval'] is False
            count += 1
    assert state['author_canonical_approval'] is False
    return campaign, state, count


def instant(value):
    return datetime.fromisoformat(value)


def receipt(campaign, state, role):
    attempt = state['jobs'][role]['attempts'][-1]
    return read(at(campaign, attempt['path']) / 'client/receipt.json')


def main():
    first, r1, n1 = check('smoke-r1')
    second, r2, n2 = check('smoke-r2')
    assert r1['jobs']['opus']['status'] == 'needs_review'
    assert r1['jobs']['reconcile']['status'] == 'pending'
    assert read(BASE / 'r1-disposition.json')['opus_coordinator_accepted'] is False
    assert all(job['status'] == 'accepted' for job in r2['jobs'].values())
    plan, draft = receipt(first, r1, 'plan'), receipt(first, r1, 'draft')
    assert instant(plan['finished_at']) <= instant(draft['started_at'])
    roles = ['astra', 'opus', 'gemini_flash', 'gemini_pro']
    reviews = [receipt(second, r2, role) for role in roles]
    assert max(instant(r['started_at']) for r in reviews) < min(instant(r['finished_at']) for r in reviews)
    target = digest(first / r1['jobs']['draft']['response_path'])
    assert all(r['expected_target_sha256'] == target for r in reviews)
    opus = receipt(second, r2, 'opus')
    assert opus['model_evidence'] == 'assistant_message'
    assert opus['observed_models'] == ['claude-opus-5']
    assert opus['assistant_response_matches_result'] is True
    for role in ['gemini_flash', 'gemini_pro']:
        r = receipt(second, r2, role)
        assert r['model_attested'] is True and r['client'] == 'agy'
    for r in [plan, draft, *reviews, receipt(second, r2, 'reconcile')]:
        assert r['status'] == 'response_received'
        assert r['observed_tool_events'] == []
    reconciliation = receipt(second, r2, 'reconcile')
    # Client timestamps are truncated to seconds; dispatcher reservations retain
    # microseconds and follow all accepted dependency state writes.
    reconcile_reserved_at = r2['jobs']['reconcile']['attempts'][-1]['started_at']
    for role in roles:
        assessment = read(at(second, r2['jobs'][role]['validation_path']))
        assert instant(assessment['validated_at']) <= instant(reconcile_reserved_at)
    print(json.dumps({'status': 'pass', 'archived_hash_checks': n1 + n2,
                      'r1': 'retained incomplete, mixed Claude aggregate identity',
                      'r2': 'all four reviews and reconciliation coordinator-validated',
                      'target_sha256': target,
                      'live_origin_checks': 'not performed: portable archive verification',
                      'literary_quality_certification': False}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
