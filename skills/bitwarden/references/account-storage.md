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
Credential store item:
Cleanup notes:
```

## Safe Bitwarden Usage

- Prefer `BW_SESSION` from the current shell environment.
- If using a local password file, pass it to `bw unlock --passwordfile`; do not `cat` it.
- Use `bw generate` for target-account passwords.
- Use `bw create item` or `bw edit item` through encoded JSON.
- Run `bw sync` after creating or editing items.
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

