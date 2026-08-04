#!/usr/bin/env python3
"""Append and review sanitized agent papercuts in a project Markdown record."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HEADER = "# Papercuts\n\n"
OPEN_HEADER = "## Open\n\n"
CLOSED_HEADER = "## Closed\n\n"
CATEGORIES = ("tool", "docs", "workflow", "environment", "integration", "other")
SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|bearer|authorization|password|secret)\b", re.I),
    re.compile(r"\b(?:AKIA|ghp_|github_pat_|sk-[A-Za-z0-9])", re.I),
)


def fail(message: str) -> None:
    print(f"papercut: error: {message}", file=sys.stderr)
    raise SystemExit(2)


def nearest_git_root(start: Path) -> Path:
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return start
    return Path(result.stdout.strip())


def record_path(raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    configured = os.environ.get("PAPERCUTS_FILE")
    if configured:
        return Path(configured).expanduser().resolve()
    return nearest_git_root(Path.cwd()) / "PAPERCUTS.md"


def validate_safe(value: str, label: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        fail(f"--{label} cannot be empty")
    if any(pattern.search(normalized) for pattern in SENSITIVE_PATTERNS):
        fail(f"--{label} looks sensitive; redact it before recording")
    return normalized


def load_or_initialize(path: Path) -> str:
    if not path.exists():
        return HEADER + OPEN_HEADER + CLOSED_HEADER
    content = path.read_text(encoding="utf-8")
    if not content.startswith(HEADER) or OPEN_HEADER not in content or CLOSED_HEADER not in content:
        fail(f"{path} must contain '# Papercuts', '## Open', and '## Closed' headings")
    return content


def insert_before_closed(content: str, entry: str) -> str:
    return content.replace(CLOSED_HEADER, entry + "\n" + CLOSED_HEADER, 1)


def command_add(args: argparse.Namespace) -> None:
    path = record_path(args.file)
    summary = validate_safe(args.summary, "summary")
    context = validate_safe(args.context, "context")
    impact = validate_safe(args.impact, "impact") if args.impact else None
    evidence = validate_safe(args.evidence, "evidence") if args.evidence else None
    stamp = datetime.now(timezone.utc)
    identifier = stamp.strftime("PC-%Y%m%d-%H%M%S")
    lines = [
        f"- [ ] **{identifier}** [{args.category}] {summary}",
        f"  - Context: {context}",
    ]
    if impact:
        lines.append(f"  - Impact: {impact}")
    if evidence:
        lines.append(f"  - Evidence/workaround: {evidence}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(insert_before_closed(load_or_initialize(path), "\n".join(lines)), encoding="utf-8")
    print(f"added {identifier} to {path}")


def command_list(args: argparse.Namespace) -> None:
    path = record_path(args.file)
    if not path.exists():
        print(f"no papercuts record at {path}")
        return
    content = load_or_initialize(path)
    open_section = content.split(OPEN_HEADER, 1)[1].split(CLOSED_HEADER, 1)[0].strip()
    if not open_section:
        print(f"no open papercuts in {path}")
        return
    print(open_section)


def command_close(args: argparse.Namespace) -> None:
    path = record_path(args.file)
    if not path.exists():
        fail(f"no papercuts record at {path}")
    resolution = validate_safe(args.resolution, "resolution")
    content = load_or_initialize(path)
    open_start = content.index(OPEN_HEADER) + len(OPEN_HEADER)
    closed_start = content.index(CLOSED_HEADER, open_start)
    open_body = content[open_start:closed_start]
    closed_body = content[closed_start + len(CLOSED_HEADER) :]
    pattern = re.compile(
        rf"(?ms)^- \[ \] \*\*{re.escape(args.identifier)}\*\*.*?(?=^- \[ |\Z)"
    )
    match = pattern.search(open_body)
    if not match:
        fail(f"open entry {args.identifier!r} was not found")
    assert match is not None
    entry = match.group(0).rstrip().replace("- [ ]", "- [x]", 1)
    entry += f"\n  - Resolution: {resolution}"
    remaining_open = (open_body[: match.start()] + open_body[match.end() :]).strip()
    rebuilt = content[:open_start]
    rebuilt += (remaining_open + "\n\n") if remaining_open else ""
    rebuilt += CLOSED_HEADER
    rebuilt += (closed_body.strip() + "\n\n") if closed_body.strip() else ""
    rebuilt += entry + "\n"
    path.write_text(rebuilt, encoding="utf-8")
    print(f"closed {args.identifier} in {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="record path (default: $PAPERCUTS_FILE or nearest Git root/PAPERCUTS.md)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="append one sanitized papercut")
    add.add_argument("--category", choices=CATEGORIES, required=True)
    add.add_argument("--summary", required=True)
    add.add_argument("--context", required=True)
    add.add_argument("--impact", help="optional short reason this is worth revisiting")
    add.add_argument("--evidence", help="sanitized error fragment or workaround")
    add.set_defaults(handler=command_add)

    list_parser = subparsers.add_parser("list", help="show unresolved papercuts")
    list_parser.set_defaults(handler=command_list)

    close = subparsers.add_parser("close", help="close an entry and retain its history")
    close.add_argument("--id", dest="identifier", required=True)
    close.add_argument("--resolution", required=True)
    close.set_defaults(handler=command_close)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
