# General `/atme` briefing

- **Task:** `t_647e6c55`
- **Branch:** `feat/general-atme-briefing`
- **Base / target:** `origin/beta` at `83d1bd2` → `beta`
- **Scope:** add a general `atme` skill that is auto-exposed as `/atme` and
  current-work recap requests and returns a compact grounded briefing.
- **Boundary:** `/atme` is automatically generated from the skill name by Hermes'
  skill-command scanner; it is not a bespoke core command.
- **Activation dependency:** BBH must remove its existing `me` skill from the
  active beta projection before this general-skill `atme` is synced.

## Evidence

- `python3 -m unittest tests.test_skill_layout tests.test_me_skill`
- `python3 -m unittest discover -s tests`
- The layout test asserts the `atme` directory; its frontmatter produces the
  native skill command `/atme` through Hermes' skill-command scanner.

## Review / next action

Independent review is required before commit and beta integration. On approval,
commit this branch; merge only after the BBH removal is ready, then use a focused
sync dry run and runtime resolver check to verify `me` resolves to General Skills.
