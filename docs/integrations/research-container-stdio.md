# Research-container stdio integration dossier

- **Status:** feature; revised protocol requires independent re-review before integration or release
- **Owner:** delegated Hermes subagent; parent owns integration/review
- **Branch:** `feat/research-container-stdio`
- **Worktree:** `/home/ryushe/worktrees/general-skills-research-stdio`
- **Base commit:** `cd5f8d05a6e67573a2b0567d404b0cb680af9a22` (fetched `origin/beta` when feature started)
- **Intended integration target:** `beta`; fetched target has advanced and integration compatibility must be checked by parent
- **Last updated:** 2026-11-16
- **Owning feature branch/ref:** `feat/research-container-stdio`
- **Latest immutable implementation/recovery checkpoint:** `a9be03b2e24e01b0d294b6ad44b11f3bfb7348e3` (ready-event fix); the branch tip contains a later dossier-only handoff commit.
- **Original feature implementation:** `51501a516382540ebcbbc8f837ea18121c4f3b6c`; prior handoff `ca72443784eefbd65bad31a3b9227dee1726a482`.
- **Inspiration / canonical references:** existing `skills/safe-fetch/scripts/research_container.py` and script README; independent reviewer found a process-death-before-start-reply cleanup gap.

## Intent and contract

Provide a small harness-neutral process interface to the existing task-scoped research transport. Preserve the core, safe-fetch command and quarantine contract. This is a transport, not a harness integration or an agent restriction.

`research_stdio.py` owns one core instance. It first writes and flushes `{"op":"ready","result":{"container":"<generated-name>"}}` before reading requests or invoking start. The harness must durably retain that exact name and the original daemon identity before sending `start`. Thereafter sequential JSON-lines `start`, `execute`, `close` requests return the core result in an envelope. Invalid input has an actionable error; completed nonzero commands remain reusable. Close retries remain possible while the process lives; EOF/exception calls close in `finally` and reports cleanup to stderr. SIGTERM, SIGKILL and process crashes do not guarantee cleanup; a single absence check cannot exclude a late daemon operation. Reconcile the exact name on the original daemon after uncertain start or process death. The harness must also bound input lines, exclusively allowlist the intended child tool, mediate its pipe, and constrain untrusted output. There is no adapter, credential access, model call, source-ingestion path, or end-to-end researcher claim.

## Evidence and review

Run from this worktree. Offline commands clear the opt-in real-Docker flag, use an unavailable Docker CLI PATH, and put this worktree first on the Python path:

- `env -u RESEARCH_DOCKER_TEST PATH=/nonexistent PYTHONPATH="$PWD/tests" /usr/bin/python3 -m unittest test_research_stdio.StdioTests.test_ready_name_is_flushed_before_blocking_start_and_sigterm -v` failed before the fix because no ready message arrived, then passed after the fix. This uses the real CLI script with injected fake core; it reads the flushed generated name before any start, sends start, waits until the fake start is blocked, and terminates the process with SIGTERM. It does not claim a real daemon operation or cleanup.
- `env -u RESEARCH_DOCKER_TEST PATH=/nonexistent PYTHONPATH="$PWD" /usr/bin/python3 -m unittest discover -s tests -p test_research_stdio.py -v`: 13 passed, including prebuffered request ordering, flush failure, sequential reuse, and fake-core subprocess.
- Same command with `test_research_container.py`: 24 passed, one opt-in real Docker test skipped.
- Same command with `test_research_engine.py`: 20 passed, fake Unix Engine.
- `printf '%s\n' '{"op":"close"}' | env -u RESEARCH_DOCKER_TEST PATH=/nonexistent /usr/bin/python3 skills/safe-fetch/scripts/research_stdio.py`: ready then close with the same name, `not_started`, exit 0; no Docker used.
- Parent reports an earlier real stdio Docker test of the **pre-ready protocol**: foreground HTTPS returned 200, exit 7 was followed by `printf REUSED`, and close reported `absent_at_check`. The first verifier had a case mismatch; a separate exact-new-name inspect passed. This is point-in-time evidence only, not evidence of daemon quiescence or a real-Docker test of the revised handshake. This worker did not run real Docker, touch the previously blocked container, or run withdrawn model/descendant probes.
- Independent complete-diff re-review after the ready fix remains required; the prior reviewer found the startup gap and has not approved this correction. Kanban CLI denied delegated child access previously; parent tracks this task.

## Blockers and deferred work

- **Independent re-review:** parent must arrange review of the complete candidate and corrected startup/cleanup contract before integration or release. In particular, validate that the owner saves the ready name before sending start and that uncertain/late operations are reconciled on the original daemon.
- **Revised-protocol live Docker test not run:** if separately authorized and needed, use a fresh task-owned container and the documented ready handshake; run a foreground HTTPS request and a nonzero-then-reuse check, capture the exact name before start, close and independently inspect only that name. One absence observation does not establish quiescence. Do not touch earlier containers or run withdrawn probes.
- **Integration / activation:** parent must reconcile the advanced beta ref, run appropriate integration checks and independently review before merge. Remove this branch-local dossier on accepted integration. A future harness-specific adapter must prove effective tool restrictions and own process/cleanup lifecycle. No runtime changed here; promotion requires separate approval.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/research-container-stdio`.
- **Resume point:** inspect the ready-event fix and evidence on the feature tip, obtain independent re-review, and reconcile against current `beta`; do not merge or deploy automatically.
- **Recovery checkpoint:** `a9be03b2e24e01b0d294b6ad44b11f3bfb7348e3`; inspect the later dossier-only handoff commit too.

## Decision record

- 2026-11-16 — Original feature authored on fetched beta; offline tests passed.
- 2026-11-16 — Parent reported the bounded pre-fix real Docker test and independent reviewer identified the missing early name. Add flushed ready event and offline process-death regression; independent re-review required.
