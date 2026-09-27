# Bitwarden load trigger

- Owner: Hermes; task `t_d5d8b184`.
- Branch: `fix/bitwarden-load-trigger`; worktree: `general-skills-bitwarden-load`.
- Base: `origin/beta` at `7b7d048416a0ed6c95dab5423d2f3dc823ab29a0`; target: `beta`.
- Defect: skill metadata and opening trigger limited discovery to an explicit request or an account-registry-selected login step, allowing agents to use Bitwarden without loading its safety workflow.
- Contract: agents load `bitwarden` before any owned-account vault operation, including status, lookup, mutation, or credential use; delegated agents receive the same trigger. Account-registry still owns login/recovery order.
- Scope: `skills/bitwarden/SKILL.md`, focused regression in `tests/test_skill_layout.py`, and this temporary branch-local handoff.
- Policy alignment: checked `account-registry` and `account-manager` routes; Bitwarden owns vault usage, not login/recovery order. No competing trigger found.
- Evidence: repository unittest suite 39 passed before adding the focused regression; `git diff --check` passed. Rerun full suite after regression; independent review pending.
- Activation: only after reviewed integration to the selected source lane, active projection verification, and fresh-session load. No stable promotion intended.
- Next: validate, review, integrate, remove this dossier from beta, and verify live projection.
