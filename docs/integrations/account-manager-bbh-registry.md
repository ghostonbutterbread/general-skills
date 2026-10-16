# Account-manager BBH registry routing integration dossier

- **Status:** review-ready
- **Owner:** Hermes bugfix subagent (PC-20260820-170810-4eb7bcdc)
- **Branch / owning ref:** `fix/account-manager-bbh-registry`
- **Worktree:** `/home/ryushe/projects/.worktrees/general-skills-account-manager-registry`
- **Base commit:** `fb0aa2841d1b9d290a2ea36867b7898d692fef3a` (fetched `origin/beta`, 2026-10-15)
- **Intended integration target:** General Skills `beta`
- **Last updated:** 2026-10-15
- **Latest immutable recovery checkpoint:** `5f9a999cc6a668376671d8bbf195ee6a3fc92030`
- **Feature implementation commit(s):** `5f9a999cc6a668376671d8bbf195ee6a3fc92030`
- **Inspiration / canonical references:** General Skills `skills/account-manager`; BBH beta `skills/account-management/SKILL.md`, `scripts/inventory_paths.py` and `account_inventory.py` (read code/guidance only, no account rows)

## Intent and implemented contract

The live General Skills beta guidance still named `~/Shared/web_bounty/{program}/shared/accounts.md` as preferred. BBH owns program account state at `$HARNESS_SHARED_BASE/{normalized-program}/credentials/account_inventory.json`, with `HARNESS_SHARED_BASE` defaulting to `~/Shared/web_bounty`. `account-management` owns normalization, initialization, lifecycle and registry commands. General Skills now routes BBH programs to that skill and bars the Markdown table as a fallback or parallel writer. The old non-web `bounty_recon` table procedure remains explicitly limited to programs outside BBH; its retention is compatibility for the existing separate lane, not evidence that any particular live program uses it. No registry, account table, or Bitwarden state was read or changed.

## Evidence and review

- `python3 -m unittest discover -s tests -p test_account_manager_routing.py -v`: 2 passed.
- `python3 -m pytest -q tests`: 47 passed, 1 subtest passed.
- `python3 -m pytest -q`: 58 passed, 1 subtest passed.
- `git diff --check`: clean.
- Reference-impact audit: repo search found the obsolete web table path only in the owning skill/reference; `README.md` description was adjusted. `skills/bitwarden/references/account-storage.md` uses generic target notes and no obsolete web path; it remains unchanged. New focused test rejects reintroduction of the deprecated web table route in both entry points and checks the BBH registry/owner plus non-web isolation. BBH registry implementation was not edited.
- Before-commit upstream re-fetch: `origin/beta` remained `fb0aa28`, identical to branch base.
- Independent review: pending parent integration review.

## Blockers and deferred work

- **Activation:** not performed or authorized in this task. Parent must review/integrate into selected `beta`, publish if authorized, synchronize intended profile projection, and verify a fresh consumer loads both skills. No active-runtime behavior claim from this branch.
- **Papercut closure:** left to parent after integration and consumer verification; no shared papercut record write.

## Interruption / resume handoff

- **Owning feature branch/ref:** `fix/account-manager-bbh-registry`
- **Latest immutable recovery checkpoint / implementation commit:** `5f9a999cc6a668376671d8bbf195ee6a3fc92030`; this dossier-only handoff commit follows it.
- **Exact resume point:** review committed diff, decide beta integration and activation separately.
- **Working-tree state at handoff:** to be clean after commit.

## Decision gates

- **Integration gate:** review exact source diff and focused/full test receipts; parent decides merge.
- **Activation / cohort gate:** publish beta, profile-scoped sync, verify actual symlinks and fresh consumer load.
- **Promotion gate:** separate explicit decision, not part of task.

## Decision record

- 2026-10-15 — verified stale routing and corrected General Skills owner without data mutation; branch prepared for review, not integrated.
