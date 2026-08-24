# Restore Flat General-Skills Layout

- **Branch:** `feat/restore-flat-general-skills`
- **Base / target:** local `beta` at `5621c315dd6bdd23ae8e7f987ec3961f24997461` → `beta`
- **Activation:** none; this change does not modify sync configuration.

## Contract

Restore the repository's flat `skills/<skill>/SKILL.md` layout for the listed
shared general skills. Update repository-internal references and add a layout
regression test. `bounty-storage` and `huge-ingest` remain owned by BBH.

## Preservation

The branch retains the ancestor commits `e72f0e5` (hoster-ssh workspace recovery
guidance) and `30c61b5` (BBH ownership transfer).

## Evidence

- RED: `python3 -m unittest tests/test_skill_layout.py -v` failed before moves
  because the category directories existed and flat skills did not.
- GREEN: focused layout and hoster tests, papercuts tests, nightly-learning
  tests with PyYAML, and the full pytest suite pass.
- `git diff --check` passes; no stale category-layout paths remain in tracked or
  untracked repository text.

## Next

Review and integrate into `beta` when approved. Do not repoint live skill sync
as part of this change.
