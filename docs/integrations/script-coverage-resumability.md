# Coverage-first script manager integration dossier

- **Status:** review-ready
- **Owner:** Hermes
- **Branch:** `feat/script-coverage-resumability`
- **Base commit:** `432b9949d90529cf6b0c6311cd5e4a9218207c98`
- **Intended integration target:** `beta`
- **Last updated:** 2026-10-23
- **Owning feature branch/ref:** `feat/script-coverage-resumability`
- **Latest immutable recovery checkpoint:** `6b056ac`
- **Feature implementation commit(s):** `faf9d55`, `6b056ac`
- **Inspiration / canonical references:** Ryu's coverage-first script request; AI Policies resource safety.

## Intent

Make reusable corpus scripts preserve full input coverage while using bounded resources; avoid treating previews, timeouts, or output caps as complete runs.

## Implemented contract

The script-manager skill names the coverage-first contract: durable pending/failed IDs, resume, counts and stop reasons, safe resource pause; heuristic patterns remain non-exhaustive. No script implementation changes live in this repository branch.

## Evidence and review

- Tests and commands: `git diff --check` passed after reviewer corrections.
- Independent review: first review's three findings were corrected; independent re-review accepted all three policy changes with no concrete conflicts.
- Merge/ancestry evidence: branch from fetched `origin/beta` at `432b994`; target still at that revision.

## Blockers and deferred work

- **Missing test or evidence:** fresh consumer activation is not established by this local change.
- **Command / fixture / environment needed:** managed runtime read-back after separately approved activation.
- **Trigger to run it:** when activating the selected General Skills beta lane.
- **Why it blocks integration, activation, or promotion:** does not block beta integration; blocks an activation claim.
- **Next completion step / successor reference:** merge reviewed policy, verify integrated beta; separately release BBH implementations.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/script-coverage-resumability`
- **Latest immutable recovery checkpoint:** `6b056ac`
- **Feature implementation commit(s):** `faf9d55`, `6b056ac`
- **Exact resume point:** commit this accepted-review handoff, integrate into beta, remove dossier there.
- **Working-tree state at handoff:** clean after this dossier commit.

## Decision gates

- **Integration gate:** review, clean diff, beta integration verification.
- **Activation / cohort gate:** do not claim consumer activation from a local commit.
- **Promotion gate:** stable promotion requires explicit approval.

## Decision record

- 2026-10-23 — created from fetched beta.
