# Patch research source-retirement integration dossier

- **Status:** feature
- **Owner:** Hermes Agent, Kanban `t_865b401d`
- **Branch / owning ref:** `feat/move-patch-research-bbh`
- **Base commit:** `ef526996809e75804015774490bc464c9cd7f8c0`
- **Intended integration target:** `beta`
- **Last updated:** 2026-09-28
- **Latest immutable recovery checkpoint:** `50a0f7b02f6ee47e7213b9a6a3bd48a438116563`
- **Feature implementation commits:** `50a0f7b02f6ee47e7213b9a6a3bd48a438116563`; current branch tip adds a later dossier-only receipt.
- **Inspiration:** Ryu requested BBH, not General Skills, to own patch research in Discord message `1554183415291707483`.

## Intent and implemented contract

Remove the superseded General Skills source, its index row and tests only after the receiving BBH skill is reviewed, tested and published. Do not leave two canonical export sources or change unrelated skills. The resulting runtime projection must be verified against BBH beta.

## Evidence and review

- Tests/commands: General Skills `python3 -m unittest discover -s tests -v` passed 40/40; `git diff --check` and `git diff --cached --check` passed; `git grep vulnerability-patch-research` found no remaining source references outside this dossier.
- Independent review: PASS on this deletion and paired receiving BBH commit (`4ad2380494972ea0ebfbd95fd335eb611db0c9a8`) by a read-only Claude CLI reviewer supplied both full diffs; no blocker. Recheck stale source references at beta tip before merging.
- Merge/ancestry: source branch from beta; verify before integration.

## Blockers and deferred work

- **Missing evidence:** receiving BBH beta merge/push and BBH skill validation.
- **Command/fixture:** BBH targeted suite and remote beta ref readback.
- **Trigger:** after receiving-source independent review passes.
- **Why it blocks:** deleting General first would strand the active runtime link and router.
- **Next step:** merge/push BBH, then merge/push this deletion, then focused sync.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/move-patch-research-bbh`
- **Latest immutable recovery checkpoint:** `50a0f7b02f6ee47e7213b9a6a3bd48a438116563`
- **Feature implementation commits:** `50a0f7b02f6ee47e7213b9a6a3bd48a438116563`; current branch tip adds a later dossier-only receipt.
- **Exact resume point:** wait for BBH beta publication, recheck references, merge deletion into clean current General beta (exclude this dossier), push/read back, then focused profile sync.
- **Working-tree state at handoff:** clean feature branch after dossier-only receipt.

## Decision gates

- **Integration:** BBH receiving source published and deletion independently reviewed.
- **Activation:** managed symlinks repoint to BBH without unrelated profile prunes, fresh runtime loads BBH source.
- **Promotion:** beta only; no main promotion.

## Decision record

- 2026-09-28 — created for General Skills source retirement.
- 2026-09-28 — deletion tests passed; independent read-only review PASS, but integration remains blocked until receiving BBH beta is published.
