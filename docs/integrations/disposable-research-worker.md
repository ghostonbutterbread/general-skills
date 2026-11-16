# Disposable research worker — integration dossier

- **Status:** transport review fixes implemented; independent re-review, descendant-lifetime approval, and restricted-child integration remain blocked
- **Owner:** delegated Hermes worker
- **Branch / owning ref:** `feat/disposable-research-worker`
- **Worktree:** `/home/ryushe/worktrees/general-research-worker-20261115`
- **Base commit:** `20189521b6aab6997ebde5a353542af2e63848de` (fetched `origin/beta`)
- **Intended integration target:** `beta` (no integration authorized)
- **Last updated:** 2026-11-15
- **Latest immutable recovery checkpoint:** `ff325e79dd60520fb97875eb6eb29e105bf6abce` (review corrections; branch tip also contains this later dossier-only handoff)
- **Feature implementation commit(s):** `81ea4a33fb4f29e255917c75e5d4eaa918a845de` (preflight); `3cf82e6a87613201f3bd439ba35e166d469bd11c` (transport); `ff325e79dd60520fb97875eb6eb29e105bf6abce` (transport review corrections)
- **Inspiration / canonical references:** `safe-fetch`, `sandbox-run`, Hermes provider and Docker documentation; General Skills owns the generic safe-fetch skill. BBH's target stores and live runtime were not modified.

## Independent transport review corrections and remaining gates

The transport now keeps delayed-operation cleanup retryable, including after a
point-in-time absence; it never promotes that observation to definitive closure.
Task-owned host timers request removal at the 900-second task deadline and when a
still-running command exceeds its deadline by one second. Cancellation does not
wait behind exec; a create completing after cancellation triggers another exact-name
cleanup attempt. Descendants of an already-completed command may remain for the
rest of the task, so this does not provide per-command descendant isolation. The
host timer is not durable across host-process death and a broken/stalled daemon can
defeat timely cleanup. Uncertain outcomes require explicit repeated exact-name
reconciliation, not a finite waiting period presented as proof.

Post-launch Docker exceptions fail closed without returning exception or stdout;
exit 124/137 is explicitly ambiguous. The entire model-visible JSON response is
bounded by UTF-8 bytes including escaping, with invalid-byte replacement and
incomplete/truncated drains accounted for. No raw command/output appears in the
parent receipt. These are transport contracts, not evidence of a real child or a
safe untrusted summary.

Verification: `PYTHONPATH="$PWD" python3 -W error::ResourceWarning -m unittest
discover -s tests -v` ran 72 tests: 71 passed, one opt-in Docker test skipped.
This includes mock lifetime/late-create regressions. The previously
approved ordinary Docker isolation/reuse test was run twice, neither with
background/detached-descendant experiments: the first reported `unverified`
cleanup after daemon slowness and failed; later explicit removal and readback of
`research-task-d1ec6e3f0c6841b2a47475e32d043c4e` returned no such container and
an empty exact-name listing. A second ordinary run passed, but its cleanup was
`absent_at_check_delayed_operation_possible`; exact-name removal/readback of
`research-task-428c7e2b86664607ae3f0d523c162c26` subsequently found no such
container and an empty listing. Neither listing proves a delayed daemon request
cannot still complete. No global cleanup/prune was used.

**Withdrawn approval gate:** the independent reviewer's real-container
background/escaped-descendant lifetime probe was blocked with approval withdrawn.
Do not rerun it or reach the same outcome by a different command or mechanism.
Only after the operator explicitly restores that approval, design and run a
scoped task-owned E2E fixture verifying the descendant is gone on explicit
cancel, host task expiry, command deadline, and cleanup failure/retry, with
exact-name readback and no other containers touched; record its actual command,
artifacts, and results. Currently only mocked timer/cancel behavior is verified.
Host crash/daemon outage durability and per-command descendant isolation remain
unverified limitations, not passed checks. The changed transport needs independent
full-diff review; core exact-child lifecycle and real agent/model tests are separate
gates. No merge, push, activation, host-auth use, target or model probe is authorized.

## New direction: host-native researcher and containerized tools

The later task explicitly replaces the broker sketch below: the native child keeps its existing host provider/model; no model, credential, login, or broker runs inside Docker. The previously denied xAI probe remains forbidden and was not retried. `skills/safe-fetch/scripts/research_container.py` supplies one reusable, networkless per-task container and `register_tool(ctx, resolve_authorized_task=None)`. Its schema and trusted integration contract are documented in `skills/safe-fetch/scripts/README.md`. The default registration denies all tool calls. A caller-supplied resolver is host-trusted and MUST verify exact effective child tools, leaf status, and bound runtime identity before returning the task instance. Current public `PluginContext.subagent_lifecycle` has no exact effective-tool attestation; no real adapter has been written or activated. Registration cannot remove host tools.

The implementation retains no raw output in `receipt()`, and tags/caps returned tool output; parent must independently treat the child final answer as untrusted and bound it. Commands can pass short inline content, but public fetch, network policy, full-source ingestion, parent-side summary sanitization and a live agent workflow are not implemented. The local Docker image tag is mutable, not pinned. The kernel and daemon remain trusted. The in-container sleep and `--rm` do not ensure a 900-second maximum: an untrusted same-UID command can interfere with the sleeper, and the host timer itself requires a live process and responsive daemon. Exact-name readback is point-in-time and timeouts can cause delayed daemon effects.

Verification commands: `RESEARCH_DOCKER_TEST=1 PYTHONPATH="$PWD" python3 -W error::ResourceWarning -m unittest discover -s tests -p test_research_container.py -v`; `PYTHONPATH="$PWD" python3 -m unittest discover -s tests -v`. Real Docker exercised non-root, host-file and host-environment sentinel absence, no Docker socket, loopback-only network, task workspace reuse through the registered handler with a test-only resolver, nonzero exit, output cap, timeout, no reuse after timeout, and exact-name cleanup readback. A separate isolated-home scratch smoke invoked the real `PluginContext.register_tool`, real registry dispatch (denied without adapter), and registration disposal. The real-Docker resolver and context were test doubles, not a verified child lifecycle. This is not inference, prompt-injection, privacy certification, or end-to-end research evidence.

Next: parent integrates with the separately developed public exact-child allowlist lifecycle only after checking its actual API and identity binding; test absent/extra host tools, cross-child isolation, cancel/failure cleanup, real host-native researcher under existing authorized model settings, and bounded untrusted parent handoff. No model/provider probe was performed here. Independent review is required before merge. Delegated child cannot mutate Kanban; parent must reconcile tracking. No merge, push, config, activation, or core edits authorized.

## Historical diagnostic contract (superseded direction)


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

## Historical interruption / resume handoff (superseded by new direction above)

The immutable implementation checkpoint is `81ea4a33fb4f29e255917c75e5d4eaa918a845de`; the later branch tip contains this dossier-only handoff. Resume from this worktree, rerun the exact preflight and full tests, then implement/verify the genuinely isolated agent path only after resolving the endpoint/credential boundary. Do not alter an active hunter. The branch remains unmerged and unpushed.

## Decision gates

- **Integration:** independent review and a real end-to-end agent run, including hostile-source, privacy, cleanup, explicit promotion and multi-question reuse tests, all passing.
- **Activation / promotion:** separate explicit user decision; this branch does not activate anything.
