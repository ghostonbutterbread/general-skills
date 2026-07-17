# General Skills

Reusable local OpenClaw/Codex skills that are not tied to one bug bounty harness or one target.

## Skills

- `bitwarden` - Bitwarden CLI workflow for storing and referencing test-account credentials without exposing secrets.
- `account-manager` - Non-secret account inventory workflow for roles, mutability, lifecycle state, and Bitwarden item references.
- `resilio-sync` - Resilio Sync handoff rules for `/srv/resilio` and large local file-set sharing.
- `safe-fetch` - Default external web-content ingestion through quarantine and sanitization unless explicitly bypassed.
- `faq` - Problem-oriented solved fixes, script lookup, and central/program FAQ routing before agents re-solve recurring issues.
- `tmpmail` - tmpmail CLI workflow for disposable terminal inboxes in owned test flows.
- `tmux` - Long-running session protocol for attachable recon, fuzzing, Arjun, scanner, SSH, and interactive CLI jobs.
- `coordination` - Parent/child task splitting protocol for broad runs, focused subagents, and interactable child-run metadata.
- `daddy` - Relative model-up/down routing for CLI agents, with benchmark guardrails for cost and quality tradeoffs.
- `script_manager` - Reusable script promotion, storage, indexing, and handoff rules so repeated agent workflows become durable helpers.
- `skill-seeds` - Lightweight shared proposal format for new or changed skills, with Ghost as the only promotion point.
- `huge-ingest` - Large dataset ingestion protocol for URL/code/page/proxy/artifact corpora, bounded packets, lane dispatch, and bounty storage routing.
- `bounty-storage` - Bug bounty storage policy for `~/Shared`, `/mnt/bounty`, and local scratch lanes.
- `gmail-otp` - Narrow Gmail OAuth inbox reader for user-initiated login/password-reset OTPs, with sending hard-allowlisted to `ryushe.dev@gmail.com`.

## Script Index

- `SCRIPT_INDEX.md` - Map of reusable script homes and registry expectations.
