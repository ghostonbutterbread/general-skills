---
name: bitwarden
description: "Unlock and use Bitwarden CLI for owned test-account credentials, login fallback, and secret references."
---

# Bitwarden

Use when Ryushe explicitly requests Bitwarden, or when the selected owned
account's `account-registry`/program auth policy chooses its opaque Bitwarden
reference for a login or recovery step.

`account-registry` owns the login/recovery order: exact healthy browser,
profile provisioning, Bitwarden/password plus approved mailbox/OTP when the
policy declares it, browser verification, then private operator handoff only
for a declared human-only blocker. Do not invent a proxy, email, OTP, or manual
fallback order here; use this skill only for its selected vault step.

## Required Rules

1. Never print or store passwords, master passwords, session keys, cookies, bearer tokens, recovery codes, verification codes, reset links, or full private emails in chat, prompts, notes, or findings.
2. Do not read a master-password file directly into model-visible output. Use Bitwarden CLI `--passwordfile` or the provided sourced helper.
3. Before using Bitwarden CLI, run `bw --version`; do not use npm package version `2026.4.0`.
4. Check `bw status`. If locked, unlock only through Ryushe-approved `~/.config/.bw.txt` or through manual operator unlock.
5. Store durable target credentials in Bitwarden. Local notes may contain only account alias, username/email, target, purpose, destructible status, cleanup note, lifecycle status, and Bitwarden item name/id.
6. If the target requires human verification, load `references/human-verification.md`.

## Workflow

1. Read `references/account-storage.md`.
2. Run Bitwarden preflight:
   ```bash
   bw --version
   bw status
   ```
3. If locked, source the helper. It defaults to the approved local password file `~/.config/.bw.txt` and refuses unsafe ownership or permissions:
   ```bash
   source skills/accounts/bitwarden/scripts/bw-session.sh
   ```
4. For login to an existing target account, search by program, domain, account
   alias, or known Bitwarden reference. Use only the minimum fields needed for
   the login step, and keep raw secrets out of model-visible output.
5. Create or update a target-account item without printing generated secrets:
   ```bash
   skills/accounts/bitwarden/scripts/bw-create-login.sh \
     "Canva.cn ryushe+ai" \
     "ryushe+ai@bugcrowdninja.com" \
     "https://www.canva.cn/"
   ```
6. Record only the item name/id and non-secret metadata in the relevant account handoff.
7. For account cleanup or deletion, follow the lifecycle rules in `references/account-storage.md`.

## Handoff Rules

- Record durable references as `bitwarden:<item-name-or-id>` only.
- Store non-secret identity details with `/account-management`: account alias,
  approved email/username, user ID, role/tenant, PwnFox color, and destructible
  status.
- If a child agent needs login context, pass an account alias and Bitwarden
  reference, not the secret value.
- If a browser automation tool cannot consume the secret without printing or
  persisting it, stop and ask Ryushe for a manual handoff.

## Stop Conditions

- Bitwarden is locked and no approved local unlock path is available.
- The master-password file is not owned by the current user or is group/world readable.
- The target blocks signup, requires phone/KYC/payment, or shows unresolved human verification.
- A command would expose a secret in stdout/stderr, shell history, logs, prompts, notes, or chat.
- The requested cleanup action is ambiguous between removing the account from a shared resource and permanently deleting the login/account.
