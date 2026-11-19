---
name: refresh-mega-sync
description: Refresh Ghost and Hoster MEGA Shared-folder sync safely.
---

# Refresh MEGA Sync

Use this when Ryushe says “refresh MEGA sync” or Ghost's `Shared` folder is not reaching Hoster. Diagnose both sides first; an explicit refresh request warrants repair, not an automatic rebuild. When a rebuild is warranted, remove only the MEGA **sync configuration**, never the underlying Shared data. Do not silently choose winners for content conflicts. For the canonical diagnostic and conflict workflow, load `mega-sync-operations`.

## When to Use

- A new file placed in Ghost `Shared` does not arrive on Hoster.
- `mega-sync` reports a stopped, disabled, stuck, or conflict-ridden Shared sync.
- Do not use for an intentional migration, account logout, or an unapproved deletion of cloud data.

## Prerequisites

- Run the Hoster portions through `terminal` with the SSH connection described by `hoster-ssh`.
- Ghost and Hoster must each have an active `mega-sync.service` and logged-in MEGAcmd account.
- The Ghost watchdog source is `~/.hermes/scripts/mega_shared_sync_watchdog.py`; it contains the current per-machine IDs and must be updated after a rebuild.

## Procedure

1. **Inspect both machines before changing anything.** Use `mega-sync` with `--path-display-size=200 --col-separator='|' --output-cols=ID,LOCALPATH,REMOTEPATH,RUN_STATE,STATUS,ERROR`, `mega-sync-issues --limit=0`, and `systemctl is-active mega-sync.service` locally and remotely. Record the exact current Shared ID, local path, and remote path on each machine.
   - Completion: each mapping and its service state are known; do not reuse IDs from a previous repair.

2. **Diagnose each mapping and its issue paths.** Use `mega-sync-issues --detail --all --disable-path-collapse --limit=0` on both machines; compare the affected local/cloud path types and versions. A missing file or content conflict alone is not evidence that either mapping is broken. Address path-level conflicts as described below, without resetting a healthy mapping. For a stopped, conflict-free mapping, use `mega-sync --enable <id>` and re-read its status.
   - Completion: identify service, mapping, transfer, and path-level problems separately; keep unresolved conflicts explicit.

3. **Rebuild only a demonstrably broken mapping**, including after an explicit refresh request when the evidence warrants it; never rebuild both by default. Before pausing it, create a timestamped private directory under `~/.megaCmd/repair-backup-<UTC timestamp>/` on that machine and copy `megacmd.cfg` plus `megaclient_syncconfig_*` into it. Pause then delete the **configuration only** with `mega-sync --pause <id>` and `mega-sync --delete <id>`. Recreate it using the exact local and remote paths discovered in step 1, for example Ghost's `mega-sync "$HOME/Shared/" /ghost_shared` or Hoster's `mega-sync "$HOME/Shared" "ghostonbutterbread@gmail.com:ghost_shared"`. Do not run durable MEGA work from SSH; dispatch only bounded commands and close the connection.
   - Completion: each rebuilt mapping has the intended paths, is `Running`, and its new ID is recorded; leave other mappings unchanged.

4. **Update the watchdog after a rebuild.** Use `patch` to replace only the IDs of mappings actually rebuilt (`LOCAL_ID` for Ghost and/or `REMOTE_ID` for Hoster) in the Ghost watchdog with their freshly reported IDs. Leave the other ID unchanged. Run the watchdog once with `terminal`; if nothing was rebuilt, do not update IDs.
   - Completion: it recognizes the current mappings and must not try to re-enable obsolete IDs; report unresolved conflicts.

5. **Verify end-to-end with a new, non-hidden marker.** Use `date -u +%Y%m%dT%H%M%SZ`, then `write_file` a file named `~/Shared/MEGA_SYNC_TEST_<timestamp>.txt` on Ghost. Poll Hoster for that exact file with bounded SSH checks, then compare `sha256sum` on both machines.
   - Completion: Hoster has the marker and both SHA-256 values match.

## Conflict Handling

- A `Running` sync with `Sync Issues` is not healthy, but it can still transfer unrelated new files. Prove the real path with the marker test.
- MEGAcmd cannot synchronize symlinks reliably. Check `mega-sync-ignore --show <id>`; a `-s:*` exclusion keeps symlinks local, but add it only when their targets are intentionally outside the portable sync set.
- Before selecting a winner, compare the exact local and peer copies, fetch the cloud copy with `mega-get <remote path> <empty private backup/download directory>`, and hash it. Preserve every conflicting local file outside the synced root before replacing it with an established authoritative cloud copy; do not overwrite the source path directly with `mega-get`. Verify the resulting copies and report remaining issues separately.
- Do not automatically resolve `credentials`, account inventory, duplicate names, file-vs-folder paths, or large artifacts. These require a deliberate winner or a preserved cloud relocation.

## Verification

- `systemctl is-active mega-sync.service` returns `active` on Ghost and Hoster.
- Both mappings show `Running`; any rebuilt mapping has the intended paths and its new ID is recorded.
- The marker file arrives on Hoster with an identical SHA-256.
- Report separately any remaining isolated `mega-sync-issues`; never describe the system as conflict-free unless the issue list is empty.
