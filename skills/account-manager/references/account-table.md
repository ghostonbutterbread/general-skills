# Account Table

## BBH registry (not this table)

For BBH-managed programs, load `account-management`. Its canonical registry is `$HARNESS_SHARED_BASE/{normalized-program}/credentials/account_inventory.json` (`HARNESS_SHARED_BASE` defaults to `~/Shared/web_bounty`). Follow that skill's normalization and `account_inventory.py` workflow. A `shared/accounts.md` file under `web_bounty` is legacy history, not an authority or fallback; do not write a parallel table. BBH lifecycle and destructibility semantics belong to `account-management`, not the legacy fields below.

## Legacy non-web path

Only for non-BBH programs that actually use the non-web lane:

```text
~/Shared/bounty_recon/{program}/shared/accounts.md
```

A missing BBH registry must be initialized via `account-management`, not replaced by this table. The remaining guidance on this page applies only to the legacy non-web table.

## Row Fields

Use a markdown table or repeated blocks. Keep it grep-friendly.

```text
Account alias:
Username/email:
Lifecycle status: pending-creation|active|removed-from-shared-resource|pending-deletion|deleted
Bitwarden item reference:
Destructible account: yes|no
Cleanup notes:
Last checked:
```

## Lifecycle Semantics

- `pending-creation`: account is planned or signup is in progress; do not use for testing yet.
- `active`: account exists and may be used according to its account-level destructible status and current task policy.
- `removed-from-shared-resource`: account was removed from a design/team/folder/invoice/resource as part of a test. The account still exists.
- `pending-deletion`: deletion is approved or in progress; do not use for new tests.
- `deleted`: target account was permanently deleted. The Bitwarden login item should be deleted after this is confirmed.

## Destructible Semantics

- `Destructible account: no`: default. Agents may not delete or burn the account.
- `Destructible account: yes`: account may be burned/deleted if the current task explicitly requires it.
- An existing verified-owned account may be reclassified from `no` to `yes`
  before a destructive test only after the record captures why it has no
  important data, roles, or entitlements, the intended destructive scope, and
  its cleanup/burn plan. Do not infer suitability from age, alias, or a
  sparse-looking UI.
- Resource-level mutability is intentionally out of scope for v1. Put exact mutable resources in program notes or handoffs.

## Required Update Points

Agents must update this table in the same turn when:

- a Bitwarden item is created for a target account
- a Bitwarden item reference changes
- signup fails or is blocked
- an account moves from `pending-creation` to `active`
- deletion is approved, started, or completed
- a Bitwarden item is deleted after permanent account deletion
- an account is reclassified as destructible or non-destructible

## Secret Handling

Never include:

- passwords
- Bitwarden session keys
- cookies or auth headers
- verification codes or links
- reset links
- card data or full invoices
- private message/email bodies

Use only Bitwarden item names or ids as references.
