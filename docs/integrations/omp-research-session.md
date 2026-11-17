# OMP research-session integration dossier

- **Status:** feature candidate; independent review and integration deferred to parent. Not activated.
- **Owner:** delegated Hermes worker; parent owns integration, Kanban and review.
- **Branch:** `feat/omp-research-session`.
- **Base:** `f17eaa16e90ddfc14bfb9de5f74065900c8e4a04`; intended integration target `beta`.
- **Previous recovery checkpoint:** `3cb3aecf975873e733c47f9e15167251b180043c`.
- **Dependency:** `feat/research-container-stdio` tip `2fa728f`; its `research_stdio.py` is not present on this branch. The two features need explicit combined integration and review.

## Intent and implemented contract

`omp_research_extension.ts` is a real OMP extension factory registering the
essential parent tool `research_task`. It consumes a bounded prompt and obtains
`model`, `modelRegistry` and `cwd` from the actual extension tool context. It
fails closed with an actionable error if the model or registry is missing; it
never guesses a model. The extension invokes the existing adapter with a
restricted in-memory child whose only tool is `research_container`, labels
findings as untrusted, passes cancellation, and requests cancellation after ten
minutes. Tool input cannot pick a path, daemon, model, receipt callback or child
identity. The optional constructor hooks are trusted test-only dependencies,
not exposed to a model.

The extension resolves colocated stdio relative to its own file, uses the core's
local socket selector and observes the daemon ID via `/info`, and pins the
socket path in the transport subprocess environment. Its private per-task
0600 JSONL receipt records and fsyncs exact container and observed daemon
identity before start, and records the cleanup result and process outcome. The
private task directory and parent entry are fsynced. Parent-readable findings are
untrusted data, not instructions. Host credentials are not mounted or otherwise
explicitly passed to the container.

The socket/daemon ID check is an observation, not exclusion against a daemon
replacement at the same socket. Cleanup can be uncertain; a single absence check
is not quiescence. The bridge network can reach other bridge-accessible services;
per-task process/pipe binding does not establish network isolation. No service,
profile, model credential, target or real container was modified.

## Evidence

- Hoster `/home/ryushe/.local/bin/omp --version`: `omp/18.22.0`.
- Hoster user-systemd unit `hoster-omp-entry-fixture-cdma` exited success. Its
  command was `python3 tests/fixtures/omp_research_offline_runner.py <fresh-private-root> /home/ryushe/.local/bin/omp entry`; it copied stdio from the separate feature and used its actual `serve()` with a fake task. The runner verified seccomp denied socket and connect (EPERM), isolated HOME, and required the `OMP ENTRY OFFLINE PASS` marker. OMP exit 1 after that marker was expected because no default model was configured in the isolated HOME.
- The production extension also loaded by path into an OMP SDK parent and
  registered `research_task` as an active tool. The OMP SDK parent then loaded
  the same registration via an offline test wrapper;
  the fixture initialized the SDK extension runner's context as an embedding host
  must. Parent mock called the registered entry and a mock child called the real
  custom-tool adapter. It checked same model/registry object identity; only the
  custom child tool was advertised; `bash`, `read` and `task` were denied;
  returned evidence carried trust labels; normal, unverified-close and parent
  cancellation paths recorded matching private identity/cleanup receipts.
- Two fake tasks had unique names and separate pipes. A child supplied the first
  task's name as an extra container argument during the second task: OMP 18.22
  stripped the extra property rather than rejecting the call, and the command
  still ran only on the second fake task's bound pipe. This is not a test of
  actual container or network separation.
- Regression: Hoster user-systemd unit `hoster-omp-adapter-closeabort-uxpt`
  passed the existing adapter fixture with network syscalls denied, including
  abort during normal close, receipt persistence, and unverified cleanup.
- Earlier adapter-only tests and review are retained in Git history at
  `3cb3aec`. Independent review accepted its cancellation fix according to the
  parent handoff; this new entry and complete diff still require independent review.
- Hoster cleanup-sidecar inspection ran separately, no eligible scope; it retained
  one unregistered, live scope (needs-attention context, no action taken).

## Blockers / next action

1. Parent: independently review the complete feature and stdio dependency,
   especially daemon observation/replacement, receipt durability and cleanup,
   OMP extension context and scope of untrusted output. Integrate against the
   current beta only after combined tests and explicit dependency reconciliation.
2. The offline test injects fake daemon selection and a fake task. Real daemon
   `/info`/selection, CLI extension loading from the actual projected skill,
   actual Docker lifecycle and public HTTPS remain unverified. Repeat on a fresh
   task-owned container only when a responsive daemon is available and the parent
   authorizes it; preserve exact-name receipts and do not touch earlier blocked
   containers. No real provider/model inference is authorized; verify separately
   only after explicit renewed approval.
3. Do not claim model/provider auth behavior, cross-container network isolation,
   daemon replacement safety or crash-proof cleanup from the fixture. Review
   bridge access and daemon identity race before any activation.
4. No merge, push or activation is authorized by this feature commit. Remove the
   branch-local dossier on accepted integration. Parent handles Kanban.
