# Large File Sharing

Use `/srv/resilio` as the local sync handoff area for larger file sets.

## Rules

- Treat anything over 1 GB as a large single file.
- Prefer a dedicated subfolder per task, for example:
  ```text
  /srv/resilio/<project-or-target>/<YYYY-MM-DD>-<short-purpose>/
  ```
- Keep folder names descriptive and stable enough for Ryushe to find later.
- Include a short inventory in the chat response:
  - full path
  - file count
  - largest file name and approximate size
  - whether anything still needs cleanup
- Use File screenshots when sharing larger files through this path. The screenshot should show the folder/file inventory, not sensitive file contents.

## Sensitive Material

Do not place secrets, private keys, API keys, cookies, tokens, credentials, private configs, or real sensitive files in `/srv/resilio` unless Ryushe explicitly approves that exact handoff.

If an example is enough, create a sanitized template with fake-but-realistic values instead of syncing the real sensitive file.

## Verification

Before reporting done:

```bash
find /srv/resilio/<handoff-folder> -maxdepth 2 -type f -printf '%s %p\n' | sort -nr | head
```

Then summarize without dumping file contents.
