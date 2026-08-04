# Papercuts Helper

## `papercut.py`

- **Purpose:** append, list, and close concise sanitized agent-friction records.
- **Inputs:** subcommand arguments; optional `--file` or `PAPERCUTS_FILE`.
- **Outputs:** `PAPERCUTS.md` at the nearest Git root by default; `list` writes only stdout.
- **Safe to run on:** local project worktrees and explicitly selected Markdown records.
- **Mutates:** only the selected Markdown record; it creates parents/file when adding.
- **Example:**
  ```bash
  python3 papercut.py add --category tool --summary "Example" \
    --context "local test" --impact "cost a retry"
  ```
- **Tests:** `python3 -m unittest discover -s tests -p 'test_*.py'` from the general-skills beta worktree.
- **Owner/scope:** shared general-skills workflow.
- **Last verified:** 2026-08-04.
