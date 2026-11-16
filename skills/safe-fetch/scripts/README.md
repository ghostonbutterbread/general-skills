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
  its receipt. Reuse that instance only for the same child/task. A start failure,
  timeout, cancellation, or uncertain cleanup requires exact-name follow-up;
  never prune other containers. The container self-exits after 900 seconds and
  uses Docker `--rm`, but daemon failure/delayed calls can still defeat timely
  cleanup. Output is returned to the child only, bounded to 32768 bytes and
  explicitly marked untrusted; `receipt()` omits command and output. Parent
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
  or daemon vulnerabilities. A command timeout marks the task non-reusable and
  requires cleanup. `absent_at_check` is point-in-time only, while the explicit
  `absent_at_check_delayed_operation_possible` warns that a timed-out daemon
  request can still race the check. Run the opt-in real test with
  `RESEARCH_DOCKER_TEST=1 PYTHONPATH="$PWD" python3 -m unittest discover -s tests -p test_research_container.py -v`.

A pass is only evidence for those observed checks; it is not a security audit,
model-authentication test, or proof that a research-agent path exists. The
probe does not test full-source ingestion, model calls, prompt injection,
knowledge promotion, reuse, or exfiltration resistance of an actual agent.
It does not authorize launching one. See the branch-local integration dossier for
blocked work and deferred end-to-end gates.
