# Disposable research worker — integration dossier

- **Status:** fail-closed transport checkpoint; **not usable for reusable research**; cleanup approval, secure completion, independent review, descendant-lifetime approval, and restricted-child integration remain blocked
- **Owner:** delegated Hermes worker
- **Branch / owning ref:** `feat/disposable-research-worker`
- **Worktree:** `/home/ryushe/worktrees/general-research-worker-20261115`
- **Base commit:** `20189521b6aab6997ebde5a353542af2e63848de` (fetched `origin/beta`)
- **Intended integration target:** `beta` (no integration authorized)
- **Last updated:** 2026-11-15
- **Latest immutable recovery checkpoint:** `48803abeb735f621bb63c2ddb1fa33cc6d8b5817` (fail-closed completion repair and tests; branch tip may contain a later dossier-only handoff)
- **Feature implementation commit(s):** `81ea4a33fb4f29e255917c75e5d4eaa918a845de` (preflight); `3cf82e6a87613201f3bd439ba35e166d469bd11c` (transport); `ff325e79dd60520fb97875eb6eb29e105bf6abce` (transport review corrections); `198466b27a2076ee1fdd1967f7bf7157c223d144` (transport re-review corrections); `48803abeb735f621bb63c2ddb1fa33cc6d8b5817` (fail-closed status checkpoint)
- **Inspiration / canonical references:** `safe-fetch`, `sandbox-run`, Hermes provider and Docker documentation; General Skills owns the generic safe-fetch skill. BBH's target stores and live runtime were not modified.

## Current completion-status blocker and exact receipt

Docker CLI rc 1 is genuinely ambiguous: the real CLI against a nonexistent Unix
socket returned 1, as did a real in-container `exit 1`. A random or formatted
marker on the command's own output is not an authenticated receipt: that same
untrusted command can print or imitate control data, and a same-UID wrapper is
not a separate security boundary. Rather than introduce a false proof, this
checkpoint intentionally **fails closed for every completed exec**, including
success and ordinary `exit 1` / `exit 7`: `exit_code` is null, the CLI rc is
labeled `docker_client_exit_code`, output is left as bounded untrusted data,
cleanup is required, and no second command is accepted. A client timeout has
no exit field. There is no completion-marker protocol and no claim of restored
ordinary failure/reuse behavior. This is a severe usability regression explicitly
chosen over unsafe reuse; the transport is not integration-ready.

Regression-first: against `70c11ad`, the daemon-rc-1 regression errored due to
missing `cleanup_required`; success/1/7/marker-like output cases and the
beyond-cap case also errored due to missing unverified status. The current full
suite command `PYTHONPATH="$PWD" python3 -W error::ResourceWarning -m unittest
discover -s tests -v` ran 85 tests: 83 passed, two opt-in Docker tests skipped.
The real unreachable-daemon CLI test passed within that suite. Timeout, race,
invalid-byte, response-bound and marker-like cases are mocked unless noted.

Opt-in command `RESEARCH_DOCKER_TEST=1 PYTHONPATH="$PWD" python3 -W
error::ResourceWarning -m unittest discover -s tests -p 'test_research_container.py'
-v` ran 29 tests: 28 passed and one failed (exit-7 fixture cleanup). The success
fixture showed `first`, CLI rc 0, unverified completion, and no reuse; exit-1
and exit-7 fixtures showed `command-output` with CLI rc 1 and 7 respectively,
both still unverified and non-reusable. Their names and cleanup receipts were:
`research-task-c52552a3630c4d1bae18ee7dfeb1ae54` absent at check with delayed
operation possible; `research-task-c70cdd8d36fc48128407aeb194663f11` same;
`research-task-6e66469dcca3431391590da088509230` **unverified**, causing the
failure. An earlier single-fixture opt-in run passed 28 tests and its container
`research-task-d75f38127efa4267a2599fb41db73935` was later checked absent by
exact-name listing (point-in-time only).

**Approval blocker:** a subsequent exact-name `rm -f` retry for the exit-7
fixture plus exact-name readback of the last three containers was blocked because
approval timed out with no user response; the command did not run. Do not retry
that command or the same cleanup outcome by another method unless the user
responds and explicitly authorizes it. The exit-7 container may still exist;
no general prune is allowed. After approval, reconcile only that exact name and
record fresh exact-name inspection; delayed daemon effects remain possible.
The other two latest fixtures were absent only at their initial checks.

**Next:** obtain approval for that cleanup, then implement and review a trusted
host/daemon-controlled completion-status path that cannot be forged by command
output, preserves the bounded output stream, actual exit codes and reuse, and
fails closed on daemon/missing/partial/late evidence. For example, assess Docker
Engine exec create/start/inspect with authenticated host-side daemon access;
this is a design direction, not an implemented or verified solution. It must
preserve or explicitly reject supported daemon/TLS configurations. Re-run the
opt-in ordinary fixtures (including real 0/1/7, cap, timeout and races), full
suite, and independent full-diff review. Existing denied descendant-lifetime and
model-probe restrictions below remain in force; do not use those probes as a
substitute. No merge, push, or activation authorized.

## Historical transport review corrections and remaining gates

The following section records earlier checkpoints; its reusable-success and
exit-code claims are superseded by the current fail-closed status above.

Re-review corrections: every transport Docker CLI invocation gets a private,
empty temporary config; proxy/auth settings from the host config are not copied.
Named Docker contexts are rejected instead of silently switching daemons;
`DOCKER_HOST` and TLS environment settings remain host-side. The caller must
keep daemon selection stable through cleanup. Drain errors propagate into
uncertain, retryable cleanup; reader-start failure kills and waits for the client;
timer-start failure cannot leave an in-flight or exec lock held; exit 125 is
treated as an ambiguous transport/command failure requiring cleanup.

Regression-first evidence: the initial seven tests failed against `cf58f2c`
(three failures/four errors); a separate failed-kill/reap regression also failed
before correction. `PYTHONPATH="$PWD" python3 -W error::ResourceWarning -m unittest
discover -s tests -p 'test_research*.py' -v` ran 31 tests: 30 passed, one
opt-in real Docker test skipped. The full suite ran 80: 79 passed, one skipped.
Read-only `docker context inspect` comparisons, using a disposable empty config,
matched the host default context and matched a synthetic `DOCKER_HOST` selection;
no container was started. Mocked tests do not prove real proxy credentials are
absent from a running container or validate TLS/remote daemon behavior.

**Additional known blocker:** the separate older `research_worker_preflight.py`
still uses the host Docker CLI config and may inject proxy credentials into its
container. Do not run it with credential-bearing proxy settings; fix and verify
its CLI config boundary separately before relying on it. The new isolation is
specific to `research_container.py` and is not a blanket guarantee for scripts.

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

## Current blockers and deferred work

- **Missing:** a real, contained agent doing multi-question reasoning over full supplied source; actual hostile-source/prompt-injection and private-data exfiltration tests, output validation, safe handoff and reuse/cleanup tests.
- **Approval blocker:** the host-side, no-secret-output xAI inference probe was not executed because its command approval was withdrawn. The operator must restore/explicitly grant the relevant command approval before any retry of that outcome. Do not bypass the approval by changing commands, using the built-in proxy, or another provider.
- **Host-native direction:** the child retains its existing authorized host provider; the task container runs tools only. No broker or model in Docker is required. A real adapter must attest exact effective child tools, leaf status and bound runtime identity; the present public lifecycle does not provide that proof. Source ingestion, a bounded untrusted parent handoff, and actual researcher workflow also remain unimplemented.
- **Trigger / next step:** after independent review and availability of the public attestation contract, integrate the host-native adapter and verify child isolation, source/citation handling and bounded handoff under expressly authorized model settings. The withdrawn xAI approval restriction above remains in force, including any attempt at the same outcome via another provider. Separately, only explicit restored approval permits the denied real descendant-lifetime fixture described above. Do not equate a prompt instruction, heuristic sanitizer, or this preflight with a security boundary.
- **Why it blocks:** this branch has not established a real restricted-child researcher, authorized end-to-end model operation, or the claimed privacy/injection and descendant-lifetime behaviors. It is not integration-ready.

## Historical interruption / resume handoff (superseded by new direction above)

The immutable implementation checkpoint is `81ea4a33fb4f29e255917c75e5d4eaa918a845de`; the later branch tip contains this dossier-only handoff. Resume from this worktree, rerun the exact preflight and full tests, then implement/verify the genuinely isolated agent path only after resolving the endpoint/credential boundary. Do not alter an active hunter. The branch remains unmerged and unpushed.

## Decision gates

- **Integration:** independent review and a real end-to-end agent run, including hostile-source, privacy, cleanup, explicit promotion and multi-question reuse tests, all passing.
- **Activation / promotion:** separate explicit user decision; this branch does not activate anything.
