# Composio mail and Hermes-only OTP relocation

- Branch docs/composio-mail; base 1015403; target beta.
- Latest owner direction supersedes already-published MCP-first mail: shared
  mail is a generic Composio inbox router, no embedded identity mapping; setup
  commands move to references/setup.md. Existing email-access-policy owns aliases.
- Remove gmail-otp from shared catalog. Preserve its tracked skill, script, and
  script README in the active bugfix profile's local skills/gmail-otp. No token
  or client configuration copied, read, or changed. Local docs explain profile
  state and invoke the relocated helper.
- Review: self-review plus offline routing/setup negative tests; no nested agent
  review available. CLI documentation verified from docs.composio.dev/docs/cli.
- Run tests and diff --check before integration. Parent must independently review.
- Activation blocker: prior focused synchronizer application is awaiting tool
  approval. Do not reissue blocked code. New rollout also needs managed removal
  of retired shared gmail-otp links; dry-run must avoid unrelated changes.
- Hoster still has prior d171517 shared skills until corrected rollout. No
  installer, mailbox read, login, or credential operation occurred.
- Successor: parent durable receipt; remove this dossier on integration.
