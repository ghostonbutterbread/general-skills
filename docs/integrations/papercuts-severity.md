# Papercut severity and recurrence integration dossier

- **Status:** feature (review correction pending re-review)
- **Owner:** Hermes bugfix
- **Branch:** `feat/papercuts-severity`
- **Base commit:** `15a1fe2c6fbc3e2d4f6898ff62a25c25b55f3f94` (`origin/beta` fetched)
- **Intended integration target:** `beta`
- **Last updated:** 2026-10-15
- **Owning feature branch/ref:** `feat/papercuts-severity`
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commit(s):** none yet
- **Inspiration / canonical references:** user severity rubric; `skills/papercuts/{SKILL.md,references/capture.md,scripts/papercut.py}`

## Intent

Record agent-assigned severity at capture and count distinct subsequent incidents on the same underlying issue, with observed time and bounded automatic escalation. Never infer historical frequency from legacy records or test against the live shared record.

## Implemented contract

`add` requires severity, breaking flag, reason, incident ID, and observed minutes. `observe` is idempotent per entry/incident ID under the existing advisory lock; unrated legacy entries require first rating. At 3 incidents Low rises to Medium; at 5 blocked incidents or 60+ observed minutes rises to High; Critical is agent-only and requires a blocker reason. `list` sorts effective severity; `close` retains scoring history. Semantic duplicate matching remains agent judgment.

## Evidence and review

- Tests: `python3 -m unittest discover -s skills/papercuts/tests -v` — 6 passed after review fix; `python3 -m unittest discover -s tests -q` — 43 passed; `git diff --check` clean.
- Independent review: first pass failed on stale escalation reason after agent-assigned severity surpassed the automatic floor; added removal and Low→Medium→agent High→Critical regression. Re-review pending.
- Replay/cohort/fixture evidence: CLI subprocess E2E on a temporary copy of the actual shared record: preserved 815 pre-existing open entries, added one rated entry, observed four distinct subsequent incidents, escalated Low to High at 65 observed minutes, closed it, and verified live record unchanged. Additional concurrency and legacy-record fixtures in focused suite.
- Merge/ancestry evidence: pending.

## Blockers and deferred work

None known. Activation requires beta integration and runtime skill projection verification; no stable promotion requested.

## Interruption / resume handoff

- **Owning feature branch/ref:** `feat/papercuts-severity`
- **Latest immutable recovery checkpoint:** none yet
- **Feature implementation commit(s):** none yet
- **Exact resume point:** independent review, beta integration and runtime activation check.
- **Working-tree state at handoff:** intentionally uncommitted while implementation is in progress.

## Decision gates

- **Integration gate:** focused/E2E tests, independent review, clean beta target.
- **Activation / cohort gate:** verify installed skill and CLI resolve to integrated beta revision; avoid live-record test writes.
- **Promotion gate:** stable only on explicit owner direction.

## Decision record

- 2026-10-15 — created feature branch; focused, repository and copied-live-record E2E checks passed. Independent review identified stale escalation reason; fixed and reran 6 focused + 43 repository tests. Re-review pending.
