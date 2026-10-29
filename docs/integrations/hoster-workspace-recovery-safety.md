# Hoster workspace recovery safety integration dossier

- **Status:** independently approved for beta integration
- **Owner:** General Skills task `t_ecb50ac1` (parent agent)
- **Branch / owning ref:** `docs/hoster-workspace-recovery-safety`
- **Worktree:** `/home/ryushe/worktrees/general-skills-hoster-workspace-safety`
- **Base commit:** `fab8e65096da3636cdcb296e0a58954c2641be7c` (`origin/beta` fetched 2026-10-29)
- **Intended integration target:** `beta`
- **Last updated:** 2026-10-29
- **Latest immutable recovery checkpoint:** `23fe37b16f53993fe7559f5f95ec8c9ce08a3ca2`
- **Feature implementation commit(s):** `23fe37b16f53993fe7559f5f95ec8c9ce08a3ca2`
- **Canonical owner / inspiration:** `skills/hoster-ssh/SKILL.md`, Workspace Attach and Recovery; parent-provided installed-wrapper failure report.

## Intent and implemented contract

Replace advice to run `--repair-empty` after a purported empty-session check with an explicit do-not-run warning: the reported installed wrapper can restart an active workspace after a failed/errored probe or with other sessions present, losing live panes. Preserve normal attach, its inactive-service start and fail-closed behavior. Require read-only topology and ownership inspection, escalation for ambiguity, and owner-coordinated recovery; no automatic restart or disruptive action without informed owner approval. This is guidance only: it does not change or verify the installed wrapper or service.

## Evidence and review

- Static frontmatter/name/description and skill-local Markdown link check passed; exact do-not-run warning and normal attach retained.
- `git diff --check` passed; source and diff inspected. Repository-wide `git grep` for `hoster-ssh|hoster-workspace|repair-empty` found no other recommendation to run the unsafe option. Neighbor review: `skills/hoster-ssh/references/systemd-cgroup-isolation.md`, `skills/hoster-ssh/scripts/README.md`, `skills/hoster-tmux-child-reaper/SKILL.md`, `skills/tmux/SKILL.md`, and `README.md`; no conflicting direct advice identified.
- No repository `AGENTS.md` was found in the checkout or ancestor directories. No policy-lint command was found in the repository; the static checks above are not a full policy lint.
- Independent review: **APPROVE** at feature tip `d4d9a9fb8b5fecba1be39bd7ff497a831eee533d` against fetched beta `fab8e65096da3636cdcb296e0a58954c2641be7c`. The reviewer inspected the full diff, dossier and neighboring guidance, confirmed normal attach and explicit prohibition of `--repair-empty`, and passed static frontmatter/local-link/reference-search and `git diff --check` checks. This was not a full policy lint or a wrapper test.
- The launcher defect is parent-provided context, not independently reproduced here. No real or mock launcher, wrapper, service, or Hoster commands were executed.

## Blockers and deferred work

- **Beta integration gate:** re-fetch and verify beta and both worktrees remain unchanged, then integrate the independently reviewed content; retire this dossier from the target and verify static checks and remote readback.
- **Missing evidence:** runtime repair and runtime validation of the underlying wrapper. **Environment:** separate owner-authorized wrapper repair effort and approved safe verification plan, not this documentation branch. **Trigger:** owner explicitly scopes and authorizes that work. **Gate:** no claim that the underlying defect is fixed or runtime guidance activated.
- An earlier proposed synthetic mock test in a different profile-local workspace-launcher documentation effort was blocked by approval timeout. Do not rerun, rephrase, or pursue that test outcome via any tool.

## Interruption / resume handoff

- **Owning feature branch/ref:** `docs/hoster-workspace-recovery-safety`
- **Latest immutable recovery checkpoint:** `23fe37b16f53993fe7559f5f95ec8c9ce08a3ca2` (implementation; review the subsequent dossier-only commit and current branch tip as well).
- **Feature implementation commit(s):** `23fe37b16f53993fe7559f5f95ec8c9ce08a3ca2`.
- **Exact resume point:** parent integrates only if beta and worktrees still match the reviewed state; no launcher test, service restart, or stable promotion.
- **Working-tree state at handoff:** intended clean after the dossier checkpoint commit.

## Decision gates

- **Integration:** independently approved; parent may integrate into named beta after rechecking current state, removing this dossier from the target in the integration operation.
- **Activation / promotion:** not authorized; no sync, deployment, service modification, or stable promotion.
- **Decision record:** 2026-10-29 — independent reviewer approved `d4d9a9f` for beta; runtime wrapper repair remains separate and unresolved.
