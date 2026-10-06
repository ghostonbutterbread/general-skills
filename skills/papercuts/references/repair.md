# Review and repair a papercut

Use this during a deliberate maintenance pass, not as an interruption to the original task.

## Verify before changing anything

1. List the open entries in the relevant record and group any duplicates by the underlying cause. Pick the clearest entry as the evidence trail; close duplicates only with an accurate cross-reference and disposition.
2. For each issue, inspect the **current** owning tool, documentation, version, environment, and affected workflow. Exercise the reported step or gather equivalent direct evidence to determine whether it **still affects us**. Do not assume an old report or a plausible fix proves the issue is present.
3. If direct evidence shows it no longer affects us, **do not patch**. Close the entry with what was checked, where, and why it is resolved/no longer applicable (for example, an upstream change already landed). Do not claim that we made a fix.
4. If the issue is still present and the fix changes a repository, create a **fresh task branch and isolated worktree** from its selected integration lane before editing. Do not patch directly on the shared integration or stable branch, or reuse another papercut's branch. Patch the owning surface rather than a convenient symptom; run the affected workflow and relevant regression checks, review the diff, and integrate through the repository's normal branch lifecycle. Then close with the verified resolution and canonical path or reference. An evidence-based closure with no patch does not need a code branch.
5. If verification cannot be done because access, environment, or context is missing, leave it open and record the blocker/wake condition in the appropriate task handoff. Mere inability to reproduce is not proof that it is gone.

```bash
PAPERCUTS_TOOL="$HOME/.hermes/synced-skills/papercuts/scripts/papercut.py"
python3 "$PAPERCUTS_TOOL" list
# Replace the example ID with the entry's actual ID from the list.
python3 "$PAPERCUTS_TOOL" close \
  --id 'PC-20260804-123456-abcdef12' \
  --resolution "Checked <current workflow/evidence>; no longer affected because <reason>; no patch made."
```

Use `--file` for an intentional alternate record on both commands. Closing retains the entry in the record's Closed section; never delete its history.

## Ownership and durable outcomes

For large third-party repositories or dependencies we do not own (including Hermes itself), do not turn routine papercut cleanup into local shims, monkey patches, or a private patch stack requiring upkeep. Record the issue and leave the stock installation unchanged unless the user explicitly requests an exception after the maintenance cost is explained. A papercut request does **not** authorize an upstream issue/PR, software update, or configuration change; those need their own task authorization. This does not prevent normal fixes to scripts and repositories we own.

Place a lasting remedy in its canonical home when one is needed: a solved operational workaround in `faq`, repeatable automation in `script-manager`, reusable behavioral guidance in a reviewed skill or seed, or repository-specific correction in that repository's docs/code. Do not auto-promote papercuts to permanent memory. A resolved-without-patch entry needs an honest verification-based disposition, not an invented durable fix.
