# Capture a papercut

Record concrete, avoidable tool, documentation, environment, or workflow friction after a safe workaround—or before handing off a blocker. Keep it short and sanitized; do not turn capture into a repair investigation.

## Match before writing

Inspect the open record with `papercut.py list` and check closed history if a prior resolution may explain the symptom. Compare the **underlying issue and affected workflow**, not merely the wording. The helper cannot match semantically equivalent reports for you.

- If an open entry describes the same issue, use `observe --id` to record a **distinct incident** rather than adding another entry. Repeated retries in one task/run count once. Re-running an observe with the same incident ID on that entry is a no-op. A closed issue that genuinely recurs can warrant a new entry referencing the old ID.
- Otherwise use `add`, assigning severity **at capture**. Name the blocked workflow, observed time cost, and reason; do not guess historical frequency or time loss.

```bash
PAPERCUTS_TOOL="$HOME/.hermes/synced-skills/papercuts/scripts/papercut.py"
python3 "$PAPERCUTS_TOOL" list
python3 "$PAPERCUTS_TOOL" add \
  --category tool --summary "Browser login kept failing" \
  --context "Owned test-browser login" --severity high --breaking yes \
  --reason "Normal browser workflow blocked; manual handoff required" \
  --minutes-lost 15 --incident "agent-a:run-42"
# If the same issue happens in another run:
python3 "$PAPERCUTS_TOOL" observe --id "PC-20261015-120000-example" \
  --incident "agent-b:run-51" --minutes-lost 8
```

`--incident` is a non-sensitive, stable agent/task/run ID (letters, digits, `.`, `_`, `:`, `-`), unique **per incident on that issue**; do not use an account name or target identifier. One run can report several different issues. `--minutes-lost` is the observed incremental agent time, rounded to whole minutes (0 is valid). `PAPERCUTS_SOURCE` supplies writer identity; otherwise the hostname is used. Use `--file` before the subcommand for **all** operations on an intentional alternate record. The default is `~/Shared/PAPERCUTS.md`. Writes serialize under an advisory lock.

## Severity rubric

- **Low:** Minor workaround, little time lost; normal task proceeds.
- **Medium:** Repeated friction or meaningful time lost; normal task still proceeds.
- **High:** Workflow blocked, degraded path required, or substantial repeated time lost.
- **Critical:** Widespread essential-workflow hard stop or serious operational consequences; requires `--breaking yes` and a specific impact reason. Frequency alone never creates Critical.

The agent assigns severity and a short reason when adding. On later evidence, `observe --severity ... --reason ...` can raise the agent rating (never silently lower it); `--breaking yes` records a newly recognized blocker. The helper automatically raises **Low to Medium at 3 distinct observed incidents**, and to **High at 5** if the workflow is blocked or at least **60 observed minutes** have been lost. Low-cost nonbreaking repetition remains at Medium; automatic escalation never produces Critical. Each entry retains its agent rating, effective severity, observed count, cumulative observed time, and escalation reason. `list` shows high priority first. Treat these as triage signals, not proof of a fix or a measured historical rate.

Old entries remain unrated with unknown prior frequency/time. On their first new occurrence, provide `--severity`, `--breaking`, and `--reason` to `observe`; counting starts at that occurrence. Do not backfill imagined events.

Categories: `tool`, `docs`, `workflow`, `environment`, `integration`, `other`. Use `--evidence` for a sanitized error fragment or workaround and `--impact` only if further context is useful. Never record credentials, cookies, authorization URLs, raw requests/responses, private target/customer content, or personal data.
