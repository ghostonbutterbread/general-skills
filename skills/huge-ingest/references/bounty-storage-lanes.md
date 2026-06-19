# Bounty Storage Lanes

Status: draft
Owner: Ghost
Canonical path: `skills/huge-ingest/references/bounty-storage-lanes.md`
Last reviewed: 2026-06-19

## Intent

Keep cloud-backed `~/Shared` small and important while still giving all agents a
common place to work with large bounty datasets.

## Tier 1: Cloud-backed Shared Truth

Path: `~/Shared`

Use for artifacts that should be backed up, human-readable, and easy to inspect:

- program scope, rules, policy, and account/resource notes
- canonical ledgers: findings, tested state, blocked queues, auth-required queues
- run manifests and export summaries
- lead summaries, handoffs, and proof packets
- small SQLite indexes or JSONL indexes that are worth keeping
- final reports and reproducible PoC notes

Avoid storing heavy raw corpora here unless Ryushe explicitly wants them backed
up.

## Tier 2: Bounty Artifact Share

Preferred path: `/mnt/bounty`

Use this for large working data that agents need to read but that does not need
cloud backup:

- `/mnt/bounty/artifacts/<program>/runs/<run_id>/`
- `/mnt/bounty/artifacts/<program>/corpus/js/`
- `/mnt/bounty/artifacts/<program>/corpus/pages/`
- `/mnt/bounty/artifacts/<program>/corpus/proxy-flows/`
- `/mnt/bounty/artifacts/<program>/screenshots/`
- `/mnt/bounty/artifacts/<program>/browser-profiles/`
- `/mnt/bounty/cache/content-addressed/<sha256>`

All machines should mount the same path when available so packets can use stable
artifact pointers.

## Tier 3: Run Host Scratch

Examples:

- Hoster: `/home/ryushe/artifacts/<program>/<run_id>/`
- Local fallback: `/home/ryushe/artifacts/<program>/<run_id>/`
- Project-specific fallback when already established

Use for active compute, temporary downloads, parser scratch, and long-running
job logs. At run end, export:

- compact manifest and summary to `~/Shared`
- heavy artifacts to `/mnt/bounty` when mounted
- regeneration commands for disposable data

Scratch may expire. Do not make scratch the only source of canonical truth.

## Manifest Contract

Every large ingest should produce a small manifest in `~/Shared` containing:

- `run_id`, `program`, `started_at`, `finished_at`, `status`
- input sources and scope assumptions
- raw/corpus/artifact roots
- counts: inputs, fetched, reused, skipped, blocked, failed, parsed, packetized
- storage decisions and cleanup/retention hints
- queues for blocked/auth-required/redownload candidates
- index paths and packet directories
- exact command or script path needed to resume or regenerate

## Agent Rule

Agents should pass pointers, packet IDs, hashes, and narrow excerpts. They should
not copy huge corpora into `~/Shared`, prompts, chat messages, or child-agent
context.

