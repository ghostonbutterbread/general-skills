# Bitwarden CWD-independent helper paths — integration dossier

- **Status:** feature (pending independent review)
- **Owner:** Hermes bugfix subagent
- **Branch / owning ref:** `fix/bitwarden-cwd-paths`
- **Worktree:** `/home/ryushe/projects/.worktrees/general-skills-bitwarden-cwd-paths`
- **Base commit:** `15a1fe2c6fbc3e2d4f6898ff62a25c25b55f3f94` (fetched `origin/beta`)
- **Intended integration target:** `beta`
- **Last updated:** 2026-10-15
- **Latest immutable recovery checkpoint:** `99d05d3` (implementation + regression + initial dossier)
- **Feature implementation commit(s):** `99d05d3`
- **Inspiration / canonical reference:** papercut `PC-20261002-194658-6a522803`; `skills/bitwarden/SKILL.md`

## Intent and contract

The documented `skills/bitwarden/scripts/...` commands resolve against the caller's CWD, not the installed skill. The BBH checkout has neither path; both helpers exist under the installed skill. Point both script examples to the same absolute skill directory, defaulting to `$HOME/.hermes/synced-skills/bitwarden`, with an explicit override for another skill installation. Keep vault behavior, helper scripts, and preflight rules unchanged. Update the account-storage reference's matching source example. No script or Bitwarden CLI execution is authorized in this task.

## Evidence and review

- From `/home/ryushe/projects/bug_bounty_harness`, `test -f` found both relative helper paths absent and both `$HOME/.hermes/synced-skills/bitwarden/scripts/...` files present. No helper or CLI executed.
- `python3 -m unittest discover -s tests -p 'test_bitwarden_skill_paths.py' -v`: 2 passed. The tests verify the documented path expressions, default and absolute override from unrelated CWD, using path checks only.
- `git diff --check`: passed. Bounded old-reference search leaves only negative assertions in the new regression test; no live relative-path guidance remains in the owning skill.
- Independent review: pending parent. No merge or push performed.

## Blockers and deferred work

- Live Bitwarden unlock/login is intentionally untested because the task forbids CLI and secret access. Path-only validation is the acceptance check. Parent should review the documentation and test; integration/runtime sync and any live use occur separately under authorized vault policy.

## Interruption / resume handoff

- **Owning feature branch/ref:** `fix/bitwarden-cwd-paths`
- **Latest immutable recovery checkpoint:** `99d05d3` (implementation + regression + initial dossier)
- **Feature implementation commit(s):** `99d05d3`
- **Exact resume point:** review both commits' diff and focused test, then integrate into `beta` only on parent authorization; retain dossier on feature branch and remove from integration target.
- **Working-tree state at handoff:** clean after dossier handoff commit.

## Decision gates

- **Integration gate:** parent independent review and fetched-beta comparison, followed by focused check in target; no subagent integration.
- **Activation gate:** no runtime sync performed; selected beta runtime must be verified by parent.
- **Promotion gate:** stable promotion not requested.

## Decision record

- 2026-10-15 — reproduced CWD defect, patched canonical guidance and account-storage reference, added path-only regression; awaiting independent review.
