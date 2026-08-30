# Script Index

Canonical map for reusable scripts that agents should discover before writing a
new one.

This index is intentionally lightweight. It points agents to the right script
home and record format; detailed usage belongs next to the script itself.

## Script Homes

| Scope | Canonical Home | Use When |
|---|---|---|
| General reusable automation | `skills/script_manager/scripts/` | The script is useful across projects and does not belong to one domain skill. |
| One skill's helper | `skills/<skill>/scripts/` | The script supports one skill, such as `faq`, `bitwarden`, or `tmux`. |
| Project-local helper | `<repo>/scripts/` or `<repo>/tools/` | The script depends on that repo's code, schema, or test fixtures. |
| Bug bounty lane helper | `~/projects/bug_bounty_harness/skills/<skill>/scripts/` | The script is reusable for one bounty lane or harness workflow. |
| Shared bounty helper | `~/Shared/bounty_recon/_shared/scripts/` | The script is small, useful across bounty programs or machines, and should be cloud-backed for agents to discover. |
| Operator/local workspace helper | `/home/ryushe/.openclaw/workspace/scripts/` | The script is tied to this OpenClaw workspace, host, or runtime. |

## Registry Rules

- Search this index and nearby `scripts/README.md` files before writing a new
  script.
- Promote repeated shell/regex/manual workflows into scripts once they are
  likely to recur.
- Put the script in the narrowest durable home that future agents will search.
- Add or update a script record in the nearest `scripts/README.md`.
- For shared bounty helpers, keep only the script and small records in
  `~/Shared`; put heavy inputs, fixtures, generated output, and corpora in
  `/mnt/bounty` or scratch.
- Keep scripts reusable by accepting files/stdin/flags instead of hard-coding
  one target path.
- Preserve raw input files; write derived outputs separately.
- Never store credentials, cookies, bearer tokens, API keys, private headers,
  or raw sensitive files in script records, examples, or committed fixtures.

## Known General Scripts

### `skills/hoster-tmux-child-reaper/scripts/tmux_spawn_reaper.py`
- Purpose: report and narrowly reap completed, explicitly registered, **empty** agent-created `tmux-spawn-*.scope` child-pane residue on Hoster.
- Inputs: Hoster user-systemd environment, a prior `--register-pane <pid>` ownership receipt, optional `--apply`.
- Outputs: JSON inspection/apply receipt.
- Safe to run on: Hoster, as an explicit agent-entry preflight.
- Mutates: only `--apply`, and only ownership-proven, empty scopes.
- Example: `python3 tmux_spawn_reaper.py`
- Tests: `python3 -m unittest discover -s tests -p 'test_tmux_spawn_reaper.py' -v`
- Owner: `hoster-tmux-child-reaper` skill.
- Last verified: pending focused test and Hoster sync/deployment.

When one is added, record:

```md
### `<script-path>`
- Purpose:
- Inputs:
- Outputs:
- Safe to run on:
- Mutates:
- Example:
- Tests:
- Owner:
- Last verified:
```
