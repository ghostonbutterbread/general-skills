# Hoster SSH helper scripts

## `hoster_user_unit.py`

- **Purpose:** dispatch one durable Hoster command over short-lived SSH into a
  named, resource-bounded `systemd --user` service.
- **Inputs:** a safe unit name, optional resource budgets, and command argv
  after `--`.
- **Output:** the transient unit name and its initial cgroup/resource status;
  long-running command output is read with `journalctl --user -u <unit>`.
- **Mutation:** starts a Hoster transient user service; it does not stop or
  inspect unrelated workloads.
- **Example:**
  ```bash
  python3 hoster_user_unit.py --unit=hoster-demo-20260724T000000Z -- \
    /bin/bash -lc 'cd /home/ryushe/projects/example && exec ./run.sh'
  ```
- **Verification:**
  ```bash
  python3 -m unittest tests/test_hoster_user_unit.py -v
  ```
- **Owner/scope:** `hoster-ssh`; Hoster-only durable workload dispatch.
- **Last verified:** 2026-07-24.
