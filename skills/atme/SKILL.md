---
name: atme
description: Summarize the current work when asked to /atme or @me.
---

# @me Briefing

Use `/atme` for a short summary of what the current conversation
has been working on. This is a general status briefing, not a task tracker,
security ledger, or a substitute for reading project evidence.

## Procedure

1. Read the current conversation first. Identify the active objective, concrete
   progress, evidence or artifacts, blockers, and the immediate next action.
2. If the conversation names an active project or Kanban card, inspect that
   specific record to confirm the status. If it names a prior session, use
   `session_search` before claiming history.
3. Return only a compact briefing:
   - **Working on:** active objective.
   - **Progress:** completed, verified work and its artifact/branch when known.
   - **Blocked by:** a real blocker, or “Nothing known.”
   - **Next:** one immediate action.
4. State uncertainty plainly. Do not invent project state, read unrelated
   histories, or expose sensitive details.

## Routing

When the user says `/atme`, `@me`, “what are we working on?”, or requests a
quick current-work recap, load this skill and give the briefing directly. For
BBH findings, coverage, or hunt artifacts, load the BBH `ledger` skill after the
briefing only when that coordination is actually needed.

## Verification

A useful @me response is grounded in the current conversation and any explicitly
named source of record, has no more than four bullets, and makes its uncertainty
visible.
