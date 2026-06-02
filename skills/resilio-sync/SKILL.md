---
name: resilio-sync
description: "Use Resilio Sync for large local file-set handoffs and sharing rules."
---

# Resilio Sync

Use when a task involves large files, large file sets, synced handoff folders, or the `/srv/resilio` sync area.

## Core Facts

- Sync root: `/srv/resilio`
- Large single-file threshold: anything over 1 GB is a large file.
- Use this path for local-style sync of larger file sets instead of trying to push them through chat.
- When sharing larger files through this path, use File screenshots so Ryushe can inspect what was placed there without dumping the content into chat.

## Workflow

1. Read `references/large-file-sharing.md`.
2. Verify the target path exists before writing:
   ```bash
   test -d /srv/resilio
   ```
3. Create a clear subfolder for the handoff, named by project or date.
4. Put only the files needed for the handoff in that folder.
5. Report the full `/srv/resilio/...` path and a concise inventory.
6. Do not paste large file contents, secrets, credentials, cookies, tokens, or private configs into chat or notes.

## Stop Conditions

- `/srv/resilio` is missing or not writable.
- The file contains secrets or sensitive private material and Ryushe has not explicitly approved this storage path for that material.
- The handoff would include unrelated bulk data that has not been scoped.
