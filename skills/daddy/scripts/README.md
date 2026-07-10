# Daddy Scripts

Scripts owned by the `daddy` skill.

### `daddy_benchmark.py`

- Purpose: dry-run relative model routing scenarios and estimate proxy cost shape against a baseline current-model run.
- Inputs: built-in scenario mixes; edit constants for local experiments.
- Outputs: per-scenario baseline cost, routed proxy cost, savings percentage, and task mix.
- Safe to run on: local terminals; no network or model calls.
- Mutates: nothing.
- Example:
  ```bash
  python3 skills/daddy/scripts/daddy_benchmark.py
  ```
- Tests: run the example command and verify all four scenarios print.
- Owner: general-skills/daddy
- Last verified: 2026-07-10
