# Relocate report-writing skills to BBH integration dossier

- **Status:** feature
- **Owner:** Hermes Agent
- **Branch:** `chore/move-reporting-skills-to-bbh`
- **Base commit:** `7b2f85e2387cad187e4ffc85fe9fbe42d408255f`
- **Intended integration target:** `beta`
- **Last updated:** 2026-09-28
- **Owning feature branch/ref:** `chore/move-reporting-skills-to-bbh`
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commit(s):** none yet
- **Inspiration / canonical references:** BBH feature `feat/canonical-report-writing-skill`, base `74db077`.

## Intent

Retire the two General Skills report-writing definitions after BBH receives a single canonical capability. Keep unrelated general skills unchanged.

## Implemented contract

Remove `security-reporting` and `evidence-first-vulnerability-reporting` source folders and expected-layout entries; README points at BBH ownership. Do not activate removal before the BBH skill is integrated and verified.

## Evidence and review

- Tests and commands: General Skills skill-layout tests (4) and `git diff --check` passed; cross-repository reference audit and independent review pending.
- Independent review: pending.
- Replay/cohort/fixture evidence: none; source ownership change only.
- Merge/ancestry evidence: pending.

## Blockers and deferred work

- **Missing test or evidence:** BBH published beta skill and safe runtime projection swap.
- **Command / fixture / environment needed:** paired beta source commits and profile-scoped synchronizer dry-run/adopt; fresh consumer load.
- **Trigger to run it:** after BBH review and integration.
- **Why it blocks integration, activation, or promotion:** old General Skills source cannot be removed until the receiver exists.
- **Next completion step / successor reference:** verify receiver, integrate cleanup, synchronize profiles.

## Interruption / resume handoff

- **Owning feature branch/ref:** `chore/move-reporting-skills-to-bbh`
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commit(s):** none yet
- **Exact resume point:** complete review, commit, then integrate after BBH.
- **Working-tree state at handoff:** intentionally uncommitted until first checkpoint.

## Decision gates

- **Integration gate:** BBH beta contains receiver and independent review passes.
- **Activation / cohort gate:** no old General Skills source projection; BBH symlink and fresh load verified.
- **Promotion gate:** beta only; no stable promotion requested.

## Decision record

- 2026-09-28 — BBH selected canonical report-writing owner; General Skills cleans up duplicate skills.
