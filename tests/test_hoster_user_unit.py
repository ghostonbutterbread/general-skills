from __future__ import annotations

import base64
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "hoster-ssh" / "scripts" / "hoster_user_unit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("hoster_user_unit", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HosterUserUnitTests(unittest.TestCase):
    def test_build_run_invocation_uses_a_bounded_user_systemd_service_and_preserves_command_argv(self):
        module = load_module()

        invocation = module.build_run_invocation(
            host="ryushe@hoster",
            identity_file="/home/ryushe/.ssh/hoster",
            unit="hoster-chromium-run-123",
            memory_high="2G",
            memory_max="3G",
            cpu_weight=100,
            command=["/bin/bash", "-lc", "cd /tmp/demo && python3 chromium_test.py demo smoke --json"],
        )

        self.assertEqual(
            invocation[:8],
            [
                "ssh",
                "-i",
                "/home/ryushe/.ssh/hoster",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=10",
                "-o",
            ],
        )
        self.assertIn("systemd-run", invocation[-1])
        self.assertIn("--user", invocation[-1])
        self.assertNotIn("--scope", invocation[-1])
        self.assertIn("systemctl", invocation[-1])
        self.assertIn("MemoryHigh", invocation[-1])
        self.assertIn("MemoryMax", invocation[-1])
        self.assertNotIn("tmux", invocation[-1])
        self.assertNotIn("nohup", invocation[-1])

        encoded = invocation[-1].split("HOSTER_UNIT_PAYLOAD=", 1)[1].split(" ", 1)[0].strip("'")
        payload = json.loads(base64.b64decode(encoded))
        self.assertEqual(payload["unit"], "hoster-chromium-run-123")
        self.assertEqual(
            payload["command"],
            ["/bin/bash", "-lc", "cd /tmp/demo && python3 chromium_test.py demo smoke --json"],
        )

    def test_invalid_unit_name_is_rejected_before_any_ssh_command_is_built(self):
        module = load_module()

        with self.assertRaisesRegex(ValueError, "unit"):
            module.build_run_invocation(
                host="ryushe@hoster",
                identity_file="/home/ryushe/.ssh/hoster",
                unit="hoster bad; rm -rf /",
                memory_high="2G",
                memory_max="3G",
                cpu_weight=100,
                command=["true"],
            )


if __name__ == "__main__":
    unittest.main()
