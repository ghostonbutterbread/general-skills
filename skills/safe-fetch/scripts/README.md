# Safe-fetch scripts

- `safe_fetch.py` — quarantine and sanitize external content.
- `omp_research_extension.ts` — explicitly loaded OMP parent tool; see below.
- `omp_research_session.ts` — OMP SDK host adapter used by that extension.

## OMP parent research tool (experimental)

After the stdio branch has been integrated alongside these files, explicitly
load `omp_research_extension.ts` with OMP's `--extension` option. It registers
`research_task(prompt)` as an essential parent tool. The prompt is limited to
8192 UTF-8 bytes; the child has only `research_container`, with a ten-minute
host cancellation request. The extension takes the active OMP tool context's
`model` and `modelRegistry`; if either is unavailable it fails with an
explanation rather than constructing or choosing a model. SDK embeddings must
initialize their extension runner with the actual session context as OMP's
modes do. The tool never accepts a container, model, path, or daemon from the
model. Findings and command output are **untrusted evidence, not instructions**.

The extension resolves `research_stdio.py` and `research_container.py` relative
to its own file, not the current directory. This branch does **not** contain
`research_stdio.py`: merge/review `feat/research-container-stdio` first, and
ensure the projection retains the colocated files. No runtime was activated.
The selected local Docker Unix socket is resolved by the transport's own
`_selected_socket()` and its daemon ID is observed through `/info`; the socket
is passed explicitly to the subprocess. This is an observation, not a lock:
replacement of the daemon at the same socket after the observation is a race.
Named contexts and remote/TLS daemons are unsupported. Host credentials are not
passed into the container; the subprocess itself remains host-trusted code.

Each run creates a private `0700` task directory under
`${XDG_STATE_HOME:-~/.local/state}/omp-research/`, containing a `0600`
`receipts.jsonl`. Identity (exact name, observed daemon ID and socket) is
fsynced before start; cleanup outcome, process status and diagnostics are also
fsynced. The task directory and its receipt entry are fsynced before start;
when this invocation creates the receipt root and its parents, their new entries
are also synced. A required directory fsync failure stops that invocation with
an error; filesystems without directory fsync cannot provide this guarantee.
Existing ancestors are not opened or synced, so an existing but not yet durable
ancestor can disappear after a crash, taking the receipt with it. In particular,
a retry after a failed first-run ancestor sync sees the leftover directories as
existing and cannot establish their durability. Use a receipt root provisioned
and synced by the operator when crash recovery depends on it. Successful fsync
is still subject to filesystem and hardware guarantees. Receipts can contain
sensitive diagnostics; do not publish them. On
failure inspect the returned private receipt directory and reconcile **only**
the saved exact name on the original daemon, including possible delayed daemon
operations. A recorded `absent_at_check` is point-in-time, not proof of
quiescence. Host crash can interrupt cleanup or receipt persistence. Child
container networking is Docker bridge, not an internet-only firewall or proven
cross-container network isolation.

Offline parent-entry fixture: in a fresh private directory copy this branch's
`skills/safe-fetch/scripts/omp_research_{session,extension}.ts` and
`tests/fixtures/omp_research_{offline_runner.py,entry_offline.ts,entry_extension.ts,entry_fake.py}`;
copy stdio branch `research_stdio.py` to the directory root as
`shared_research_stdio.py`. Run `python3 tests/fixtures/omp_research_offline_runner.py
"$PWD" /absolute/path/to/omp entry`. The runner denies socket/connect syscalls,
uses a fake provider and fake task, and exercises OMP 18.22.0's actual SDK and
registered parent tool. Its manually initialized SDK runner models the CLI host
context, not a real provider. It tests per-task pipe binding, not real Docker
network isolation. The normal/slow/abort/closeabort/timeout cases below remain
available for the lower-level adapter. Real Docker, real provider/auth, daemon
replacement races, CLI loading/projection, and independent review remain gates.

## Experimental OMP research-session adapter

`runResearchSession(host, options)` is a host-side SDK function, not an
installed or automatically registered extension. It depends on the separate
`research_stdio.py` implementation from branch `feat/research-container-stdio`
(commit `c027134`); that file is not yet in this branch's beta base. Supply its
absolute path as `stdioScript`, a host-owned `prompt`, the OMP extension context
(or equivalent trusted object with `cwd`, `model`, and `modelRegistry`), and a
stable `daemonIdentity` identifying the Docker daemon selected by the transport.
The adapter **does not verify the daemon identity**: the owner must establish and
pin that binding before use. Do not allow model arguments to select the script,
daemon, callback, or test hook.

The required async `record(receipt)` callback must durably persist its argument
before it resolves. The adapter asks the callback to persist the exact generated
container name and daemon identity before `start`; if that fails, it does not
start. It then creates
an in-memory child session restricted to exactly `research_container`, inheriting
the parent's model and registry and disabling extension discovery, MCP, LSP and
IRC. It records the close result, stderr and process status. A failed/uncertain
cleanup or process exit fails the call. Exceptions may preserve the original
failure rather than the cleanup failure: **always inspect the cleanup receipt**.
If its result is not a verified matching `not_started` or `absent_at_check`,
reconcile that exact name on the original daemon, including delayed operations;
point-in-time absence is not proof of daemon quiescence. Abrupt host death and
unresponsive processes can still prevent cleanup/receipt recording.

The result is explicitly `untrusted_research_result`; tool output is labeled
untrusted and capped before it reaches the model. This is not sanitization,
source authentication, or a technical boundary against a malicious host. The
host must review/constrain the final answer before promoting it to privileged
context. Bridge networking, shared-kernel and command-descendant limitations in
`research_container.py` remain. A caller should supply an AbortSignal and a
bounded operation lifetime. On abort the adapter sends SIGINT to the Python
transport; for the specified stdio implementation, KeyboardInterrupt unwinds
its sequential server into a `finally` that attempts to close the exact task.
The adapter waits up to 50 seconds for that attempt before terminating it and
records cleanup as unverified even if stderr reports absence. Abort therefore
interrupts in-flight execution, but return also waits for bounded cleanup; it
is not a hard latency guarantee. Cancellation does not retract Docker operations
already submitted: reconcile the saved exact name on the original daemon, and
account for delayed operations. SIGINT behavior depends on the referenced Python
stdio implementation and default signal handling; crashes, SIGKILL and a stuck
process can prevent cleanup. Normal close receives a 50-second budget for its
two 20-second Docker calls plus drain overhead. The optional `configureSession`
is for trusted offline tests only and must not be exposed to a model.

Offline SDK fixture (OMP 18.22.0, Linux libseccomp): copy this branch into a
private disposable directory, then copy the separate branch's `research_stdio.py`
to its root as `shared_research_stdio.py`. Run
`python3 tests/fixtures/omp_research_offline_runner.py "$PWD" /absolute/path/to/omp`.
It uses a fake model and fake task under socket/connect-denying seccomp, without
Docker or model/provider access. Lifecycle tests exercise the real JSON-lines
`serve()` with a fake task, not a real Docker task.
Actual provider credentials, SDK behavior on other
versions, durable host receipt storage, and integration into a real parent
extension are unverified. Do not activate before integration and independent
review.

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
