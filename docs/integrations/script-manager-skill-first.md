# Script Manager skill-first discovery

- Status: local implementation; awaiting parent independent review, not integrated.
- Owner/task: bugfix-profile delegated Script Manager documentation task.
- Branch: `docs/script-manager-skill-first`
- Worktree: `/home/ryushe/projects/.worktrees/general-skills-script-manager-skill-first`
- Base: `cfa32cf2c55dde89c67cad098b38b4c57e169eb7` (fetched `beta` / `origin/beta`).
- Intended target: `beta`, only after review; no push or stable promotion authorized.
- Canonical owner: `skills/script_manager/SKILL.md` and its owned references.

## Contract and scope

User requested skill-first discovery: load the relevant skill, read its linked
script index, reuse/edit helpers, and maintain minimal path + purpose entries.
Respect existing testing/scripts README or docs/references layouts instead of
assuming a root README. Update the same index and skill pointer when scripts
change. Canonical-source and existing coding/branch lifecycle remain in force.
Bounded discovery metadata is permitted within task authority, not as an
override of a lane that excludes skill edits.

Changed the owner, template, and local scripts README. Root README now routes to
the owner; the global catalog has only a supersession banner, preserving all
historical entries. No scripts, other repositories, profiles, or runtime
projections were changed. No registry, migration, or automation was added.

## Alignment and evidence

Checked `policy-authoring` and its editor guide, `policy-repository-lifecycle`,
`coding-policy`, `coding-agent-operations-policy`, `coding-spec-lifecycle-policy`,
and `branch-lifecycle`. Lifecycle stays with those owners. The latter's
restricted execution-host lane still excludes skills: explicitly retain its
authorization/handoff boundary rather than silently overriding it here.
Checked root README, retained catalog, owned template/README, and existing
`test_script_manager_policy.py`; redirected stale catalog doctrine without
removing history. Repository has no AGENTS.md, SCRIPT_POLICY.md, or dedicated
lint command/config tracked at this base.

Executed from this feature worktree with its source first on PYTHONPATH:

- `python3 -m unittest discover -s tests -p 'test_script_manager_policy.py' -v`:
  11 tests, OK; includes actual local-reference resolution and negative tests
  removing a pointer/reference in temporary copies.
- `python3 -m unittest discover -s tests -q`: 35 tests, OK (final rerun).
- YAML frontmatter parse: 22 skills OK.
- `git diff --check`: passed; Python edit syntax lint: passed.
- Dedicated repository lint unavailable; structural/documentation tests above
  are the available checks, not a claimed run of ai-policies' separate linter.
- Fetched origin again before handoff: base still matches origin/beta.

## Handoff and blockers

Kanban `hermes kanban --board general-skills list` exited 1:
`delegate_task child contexts cannot mutate Kanban tasks or boards`.
No card was created or modified; parent must list/create/claim and reconcile it.
No child delegation tool is available and this task forbids delegating children;
independent review and fresh-consumer smoke are deferred to the parent, before
any beta integration. Do not treat editor self-checks as independent review.
Review the skill + existing-layout rename/remove scenario and confirm discovery
metadata does not override lane authority. Then follow the existing integration
owner; remove this temporary dossier from the integration target on acceptance.

Recovery checkpoint / implementation commit:
`6e4e99e12c75159c79507209788d7d77973b1526` on
`docs/script-manager-skill-first`. The branch tip includes a later dossier-only
handoff commit recording this immutable checkpoint; verify that later range is
handoff-only. Next action: parent independent review and Kanban reconciliation,
then an explicit beta integration decision. No deployment or sync performed.
