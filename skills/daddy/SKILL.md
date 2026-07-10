---
name: daddy
description: "Route CLI subtasks one model up or down from the current agent."
---

# Daddy

Use this skill when a CLI agent needs to temporarily delegate a bounded subtask
to a cheaper or stronger model relative to the model it is currently running.

The core rule is simple: anchor on the current model, then move relative to it.
Do not hardcode a default base model inside this skill.

## Aim

Let agents reduce cost for mechanical work and raise reasoning strength for hard
work by asking the launcher/runtime for a model one step down, one step up, or
at the strongest available tier relative to the current model.

This skill decides movement direction and packet shape. The launcher/runtime
resolves model names and records telemetry.

## Runtime Model Anchor

First determine the current model from the CLI/session/runtime if available:

```yaml
current_model: <runtime model id>
```

Resolve movement from the ladder containing that model:

```yaml
model_ladders:
  chatgpt: [luna, tera, sol]
  claude: [claude-fast, claude-balanced, claude-strong]
```

Example:

```yaml
current_model: claude-balanced
ladder: [claude-fast, claude-balanced, claude-strong]
down: claude-fast
base: claude-balanced
up: claude-strong
```

If the current model is not visible, ask the parent agent or launcher for
relative lane metadata instead of guessing:

```yaml
current_model: unknown
available_relative_lanes:
  down: <model or command if provided>
  base: <current/default lane if provided>
  up: <model or command if provided>
  max: <strongest lane if provided>
```

The skill does not require a `provider`, `base_model`, or `model_reasoning`
config. Those are runtime or launcher concerns.

## Relative Movement

Supported movements:

- `2down` - two steps below the current model, clamped to the lowest available model.
- `down` or `1down` - one step below the current model.
- `base` - stay on the current model.
- `up` or `1up` - one step above the current model.
- `2up` - two steps above the current model, clamped to the strongest available model.
- `max` - strongest available model in the resolved ladder.

`daddy` means `up` by default: spawn or ask the model one tier above the current
agent for a bounded assist.

Clamp movement at ladder boundaries. If the current model is already strongest
and the agent asks for `up`, use the current model and note that no higher model
was available.

## Default Use

Goal-mode CLI agents should load this skill by default when the run may contain
mixed-complexity work.

Non-goal agents may load it for long, expensive, uncertain, or mixed work.

Do not spend routing effort on short single-step tasks unless the user or parent
agent asks.

## Route Selection

Choose `down` or `2down` for cheap, verifiable, or high-volume work:

- recon sorting and first-pass classification
- URL, status, duplicate, or scan-result cleanup
- log summarization
- extracting endpoints, parameters, filenames, stack traces, or simple facts
- formatting and mechanical edits
- applying clearly specified changes

Choose `base` for normal agent work:

- ordinary orchestration
- routine coding and debugging
- standard analysis
- bug bounty workflow coordination
- deciding the next step when risk is low

Choose `up` for high-intelligence or high-risk judgment:

- exploit development reasoning
- exploit-chain design or validation
- ambiguous auth, IDOR, SSRF, XSS, SQLi, or business-logic triage
- reportability and severity decisions
- confusing bugs after repeated attempts
- architectural decisions with meaningful downstream cost
- final review of security-sensitive changes

Choose `2up` or `max` only for exceptional cases:

- repeated failure after `up`
- high-value exploit-chain review
- decisions involving security, privacy, data loss, production impact, or expensive false positives
- final confidence review before reporting a critical finding

## Budget Guard

`daddy` is not automatically cheaper. It saves money when down-lane volume
dominates and up-lane calls stay bounded.

Use these default budget expectations until live telemetry proves better values:

- Recon-heavy goals: `down` may be 60-85% of delegated subtasks; `up` should usually stay under 5-10%.
- Balanced goals: `down` may be 40-65%; `up` should usually stay under 10-15%.
- Security-review-heavy goals: expect higher cost if `up` becomes common; use `up` for short risk calls, not whole-run ownership.

If a run needs `up` for most subtasks, stop treating it as a cost-saving route.
The right answer may be to run the whole goal on a stronger model or narrow the
task.

## Delegation Pattern

Do not assume the whole CLI context follows when changing models.

Preferred pattern:

1. Parent agent keeps the main task context.
2. Parent chooses a movement, such as `down`, `up`, or `max`.
3. Parent asks the launcher/runtime to resolve the relative model from the current model.
4. Parent sends a compact packet to a child agent or model call.
5. Child returns bounded output.
6. Parent integrates the answer and continues on the original lane.

If the CLI supports true in-session model switching, summarize the active
context before switching and record why the switch happened. If the CLI does
not support switching, spawn a child CLI/model call with a bounded packet.

## Escalation Packet

Use this for `up`, `2up`, or `max`:

```markdown
# Daddy escalation packet

## Goal
<current goal>

## Route
current_model: <runtime model id or unknown>
requested_movement: up|2up|max
resolved_model: <if known>

## Why escalation is justified
<1-3 bullets>

## Relevant context
<focused excerpts, file paths, outputs, request/response facts, or constraints>

## Already tried
<brief attempts and outcomes>

## Exact question
<one bounded question>

## Desired output
<diagnosis | risk call | next 3 steps | options with tradeoffs | review verdict>
```

Ask the stronger model for a bounded answer, not ownership of the entire task
unless Ryushe explicitly requested a handoff.

## De-escalation Packet

Use this for `down` or `2down`:

```markdown
# Daddy de-escalation packet

## Goal
<mechanical subtask>

## Route
current_model: <runtime model id or unknown>
requested_movement: down|2down
resolved_model: <if known>

## Inputs
<files, commands, logs, or artifacts>

## Output format
<strict expected output>

## Stop conditions
<when to stop and return to parent/base>
```

Keep down-lane work mechanical, bounded, and easy to verify.

## Benchmarking Against Normal Mode

Test `/daddy` against a normal run with two tracks:

- `baseline_normal` - the current model handles every subtask directly.
- `daddy_routed` - the parent keeps the main task, sends mechanical subtasks down, and sends hard judgment subtasks up.

A dry benchmark can validate routing shape and cost proxy. It cannot prove real
model quality or real savings.

A live benchmark requires launcher telemetry:

```yaml
benchmark_event:
  run_id: <id>
  mode: baseline_normal|daddy_routed
  parent_model: <current model>
  requested_movement: base|down|up|max
  selected_model: <resolved model>
  task_type: recon_sort|mechanical_extract|normal_coding|exploit_reasoning|reportability_review
  input_tokens: <number>
  output_tokens: <number>
  latency_ms: <number>
  success: true|false
  reviewer_score: 1-5
  rework_needed: true|false
```

Score with these metrics:

- cost proxy or actual token cost
- wall-clock latency
- success rate
- reviewer quality score
- rework rate
- number of escalations that changed the final decision
- context-packet size versus full-context size

Pass condition for the first real benchmark:

- mechanical tasks cost less than baseline without quality regression
- hard judgment tasks are equal or better than baseline by reviewer score
- no critical task loses needed context because packeting was too thin
- routing overhead does not erase savings

Dry benchmark matrix from proposal testing:

```text
up_heavy_security_review: baseline=100.00 routed=133.90 savings=-33.9%
balanced_goal_run:       baseline=100.00 routed=86.60  savings=13.4%
recon_heavy_goal_run:    baseline=100.00 routed=64.80  savings=35.2%
all_mechanical:          baseline=100.00 routed=48.70  savings=51.3%
```

Interpretation: `daddy` should be excellent for long recon, ingestion, and
mechanical goal runs, modestly useful for balanced goals, and intentionally
expensive when it buys stronger reasoning for hard security-review work.

## Decision Record

When routing matters, record a short note in the run log, handoff, or final
summary:

```yaml
model_route_decision:
  current_model: <runtime model id or unknown>
  requested_movement: 2down|down|base|up|2up|max
  selected_model: <resolved model id if known>
  reason: <short reason>
  returned_to_parent: true
```

## Guardrails

- Do not hardcode a default base model inside this skill.
- Do not require provider config unless the launcher cannot resolve ambiguity.
- Do not guess model ladders from vibes; use runtime/launcher metadata.
- Do not escalate because a task is boring.
- Do not dump entire repos, logs, transcripts, proxy histories, secrets, cookies, tokens, or private state into another model.
- Do not let the child model silently change the original goal.
- Return control to the original agent after the bounded question is answered.
- If no current model or relative lane metadata is available, continue on the current model and note that relative routing was unavailable.
- Treat dry benchmark wins as hypotheses until confirmed with live telemetry.

## Quick Tests

Given current model `tera` and ladder `[luna, tera, sol]`:

- Deduplicate 10,000 URLs -> `down` -> `luna`.
- Implement a normal parser change -> `base` -> `tera`.
- Decide whether an auth bypass is reportable -> `up` -> `sol`.
- Ask for `2up` -> `sol`, clamped to strongest available.

Given current model `claude-balanced` and ladder `[claude-fast, claude-balanced,
claude-strong]`:

- Summarize noisy recon logs -> `down` -> `claude-fast`.
- Review exploit-chain logic -> `up` -> `claude-strong`.

Given current model `sol` and ladder `[luna, tera, sol]`:

- Ask for `up` -> stay on `sol` and record that no higher model exists.
