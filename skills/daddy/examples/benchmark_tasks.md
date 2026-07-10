# Daddy Benchmark Task Fixtures

Use these task classes for an A/B test.

## Tracks

- `baseline_normal`: current model handles all tasks directly.
- `daddy_routed`: current model keeps parent context, delegates bounded packets down/up.

## Fixture Classes

| task_type | expected_route | success check |
|---|---:|---|
| recon_sort | down | correctly groups URLs/statuses and preserves full URLs |
| mechanical_extract | down | extracts exact endpoints/params/facts without invention |
| normal_coding | base | implements requested change and passes targeted tests |
| exploit_reasoning | up | identifies exploit path, blockers, and next validation steps |
| reportability_review | up | gives defensible severity/reportability call with uncertainty |

## Minimum Benchmark

Run at least 20 tasks:

- 6 recon_sort
- 4 mechanical_extract
- 4 normal_coding
- 3 exploit_reasoning
- 3 reportability_review

For each task, record: selected model, token counts, latency, success, reviewer
score, rework needed, and whether routing changed the final decision.
