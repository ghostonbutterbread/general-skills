"""Behavioral tests for the portable agent-outreach sender."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/agent-outreach/scripts/send.py'

class OutreachTests(unittest.TestCase):
    def test_sends_markdown_to_configured_webhook_without_mentions(self):
        self.assertTrue(SCRIPT.is_file(), 'agent-outreach sender must exist')
        spec = importlib.util.spec_from_file_location('outreach', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            secret = root / 'webhook'
            secret.write_text('https://discord.com/api/webhooks/1234567890/fake-token')
            secret.chmod(0o600)
            config = root / 'config.toml'
            config.write_text('[agent_outreach.destinations.default]\nwebhook_file = "' + str(secret) + '"\n')
            class Response:
                status = 200
                def __enter__(self): return self
                def __exit__(self, *args): pass
                def read(self): return b'{"id":"123456789"}'
            captured = []
            def open_request(request, timeout):
                captured.append(request)
                return Response()
            with patch.dict(os.environ, {'GENERAL_SKILLS_CONFIG': str(config)}), patch.object(sender, 'open_webhook', side_effect=open_request):
                result = sender.main(['--kind', 'handoff', '--agent', 'Scout', '--run', 'run-42', '--summary', 'Login needed', '--action', 'Complete login', '--status', 'Paused', '--link', 'https://example.invalid/handoff'])
            self.assertEqual(result, 0)
            self.assertTrue(captured[0].full_url.endswith('?wait=true'))
            self.assertEqual(captured[0].get_header('User-agent'), 'AgentOutreach/1.0')
            payload = json.loads(captured[0].data)
            self.assertIn('Login needed', payload['content'])
            self.assertIn('run-42', payload['content'])
            self.assertIn('https://example.invalid/handoff', payload['content'])
            self.assertEqual(payload['allowed_mentions'], {'parse': []})
            self.assertNotIn('fake-token', payload['content'])

    def test_refuses_world_readable_webhook(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('outreach_permissions', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / 'webhook'
            secret.write_text('https://discord.com/api/webhooks/1234567890/fake-token')
            secret.chmod(0o644)
            config = Path(tmp) / 'config.toml'
            config.write_text('[agent_outreach.destinations.default]\nwebhook_file = "' + str(secret) + '"\n')
            with patch.dict(os.environ, {'GENERAL_SKILLS_CONFIG': str(config)}):
                with self.assertRaisesRegex(ValueError, 'chmod 600'):
                    sender.webhook_for('default')

    def test_rejects_non_discord_url(self):
        spec = importlib.util.spec_from_file_location('outreach_url', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / 'webhook'
            secret.write_text('https://elsewhere.invalid/api/webhooks/123/fake-token')
            secret.chmod(0o600)
            config = Path(tmp) / 'config.toml'
            config.write_text('[agent_outreach.destinations.default]\nwebhook_file = "' + str(secret) + '"\n')
            with patch.dict(os.environ, {'GENERAL_SKILLS_CONFIG': str(config)}):
                with self.assertRaisesRegex(ValueError, 'Discord HTTPS'):
                    sender.webhook_for('default')

    def test_failure_does_not_print_webhook_or_retry(self):
        import contextlib
        import io
        import urllib.error
        spec = importlib.util.spec_from_file_location('outreach_failure', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        with tempfile.TemporaryDirectory() as tmp:
            secret = Path(tmp) / 'webhook'
            secret.write_text('https://discord.com/api/webhooks/1234567890/fake-token')
            secret.chmod(0o600)
            config = Path(tmp) / 'config.toml'
            config.write_text('[agent_outreach.destinations.default]\nwebhook_file = "' + str(secret) + '"\n')
            failure = urllib.error.HTTPError('https://discord.com/api/webhooks/1234567890/fake-token', 429, 'rate limited', {}, None)
            error = io.StringIO()
            with patch.dict(os.environ, {'GENERAL_SKILLS_CONFIG': str(config)}), patch.object(sender, 'open_webhook', side_effect=failure) as opener, contextlib.redirect_stderr(error):
                result = sender.main(['--kind', 'safety', '--agent', 'Builder', '--run', '42', '--summary', 'Unexpected write', '--action', 'Review', '--status', 'Paused'])
            self.assertEqual(result, 1)
            self.assertEqual(opener.call_count, 1)
            self.assertIn('429', error.getvalue())
            self.assertNotIn('fake-token', error.getvalue())

    def test_oversized_message_does_not_attempt_delivery(self):
        import contextlib
        import io
        spec = importlib.util.spec_from_file_location('outreach_limit', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        with patch.object(sender, 'open_webhook') as opener, contextlib.redirect_stderr(io.StringIO()):
            result = sender.main(['--kind', 'notice', '--agent', 'Agent', '--run', '42', '--summary', 'x' * 2100, '--action', 'Review', '--status', 'Paused'])
        self.assertEqual(result, 1)
        opener.assert_not_called()

    def test_uncertain_post_failures_do_not_claim_definitive_failure(self):
        import contextlib
        import http.client
        import io
        import urllib.error
        spec = importlib.util.spec_from_file_location('outreach_uncertain', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        class InterruptedResponse:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): raise http.client.IncompleteRead(b'')
        for effect in (urllib.error.HTTPError('https://discord.com/api/webhooks/123/fake-token', 500, 'error', {}, None), InterruptedResponse()):
            error = io.StringIO()
            kwargs = {'side_effect': effect} if isinstance(effect, Exception) else {'return_value': effect}
            with patch.object(sender, 'webhook_for', return_value='https://discord.com/api/webhooks/123/fake-token'), patch.object(sender, 'open_webhook', **kwargs), contextlib.redirect_stderr(error):
                result = sender.main(['--kind', 'safety', '--agent', 'Builder', '--run', '42', '--summary', 'Unexpected write', '--action', 'Review', '--status', 'Paused'])
            self.assertEqual(result, 1)
            self.assertIn('uncertain', error.getvalue().lower())
            self.assertIn('before retry', error.getvalue().lower())
            self.assertNotIn('fake-token', error.getvalue())

    def test_mistaken_destination_does_not_leak_url(self):
        import contextlib
        import io
        spec = importlib.util.spec_from_file_location('outreach_destination', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'config.toml'
            config.write_text('[agent_outreach.destinations]\n')
            error = io.StringIO()
            with patch.dict(os.environ, {'GENERAL_SKILLS_CONFIG': str(config)}), contextlib.redirect_stderr(error):
                result = sender.main(['--destination', 'https://discord.com/api/webhooks/123/fake-token', '--kind', 'notice', '--agent', 'A', '--run', '42', '--summary', 'Hi', '--action', 'Review', '--status', 'Paused'])
            self.assertEqual(result, 1)
            self.assertNotIn('fake-token', error.getvalue())

    def test_post_response_requires_a_confirmed_message(self):
        import contextlib
        import io
        spec = importlib.util.spec_from_file_location('outreach_confirmation', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        class Response:
            def __init__(self, status, body): self.status, self.body = status, body
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return self.body
        for response in (Response(204, b''), Response(200, b'not-json'), Response(200, b'{}')):
            error = io.StringIO()
            with patch.object(sender, 'webhook_for', return_value='https://discord.com/api/webhooks/123/fake-token'), patch.object(sender, 'open_webhook', return_value=response), contextlib.redirect_stderr(error):
                result = sender.main(['--kind', 'notice', '--agent', 'A', '--run', '42', '--summary', 'Hi', '--action', 'Review', '--status', 'Paused'])
            self.assertEqual(result, 1)
            self.assertIn('uncertain', error.getvalue().lower())
            self.assertIn('before retry', error.getvalue().lower())

    def test_post_value_error_is_uncertain_and_redacted(self):
        import contextlib
        import io
        spec = importlib.util.spec_from_file_location('outreach_post_value', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        class Response:
            status = 200
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): raise ValueError('fake-token')
        error = io.StringIO()
        with patch.object(sender, 'webhook_for', return_value='https://discord.com/api/webhooks/123/fake-token'), patch.object(sender, 'open_webhook', return_value=Response()), contextlib.redirect_stderr(error):
            result = sender.main(['--kind', 'notice', '--agent', 'A', '--run', '42', '--summary', 'Hi', '--action', 'Review', '--status', 'Paused'])
        self.assertEqual(result, 1)
        self.assertIn('uncertain', error.getvalue().lower())
        self.assertNotIn('fake-token', error.getvalue())

    def test_non_posix_host_fails_cleanly(self):
        spec = importlib.util.spec_from_file_location('outreach_posix', SCRIPT)
        sender = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sender)
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / 'config.toml'
            config.write_text('[agent_outreach.destinations.default]\nwebhook_file = "unused"\n')
            with patch.dict(os.environ, {'GENERAL_SKILLS_CONFIG': str(config)}), patch.object(sender.os, 'getuid', create=True) as getuid:
                # Simulate a platform without getuid at the capability check.
                with patch('builtins.hasattr', side_effect=lambda obj, name: False if obj is sender.os and name == 'getuid' else getattr(obj, name, None) is not None):
                    with self.assertRaisesRegex(ValueError, 'POSIX host'):
                        sender.webhook_for('default')
                getuid.assert_not_called()

if __name__ == '__main__':
    unittest.main()
