"""Queue behavior with deterministic clients; no paid models or manuscripts."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from tools import literary_clients as clients
from tools import literary_orchestrator as queue


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.campaign = self.root / 'queue'
        (self.root / 'prompt.md').write_text('Read the supplied packet and return the requested complete artifact.')
        (self.root / 'target.txt').write_text('Вона відчинила вікно.\nЗа вікном ішов дощ.\n', encoding='utf-8')
        self.calls = []

    def file(self, kind='target', path='target.txt', **extra):
        return {'kind': kind, 'label': kind.upper(), 'path': path,
                'sha256': queue.sha(self.root / path), **extra}

    def job(self, jid='astra', role='astra', **extra):
        client, model = {
            'astra': ('codex', 'gpt-6-astra'), 'writer': ('codex', 'gpt-5.6-sol'),
            'opus': ('claude', 'claude-opus-5'),
            'gemini_flash': ('agy', 'gemini-3.8-flash-high'),
            'gemini_pro': ('agy', 'gemini-3.1-pro-high'),
        }[role]
        return {'id': jid, 'role': role, 'client': client, 'model': model,
                'task_kind': 'draft' if role == 'writer' else 'review',
                'prompt': {'path': 'prompt.md', 'sha256': queue.sha(self.root / 'prompt.md')},
                'inputs': [self.file()], 'max_attempts': 3, **extra}

    def init(self, jobs, **extra):
        manifest = {'schema_version': 1, 'task_id': 'queue-test',
                    'authority': 'Authorized synthetic orchestration test', 'jobs': jobs, **extra}
        path = self.root / 'manifest.json'
        queue.atomic(path, manifest)
        queue.initialize(path, self.root, self.campaign)
        return manifest

    def fake(self, job, attempt, timeout):
        self.assertFalse(list(attempt.iterdir()), 'Client directory must be fresh and empty')
        self.calls.append(job['id'])
        response = ('Status: final\nTarget SHA-256: ' + str(job.get('expected_target_sha256'))
                    + '\nCoverage: both supplied lines. This synthetic fixture tests scheduling only. '
                    'It does not represent an actual literary assessment. All assertions concern the queue behavior.')
        (attempt / 'response.txt').write_text(response)
        (attempt / 'stdout.jsonl').write_text('{}\n')
        (attempt / 'stderr.txt').write_text('')
        result = {'status': 'response_received', 'requested_model': job['model'],
                  'observed_model': job['model'], 'observed_models': [job['model']],
                  'response_sha256': queue.sha(attempt / 'response.txt')}
        queue.atomic(attempt / 'receipt.json', result)
        return result

    def state(self):
        return queue.read(self.campaign / 'state.json')

    def assessment(self, jid, **extra):
        state = self.state()['jobs'][jid]
        value = {'checked_by': 'offline test fixture', 'notes': 'Synthetic assessment tests the gate, not literary quality.',
                 'response_sha256': state['response_sha256'], 'model_checked': True, 'model_status': 'matched',
                 'artifact_checked': True, 'target_sha256': state.get('expected_target_sha256'),
                 'full_coverage_checked': True, 'quotes_checked': True, 'independence_checked': True, **extra}
        path = self.root / (jid + '-assessment.json')
        queue.atomic(path, value)
        return path

    def accept(self, jid, **extra):
        return queue.accept(self.campaign, jid, self.assessment(jid, **extra))

    def review_graph(self):
        members = [self.job(role, role, review_set='unit-v1')
                   for role in ['astra', 'opus', 'gemini_flash', 'gemini_pro']]
        final = self.job('reconcile', task_kind='reconcile', review_set='unit-v1',
                         depends_on=[j['id'] for j in members], inputs=[self.file()] + [
                             {'kind': 'report', 'label': j['id'].upper(), 'from_job': j['id']} for j in members])
        return members + [final]

    def test_dependent_draft_waits_for_actual_coordinator_acceptance_and_resume_does_not_repeat(self):
        plan = self.job('plan', task_kind='plan')
        draft = self.job('draft', 'writer', depends_on=['plan'], inputs=[
            {'kind': 'plan', 'label': 'PLAN', 'from_job': 'plan'}, self.file()])
        self.init([plan, draft])
        result = queue.run(self.campaign, executor=self.fake)
        self.assertEqual('needs_coordinator_review', result['status'])
        self.assertEqual(['plan'], self.calls)
        with self.assertRaisesRegex(ValueError, 'exact pending'):
            self.accept('plan', response_sha256='0' * 64)
        self.accept('plan')
        queue.run(self.campaign, executor=self.fake)
        packet = (self.campaign / 'attempts/draft/001/packet.txt').read_text()
        self.assertIn(self.state()['jobs']['plan']['response_sha256'], packet)
        self.assertIn('Synthetic fixture'.lower(), packet.lower())
        self.accept('draft')
        self.assertEqual('complete', queue.run(self.campaign, executor=self.fake)['status'])
        self.assertEqual(['plan', 'draft'], self.calls)
        self.assertFalse(self.state()['author_canonical_approval'])

    def test_four_reviewers_run_parallel_and_reconciliation_receives_every_validated_report(self):
        self.init(self.review_graph())
        barrier = threading.Barrier(4)
        def parallel(job, attempt, timeout):
            if job['task_kind'] == 'review':
                barrier.wait(timeout=5)
            return self.fake(job, attempt, timeout)
        queue.run(self.campaign, executor=parallel)
        self.assertEqual({'astra', 'opus', 'gemini_flash', 'gemini_pro'}, set(self.calls))
        for role in ['astra', 'opus', 'gemini_flash']:
            self.accept(role)
        queue.run(self.campaign, executor=parallel)
        self.assertNotIn('reconcile', self.calls)
        self.accept('gemini_pro')
        queue.run(self.campaign, executor=parallel)
        self.assertEqual('reconcile', self.calls[-1])
        packet = queue.read(self.campaign / 'attempts/reconcile/001/packet.json')
        self.assertEqual(4, sum(item['kind'] == 'report' for item in packet['inputs']))

    def test_per_client_limit_serializes_two_codex_jobs(self):
        self.init([self.job('one'), self.job('two')])
        active = 0
        guard = threading.Lock()
        def limited(job, attempt, timeout):
            nonlocal active
            with guard:
                active += 1
                self.assertEqual(1, active)
            time.sleep(0.03)
            result = self.fake(job, attempt, timeout)
            with guard:
                active -= 1
            return result
        queue.run(self.campaign, executor=limited)
        self.assertEqual(['one', 'two'], self.calls)

    def test_final_quota_attempt_still_delays_same_client_and_allows_other_client(self):
        self.init([self.job('limited', max_attempts=1), self.job('later'), self.job('opus', 'opus')])
        def executor(job, attempt, timeout):
            if job['id'] == 'limited':
                self.calls.append(job['id'])
                result = {'status': 'failed', 'failure_kind': 'quota', 'retry_after_seconds': 60}
                queue.atomic(attempt / 'receipt.json', result)
                return result
            return self.fake(job, attempt, timeout)
        queue.run(self.campaign, executor=executor)
        self.assertEqual({'limited', 'opus'}, set(self.calls))
        self.assertEqual('failed', self.state()['jobs']['limited']['status'])
        self.assertEqual('pending', self.state()['jobs']['later']['status'])
        self.accept('opus')
        self.assertEqual('waiting_service', queue.status(self.campaign)['status'])
        self.assertGreater(queue.status(self.campaign)['next_retry_at'], time.time())

    def test_transient_retry_has_fresh_attempt_and_preserves_previous_evidence(self):
        self.init([self.job()])
        counter = 0
        def executor(job, attempt, timeout):
            nonlocal counter
            counter += 1
            if counter == 1:
                result = {'status': 'failed', 'failure_kind': 'transport', 'retry_after_seconds': 0}
                queue.atomic(attempt / 'receipt.json', result)
                return result
            return self.fake(job, attempt, timeout)
        queue.run(self.campaign, executor=executor)
        self.assertEqual(2, len(self.state()['jobs']['astra']['attempts']))
        self.assertEqual('failed', queue.read(self.campaign / 'attempts/astra/001/client/receipt.json')['status'])
        self.assertEqual('needs_review', self.state()['jobs']['astra']['status'])

    def test_reviews_require_exact_target_full_coverage_and_independence(self):
        self.init([self.job()])
        queue.run(self.campaign, executor=self.fake)
        for changes in [{'target_sha256': '0' * 64}, {'full_coverage_checked': False},
                        {'quotes_checked': False}, {'independence_checked': False}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.accept('astra', **changes)
        self.accept('astra')

    def test_unattested_backend_is_explicit_and_mixed_backend_cannot_hide_as_unattested(self):
        for observed in [[], ['gpt-6-astra', 'unexpected-backend']]:
            with self.subTest(observed=observed):
                self.campaign = self.root / ('queue-' + str(len(observed)))
                self.init([self.job()])
                def executor(job, attempt, timeout):
                    result = self.fake(job, attempt, timeout)
                    result.update(observed_model=None, observed_models=observed)
                    queue.atomic(attempt / 'receipt.json', result)
                    return result
                queue.run(self.campaign, executor=executor)
                if not observed:
                    with self.assertRaisesRegex(ValueError, 'unattested'):
                        self.accept('astra')
                    self.accept('astra', model_status='unattested')
                else:
                    with self.assertRaisesRegex(ValueError, 'Unexpected backend'):
                        self.accept('astra', model_status='unattested')

    def test_documented_exact_backend_alias_can_be_accepted(self):
        self.init([self.job(accepted_backend_ids=['gpt-6-astra-2026-09'],
                            model_alias_basis='Synthetic documented backend mapping for this test')])
        def executor(job, attempt, timeout):
            result = self.fake(job, attempt, timeout)
            result.update(observed_model='gpt-6-astra-2026-09', observed_models=['gpt-6-astra-2026-09'])
            queue.atomic(attempt / 'receipt.json', result)
            return result
        queue.run(self.campaign, executor=executor)
        self.accept('astra', model_status='documented_alias')

    def test_changed_frozen_or_live_target_is_stale_and_blocks_dependent_work(self):
        self.init([self.job('plan', task_kind='plan'), self.job('draft', 'writer', depends_on=['plan'])])
        queue.run(self.campaign, executor=self.fake)
        self.accept('plan')
        (self.root / 'target.txt').write_text('Changed source')
        states = queue.status(self.campaign)['jobs']
        self.assertEqual({'plan': 'stale', 'draft': 'stale'}, states)
        queue.run(self.campaign, executor=self.fake)
        self.assertEqual(['plan'], self.calls)

    def test_explicit_frozen_input_survives_origin_change(self):
        self.init([self.job(inputs=[self.file(watch_origin=False)])])
        (self.root / 'target.txt').write_text('Different current version')
        queue.run(self.campaign, executor=self.fake)
        self.assertEqual('needs_review', self.state()['jobs']['astra']['status'])

    def test_response_receipt_packet_stdout_and_validation_mutation_invalidate_complete_status(self):
        for rel in ['client/response.txt', 'client/receipt.json', 'packet.txt', 'packet.json',
                    'client/stdout.jsonl', 'coordinator-validation.json']:
            with self.subTest(rel=rel):
                self.campaign = self.root / ('queue-' + rel.replace('/', '-').replace('.', '-'))
                self.init([self.job()])
                queue.run(self.campaign, executor=self.fake)
                self.accept('astra')
                path = self.campaign / 'attempts/astra/001' / rel
                path.write_bytes(path.read_bytes() + b'\n')
                self.assertEqual('stale', queue.status(self.campaign)['jobs']['astra'])
                self.assertNotEqual('complete', queue.status(self.campaign)['status'])

    def test_packet_changed_during_client_call_cannot_be_legitimized_at_completion(self):
        self.init([self.job()])
        def executor(job, attempt, timeout):
            (attempt.parent / 'packet.txt').write_text('Tampered after dispatch')
            return self.fake(job, attempt, timeout)
        queue.run(self.campaign, executor=executor)
        self.assertEqual('stale', queue.status(self.campaign)['jobs']['astra'])

    def test_acceptance_resumes_validation_state_crash_window_without_rewriting(self):
        self.init([self.job()])
        queue.run(self.campaign, executor=self.fake)
        pending = self.state()
        assessment = self.assessment('astra')
        queue.accept(self.campaign, 'astra', assessment)
        validation = self.campaign / 'attempts/astra/001/coordinator-validation.json'
        original = validation.read_bytes()
        queue.atomic(self.campaign / 'state.json', pending)
        queue.accept(self.campaign, 'astra', assessment)
        self.assertEqual(original, validation.read_bytes())
        self.assertEqual('complete', queue.status(self.campaign)['status'])

    def test_unknown_running_attempt_never_auto_duplicates_and_needs_explicit_process_check(self):
        self.init([self.job()])
        state = self.state()
        state['jobs']['astra'].update(status='running', attempts=[{'path': 'attempts/astra/001', 'status': 'running'}])
        (self.campaign / 'attempts/astra/001').mkdir(parents=True)
        queue.atomic(self.campaign / 'state.json', state)
        queue.run(self.campaign, executor=self.fake)
        self.assertEqual([], self.calls)
        self.assertEqual('needs_recovery', self.state()['jobs']['astra']['status'])
        with self.assertRaisesRegex(ValueError, 'process_checked'):
            queue.retry(self.campaign, 'astra', 'Inspected interrupted fixture attempt')
        queue.retry(self.campaign, 'astra', 'Inspected empty attempt: no client was launched', process_checked=True)
        queue.run(self.campaign, executor=self.fake)
        self.assertEqual(['astra'], self.calls)
        self.assertTrue((self.campaign / 'attempts/astra/002/client/receipt.json').is_file())

    def test_completed_orphan_receipt_is_adopted_without_another_model_call(self):
        self.init([self.job()])
        queue.run(self.campaign, executor=self.fake)
        state = self.state()
        state['jobs']['astra']['status'] = 'running'
        queue.atomic(self.campaign / 'state.json', state)
        queue.run(self.campaign, executor=self.fake)
        self.assertEqual(['astra'], self.calls)
        self.assertEqual('needs_review', self.state()['jobs']['astra']['status'])

    def test_attempt_budget_and_unknown_exception_prevent_unbounded_duplicate_launches(self):
        self.init([self.job(max_attempts=1)])
        def executor(*args):
            raise RuntimeError('Child state is unknown')
        queue.run(self.campaign, executor=executor)
        self.assertEqual('needs_recovery', self.state()['jobs']['astra']['status'])
        with self.assertRaisesRegex(ValueError, 'budget exhausted'):
            queue.retry(self.campaign, 'astra', 'Explicit inspection of the unknown child', process_checked=True)

    def test_second_coordinator_is_rejected_by_process_lock(self):
        self.init([self.job()])
        with queue.locked(self.campaign):
            with self.assertRaisesRegex(ValueError, 'Another coordinator'):
                queue.run(self.campaign, executor=self.fake)

    def test_changed_runtime_is_rejected_and_frozen_runtime_cli_can_resume(self):
        self.init([self.job()])
        script = self.campaign / 'runtime/literary_orchestrator.py'
        result = subprocess.run([sys.executable, str(script), 'status', '--queue', str(self.campaign)],
                                capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('ready', json.loads(result.stdout)['status'])
        script.write_text(script.read_text() + '\n# altered\n')
        with self.assertRaisesRegex(ValueError, 'Runtime changed'):
            queue.run(self.campaign, executor=self.fake)

    def test_real_client_adapter_contract_with_temporary_subprocess(self):
        self.init([self.job('opus', 'opus')])
        response = ('Status: final\nTarget SHA-256: ' + queue.sha(self.root / 'target.txt') +
                    '\nCoverage: two supplied lines were read. This is an offline transport test. '
                    'No live model was involved, and the test makes no assertion about language quality. '
                    'The entire response is returned in the final client envelope.')
        fake = self.root / 'fake_client.py'
        fake.write_text('import sys, json\nassert sys.stdin.read()\nprint(json.dumps(' +
                        repr({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': response,
                              'modelUsage': {'claude-opus-5': {'inputTokens': 1}}}) + '))\n')
        with mock.patch.object(clients, '_command', return_value=[sys.executable, str(fake)]):
            result = queue.run(self.campaign)
        self.assertEqual('needs_coordinator_review', result['status'])
        self.accept('opus')
        self.assertEqual('complete', queue.status(self.campaign)['status'])

    def test_manifest_rejects_architecture_bypass_and_missing_reconciliation_artifacts(self):
        valid = {'schema_version': 1, 'task_id': 'manifest-test', 'authority': 'Authorized synthetic test',
                 'jobs': self.review_graph()}
        mutations = [
            lambda m: m['jobs'][2].update(client='codex'),
            lambda m: m['jobs'][1].update(client='agy'),
            lambda m: m['jobs'][0].update(model='gpt-5.6-sol'),
            lambda m: m['jobs'][3]['inputs'].append(self.file('source')),
            lambda m: m['jobs'][0]['inputs'].append(self.file('report')),
            lambda m: m['jobs'][0].update(depends_on=['reconcile']),
            lambda m: m['jobs'].pop(0),
            lambda m: m['jobs'][-1]['inputs'].pop(),
            lambda m: m['jobs'][0].update(accepted_backend_ids='gpt-6-astra'),
            lambda m: m['jobs'][0].update(accepted_backend_ids=['alias'], model_alias_basis=''),
            lambda m: m['jobs'][0].update(max_attempts=3.5),
            lambda m: m.update(max_parallel=True),
        ]
        queue.validate_manifest(valid)
        for change in mutations:
            candidate = deepcopy(valid)
            change(candidate)
            with self.subTest(manifest=candidate), self.assertRaises(ValueError):
                queue.validate_manifest(candidate)

    def test_review_set_rejects_different_target_hashes(self):
        (self.root / 'other.txt').write_text('Інший текст.\n', encoding='utf-8')
        jobs = self.review_graph()
        jobs[1]['inputs'] = [self.file(path='other.txt')]
        self.init(jobs)
        queue.run(self.campaign, executor=self.fake)
        self.assertEqual('stale', self.state()['jobs']['opus']['status'])
        self.assertNotIn('opus', self.calls)

    def test_opus_adapter_needs_explicit_self_review_and_independent_bilingual_sol(self):
        graph = self.review_graph()
        producer = {**self.job('adapter', 'writer'), 'role': 'primary_adapter', 'client': 'claude', 'model': 'claude-opus-5',
                    'selection_basis': 'Author selected Opus in the synthetic fixture'}
        for job in graph[:-1]:
            job['depends_on'] = ['adapter']
            job['inputs'] = [{'kind': 'target', 'label': 'TARGET', 'from_job': 'adapter'}]
        manifest = {'schema_version': 1, 'task_id': 'opus-adapter', 'authority': 'Authorized synthetic fixture',
                    'jobs': [producer, *graph]}
        with self.assertRaisesRegex(ValueError, 'self_review'):
            queue.validate_manifest(manifest)
        graph[1]['review_relationship'] = 'self_review'
        with self.assertRaisesRegex(ValueError, 'bilingual Sol'):
            queue.validate_manifest(manifest)
        bilingual = self.job('bilingual', 'writer', task_kind='review', review_set='unit-v1',
                             depends_on=['adapter'], inputs=[{'kind': 'target', 'label': 'TARGET', 'from_job': 'adapter'},
                                                            self.file('source')])
        bilingual['role'] = 'bilingual'
        manifest['jobs'].append(bilingual)
        graph[-1]['depends_on'].append('bilingual')
        graph[-1]['inputs'].append({'kind': 'report', 'label': 'BILINGUAL', 'from_job': 'bilingual'})
        queue.validate_manifest(manifest)
        bilingual['inputs'].pop()
        with self.assertRaisesRegex(ValueError, 'relevant source'):
            queue.validate_manifest(manifest)

    def test_self_review_assessment_cannot_claim_independence(self):
        self.init([self.job('opus', 'opus', target_producer_model='claude-opus-5', review_relationship='self_review')])
        queue.run(self.campaign, executor=self.fake)
        with self.assertRaisesRegex(ValueError, 'self-review'):
            self.accept('opus')
        self.accept('opus', review_relationship='self_review')


if __name__ == '__main__':
    unittest.main()
