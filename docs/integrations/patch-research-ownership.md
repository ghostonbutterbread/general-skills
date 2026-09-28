# Patch research source-retirement integration dossier

- **Status:** feature
- **Owner:** Hermes Agent, Kanban `t_865b401d`
- **Branch / owning ref:** `feat/move-patch-research-bbh`
- **Base commit:** `ef526996809e75804015774490bc464c9cd7f8c0`
- **Intended integration target:** `beta`
- **Last updated:** 2026-09-28
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commits:** none yet
- **Inspiration:** Ryu requested BBH, not General Skills, to own patch research in Discord message `1554183415291707483`.

## Intent and implemented contract

Remove the superseded General Skills source, its index row and tests only after the receiving BBH skill is reviewed, tested and published. Do not leave two canonical export sources or change unrelated skills. The resulting runtime projection must be verified against BBH beta.

## Evidence and review

- Tests/commands: General Skills `python3 -m unittest discover -s tests -v` passed 40/40; `git diff --check` and `git diff --cached --check` passed; `git grep vulnerability-patch-research` found no remaining source references outside this dossier.
- Independent review: pending; verify BBH replacement exists and retains the parallel research contract.
- Merge/ancestry: source branch from beta; verify before integration.

## Blockers and deferred work

- **Missing evidence:** receiving BBH beta merge/push and BBH skill validation.
- **Command/fixture:** BBH targeted suite and remote beta ref readback.
- **Trigger:** after receiving-source independent review passes.
- **Why it blocks:** deleting General first would strand the active runtime link and router.
- **Next step:** merge/push BBH, then merge/push this deletion, then focused sync.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/move-patch-research-bbh`
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commits:** none yet
- **Exact resume point:** delete source skill/index/tests, test, commit, review, wait for receiving BBH publication, merge/push, sync.
- **Working-tree state at handoff:** feature branch, expected task-owned edits.

## Decision gates

- **Integration:** BBH receiving source published and deletion independently reviewed.
- **Activation:** managed symlinks repoint to BBH without unrelated profile prunes, fresh runtime loads BBH source.
- **Promotion:** beta only; no main promotion.

## Decision record

- 2026-09-28 — created for General Skills source retirement.
