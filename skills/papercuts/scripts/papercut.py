#!/usr/bin/env python3
"""Capture, prioritize, and review sanitized agent papercuts in a Markdown record."""

from __future__ import annotations

import argparse
import fcntl
import os
import re
import socket
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HEADER = "# Papercuts\n\n"
OPEN_HEADER = "## Open\n\n"
CLOSED_HEADER = "## Closed\n\n"
CATEGORIES = ("tool", "docs", "workflow", "environment", "integration", "other")
SEVERITIES = ("low", "medium", "high", "critical")
SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:api[_-]?key|access[_-]?token|refresh[_-]?token|bearer|authorization|password|secret)\b", re.I),
    re.compile(r"\b(?:AKIA|ghp_|github_pat_|sk-[A-Za-z0-9])", re.I),
)
ENTRY = re.compile(r"(?ms)^- \[ \] \*\*(PC-[^*]+)\*\*.*?(?=^- \[ |\Z)")
INCIDENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,119}\Z")


def fail(message: str) -> None:
    print(f"papercut: error: {message}", file=sys.stderr)
    raise SystemExit(2)


def record_path(raw_path: str | None) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    configured = os.environ.get("PAPERCUTS_FILE")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path.home() / "Shared" / "PAPERCUTS.md"


def validate_safe(value: str, label: str) -> str:
    normalized = " ".join(value.strip().split())
    if not normalized:
        fail(f"--{label} cannot be empty")
    if any(pattern.search(normalized) for pattern in SENSITIVE_PATTERNS):
        fail(f"--{label} looks sensitive; redact it before recording")
    return normalized


def incident_key(value: str) -> str:
    if not INCIDENT.fullmatch(value):
        fail("--incident must be a non-sensitive task/run ID (letters, numbers, . _ : -)")
    validate_safe(value, "incident")
    return value


def source_name(args: argparse.Namespace) -> str:
    return validate_safe(args.source or os.environ.get("PAPERCUTS_SOURCE") or socket.gethostname(), "source")


def load_or_initialize(path: Path) -> str:
    if not path.exists():
        return HEADER + OPEN_HEADER + CLOSED_HEADER
    content = path.read_text(encoding="utf-8").rstrip() + "\n\n"
    if not content.startswith(HEADER) or OPEN_HEADER not in content or CLOSED_HEADER not in content:
        fail(f"{path} must contain '# Papercuts', '## Open', and '## Closed' headings")
    return content


def open_span(content: str) -> tuple[int, int]:
    start = content.index(OPEN_HEADER) + len(OPEN_HEADER)
    return start, content.index(CLOSED_HEADER, start)


def entries(content: str) -> list[re.Match[str]]:
    start, end = open_span(content)
    return list(ENTRY.finditer(content, start, end))


def field(entry: str, name: str) -> str | None:
    match = re.search(rf"(?m)^  - {re.escape(name)}: (.*)$", entry)
    return match.group(1) if match else None


def replace_field(entry: str, name: str, value: str) -> str:
    pattern = rf"(?m)^  - {re.escape(name)}: .*$"
    if re.search(pattern, entry):
        return re.sub(pattern, lambda _: f"  - {name}: {value}", entry, count=1)
    return entry.rstrip() + f"\n  - {name}: {value}\n\n"


def occurrence_line(key: str, minutes: int) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"  - Occurrence: {key} @ {stamp} (+{minutes} min)"


def priority(agent: str, breaking: bool, count: int, minutes: int) -> tuple[str, str | None]:
    rank = SEVERITIES.index(agent)
    floor = 1 if count >= 3 else 0
    if count >= 5 and (breaking or minutes >= 60):
        floor = 2
    effective = SEVERITIES[max(rank, floor)]
    reason = None
    if floor > rank:
        reason = "3 distinct incidents" if floor == 1 else (
            "5 distinct incidents with a blocked workflow" if breaking else
            "5 distinct incidents and at least 60 minutes lost"
        )
    return effective, reason


@contextmanager
def locked_record(path: Path):
    """Serialize helper updates to one record across cooperating processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_name(path.name + ".lock").open("a+", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def validate_rating(severity: str, breaking: str, reason: str) -> str:
    rationale = validate_safe(reason, "reason")
    if severity == "critical" and breaking != "yes":
        fail("critical requires a blocked essential workflow (--breaking yes) and an impact reason")
    return rationale


def command_add(args: argparse.Namespace) -> None:
    path = record_path(args.file)
    summary = validate_safe(args.summary, "summary")
    context = validate_safe(args.context, "context")
    impact = validate_safe(args.impact, "impact") if args.impact else None
    evidence = validate_safe(args.evidence, "evidence") if args.evidence else None
    source = source_name(args)
    key = incident_key(args.incident)
    rationale = validate_rating(args.severity, args.breaking, args.reason)
    stamp = datetime.now(timezone.utc)
    identifier = f"{stamp.strftime('PC-%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}"
    lines = [
        f"- [ ] **{identifier}** [{args.category}] {summary}",
        f"  - Context: {context}",
        f"  - Source: {source}",
        f"  - Severity: {args.severity} (agent: {args.severity})",
        f"  - Breaking: {args.breaking}",
        f"  - Severity reason: {rationale}",
        "  - Occurrences: 1",
        f"  - Time lost: {args.minutes_lost} min (observed)",
        occurrence_line(key, args.minutes_lost),
    ]
    if impact:
        lines.append(f"  - Impact: {impact}")
    if evidence:
        lines.append(f"  - Evidence/workaround: {evidence}")
    with locked_record(path):
        content = load_or_initialize(path)
        content = content.replace(CLOSED_HEADER, "\n".join(lines) + "\n\n" + CLOSED_HEADER, 1)
        path.write_text(content, encoding="utf-8")
    print(f"added {identifier} to {path} (severity {args.severity})")


def command_observe(args: argparse.Namespace) -> None:
    path = record_path(args.file)
    if not path.exists():
        fail(f"no papercuts record at {path}")
    key = incident_key(args.incident)
    with locked_record(path):
        content = load_or_initialize(path)
        match = next((item for item in entries(content) if item.group(1) == args.identifier), None)
        if match is None:
            fail(f"open entry {args.identifier!r} was not found")
        assert match is not None
        entry = match.group()
        if re.search(rf"(?m)^  - Occurrence: {re.escape(key)} @ ", entry):
            print(f"incident {key} already recorded on {args.identifier}; unchanged")
            return
        rating = field(entry, "Severity")
        if rating is None:
            if not (args.severity and args.breaking and args.reason):
                fail("legacy entry is unrated; provide --severity, --breaking, and --reason")
            agent = args.severity
            breaking = args.breaking
            entry = replace_field(entry, "Breaking", breaking)
            entry = replace_field(entry, "Severity reason", validate_rating(agent, breaking, args.reason))
            count = 0  # Historical occurrences are unknown, not inferred.
            minutes = 0
        else:
            parsed = re.fullmatch(r"(low|medium|high|critical) \(agent: (low|medium|high|critical)\)", rating)
            if not parsed:
                fail(f"entry {args.identifier} has an unsupported severity field")
            assert parsed is not None
            agent = parsed.group(2)
            breaking = field(entry, "Breaking")
            count_field = field(entry, "Occurrences")
            minutes_field = field(entry, "Time lost")
            if breaking not in ("yes", "no") or not count_field or not minutes_field:
                fail(f"entry {args.identifier} is missing scoring fields")
            assert count_field is not None and minutes_field is not None
            count = int(count_field)
            minutes = int(minutes_field.split(" min", 1)[0])
            if args.severity and SEVERITIES.index(args.severity) > SEVERITIES.index(agent):
                agent = args.severity
                entry = replace_field(entry, "Severity reason", validate_rating(agent, args.breaking or breaking, args.reason or ""))
            if args.breaking == "yes":
                breaking = "yes"
                entry = replace_field(entry, "Breaking", breaking)
        if agent == "critical" and breaking != "yes":
            fail("critical requires --breaking yes")
        count += 1
        minutes += args.minutes_lost
        effective, escalation = priority(agent, breaking == "yes", count, minutes)
        entry = replace_field(entry, "Severity", f"{effective} (agent: {agent})")
        entry = replace_field(entry, "Occurrences", str(count))
        entry = replace_field(entry, "Time lost", f"{minutes} min (observed)")
        if escalation:
            entry = replace_field(entry, "Escalation", escalation)
        else:
            entry = re.sub(r"(?m)^  - Escalation: .*\n", "", entry)
        entry = entry.rstrip() + "\n" + occurrence_line(key, args.minutes_lost) + "\n\n"
        content = content[:match.start()] + entry + content[match.end():]
        path.write_text(content, encoding="utf-8")
    print(f"observed {args.identifier}: {count} incidents, {minutes} min, severity {effective}")


def command_list(args: argparse.Namespace) -> None:
    path = record_path(args.file)
    if not path.exists():
        print(f"no papercuts record at {path}")
        return
    content = load_or_initialize(path)
    items = entries(content)
    if not items:
        print(f"no open papercuts in {path}")
        return
    def rank(match: re.Match[str]) -> int:
        value = field(match.group(), "Severity")
        return SEVERITIES.index(value.split(" ", 1)[0]) if value and value.split(" ", 1)[0] in SEVERITIES else -1
    print("\n\n".join(item.group().strip() for item in sorted(items, key=rank, reverse=True)))


def command_close(args: argparse.Namespace) -> None:
    path = record_path(args.file)
    if not path.exists():
        fail(f"no papercuts record at {path}")
    resolution = validate_safe(args.resolution, "resolution")
    with locked_record(path):
        content = load_or_initialize(path)
        start, end = open_span(content)
        open_body = content[start:end]
        closed_body = content[end + len(CLOSED_HEADER):]
        match = next((item for item in ENTRY.finditer(open_body) if item.group(1) == args.identifier), None)
        if not match:
            fail(f"open entry {args.identifier!r} was not found")
        assert match is not None
        entry = match.group().rstrip().replace("- [ ]", "- [x]", 1)
        entry += f"\n  - Resolution: {resolution}"
        remaining = (open_body[:match.start()] + open_body[match.end():]).strip()
        content = content[:start] + (remaining + "\n\n" if remaining else "") + CLOSED_HEADER
        content += (closed_body.strip() + "\n\n" if closed_body.strip() else "") + entry + "\n"
        path.write_text(content, encoding="utf-8")
    print(f"closed {args.identifier} in {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", help="record path (default: $PAPERCUTS_FILE or ~/Shared/PAPERCUTS.md)")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add = subparsers.add_parser("add", help="append one sanitized, severity-rated papercut")
    add.add_argument("--category", choices=CATEGORIES, required=True)
    add.add_argument("--summary", required=True)
    add.add_argument("--context", required=True)
    add.add_argument("--source", help="writer identity (default: $PAPERCUTS_SOURCE or hostname)")
    add.add_argument("--impact", help="optional short reason this is worth revisiting")
    add.add_argument("--evidence", help="sanitized error fragment or workaround")
    add.add_argument("--severity", choices=SEVERITIES, required=True)
    add.add_argument("--breaking", choices=("yes", "no"), required=True)
    add.add_argument("--reason", required=True, help="impact justification for agent-assigned severity")
    add.add_argument("--incident", required=True, help="non-sensitive unique task/run incident ID")
    add.add_argument("--minutes-lost", type=nonnegative_minutes, required=True)
    add.set_defaults(handler=command_add)

    observe = subparsers.add_parser("observe", help="record one distinct incident on an open entry")
    observe.add_argument("--id", dest="identifier", required=True)
    observe.add_argument("--incident", required=True)
    observe.add_argument("--minutes-lost", type=nonnegative_minutes, required=True)
    observe.add_argument("--severity", choices=SEVERITIES, help="first rating of legacy entry, or increased agent impact rating")
    observe.add_argument("--breaking", choices=("yes", "no"))
    observe.add_argument("--reason", help="required for first rating or a higher agent rating")
    observe.set_defaults(handler=command_observe)

    listing = subparsers.add_parser("list", help="show unresolved papercuts, highest severity first")
    listing.set_defaults(handler=command_list)
    close = subparsers.add_parser("close", help="close an entry and retain its history")
    close.add_argument("--id", dest="identifier", required=True)
    close.add_argument("--resolution", required=True)
    close.set_defaults(handler=command_close)
    return parser


def nonnegative_minutes(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("minutes must be a nonnegative integer") from None
    if number < 0:
        raise argparse.ArgumentTypeError("minutes must be a nonnegative integer")
    return number


def main() -> None:
    args = build_parser().parse_args()
    args.handler(args)


if __name__ == "__main__":
    main()
