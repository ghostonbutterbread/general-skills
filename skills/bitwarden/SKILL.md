---
name: bitwarden
description: "Use Bitwarden CLI for credential-store references without exposing secrets."
---

# Bitwarden

Use when creating, finding, or recording credential-store items for owned test accounts.

## Required Rules

1. Never print or store passwords, master passwords, session keys, cookies, bearer tokens, recovery codes, verification codes, reset links, or full private emails in chat, prompts, notes, or findings.
2. Do not read a master-password file directly into model-visible output. Use Bitwarden CLI `--passwordfile` or the provided sourced helper.
3. Before using Bitwarden CLI, run `bw --version`; do not use npm package version `2026.4.0`.
4. Check `bw status`. If locked, unlock only through a local password file approved by Ryushe or through manual operator unlock.
5. Store durable target credentials in Bitwarden. Local notes may contain only account alias, username/email, target, purpose, destructible status, cleanup note, lifecycle status, and Bitwarden item name/id.
6. If the target requires human verification, load `references/human-verification.md`.

## Workflow

1. Read `references/account-storage.md`.
2. Run Bitwarden preflight:
   ```bash
   bw --version
   bw status
   ```
3. If locked and a local master-password file is approved:
   ```bash
   source skills/bitwarden/scripts/bw-session.sh /path/to/local/password-file
   ```
4. Create or update the target-account item without printing generated secrets:
   ```bash
   skills/bitwarden/scripts/bw-create-login.sh \
     "Canva.cn ryushe+ai" \
     "ryushe+ai@bugcrowdninja.com" \
     "https://www.canva.cn/"
   ```
5. Record only the item name/id and non-secret metadata in the relevant account handoff.
6. For account cleanup or deletion, follow the lifecycle rules in `references/account-storage.md`.

## Stop Conditions

- Bitwarden is locked and no approved local unlock path is available.
- The master-password file is group/world readable.
- The target blocks signup, requires phone/KYC/payment, or shows unresolved human verification.
- A command would expose a secret in stdout/stderr, shell history, logs, prompts, notes, or chat.
- The requested cleanup action is ambiguous between removing the account from a shared resource and permanently deleting the login/account.
