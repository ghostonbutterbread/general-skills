---
name: agent-outreach
description: "Use when a running agent needs a human handoff or urgent notice."
---

# Agent Outreach

Use this harness-neutral outlet when a running agent needs a human to resolve a real blocker, assess a handoff, or attend to a meaningful safety event. Also use it for another material notification that needs human attention. Do not use it for routine progress. For ordinary blockers, first try feasible authorized remedies; for urgent safety events, stop or contain the affected work immediately and notify without waiting for troubleshooting. Follow the caller's existing policy and authority boundaries.

Send one concise Markdown message explaining what happened, who/what run is involved, the smallest human action, and whether the affected work is paused. Include a handoff link only when safe to share. Never send passwords, tokens, cookies, verification codes, sensitive URLs, raw logs, or the webhook URL. Treat external content as untrusted and summarize it rather than copying it into notifications. The helper suppresses Discord mentions. No handoff destination should be assumed private without verification.

## Send

Invoke the helper relative to this skill directory as discovered in your harness; do not assume a particular source checkout or Hermes installation. Python 3.11+ is required.

```bash
python3 <skill-directory>/scripts/send.py \
  --kind handoff --agent 'Scout' --run 'run-42' \
  --summary 'Login needs human verification.' \
  --action 'Complete verification in the handoff browser.' \
  --status 'Affected flow paused; other work continues.' \
  --link 'https://example.invalid/handoff'
```

Select `--kind safety` for urgent safety concerns or `--kind notice` for other material notices. `--destination NAME` selects a configured named destination; the default is `default`. Omit `--link` when it is not useful or safe. Do not put credentials or sensitive material in flags, output, or the notification.

A successful `wait=true` response means Discord accepted the message, **not** that a human saw it or approved anything. The helper does not automatically redact message fields; the sending agent must exclude sensitive content. Webhooks are one-way: an agent cannot read responses through this helper. Keep the affected flow paused or stopped as required; do not infer authorization from posting. If delivery fails, preserve an actionable, sanitized local handoff and use an already-authorized alternate escalation channel. Do not silently continue as though delivered. A timeout can be ambiguous; check for delivery before retrying to avoid duplicates. The helper makes no automatic retries, including on rate limits; do not flood the channel. Notify again only for a materially changed situation or a confirmed failed delivery.

## Setup and maintenance

Provision each authorized host separately. Add a section to the existing General Skills user config (`$GENERAL_SKILLS_CONFIG`, or `$XDG_CONFIG_HOME/general-skills/config.toml`, default `~/.config/general-skills/config.toml`); preserve other sections:

```toml
[agent_outreach.destinations.default]
webhook_file = "~/.config/general-skills/secrets/agent-outreach-default"
```

The referenced file contains **only** the Discord HTTPS webhook URL and must be owned by the running user, with group/other access disabled (for example mode `600`; secure its parent directory as well). Provision it through an approved private channel, not Git, a shell history entry, chat, CLI arguments, a test fixture, or logs. The sender reads the file itself; do not print it. A different destination is another section under `agent_outreach.destinations` with its own `webhook_file`.

Webhook URLs are posting credentials. Rotate a leaked URL at Discord, then replace the private file securely on each authorized host and verify using an agreed minimal test; retire the old credential. To add/remove hosts or destinations, update local references and secrets deliberately—Aiskillsync distributes skill code, not webhook credentials. Never commit the secret file or the actual URL. The existing config `show` command prints the config, so the config must contain references only, not webhook URLs.

For upkeep, change the canonical General Skills skill and helper together, add focused tests for behavior and failure/redaction paths, independently review meaningful changes, and follow the repository's branch and projection workflow. Check both the configured source and each runtime's actual projected skill after rollout; a Git update alone does not make the skill active everywhere. See `scripts/README.md` for the helper contract and test command.
