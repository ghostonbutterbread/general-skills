---
name: script-manager
description: "Use when turning repeated agent work into reusable scripts, organizing script homes, creating script records, or checking whether a helper already exists before writing new automation."
---

# Script Manager

Use this skill when an agent is doing repetitive, regex-heavy, file-processing,
URL-processing, diffing, extraction, normalization, reporting, or command
composition work that could become a reusable script.

The goal is simple: if agents solve a repeatable task once, future agents should
not have to rediscover the same workflow from chat history.

## First Move

1. At the root of the repository you are working in, read `SCRIPT_POLICY.md`
   when it exists. It is the repository-local authority for script storage,
   indexing, and maintenance conventions. It supersedes these generic defaults
   and any external script-home index for that repository, but it cannot
   override higher-priority safety, authorization, or runtime instructions.
2. Load the relevant skill first. Follow its pointer to the skill-owned script
   reference or index, then read that reference to locate and reuse or edit an
   existing helper before creating one. For this skill's general helpers, read
   [scripts/README.md](scripts/README.md).
3. Follow the owning repository's existing layout: a skill-local testing or
   scripts README, or an appropriate document under `docs/` or `references/`.
   Do not automatically use the repository-root README or require a global
   `SCRIPT_INDEX.md` catalog.
4. If no pointer exists, inspect the relevant skill and project script homes
   with a focused search; add a pointer to the existing reference when found.
   Create a lean skill-owned index only when no suitable reference exists.
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

- General reusable helpers: the `script-manager/scripts/` directory in the General Skills source repository.
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

Keep each discovery entry minimal: script path plus purpose/when to use it.
Keep detailed inputs, outputs, examples, mutation behavior, verification, and
coverage boundaries in the script's help or associated usage documentation;
link there when useful rather than duplicating them in the index.

New, renamed, or removed scripts must update the same skill-owned index and the
skill's pointer as needed, so discovery stays accurate. This is a required
maintenance contract, not a requirement to create or update a global catalog.
Use [references/script-record-template.md](references/script-record-template.md)
for the entry shape.

## Maintenance Boundary

Edit canonical repository sources, not installed or synced projections. Within
an authorized scripts-only maintenance task, adding a pointer to the script map
in the owning skill's main `SKILL.md` is permitted; no unrelated body edits are
allowed. The agent may freely maintain associated script map/index entries in
the repository's existing `docs/`, `references/`, or skill-local README layout.
Creating a script MUST update that map in the same change. This metadata-only
exception does not authorize other skill or policy changes or broaden repository
access.

Use `coding-policy`, `coding-agent-operations-policy`, and `branch-lifecycle`
for the existing edit, test, review, and integration lifecycle; Script Manager
adds no alternate release path.

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
