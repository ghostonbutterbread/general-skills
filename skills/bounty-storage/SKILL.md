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

Put canonical truth in `~/Shared`. Put long persistent bounty runs, stable heavy
artifact libraries, and bulky artifacts in `/mnt/bounty`. Put disposable run
scratch on the machine doing the work.

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
- artifact health notes for missing, stale, moved, or regenerated heavy data
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

Use a program-first layout. Keep stable category/corpus directories for normal
agent lookup, and keep `runs/<run_id>/` directories for history/provenance:

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
          by-host/
          by-sha256/
        sourcemaps/
        chunks/
        indexes/
        runs/<run_id>/
      pages/
      api/
    screenshots/
      admin/
      auth/
      billing/
      settings/
      unknown/
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
/mnt/bounty/canva/web/recon/javascript/downloads/by-host/static.canva.com/
/mnt/bounty/canva/web/recon/javascript/downloads/by-sha256/ab/abcdef...js
/mnt/bounty/canva/web/screenshots/admin/
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

For JavaScript, `downloads/by-host/` is the human browse path and
`downloads/by-sha256/` is the dedupe path. The host path keeps the URL origin
obvious; the SHA-256 path stores each unique JavaScript body once by content
hash.

For screenshots, stable folders such as `admin/`, `auth/`, `billing/`, and
`settings/` are the browseable library. `screenshots/runs/<run_id>/` preserves
what happened during a specific run.

## Artifact Maps And Health

Shared artifact maps are the first place agents should look for heavy bounty
artifacts. They should point to stable category/corpus paths first and run IDs
second for provenance.

Prefer machine-readable per-artifact maps:

```text
~/Shared/web_bounty/<program>/web/recon/artifacts/screenshots-map.json
~/Shared/web_bounty/<program>/web/recon/artifacts/javascript-map.json
~/Shared/web_bounty/<program>/web/recon/artifacts/proxy-flows-map.json
~/Shared/bounty_recon/<program>/apk/recon/artifacts/static-map.json
```

Use the Shared helper for concurrent-safe updates and health checks:

```bash
python3 ~/Shared/bounty_recon/_shared/scripts/bounty_artifact_map.py <program> screenshots --entry-json '<json>' --check
```

Markdown `artifact-map.md` files are human summaries. JSON maps are the
machine-readable source for agents.

When following a Shared artifact pointer, check that the target exists. If it is
missing, deleted, stale, or moved, update the artifact map with `status:
missing`, `stale`, `moved`, or `regenerate` and record the new path or
regeneration command when known. Do not silently recreate unrelated folders or
trust stale pointers.

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

## Trusted Promoters

Some tools already own their own canonical append/dedupe behavior. Use the
tool's native flow first, then write a Shared manifest or artifact-map pointer.

Approved trusted promoters:

```text
recon-ry
```

For `recon-ry`, the durable project root may remain the tool-owned project
directory, such as `/home/ryushe/bounties/<program>/` on Hoster. Its stable root
files, such as `urls.txt`, `alive.txt`, `params.txt`, and `jsfiles.txt`, are the
tool-owned canonical recon view. Agents should ingest or index those outputs
into Shared only when a Shared manifest/counts record is needed.

If a tool is not on this list, it follows the generic lifecycle: raw output in
`/mnt/bounty`, curated promotion into fixed Shared aggregate files, and a
manifest stating what was promoted.

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

## Moving Programs Out Of Shared

If `~/Shared` fills up, a program can be archived or moved without breaking the
system as long as Shared keeps a small pointer stub:

```text
~/Shared/web_bounty/<program>/ARCHIVED.md
~/Shared/web_bounty/<program>/archive-manifest.json
```

or:

```text
~/Shared/bounty_recon/<program>/ARCHIVED.md
~/Shared/bounty_recon/<program>/archive-manifest.json
```

Agents must treat those files as authoritative. They should not recreate a fresh
program tree in Shared until the archive manifest says where the active Shared
path is or Ryushe approves restoration.

Before writing Shared program state, resolve the target path:

```bash
python3 ~/Shared/bounty_recon/_shared/scripts/bounty_path_resolve.py <program> --surface web
```

For scripts:

```bash
shared_program_path="$(python3 ~/Shared/bounty_recon/_shared/scripts/bounty_path_resolve.py <program> --surface web --path-only)"
```

If the resolver reports `restore_required=true`, do not create a fresh Shared
tree. Use the archive manifest's active/moved path, or ask Ryushe to restore the
program first.

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
