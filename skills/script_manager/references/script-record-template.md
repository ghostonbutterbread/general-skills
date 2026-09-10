# Script Record Template

Use this in the nearest `scripts/README.md` or central script index.

```md
### `<relative/path/to/script>`

- Purpose:
- Scope: general | skill-local | project-local | target-local | host-local
- Inputs:
- Outputs:
- Coverage boundary: exhaustive: false | closed-contract proof
- Mutates: no | files only | network | external system
- Safe default:
- Example:
- Verification:
- Related skill:
- Related index/store:
- Owner:
- Last verified:
- Notes:
```

## Rules

- Keep examples sanitized. Do not include cookies, bearer tokens, API keys,
  passwords, private headers, reset links, or real sensitive file paths.
- If the script can touch a live service, record the rate limit and stop
  condition.
- If the script consumes untrusted content, record whether it treats source text
  as data only.
- If the script emits heuristic or vocabulary-driven output, record its coverage
  boundary. Use `exhaustive: false` unless a closed input contract proves
  otherwise.
- If the script writes into a shared aggregate file, record whether it appends,
  rewrites, dedupes, or stages through a temporary file first.
