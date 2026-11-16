"""Offline blocker evidence against the specified native lifecycle candidate.

No model, provider, Docker, or network is used. This is not an adapter.
Run in a fenced subprocess with HERMES_NATIVE_CHECKOUT pointing at the candidate.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import threading
from types import ModuleType, SimpleNamespace
from typing import Any
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path(os.environ['HERMES_NATIVE_CHECKOUT']).resolve()
sys.path.insert(0, str(NATIVE))
spec = importlib.util.spec_from_file_location('research_container_fixture', ROOT / 'skills/safe-fetch/scripts/research_container.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)

from agent.subagent_lifecycle import bind_subagent_parent, SubagentState
from hermes_cli.plugins import PluginManager, PluginManifest
from hermes_cli.plugins_context import PluginContext
from tools.registry import registry


class LifecycleBlockerTests(unittest.TestCase):
    def setUp(self):
        self.manager = PluginManager()
        self.ctx = PluginContext(PluginManifest(name='research-blocker-fixture', source='user'), self.manager)
        self.registration = transport.register_tool(self.ctx)
        self.assertIsNotNone(self.registration)

    def tearDown(self):
        self.registration.dispose()

    def dispatch(self, **kwargs):
        return json.loads(registry.dispatch('research_container', {'command': 'never executed'},
                                            scope=self.manager.scope_key, **kwargs))

    def test_real_plugin_registration_denies_unknown_and_forged_runtime_ids(self):
        with patch.object(transport.ResearchContainer, 'execute', side_effect=AssertionError('must not execute')):
            for kwargs in ({}, {'task_id': 'sa-victim', 'session_id': 'child-session'},
                           {'task_id': 'sa-victim', 'session_id': 'parent-session', 'user_task': 'research'}):
                with self.subTest(kwargs=kwargs):
                    self.assertEqual(self.dispatch(**kwargs)['error'], 'exact_child_allowlist_not_verified')

    def test_public_status_returns_server_snapshot_but_only_in_parent_scope(self):
        parent = SimpleNamespace(session_id='fixture-parent')
        child = SimpleNamespace(_subagent_id='fixture-child-1', session_id='fixture-child-session',
                                provider=None, model=None, _delegate_role='leaf', _delegate_depth=1,
                                valid_tool_names={'research_container'}, _delegate_force_leaf=True)
        finish = threading.Event()
        fake: Any = ModuleType('tools.delegate_tool')
        fake._build_child_preserving_parent_tools = lambda **kwargs: child
        fake._credential_overrides = lambda *args: {}
        fake._load_config = lambda: {}
        fake._resolve_delegation_credentials = lambda *args: {'model': 'offline-fixture'}
        fake.DEFAULT_MAX_ITERATIONS = 1
        def run(*args):
            if not finish.wait(5):
                raise RuntimeError('fixture did not release child')
            return {'status': 'completed', 'summary': 'offline'}
        fake._run_child_lifecycle = run
        service = self.ctx.subagent_lifecycle
        with patch.dict(sys.modules, {'tools.delegate_tool': fake}):
            with bind_subagent_parent(parent):
                handle = service.launch({'goal': 'offline fixture', 'exact_tools': ['research_container'],
                                         'force_leaf': True, 'inherit_parent_route': True})
                forged = {**handle.to_dict(), 'effective_tools': ['terminal'], 'role': 'orchestrator'}
                snapshot = service.status(forged)
                self.assertEqual(snapshot.handle.effective_tools, ('research_container',))
                self.assertEqual(snapshot.handle.role, 'leaf')
                self.assertFalse(hasattr(snapshot.handle, 'child_session_id'))
                self.assertFalse(hasattr(snapshot.handle, 'force_leaf'))
            try:
                with bind_subagent_parent(child):
                    self.assertEqual(service.status(handle).state, SubagentState.UNKNOWN)
                    self.assertEqual(service.status(handle).diagnostic, 'UNKNOWN_HANDLE')
                    self.assertEqual(self.dispatch(task_id=handle.subagent_id, session_id=child.session_id)['error'],
                                     'exact_child_allowlist_not_verified')
            finally:
                finish.set()
                with bind_subagent_parent(parent):
                    self.assertTrue(service.wait(handle, timeout_seconds=5).completed)
                    self.assertEqual(service.result(handle).terminal_state, SubagentState.SUCCEEDED)

    def test_child_can_dispatch_before_launch_returns_handle(self):
        import agent.subagent_lifecycle as lifecycle
        parent = SimpleNamespace(session_id='fixture-parent-race')
        child = SimpleNamespace(_subagent_id='fixture-race-child', session_id='fixture-race-session',
                                provider=None, model=None, _delegate_role='leaf', _delegate_depth=1,
                                valid_tool_names={'research_container'})
        entered = threading.Event()
        results = []
        fake: Any = ModuleType('tools.delegate_tool')
        fake._build_child_preserving_parent_tools = lambda **kwargs: child
        fake._credential_overrides = lambda *args: {}
        fake._load_config = lambda: {}
        fake._resolve_delegation_credentials = lambda *args: {'model': 'offline-fixture'}
        fake.DEFAULT_MAX_ITERATIONS = 1
        def run(*args):
            with bind_subagent_parent(child):
                results.append(self.dispatch(task_id=child._subagent_id, session_id=child.session_id))
            entered.set()
            return {'status': 'completed', 'summary': 'offline'}
        fake._run_child_lifecycle = run
        executor = lifecycle._EXECUTOR
        class OrderedExecutor:
            def submit(self, *args):
                future = executor.submit(*args)
                if not entered.wait(5):
                    raise RuntimeError('child did not dispatch before return')
                return future
        with patch.dict(sys.modules, {'tools.delegate_tool': fake}), patch.object(lifecycle, '_EXECUTOR', OrderedExecutor()):
            with bind_subagent_parent(parent):
                handle = self.ctx.subagent_lifecycle.launch({'goal': 'race fixture',
                    'exact_tools': ['research_container'], 'force_leaf': True, 'inherit_parent_route': True})
                self.assertTrue(self.ctx.subagent_lifecycle.wait(handle, timeout_seconds=5).completed)
        self.assertEqual(results[0]['error'], 'exact_child_allowlist_not_verified')

    def test_registry_does_not_authenticate_id_kwargs(self):
        # Same plain kwargs can be presented by a direct registry caller; they are not
        # themselves a lifecycle-issued capability or an attestation of the caller.
        seen = []
        self.registration.dispose()
        def capture(kwargs):
            seen.append(kwargs)
            return None
        self.registration = transport.register_tool(self.ctx, capture)
        self.dispatch(task_id='fixture-child-1', session_id='fixture-child-session')
        self.assertEqual(seen[0]['task_id'], 'fixture-child-1')
        self.assertEqual(seen[0]['session_id'], 'fixture-child-session')


if __name__ == '__main__':
    unittest.main()
