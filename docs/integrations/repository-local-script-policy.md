# Repository-local script policy discovery

- **Intent:** Keep shared `script_manager` repository-neutral while allowing one
  conventional repository-owned script contract.
- **Base:** `origin/beta` at `ce57e028e06c946ea2324bd2814f2dffdf7916c3`.
- **Target:** `beta`.
- **Branch:** `feat/repository-local-script-policy`.
- **Contract:** When a repository-root `SCRIPT_POLICY.md` exists, it owns that
  repository's storage, indexing, and maintenance conventions without
  overriding higher-priority safety or authorization. Multiple cohesive helpers
  are allowed; matching existing owners are reused instead of duplicated.
- **Evidence:** `tests/test_script_manager_policy.py` failed on the absent lookup,
  BBH-specific wording, and missing multiple-helper boundary before
  implementation. It now passes (`4 passed`); the full repository suite passes
  (`37 passed, 1 subtest passed`) and `git diff --check` passes.
- **Activation:** Merge and push General Skills beta, update the selected Hoster
  checkout, and verify the active `script_manager` projection in a fresh agent.
- **Next:** Obtain independent review, reconcile current `origin/beta`, then
  merge and remove this dossier from beta.
