# OMP research-session integration dossier

- **Status:** blocked experiment; not reviewed or activated
- **Owner:** delegated Hermes worker; parent owns integration
- **Branch:** `feat/omp-research-session`
- **Base commit:** `f17eaa16e90ddfc14bfb9de5f74065900c8e4a04`
- **Intended integration target:** `beta`
- **Last updated:** 2026-11-17 UTC
- **Owning feature branch/ref:** `feat/omp-research-session`
- **Latest immutable recovery checkpoint:** `3d9f56d1cdc233af8b79fa4dc31ada1ef71004e2` (implementation; this branch also contains a later dossier-only handoff commit)
- **Feature implementation commit(s):** `3d9f56d1cdc233af8b79fa4dc31ada1ef71004e2`
- **Inspiration / canonical references:** OMP 18.22.0 installed on Hoster; stdio branch `feat/research-container-stdio` at `c027134`.

## Intent

Connect one shared host-owned research stdio process to a restricted OMP SDK
session; inherit the parent model/provider, preserve container identity before
start, and keep research output untrusted. No integration or activation is
in scope for this branch.

## Implemented contract

`skills/safe-fetch/scripts/omp_research_session.ts` exports a host-only async
adapter. The owner supplies trusted parent context, script path, daemon identity,
durable receipt callback and prompt. It starts one process, creates a separate
in-memory restricted SDK session with one custom tool, closes, checks the receipt
and returns explicitly untrusted text. Daemon identity is a caller assertion.
No production extension registers the function, supplies durable storage, or
selects/verifies the Docker daemon; this branch alone does not provide a usable
production research tool. It depends on the separate stdio branch.

## Evidence and review

- Hoster via the explicitly authorized Tailscale address; no LAN alias.
- OMP 18.22.0 compiled bundle's extension-context implementation supplies
  `cwd`, `modelRegistry`, and a `model` getter. Its SDK uses the supplied
  `modelRegistry` and derives default credential resolution from its resolver.
- `python3 tests/fixtures/omp_research_offline_runner.py <private-root> /home/ryushe/.local/bin/omp`
  on Hoster: **PASS**, socket and connect syscalls blocked by seccomp, isolated
  HOME, installed bundled mock model, fake container task. Exact advertised
  and active tool, rejected built-in, identity-before-start, receipt failure,
  unverified cleanup, trust marker and parent model/registry object inheritance
  were checked. Tested both stand-in protocol and real `research_stdio.py`
  `serve()` from `c027134` against FakeTask (no Docker). OMP's exit 1 after
  successful fixture is expected because isolated HOME has no default model.
- Independent review: not performed; required before integration.
- Project Kanban CLI: `delegate_task child contexts cannot mutate Kanban tasks or boards`;
  parent must update the existing task. This permission issue is separate from
  SDK and SSH connectivity.

## Blockers and deferred work

- **Missing:** actual parent extension registration, durable receipt backend,
  verified daemon selection/binding, and integration with shared stdio branch.
  **Trigger:** parent integrates both branches and provides trusted host wiring.
  **Why:** current callback and daemon identity are host-supplied assertions.
- **Missing:** real model/provider authentication and request behavior. Static
  bundle and fake prove object inheritance, not provider credentials, custom
  provider hooks, account routing, billing, or a real request. **Trigger:** only
  explicit renewed authorization for real model access; then exercise the actual
  entry point with a permitted provider and verify the received model identity.
- **Missing:** actual Docker/end-to-end cancellation and uncertainty tests,
  durable recording on host death, and independent security/reliability review.
  **Trigger:** separate approval and safe supported test environment; no Docker,
  targets, previously forbidden descendant probe, or real model was used here.
- `configureSession` is a trusted test hook; it must not be accessible to the
  child or model. Tool restrictions do not sandbox malicious host code. Delayed
  daemon operations and cleanup uncertainty still need exact-name reconciliation.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/omp-research-session`
- **Latest immutable recovery checkpoint:** `3d9f56d1cdc233af8b79fa4dc31ada1ef71004e2` (implementation; this dossier is a later handoff-only commit)
- **Feature implementation commit(s):** `3d9f56d1cdc233af8b79fa4dc31ada1ef71004e2`
- **Exact resume point:** review this diff and the stdio dependency, wire a
  trusted parent and durable receipts, and obtain only separately authorized
  real integration evidence. Do not merge, activate, or assume actual provider
  or Docker success from the offline test.
- **Working-tree state at handoff:** see final Git status.

## Decision gates

- **Integration:** reconcile stdio dependency, independent review, validate
  host wiring and exact-daemon identity/cleanup contract.
- **Activation:** explicit authorization plus evidence for the real workflow.
- **Promotion:** separate operator decision.

## Decision record

- 2026-11-17 UTC — offline SDK adapter experiment; real provider and Docker
  deliberately not accessed. Retain this dossier until the feature is integrated,
  rejected, or superseded.
