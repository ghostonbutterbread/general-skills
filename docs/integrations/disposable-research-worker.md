# Disposable research worker — integration dossier

- **Status:** blocked; diagnostic slice only, not a research agent
- **Owner:** delegated Hermes worker
- **Branch / owning ref:** `feat/disposable-research-worker`
- **Worktree:** `/home/ryushe/worktrees/general-research-worker-20261115`
- **Base commit:** `20189521b6aab6997ebde5a353542af2e63848de` (fetched `origin/beta`)
- **Intended integration target:** `beta` (no integration authorized)
- **Last updated:** 2026-11-15
- **Latest immutable recovery checkpoint:** see follow-up dossier-only commit
- **Feature implementation commit(s):** see follow-up dossier-only commit
- **Inspiration / canonical references:** `safe-fetch`, `sandbox-run`, Hermes provider and Docker documentation; General Skills owns the generic safe-fetch skill. BBH's target stores and live runtime were not modified.

## Intent and implemented contract

A future reusable per-hunt worker must genuinely reason over full quarantined source, support related questions, and produce sourced candidate ideas only. Its output must remain untrusted; writing reviewed knowledge requires a separate explicit, scoped host handoff. The worker must not direct a privileged hunter. It must receive neither broad host mounts, Docker socket, live session credentials nor ambient tokens, and have no arbitrary direct write capability. No live targets.

This branch implements only `skills/safe-fetch/scripts/research_worker_preflight.py`: a fixed-command, no-pull, no-network Docker diagnostic with no host mounts, a disposable container, process/resource restrictions, and task-owned environment/file canaries. It does not read external content, instantiate an LLM, or implement reuse, promotion or a broker. Its pass reports only the five checks executed and point-in-time container absence; it is not a security certification. A Docker operation may finish after a timeout and after the first cleanup attempt; `unverified` means recheck the exact task container name. Its isolated probe uses the local mutable `python:3.12-slim` tag, not a supply-chain-pinned image.

## Evidence and review

- `PYTHONPATH="$PWD" python3 -m unittest discover -s tests -v`: 56 passed, including seven diagnostic tests. Most probe-result scenarios use mocks; the host-executed negative canary control and CLI argument rejection execute actual Python, not an agent. No model prompt-injection test has run.
- `python3 skills/safe-fetch/scripts/research_worker_preflight.py --timeout 12`: failed closed; Docker start timed out, cleanup was unverified, and a delayed task-owned container briefly appeared. A later exact-name cleanup/readback found it absent.
- `python3 skills/safe-fetch/scripts/research_worker_preflight.py --timeout 90`: returned `probe_passed: true`, all five checks true, `cleanup: absent_at_check`, `agent_executed: false`. This validates only the named checks under that one local Docker/image configuration.
- A separate no-network, non-root, no-mount run of `nousresearch/hermes-agent:latest` with isolated tmpfs home and no credentials launched the real Hermes CLI but exited 1: no configured API keys or providers. PID 1 warning also indicates future worker launcher needs an init/reaper. No live profile was mounted or used.
- Docker client/server 29.1.3, rootful with AppArmor and default seccomp. Real Docker startup was intermittently slow; timeout is not evidence that no delayed daemon request will complete.
- Official documentation index was fetched with `safe_fetch.py` into quarantine; risk flags require lab handling. Hermes image and local provider source were inspected. The local process exposed no dedicated API-key environment names checked; that does not prove no model service exists elsewhere.
- Independent full-diff review: not performed. Delegated child contexts cannot mutate project Kanban; parent must reconcile tracking.

## Blockers and deferred work

- **Missing:** a real, contained agent doing multi-question reasoning over full supplied source; actual hostile-source/prompt-injection and private-data exfiltration tests, output validation, safe handoff and reuse/cleanup tests.
- **Environment needed:** authorized dedicated inference endpoint with a narrowly scoped, revocable credential/budget and a tested mediation design that does not expose that credential to the agent; or an appropriately isolated local model endpoint. Do not use the live Hermes OAuth/session or an ambient provider token. A networkless agent cannot independently reach a remote provider.
- **Trigger:** endpoint and narrowly scoped credential or isolated model approved and provisioned, and Docker execution reliable enough to complete the probe.
- **Next step:** design and test a broker/transport without broad network or host exposure; deliver source into task-owned isolated storage, integrate an actual agent with explicit source/citation and question interface, then prove the named negative controls and cleanup against real runtime behavior. Do not equate a prompt instruction, heuristic sanitizer, or this preflight with a security boundary.
- **Why it blocks:** no substantive model call has succeeded, so user-requested agent operation and privacy/injection claims are unverified. This branch is not integration-ready.

## Interruption / resume handoff

See follow-up dossier-only commit for the immutable implementation checkpoint. Resume from this worktree, rerun the exact preflight and full tests, then implement/verify the genuinely isolated agent path only after resolving the endpoint/credential boundary. Do not alter an active hunter. The branch remains unmerged and unpushed.

## Decision gates

- **Integration:** independent review and a real end-to-end agent run, including hostile-source, privacy, cleanup, explicit promotion and multi-question reuse tests, all passing.
- **Activation / promotion:** separate explicit user decision; this branch does not activate anything.
