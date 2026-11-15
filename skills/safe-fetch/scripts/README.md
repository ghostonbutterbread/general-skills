# Safe-fetch scripts

- `safe_fetch.py` — quarantine and sanitize external content.
- `research_worker_preflight.py` — **experimental diagnostic only**, not a
  research agent. Run `python3 research_worker_preflight.py --timeout 20` to
  probe a fixed locally available `python:3.12-slim` Docker image. No network,
  host mounts, caller commands, live credentials, or image pulls are requested.
  It tests non-root UID, read-only root mount, a host-file canary, an environment
  canary, and the network namespace, then removes only its generated container.
  It exits nonzero on missing/failed checks or uncertain cleanup. Cleanup's
  `absent_at_check` is a point-in-time observation, not proof against a delayed
  daemon operation after a timeout; recheck that exact name if Docker stalls.

A pass is only evidence for those observed checks; it is not a security audit,
model-authentication test, or proof that a research-agent path exists. The
probe does not test full-source ingestion, model calls, prompt injection,
knowledge promotion, reuse, or exfiltration resistance of an actual agent.
It does not authorize launching one. See the branch-local integration dossier for
blocked work and deferred end-to-end gates.
