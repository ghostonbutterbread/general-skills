---
name: security-reporting
description: "Use when drafting, revising, reviewing, or packaging a security vulnerability report and its triager-facing proof of concept."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [security, reporting, proof-of-concept, triage, disclosure]
    related_skills: [poc-tooling-policy, sync-reports, live-testing-policy]
---

# Security Reporting

## Overview

Write reports for a triager who needs to understand and validate the demonstrated security boundary break quickly. The final report is not a research diary: it explains what the vulnerability is, why it exists, what the attacker can do, how to reproduce it, and the smallest durable remediation.

Keep claims evidence-bound. Preserve exhaustive source analysis, proxy traces, and exploration notes in the evidence packet, not in the report body.

For the triager-first writing contract—including concise Impact framing, multi-organisation consequences, and conditional OAuth pivots—see [references/triager-first-report-style.md](references/triager-first-report-style.md).

## Two-Artifact Report Pipeline

For each reportable finding, keep two linked documents:

1. **Evidence Report** — the complete internal source of truth: validated evidence, reproduction variants, source references, expected/actual behavior, tested controls, negatives, PoC pointers, and open questions. Optimize for traceability, not length.
2. **Submission Report** — the concise triager-facing derivative. It may only compress or clarify the Evidence Report; it must not introduce claims from memory, omit material prerequisites, or weaken documented negatives.

When converting a finding card into a Submission Report, extract the affected location, ordinary-language vulnerability and immediate cause, demonstrated attacker outcome, company/user consequence, prerequisites, and material negatives before drafting. Write the Summary in this order: **location → vulnerability/cause → attacker capability → company/user effect**. Keep implementation detail only when it establishes root cause.

Use a separate judge pass against the Evidence Report, PoC, and program overlay before treating the Submission Report as final.

## Revision and comparison discipline

When the user identifies an existing report to revise, first identify the canonical submission artifact and edit that file **in place**. Do not create parallel `*_DRAFT`, `*_FRAMED`, or versioned report variants merely to preserve an earlier copy; the Evidence Report already preserves the detailed record. If a separate draft is genuinely requested, name it explicitly and state which file is canonical.

When the user asks to compare report quality or framing against outside examples, research public online report guidance and publicly available high-quality reports first. Do not substitute the user’s private prior reports as the primary comparison source; use them only when requested or as explicitly labeled secondary context.

### Actor language

Use the user’s requested attacker/victim framing in report prose. Add a role only where it clarifies the attack story (for example, “victim reviewer” or “targeted victim”); retain an exact product role name only when it is material evidence.

## When to Use

- Drafting, rewriting, reviewing, or submitting a confirmed security finding.
- Converting technical validation into a report-ready summary and reproduction path.
- Packaging a proof of concept for a bug-bounty triager.
- Applying program-specific report standards, quality rubrics, length caps, or code-reference expectations.

Do not use this skill to decide whether an unproven finding is reportable. Use the applicable validation, exploitability, and live-testing skills first.

## Markdown Layout Portability

Emit each prose paragraph as **one unbroken source line**. Do not insert literal newlines within a paragraph: copied text preserves them, and some bug-card editors treat them as fixed line breaks rather than reflowable text. Let the receiving editor create its own visual soft wrap. Use exactly one blank line only when starting a genuine new paragraph, section, list, quote, or code block. Never use two trailing spaces or `<br>` for manual vertical spacing.

## Core Report Format

Use this order unless the program’s form requires another structure:

```markdown
# <attacker capability> allows <security-relevant outcome>

## Summary
<one or two compact paragraphs: boundary break, cause, demonstrated result>

## How to reproduce
1. ...
2. ...
3. ...

## Impact
<short company-focused framing>
- <demonstrated consequence>
- <demonstrated consequence>
- <material prerequisite or limit>

## Remediation
<smallest fix that removes the broken boundary>
```

Do not add a separate “Vulnerability details” section when Summary already does that work. Omit methodology, generic CVSS narrative, research chronology, and large code dumps unless the program specifically asks for them.

## Summary: Cause and Outcome

State the causal chain plainly:

**attacker-controlled input → missing or incorrect control → observed security outcome**.

Lead with the boundary break and demonstrated result, then state the root cause. Example:

> An error-triggered model fallback receives attacker-controlled content without the primary path’s execution restrictions. I triggered the fallback and caused the server to execute the supplied command. The issue exists because the fallback remains reachable after model errors without equivalent validation.

Do not claim untested scale, escalation, affected versions, account compromise, data access, or chains as established facts.

### Summary narrative: lead with meaning, not mechanics

Use one or two compact paragraphs that let a triager understand the issue before reading reproduction:

1. **Vulnerability:** location → attacker-controlled input → missing control → observed boundary break.
2. **Capability story:** where the payload/action runs → whose access it inherits → what concrete settings, data, or resources it changes or obtains → who is affected and why.

Name two to four important demonstrated attacker capabilities in plain language. Do not lead with low-level mechanics such as Server Actions, endpoint IDs, or framework terminology unless they are essential to understanding the harm; put those details in reproduction or Impact.

Do not describe an owned-test environment or researcher setup in the Summary. State the required attacker role and the demonstrated result; keep ownership and cleanup in the evidence record or Cleanup.

## Reproduction: Portable, Direct Steps

Write walkthroughs as neutral, imperative steps for the triager’s environment—not as a first-person research diary:

- Use concise action labels: “Open the project,” “Save the controlled payload,” “Verify persistence,” and “Run the attached JavaScript PoC.”
- State prerequisites once before the numbered steps: required role, controlled resource, browser origin, feature state, or dependency.
- Use portable placeholders such as `<target-url>`, `<account>`, and `<resource-id>`; do not require researcher-local configuration.
- Add a short note only where a step is not self-explanatory, and explain what that step proves rather than how it was discovered.
- State expected secure behavior and actual behavior where their contrast clarifies the flaw.
- Link or attach the standalone PoC; do not require a local path, private browser profile, or hidden proxy capture.

Use first person only in a brief evidence-attribution sentence when it materially clarifies a measured result. Never begin every PoC step with “I,” and never use first-person narration in a console or terminal PoC. Each step must be executable without the triager inferring an omitted parameter or state transition.

## Impact: Production Consequences

Write Impact as the concise answer to: **“If this occurs in production, what can the attacker do next, and what does that mean for the company or affected user?”** It is not a test log.

Use short, labeled bullets. Each bullet follows one chain:

```text
proven capability → attacker next action → operational consequence → company/user harm
```

For example, write: “**Cross-organisation access:** An attacker can add themselves to another organisation, gaining the resulting role’s permitted settings and data access.” Do not write: “Testing created an invitation.” Avoid generic bullets such as “runs as the user” when the concrete consequence bullets explain the downstream harm.

Use conditional language for a real but user-mediated pivot: “If a targeted player follows the legitimate sign-in link and completes login, the attacker receives the authorization code…” Do not turn a demonstrated capability into an unconditional or silent takeover claim.

For multi-tenant products, separate what was proven from what is conditional: organisation membership or role access may be proven; PII, marketing, customer, or unreleased-product data should be described as potentially reachable according to that role unless content access was separately confirmed. Keep exhaustive negatives in the Evidence Report; include a condition in Impact only when omitting it would misstate the claimed harm.

## Remediation

Recommend the smallest durable change that removes the root cause; add defense in depth only when it is relevant. Avoid speculative redesigns.

For example: remove an unnecessary fallback; if it must remain, apply the same validation and execution restrictions before it receives user-controlled content, and fail closed when the primary path errors.

## Triager-First PoC Packaging

A report PoC is a review tool, not a research harness. It should prove the exact report claim in one clear run. Use neutral step names, short notes, status labels, and evidence panels rather than first-person narration; explain a step only when the action is not inherently obvious, and explain what it proves.

### Choose the artifact

- **Small browser-context proof:** prefer one self-contained JavaScript snippet that a triager pastes into DevTools while logged in. It must use no external dependencies or embedded session values, request only controlled identifiers, print clear baseline/action/verification evidence, and ask for explicit confirmation before a state-changing request. Pair it with only the prerequisites and concise numbered steps explaining what each phase proves.
- **Browser proof needing visible setup, comparison, or cleanup:** use one self-contained HTML page with embedded JavaScript. Use this when origin, CORS, session behavior, cross-account state, a visible evidence panel, or restoration controls make a console snippet insufficient.
- **Extensive, multi-step, or non-browser behavior:** use one self-contained Python 3 script with an interactive TUI by default. Support familiar aliases for repeatability, e.g. `-u`/`--url`, `-c`/`--cookie`, and `-i`/`--id`; do not require flags for ordinary first use. Include an explicit proxy toggle.
- **Password-protected hosted delivery:** a program-approved `curl -fsSL -u <download-user> <protected-poc-url> | python3` path is acceptable when paired with a direct-download option and SHA-256 for inspection of the exact pinned artifact.

Choose the smallest artifact that makes the demonstrated boundary obvious. Every instruction, prompt, code line, and output panel must establish a prerequisite, control, action, verification, limitation, or cleanup; remove everything else.

For terminal PoCs, use the established evidence-first visual contract: a clear finding banner, visible `WHAT THIS POC VALIDATES` and `WHAT THIS POC DOES NOT TEST` blocks, compact colored step panels, sanitized evidence, and a final verdict (`VULNERABLE`, `NOT REPRODUCED`, `BLOCKED`, or `INCONCLUSIVE`). Before live authorization exists, provide a non-running `--preview`/design-walkthrough mode that makes no network request, accepts no credentials, and exposes the exact wording and flow for approval.

### Required PoC behavior

At the first screen or document header, state:

- what it validates;
- prerequisites and controlled-resource/ownership assumptions;
- required inputs;
- expected secure and vulnerable results;
- material negatives and intentionally untested actions;
- default limits, stop conditions, secret handling, and cleanup.

Its final output must provide a clear verdict (`VULNERABLE`, `NOT REPRODUCED`, `BLOCKED`, or `INCONCLUSIVE`) plus sanitized baseline/action/verification evidence. For state changes, use a controlled canary and verify it afterward where possible.

Never embed secrets, print raw session material, depend on researcher-local paths, or conceal dependencies. Make writes deliberate and cleanup opt-in for controlled state only.

## Program Overlays

Keep a compact overlay for programs with distinctive requirements: required fields, title conventions, length caps, accepted PoC artifact types, code-reference preferences, attachments, and prohibited claims. Use the core format when an overlay does not exist; do not invent a program rule.

Some programs reward source-code references or high-quality evidence differently. Tune the report to those requirements without changing evidence standards or padding the report.

## Writer–Judge Loop

Use an independent second pass after drafting. Give the judge the draft, sanitized evidence, the attached PoC, and the program overlay. Revise until it passes or explicitly label an unresolved gap.

The judge must verify:

- required sections, order, and program requirements;
- a compact Summary that states cause and outcome;
- portable, direct-step reproduction with no local paths or secrets;
- evidence support for every impact claim, prerequisite, and negative;
- concise language without duplicate sections, research diary, or generic filler;
- remediation that addresses the root cause;
- a one-run, portable PoC that proves the exact claim and exposes no secrets.

## Common Pitfalls

1. **Overexplaining source analysis.** Keep only the function, route, or component evidence necessary to establish root cause; move the rest to evidence.
2. **Making the triager assume local state.** Replace machine paths, raw IDs, private sessions, and investigator-specific setup with portable placeholders and declared prerequisites.
3. **Treating a plausible consequence as proven.** State only what the PoC demonstrated; name prerequisites and untested escalation as limits.
4. **Shipping a research harness as a PoC.** Reduce multiple scripts, modes, and hidden dependencies to one guided artifact and one clear verdict.
5. **Skipping the independent judge.** A second rubric pass is the practical control for excess length, missing prerequisites, and program-format drift.

## Completion Checklist

- [ ] The report uses Summary → How to reproduce → Impact → Remediation, unless a program form differs.
- [ ] Summary states the broken boundary, cause, and observed result in one or two compact paragraphs.
- [ ] Reproduction is portable, direct-step, and requires no local researcher path or hidden setup.
- [ ] Impact uses concise production-consequence bullets; conditions are included only when they materially qualify the claimed harm, while exhaustive negatives remain in the Evidence Report.
- [ ] The PoC is one runnable artifact with guided inputs, a clear result, sanitized evidence, and controlled cleanup.
- [ ] No secret, token, cookie, private body, or local-only evidence is included.
- [ ] A program overlay was applied when available.
- [ ] An independent judge pass approved the final package or recorded its precise blocker.
