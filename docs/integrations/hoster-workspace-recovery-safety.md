# Hoster workspace recovery safety integration dossier

- **Status:** feature; independent review pending
- **Owner:** General Skills task `t_ecb50ac1` (parent agent)
- **Branch / owning ref:** `docs/hoster-workspace-recovery-safety`
- **Worktree:** `/home/ryushe/worktrees/general-skills-hoster-workspace-safety`
- **Base commit:** `fab8e65096da3636cdcb296e0a58954c2641be7c` (`origin/beta` fetched 2026-10-29)
- **Intended integration target:** `beta`
- **Last updated:** 2026-10-29
- **Latest immutable recovery checkpoint:** none yet; will record after implementation commit
- **Feature implementation commit(s):** none yet
- **Canonical owner / inspiration:** `skills/hoster-ssh/SKILL.md`, Workspace Attach and Recovery; parent-provided installed-wrapper failure report.

## Intent and implemented contract

Replace advice to run `--repair-empty` after a purported empty-session check with an explicit do-not-run warning: the reported installed wrapper can restart an active workspace after a failed/errored probe or with other sessions present, losing live panes. Preserve normal attach, its inactive-service start and fail-closed behavior. Require read-only topology and ownership inspection, escalation for ambiguity, and owner-coordinated recovery; no automatic restart or disruptive action without informed owner approval. This is guidance only: it does not change or verify the installed wrapper or service.

## Evidence and review

- Static frontmatter/name/description and skill-local Markdown link check passed; exact do-not-run warning and normal attach retained.
- `git diff --check` passed; source and diff inspected. Repository-wide `git grep` for `hoster-ssh|hoster-workspace|repair-empty` found no other recommendation to run the unsafe option. Neighbor review: `skills/hoster-ssh/references/systemd-cgroup-isolation.md`, `skills/hoster-ssh/scripts/README.md`, `skills/hoster-tmux-child-reaper/SKILL.md`, `skills/tmux/SKILL.md`, and `README.md`; no conflicting direct advice identified.
- No repository `AGENTS.md` was found in the checkout or ancestor directories. No policy-lint command was found in the repository; the static checks above are not a full policy lint.
- Independent review: **pending**. A fresh reviewer must inspect the exact feature tip and dossier, compare against freshly fetched `origin/beta`, review the full diff and the referenced owner/neighbor guidance, and independently rerun static frontmatter/link, unsafe-reference search and `git diff --check`. Review must establish that normal attach remains intact and no advice authorizes `--repair-empty` or automatic restarts. No integration authority is granted by this task.
- The launcher defect is parent-provided context, not independently reproduced here. No real or mock launcher, wrapper, service, or Hoster commands were executed.

## Blockers and deferred work

- **Missing evidence:** independent review and fresh-base comparison. **Environment/command:** clean read-only review of this branch and `origin/beta` with static checks only. **Trigger:** parent appoints a fresh reviewer. **Gate:** required before any future integration; reviewer reports findings to parent.
- **Missing evidence:** runtime repair and runtime validation of the underlying wrapper. **Environment:** separate owner-authorized wrapper repair effort and approved safe verification plan, not this documentation branch. **Trigger:** owner explicitly scopes and authorizes that work. **Gate:** no claim that the underlying defect is fixed or runtime guidance activated.
- An earlier proposed synthetic mock test in a different profile-local workspace-launcher documentation effort was blocked by approval timeout. Do not rerun, rephrase, or pursue that test outcome via any tool.

## Interruption / resume handoff

- **Owning feature branch/ref:** `docs/hoster-workspace-recovery-safety`
- **Latest immutable recovery checkpoint:** none yet; will record after implementation commit.
- **Feature implementation commit(s):** none yet.
- **Exact resume point:** review the committed tip, perform the independent review above, then hand the result to the parent. Do not integrate, push, activate, sync skills, change Hoster, or close task records under this authorization.
- **Working-tree state at handoff:** intended clean after the dossier checkpoint commit.

## Decision gates

- **Integration:** pending independent review and separate parent authorization; remove this dossier from the target in the integration operation if subsequently accepted.
- **Activation / promotion:** not authorized; no sync, deployment, service modification, or stable promotion.
- **Decision record:** 2026-10-29 — isolated documentation feature prepared; review pending.
