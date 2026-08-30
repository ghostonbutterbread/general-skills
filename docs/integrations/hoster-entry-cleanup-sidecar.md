# Hoster-entry cleanup sidecar

- **Branch:** `feat/hoster-entry-cleanup-sidecar`
- **Base:** `e7097ca38cc7d2ef4854bde3161043654e0e27ed` (`beta`)
- **Target:** `beta`
- **Intent:** Make the Hoster entry contract match Ryu's requested autonomous sidecar workflow: the main agent starts its task while a bounded cleanup subagent independently reconciles existing safe residue and returns a compact status.

## Implemented contract

- `hoster-ssh` directs meaningful Hoster work to start the short-lived cleanup sidecar concurrently with the main task.
- `hoster-tmux-child-reaper` now owns the parent/sidecar contract, a bounded child packet, exact compact result vocabulary, and explicit separation from tmux pane terminology.
- The helper remains the narrow mechanical primitive: only previously registered, currently empty scopes may be stopped; all remaining or ambiguous state is report-only.
- Pane registration is described as a future launcher-owned creation concern, not a manual duty for the parent worker or the cleanup sidecar.

## Evidence

- `PYTHONPATH=/home/ryushe/worktrees/general-skills-hoster-entry-cleanup-sidecar python3 -m unittest discover -s tests -v` — 19 passed.
- `git diff --check` — passed.
- Independent review caught and corrected the sidecar-packet timing phrase so it explicitly runs while the parent begins work, never as a blocking prerequisite.
- Added focused documentation-contract coverage for concurrent sidecar/main-task separation, compact status vocabulary, no-timer behavior, and fail-closed boundaries.

## Activation boundary

The reviewed feature must be merged to `beta`, then synchronized through Aiskillsync to the Hoster runtime projection. A fresh agent must resolve the synced skill after sync.

## Next action

Run checks, obtain independent review, then merge and synchronize if approved. Remove this temporary dossier from `beta` during integration.
