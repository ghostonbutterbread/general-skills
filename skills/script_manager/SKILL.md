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

1. At the repository root, read `SCRIPT_POLICY.md` when it exists. It is the
   repository-local authority for script storage, indexing, and maintenance
   conventions. It may specialize these generic defaults, but it cannot
   override higher-priority safety, authorization, or runtime instructions.
2. Search the current project and the installed General Skills projection before writing one:
   ```bash
   rg -n "<task keyword>|<file type>|<tool name>" . "$HOME/.hermes/synced-skills" -g '*.md' -g '*.py' -g '*.sh'
   ```
3. Read `SCRIPT_INDEX.md` at the General Skills repository root when working from a source checkout; otherwise inspect the relevant installed skill's `scripts/README.md`.
4. If the task is project-specific, inspect that repo's `scripts/`, `tools/`,
   `skills/*/scripts/`, and README files before creating a new helper.
5. Decide whether the work needs a script, a one-off shell command, or a note.

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

Multiple cohesive scripts are valid when they own different jobs, interfaces,
or lifecycles. Do not force unrelated behavior into one giant script. Reuse or
extend a documented helper when its responsibility already matches; create a
separate helper when the responsibility is materially different.

## Deterministic Mechanics, Bounded Authority

Prefer documented scripts for deterministic, repeatable mechanics such as
enumeration, parsing, normalization, deduplication, joining, and artifact
publication. Reuse an existing documented helper before creating another one.
This preference transfers mechanical work to scripts; it does not transfer
semantic or open-world judgment.

Classify script output as:

- **Observed facts:** mechanically derived values with evidence or provenance.
- **Seed signals:** deterministic pattern matches for prioritization, explicitly
  non-exhaustive.
- **Unknowns:** unsupported, unfamiliar, ambiguous, computed, or unclassified
  behavior that still requires agent interpretation.

Heuristic or vocabulary-driven output must declare its coverage boundary. Use
`exhaustive: false` unless exhaustiveness is genuinely proved by a closed input
contract. If coverage metadata is absent, interpret it as `exhaustive: false`.
Zero matches must never be promoted into “absent,” “safe,” “complete,” or “fully
searched.” Agents remain responsible for semantic context, unfamiliar
technologies, computed behavior, ambiguity, and unknowns.

Do not silently teach a running script from one agent observation. Promote a
confirmed miss only with preserved triggering evidence, a failing fixture or
test, a generalized implementation, validation against false positives, and
review. If the durable lesson belongs in another skill or repository, propose it
through that repository's normal skill-seed or review workflow rather than
creating a parallel helper.

## Storage Decision

Put scripts in the narrowest durable home:

- General reusable helpers: the `script_manager/scripts/` directory in the General Skills source or active synced projection.
- One skill's helper: that skill's `scripts/` directory.
- Project-specific helper: `<repo>/scripts/` or `<repo>/tools/`.
- Host/runtime helper: the runtime's configured local scripts directory; do not assume an OpenClaw workspace.

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
`SCRIPT_INDEX.md`.

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

For heuristic or vocabulary-driven output, also record the coverage boundary;
default it to `exhaustive: false` unless a closed input contract proves
otherwise.

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
