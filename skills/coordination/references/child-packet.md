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

## Safety / Secrets
What sensitive material is excluded, and what policy applies.

## Stop Condition
When to return instead of continuing.

## Required Output
Findings, changed files, evidence paths, uncertainty, blockers, and next step.
```

Keep packets small. If a packet needs a huge history dump, the parent has not
split the task cleanly enough.
