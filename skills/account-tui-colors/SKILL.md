---
name: account-tui-colors
description: "Use when launching, configuring, or handing off Claude Code, Codex CLI, or OpenCode under an account or lane identified by a color. Align that agent's TUI accent/theme to the effective account color, with deterministic nearest-color fallback."
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

When a coding agent runs in an account- or lane-specific context, its TUI must
visibly use that account's effective color. This makes parallel sessions easy to
distinguish and prevents an operator from acting in the wrong lane.

Applies to **Claude Code**, **Codex CLI**, and **OpenCode**. It changes only
user-local UI configuration; it must never edit repository configuration,
authentication, secret files, or an unrelated agent's theme.

## When to Use

- Launching or handing off Claude Code, Codex CLI, or OpenCode for a named
  account, PwnFox lane, or color-coded worker.
- The account color changes during a durable agent session.
- A user asks for a coding-agent TUI to match an account/lane color.

Do not use when there is no account/lane color. Do not infer one from a project
brand, terminal theme, or a user name.

## Resolve the Effective Color

1. Take an explicitly supplied account/lane color first. If the work is using a
   registered testing account, resolve its `proxy_identity.pwnfox` color through
   `account-management`; do not guess from an alias.
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

- source account/lane color and effective TUI hue;
- any fallback, explicitly (for example, `magenta → purple`);
- tool and user-local theme/profile/config path changed;
- verification that the chosen theme is active, or the exact blocker (such as
  an older tool version or a non-truecolor terminal).

## Common Pitfalls

1. **Making magenta a new arbitrary palette category.** Use purple unless the
   tool has a user-approved exact magenta theme; the canonical fallback is
   `magenta → purple`.
2. **Changing a repo config for personal lane identity.** Themes belong in user
   config or isolated session/profile state, not in committed project files.
3. **Overwriting an active parallel lane's global theme.** Use a per-profile or
   per-session config where available.
4. **Changing success/warning/error to the account hue.** Keep them semantically
   recognizable; change the primary/accent identity only.
5. **Treating a printed configuration edit as proof.** Verify the selection via
   the running TUI or its persisted active setting.

## Verification Checklist

- [ ] Account/lane color came from explicit context or the approved registry.
- [ ] Effective hue was exact or determined by the table.
- [ ] `magenta` was recorded and rendered as `purple`.
- [ ] Only the selected tool's user-local or isolated config was changed.
- [ ] The active theme/profile was checked after the change.
- [ ] No repository, auth, or secret file was modified.
