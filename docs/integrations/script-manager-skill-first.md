# Script Manager skill-first discovery

- Status: independently approved for beta integration; parent integration authorized.
- Acceptance: reviewer verified candidate f821431, all six local links, both missing-link negative cases, and 35 passing isolated tests. Parent also ran 35 passing tests.
- Release scope: integrate and publish beta; verify existing local runtime projections and fresh read-only discovery. No main promotion or Hoster deployment. Remove this temporary dossier during integration.
- Deferred: older branch-lifecycle metadata-edit wording remains a separate alignment issue; this release does not authorize broader policy edits.
- Owner/task: bugfix-profile delegated Script Manager documentation task.
- Branch: `docs/script-manager-skill-first`
- Worktree: `/home/ryushe/projects/.worktrees/general-skills-script-manager-skill-first`
- Base: `cfa32cf2c55dde89c67cad098b38b4c57e169eb7` (`beta`).
- Target: `beta`; parent review complete and beta publication/local activation authorized. No stable promotion or Hoster deployment.
- Original implementation: `6e4e99e12c75159c79507209788d7d77973b1526`.
- Prior handoff checkpoint: `0d32cc762759ed6970298a271013d4a459618bc1`.

## Contract and scope

Load the relevant skill, follow its script-map pointer, reuse/edit helpers, and
maintain minimal path + purpose entries in the existing testing/scripts README
or docs/references layout. The root README routes to Script Manager; the global
catalog retains its historical entries with a supersession banner.

The user clarified the scripts-only exception: adding a script-map pointer in
main `SKILL.md` is allowed, with no unrelated body edits. Associated map/index
entries may be freely maintained in the existing layout. Creating a script MUST
update that map. The owner and its existing test now reflect this, removing the
previous lane-owner approval blocker for this metadata-only exception.

No scripts, permissions machinery, or implementation-subagent requirement added.
Normal branch/test/review/release guidance and the fresh release reviewer remain.

## Alignment and evidence

Compared Script Manager, its owned template/README, historical catalog/root
README, canonical coding-agent-operations-policy and proposal routing, BBH's
SCRIPT_POLICY.md/AGENTS.md, policy-authoring, and installed branch-lifecycle.
The parallel canonical documentation edits align the metadata-only exception.
BBH AGENTS.md still needs its protected-file approval; the active branch-lifecycle
copy needs a parent-owned skill update if no canonical source is found. Neither
blocker is silently overridden or represented as released.

Repository has no tracked AGENTS.md, SCRIPT_POLICY.md, or dedicated lint command.
Executed from this feature worktree with `PYTHONPATH="$PWD"`:

- `python3 -m unittest discover -s tests -q`: 35 tests, OK.
- Existing tests resolve owned references and reject missing pointers/references.
- Updated boundary assertions cover pointer-addition only, no unrelated body
  edits, freely maintained associated entries, mandatory creation map update,
  and removal of the obsolete metadata authorization handoff.
- `git diff --check`: passed.

## Handoff

Parent owns Kanban and independent review; no child delegation performed. Review
the full branch range, then decide integration and remove this temporary dossier
from the integration target on acceptance. No push, merge, sync, or deployment.
Recovery implementation checkpoint: `209eaea6b1360e9bc90693e9258bcddf06154d1f`
on `docs/script-manager-skill-first`. It contains the clarified owner, test, and
dossier; the subsequent dossier-only commit records this immutable checkpoint.
Verify that handoff-only range separately.
