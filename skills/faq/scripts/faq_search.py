#!/usr/bin/env python3
"""Search central and program FAQ markdown for solved-problem entries."""

from __future__ import annotations

import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CENTRAL = Path("/home/ryushe/notes/appsec/faq")
DEFAULT_SHARED = Path(os.environ.get("HARNESS_SHARED_BASE", "~/Shared")).expanduser()


@dataclass
class Match:
    score: int
    path: Path
    title: str
    line: int
    snippet: str


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def title_for(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ")


def candidate_roots(args: argparse.Namespace) -> list[Path]:
    roots: list[Path] = []
    if args.program:
        family = args.family or "web_bounty"
        lane = args.lane or "web"
        roots.append(DEFAULT_SHARED / family / args.program / lane / "notes" / "faq")
        roots.append(Path.home() / "Shared" / family / args.program / lane / "notes" / "faq")
    roots.append(args.central.expanduser())

    seen: set[Path] = set()
    existing: list[Path] = []
    for root in roots:
        resolved = root.expanduser()
        if resolved in seen or not resolved.exists():
            continue
        seen.add(resolved)
        existing.append(resolved)
    return existing


def score_text(query_terms: list[str], text: str, path: Path) -> int:
    haystack = f"{path.name}\n{text}".lower()
    score = 0
    for term in query_terms:
        if term in haystack:
            score += 10
        score += haystack.count(term) * 2
    if "#faq" in haystack:
        score += 3
    if "script:" in haystack or "command:" in haystack:
        score += 3
    return score


def best_line(query_terms: list[str], text: str) -> tuple[int, str]:
    lines = text.splitlines()
    for index, line in enumerate(lines, start=1):
        lower = line.lower()
        if any(term in lower for term in query_terms):
            return index, line.strip()
    for index, line in enumerate(lines, start=1):
        if line.strip():
            return index, line.strip()
    return 1, ""


def search(query: str, roots: list[Path], limit: int) -> list[Match]:
    query_terms = [term for term in re.split(r"[^a-z0-9_.:/-]+", query.lower()) if term]
    if not query_terms:
        return []

    matches: list[Match] = []
    for root in roots:
        for path in sorted(root.rglob("*.md")):
            text = read_text(path)
            score = score_text(query_terms, text, path)
            if score <= 0:
                continue
            line, snippet = best_line(query_terms, text)
            matches.append(Match(score, path, title_for(path, text), line, snippet))
    matches.sort(key=lambda item: (-item.score, str(item.path)))
    return matches[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Problem, error, script, tool, or flow to search for")
    parser.add_argument("--family", help="Shared family, for example web_bounty")
    parser.add_argument("--program", help="Program name for active program FAQ lookup")
    parser.add_argument("--lane", help="Program lane, for example web")
    parser.add_argument("--central", type=Path, default=DEFAULT_CENTRAL)
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    roots = candidate_roots(args)
    if not roots:
        print("No FAQ roots found.")
        return 2

    matches = search(args.query, roots, args.limit)
    print("FAQ roots:")
    for root in roots:
        print(f"- {root}")
    if not matches:
        print("\nNo matching FAQ entries found.")
        return 1

    print("\nMatches:")
    for match in matches:
        print(f"- {match.title}")
        print(f"  path: {match.path}:{match.line}")
        print(f"  score: {match.score}")
        if match.snippet:
            print(f"  snippet: {match.snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
