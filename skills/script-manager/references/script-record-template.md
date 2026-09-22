# Script Record Template

Use a minimal entry in the script reference/index linked by the owning skill.
Follow that repository's existing layout; do not create a global catalog or
assume the repository-root README is the index.

```md
- `<relative/path/to/script>` — Purpose / when to use it.
```

Resolve paths relative to the index's documented base. Link to detailed usage
when useful; keep inputs, outputs, examples, mutation behavior, verification,
and heuristic coverage boundaries in the script's help or associated usage
documentation, not duplicated in every discovery entry. In that usage
documentation, preserve applicable rate/stop conditions for live services,
untrusted-content handling, and append/rewrite/dedupe behavior for shared files.

Keep examples sanitized and coverage claims bounded (`exhaustive: false` unless
a closed input contract proves otherwise). When adding, renaming, or removing a
script, update this same index and the owning skill's pointer as needed.
