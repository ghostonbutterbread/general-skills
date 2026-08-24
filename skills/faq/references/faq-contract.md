# FAQ Contract

## Purpose

FAQ prevents agents from solving the same operational problem repeatedly. It is
the first lookup layer for solved blockers, existing scripts, known commands,
and recurring target quirks.

## Knowledge Split

- `faq` answers: "I hit this problem. What do I do?"
- `notes` answer: "What do we know?"
- `hypotheses` answer: "What might be true but is not proven?"
- `todo` answers: "What still needs action?"
- `findings` answer: "What evidence is reportable?"

Do not merge these buckets. The separation is what keeps retrieval clean.

## Lookup Order

1. Active program FAQ:
   - `~/Shared/{family}/{program}/{lane}/notes/faq/`
   - Use for platform-specific auth flows, request quirks, account/resource
     setup, endpoint behavior, target scripts, and target-only workarounds.

2. Central AppSec FAQ:
   - `/home/ryushe/notes/appsec/faq/`
   - Use for reusable browser, proxy, Caido, tooling, payload, workflow, and
     agent-operation fixes.

3. Project-local docs:
   - The repo or project that owns the implementation behavior.
   - Add a central FAQ pointer only when the fix generalizes.

4. Todo:
   - `~/projects/todo/`
   - Use when the fix is not built or verified yet.

## Search Pattern

Use exact terms first:

```bash
python3 /home/ryushe/projects/general-skills/skills/faq/scripts/faq_search.py \
  "<tool error flow endpoint concept>" \
  --family web_bounty \
  --program <program> \
  --lane web
```

Use raw search when needed:

```bash
rg -i "<error phrase|tool|flow|endpoint>" \
  ~/Shared/*/*/*/notes/faq \
  /home/ryushe/notes/appsec/faq
```

## Note Shape

```md
# <Solved Problem Title>

Status: active
Scope: central | program-specific | project-specific
Applies to: <program/project/tool/context>
Last verified: YYYY-MM-DD
Tags: #faq #<topic> #<tool-or-program>

## Trigger

What the agent sees: error text, blocked flow, weird response, missing state, or
task phrase.

## Fix

The shortest repeatable solution.

## Script Or Command

- Script: `<absolute path>` or none
- Skill: `<skill name/path>` or none
- Command:
  ```bash
  <command>
  ```

## Verification

How the fix was checked.

## Boundaries

When not to apply this fix.

## Related

- Full URLs, file paths, specs, todos, findings, or handoff notes.
```

## Tags

Use tags that match future search language:

- `#faq`
- `#script`
- `#auth-flow`
- `#chromium`
- `#caido`
- `#pwnfox`
- `#program-<name>`
- `#tooling`
- `#hoster-sync`

## Indexing

Markdown is the source of truth. Generated indexes may summarize it under:

- `/home/ryushe/notes/appsec/indexes/faq-by-tag.md`
- `/home/ryushe/notes/appsec/indexes/faq-by-tool.md`
- `/home/ryushe/notes/appsec/indexes/faq-by-script.md`
- active program `notes/index.md`

Generated indexes are disposable. FAQ notes are canonical.

## Promotion Rules

- Promote a hypothesis only after it becomes a repeatable fix.
- Promote a hunter-memory claim only after it is stable and scoped.
- Promote a one-off tool failure only if it is likely to recur.
- Leave uncertain information in notes, hypotheses, or handoffs.

## Sensitive Data

Never store secrets or raw private traffic. Store sanitized artifact references
instead.
