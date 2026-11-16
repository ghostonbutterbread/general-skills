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
                def read(self): return b'{}'
            captured = []
            def open_request(request, timeout):
                captured.append(request)
                return Response()
            with patch.dict(os.environ, {'GENERAL_SKILLS_CONFIG': str(config)}), patch.object(sender, 'open_webhook', side_effect=open_request):
                result = sender.main(['--kind', 'handoff', '--agent', 'Scout', '--run', 'run-42', '--summary', 'Login needed', '--action', 'Complete login', '--status', 'Paused'])
            self.assertEqual(result, 0)
            payload = json.loads(captured[0].data)
            self.assertIn('Login needed', payload['content'])
            self.assertIn('run-42', payload['content'])
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

if __name__ == '__main__':
    unittest.main()
