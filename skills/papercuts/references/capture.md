# Capture a papercut

Use this when concrete tool, browser/auth, documentation, or workflow friction blocks progress or causes a repeated workaround. Record it after a safe workaround—or before handing off a blocker—without interrupting the task to repair it. Do not record speculation, preferences, raw transcripts, or sensitive details.

## Check before adding

1. Inspect the relevant shared record's open entries with `papercut.py list`. Also inspect its closed entries when a prior resolution may explain the same symptom. Compare the **underlying issue and affected workflow**, not just matching words. The helper does not deduplicate automatically.
2. If an open entry already describes the same issue, **do not add another**. Use its ID for the handoff; if new evidence matters, include it in the task's existing notes or bring it to the reviewer rather than creating a second papercut. A closed issue that has genuinely recurred may warrant a new entry referencing the old ID, after confirming it is a new occurrence.
3. If no entry covers this issue, add one short sanitized record. Keep enough context for later verification; do not diagnose deeply just to log it.

```bash
PAPERCUTS_TOOL="$HOME/.hermes/synced-skills/papercuts/scripts/papercut.py"
python3 "$PAPERCUTS_TOOL" list
# Inspect the Closed section of ~/Shared/PAPERCUTS.md when relevant.
python3 "$PAPERCUTS_TOOL" add \
  --category tool \
  --summary "Browser login kept failing" \
  --context "OAuth flow in the test browser"
```

The default record is `~/Shared/PAPERCUTS.md`. Use `--file` on **both** `list` and `add` for an intentional alternate record. The helper makes no network calls and serializes writes with an advisory lock. `PAPERCUTS_SOURCE` sets the writer identity; otherwise the hostname is recorded. When multiple agents share a host, set an explicit identity, for example `PAPERCUTS_SOURCE="hoster:recon-agent"`.

Categories are `tool`, `docs`, `workflow`, `environment`, `integration`, and `other`. Summarize the observable failure and name the task/tool/surface in `--context`. Use `--evidence` for a sanitized error fragment or workaround and `--impact` only when the reason to revisit is unclear. Redact secrets, authorization URLs, cookies, raw request/response data, private target or customer content, and personal data; replace them with a class such as `[redacted token]`.
