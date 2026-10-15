# Papercuts Helper

## `papercut.py`

- **Purpose:** capture severity-rated sanitized friction; observe distinct recurrences on an existing ID; list by effective severity; close with history preserved.
- **Inputs:** subcommand arguments; optional `--file` or `PAPERCUTS_FILE`. New entries require severity, breaking status, reason, non-sensitive incident ID, and observed minutes lost.
- **Outputs:** `~/Shared/PAPERCUTS.md` by default; `list` writes only stdout. Existing unrated entries remain readable and are rated on their next observation.
- **Safe to run on:** local worktrees and explicitly selected Markdown records. For tests always use a temporary `--file`, not the live shared record.
- **Mutates:** only the selected Markdown record; creates parents/file on add and an advisory lock file on write.
- **Example:**
  ```bash
  python3 papercut.py add --category tool --summary "Example helper failed" \
    --context "local test" --severity low --breaking no \
    --reason "One retry needed" --minutes-lost 2 --incident "agent:run-1"
  ```
- **Tests:** `python3 -m unittest discover -s skills/papercuts/tests -v` from the repository root.
- **Owner/scope:** shared general-skills workflow; see `../references/capture.md` for rubric and deduplication guidance.
