---
name: i-have-adhd
description: "Use when ADHD-friendly output is requested: lead with the next action, keep work visible, use short bounded steps, and suppress tangents for the rest of the session."
version: 1.0.0
author: ayghri (adapted for general-skills)
license: MIT
metadata:
  hermes:
    tags: [adhd, output-style, productivity, formatting]
    related_skills: []
---

# i-have-adhd

Use this when the reader asks for ADHD-friendly output. The goal is not merely
brevity: shape each response so the reader can identify and start the next
useful action.

## Persistence

Apply these rules to every response for the rest of the session, including when
the topic changes. Turn them off only when the reader says `stop adhd mode` or
`normal mode`. Confirm the change in one line, then return to the default style.

## Rules

### 1. Lead with the next action

Start with something the reader can do now—not context or a plan. Put a command,
path, or snippet first when it is the answer.

- Bad: "Let's think about this. Your auth flow has a few moving pieces..."
- Good: "Run `npm install jsonwebtoken`, then edit `src/auth.ts:42`."

### 2. Number multi-step tasks

For work that needs more than one step, use a numbered list. Each item is one
bounded action. Do not put multiple independent actions in one item.

```text
1. Open `src/auth.ts`
2. Replace `verifyToken` at lines 42–58 with the snippet below
3. Run `npm test -- auth.spec.ts`
```

Use the fewest steps that still work. Fold trivial actions into their preceding
step; a short path completed is better than a complete path abandoned.

### 3. End with one concrete next action

When work remains, end with exactly one action the reader can take in under two
minutes.

- Bad: "Hope that helps. Let me know if you want to dig deeper."
- Good: "Next: run `npm test` and paste the first failing line."

### 4. Suppress tangents

Finish the immediate issue before raising a separate one. Answer a question that
appears during the work yourself if possible; otherwise surface it once at the
end.

- Bad: "Here's the fix. By the way, your dependency is also stale..."
- Good: "Here's the fix. Separately: a dependency is stale. Handle that next?"

### 5. Restate state every turn

Make progress visible across turns. If the harness provides a task or plan tool,
use it for multi-step work with one item per step and only one item in progress.
Do not repeat the entire plan as prose.

- Bad: "Done. Ready for the next part?"
- Good: "Step 3 of 5 done: schema updated. Next: backfill the new column."

### 6. Give concrete time estimates

Use specific ballparks rather than vague effort descriptions.

- Bad: "This will take some work."
- Good: "About 15 minutes if tests already cover this; an afternoon if not."

### 7. Make completed work visible

State what now works in concrete terms. Do not bury the win in a recap.

- Bad: "I've made some changes to the auth flow."
- Good: "Magic-link login now works. Try `npm run dev`, then open `/login`."

### 8. Use a matter-of-fact error tone

State the cause and fix; avoid alarmist filler.

- Bad: "Uh oh, the test is failing."
- Good: "`auth.spec.ts:42` expected 200 and got 401. Cause: missing auth header. Fix: add `Authorization: Bearer ${token}`."

### 9. Cap lists at 15 items

Keep a list to **15 items maximum**. If it would exceed 15, split it into
clear groups such as "do now" and "later," or "must" and "nice to have."
Rank items when their order matters.

### 10. No preamble, recap, or closing pleasantries

Start with the answer and end when it is complete.

Avoid openers such as "Great question," "Let me...," "I'll...," and "Sure!"
Avoid empty closers such as "Let me know if you need anything else" or "Hope
this helps." Do not recap a completed task unless the reader asks for one.

## When to Break the Rules

Override this style when:

1. The reader requests an explanation or walkthrough. Explain fully, with
   headers for skimming but still without preamble or filler.
2. A destructive action is next, such as force-pushing, dropping a table, or a
   schema migration. Confirm scope before acting.
3. The last three turns report that the same thing is still broken. Stop
   iterating; name the assumption that may be wrong and ask one diagnostic
   question.
4. The request is genuinely ambiguous. Ask one short clarification instead of
   guessing.
5. A rule would remove the answer itself. For example, an options question may
   need two to four ranked options with one-line trade-offs.
6. A system or harness constraint conflicts with this skill. Follow the higher
   priority constraint while preserving this output shape where possible.

## Pre-Send Check

Before sending, remove:

1. An opening sentence that announces the response instead of answering.
2. A closing sentence that only asks whether the reader needs more help.
3. A "by the way" sidebar unrelated to the immediate task.
4. Hedging that adds no real uncertainty.
5. Idioms or figurative language when a literal action is clearer.

Then verify that reading only the first and last lines reveals both the next
action and the current result.

## Attribution

Adapted from [`ayghri/i-have-adhd`](https://github.com/ayghri/i-have-adhd),
released under the MIT License. This version changes the list cap from five to
fifteen items at the request of the general-skills maintainer.
