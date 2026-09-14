"""Offline contract tests: all model clients are mocked or temporary executables."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

from tools import literary_clients as clients


TARGET = "a" * 64
REPORT = (
    "Status: final\nTarget SHA-256: " + TARGET + "\n\n"
    "Coverage: supplied paragraphs 1–3. The reported examination is complete. "
    "No additional mandatory correction is proposed. This fixture is a transport "
    "test, not evidence of a literary review or an actual model's language quality."
)


class FakeProcess:
    pid = 42424242

    def __init__(self, stdout, stderr="", code=0, on_communicate=None):
        self.stdout = stdout.encode() if isinstance(stdout, str) else stdout
        self.stderr = stderr.encode() if isinstance(stderr, str) else stderr
        self.code = code
        self.returncode = None
        self.inputs = []
        self.on_communicate = on_communicate

    def communicate(self, input=None, timeout=None):
        self.inputs.append(input)
        if self.on_communicate:
            self.on_communicate(self, input, timeout)
        self.returncode = self.code
        return self.stdout, self.stderr

    def poll(self):
        return self.returncode


class LiteraryClientTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.attempt = Path(self.temporary.name) / "attempt"
        self.attempt.mkdir()

    def job(self, **overrides):
        data = {
            "id": "chapter-01-opus", "role": "opus", "client": "claude",
            "model": "claude-opus-5", "effort": "high", "task_kind": "review",
            "prompt": "Review the embedded Ukrainian text: «Доброго ранку». " + TARGET,
            "expected_target_sha256": TARGET,
        }
        data.update(overrides)
        return data

    def result(self, response=REPORT, **overrides):
        data = {"type": "result", "subtype": "success", "is_error": False,
                "result": response, "modelUsage": {"claude-opus-5": {"inputTokens": 20}}}
        data.update(overrides)
        return json.dumps(data, ensure_ascii=False)

    def agy_result(self, response=REPORT, **overrides):
        result = {"status": "SUCCESS", "response": response}
        result.update(overrides)
        return json.dumps({"event": "result", "result": result}, ensure_ascii=False) + "\n"

    def assistant_event(self, text=REPORT, model="claude-opus-5", **overrides):
        message = {"role": "assistant", "model": model, "content": [{"type": "text", "text": text}]}
        message.update(overrides)
        return json.dumps({"type": "assistant", "message": message}, ensure_ascii=False)

    def claude_stream(self, assistant=None, result=None):
        return "\n".join([
            json.dumps({"type": "system", "subtype": "init", "model": "requested-selector-echo"}),
            assistant if assistant is not None else self.assistant_event(),
            result if result is not None else self.result(),
        ]) + "\n"

    def run_fake(self, job=None, stdout=None, stderr="", code=0, prepare=None, on_communicate=None):
        process = FakeProcess(stdout if stdout is not None else self.result(), stderr, code, on_communicate)
        observed = {}

        def spawn(command, **kwargs):
            observed.update(command=command, kwargs=kwargs)
            self.assertTrue(kwargs["start_new_session"])
            self.assertEqual(subprocess.PIPE, kwargs["stdin"])
            self.assertEqual(subprocess.PIPE, kwargs["stdout"])
            self.assertNotEqual(Path(kwargs["cwd"]).resolve(), Path.cwd())
            self.assertFalse(list(Path(kwargs["cwd"]).iterdir()))
            if prepare:
                prepare(command)
            return process

        with mock.patch.object(clients.subprocess, "Popen", side_effect=spawn):
            receipt = clients.execute(job or self.job(), self.attempt, 10)
        self.assertEqual(receipt, json.loads((self.attempt / "receipt.json").read_text()))
        self.assertFalse(Path(observed["kwargs"]["cwd"]).exists())
        return receipt, observed, process

    def test_claude_success_is_pending_coordinator_validation_and_uses_stdin(self):
        def check_running(process, stdin, timeout):
            current = json.loads((self.attempt / "receipt.json").read_text())
            self.assertEqual("running", current["status"])
            self.assertEqual(process.pid, current["pid"])
            self.assertEqual(process.pid, current["pgid"])
            self.assertIn("process_start_ticks", current)
            self.assertLessEqual(timeout, clients.POLL_SECONDS)

        receipt, observed, process = self.run_fake(on_communicate=check_running)
        command = observed["command"]
        self.assertEqual("response_received", receipt["status"])
        self.assertEqual("pending", receipt["coordinator_validation"])
        self.assertEqual("not_assessed", receipt["coverage_validation"])
        self.assertEqual("not_assessed", receipt["literary_quality_validation"])
        self.assertIsNone(receipt["failure_kind"])
        self.assertTrue(receipt["model_attested"])
        self.assertEqual("claude-opus-5", receipt["observed_model"])
        self.assertEqual(REPORT, (self.attempt / "response.txt").read_text())
        self.assertEqual(hashlib.sha256(REPORT.encode()).hexdigest(), receipt["response_sha256"])
        for flag in ("--safe-mode", "--strict-mcp-config", "--no-session-persistence"):
            self.assertIn(flag, command)
        self.assertEqual("", command[command.index("--tools") + 1])
        self.assertEqual('{"mcpServers":{}}', command[command.index("--mcp-config") + 1])
        self.assertEqual("none", command[command.index("--permission-prompts") + 1])
        self.assertEqual("stream-json", command[command.index("--output-format") + 1])
        self.assertIn("--verbose", command)
        self.assertNotIn(self.job()["prompt"], command)
        self.assertIn(self.job()["prompt"].encode(), process.inputs[0])
        self.assertNotIn("--fallback-model", command)

    def test_codex_uses_fixed_explicit_flags_and_last_message_file(self):
        stdout = "\n".join(json.dumps(e) for e in [
            {"type": "thread.started", "thread_id": "fictional-test-thread"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": REPORT}},
            {"type": "turn.completed", "usage": {"input_tokens": 50}},
        ])

        def prepare(command):
            target = Path(command[command.index("--output-last-message") + 1])
            self.assertTrue(target.is_absolute())
            self.assertEqual(self.attempt / "response.txt", target)
            target.write_text(REPORT)

        receipt, observed, process = self.run_fake(
            self.job(client="codex", role="astra", model="gpt-6-astra"), stdout, prepare=prepare)
        command = observed["command"]
        self.assertEqual(["codex", "exec"], command[:2])
        self.assertEqual("-", command[-1])
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ephemeral", command)
        self.assertIn('approval_policy="never"', command)
        self.assertIn("project_doc_max_bytes=0", command)
        self.assertIn("features.multi_agent=false", command)
        self.assertIn("mcp_servers={}", command)
        self.assertIn("features.skip_host_skill_discovery=true", command)
        self.assertEqual("read-only", command[command.index("--sandbox") + 1])
        self.assertEqual("gpt-6-astra", command[command.index("--model") + 1])
        self.assertEqual("response_received", receipt["status"])
        self.assertFalse(receipt["model_attested"])
        self.assertIsNone(receipt["observed_model"])
        self.assertIn(b"Status: final", process.inputs[0])

    def test_codex_cannot_use_commentary_as_missing_last_message(self):
        stdout = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": REPORT}}) + "\n"
        stdout += json.dumps({"type": "turn.completed"})
        receipt, _, _ = self.run_fake(self.job(client="codex", role="sol", model="gpt-5.6-sol"), stdout)
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertEqual("", (self.attempt / "response.txt").read_text())

    def test_codex_error_even_with_final_file_is_not_success(self):
        stdout = json.dumps({"type": "error", "message": "Usage limit reached. Try again in 2 minutes."})

        def prepare(command):
            Path(command[command.index("--output-last-message") + 1]).write_text(REPORT)

        receipt, _, _ = self.run_fake(self.job(client="codex", role="sol", model="gpt-5.6-sol"), stdout, prepare=prepare)
        self.assertEqual("quota", receipt["failure_kind"])
        self.assertEqual(120, receipt["retry_after_seconds"])
        self.assertEqual("failed", receipt["status"])

    def test_agy_one_embedded_event_no_file_mode_and_backend_log_attestation(self):
        job = self.job(role="gemini_pro", client="agy", model="gemini-3.1-pro-high")

        def prepare(command):
            Path(command[command.index("--log-file") + 1]).write_text(
                'INFO Print mode: starting conversation model="GEMINI_3_1_PRO_HIGH"\n')

        receipt, observed, process = self.run_fake(job, self.agy_result(), prepare=prepare)
        command = observed["command"]
        self.assertEqual("agy", command[0])
        self.assertIn("--new-project", command)
        self.assertIn("--sandbox", command)
        self.assertEqual("plan", command[command.index("--mode") + 1])
        self.assertNotIn("--dangerously-skip-permissions", command)
        self.assertNotIn("--print", command)
        stdin = process.inputs[0].decode()
        self.assertEqual(1, len(stdin.splitlines()))
        event = json.loads(stdin)
        self.assertEqual("user", event["event"])
        self.assertIn(job["prompt"], event["message"]["content"][0]["text"])
        self.assertEqual("response_received", receipt["status"])
        self.assertEqual("GEMINI_3_1_PRO_HIGH", receipt["observed_model"])
        self.assertTrue(receipt["model_attested"])

    def test_agy_init_echo_and_model_self_report_are_not_attestation(self):
        report = REPORT + "\nI am gpt-6-astra."
        stdout = json.dumps({"event": "init", "init": {"model": "gemini-3.1-pro-high"}}) + "\n" + self.agy_result(report)
        receipt, _, _ = self.run_fake(self.job(role="gemini_pro", client="agy", model="gemini-3.1-pro-high"), stdout)
        self.assertFalse(receipt["model_attested"])
        self.assertIsNone(receipt["observed_model"])

    def test_agy_success_string_without_result_envelope_is_not_a_result(self):
        receipt, _, _ = self.run_fake(self.job(role="gemini_flash", client="agy", model="gemini-3.8-flash-high"),
                                     json.dumps({"status": "SUCCESS", "response": REPORT}))
        self.assertEqual("invalid_response", receipt["failure_kind"])

    def test_missing_claude_success_indicator_is_invalid(self):
        receipt, _, _ = self.run_fake(stdout=json.dumps({"result": REPORT}))
        self.assertEqual("invalid_response", receipt["failure_kind"])

    def test_multiple_usage_models_do_not_attest_one_backend(self):
        receipt, _, _ = self.run_fake(stdout=self.result(modelUsage={"model-a": {}, "model-b": {}}))
        self.assertFalse(receipt["model_attested"])
        self.assertEqual(["model-a", "model-b"], receipt["observed_models"])
        self.assertIsNone(receipt["observed_model"])
        self.assertEqual(["model-a", "model-b"], receipt["usage_models"])
        self.assertEqual([], receipt["auxiliary_models"])
        self.assertEqual("model_usage", receipt["model_evidence"])

    def test_claude_complete_assistant_attests_opus_despite_auxiliary_haiku_usage(self):
        usage = {"claude-haiku-4-5-20251001": {"outputTokens": 20}, "claude-opus-5": {"outputTokens": 1188}}
        stdout = self.claude_stream(result=self.result(modelUsage=usage))
        receipt, _, _ = self.run_fake(stdout=stdout)
        self.assertEqual("response_received", receipt["status"])
        self.assertEqual(["claude-opus-5"], receipt["observed_models"])
        self.assertEqual("claude-opus-5", receipt["observed_model"])
        self.assertTrue(receipt["model_attested"])
        self.assertTrue(receipt["assistant_response_matches_result"])
        self.assertEqual("assistant_message", receipt["model_evidence"])
        self.assertEqual(sorted(usage), receipt["usage_models"])
        self.assertEqual(["claude-haiku-4-5-20251001"], receipt["auxiliary_models"])

    def test_claude_different_complete_assistant_models_remain_blocking(self):
        assistants = self.assistant_event("An earlier assistant answer.", "claude-haiku-4-5-20251001") + "\n" + self.assistant_event()
        receipt, _, _ = self.run_fake(stdout=self.claude_stream(assistant=assistants))
        self.assertEqual("failed", receipt["status"])
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertEqual(["claude-haiku-4-5-20251001", "claude-opus-5"], receipt["observed_models"])
        self.assertFalse(receipt["model_attested"])
        self.assertIsNone(receipt["observed_model"])
        self.assertEqual(REPORT, (self.attempt / "response.txt").read_text())

    def test_claude_final_result_must_equal_last_complete_assistant_text(self):
        receipt, _, _ = self.run_fake(stdout=self.claude_stream(assistant=self.assistant_event(REPORT + " extra")))
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertFalse(receipt["assistant_response_matches_result"])
        self.assertFalse(receipt["model_attested"])
        self.assertEqual("unbound_assistant_metadata", receipt["model_evidence"])
        self.assertEqual(REPORT, (self.attempt / "response.txt").read_text())

    def test_claude_missing_assistant_model_keeps_conservative_usage_list(self):
        usage = {"claude-opus-5": {"outputTokens": 1188}, "claude-haiku-4-5-20251001": {"outputTokens": 20}}
        stdout = self.claude_stream(assistant=self.assistant_event(model=None), result=self.result(modelUsage=usage))
        receipt, _, _ = self.run_fake(stdout=stdout)
        self.assertEqual("response_received", receipt["status"])
        self.assertTrue(receipt["assistant_response_matches_result"])
        self.assertFalse(receipt["model_attested"])
        self.assertEqual(sorted(usage), receipt["observed_models"])
        self.assertEqual([], receipt["auxiliary_models"])
        self.assertEqual("model_usage", receipt["model_evidence"])

    def test_claude_complete_text_blocks_preserve_content_and_ignore_thinking(self):
        content = [{"type": "thinking", "thinking": "Do not attest identity from this text."},
                   {"type": "text", "text": REPORT[:80]}, {"type": "text", "text": REPORT[80:]}]
        receipt, _, _ = self.run_fake(stdout=self.claude_stream(assistant=self.assistant_event(content=content)))
        self.assertEqual("response_received", receipt["status"])
        self.assertTrue(receipt["assistant_response_matches_result"])
        self.assertEqual("assistant_message", receipt["model_evidence"])

    def test_claude_complete_assistant_without_terminal_result_is_invalid(self):
        receipt, _, _ = self.run_fake(stdout=self.assistant_event())
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertFalse(receipt["model_attested"])

    def test_claude_terminal_result_cannot_precede_its_assistant(self):
        stdout = self.result() + "\n" + self.assistant_event()
        receipt, _, _ = self.run_fake(stdout=stdout)
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertFalse(receipt["model_attested"])

    def test_claude_token_events_do_not_attest_a_complete_assistant_response(self):
        event = {"type": "stream_event", "event": {"type": "message_start", "message": {"model": "claude-opus-5"}}}
        usage = {"claude-opus-5": {}, "claude-haiku-4-5-20251001": {}}
        receipt, _, _ = self.run_fake(stdout=json.dumps(event) + "\n" + self.result(modelUsage=usage))
        self.assertFalse(receipt["model_attested"])
        self.assertEqual(sorted(usage), receipt["observed_models"])
        self.assertEqual("model_usage", receipt["model_evidence"])

    def test_exact_review_header_required_not_hash_merely_mentioned(self):
        response = "Status: final\n" + "A quote mentions " + TARGET + ". " + "A detailed test sentence. " * 20
        receipt, _, _ = self.run_fake(stdout=self.result(response))
        self.assertEqual("invalid_response", receipt["failure_kind"])

    def test_conflicting_target_headers_are_not_accepted(self):
        receipt, _, _ = self.run_fake(stdout=self.result(REPORT + "\nTarget SHA-256: " + "b" * 64))
        self.assertEqual("invalid_response", receipt["failure_kind"])

    def test_empty_short_wrong_hash_and_plan_are_not_finished_reviews(self):
        responses = ["", "Done", REPORT.replace(TARGET, "b" * 64), REPORT.replace("Status: final", "Status: plan"),
                     "Status: final\nTarget SHA-256: " + TARGET, "I will review the whole chapter. " * 20]
        for index, response in enumerate(responses):
            with self.subTest(response=index):
                attempt = self.attempt / str(index)
                attempt.mkdir()
                with mock.patch.object(clients.subprocess, "Popen", return_value=FakeProcess(self.result(response))):
                    receipt = clients.execute(self.job(), attempt, 5)
                self.assertEqual("failed", receipt["status"])
                self.assertEqual("invalid_response", receipt["failure_kind"])

    def test_plan_task_can_return_a_plan_without_review_header(self):
        job = self.job(task_kind="plan", expected_target_sha256=None)
        receipt, _, _ = self.run_fake(job, self.result("I will use the following chapter architecture.\nScene one establishes the debt; scene two reveals its cost."))
        self.assertEqual("response_received", receipt["status"])

    def test_completed_working_draft_can_call_itself_a_draft(self):
        receipt, _, _ = self.run_fake(self.job(task_kind="draft", expected_target_sha256=None),
                                     self.result("Status: draft\n\nВін підвів голову. Біля дверей стояла мати. — Ти повернувся?"))
        self.assertEqual("response_received", receipt["status"])

    def test_tool_use_in_successful_agy_report_invalidates_independence(self):
        event = {"event": "step_update", "step_update": {"step_type": "CORTEX_STEP_TYPE_READ_FILE", "path": "/private/unrelated"}}
        stdout = json.dumps(event) + "\n" + self.agy_result()
        receipt, _, _ = self.run_fake(self.job(role="gemini_flash", client="agy", model="gemini-3.8-flash-high"), stdout)
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertEqual(["step:CORTEX_STEP_TYPE_READ_FILE"], receipt["observed_tool_events"])
        self.assertNotIn("/private/unrelated", json.dumps(receipt))

    def test_permission_denial_is_a_prohibited_attempt_not_success(self):
        receipt, _, _ = self.run_fake(stdout=self.result(permission_denials=[{"tool_name": "Read", "input": "omitted"}]))
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertEqual(["permission_denials"], receipt["observed_tool_events"])

    def test_codex_tool_event_is_rejected_even_with_final_response(self):
        stdout = json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "do not print"}})
        stdout += "\n" + json.dumps({"type": "turn.completed"})
        def prepare(command):
            Path(command[command.index("--output-last-message") + 1]).write_text(REPORT)
        receipt, _, _ = self.run_fake(self.job(client="codex", role="sol", model="gpt-5.6-sol"), stdout, prepare=prepare)
        self.assertEqual("invalid_response", receipt["failure_kind"])
        self.assertEqual(["command_execution"], receipt["observed_tool_events"])

    def test_quota_despite_exit_zero_uses_explicit_machine_retry(self):
        stdout = self.result("Session limit exceeded", is_error=True, subtype="error_during_execution", retry_after_seconds=17)
        receipt, _, _ = self.run_fake(stdout=stdout)
        self.assertEqual("quota", receipt["failure_kind"])
        self.assertEqual(17, receipt["retry_after_seconds"])

    def test_explicit_stderr_quota_is_not_hidden_by_success_envelope(self):
        receipt, _, _ = self.run_fake(stderr="API Error: 429, quota exceeded. Retry-After: 45")
        self.assertEqual("quota", receipt["failure_kind"])
        self.assertEqual(45, receipt["retry_after_seconds"])

    def test_logger_warning_does_not_retry_a_completed_response(self):
        warning = "WARNING: error reporting is disabled; quota monitoring is unavailable."
        receipt, _, _ = self.run_fake(stderr=warning)
        self.assertEqual("response_received", receipt["status"])
        self.assertIsNone(receipt["failure_kind"])
        self.assertEqual(REPORT, (self.attempt / "response.txt").read_text())
        self.assertEqual(warning, (self.attempt / "stderr.txt").read_text())
        self.assertTrue(receipt["stderr_warnings"])

    def test_codex_logger_error_does_not_discard_completed_last_message(self):
        def prepare(command):
            Path(command[command.index("--output-last-message") + 1]).write_text(REPORT)
        receipt, _, _ = self.run_fake(
            self.job(client="codex", role="astra", model="gpt-6-astra"),
            json.dumps({"type": "turn.completed"}),
            stderr="ERROR codex_core::logging: telemetry destination is closed", prepare=prepare,
        )
        self.assertEqual("response_received", receipt["status"])
        self.assertTrue(receipt["stderr_warnings"])

    def test_explicit_stderr_auth_failure_is_not_a_logger_warning(self):
        receipt, _, _ = self.run_fake(stderr="API Error: 401 unauthorized")
        self.assertEqual("unavailable", receipt["failure_kind"])

    def test_plain_stdout_error_before_json_protocol_is_classified(self):
        receipt, _, _ = self.run_fake(stdout="You've hit your limit; try again in 3 minutes.", code=1)
        self.assertEqual("quota", receipt["failure_kind"])
        self.assertEqual(180, receipt["retry_after_seconds"])

    def test_agy_non_success_is_failure_and_unknown_reset_stays_unknown(self):
        receipt, _, _ = self.run_fake(self.job(role="gemini_flash", client="agy", model="gemini-3.8-flash-high"),
                                     self.agy_result("Quota exceeded. Resets at 21:10 UTC.", status="ERROR"))
        self.assertEqual("quota", receipt["failure_kind"])
        self.assertIsNone(receipt["retry_after_seconds"])

    def test_duration_parser_and_retry_header_do_not_guess(self):
        self.assertEqual(3723, clients._retry_delay([], "Quota exceeded, try again in 1 hour 2 minutes 3 seconds."))
        self.assertEqual(30, clients._retry_delay([], "Retry-After: 30"))
        self.assertEqual(1.25, clients._retry_delay([{"error": {"retry_after_ms": 1250}}], ""))
        self.assertEqual(4.5, clients._retry_delay([{"details": [{"retryDelay": "4.5s"}]}], ""))
        self.assertIsNone(clients._retry_delay([], "Try later; current session has used 30 minutes."))
        self.assertIsNone(clients._retry_delay([{"retry_after_seconds": True}], ""))

    def test_missing_binary_is_recorded_without_fallback(self):
        with mock.patch.object(clients.subprocess, "Popen", side_effect=FileNotFoundError) as call:
            receipt = clients.execute(self.job(), self.attempt, 5)
        call.assert_called_once()
        self.assertEqual("unavailable", receipt["failure_kind"])
        self.assertEqual("claude-opus-5", receipt["requested_model"])
        self.assertEqual("", (self.attempt / "response.txt").read_text())

    def test_unavailable_model_error_and_transport_exit_are_separate(self):
        receipt, _, _ = self.run_fake(stderr="The requested model is unavailable", code=1)
        self.assertEqual("unavailable", receipt["failure_kind"])

    def test_malformed_json_is_not_a_success(self):
        receipt, _, _ = self.run_fake(stdout="Status: final\nA plain response is not the client envelope.")
        self.assertEqual("invalid_response", receipt["failure_kind"])

    def test_agy_utf8_packet_bound_includes_envelope_and_prevents_launch(self):
        # 70k characters are 140k UTF-8 bytes. Checking character count would fail.
        job = self.job(client="agy", role="gemini_pro", model="gemini-3.1-pro-high", prompt="ї" * 70_000)
        with mock.patch.object(clients.subprocess, "Popen") as call:
            receipt = clients.execute(job, self.attempt, 5)
        call.assert_not_called()
        self.assertEqual("packet_too_large", receipt["failure_kind"])
        self.assertGreater(receipt["input_bytes"], clients.AGY_MAX_INPUT_BYTES)

    def test_policy_refuses_rerouting_before_popen(self):
        invalid = [
            self.job(role="gemini_pro"), self.job(model="gemini-3.1-pro-high"),
            self.job(client="agy"), self.job(client="gemini"),
            self.job(role="reviewer", client="agy"),
        ]
        for index, job in enumerate(invalid):
            with self.subTest(job=job):
                folder = self.attempt / str(index)
                folder.mkdir()
                with mock.patch.object(clients.subprocess, "Popen") as call:
                    receipt = clients.execute(job, folder, 5)
                call.assert_not_called()
                self.assertEqual("failed", receipt["status"])

    def test_explicit_supplementary_agy_opus_is_distinct_role(self):
        receipt, _, _ = self.run_fake(self.job(client="agy", role="supplementary_opus", model="claude-opus-4.6"), self.agy_result())
        self.assertEqual("response_received", receipt["status"])
        self.assertEqual("supplementary_opus", receipt["role"])

    def test_immutable_existing_attempt_is_not_touched(self):
        path = self.attempt / "response.txt"
        path.write_text("historical report")
        with mock.patch.object(clients.subprocess, "Popen") as call:
            with self.assertRaisesRegex(ValueError, "empty"):
                clients.execute(self.job(), self.attempt, 5)
        call.assert_not_called()
        self.assertEqual("historical report", path.read_text())
        self.assertEqual([path], list(self.attempt.iterdir()))

    def test_cancellation_before_launch(self):
        cancel = threading.Event()
        cancel.set()
        with mock.patch.object(clients.subprocess, "Popen") as call:
            receipt = clients.execute(self.job(_cancel_event=cancel), self.attempt, 5)
        call.assert_not_called()
        self.assertEqual("interrupted", receipt["failure_kind"])

    def test_cancellation_during_communicate_kills_process_group(self):
        cancel = threading.Event()
        def callback(process, stdin, timeout):
            if timeout is not None:
                cancel.set()
                raise subprocess.TimeoutExpired("fake", timeout)
        process = FakeProcess(self.result(), on_communicate=callback)
        with mock.patch.object(clients.subprocess, "Popen", return_value=process), mock.patch.object(clients.os, "killpg") as kill:
            receipt = clients.execute(self.job(_cancel_event=cancel), self.attempt, 5)
        kill.assert_called_once_with(process.pid, signal.SIGKILL)
        self.assertEqual("interrupted", receipt["failure_kind"])
        self.assertEqual(2, len(process.inputs))
        self.assertIsNone(process.inputs[-1])

    def test_timeout_kills_group_and_writes_final_receipt(self):
        process = FakeProcess(self.result())
        with mock.patch.object(clients.subprocess, "Popen", return_value=process), \
                mock.patch.object(clients.os, "killpg") as kill, \
                mock.patch.object(clients.time, "monotonic", side_effect=[0, 1, 3, 4]):
            receipt = clients.execute(self.job(), self.attempt, 1)
        kill.assert_called_once_with(process.pid, signal.SIGKILL)
        self.assertEqual("timeout", receipt["failure_kind"])
        self.assertEqual("failed", receipt["status"])
        self.assertEqual(4, receipt["elapsed_seconds"])

    @unittest.skipUnless(sys.platform.startswith("linux"), "Linux process identity check")
    def test_linux_process_start_ticks_match_proc_stat(self):
        expected = int(Path(f"/proc/{os.getpid()}/stat").read_text().rsplit(")", 1)[1].split()[19])
        self.assertEqual(expected, clients._start_ticks(os.getpid()))

    @unittest.skipUnless(sys.platform.startswith("linux"), "POSIX process-group integration test")
    def test_real_temporary_fake_cli_timeout_kills_its_child(self):
        binary_dir = Path(self.temporary.name) / "bin"
        binary_dir.mkdir()
        executable = binary_dir / "agy"
        executable.write_text(
            f"#!{sys.executable}\n"
            "import json, subprocess, sys, time\n"
            "sys.stdin.read()\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
            "print(json.dumps({'event': 'init', 'init': {'child_pid': child.pid}}), flush=True)\n"
            "time.sleep(30)\n"
        )
        executable.chmod(0o700)
        with mock.patch.dict(os.environ, {"PATH": str(binary_dir) + os.pathsep + os.environ.get("PATH", "")}):
            receipt = clients.execute(self.job(client="agy", role="gemini_pro", model="gemini-3.1-pro-high"), self.attempt, 0.5)
        self.assertEqual("timeout", receipt["failure_kind"])
        child_pid = json.loads((self.attempt / "stdout.jsonl").read_text().splitlines()[0])["init"]["child_pid"]
        for _ in range(100):
            try:
                child_state = Path(f"/proc/{child_pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
            except FileNotFoundError:
                break
            if child_state == "Z":  # Exited; init has not reaped it yet.
                break
            time.sleep(0.01)
        else:
            os.kill(child_pid, signal.SIGKILL)
            self.fail("Descendant survived the timeout process-group cleanup")
        self.assertLess(receipt["elapsed_seconds"], 3)


if __name__ == "__main__":
    unittest.main()
