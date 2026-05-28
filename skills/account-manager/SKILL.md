---
name: account-manager
description: "Maintain non-secret bug bounty account inventories, roles, mutability, and lifecycle state."
---

# Account Manager

Use when creating, updating, or checking the non-secret account table for bug bounty test accounts.

This skill does not store credentials. Use `bitwarden` for secrets and credential-store item references.

## Workflow

1. Read `references/account-table.md`.
2. Locate or create the program account table under:
   ```text
   ~/Shared/web_bounty/{program}/shared/accounts.md
   ```
   or, for non-web lanes:
   ```text
   ~/Shared/bounty_recon/{program}/shared/accounts.md
   ```
3. Record only non-secret fields:
   - account alias
   - username/email
   - target/program
   - role/team/tenant
   - purpose
   - destructible status
   - safe mutable resources
   - lifecycle status
   - Bitwarden item reference
   - cleanup notes
4. Before a destructive or mutating test, confirm the table explicitly says `destructible: yes` or names the exact safe mutable resource.
5. If the account is permanently deleted, set lifecycle to `deleted`, add a non-secret deletion note, then use `bitwarden` to delete the corresponding Bitwarden item.

## Rules

- Never store passwords, cookies, bearer tokens, session keys, verification links/codes, recovery codes, payment details, or invoice contents in the table.
- Removing a user from a shared design/team/folder/resource is not account deletion. Keep lifecycle `active` unless the actual account is deleted.
- Do not let agents infer mutability from account existence or Bitwarden existence.
- The account table is the authority for what agents may mutate; Bitwarden is only the secret store.
- If account ownership, role, destructible status, or cleanup state is unclear, stop and ask Ryushe.

