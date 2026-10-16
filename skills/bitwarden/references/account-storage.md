# Account Storage

## BBH-managed programs

For BBH account lookups, credential-reference updates, resource cleanup, and
account deletion, load `account-management` and follow its canonical
`$HARNESS_SHARED_BASE/{normalized-program}/credentials/account_inventory.json`
workflow (`HARNESS_SHARED_BASE` defaults to `~/Shared/web_bounty`). Follow that
skill's normalization, initialization, lifecycle, and `account_inventory.py`
commands. Do not create or update a parallel account/resource table or use the
legacy note lifecycle below as an authority for BBH. A missing registry must be
initialized through `account-management`, not replaced by notes. Keep Bitwarden
items as secret-store references; a shared-resource removal is not permanent
account deletion and does not by itself justify deleting a login item. Confirm
permanent account deletion and record the non-secret lifecycle/credential-reference
change in the canonical inventory before deleting the corresponding Bitwarden
item. Never infer destructibility or deletion approval from a Bitwarden item.

## Legacy account notes outside BBH

The account-note format and lifecycle rules below apply only to non-BBH
programs using legacy account/resource notes. They do not override
`account-management` for BBH.

### Account Note Format

Use this shape in target notes after credentials are stored:

```text
Account alias:
Username/email:
Target/program:
Purpose:
Destructible: yes|no
Destructible reason:
Lifecycle status: pending-creation|active|removed-from-shared-resource|pending-deletion|deleted
Credential store item:
Cleanup notes:
```

### Legacy Account Lifecycle Rules

For non-BBH programs only, separate resource cleanup from account deletion:

- Removing an account from a shared item, team, design, folder, invoice permission set, or other test resource does not mean the target account was deleted.
- For shared-resource removal, keep the Bitwarden login item active. Update the target account/resource table with the resource relationship and cleanup note.
- Permanently deleting the target account means the credential is no longer usable and Bitwarden must be updated.
- For permanent deletion, update local notes first with `Lifecycle status: pending-deletion`, perform the approved deletion, then update notes to `Lifecycle status: deleted`.
- After permanent deletion is confirmed, delete the Bitwarden login item. Keep the non-secret account table row for audit history with `Lifecycle status: deleted`.

Recommended account-table note before deleting the Bitwarden item:

```text
Target account permanently deleted on YYYY-MM-DD.
Do not use for testing.
Deletion confirmed by: <agent/operator>
Cleanup notes: <short non-secret note>
```

Agents must not infer destructibility or deletion permission from a Bitwarden item name. For these non-BBH notes only, the legacy account/resource table is the authority for account deletion decisions; resource-level mutation still requires task-specific approval. For BBH, use `account-management` and its canonical inventory instead.

## Safe Bitwarden Usage

- Prefer `BW_SESSION` from the current shell environment.
- If Bitwarden is locked, use the approved local password file through the helper. Set `BITWARDEN_SKILL_DIR` to the absolute directory containing the loaded `SKILL.md` if it is not installed at the Hermes default; source in the shell that will use `BW_SESSION`:
  ```bash
  BITWARDEN_SKILL_DIR="${BITWARDEN_SKILL_DIR:-$HOME/.hermes/synced-skills/bitwarden}"
  source "$BITWARDEN_SKILL_DIR/scripts/bw-session.sh"
  ```
- The approved default path is `~/.config/.bw.txt`.
- The password file must be owned by the current user and mode `600` or `400`.
- If using another approved local password file, pass it to `bw unlock --passwordfile`; do not `cat` it.
- Use `bw generate` for target-account passwords.
- Use `bw create item` or `bw edit item` through encoded JSON.
- Run `bw sync` after creating, editing, or deleting items.
- Output only item ids, item names, and non-secret metadata.

## Unsafe Patterns

Do not use:

```bash
cat /path/to/password-file
echo "$BW_SESSION"
echo "$TARGET_PASSWORD"
bw get password ...
bw get item ... | tee notes.md
```

Do not paste:

- Bitwarden master password
- target account password
- session key
- verification code or link
- reset link
- cookies or auth headers
- invoice PDFs or full private billing contents
