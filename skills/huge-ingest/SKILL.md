---
name: huge-ingest
description: "Ingest large URL, code, page, proxy, or artifact datasets without context drift."
---

# Huge Ingest

Use this when a task involves more data than one agent should read directly:
large URL lists, JavaScript/source bundles, scraped pages, screenshots, proxy
flows, API inventories, binary/source exports, or mixed recon artifacts.

Huge Ingest is the parent ingestion protocol. It does not replace `/js`,
`/url-ingest`, `/live-map`, `/hunter-loop`, `/analyze-endpoint`, or vuln-lane
skills. It creates the manifest, storage layout, bounded packets, and review
lanes those skills consume.

## Load Order

1. Read `references/bounty-storage-lanes.md` for bug bounty storage routing.
2. Identify input type: URLs, JS/source, pages, proxy flows, screenshots,
   reports, binaries, or mixed.
3. Create or locate a run manifest before deep reading.
4. Store heavy raw/corpus data outside cloud-backed `~/Shared` unless the data
   is small and canonical.
5. Build small indexes and bounded packets.
6. Map broadly first, then dispatch vulnerability or resolution lanes only when
   evidence justifies it.

## Core Rule

Never paste or load the whole dataset into agent context.

The parent agent owns:

- scope and safety boundaries
- manifest and storage routing
- dedupe, hashing, and resumability
- packet selection and prioritization
- lane dispatch and result merge
- canonical summaries, ledgers, and proof standards

Specialists receive only one packet, one objective, and one stop condition.

## Pipeline

1. **Intake**
   - Normalize input paths/URLs and record source provenance.
   - Validate scope before live probing or mutation.
   - Hash large files and content-address reusable blobs.
   - Keep blocked, failed, or auth-required items queued instead of stopping the
     entire run.

2. **Manifest**
   - Write a run manifest with run ID, program, input source, storage roots,
     counts, caps, and status.
   - Include pointers to raw artifacts, indexes, packets, and exported
     summaries.
   - Record redownload recipes when raw data is disposable.

3. **Cheap Map**
   - Extract routes, hosts, params, request builders, GraphQL ops, identifiers,
     forms, DOM sinks, storage keys, error/status patterns, and provenance.
   - Prefer deterministic parsers and SQLite/JSONL indexes over long prompt
     context.
   - Produce map packets with exact artifact pointers and byte/chunk evidence.

4. **Triage Lanes**
   - Group evidence by lane: request-shape, access-control/IDOR, DOM-XSS,
     stored/reflected XSS, SSRF/import, auth/ATO, payment, secrets, business
     logic, fuzzing, or framework-specific lanes.
   - For broad reviews, split by lane. Do not ask one worker to deeply inspect
     every vulnerability class across every packet.
   - Each lane returns: lead, evidence, confidence, missing proof, exact next
     action, and whether a resolution lane is justified.

5. **Resolution Lanes**
   - Only resolution agents test or verify a lead after triage identifies a
     concrete hypothesis.
   - Resolution checks controllability, request shape, auth/resource boundary,
     mutability, effect, replayability, and cleanup needs.
   - Promote only verified or clearly test-ready items into findings/handoffs.

6. **Merge**
   - Merge results into canonical ledgers, lead summaries, tested-state logs,
     and storage manifests.
   - Keep uncertainty explicit: confirmed, test-ready, mapping lead, blocked,
     duplicate, dead, out-of-scope, or needs-auth.

## Packet Shape

Use compact JSON or Markdown packets with:

- `packet_id`, `run_id`, `program`, `lane`, `objective`
- full URL or artifact pointer
- content hash, chunk ID, byte range, or line range when available
- related request/proxy/page provenance
- extracted params, IDs, sinks, sources, or request shape
- prior attempts and known blockers
- account/resource boundary and safe-test status
- stop condition and proof standard

Do not include raw cookies, bearer tokens, passwords, reset links, private
headers, API keys, broad proxy dumps, or unrelated app history.

## Bug Bounty Defaults

Preferred canonical outputs in `~/Shared`:

- scope, policies, program notes
- run manifests and small indexes
- lead summaries and handoffs
- tested/not-tested ledgers
- findings, proof packets, and reports
- auth-required / blocked queues

Preferred heavy outputs in mounted bounty artifact storage:

- raw JavaScript/source corpora
- scraped HTML/page bodies
- screenshots and videos at scale
- proxy flow dumps
- browser profiles and CDP traces
- large chunk stores and repeated parser output

If `/mnt/bounty` or another bounty artifact mount is unavailable, use the
current run host's artifact directory and export a manifest into `~/Shared` that
explains where the heavy data lives and how to regenerate it.

## Related Skills

- `/coordination` for parent/child run tracking
- `/tmux` for long-running or attachable ingestion jobs
- `/script_manager` when a repeatable extractor/parser should become reusable
- `/js` for JavaScript-specific inventory and deep review
- `/url-ingest` for URL queueing, dedupe, and tested-state tracking
- `/live-map` and `/hunter-loop` for app mapping and specialist dispatch
- `/analyze-endpoint` for request contracts after a lead has request evidence

