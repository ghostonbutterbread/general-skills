# Account Storage

## Account Note Format

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

## Account Lifecycle Rules

Separate resource cleanup from account deletion:

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

Agents must not infer destructibility or deletion permission from a Bitwarden item name. The account/resource table is the authority for what can be mutated or deleted.

## Safe Bitwarden Usage

- Prefer `BW_SESSION` from the current shell environment.
- If Bitwarden is locked, use the approved local password file through the helper:
  ```bash
  source skills/bitwarden/scripts/bw-session.sh
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
