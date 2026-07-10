#!/usr/bin/env python3
"""Dry-run Daddy routing benchmark.

This simulator validates routing shape and rough cost proxy. It does not
measure real model quality, latency, or token billing.
"""

from __future__ import annotations

LADDER = ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"]
CURRENT_MODEL = "gpt-5.6-terra"
COST_UNITS = {"gpt-5.6-luna": 0.35, "gpt-5.6-terra": 1.0, "gpt-5.6-sol": 3.0}
ROUTING_OVERHEAD_UNITS = 0.08

SCENARIOS = {
    "up_heavy_security_review": [("down", 50), ("base", 20), ("up", 30)],
    "balanced_goal_run": [("down", 60), ("base", 30), ("up", 10)],
    "recon_heavy_goal_run": [("down", 80), ("base", 15), ("up", 5)],
    "all_mechanical": [("down", 90), ("base", 10), ("up", 0)],
}


def move(route: str) -> str:
    idx = LADDER.index(CURRENT_MODEL)
    offsets = {"down": 1, "base": 0, "up": -1}
    return LADDER[max(0, min(len(LADDER) - 1, idx + offsets[route]))]


def scenario_cost(mix: list[tuple[str, int]]) -> tuple[float, float]:
    baseline = sum(count for _, count in mix) * COST_UNITS[CURRENT_MODEL]
    routed = 0.0
    for route, count in mix:
        selected = move(route)
        overhead = 0.0 if route == "base" else ROUTING_OVERHEAD_UNITS
        routed += count * (COST_UNITS[selected] + overhead)
    return baseline, routed


def main() -> None:
    for name, mix in SCENARIOS.items():
        baseline, routed = scenario_cost(mix)
        savings = (baseline - routed) / baseline * 100
        print(
            f"{name}: baseline={baseline:.2f} routed={routed:.2f} "
            f"savings={savings:.1f}% mix={mix}"
        )


if __name__ == "__main__":
    main()
