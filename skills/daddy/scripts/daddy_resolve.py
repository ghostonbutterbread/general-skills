#!/usr/bin/env python3
"""Resolve Daddy model movement from highest-to-lowest model tables."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "tables"

MOVEMENTS = {
    "2up": -2,
    "1up": -1,
    "up": -1,
    "base": 0,
    "1down": 1,
    "down": 1,
    "2down": 2,
}


def normalize(model: str) -> str:
    return model.strip().lower()


def parse_table(provider: str) -> list[list[str]]:
    path = TABLE_DIR / f"{provider}.txt"
    if not path.exists():
        raise SystemExit(f"unknown provider table: {path}")

    rows: list[list[str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        aliases = [normalize(part) for part in line.split(",") if part.strip()]
        if aliases:
            rows.append(aliases)
    return rows


def numeric_key(model: str) -> tuple[str, float] | None:
    value = normalize(model)
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if not match:
        return None
    family = value[: match.start()].strip("-_. ")
    if not family:
        return None
    return family, float(match.group(1))


def exact_index(rows: list[list[str]], current: str) -> int | None:
    current = normalize(current)
    for index, aliases in enumerate(rows):
        if current in aliases:
            return index
    return None


def representative(rows: list[list[str]]) -> list[str]:
    return [aliases[0] for aliases in rows]


def inferred_position(rows: list[list[str]], current: str) -> tuple[int, str] | None:
    current_key = numeric_key(current)
    if current_key is None:
        return None
    current_family, current_version = current_key

    reps = representative(rows)
    comparable: list[tuple[int, float]] = []
    for index, model in enumerate(reps):
        key = numeric_key(model)
        if key and key[0] == current_family:
            comparable.append((index, key[1]))

    if not comparable:
        return None

    stronger_count = 0
    for _, version in comparable:
        if version > current_version:
            stronger_count += 1

    if stronger_count == 0 and current_version > max(version for _, version in comparable):
        return 0, "above_table"
    if stronger_count == len(comparable) and current_version < min(version for _, version in comparable):
        return comparable[-1][0] + 1, "below_table"
    return comparable[stronger_count][0], "between_table"


def resolve(rows: list[list[str]], current: str, movement: str) -> dict[str, object]:
    movement = normalize(movement)
    if movement == "max":
        return {
            "current_model": current,
            "movement": movement,
            "selected_model": rows[0][0],
            "status": "max",
        }
    if movement not in MOVEMENTS:
        raise SystemExit(f"unknown movement: {movement}")

    exact = exact_index(rows, current)
    models = representative(rows)

    if exact is not None:
        target = max(0, min(len(rows) - 1, exact + MOVEMENTS[movement]))
        return {
            "current_model": current,
            "movement": movement,
            "selected_model": models[target] if movement != "base" else normalize(current),
            "status": "exact",
            "current_index": exact,
            "selected_index": target,
        }

    inferred = inferred_position(rows, current)
    if inferred is None:
        return {
            "current_model": current,
            "movement": movement,
            "selected_model": normalize(current),
            "status": "unknown_not_listed",
            "note": "No exact or numeric same-family match. Add this model to a table.",
        }

    position, status = inferred
    if movement == "base":
        selected = normalize(current)
    elif MOVEMENTS[movement] < 0:
        target = position + MOVEMENTS[movement]
        selected = normalize(current) if target < 0 else models[target]
    else:
        target = position + MOVEMENTS[movement] - 1
        selected = normalize(current) if target >= len(models) else models[target]

    return {
        "current_model": current,
        "movement": movement,
        "selected_model": selected,
        "status": f"inferred_{status}",
        "virtual_position": position,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, help="table name, such as chatgpt or claude")
    parser.add_argument("--current", required=True, help="current model id")
    parser.add_argument("--movement", required=True, help="up, down, base, max, 2up, or 2down")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args()

    result = resolve(parse_table(args.provider), args.current, args.movement)
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(result["selected_model"])


if __name__ == "__main__":
    main()
