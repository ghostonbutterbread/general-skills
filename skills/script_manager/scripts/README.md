# Script Manager Scripts

General reusable helper scripts can live here when they are not owned by a more
specific skill or project.

Before adding a script here, ask:

- Is this useful outside one project or target?
- Is the interface stable enough for future agents?
- Would a narrower skill-local or project-local `scripts/` directory be easier
  to find?

## Records

Add one record per script.

### Pending: chunk extractor helper

- Purpose: extract stable bracketed chunk filenames from URL lists, compare them
  with an existing chunk/file list, and emit newly observed chunks.
- Scope: general, if implemented with configurable delimiters/extensions.
- Inputs: URL list from file or stdin; optional known chunk file list.
- Outputs: normalized chunk list, optional new-only list, summary JSON/text.
- Mutates: no by default; optional append should be explicit and compatible with
  `anew`.
- Example:
  ```bash
  python3 skills/script_manager/scripts/chunk_list.py extract urls.txt --output chunks.txt
  python3 skills/script_manager/scripts/chunk_list.py diff chunks.txt known_chunks.txt --new-output new_chunks.txt
  ```
- Verification: fixture with repeated URLs, duplicated chunks, mixed extensions,
  and no-match lines.
- Related skill: `script_manager`
- Last verified: not implemented yet
