---
name: bounty-storage
description: "Route bug bounty files between cloud-backed Shared, mounted bounty artifacts, and local scratch."
---

# Bounty Storage

Use this before writing bug bounty artifacts, run outputs, downloaded corpora,
large recon datasets, screenshots, proxy data, browser profiles, or durable
findings state.

Canonical policy document:

`/home/ryushe/projects/ai-policies/policies/bug-bounty/bounty-storage.md`

Workflow skills such as `/huge-ingest`, `/js`, `/url-ingest`, `/hunter-loop`,
`/tmux`, `/recon`, and vulnerability-lane skills should load this when they need
to decide where files belong.

## First Move

When working on a bounty engagement and scripts are relevant, check:

`~/Shared/bounty_recon/_shared/script-index.md`

Then check:

`~/Shared/bounty_recon/_shared/scripts/README.md`

This is how agents know the Shared script lane exists. Use it for small reusable
bounty scripts and records; keep heavy inputs and generated outputs in
`/mnt/bounty` or scratch.

## Core Rule

Put canonical truth in `~/Shared`. Put long persistent bounty runs and heavy
artifacts in `/mnt/bounty`. Put disposable run scratch on the machine doing the
work.

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
- artifact maps that point to `/mnt/bounty`
- blocked queues, auth-required queues, redownload queues
- small JSONL/SQLite indexes that point to heavy artifacts
- sanitized request contracts and replay notes
- small reusable bug bounty scripts and script records

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
    urls/
      urls.txt
      params.txt
      endpoints.txt
    js/
      js_urls.txt
    artifact-map.md
  findings/
  reports/

~/Shared/bounty_recon/<program>/apk/
  recon/
    artifact-map.md
  findings/
  reports/

~/Shared/bounty_recon/_shared/
  scripts/
  script-index.md
  templates/
```

### Mounted Bounty Artifacts

Preferred path: `/mnt/bounty`

Use for long-running bounty runs and large working data that multiple
machines/agents may need but that does not need cloud backup.

Use a program-first layout:

```text
/mnt/bounty/<program>/
  web/
    recon/
      fuzzing/
        <target-slug>/
          runs/<run_id>/
          index.jsonl
      subdomains/
        runs/<run_id>/
        index.jsonl
      javascript/
        urls/
        downloads/
        sourcemaps/
        chunks/
        indexes/
        runs/<run_id>/
      pages/
      api/
    screenshots/
      runs/<run_id>/
      index.jsonl
    proxy/
      flows/
      har/
      runs/<run_id>/
    videos/
    browser-profiles/
    cdp-traces/
  apk/
    static/
      decompile/
      jadx/
      apktool/
    dynamic/
      traces/
      frida/
      screenshots/
    runs/<run_id>/

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
- persistent fuzzing, recon, subdomain, JavaScript, screenshot, and proxy runs

Examples:

```text
/mnt/bounty/canva/web/recon/fuzzing/accounts-api/runs/<run_id>/
/mnt/bounty/canva/web/recon/javascript/downloads/
/mnt/bounty/canva/web/screenshots/runs/<run_id>/
/mnt/bounty/canva/web/proxy/flows/<flow-set>/
/mnt/bounty/canva/apk/static/jadx/runs/<run_id>/
```

Agents should write stable artifact pointers into `~/Shared` so another machine
can find the heavy data without copying it. Curated aggregate lists live in
Shared; heavy evidence and raw output live in `/mnt/bounty`. For example, a
parameter fuzz run writes raw output under
`/mnt/bounty/<program>/web/recon/fuzzing/<target-slug>/runs/<run_id>/`, then
appends new unique discovered URLs or params into the appropriate Shared list
with a dedupe tool such as `anew`.

## Canonical Aggregates

To avoid drift, append only to known aggregate files unless the run manifest
explicitly declares a new aggregate:

```text
~/Shared/web_bounty/<program>/web/recon/urls/urls.txt
~/Shared/web_bounty/<program>/web/recon/urls/endpoints.txt
~/Shared/web_bounty/<program>/web/recon/urls/params.txt
~/Shared/web_bounty/<program>/web/recon/js/js_urls.txt
~/Shared/bounty_recon/<program>/apk/recon/endpoints.txt
~/Shared/bounty_recon/<program>/apk/recon/deeplinks.txt
~/Shared/bounty_recon/<program>/apk/recon/permissions.txt
```

Do not create ad hoc files inside aggregate directories just because a tool used
a different output name. Raw output stays in `/mnt/bounty`; only curated unique
items get appended to Shared.

## Long-Running Runs

Long persistent runs should use `/tmux`, a manifest under `~/.tmux_sessions/`,
raw output under `/mnt/bounty`, and a compact Shared manifest/artifact-map entry.
Agents can check completion with:

```bash
python3 ~/Shared/bounty_recon/_shared/scripts/bounty_run_watch.py --program <program> --update
```

For active monitoring:

```bash
python3 ~/Shared/bounty_recon/_shared/scripts/bounty_run_watch.py --program <program> --watch --interval 120 --update
```

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

Scratch is not canonical. Long persistent runs should prefer `/mnt/bounty`
directly when it is writable. Use scratch only for temporary staging or when the
mount is missing, then export a manifest or summary to `~/Shared` and move heavy
retained artifacts to `/mnt/bounty` when available.

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
- surface, such as `web` or `apk`
- category path, such as `web/recon/fuzzing/<target-slug>` or `web/recon/javascript`
- counts: inputs, fetched, reused, skipped, blocked, failed, parsed, packetized
- blocked/auth-required/redownload queue paths
- index paths and packet directories
- curated Shared lists updated from the run
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

## Reusable Scripts

Small reusable bounty scripts can live in:

`~/Shared/bounty_recon/_shared/scripts/`

Do not put virtual environments, dependencies, bulky fixtures, generated output,
raw target data, or secrets there. If a script depends on a repo, keep the source
in that repo and put only a small Shared record or wrapper pointing to the repo
path and commit.

## Edge Cases

Read the canonical policy for the only policy-level edge cases:

- `/mnt/bounty` missing or not writable
- concurrent agents writing at once
- different machines having different local paths
- retention: keep vs regenerate vs expire

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
