# General mail skill integration

- Intent: ordinary authorized inbox access, distinct from OTP-only access.
- Branch: docs/general-mail; base e8e18b9; target beta.
- Contract: shared mail owns Gmail MCP → Composio CLI order, secure setup
  handoff, no implicit mailbox mutation; email-access-policy owns test identities.
- Changes: mail skill, README route, gmail-otp compatibility route, offline tests.
- Evidence: official https://docs.composio.dev/docs/cli fetched directly and
  parsed; login, link gmail, search, execute and --get-schema confirmed. Installer
  downloaded for documentation inspection only, never executed. No mailbox read.
- Review: self-review against policy-authoring, email-access-policy, account and
  general-security routers, gmail-otp. No duplicate provider doctrine retained.
- Verification: run pytest on tests and diff --check before integration.
- Blocker: installed Composio unavailable; no live CLI/auth/mailbox test by design.
  On an authorized retrieval task, inspect installed --help and schemas first.
- Independent agent review unavailable in this child (no nested delegation).
- Activation: push beta, focused profile dry-run/apply/no-op; verify runtime
  links on local and Hoster. Fresh-agent behavioral smoke remains parent-owned.
- Successor: durable release receipt outside repository; remove this dossier on
  integration. No stable promotion requested.
