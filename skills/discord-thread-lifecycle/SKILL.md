---
name: discord-thread-lifecycle
description: "Create and maintain Discord thread names as visible lifecycle state: active, completed, or blocked/cancelled."
---

# Discord Thread Lifecycle

This is Hermes operating behavior maintained as a Hermes skill; do not place
this naming convention in the AI-policy repository.

Use this when creating, updating, closing, or summarizing a Discord thread
that represents an agent task, investigation, question, or handoff.

## Naming contract

Thread names begin with exactly one lifecycle marker, followed by the
**current work phrase**:

- `❔ <current work>` — **active / awaiting work or a decision**.
- `✅ <current work>` — **completed / verified**.
- `❌ <current work>` — **blocked / canceled**.

The phrase is intentionally live state, not an immutable original topic. Keep
it short and change it whenever the meaningful work phase changes, while
retaining the status marker. For example, an active thread can move from
`❔ building wayback skill` to `❔ patching wayback skill` once patching becomes
the work at hand.

Do not use `✅` for a merely planned, partial, or unverified outcome. Do not
turn an active thread into `❌` simply because an agent has paused; reserve it
for a real blocker or cancellation.

Examples:

```text
✅ built wayback skill
❔ building wayback skill
❌ issue building wayback skill
```

## Workflow

1. **Create active.** New agent-created task threads start as
   `❔ <current work>`. Include the marker in the `create_thread` name, not just
   in the opening message.
2. **Keep the work phrase current.** Rename the thread when work materially
   changes phase (for example, `❔ building wayback skill` →
   `❔ patching wayback skill`). Do not rename for routine minor progress.
3. **Record the state change in-thread.** When completing or blocking a task,
   post a short outcome or blocker message before changing the thread name.
   The name is a status index, not the evidence itself.
4. **Rename immediately after a verified transition.** Change the lifecycle
   marker and, when useful, phrase the result or issue in the current work
   text. Verify the returned or fetched thread name equals the intended name.
5. **Reopen when needed.** If new requested work resumes a completed or
   blocked thread, change it back to `❔ <current work>` and state the new
   objective in the thread.
6. **Do not bulk-infer status.** Never rename unrelated existing threads merely
   from age, inactivity, or an incomplete transcript. Update a thread only when
   its owner or the task's verified result supplies the status.

## Tooling and permission checks

- First obtain the Discord thread/channel ID from conversation context or the
  result of `create_thread`.
- Thread creation is available through `discord.create_thread`.
- Renaming requires Discord's **Manage Threads** permission and a tool action
  that sends `PATCH /channels/{thread_id}` with `{ "name": "…" }`.
- If that rename action is unavailable in the installed Hermes Discord tool,
  create new threads with the correct `❔` prefix and report the capability gap
  instead of claiming that an existing thread was renamed. A human moderator
  can apply the name manually until the action is installed.
- Treat a Discord 403 as a permission/configuration failure. Report the
  action, thread ID, and required **Manage Threads** permission; do not retry
  blindly.

## Completion checklist

Before marking `✅`:

- The requested deliverable or answer is present in the thread.
- Any requested verification actually ran and its outcome is recorded.
- The name reflects the completed result and has the `✅` marker.

Before marking `❌`:

- The blocker or cancellation reason is recorded in the thread.
- The next owner/action, if known, is stated.
- The name reflects the issue or cancellation and has the `❌` marker.

## Status updates from agent work

For a task that uses a dedicated Discord thread, agents should make a lifecycle
update at these boundaries:

- immediately after creation (`❔`)
- when waiting on a user decision or external dependency (`❔`, with a clear
  in-thread question)
- when the work materially changes phase (retain `❔`, update the work phrase)
- after verified completion (`✅`)
- after a terminal blocker or cancellation (`❌`)

Do not churn names for routine intermediate progress; put progress in messages.
