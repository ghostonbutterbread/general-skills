# Account Table

Use this file to keep non-secret account and Bitwarden-reference context visible to agents.

Version 1 intentionally tracks only account-level state. Do not try to model every team, role, resource, design, invoice, or permission here yet.

## Canonical Paths

Prefer:

```text
~/Shared/web_bounty/{program}/shared/accounts.md
```

Fallback for legacy or non-web lanes:

```text
~/Shared/bounty_recon/{program}/shared/accounts.md
```

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
- Resource-level mutability is intentionally out of scope for v1. Put exact mutable resources in program notes or handoffs.

## Required Update Points

Agents must update this table in the same turn when:

- a Bitwarden item is created for a target account
- a Bitwarden item reference changes
- signup fails or is blocked
- an account moves from `pending-creation` to `active`
- deletion is approved, started, or completed
- a Bitwarden item is deleted after permanent account deletion

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
