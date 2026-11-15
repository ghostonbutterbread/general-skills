import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "skills/safe-fetch/scripts/research_worker_preflight.py"
spec = importlib.util.spec_from_file_location("research_worker_preflight", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PreflightTests(unittest.TestCase):
    def run_mock(self, checks=None, run_rc: int | None = 0, cleanup_rc=0, cleanup_out=""):
        calls = []
        checks = checks if checks is not None else {key: True for key in module.EXPECTED}

        def docker(args, timeout, env=None):
            calls.append((args, env))
            if args[0] == "run":
                return run_rc, json.dumps(checks), ""
            if args[0] == "rm":
                return 0, "", ""
            return cleanup_rc, cleanup_out, ""

        with patch.object(module, "docker", side_effect=docker):
            result = module.probe(1)
        return result, calls

    def test_expected_configuration_and_privacy_canary(self):
        result, calls = self.run_mock()
        self.assertTrue(result["probe_passed"])
        self.assertFalse(result["agent_executed"])
        args, env = calls[0]
        self.assertIn("none", args)
        for option in ("--read-only", "--cap-drop", "--security-opt", "--user", "--pull=never"):
            self.assertIn(option, args)
        self.assertNotIn("--mount", args)
        self.assertNotIn("-v", args)
        canary = next(k for k in env if k.startswith("RESEARCH_HOST_CANARY_"))
        self.assertNotIn(env[canary], " ".join(args))
        self.assertEqual(calls[1][0][-1], result["container"])
        self.assertEqual(result["cleanup"], "absent_at_check")

    def test_leaked_canary_is_fail_closed(self):
        checks = {key: True for key in module.EXPECTED}
        checks["canary_env_absent"] = False
        result, _ = self.run_mock(checks)
        self.assertFalse(result["probe_passed"])

    def test_host_file_and_network_negative_controls(self):
        for key in ("host_canary_absent", "network_none", "nonroot", "root_read_only"):
            checks = {k: True for k in module.EXPECTED}
            checks[key] = False
            with self.subTest(key=key):
                self.assertFalse(self.run_mock(checks)[0]["probe_passed"])

    def test_partial_forged_response_and_timeout_fail_closed(self):
        for checks, rc in (({"nonroot": True}, 0), ({key: True for key in module.EXPECTED}, None)):
            result, calls = self.run_mock(checks, rc)
            self.assertFalse(result["probe_passed"])
            self.assertEqual(calls[1][0][0], "rm")
            self.assertEqual(calls[2][0][0], "ps")

    def test_unverified_cleanup_fails_closed(self):
        for rc, out in ((1, ""), (0, "lingering\n")):
            result, _ = self.run_mock(cleanup_rc=rc, cleanup_out=out)
            self.assertEqual(result["cleanup"], "unverified")
            self.assertFalse(result["probe_passed"])

    def test_real_probe_detects_host_canary_exposure(self):
        with tempfile.TemporaryDirectory() as directory:
            host_file = Path(directory) / "host-only"
            host_file.write_text("fixture", encoding="utf-8")
            env = dict(os.environ, PROBE_NAME="INJECTED_FIXTURE", PROBE_PATH=str(host_file), INJECTED_FIXTURE="fixture")
            p = subprocess.run([sys.executable, "-c", module.PROBE], env=env, capture_output=True, text=True, timeout=5, check=True)
        checks = json.loads(p.stdout)
        self.assertFalse(checks["canary_env_absent"])
        self.assertFalse(checks["host_canary_absent"])

    def test_untrusted_command_argument_is_rejected(self):
        # A source-provided instruction cannot become an arbitrary command or mount.
        p = subprocess.run([sys.executable, str(SCRIPT), "--", "--mount", "/:/host"],
                           capture_output=True, text=True, timeout=5)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("unrecognized arguments", p.stderr)


if __name__ == "__main__":
    unittest.main()
