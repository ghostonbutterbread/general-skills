---
name: script_manager
description: "Use when turning repeated agent work into reusable scripts, organizing script homes, creating script records, or checking whether a helper already exists before writing new automation."
---

# Script Manager

Use this skill when an agent is doing repetitive, regex-heavy, file-processing,
URL-processing, diffing, extraction, normalization, reporting, or command
composition work that could become a reusable script.

The goal is simple: if agents solve a repeatable task once, future agents should
not have to rediscover the same workflow from chat history.

## First Move

1. Search for an existing script before writing one:
   ```bash
   rg -n "<task keyword>|<file type>|<tool name>" /home/ryushe/projects/general-skills /home/ryushe/.openclaw/workspace/scripts /home/ryushe/projects -g '*.md' -g '*.py' -g '*.sh'
   ```
2. Read `/home/ryushe/projects/general-skills/SCRIPT_INDEX.md`.
3. If the task is project-specific, inspect that repo's `scripts/`, `tools/`,
   `skills/*/scripts/`, and README files before creating a new helper.
4. Decide whether the work needs a script, a one-off shell command, or a note.

## When To Script

Create or promote a script when at least one is true:

- The same manual steps are likely to happen again.
- The task involves repeated parsing, regex extraction, diffing, dedupe, joins,
  chunking, normalization, or report generation.
- The output will feed another agent, tool, index, queue, or review workflow.
- The logic is easy to get subtly wrong by hand.
- The task processes enough files/URLs that manual effort will hide useful work
  from future agents.

Do not create a script for a tiny one-off command unless it captures a reusable
pattern.

## Storage Decision

Put scripts in the narrowest durable home:

- General reusable helpers: `/home/ryushe/projects/general-skills/skills/script_manager/scripts/`
- One skill's helper: `/home/ryushe/projects/general-skills/skills/<skill>/scripts/`
- Bug bounty skill helper: `/home/ryushe/projects/bug_bounty_harness/skills/<skill>/scripts/`
- Project-specific helper: `<repo>/scripts/` or `<repo>/tools/`
- OpenClaw host/runtime helper: `/home/ryushe/.openclaw/workspace/scripts/`

If unsure, start project-local. Promote to a general or skill-local home only
after the interface is stable and clearly reusable.

## Script Shape

Reusable scripts should:

- accept input paths, stdin, or both
- write explicit output files or stdout, not hidden side effects
- support `--help`
- support dry-run or read-only mode when mutation is possible
- keep raw inputs separate from derived outputs
- use deterministic output ordering where possible
- print concise progress and clear errors
- avoid secrets in args, logs, examples, fixtures, and manifests
- include a small smoke test, fixture, or documented manual verification

Prefer structured parsing over brittle regex when the input has a real parser.
Regex is fine for simple universal patterns like bracketed chunk names when the
delimiter and extension shape are stable.

## Record Contract

Every promoted script needs a record in the nearest `scripts/README.md` or in
`/home/ryushe/projects/general-skills/SCRIPT_INDEX.md`.

Minimum fields:

- script path
- purpose
- inputs
- outputs
- whether it mutates files or systems
- example command
- verification command or smoke test
- owner/scope
- last verified date

Use `references/script-record-template.md` for the shape.

## Example: Chunk Renderer URLs

For a task like extracting bracketed chunk names from many URLs:

1. Preserve the original URL list.
2. Extract chunk tokens with a narrow pattern, such as bracketed names ending in
   a known extension.
3. Normalize and sort unique chunk names.
4. Diff against the existing chunk file list, or append new entries with `anew`.
5. Write a summary: input count, extracted count, new count, output paths.
6. Add a script record so future agents know the helper exists.

The reusable interface should look like:

```bash
python3 <script> extract-chunks urls.txt --extensions js,css --output chunks.txt
python3 <script> diff-chunks chunks.txt known_chunks.txt --new-output new_chunks.txt
cat chunks.txt | anew known_chunks.txt
```

## Handoff

When finishing script work, report:

- where the script lives
- what recurring task it replaces
- the exact command to run it
- what files it reads and writes
- verification performed
- whether it was added to a script index or README

If a useful script idea is identified but not implemented, add a todo in the
right project tracker with enough detail for the next agent to build it.
