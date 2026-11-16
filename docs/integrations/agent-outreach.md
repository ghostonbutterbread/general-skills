# Agent Outreach integration dossier

- **Status / owner:** feature in progress / Hermes, task `t_b922383b`.
- **Base:** `origin/beta` at `20189521b6aab6997ebde5a353542af2e63848de`; feature `feat/agent-outreach`; target `beta`.
- **Intent:** portable shared skill lets agents request human help or signal safety concerns with concise Markdown through named Discord webhooks. Keep webhook credentials in local private files referenced from General Skills config, never in Git. Provide future-maintainer instructions.
- **Contract:** one-way HTTP sender, suppress mentions, verify secret file permissions, refuse non-Discord destinations, no automatic retry, explicit delivery uncertainty. Successful delivery is not human acknowledgment. Config follows existing General Skills XDG and override precedence; helpers are skill-local for projected runtimes.
- **Evidence:** first focused sender test observed failing because sender was absent, then passing after implementation. Additional tests and independent review pending.
- **Boundaries:** Webhook provided in chat should be rotated before use. No production secret provisioned or live Discord post yet; end-to-end delivery remains unverified until an authorized secure credential and destination exist. Code publication, runtime projection, host secret provisioning, and live message verification are separate states.
- **Next:** run focused and safe broader tests, obtain independent review of the complete diff, address and re-review findings, then follow beta integration and projection workflow. Keep this dossier off beta.
