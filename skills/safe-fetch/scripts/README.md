# Safe-fetch scripts

- `safe_fetch.py` — quarantine and sanitize external content.
- `research_worker_preflight.py` — **experimental diagnostic only**, not a
  research agent. Run `python3 research_worker_preflight.py --timeout 20` to
  probe a fixed locally available `python:3.12-slim` Docker image. No network,
  host mounts, caller commands, live credentials, or image pulls are requested.
  It tests non-root UID, read-only root mount, a host-file canary, an environment
  canary, and the network namespace, then removes only its generated container.
  It exits nonzero on missing/failed checks or uncertain cleanup. Cleanup's
  `absent_at_check` is a point-in-time observation, not proof against a delayed
  daemon operation after a timeout; recheck that exact name if Docker stalls.

- `research_container.py` — experimental host-side transport for a restricted
  native researcher; it does not itself launch a model or a subagent. It is not
  automatically installed or activated. Host-owned code creates a
  `ResearchContainer()`, calls `start()`, registers `register_tool(ctx,
  resolve_authorized_task)`, and always calls `close()` in `finally`, retaining
  its receipt. Reuse that instance only for the same child/task. `close()` also
  serves as cancellation and does not wait for an in-flight exec. Task-local host
  timers request exact-name removal at 900 seconds after start and at one second
  after an in-flight command's deadline. A completed command's detached children
  can continue until task close/expiry; command timeout is NOT their lifetime
  bound. Never use this for work requiring per-command descendant isolation.
  Timers require a live host process and responsive daemon, and in-container
  sleep/`--rm` are not a trusted substitute after host death. Failed/timed-out
  Docker operations, cancellation, or an incomplete listing leave state uncertain;
  repeatedly call `close()` on the exact task instance/name and independently
  reconcile delayed daemon operations. Absence at a single check cannot establish
  that a timed-out create will not appear later. Never prune other containers.
  The entire model-visible serialized JSON response is capped at 32768 UTF-8
  bytes with truncation flagged; output is explicitly untrusted and `receipt()`
  omits command and output. Parent
  must separately constrain/review the child's final result as untrusted data;
  this transport does not sanitize arbitrary natural-language summaries.

  **Integration gate:** registration alone never restricts host tools. With no
  resolver the tool fails closed. The host-supplied resolver MUST use trusted
  runtime identity (Hermes currently passes `task_id` and `session_id` in handler
  kwargs), verify a live bound child is a leaf and its *effective* tool names are
  exactly `research_container`, and return only that child's container. Model
  arguments and self-asserted IDs are not proof. The current public lifecycle
  does not expose this proof: do not provide a permissive resolver or launch a
  child until the new core exact-allowlist lifecycle exists and its semantics are
  verified. Match the eventual real public contract, do not assume API names.
  Parent must handle lifecycle cancellation and cleanup and prevent cross-task
  resolver use and concurrent rebinding. This seam is host-trusted code, not an
  authorization boundary against a malicious host plugin.

  The tool schema is `research_container(command: string, timeout: int=15)`;
  timeout range is 1–60 seconds. Commands run as UID 65534, read-only root,
  bounded tmpfs, no capabilities, resource limits, no host mounts or Docker
  socket, and **network none**. No credentials or host environment are passed
  into the container. The local `python:3.12-slim` tag is not digest-pinned;
  verify/trust the image and Docker host before use. Network is intentionally
  unavailable; public fetch and full-source transfer are not implemented.
  Containers share the host kernel and do not guarantee defense against kernel
  or daemon vulnerabilities. Exit 124 or 137 may be a command's own exit and is
  reported as ambiguous, not definitive timeout. Such a result, a host watchdog
  expiry, or an exec client error marks the task non-reusable and requires cleanup.
  `absent_at_check` is point-in-time only, while the explicit
  `absent_at_check_delayed_operation_possible` leaves state uncertain and every
  subsequent `close()` retries exact-name removal and inspection. Run the opt-in real test with
  `RESEARCH_DOCKER_TEST=1 PYTHONPATH="$PWD" python3 -m unittest discover -s tests -p test_research_container.py -v`.

A pass is only evidence for those observed checks; it is not a security audit,
model-authentication test, or proof that a research-agent path exists. The
probe does not test full-source ingestion, model calls, prompt injection,
knowledge promotion, reuse, or exfiltration resistance of an actual agent.
It does not authorize launching one. See the branch-local integration dossier for
blocked work and deferred end-to-end gates.
