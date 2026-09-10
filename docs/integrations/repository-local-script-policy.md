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
  implementation. It now passes (`5 passed`); the full repository suite passes
  (`38 passed, 1 subtest passed`) and `git diff --check` passes.
- **Activation:** Merge and push General Skills beta, update the selected Hoster
  checkout, and verify the active `script_manager` projection in a fresh agent.
- **Review:** Initial independent review blocked on BBH/runtime-specific entries
  in the General Skills index, ambiguous precedence, and an untested safety
  boundary. The follow-up makes `SCRIPT_INDEX.md` General-Skills-only, gives the
  working repository's policy explicit precedence over generic defaults, and
  pins neutrality plus the higher-priority safety boundary in tests.
- **Decision:** Focused independent re-review returned `APPROVE`. Its only
  wording note—an overly broad `SCRIPT_INDEX.md` record alternative—was tightened
  before integration.
- **Next:** Reconcile current `origin/beta`, merge, push, activate the Hoster beta
  projection, and remove this dossier from the integration result.
