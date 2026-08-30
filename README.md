# General Skills

Reusable local OpenClaw/Codex skills that are not tied to one bug bounty harness or one target.

## Skills

- `safe-fetch` - Default external web-content ingestion through quarantine and sanitization unless explicitly bypassed.
- `faq` - Problem-oriented solved fixes, script lookup, and central/program FAQ routing before agents re-solve recurring issues.
- `papercuts` - Concise, sanitized records of agent workflow friction that later maintenance passes can verify and eliminate.
- `coordination` - Parent/child task splitting protocol for broad runs, focused subagents, and interactable child-run metadata.
- `skill-seeds` - Lightweight shared proposal format for new or changed skills, with Ghost as the only promotion point.
- `tmux` - Long-running session protocol for attachable recon, fuzzing, Arjun, scanner, and interactive CLI jobs; Hoster workloads defer to `hoster-ssh`.
- `hoster-ssh` - Bounded Hoster SSH dispatch and lifecycle protocol: durable workloads run in named user-systemd services, not `ssh.service`.
- `hoster-tmux-child-reaper` - Short-lived Hoster-entry cleanup sidecar: it reports or safely reaps only ownership-proven empty tmux scopes while the main worker begins its task; never timer-driven or a general pane cleaner.
- `script_manager` - Reusable script promotion, storage, indexing, and handoff rules so repeated agent workflows become durable helpers.
- `resilio-sync` - Resilio Sync handoff rules for `/srv/resilio` and large local file-set sharing.
- `daddy` - Relative model-up/down routing for CLI agents, with benchmark guardrails for cost and quality tradeoffs.
- `account-manager` - Non-secret account inventory workflow for roles, mutability, lifecycle state, and Bitwarden item references.
- `bitwarden` - Bitwarden CLI workflow for storing and referencing test-account credentials without exposing secrets.
- `account-tui-colors` - Terminal color guidance for account-oriented workflows.
- `gmail-otp` - Narrow Gmail OAuth inbox reader for user-initiated login/password-reset OTPs, with sending hard-allowlisted to `ryushe.dev@gmail.com`.
- `security-reporting` - Evidence-bound, triager-facing security report and PoC workflow.
- `evidence-first-vulnerability-reporting` - Two-artifact evidence and submission report workflow.
- `nightly-learning` - Report-only AppSec learning intake from a curated source registry, with safe-fetch provenance and manual promotion only.
- `i-have-adhd` - ADHD-friendly output mode: lead with the next action, show state, suppress tangents, and cap lists at 15 items.

All skills use the flat `skills/<skill>/SKILL.md` layout. This repository owns
general shared skills; capability-specific skills belong in their dedicated
repositories (for example, `coding-skills` and `job-search-skills`).

`bounty-storage` and `huge-ingest` are canonically owned by BBH as of its paired
adoption change; they are intentionally not general-skills entries.

## Script Index

- `SCRIPT_INDEX.md` - Map of reusable script homes and registry expectations.
