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
| Operator/local workspace helper | `/home/ryushe/.openclaw/workspace/scripts/` | The script is tied to this OpenClaw workspace, host, or runtime. |

## Registry Rules

- Search this index and nearby `scripts/README.md` files before writing a new
  script.
- Promote repeated shell/regex/manual workflows into scripts once they are
  likely to recur.
- Put the script in the narrowest durable home that future agents will search.
- Add or update a script record in the nearest `scripts/README.md`.
- Keep scripts reusable by accepting files/stdin/flags instead of hard-coding
  one target path.
- Preserve raw input files; write derived outputs separately.
- Never store credentials, cookies, bearer tokens, API keys, private headers,
  or raw sensitive files in script records, examples, or committed fixtures.

## Known General Scripts

No general `script_manager` helper scripts have been promoted yet.

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
