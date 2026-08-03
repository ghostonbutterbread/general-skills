---
name: account-tui-colors
description: "Use when launching, configuring, or handing off Claude Code, Codex CLI, or OpenCode under a PwnFox account profile. Resolve the current main account's color, keep it stable across secondary-account comparisons, and repaint only when the active account changes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [coding-agent, tui, theme, color, account, claude-code, codex, opencode]
    related_skills: [claude-code, codex, opencode, account-management]
---

# Account-Aligned Coding-Agent TUI Colors

## Overview

When a coding agent runs through a PwnFox account profile, its TUI must visibly
use the color assigned to the **current main account**. This makes parallel
sessions easy to distinguish and keeps the visual cue aligned with the identity
driving the work.

Applies to **Claude Code**, **Codex CLI**, and **OpenCode**. It changes only
user-local UI configuration; it must never edit repository configuration,
authentication, secret files, or an unrelated agent's theme.

## When to Use

- Launching or handing off Claude Code, Codex CLI, or OpenCode through a PwnFox
  account profile.
- The work's current main account changes during a durable agent session.
- A user asks for a coding-agent TUI to track the PwnFox account in use.

Do not use when the PwnFox profile/account cannot be resolved. Do not infer a
color from a project brand, terminal theme, user name, or coding-provider
credentials.

## Active Account Color Contract

1. At launch, infer the TUI color from the selected PwnFox profile: resolve its
   account alias and `proxy_identity.pwnfox` color from the approved account
   registry/resolver metadata. This is profile/lease metadata, **not** a request
   to inspect cookies, tokens, or CLI provider credentials.
2. Treat that identity as the **main account** and retain its alias and effective
   hue as runtime handoff state for the coding-agent session.
3. In a two-account workflow such as IDOR, keep the main account's color while
   a secondary account is used solely for comparison, replay, or object access.
   Do not repaint for every secondary request.
4. Re-resolve and repaint **before the next action** only when the operator or
   workflow changes the selected PwnFox profile/main identity. If the former
   secondary account becomes the account driving the work, it is now main and
   its color must replace the old color.
5. Record each real transition as `old-account/color → new-account/color` in the
   handoff/run note. Reusing a secondary account without promoting it is not a
   transition and produces no UI change.

Example: an IDOR run starts as `blue` and sends replay/comparison requests as
`green`; the TUI stays blue. If the work switches to green as its main account,
change the TUI to green once before continuing.

## Resolve the Effective Color

1. First use the selected PwnFox profile's registered account/color. An explicit
   active-account override in the launch/handoff is authoritative when present.
   If neither is available, stop and ask which PwnFox profile is main; never
   guess from an alias alone.
2. Normalize only for comparison: lowercase and remove spaces, hyphens, and
   underscores. Keep the original value in the handoff/report.
3. Use an exact supported hue when possible. Otherwise apply this deterministic
   nearest-hue map:

| Requested account color | Effective TUI hue |
|---|---|
| red, scarlet, crimson | red |
| orange, brown | orange |
| yellow, amber, gold | yellow |
| green, lime | green |
| cyan, teal, aqua, turquoise | cyan |
| blue, navy, indigo | blue |
| purple, violet, **magenta**, fuchsia, pink, lilac | **purple** |

**Required fallback:** magenta has no direct standard target in this policy, so
use **purple**. Record the decision as `magenta → purple` in the launch/handoff
note. For an unrecognized value, stop before changing UI configuration and ask
for the intended color rather than silently choosing one.

Use a readable accent on the existing base theme; preserve success/warning/error
semantics and do not recolor the full terminal emulator.

## Safe Scope and Collision Rules

- Prefer a theme whose name includes both the tool and effective hue, such as
  `claude-account-purple` or `opencode-account-purple`.
- Inspect an existing file before updating it. Preserve unrelated fields and
  make a narrowly scoped color/theme edit.
- Do not edit a project-local theme/config unless the user explicitly requests
  a repository-shared appearance. Account identity is machine-local state.
- If the same local UI config is used by simultaneous accounts, create/select a
  per-session or per-profile theme before launch; do not overwrite an active
  other-account session's visual identity.

## Claude Code

Claude Code supports custom theme files from v2.1.118 onward.

1. Ensure `~/.claude/themes/` exists.
2. Create or update `~/.claude/themes/claude-account-<hue>.json` with a dark or
   light base matching the current preference and at least the `claude` accent
   override. Use a clear hex value for the effective hue.
3. Select `custom:claude-account-<hue>` using `/theme` in the TUI, or set the
   user-level `theme` preference in `~/.claude/settings.json` while preserving
   its JSON contents.
4. Restart/reopen the session when the running TUI does not repaint.

Example purple fallback theme (`magenta → purple`):

```json
{
  "name": "Account Purple",
  "base": "dark",
  "overrides": {
    "claude": "#A78BFA"
  }
}
```

Do not claim that Claude Code changes the terminal emulator palette; it only
changes its own interface colors.

## Codex CLI

Codex persists the chosen interactive TUI theme in the user config at
`~/.codex/config.toml`, under `tui.theme`.

1. In an interactive Codex session, use `/theme`, preview/select the closest
   available hue, and confirm it persists as `tui.theme`.
2. If an exact account hue is not available, use the effective hue from the
   map—therefore **magenta selects purple**.
3. For a long-running or isolated account lane, prefer a Codex profile
   (`$CODEX_HOME/<profile>.config.toml` and `--profile`) so its theme selection
   cannot alter another account's running lane.
4. Verify the effective theme with `codex`'s `/status` or by inspecting the
   active profile's `tui.theme`; do not invent an undocumented custom color key.

## OpenCode

OpenCode supports named and custom TUI themes.

1. Put a user-local custom theme at
   `~/.config/opencode/themes/opencode-account-<hue>.json` (or the equivalent
   `$XDG_CONFIG_HOME/opencode/themes/` path). Use the theme's `primary` and/or
   `accent` keys for the effective hue, keeping contrast and status colors
   distinct.
2. Select it in user-local `~/.config/opencode/tui.json` with
   `"theme": "opencode-account-<hue>"`, or select it with `/theme` in the TUI.
3. For an account-specific temporary run, use a distinct `OPENCODE_CONFIG`
   / `OPENCODE_CONFIG_DIR` rather than changing the global `tui.json` used by
   another active account.
4. Confirm `COLORTERM` is `truecolor` or `24bit` before expecting exact hex
   rendering; otherwise report that the terminal will approximate the color.

Minimal custom purple theme:

```json
{
  "$schema": "https://opencode.ai/theme.json",
  "defs": { "account": "#A78BFA" },
  "theme": {
    "primary": "account",
    "accent": "account"
  }
}
```

## Completion Criteria

Before handing the agent over, report:

- selected PwnFox profile, inferred main account, and effective TUI hue;
- any fallback, explicitly (for example, `magenta → purple`);
- each actual main-account transition, if one occurred;
- tool and user-local theme/profile/config path changed;
- verification that the chosen theme is active, or the exact blocker (such as
  an older tool version or a non-truecolor terminal).

## Common Pitfalls

1. **Making magenta a new arbitrary palette category.** Use purple unless the
   tool has a user-approved exact magenta theme; the canonical fallback is
   `magenta → purple`.
2. **Changing a repo config for personal lane identity.** Themes belong in user
   config or isolated session/profile state, not in committed project files.
3. **Repainting for every secondary request.** Keep the selected main account's
   color through comparison/replay work. Repaint only when that secondary account
   becomes the main PwnFox profile driving the work.
4. **Changing success/warning/error to the account hue.** Keep them semantically
   recognizable; change the primary/accent identity only.
5. **Treating a printed configuration edit as proof.** Verify the selection via
   the running TUI or its persisted active setting.

## Verification Checklist

- [ ] Selected PwnFox profile resolved to an approved main account and color.
- [ ] A secondary IDOR/comparison account did not trigger a repaint.
- [ ] A main-account/profile switch repainted before the next action.
- [ ] Effective hue was exact or determined by the table.
- [ ] `magenta` was recorded and rendered as `purple`.
- [ ] Only the selected tool's user-local or isolated config was changed.
- [ ] The active theme/profile was checked after the change.
- [ ] No repository, auth, or secret file was modified.
