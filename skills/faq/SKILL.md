---
name: faq
description: "Search and record problem-oriented solved fixes, scripts, and workarounds before agents re-solve recurring issues."
---

# FAQ

Use when an agent hits a blocker, tool error, setup issue, target quirk,
auth-flow problem, request-shape problem, or repeated workflow issue and needs
to know whether we already solved it.

FAQ is solved-problem memory. It is not general notes, hypotheses, todos, or
findings.

## First Move

1. Search FAQ before solving.
2. Prefer exact error strings, tool names, endpoint names, and flow names.
3. Check both scopes:
   - central: `/home/ryushe/notes/appsec/faq/`
   - active program: `~/Shared/{family}/{program}/{lane}/notes/faq/`
4. If an entry links a script, command, skill, or playbook, reuse it first.
5. If no entry exists, solve once and write the smallest reusable FAQ note.

## Helper

```bash
python3 /home/ryushe/projects/general-skills/skills/faq/scripts/faq_search.py \
  "chromium off flow auth" \
  --family web_bounty \
  --program canva \
  --lane web
```

## Storage

- Central FAQ: reusable cross-program fixes, tool failures, browser/proxy/Caido
  problems, common scripts, and agent workflow fixes.
- Program FAQ: target-specific auth flows, request shapes, endpoint quirks,
  owned-account setup, and platform-specific helper scripts.
- Project-local docs: implementation fixes that only matter inside one repo.
- Todo: future action that is not solved yet.

Read `references/faq-contract.md` for note shape, tags, indexing, and promotion
rules.

## Rules

- Store solved fixes, not raw logs.
- Include script paths, commands, or skill paths when they exist.
- Include full URLs for endpoints and sources.
- Keep failures scoped to the exact surface and context.
- Never store raw cookies, bearer tokens, API keys, passwords, private headers,
  reset links, credentials, or full proxy dumps.
