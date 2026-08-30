# Hoster tmux-child-reaper scripts

## `tmux_spawn_reaper.py`

- **Purpose:** register live agent-created tmux child panes, then inspect and only with `--apply` stop completed **empty** registered child-pane scopes.
- **Inputs:** Hoster's user-systemd session; `--register-pane <pid>` at child-pane creation; optional `--apply` for a later explicit reaper run.
- **Output:** a restricted local ownership registry plus one JSON inspection/apply receipt.
- **Mutation:** `--apply` invokes `systemctl --user stop` only for scopes rechecked as eligible immediately before the call.
- **Safe to run on:** Hoster only, from an agent entering its durable workspace.
- **Never selects:** ordinary tmux panes, active agent processes, browser/VNC/proxy/scanner work, `ssh-agent` residue, or unknown/ambiguous scopes.
- **Example:** `python3 tmux_spawn_reaper.py`
- **Tests:** `python3 -m unittest discover -s tests -p 'test_tmux_spawn_reaper.py' -v`
- **Owner/scope:** `hoster-tmux-child-reaper`; explicit agent preflight, never a timer.
- **Last verified:** pending focused test and Hoster sync/deployment.
