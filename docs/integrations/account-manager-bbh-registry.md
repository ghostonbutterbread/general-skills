# Account-manager BBH registry routing integration dossier

- **Status:** second review's template and handoff blockers corrected; final independent re-review pending
- **Owner:** Hermes bugfix subagent (PC-20260820-170810-4eb7bcdc)
- **Branch / owning ref:** `fix/account-manager-bbh-registry`
- **Worktree:** `/home/ryushe/projects/.worktrees/general-skills-account-manager-registry`
- **Base commit:** `fb0aa2841d1b9d290a2ea36867b7898d692fef3a` (fetched `origin/beta`, 2026-10-15)
- **Intended integration target:** General Skills `beta`
- **Last updated:** 2026-10-15
- **Latest immutable implementation checkpoint:** `dca395ff7b0c6ec0861cb0e2b2b76b0cddd79db5` (template scope and regression; this dossier receipt follows)
- **Feature implementation commit(s):** `5f9a999cc6a668376671d8bbf195ee6a3fc92030`, `7a15afaf4c9d6a77558516fe1c6985bb02cb6ac1`, `dca395ff7b0c6ec0861cb0e2b2b76b0cddd79db5`
- **Inspiration / canonical references:** General Skills `skills/account-manager`; BBH beta `skills/account-management/SKILL.md`, `scripts/inventory_paths.py` and `account_inventory.py` (read code/guidance only, no account rows)

## Intent and implemented contract

The live General Skills beta guidance still named `~/Shared/web_bounty/{program}/shared/accounts.md` as preferred. BBH owns program account state at `$HARNESS_SHARED_BASE/{normalized-program}/credentials/account_inventory.json`, with `HARNESS_SHARED_BASE` defaulting to `~/Shared/web_bounty`. `account-management` owns normalization, initialization, lifecycle and registry commands. General Skills now routes BBH programs to that skill and bars the Markdown table as a fallback or parallel writer. The old non-web `bounty_recon` table procedure remains explicitly limited to programs outside BBH; its retention is compatibility for the existing separate lane, not evidence that any particular live program uses it. The required Bitwarden `account-storage.md` entry now routes BBH account/credential-reference and cleanup updates to `account-management` instead of treating legacy account/resource notes as BBH authority. Its table and deletion-note instructions remain scoped to non-BBH. The `accounts-template.md` asset is explicitly labeled legacy non-BBH and warns BBH users away from a Markdown table. No registry, account table, private row, or Bitwarden state was read or changed.

## Evidence and review

- Initial implementation receipt: `python3 -m unittest discover -s tests -p test_account_manager_routing.py -v`: 2 passed; `python3 -m pytest -q tests`: 47 passed, 1 subtest; `python3 -m pytest -q`: 58 passed, 1 subtest.
- Repair receipt: `python3 -m unittest discover -s tests -p test_account_manager_routing.py -v`: 3 passed; `python3 -m pytest -q tests/test_bitwarden_skill_paths.py`: 2 passed; `python3 -m pytest -q`: 59 passed, 1 subtest.
- Second review identified an unqualified Markdown template and stale handoff checkpoint. Template fix `dca395f` with an asset regression: 6 focused tests and 60 full tests plus 1 subtest passed; `git diff --check` clean.
- `git diff --check`: clean (repair diff).
- Reference-impact audit: bounded `skills/` search for `account/resource table`, `shared/accounts.md`, and `account-storage.md` found only the Bitwarden required reference/entry and the already-scoped account-manager entry/reference. The prior dossier incorrectly described the generic Bitwarden lifecycle reference as harmless; independent review found its unqualified table authority contradicted the BBH route. The repaired reference explicitly scopes legacy table and deletion notes to non-BBH and points BBH to the canonical inventory. Focused regression checks the required Bitwarden entry-to-reference path, BBH routing/negative fallback, and retained legacy semantics. BBH registry implementation was not edited.
- Previous before-commit upstream re-fetch: `origin/beta` remained `fb0aa28`, identical to branch base. No additional fetch/sync or integration in this delegated repair.
- Independent review of `7a15afa` blocked on the unqualified template and outdated dossier; both are corrected for final re-review.

## Blockers and deferred work

- **Activation:** not performed or authorized in this task. Parent must review/integrate into selected `beta`, publish if authorized, synchronize intended profile projection, and verify a fresh consumer loads both skills. No active-runtime behavior claim from this branch.
- **Papercut closure:** left to parent after integration and consumer verification; no shared papercut record write.

## Interruption / resume handoff

- **Owning feature branch/ref:** `fix/account-manager-bbh-registry`
- **Latest immutable implementation checkpoint:** `dca395ff7b0c6ec0861cb0e2b2b76b0cddd79db5`; this documentation receipt is the feature tip.
- **Exact resume point:** independently re-review the full BBH/Bitwarden/template route and focused/full receipts, then decide beta integration and activation separately.
- **Working-tree state at handoff:** clean after documentation receipt commit.

## Decision gates

- **Integration gate:** review exact source diff and focused/full test receipts; parent decides merge.
- **Activation / cohort gate:** publish beta, profile-scoped sync, verify actual symlinks and fresh consumer load.
- **Promotion gate:** separate explicit decision, not part of task.

## Decision record

- 2026-10-15 — verified stale routing and corrected General Skills owner without data mutation; branch prepared for review, not integrated.
- 2026-10-15 — independent review identified required Bitwarden reference conflict; scoped legacy instructions to non-BBH and added entry-path regression. Local tests pass; independent re-review and integration remain with parent.
- 2026-10-15 — second review identified an unqualified legacy template and stale dossier; scoped asset, added regression, and updated immutable implementation checkpoint.
