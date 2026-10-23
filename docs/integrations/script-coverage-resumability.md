# Coverage-first script manager integration dossier

- **Status:** feature
- **Owner:** Hermes
- **Branch:** `feat/script-coverage-resumability`
- **Base commit:** `432b9949d90529cf6b0c6311cd5e4a9218207c98`
- **Intended integration target:** `beta`
- **Last updated:** 2026-10-23
- **Owning feature branch/ref:** `feat/script-coverage-resumability`
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commit(s):** none yet
- **Inspiration / canonical references:** Ryu's coverage-first script request; AI Policies resource safety.

## Intent

Make reusable corpus scripts preserve full input coverage while using bounded resources; avoid treating previews, timeouts, or output caps as complete runs.

## Implemented contract

The script-manager skill names the coverage-first contract: durable pending/failed IDs, resume, counts and stop reasons, safe resource pause; heuristic patterns remain non-exhaustive. No script implementation changes live in this repository branch.

## Evidence and review

- Tests and commands: `git diff --check` pending.
- Independent review: pending.
- Merge/ancestry evidence: branch from fetched `origin/beta` at `432b994`.

## Blockers and deferred work

- **Missing test or evidence:** independent policy review and beta-consumer verification.
- **Command / fixture / environment needed:** compare shared safety and BBH local policy; inspect diff.
- **Trigger to run it:** before integration.
- **Why it blocks integration, activation, or promotion:** conflicting rules can mislead script authors.
- **Next completion step / successor reference:** review, commit, integrate; separately release BBH implementations.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/script-coverage-resumability`
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commit(s):** none yet
- **Exact resume point:** wait for reviewer; resolve findings.
- **Working-tree state at handoff:** intentionally uncommitted pending review.

## Decision gates

- **Integration gate:** review, clean diff, beta integration verification.
- **Activation / cohort gate:** do not claim consumer activation from a local commit.
- **Promotion gate:** stable promotion requires explicit approval.

## Decision record

- 2026-10-23 — created from fetched beta.
