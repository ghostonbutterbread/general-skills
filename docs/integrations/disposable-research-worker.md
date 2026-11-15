# Disposable research worker — integration dossier

- **Status:** blocked on withdrawn approval for model-access probe; diagnostic slice only, not a research agent
- **Owner:** delegated Hermes worker
- **Branch / owning ref:** `feat/disposable-research-worker`
- **Worktree:** `/home/ryushe/worktrees/general-research-worker-20261115`
- **Base commit:** `20189521b6aab6997ebde5a353542af2e63848de` (fetched `origin/beta`)
- **Intended integration target:** `beta` (no integration authorized)
- **Last updated:** 2026-11-15
- **Latest immutable recovery checkpoint:** `81ea4a33fb4f29e255917c75e5d4eaa918a845de` (implementation commit; branch tip also contains a later dossier-only handoff)
- **Feature implementation commit(s):** `81ea4a33fb4f29e255917c75e5d4eaa918a845de`
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
- Follow-up provider discovery: `hermes proxy providers` lists only `nous` and `xai`; `hermes proxy status` says Nous is not logged in and xAI is ready. `hermes auth status` says both `xai-oauth` and `openai-codex` are logged in, but login/ready is not proof of inference entitlement. The proxy adapter registry has no Codex adapter. Hermes's built-in proxy accepts any bearer and is not an appropriate unauthenticated container/LAN endpoint; xAI's OAuth adapter uses the host credential pool and can refresh/rotate credentials. The docs note that xAI OAuth inference can return 403 despite a successful login; no 403 was observed here.
- A single bounded xAI host-side inference probe was proposed using Hermes's adapter, an exact upstream assertion, and no credential output. The approval tool returned **BLOCKED: approval withdrawn before user answered; command did not run; do not retry or attempt the same outcome differently**. Consequently there is no inference response, and neither xAI entitlement nor any model mediation is validated. A prior command to locate the interpreter failed before reaching an inference call; no credential was printed.
- A possible architecture to investigate after the approval gate is a task-owned host-only inference broker exposed to a `--network none` container via a single Unix-domain socket, with fixed model/path and bounded request/count, explicit cleanup, and no host-auth or Docker-socket mounts. This is a design sketch, not an implemented or audited security boundary; full source is necessarily sent to the model provider and output is untrusted. The built-in proxy's unauthenticated TCP listener is not itself sufficient. Protect against upstream credential disclosure, request smuggling, unintended endpoint access, resource exhaustion and host filesystem exposure; test the actual runtime rather than presuming socket isolation.
- Follow-up verification: `PYTHONPATH="$PWD" python3 -m unittest discover -s tests -v` passed all 56 tests; `git diff --check` passed. These tests do not validate a model-backed researcher.

## Blockers and deferred work

- **Missing:** a real, contained agent doing multi-question reasoning over full supplied source; actual hostile-source/prompt-injection and private-data exfiltration tests, output validation, safe handoff and reuse/cleanup tests.
- **Approval blocker:** the host-side, no-secret-output xAI inference probe was not executed because its command approval was withdrawn. The operator must restore/explicitly grant the relevant command approval before any retry of that outcome. Do not bypass the approval by changing commands, using the built-in proxy, or another provider.
- **Environment needed:** after the approval gate is resolved, validate whether an existing authenticated provider is inference-entitled and whether its subscription permits this use; otherwise provision an authorized dedicated inference endpoint with a narrowly scoped, revocable credential/budget, or an isolated local model endpoint. In all cases the credential must remain on the host, not in the container. A networkless agent cannot independently reach a remote provider.
- **Trigger:** operator grants the blocked model-access approval and an authorized, inference-capable provider/mediation path is established; Docker execution must be reliable enough to complete the probe.
- **Next step:** after approval, run one bounded benign inference probe without printing credentials; then design and test a broker/transport without broad network or host exposure; deliver source into task-owned isolated storage, integrate an actual agent with explicit source/citation and question interface, then prove the named negative controls and cleanup against real runtime behavior. Do not equate a prompt instruction, heuristic sanitizer, or this preflight with a security boundary.
- **Why it blocks:** no substantive model call has succeeded, so user-requested agent operation and privacy/injection claims are unverified. This branch is not integration-ready.

## Interruption / resume handoff

The immutable implementation checkpoint is `81ea4a33fb4f29e255917c75e5d4eaa918a845de`; the later branch tip contains this dossier-only handoff. Resume from this worktree, rerun the exact preflight and full tests, then implement/verify the genuinely isolated agent path only after resolving the endpoint/credential boundary. Do not alter an active hunter. The branch remains unmerged and unpushed.

## Decision gates

- **Integration:** independent review and a real end-to-end agent run, including hostile-source, privacy, cleanup, explicit promotion and multi-question reuse tests, all passing.
- **Activation / promotion:** separate explicit user decision; this branch does not activate anything.
