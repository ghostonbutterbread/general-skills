---
name: papercuts
description: "Use when an agent recovers from or is blocked by avoidable workflow friction and should leave a concise, safe record for later improvement."
---

# Papercuts

A papercut is small but real friction encountered while doing work: a dead-end
tool call, stale instruction, broken link, misleading error, missing discovery
step, brittle helper, or repeated manual workaround. Capturing it gives a later
maintenance pass evidence to remove the friction instead of making future
agents rediscover it.

Papercuts are **not** a live incident log, task tracker, raw transcript, or
permanent memory. They record the obstacle and its operational context; a
reviewer decides whether to fix, reject, or promote the lesson into a skill,
FAQ, script, or project documentation.

## When to Use

Record one whenever a concrete tool, browser/auth flow, instruction, or workflow
issue blocks progress or creates needless friction. Capture it immediately after
a safe workaround—or before handing off a blocker—without stopping to diagnose
it deeply.

A one-line description is enough. Do not record speculative complaints,
duplicates, user preference choices, or sensitive details. Do not interrupt an
active task to repair every papercut; log the friction quickly, then continue
when safe.

## Quick Capture

On this Hermes host, run the synced helper from the relevant project root:

```bash
PAPERCUTS_TOOL="$HOME/.hermes/synced-skills/papercuts/scripts/papercut.py"
python3 "$PAPERCUTS_TOOL" add \
  --category tool \
  --summary "Browser login kept failing" \
  --context "OAuth flow in the test browser"
```

The helper writes `PAPERCUTS.md` at the nearest Git root. Use `--file` to
choose an explicit shared or project record. It never makes network calls and
only appends to the selected Markdown file.

```bash
# Show unresolved entries.
python3 "$PAPERCUTS_TOOL" list

# Close a verified fix without deleting its evidence.
python3 "$PAPERCUTS_TOOL" close \
  --id PC-20260804-123456 \
  --resolution "Replaced the unavailable-command example and verified the fallback."
```

## Entry Standard

Keep entries short—usually one or two lines:

1. **Category:** `tool`, `docs`, `workflow`, `environment`, `integration`, or
   `other`.
2. **Summary:** what failed or created friction, in plain language.
3. **Context:** a few words naming the task, tool, or surface—not a raw
   transcript.
4. **Optional detail:** a sanitized error fragment, workaround, or brief reason
   to revisit it. Use `--impact` only when the reason is not obvious.

Never place credentials, cookies, tokens, authorization URLs, private target
data, raw request/response dumps, personal data, or customer content in a
papercut. Replace sensitive values with a class such as `[redacted token]`.

## Review and Promotion

During a deliberate maintenance pass:

1. Run `papercut.py list` for the relevant record.
2. Group duplicates by root cause; keep the clearest entry as evidence.
3. Verify the proposed fix in its real context before marking it closed.
4. Put the lasting knowledge in its canonical home:
   - solved operational workaround → `faq`;
   - repeatable automation → `script_manager`;
   - reusable behavioral workflow → a reviewed skill or skill seed;
   - repository-specific correction → that repository’s docs/code.
5. Close the source entry with the verified resolution and link/path to the
   durable fix.

Do not auto-promote papercuts to permanent memory. A record is a candidate for
improvement, not proof that a general rule is correct.

## Common Pitfalls

- **Venting without context:** rewrite it as an observable failure and impact.
- **Logging secrets or raw traffic:** redact it; use an artifact pointer when
  authorized instead.
- **Fixing the first report blindly:** reproduce or verify it before closure.
- **Treating it as a todo:** use the project tracker for planned work; retain
  the papercut only as the evidence of friction.
- **Losing closed history:** close entries in place rather than deleting them.

## Completion Criteria

A useful record has a clear cause, enough context for reproduction or triage,
no sensitive material, and an open/closed state. A reviewed item is complete
only when its fix is verified and its durable home is named in the resolution.
