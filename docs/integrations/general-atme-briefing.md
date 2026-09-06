# General `@me` briefing

- **Task:** `t_647e6c55`
- **Branch:** `feat/general-atme-briefing`
- **Base / target:** `origin/beta` at `83d1bd2` → `beta`
- **Scope:** add a general `me` skill that recognizes `/atme`, `@me`, and
  current-work recap requests and returns a compact grounded briefing.
- **Boundary:** this is skill-level routing, not registration of a native Hermes
  slash command. A native `/atme` command would require a separate Hermes-core
  change.
- **Activation dependency:** BBH must remove its existing `me` skill from the
  active beta projection before this general-skill `me` is synced.

## Evidence

- `python3 -m unittest tests.test_skill_layout tests.test_me_skill`
- `python3 -m unittest discover -s tests`

## Review / next action

Independent review is required before commit and beta integration. On approval,
commit this branch; merge only after the BBH removal is ready, then use a focused
sync dry run and runtime resolver check to verify `me` resolves to General Skills.
