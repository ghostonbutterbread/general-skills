# Safe-fetch scripts

- `safe_fetch.py` — quarantine and sanitize external content.
- `research_stdio.py` — harness-neutral, persistent JSON-lines process around
  one `ResearchContainer`; see the protocol below. It does not launch an agent.

## Persistent stdio protocol

From the **skill directory**, launch `python3 scripts/research_stdio.py`, or set
`SAFE_FETCH_SKILL_DIR` to that directory and run
`python3 "$SAFE_FETCH_SKILL_DIR/scripts/research_stdio.py"`. Keep one process
and its pipes open for one task. No model credentials or authentication are
involved. The first stdout message is a flushed `ready` event containing the
generated container name, before the process reads any request or starts a
container. The owning harness **must receive and durably retain that exact name
before sending `start`**, along with the identity of the original Docker daemon.
If it cannot retain the name, it must not send `start`. Requests are sequential
JSON objects, one per line; stdout then returns one flushed JSON object per
request, `{"op": ..., "result": {...}}`. Do not send another request until its
reply arrives. The process does not limit input line length; the harness must
bound input lines before forwarding them. The process does not enforce access
control: **every harness must independently enforce its child agent's effective
exclusive tool allowlist** and mediate who can write to the process. A harness
adapter is not supplied. This CLI alone does not restrict other agent tools.

```jsonl
{"op":"start"}
{"op":"execute","command":"printf 'hello\\n'","timeout":15}
{"op":"close"}
```

Example replies (the generated name varies):

```jsonl
{"op":"ready","result":{"container":"research-task-example"}}
{"op":"start","result":{"ok":true,"container":"research-task-example","network":"bridge"}}
{"op":"execute","result":{"ok":true,"exit_code":0,"timed_out":false,"output":"hello\n","truncated":false,"trust":"untrusted_container_output"}}
{"op":"close","result":{"container":"research-task-example","cleanup":"absent_at_check"}}
```

An unexpected transport exception may terminate the process before a reply;
check stderr and exit status rather than waiting indefinitely.

- `start` has no other fields. Its core result contains `ok`, `container` and
  `network` on success. Never wait for this reply to save the name: start may
  reach Docker and the process may die before returning the reply.
  Start once per process (a failed unsupported-daemon preflight may be retried).
- `execute` requires `command` (nonempty shell string, max 8192 characters);
  optional integer `timeout` is 1–60 seconds, default 15. The core result includes
  `ok`, `exit_code`, `output`, `timed_out`, `truncated`, and `trust` for a
  completed command. A nonzero exit is a completed command, not a broken session.
  Output is **untrusted**; the harness must constrain what reaches a model. Unlike
  the plugin's model-response wrapper, this wire envelope does not promise a
  32768-byte serialized JSON limit; JSON escaping can enlarge output.
- `close` has no other fields. The core result has `container` and `cleanup`.
  `not_started` or `absent_at_check` ends the process; other values leave it
  open for another `close`. Even `absent_at_check` is only a point-in-time
  observation. `unverified` and `absent_at_check_delayed_operation_possible`
  require continued exact-name reconciliation on the original daemon; a delayed
  operation may still appear later. Do not prune other containers.

Malformed JSON, non-object requests, unknown operations or extra fields return a
result with `ok: false`, `error`, and corrective `message`, without terminating
the session. Core errors are passed through unchanged: for example,
`invalid_command`/`invalid_timeout` require corrected inputs;
`unsupported_docker_daemon` requires supported local daemon configuration;
`start_failed_or_timed_out`, `command_timed_out`, and
`docker_exec_completion_unverified` require cleanup and reconciliation, not
blind re-execution. `container_not_running` requires a valid started task.

On EOF or an unexpected exception, the process attempts `close()` in `finally`
(unless already closed), and emits a JSON cleanup receipt to **stderr**, not an
extra stdout reply. Exit status is 0 only when cleanup is observed as
`not_started` or `absent_at_check` and no unexpected exception occurred;
otherwise it is 1. If cleanup itself raises, stderr gives the exact task name and
`unverified`. Capture stderr and process status. SIGTERM, SIGKILL and process
crashes are not guaranteed to run `finally`; cleanup is best effort. After
uncertain start or process death, the owner must reconcile the retained exact
name on the original daemon, including possible later daemon completion. One
absence check or cleanup receipt does not prove the daemon is quiescent.
The existing safe-fetch command and quarantine contract are unchanged.

## Core research container

- `research_container.py` — experimental host-side transport for a restricted
  native researcher; it does not itself launch a model or a subagent, and merely
  installing the file does not register a working researcher. Host-owned code creates a
  `ResearchContainer()`, calls `start()`, registers `register_tool(ctx,
  resolve_authorized_task)`, and always calls `close()` in `finally`, retaining
  its receipt. Exec creation, attached output and completion inspection use the
  host-only Docker Engine API on the selected local Unix socket. A completed
  `Running: false` / integer `ExitCode` response supplies the command status;
  ordinary nonzero exits (including 124/125/137) remain reusable. Output is never
  interpreted as status. Missing, malformed, failed or timed-out engine evidence
  marks the task uncertain and requires cleanup. This transport remains
  experimental and requires independent review before integration.
  `close()` also serves as cancellation: it shuts down active Engine socket I/O
  and bars subsequent phases once cancellation is observed, without waiting for
  the in-flight exec. A send racing with cancellation may already have reached
  the daemon; socket shutdown cannot retract a submitted or accepted operation.
  Task-local host
  timers request exact-name removal at 900 seconds after start and at one second
  after an in-flight command's deadline. Engine connect, HTTP headers, bodies and
  multiplex frames share the command's absolute host deadline (timeout plus the
  existing one-second grace); socket shutdown interrupts slow-trickled responses.
  `command_timed_out` is distinct from `docker_exec_completion_unverified`, and
  both require cleanup; a real command exit 124 remains an ordinary exit. Every
  uncertain exec requests asynchronous exact-name cleanup, including early socket
  timeouts. After an externally cancelled in-flight transport ends, it requests
  another attempt. Cleanup may fail, outlast the return, or fail to start if a
  host thread cannot be created; `cleanup_required` still requires caller action.
  These are best-effort process/thread deadlines, not hard real-time guarantees:
  OS scheduling, host filesystem/config access before Engine I/O, or a stuck host
  process can delay return, and a daemon may finish an operation after cutoff.
  A completed command's detached children
  can continue until task close/expiry; command timeout is NOT their lifetime
  bound. Never use this for work requiring per-command descendant isolation.
  Timers require a live host process and responsive daemon, and in-container
  sleep/`--rm` are not a trusted substitute after host death. Failed/timed-out
  Docker operations, cancellation, or an incomplete listing leave state uncertain;
  repeatedly call `close()` on the exact task instance/name and independently
  reconcile delayed daemon operations. An already-submitted operation can finish
  after both automatic attempts; neither attempt nor a single absence check proves
  that delayed daemon effects are impossible. Never prune other containers.
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
  socket, and Docker **bridge networking** for internet access. The bridge can
  also reach services exposed to it; it is not an internet-only firewall. Docker
  operations use a fresh private empty CLI
  config, preventing host-configured proxy/auth injection; host environment and
  host credentials are not explicitly passed to the container. Only default or
  explicit local Unix-socket Docker endpoints are supported; remote/TLS endpoints,
  named contexts, conflicting context/host overrides, and unreadable/malformed
  config fail closed rather than silently selecting another daemon. The selected
  socket is pinned for CLI lifecycle operations; changing selection while the task
  is active prevents exec and cleanup until the original selection is restored.
  The local `python:3.12-slim` tag is not digest-pinned;
  verify/trust the image and Docker host before use. The container can access
  the internet, but source transfer to a researcher is not yet implemented.
  Containers share the host kernel and do not guarantee defense against kernel
  or daemon vulnerabilities. Timeout uses a host watchdog, not the shell's `timeout`
  exit code; a watchdog expiry or unverified exec marks the task non-reusable and
  requires cleanup. `absent_at_check` is point-in-time only, while the explicit
  `absent_at_check_delayed_operation_possible` leaves state uncertain and every
  subsequent `close()` retries exact-name removal and inspection. Run the opt-in real test with
  `RESEARCH_DOCKER_TEST=1 PYTHONPATH="$PWD" python3 -m unittest discover -s tests -p test_research_container.py -v`.

Passing tests is not proof that a research-agent path exists. Full-source
ingestion, model calls, prompt injection and knowledge promotion by an actual
agent remain unverified.
