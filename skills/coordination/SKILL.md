---
name: coordination
description: "Coordinate parent-agent work, split broad tasks into focused subagents, and preserve interactable child runs."
---

# Coordination

Use this when a task is broad, multi-surface, long-running, or likely to bloat
the main context. The parent agent stays responsible for the map, critical
path, safety boundaries, and final integration. Child agents own one focused
packet each.

## Core Rule

Do not let one agent try to do everything.

The parent agent should:

- define the objective and current critical path
- split only independent or sidecar work into child packets
- keep sensitive context and broad history out of child prompts
- track every spawned child by run ID, owner, objective, attach path, and result
- merge results into the canonical spec, notes, todo, report, or finding

Child agents should:

- receive one objective, one bounded scope, and one stop condition
- return evidence, uncertainty, blockers, and changed files/artifacts
- avoid expanding scope without asking the parent

## Load Order

1. Identify whether this is project work, bug bounty work, research, or ops.
2. If project work is meaningful, check the active spec/todo system first.
3. Read `references/run-modes.md` before choosing how to spawn children.
4. Use `references/child-packet.md` as the packet shape when delegating.
5. Decide what the parent can continue doing while children run.
6. Spawn focused child agents only for non-blocking or clearly separable work.
7. Record result summaries and attach/reopen instructions before finishing.

## Spawn Decision

Prefer the smallest useful child:

- Native Codex subagent: bounded parallel coding, review, or analysis.
- CLI under tmux: long-running or interactable Codex/Claude/OpenCode child.
- OpenClaw session: chat-like or externally interactable child session.
- No child: immediate blocker, tiny task, or context too sensitive to split.

The parent should not delegate the next action if it cannot make progress until
that action returns.

## Interactable Children

When a child should be reopenable by Ryushe or another agent, create a durable
run record with:

- run ID and human-readable name
- parent request and parent session/topic when known
- agent/tool type, model, workspace, and command flags
- attach command or session reference
- transcript/log/artifact paths
- current status and last meaningful output
- sensitive-data handling notes

Until a dedicated runner exists, use tmux/session tooling and write the attach
details into the task/spec/log you are already maintaining.

## Output

Every coordinated run should end with:

- what the parent handled directly
- which child packets were spawned or intentionally not spawned
- where their logs/artifacts live
- what changed in canonical project state
- next action or blocker
