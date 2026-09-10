# Child Packet Template

Use this shape when spawning or briefing a child agent.

```md
## Objective
One concrete outcome.

## Scope
Files, URLs, modules, artifacts, or hypothesis owned by this child.

## Out Of Scope
What the child must not touch or decide.

## Context
Only the relevant facts needed for this packet.

## Tools / Mode
Native subagent, tmux CLI, OpenClaw session, browser, proxy, or read-only.

## Required Policies / Guidance
Accessible references or necessary text for the policies and repository guidance
that apply to this packet. Load and follow them before acting; report missing
required guidance to the parent. Do not assume inherited parent context.

## Safety / Secrets
Scope, permissions, safety and verification constraints; excluded sensitive material.

## Stop Condition
When to return instead of continuing.

## Required Output
Findings, changed files, evidence paths, uncertainty, blockers, and next step.
```

Keep packets small. If a packet needs a huge history dump, the parent has not
split the task cleanly enough.
