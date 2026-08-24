# Category General Skills Layout

## Intent

Move the user-approved general skills into the repository's categorized layout
and complete the paired ownership transfer of `bounty-storage` and `huge-ingest`
to BBH.

## Branch and target

- Branch: `feat/category-general-skills`
- Base: `fe7f3accd4ca41ec270f517f96231b770d848520` (`origin/beta`)
- Intended target: `beta`

## Implemented contract

- `core/`: `safe-fetch`, `faq`, `papercuts`, `coordination`, `skill-seeds`
- `operations/`: `tmux`, `hoster-ssh`, `script_manager`, `resilio-sync`, `daddy`
- `accounts/`: `account-manager`, `bitwarden`, `account-tui-colors`, `gmail-otp`
- `learning/`: `nightly-learning`, `i-have-adhd`
- Repo-local, installed-path, test, script-index, and README references follow
  the new paths.
- `skill-seeds` authoring guidance discovers the target repository's declared
  layout, supports categorized and flat repositories, and does not prescribe a
  global category table.

## Evidence

- `python3 tests/test_hoster_user_unit.py` — 2 passed.
- `python3 skills/core/papercuts/tests/test_papercut.py` — 5 passed.
- `uv run --with pytest --with pyyaml python -m pytest skills/learning/nightly-learning/scripts/test_nightly_learning.py -q` — 5 passed.
- Gmail OTP byte-compilation and both Daddy script examples passed.
- A `git grep` check found no stale root-level paths for the 16 migrated skills.
- BBH adoption commit `078ba7e` owns full canonical copies of both transferred
  skills; this branch removes the former general-skills copies after that
  adoption was independently verified.

## Activation boundary

This is a committed repository-layout change only. It makes no runtime config,
sync, push, or deployment change.

## Next action

Review and merge this branch into `beta`; integration should remove this
branch-local dossier from the target lane with the merge operation.
