# Papercut repair branch isolation

Status: feature branch. Owner: General Skills `skills/papercuts/references/repair.md`. Canonical path: `skills/papercuts/references/repair.md`. Supersedes: direct-to-integration ambiguity in the repair reference. Implementation commit: pending.

- **Intent:** Confirmed repository papercut fixes use a fresh task branch/worktree from the selected integration lane before edits, preserving a review/rollback boundary. Evidence-based no-patch closure remains branch-free.
- **Branch/base/target:** `docs/papercuts-repair-branch`, fetched `origin/beta` at `2b325702911a5213f1735b1cb147ad7749729804`, target `beta`.
- **Contract:** Repair reference specifies isolation; existing branch-lifecycle owns integration mechanics. No CLI/storage change.
- **Evidence:** Focused layout tests (5 passed), papercut helper tests (5 passed), and `git diff --check` clean. Independent review pending.
- **Activation:** Feature branch is not runtime skill. Merge to selected beta source, verify projected reference and branch containment, then retire this temporary dossier from beta.
- **Next action:** Run tests, commit, independently review, integrate to beta, verify runtime projection and remote state.
