# Papercut capture and repair lifecycle

Status: feature branch under review. Owner: General Skills `skills/papercuts/`. Canonical paths: `skills/papercuts/SKILL.md`, `references/capture.md`, `references/repair.md`. Supersedes: the single-body papercuts workflow in the same skill. Implementation commit: pending.

- **Intent:** Route creation and maintenance separately, deduplicate before adding, and check whether a reported issue still affects us before patching; close already-resolved entries without a patch.
- **Branch/base/target:** `docs/papercuts-lifecycle`, fetched `origin/beta` at `b01cc6f95d7d63dd634534bf4badbc72046b8d8f`, target `beta`.
- **Contract:** Main skill is a compact router; capture and repair references own their respective workflows. No CLI/storage change.
- **Evidence:** `python3 -m unittest discover -s tests -p 'test_skill_layout.py' -v` (5 passed); `python3 -m unittest discover -s skills/papercuts/tests -v` (5 passed); `git diff --check` clean. Independent review pending.
- **Activation boundary:** Feature branch does not activate the linked runtime skill. Merge into the selected beta source and verify the runtime projection before reporting it active.
- **Next action:** Verify references and tests, independently review, integrate to beta if clean, remove this temporary dossier from beta, and verify projected skill content.
