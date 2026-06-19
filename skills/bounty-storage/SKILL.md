---
name: bounty-storage
description: "Route bug bounty files between cloud-backed Shared, mounted bounty artifacts, and local scratch."
---

# Bounty Storage

Use this before writing bug bounty artifacts, run outputs, downloaded corpora,
large recon datasets, screenshots, proxy data, browser profiles, or durable
findings state.

This is the storage policy. Workflow skills such as `/huge-ingest`, `/js`,
`/url-ingest`, `/hunter-loop`, `/tmux`, `/recon`, and vulnerability-lane skills
should load this when they need to decide where files belong.

## Core Rule

Put canonical truth in `~/Shared`. Put heavy working artifacts in `/mnt/bounty`.
Put disposable run scratch on the machine doing the work.

Do not put large raw corpora in `~/Shared` unless Ryushe explicitly asks for
cloud-backed retention.

## Storage Lanes

### Shared Truth

Path: `~/Shared`

Use for artifacts that should be backed up, easy for Ryushe to inspect, and
safe for future agents to treat as canonical:

- program scope, rules, policy, and account/resource notes
- findings, proof packets, and final reports
- tested/not-tested ledgers and coverage summaries
- lead summaries and handoffs
- run manifests and compact export summaries
- blocked queues, auth-required queues, redownload queues
- small JSONL/SQLite indexes that point to heavy artifacts
- sanitized request contracts and replay notes

Recommended bounty layout:

```text
~/Shared/bounty_recon/<program>/
  scope/
  credentials/              # references only, no secrets
  agent_shared/
    findings/
    hunter-loop/
    application-map/
  ghost/<skill-or-lane>/

~/Shared/web_bounty/<program>/web/
  recon/
  findings/
  reports/
```

### Mounted Bounty Artifacts

Preferred path: `/mnt/bounty`

Use for large working data that multiple machines/agents may need but that does
not need cloud backup:

```text
/mnt/bounty/artifacts/<program>/
  runs/<run_id>/
  corpus/
    js/
    pages/
    source/
    proxy-flows/
    api/
  screenshots/
  videos/
  browser-profiles/
  cdp-traces/
  chunks/
  indexes/

/mnt/bounty/cache/
  content-addressed/<sha256-prefix>/<sha256>
  downloads/
```

Examples:

- raw JavaScript/source bundles
- scraped HTML/page bodies
- screenshot and video sets
- proxy flow dumps and large request histories
- browser profiles, CDP traces, and HAR files
- chunk stores and parser intermediate output
- redownloadable corpora where URLs/manifests are preserved

Agents should write stable artifact pointers into `~/Shared` so another machine
can find the heavy data without copying it.

### Local Run Scratch

Preferred local scratch: `~/workdir/<program>/<run_id>/`

Accept existing project or host conventions when already established:

- Hoster active jobs: `/home/ryushe/artifacts/<program>/<run_id>/`
- local active jobs: `/home/ryushe/artifacts/<program>/<run_id>/`
- task-owned temp dirs under `/tmp` only for throwaway data

Use scratch for:

- active downloads
- parser temp files
- tool logs
- retry state
- partial output before promotion
- experiments that may be deleted

Scratch is not canonical. Before finishing, export a manifest or summary to
`~/Shared` and move heavy retained artifacts to `/mnt/bounty` when available.

## Fallback Order

When writing a large artifact:

1. If `/mnt/bounty` exists and is writable, use it.
2. Else use the current run host's artifact directory.
3. Else use `~/workdir/<program>/<run_id>/`.
4. Always write a small manifest into `~/Shared` that records the actual heavy
   artifact path and regeneration command.

Do not silently dump large data into `~/Shared` because `/mnt/bounty` is missing.

## Run Manifest

Every large run should leave a compact manifest in `~/Shared` with:

- `run_id`, `program`, `tool_or_skill`, `host`, `started_at`, `finished_at`
- scope assumptions and input sources
- shared output path
- heavy artifact root
- scratch path
- counts: inputs, fetched, reused, skipped, blocked, failed, parsed, packetized
- blocked/auth-required/redownload queue paths
- index paths and packet directories
- cleanup/retention notes
- exact command, script, or tmux session needed to resume or regenerate

Prefer JSON for machine use plus a short Markdown summary for humans.

## Sensitive Data

Never store real secrets, cookies, bearer tokens, passwords, reset links, API
keys, or private headers in Shared or bounty artifact storage.

For credentials, store references only:

- Bitwarden item reference
- account nickname or lane
- role and test-resource ownership
- non-secret setup notes

If proxy or browser artifacts contain sensitive headers/cookies, keep them in
controlled scratch or a clearly labeled restricted artifact path and write a
sanitized manifest/handoff instead.

## Agent Handoff

When handing work to another agent, pass:

- manifest path
- packet ID
- artifact pointer
- hash/chunk/range
- compact evidence excerpt
- allowed scope and stop condition

Do not pass huge directories, raw proxy dumps, browser profiles, or secret-bearing
files as prompt content.

