# General Skills Script Index

This is the General Skills source index, not a cross-repository placement
policy. When another repository has a root `SCRIPT_POLICY.md`, that repository's
file owns its script storage, indexing, and maintenance conventions. Otherwise,
use the shared `script_manager` fallback guidance.

This index is intentionally lightweight. It catalogs General Skills script
homes and records; detailed usage belongs next to each script.

## General Skills Script Homes

| Scope | Home | Use when |
|---|---|---|
| General reusable automation | `skills/script_manager/scripts/` | The helper works across projects and belongs to no narrower skill. |
| One General Skills skill | `skills/<skill>/scripts/` | The helper supports one skill such as `faq`, `bitwarden`, or `tmux`. |
| Another repository | Its root `SCRIPT_POLICY.md`, otherwise `<repo>/scripts/` or `<repo>/tools/` | The helper depends on that repository's code, schema, or fixtures. |
| Host/runtime local | The runtime's configured local script directory | The helper is intentionally host-local and not canonical shared automation. |

## Registry Rules

- Search this index and nearby `scripts/README.md` files before writing a new
  General Skills helper.
- Reuse or extend an existing helper when its responsibility matches.
- Put the helper in the narrowest durable home future agents will search.
- Add or update a script record in the nearest `scripts/README.md`.
- Keep scripts reusable by accepting files, stdin, or flags instead of
  hardcoding one machine, target, or transient path.
- Preserve raw inputs and write derived outputs separately.
- Never store credentials, cookies, bearer tokens, API keys, private headers,
  or sensitive source files in records, examples, or committed fixtures.

## Known General Scripts

### `skills/hoster-tmux-child-reaper/scripts/tmux_spawn_reaper.py`

- Purpose: provide the bounded mechanical step for a short-lived Hoster-entry
  cleanup sidecar: report and narrowly reap completed, explicitly registered,
  empty `tmux-spawn-*.scope` residue while the main worker begins its task.
- Inputs: Hoster user-systemd environment, prior launcher-owned
  `--register-pane <pid>` provenance when applicable, and optional `--apply`
  after inspection.
- Outputs: JSON inspection/apply receipt; the sidecar reduces it to
  `cleanup: success | needs-attention | failed` for its parent.
- Safe to run on: Hoster, only as an explicit Hoster-entry sidecar.
- Mutates: only with `--apply`, and only ownership-proven empty scopes.
- Example: `python3 tmux_spawn_reaper.py`
- Tests: `python3 -m unittest discover -s tests -p 'test_tmux_spawn_reaper.py' -v`
- Owner: `hoster-tmux-child-reaper` skill.
- Last verified: General Skills beta `e7097ca`; focused tests and Hoster runtime
  projection.

When adding a record, use `skills/script_manager/references/script-record-template.md`.
