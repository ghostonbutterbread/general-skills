---
name: skill-seeds
description: "Propose new or changed skills as Shared markdown seeds for Ghost to review, promote, commit, and sync."
---

# Skill Seeds

Use this when an agent or human wants to create, modify, merge, or deprecate a
skill without directly editing a skill repository.

## Rule

Write a seed. Do not edit live skill repos, registries, provider runtime skill
folders, or sync destinations.

Ghost is the promotion point for turning seeds into committed skills. This keeps
skill creation fast during brainstorming while preserving one controlled path
for git, registry updates, provider sync, and cleanup.

## Seed Directory

Write one markdown file per proposal under:

```text
~/Shared/skill_seeds/
```

Filename:

```text
YYYY-MM-DD-<short-name>.md
```

## Seed Format

```markdown
---
name: proposed-skill-name
source: claude | codex | ryushe | ghost | other
created: YYYY-MM-DDTHH:MM:SSZ
status: new
project: unknown | general-skills | bounty-harness | ai-policies | openclaw | <repo/path>
type: new | update | merge | deprecate
---

# <proposed skill or change>

## Intent
What this should help an agent do, and when it should trigger.

## Proposed trigger
Skill name, slash command, phrase, or workflow signal.

## Target
Best guess for where this belongs. Use `unknown` if unsure.

## Body draft
Rough skill content, update notes, or replacement guidance.

## Why now
Why this belongs in durable skill memory instead of a one-off chat answer.

## Notes
Context, examples, links, caveats, or observed agent failures.
```

## Promotion Flow

Seed authors may draft freely. Ghost later reviews seeds and chooses:

- `promote`: create or update the real skill in the correct repo, validate,
  commit, push, and sync.
- `merge`: fold the seed into an existing skill.
- `reject`: mark rejected with a reason.
- `defer`: leave it for later review.

Keep the seed as an audit trail. Update frontmatter and notes after review
instead of deleting the file.

## Safety

Do not include secrets, credentials, cookies, tokens, private configs, or real
sensitive files in seeds. Use sanitized examples and artifact pointers only.

## Claude And Side-Agent Guidance

When asked to "make a skill", "update a skill", "save this as a skill", or
"turn this workflow into durable instructions", write a seed unless Ryushe
explicitly asks you to edit a specific repo.

The seed can be rough. Prefer capturing the idea quickly over guessing the
correct canonical repo, registry format, sync command, or provider runtime path.
