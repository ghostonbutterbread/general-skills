# Account Table

Use this file to keep non-secret testing context visible to agents.

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
Target/program:
Role/team/tenant:
Purpose:
Destructible: yes|no
Safe mutable resources:
Lifecycle status: pending-creation|active|removed-from-shared-resource|pending-deletion|deleted
Bitwarden item reference:
Cleanup notes:
Last checked:
```

## Lifecycle Semantics

- `pending-creation`: account is planned or signup is in progress; do not use for testing yet.
- `active`: account exists and may be used according to its role/destructible/resource fields.
- `removed-from-shared-resource`: account was removed from a design/team/folder/invoice/resource as part of a test. The account still exists.
- `pending-deletion`: deletion is approved or in progress; do not use for new tests.
- `deleted`: target account was permanently deleted. The Bitwarden login item should be deleted after this is confirmed.

## Mutability Semantics

- `Destructible: no`: default. Agents may not delete the account or destructive resources.
- `Destructible: yes`: account may be burned/deleted if the current task explicitly requires it.
- `Safe mutable resources`: exact private owned resources agents may modify for proof, such as a test design, avatar, folder, team, invoice permission set, or dummy upload.

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
