# Skill Creator Repository Boundaries

- **Branch:** `feat/skill-creator-repo-boundaries`
- **Base / target:** `beta` at `411cc810b8c676044ce2a5ff44e3309bb7d40596` → `beta`
- **Status:** temporary branch-local integration dossier
- **Activation:** none; this change does not modify sync configuration.

## Intent

Preserve the seed-first workflow while making proposed skill ownership explicit:
repositories are top-level capability boundaries, and `general-skills` remains
flat.

## Implemented contract

- The `skill-seeds` template requires a proposed canonical repository and
  repository-relative path in `project`, `canonical_target`, and `## Target`.
- General, coding, and security are broad umbrellas; no arbitrary nested
  category taxonomy is introduced.
- A genuinely new non-general/non-coding/non-security capability class proposes
  a dedicated flat repository (for example, `mobile-security`).
- Recon remains a security subdomain in the security/BBH capability repository.
- A focused layout test asserts these repository-boundary rules remain present.

## Evidence

- `python3 -m unittest tests/test_skill_layout.py -v` — 2 tests passed,
  including the focused capability-boundary regression assertion.
- `git diff --check` — passed.

## Blockers

None known.

## Next

Review and integrate into `beta` when approved. Remove this temporary dossier
from the integration target as part of the integration operation; do not repoint
live skill sync.
