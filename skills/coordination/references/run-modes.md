# Coordination Run Modes

Choose the run mode based on observability, interactivity, and scope.

## Native Codex Subagent

Use for bounded side work that can return a concise final answer.

Good fits:

- review one diff or file family
- implement a narrow slice with disjoint write ownership
- inspect a specific code path while the parent works elsewhere

Rules:

- give concrete ownership and stop conditions
- do not pass secrets or broad context dumps
- keep write sets disjoint across workers
- parent reviews and integrates returned changes

## Codex Remote TUI

Current local `codex --help` exposes:

```text
--remote <ADDR>
--remote-auth-token-env <ENV_VAR>
```

Use this only when there is already a trusted Codex app-server endpoint to
connect to. Record the websocket address shape, auth-token env var name, and
parent run record. Do not write bearer tokens into prompts, manifests, or logs.

## Claude CLI Session

Current local `claude --help` exposes:

```text
--tmux
--worktree [name]
--name <name>
--resume [value]
--session-id <uuid>
```

Use this for a dedicated interactable Claude child session. Prefer a named tmux
session and a durable manifest so Ryushe can attach or resume it.

## CLI Under Tmux

Use when Ryushe or another agent may need to attach to the child process, or
when the child may outlive the current turn.

Good fits:

- Claude/Codex/OpenCode child with its own terminal
- long-running recon, fuzzing, scans, or build loops
- interactive agent that needs manual steering later

Record:

- tmux session name
- command and working directory
- log/transcript path
- attach command
- stop/cleanup command

Prefer the existing `/tmux` skill for lifecycle details.

## OpenClaw Session

Use when the desired child is a separate OpenClaw conversation/session and the
runtime exposes session spawn/send/history tools.

Good fits:

- chat-like subagent that Ryushe can continue interacting with
- ACP/OpenClaw delegated investigations
- separate topic/session experiments

Record the session ID, title, parent task, and summary path.

## Human Handoff

Use when the next step needs credentials, CAPTCHA, payment, destructive action,
private data access, or a policy decision.

The parent should provide the smallest useful handoff: URL, state, exact ask,
known constraints, and where to resume.

## Verification Rule

Verify exact CLI flags against the installed binary before turning them into a
default command. Do not cargo-cult flags from screenshots or other people's
setups without local help/version checks.
