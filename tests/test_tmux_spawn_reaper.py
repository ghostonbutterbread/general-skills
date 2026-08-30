from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "hoster-tmux-child-reaper" / "scripts" / "tmux_spawn_reaper.py"
RECORD = {
    "scope": "tmux-spawn-safe.scope",
    "control_group": "/user.slice/user-1000.slice/user@1000.service/app.slice/tmux-spawn-safe.scope",
    "original_pane_pid": 111,
    "launcher_pid": 222,
    "socket_path": "/tmp/tmux-1000/ghost-workspace",
}


def load_module():
    spec = importlib.util.spec_from_file_location("tmux_spawn_reaper", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TmuxSpawnReaperTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def props(self):
        return {
            "ActiveState": "active",
            "Description": "tmux child pane 111 launched by process 222",
            "ControlGroup": RECORD["control_group"],
        }

    def test_candidate_is_eligible_only_for_registered_empty_scope(self):
        with patch.object(self.module, "properties", return_value=self.props()), patch.object(self.module, "cgroup_processes", return_value=[]):
            result = self.module.candidate(RECORD["scope"], {RECORD["scope"]: RECORD}, {444})

        self.assertTrue(result["eligible"])
        self.assertEqual(result["reasons"], [])

    def test_candidate_refuses_unregistered_lookalike_scope(self):
        with patch.object(self.module, "properties", return_value=self.props()), patch.object(self.module, "cgroup_processes", return_value=[]):
            result = self.module.candidate(RECORD["scope"], {}, set())

        self.assertFalse(result["eligible"])
        self.assertIn("unregistered-scope", result["reasons"])

    def test_candidate_refuses_residual_ssh_agent_even_without_socket_inventory(self):
        with patch.object(self.module, "properties", return_value=self.props()), patch.object(self.module, "cgroup_processes", return_value=[{"pid": 333, "command": "ssh-agent"}]):
            result = self.module.candidate(RECORD["scope"], {RECORD["scope"]: RECORD}, set())

        self.assertFalse(result["eligible"])
        self.assertIn("process-remains", result["reasons"])

    def test_candidate_refuses_live_pane_from_any_tmux_socket(self):
        with patch.object(self.module, "properties", return_value=self.props()), patch.object(self.module, "cgroup_processes", return_value=[{"pid": 333, "command": "ssh-agent"}]):
            result = self.module.candidate(RECORD["scope"], {RECORD["scope"]: RECORD}, {111})

        self.assertFalse(result["eligible"])
        self.assertIn("original-pane-still-live", result["reasons"])

    def test_candidate_refuses_registry_metadata_mismatch_and_non_benign_process(self):
        mismatched = {**RECORD, "control_group": "/different.scope"}
        with patch.object(self.module, "properties", return_value=self.props()), patch.object(self.module, "cgroup_processes", return_value=[{"pid": 555, "command": "claude"}]):
            result = self.module.candidate(RECORD["scope"], {RECORD["scope"]: mismatched}, set())

        self.assertFalse(result["eligible"])
        self.assertIn("registry-mismatch", result["reasons"])
        self.assertIn("process-remains", result["reasons"])

    def test_register_requires_live_pane_and_unique_live_tmux_server(self):
        with patch.object(self.module, "properties", return_value=self.props()), patch.object(self.module, "pane_inventory", return_value=({111}, {222: {RECORD["socket_path"]}})):
            record = self.module.register(RECORD["scope"], {})

        self.assertEqual(record, RECORD)

    def test_register_pane_requires_exactly_one_matching_scope(self):
        with patch.object(self.module, "scopes", return_value=[RECORD["scope"]]), patch.object(self.module, "metadata", return_value=(self.props(), 111, 222)), patch.object(self.module, "register", return_value=RECORD) as register:
            result = self.module.register_pane(111, {})

        self.assertEqual(result, RECORD)
        register.assert_called_once_with(RECORD["scope"], {})

    def test_apply_rechecks_all_tmux_servers_and_stops_only_eligible_registered_scope(self):
        initial = {"scope": RECORD["scope"], "eligible": True}
        rechecked = {"scope": RECORD["scope"], "eligible": True}
        with patch.object(self.module, "registry_path", return_value=Path("/tmp/registry.json")), patch.object(self.module, "load_registry", return_value={RECORD["scope"]: RECORD}), patch.object(self.module, "pane_inventory", side_effect=[(set(), {}), (set(), {})]), patch.object(self.module, "scopes", return_value=[RECORD["scope"]]), patch.object(self.module, "candidate", side_effect=[initial, rechecked]), patch.object(self.module, "run") as run, patch("sys.argv", ["reaper", "--apply"]):
            self.assertEqual(self.module.main(), 0)

        run.assert_called_once_with("systemctl", "--user", "stop", RECORD["scope"])

    def test_registry_round_trip_uses_restricted_json_file(self):
        with self.subTest("round trip"):
            with __import__("tempfile").TemporaryDirectory() as temporary:
                path = Path(temporary) / "state" / "registry.json"
                self.module.save_registry(path, {RECORD["scope"]: RECORD})
                self.assertEqual(self.module.load_registry(path), {RECORD["scope"]: RECORD})
                self.assertEqual(json.loads(path.read_text())["version"], 1)


if __name__ == "__main__":
    unittest.main()
