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
- give children focused packets, including critical-path work when useful;
  parent concurrency is beneficial, not required
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
6. Use the spawn decision below to choose focused child work.
7. Record result summaries and attach/reopen instructions before finishing.

## Spawn Decision

Keep one primary agent responsible for the task; focused subagents are normal
helpers, not exceptions to a solo default. The parent may choose delegation
without explicit user direction when independent work, fresh-context analysis,
preparation for an upcoming step, or separate review improves speed or confidence.
Large tasks are a useful signal to look for focused child work, not a mandate
to split every task. Avoid redundant work and fragmentation whose coordination
cost outweighs the benefit.

For example, while implementing one component, the parent can ask a child to
analyze a specific local JavaScript module needed for a later decision. Give
that child the exact question and use its evidence when the decision arrives.

Choose the mode appropriate to the packet:

- Native subagent: bounded coding, review, or analysis.
- CLI under tmux: long-running or interactable Codex/Claude/OpenCode child.
- OpenClaw session: chat-like or externally interactable child session.
- No child: work is simpler directly or necessary context cannot be shared safely.

## Child Policy Handoff

Required boundary: delegation does not expand authority or remove applicable
policies. Each child packet must identify the policies and repository guidance
necessary for its assigned work, provide accessible references (or the necessary
text when references are unavailable), and require the child to load and follow
them before acting. Do not assume children inherit the parent's loaded context.
Pass the relevant scope, permissions, safety and verification constraints, not
an indiscriminate policy dump. A missing required policy or permission is a
blocker to the affected action; return it to the parent rather than improvise.
Security-related delegation remains subject to its domain safety boundaries;
this general guidance does not authorize autonomous live probing or exploitation.

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
