---
name: account-manager
description: "Route BBH account lookups to its canonical registry; maintain legacy non-web account tables outside BBH."
---

# Account Manager

Use when checking or updating non-secret bug bounty test-account context. This skill does not store credentials. Use `bitwarden` for secrets and credential-store item references.

## BBH-managed programs

Load BBH's `account-management` skill for account lookups and updates. Its canonical registry is `$HARNESS_SHARED_BASE/{normalized-program}/credentials/account_inventory.json` (`HARNESS_SHARED_BASE` defaults to `~/Shared/web_bounty`); follow its normalization, initialization, and `account_inventory.py` commands. A legacy `shared/accounts.md` is historical, not the authority for account status, credential references, or destructibility. Do not create or update a parallel Markdown table, and do not use this skill's legacy lifecycle/update rules for BBH programs.

## Legacy non-web programs outside BBH

Only for a program not managed by BBH that actually uses the non-web lane, read `references/account-table.md` and locate or create:

```text
~/Shared/bounty_recon/{program}/shared/accounts.md
```

A missing BBH registry is not a reason to fall back to this table; initialize it via `account-management` instead. For the legacy table, record only non-secret v1 fields:
- account alias
- username/email
- lifecycle status
- Bitwarden item reference
- destructible status
- cleanup notes
- last checked date

When creating or updating a Bitwarden login item, update the legacy table in the same turn. If the account is permanently deleted, set lifecycle to `deleted`, add a non-secret deletion note, then use `bitwarden` to delete the corresponding Bitwarden item.

## Rules

- Never store passwords, cookies, bearer tokens, session keys, verification links/codes, recovery codes, payment details, or invoice contents in account inventories.
- For the legacy non-web table, removing a user from a shared design/team/folder/resource is not account deletion. Keep lifecycle `active` unless the actual account is deleted.
- Do not let agents infer destructibility from account existence or Bitwarden existence.
- The legacy table is authoritative only for non-BBH non-web account deletion decisions. Program-specific notes can define resource-level mutation later.
- An agent may reclassify an existing verified-owned, low-residue account as
  destructible before a destructive test when it records why the account has no
  important data, roles, or entitlements; the intended destructive scope; and
  its cleanup/burn plan. Do not use age, an alias, or a sparse-looking UI as the
  basis for this classification.
- If account ownership, destructible status, or cleanup state is unclear, stop and ask Ryushe.
