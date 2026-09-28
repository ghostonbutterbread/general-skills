# Relocate report-writing skills to BBH integration dossier

- **Status:** feature
- **Owner:** Hermes Agent
- **Branch:** `chore/move-reporting-skills-to-bbh`
- **Base commit:** `7b2f85e2387cad187e4ffc85fe9fbe42d408255f`
- **Intended integration target:** `beta`
- **Last updated:** 2026-09-28
- **Owning feature branch/ref:** `chore/move-reporting-skills-to-bbh`
- **Latest immutable recovery checkpoint:** `db3fd07` (General Skills source cleanup)
- **Feature implementation commit(s):** `db3fd07`
- **Inspiration / canonical references:** BBH feature `feat/canonical-report-writing-skill`, base `74db077`.

## Intent

Retire the two General Skills report-writing definitions after BBH receives a single canonical capability. Keep unrelated general skills unchanged.

## Implemented contract

Remove `security-reporting` and `evidence-first-vulnerability-reporting` source folders and expected-layout entries; README points at BBH ownership. Do not activate removal before the BBH skill is integrated and verified.

## Evidence and review

- Tests and commands: General Skills skill-layout tests (4) and `git diff --check` passed; cross-repository reference audit and independent review pending.
- Independent review: CHANGES on paired migration — BBH Evidence Report minimum structure restored on receiver; profile-local duplicate cleanup remains activation gate.
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
- **Latest immutable recovery checkpoint:** `db3fd07` (General Skills source cleanup)
- **Feature implementation commit(s):** `db3fd07`
- **Exact resume point:** integrate after BBH receiver is verified; then reconcile runtime projections and local duplicates.
- **Working-tree state at handoff:** clean after dossier follow-up; confirm at handoff.

## Decision gates

- **Integration gate:** BBH beta contains receiver and independent review passes.
- **Activation / cohort gate:** no old General Skills source projection; BBH symlink and fresh load verified.
- **Promotion gate:** beta only; no stable promotion requested.

## Decision record

- 2026-09-28 — BBH selected canonical report-writing owner; General Skills cleans up duplicate skills.
- 2026-09-28 — Independent re-review confirmed receiver's Evidence Report structure and General Skills checkpoint. Accepted for beta integration after BBH receiver; profile-local duplicate cleanup remains activation gate.
