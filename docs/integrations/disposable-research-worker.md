# Disposable research worker — integration dossier

- **Status:** Engine cancellation and early timeout repairs have offline evidence; fresh independent review, prior cleanup approval, descendant-lifetime approval, and restricted-child integration remain blocked
- **Owner:** delegated Hermes worker
- **Branch / owning ref:** `feat/disposable-research-worker`
- **Worktree:** `/home/ryushe/worktrees/general-research-worker-20261115`
- **Base commit:** `20189521b6aab6997ebde5a353542af2e63848de` (fetched `origin/beta`)
- **Intended integration target:** `beta` (no integration authorized)
- **Last updated:** 2026-11-15
- **Latest immutable recovery checkpoint:** `c66ab070656d91737ab5d9b95ae4ea9c1c09c379` (Engine cancellation and cleanup correction); the branch tip includes a later dossier-only handoff commit.
- **Feature implementation commit(s):** `81ea4a33fb4f29e255917c75e5d4eaa918a845de` (preflight); `3cf82e6a87613201f3bd439ba35e166d469bd11c` (transport); `ff325e79dd60520fb97875eb6eb29e105bf6abce` (transport review corrections); `198466b27a2076ee1fdd1967f7bf7157c223d144` (transport re-review corrections); `48803abeb735f621bb63c2ddb1fa33cc6d8b5817` (fail-closed status checkpoint); `a499b1e618cb1002dc97d2f4b32c1c1fb8112b2e` (engine completion repair); `268a525cca7e87ba61dffea3d45761cc861afb5b` (absolute deadline repair)
- **Inspiration / canonical references:** `safe-fetch`, `sandbox-run`, Hermes provider and Docker documentation; General Skills owns the generic safe-fetch skill. BBH's target stores and live runtime were not modified.
- **Correction implementation:** `c66ab070656d91737ab5d9b95ae4ea9c1c09c379` on this feature branch; not propagated, merged, pushed, or activated.

## Cancellation and early Engine timeout correction

Independent review of `101b269` reproduced continued Engine exec phases after
`close()` and missing cleanup after an early socket timeout. The former occurred
because `close()` did not signal the active transport; the latter because the
caller cancelled the command watchdog when a timeout happened before the absolute
deadline. Added fake Unix Engine barrier tests were red at version, create,
start, and inspect (worker still blocked after close), and early timeout failed
to request cleanup.

The task now registers the active Engine socket with a cancellation object;
`close()` signals it and shuts down that socket, and each later phase checks the
signal. Any uncertain exec, including an early timeout, requests asynchronous
exact-name removal; a cancelled in-flight exec requests another attempt after
transport termination. A cleanup-thread start failure leaves the explicit
`cleanup_required` result and retryable uncertain state. No cancellation flag
can retract bytes already submitted to the daemon, including a send racing with
the flag. An accepted daemon request may finish after both cleanup attempts; the
fake Engine demonstrates this. Repeated exact-name `close()` and independent
reconciliation remain necessary; do not claim a proven container lifetime.

The isolated suite used `/usr/bin/python3`, a disposable HOME/XDG environment,
an empty PATH except a bash symlink (no Docker executable), repository-first
`PYTHONPATH`, and `-W error::ResourceWarning`: **100 tests, 99 passed, one
opt-in real-Docker test skipped**. The four barrier cases and early accepted-start
timeout each passed three additional runs. Tests include cancellation before
connect, cleanup thread start failure, bounded output and deadline, normal exit
0/1/7/124 and reuse; Engine and cleanup are fake/mocked. Prior test runs exposed
cross-test cleanup threads overlapping mocks; fixtures now join those threads.
There is no real-Docker end-to-end evidence for this correction. The named
previously blocked container was not inspected or retried; withdrawn descendant
and provider/model probes were not run. Fresh independent complete-branch review
is required, including the cancellation/send boundary, concurrent cleanup order,
and retained daemon uncertainty. The parent must arrange it; no nested reviewer
is available in this worker. No merge, push, or activation is authorized.

## Engine absolute-deadline repair (historical)

Independent review of `a499b1e` found that per-socket read timeouts restart on
incoming bytes, so `getresponse()` or chunk parsing could remain blocked after
the command watchdog had marked the task uncertain and requested cleanup. The
new fake Unix Engine regression on that revision failed in all three cases:
version headers, start headers and chunk metadata returned after **4.005 s,
4.011 s and 4.006 s** respectively for `timeout=1`, exceeding the test's 3.2 s
limit. The command was classified as cancelled, not timed out.

One absolute monotonic deadline, including the existing one-second grace, now
covers each Engine connection, request, headers, body and multiplex parser. A
deadline timer shuts down a duplicate socket to interrupt blocking buffered HTTP
reads even if `HTTPConnection` has detached the original. The timer and sockets
are closed/joined on both success and failure. A timeout returns
`command_timed_out`; transport/protocol failures remain
`docker_exec_completion_unverified`. The timeout watchdog still requests
asynchronous exact-name cleanup, including when the socket timer wins their race;
state stays uncertain, no partial output is returned, and cleanup remains
retryable. Normal Engine exit 0/1/7/124, reuse and output limits are unchanged.

After repair the three original regressions pass within 3.2 seconds each, as do
the pre-existing slow frame regression, delayed-connect-plus-header shared
deadline, timer-start failure, watchdog-race/failed-cleanup/retry, normal status,
malformed-frame, failure, reuse and cap cases. The regressions verify timeout
classification, lock release, no surviving test-created timer threads, cleanup
request, and refusal of reuse. They use a temporary Unix socket and mocked
Docker CLI, not a Docker daemon. Full local suite:
`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD" python3 -W error::ResourceWarning -m unittest discover -s tests -v`
ran **96 tests: 95 passed and one opt-in real-Docker test skipped**. The
three-phase trickle test and watchdog-race retry test each passed two additional
consecutive runs.

Limits: this is not a hard real-time guarantee. Scheduling, host config/filesystem
access and host-process failure can delay return; daemon work and cleanup can
outlive the return, require retries, and cannot be proven absent by one listing.
The changed transport has not been tested on a real Docker daemon and needs fresh
independent review of the complete branch and this correction. When separately
authorized, rerun the real foreground fixture in the next section; real timeout,
output-cap and retry evidence remains deferred. No previously blocked container,
descendant probe, provider or live target was inspected or exercised here. No
merge, push or activation was performed. Parent owns Kanban reconciliation.

## Historical engine completion repair

Host-only stdlib HTTP over a pinned local Unix Docker socket now negotiates the
Engine API version and performs exec create, attached start, bounded Docker
multiplexed output parsing, and exec inspect. Only a valid completed engine
inspection provides `exit_code`; output (including marker-like data) cannot.
Verified ordinary exit 0/1/7/124 remains reusable. Malformed, failed, timed-out,
or missing status becomes uncertain and requires owned-container cleanup. The
host watchdog remains responsible for timeout cleanup. Remote/TLS daemons, named
contexts, conflicting context/host settings, escaped socket paths, and changed
daemon selection fail closed; CLI create/removal uses the pinned daemon and an
empty isolated config. The container receives no socket, host credentials, or
model provider access. Resource limits and the existing restricted-child gate
remain unchanged.

Regression-first: the new fake Unix Engine lifecycle test failed against the
prior transport (`exit_code` was null). Regressions for unexpected HTTP success,
unsupported start/cleanup, and escaped daemon path were observed failing before
repair, as did the slow-trickle deadline regression. Fake-engine tests exercise
lifecycle, chunked multiplexing, forged marker, output caps, timeout, daemon
failures and malformed/incomplete status/frames. Full suite:
`PYTHONPATH="$PWD" python3 -W error::ResourceWarning -m unittest discover -s tests -v`
ran **92 tests, 91 passed, one opt-in Docker fixture skipped**.

The real foreground-only fixture command is `RESEARCH_DOCKER_TEST=1 PYTHONPATH="$PWD" python3 -W error::ResourceWarning -m unittest discover -s tests -p test_research_container.py -k test_real_foreground_reuse_and_exit_status -v`.
An earlier revision passed with `research-task-8c9e8abb24904e44af18f1f03fa3ba59`
returning 0, 1, 7, 0 and `absent_at_check`. On final code the same fixture's
new container `research-task-67f448b28e114fec8cc54b204f72f798` returned **0, 1,
7, 0** in order from one reused container, but the test **failed** because its
cleanup was `unverified`. A subsequent exact-name removal reported removal
already in progress; the following exact-name listing was empty. This is a
point-in-time observation, not proof that removal finished; the parent later
independently observed that exact container absent. No other names were
touched. Neither real fixture exercised nonempty output, 124, timeouts, escaped
descendants, a model, or a real child. Those failure and output checks above are
fake-engine tests, not real Docker proof.

**Still blocked:** prior cleanup of `research-task-6e66469dcca3431391590da088509230`
was denied and was not retried or reached differently; operator approval and
exact-name reconciliation are still needed. The denied descendant-lifetime probe
and model/provider probes were not run. Independent complete-diff review is still
required; exact-child allowlist attestation and host-native agent integration are
not implemented. Parent owns Kanban reconciliation (child cannot mutate board).
No merge, push, activation, or global configuration changes were made. Next:
independent review of the branch and evidence, then separately authorized cleanup
and restricted-child integration; never infer descendant isolation from foreground
completion. The previous status section is historical and superseded.

## Historical fail-closed completion checkpoint

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
