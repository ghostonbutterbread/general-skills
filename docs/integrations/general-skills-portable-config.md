# General Skills portable user configuration

- **Status:** implementation complete; awaiting review and beta integration.
- **Owner branch:** `fix/general-skills-portable-config`
- **Base:** `origin/beta` at `c4bfecf8cc0db7040589d66fdda94cacf8d186db`
- **Target:** `beta`
- **Implementation checkpoint:** `a9b2f17` (`fix: make general skills host-portable`)

## Intent

Remove host- and checkout-specific paths from the General Skills Hoster SSH,
FAQ, Script Manager, and Safe Fetch workflows. Preserve the current defaults
while letting an operator change them without editing a synced skill.

## Implemented contract

- `scripts/general_skills_config.py` creates
  `$XDG_CONFIG_HOME/general-skills/config.toml` (or
  `~/.config/general-skills/config.toml`) on first use without overwriting user
  edits.
- The generated TOML defaults use `~` rather than a named user home.
- Hoster SSH resolves its identity file from `HOSTER_SSH_KEY`, then the config,
  then `~/.ssh/hoster`; `--identity-file` remains the per-command override.
- FAQ resolves its central store from `FAQ_CENTRAL`, then the config, then
  `~/notes/appsec/faq`.
- Script Manager guidance uses source-relative or synced-skill locations.
- Safe Fetch uses `SAFE_FETCH_QUARANTINE`, otherwise XDG state storage.

## Evidence

- Focused configuration and Hoster helper tests pass.
- Helper `--help` smoke checks pass for FAQ, Safe Fetch, and the config helper.
- Source scans report no `/home/ryushe` or `.openclaw` references in the four
  modified skill directories.
- `git diff --check` passes.

## Known baseline issue

`tests/test_skill_layout.py` fails on both the unchanged beta worktree and this
branch because its expected set omits existing `security-reporting` and
`evidence-first-vulnerability-reporting` skills. This change does not touch the
layout test or those skills.

## Activation boundary

This branch is not live until reviewed, merged into `beta`, and projected by
Aiskillsync. The current active General Skills projection remains the beta
worktree.

## Next action

Review the diff; if accepted, commit this branch, merge it into a clean beta
worktree, run the focused suite again, then sync and verify the active runtime
projection.
