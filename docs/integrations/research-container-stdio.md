# Research-container stdio integration dossier

- **Status:** feature; review and real-Docker evidence pending
- **Owner:** delegated Hermes subagent; parent owns integration/review
- **Branch:** `feat/research-container-stdio`
- **Worktree:** `/home/ryushe/worktrees/general-skills-research-stdio`
- **Base commit:** `cd5f8d05a6e67573a2b0567d404b0cb680af9a22` (fetched `origin/beta`)
- **Intended integration target:** `beta`
- **Last updated:** 2026-11-16
- **Owning feature branch/ref:** `feat/research-container-stdio`
- **Latest immutable recovery checkpoint:** `51501a516382540ebcbbc8f837ea18121c4f3b6c` (implementation; a later dossier-only handoff commit follows)
- **Feature implementation commit(s):** `51501a516382540ebcbbc8f837ea18121c4f3b6c` (implementation; a later dossier-only handoff commit follows)
- **Inspiration / canonical references:** existing `skills/safe-fetch/scripts/research_container.py` and script README.

## Intent

Provide a small harness-neutral process interface to the existing task-scoped research transport. Preserve the core, safe-fetch command and quarantine contract. This is a transport, not a harness integration or an agent restriction.

## Implemented contract

`research_stdio.py` owns one core instance; sequential JSON-lines `start`, `execute`, `close` requests return the core result in an envelope. Invalid input has an actionable error; completed nonzero commands remain reusable. Close retries remain possible while the process lives; EOF/exception calls close in `finally` and reports cleanup to stderr. Cleanup can remain uncertain. The harness must exclusively allowlist the intended child tool, mediate its pipe, constrain untrusted output, and track exact-name cleanup. There is no adapter, credential access, model call, source-ingestion path, or end-to-end researcher claim.

## Evidence and review

- `env -u RESEARCH_DOCKER_TEST PATH=/nonexistent /usr/bin/python3 -m unittest discover -s tests -p test_research_stdio.py -v`: 10 passed; actual CLI subprocess uses fake transport and real core is exercised with mocked Docker/Engine.
- Same command with `test_research_container.py`: 24 passed, one opt-in real Docker test skipped.
- Same command with `test_research_engine.py`: 20 passed, fake Unix Engine.
- Actual CLI, no start: `printf '%s\n' '{"op":"close"}' | env PATH=/nonexistent /usr/bin/python3 skills/safe-fetch/scripts/research_stdio.py` returned `not_started`, exit 0.
- `git diff --check`: passed. Independent complete-diff review: pending parent assignment.
- Kanban CLI denied delegated child access; parent must track this task and link this dossier/branch.

## Blockers and deferred work

- **Missing evidence:** real foreground CLI → core → Docker bridge HTTPS request and exact-name cleanup, plus independent review. No approval for that real Docker action was supplied in this delegated context; no prior blocked container was touched. The withdrawn real model and detached-descendant probes were not run.
- **Fixture / environment:** after explicit approval, use this CLI to start its freshly generated unique task-owned container, execute a foreground Python HTTPS request to a valid public HTTPS endpoint, inspect its stdout/exit and close; capture its returned exact name and cleanup receipt. Independently reconcile only that exact name, including delayed-operation risk. Never inspect or act on any earlier container. Do not run existing opt-in tests blindly because their scope may differ from this approval.
- **Trigger:** explicit real Docker test approval and an available suitable daemon/image/network; obtain independent review from parent before integration.
- **Impact:** real Docker entrypoint/HTTPS and integrated researcher workflow remain unverified. No activation or E2E claim.
- **Next:** parent reviews branch; authorize bounded real test if desired; implement a separate harness-specific adapter with a proven effective child tool allowlist and process/cleanup lifecycle.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/research-container-stdio`
- **Latest immutable recovery checkpoint:** `51501a516382540ebcbbc8f837ea18121c4f3b6c` (implementation; a later dossier-only handoff commit follows)
- **Feature implementation commit(s):** `51501a516382540ebcbbc8f837ea18121c4f3b6c` (implementation; a later dossier-only handoff commit follows)
- **Exact resume point:** inspect branch diff and dossier, arrange independent review and approved real Docker test; do not merge or deploy automatically.
- **Working-tree state at handoff:** clean after committed handoff.

## Decision gates

- **Integration gate:** independent review; report missing live test or complete it with approval; remove dossier from beta on accepted merge.
- **Activation / cohort gate:** explicit future harness adapter and verified tool restrictions plus owner authorization; no runtime changed here.
- **Promotion gate:** separate explicit approval.

## Decision record

- 2026-11-16 — feature authored on fetched beta; offline tests passed; real Docker and independent review deferred.
