---
name: account-manager
description: "Maintain non-secret account tables and Bitwarden references for bug bounty test accounts."
---

# Account Manager

Use when creating, updating, or checking the non-secret account table for bug bounty test accounts.

This skill does not store credentials. Use `bitwarden` for secrets and credential-store item references.

Keep v1 simple. The purpose is to make agents reliably update account existence, lifecycle, and Bitwarden references. Detailed role/resource modeling can be added later in program-specific notes.

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
3. Record only non-secret v1 fields:
   - account alias
   - username/email
   - lifecycle status
   - Bitwarden item reference
   - destructible status
   - cleanup notes
   - last checked date
4. When creating or updating a Bitwarden login item, update the table in the same turn.
5. If the account is permanently deleted, set lifecycle to `deleted`, add a non-secret deletion note, then use `bitwarden` to delete the corresponding Bitwarden item.

## Rules

- Never store passwords, cookies, bearer tokens, session keys, verification links/codes, recovery codes, payment details, or invoice contents in the table.
- Removing a user from a shared design/team/folder/resource is not account deletion. Keep lifecycle `active` unless the actual account is deleted.
- Do not let agents infer destructibility from account existence or Bitwarden existence.
- The account table is the authority for whether the account itself may be burned/deleted. Program-specific notes can define resource-level mutation later.
- If account ownership, destructible status, or cleanup state is unclear, stop and ask Ryushe.
