---
name: refresh-mega-sync
description: Refresh Ghost and Hoster MEGA Shared-folder sync safely.
---

# Refresh MEGA Sync

Use this when Ryushe says “refresh MEGA sync” or Ghost's `Shared` folder is not reaching Hoster. It rebuilds only the MEGA **sync configuration**, never deletes the underlying Shared data. It does not silently choose winners for content conflicts.

## When to Use

- A new file placed in Ghost `Shared` does not arrive on Hoster.
- `mega-sync` reports a stopped, disabled, stuck, or conflict-ridden Shared sync.
- Do not use for an intentional migration, account logout, or an unapproved deletion of cloud data.

## Prerequisites

- Run the Hoster portions through `terminal` with the SSH connection described by `hoster-ssh`.
- Ghost and Hoster must each have an active `mega-sync.service` and logged-in MEGAcmd account.
- The Ghost watchdog source is `~/.hermes/scripts/mega_shared_sync_watchdog.py`; it contains the current per-machine IDs and must be updated after a rebuild.

## Procedure

1. **Inspect both machines before changing anything.** Use `mega-sync` with `--path-display-size=200 --col-separator='|' --output-cols=ID,LOCALPATH,REMOTEPATH,RUN_STATE,STATUS,ERROR`, `mega-sync-issues --limit=0`, and `systemctl is-active mega-sync.service` locally and remotely. Record the exact current Shared ID and remote path on each machine.
   - Completion: each mapping and its service state are known; do not reuse IDs from a previous repair.

2. **Back up sync metadata on both machines.** Create a timestamped directory under `~/.megaCmd/repair-backup-<UTC timestamp>/` and copy `megacmd.cfg` plus `megaclient_syncconfig_*` into it.
   - Completion: both backup directories exist before pausing a sync.

3. **Rebuild Ghost's Shared mapping without deleting data.** Pause then delete the **configuration only** with `mega-sync --pause <id>` and `mega-sync --delete <id>`. Recreate it with the exact local and remote paths discovered in step 1, for example `mega-sync "$HOME/Shared/" /ghost_shared`.
   - Completion: the new Ghost mapping is `Running` and has a new ID.

4. **Rebuild Hoster's Shared mapping the same way.** Use its discovered path, typically `mega-sync "$HOME/Shared" "ghostonbutterbread@gmail.com:ghost_shared"`. Do not run durable MEGA work from SSH; only dispatch the bounded commands and close the connection.
   - Completion: the new Hoster mapping is `Running` and has a new ID.

5. **Update the watchdog IDs.** Use `patch` to replace `LOCAL_ID` and `REMOTE_ID` in the Ghost watchdog with the freshly reported IDs. Run the watchdog once with `terminal`.
   - Completion: it recognizes the new mappings. It may report unresolved conflicts, but must not try to re-enable obsolete IDs.

6. **Verify end-to-end with a new, non-hidden marker.** Use `date -u +%Y%m%dT%H%M%SZ`, then `write_file` a file named `~/Shared/MEGA_SYNC_TEST_<timestamp>.txt` on Ghost. Poll Hoster for that exact file with bounded SSH checks, then compare `sha256sum` on both machines.
   - Completion: Hoster has the marker and both SHA-256 values match.

## Conflict Handling

- A `Running` sync with `Sync Issues` is not healthy, but it can still transfer unrelated new files. Prove the real path with the marker test.
- MEGAcmd cannot synchronize symlinks reliably. Check `mega-sync-ignore --show <id>`; a `-s:*` exclusion keeps symlinks local and prevents them from becoming a general outage.
- Preserve every conflicting local file under the timestamped repair backup before replacing it with a known cloud copy. Use `mega-get <remote path> <empty backup/download directory>`; it avoids overwriting the source path directly.
- Do not automatically resolve `credentials`, account inventory, duplicate names, file-vs-folder paths, or large artifacts. These require a deliberate winner or a preserved cloud relocation.

## Verification

- `systemctl is-active mega-sync.service` returns `active` on Ghost and Hoster.
- Both rebuilt mappings show `Running`.
- The marker file arrives on Hoster with an identical SHA-256.
- Report separately any remaining isolated `mega-sync-issues`; never describe the system as conflict-free unless the issue list is empty.
