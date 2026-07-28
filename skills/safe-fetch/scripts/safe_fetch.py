#!/usr/bin/env python3
"""Fetch external content into quarantine and emit a sanitized document."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html.parser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
import uuid


DEFAULT_QUARANTINE = Path.home() / "safe-fetch" / "quarantine"
MAX_DEFAULT_CHARS = 200_000
ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

PROMPT_INJECTION_PATTERNS = [
    (r"\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|rules|messages)\b", "ignore_previous_instructions"),
    (r"\bignore\b.{0,80}\b(policy|safety|restrictions?)\b", "ignore_safety_policy"),
    (r"\bsystem\s+override\b|\bunrestricted\s+diagnostic\s+mode\b", "role_or_prompt_reference"),
    (r"\b(system|developer|assistant)\s*(prompt|message|instructions?)\b", "role_or_prompt_reference"),
    (r"<\s*/?\s*(system|user_input|developer|assistant)\s*>|```+\s*(system|developer|assistant)\b", "role_boundary_injection"),
    (r"\bhigher-priority\s+instruction\b|\bnew\s+instruction\s*:", "role_boundary_injection"),
    (r"\bdo\s+not\s+(tell|reveal|mention|disclose)\b", "concealment_instruction"),
    (r"\bdo\s+not\s+summarize\b|\binstead,?\s+run\b", "tool_use_instruction"),
    (r"\b(exfiltrate|leak|steal|send)\b.{0,80}\b(secret|token|key|cookie|credential|password)\b", "secret_exfiltration_instruction"),
    (r"\b(send|post|upload)\b.{0,80}\b(/etc/passwd|environment variables?|secrets?|tokens?|credentials?)\b", "secret_exfiltration_instruction"),
    (r"\b(environment variables?|/etc/passwd|secrets?|tokens?|credentials?)\b.{0,120}\b(send|post|upload|exfiltrate)\b", "secret_exfiltration_instruction"),
    (r"\bcurl\b.{0,80}\bPOST\b.{0,80}/etc/passwd\b", "secret_exfiltration_instruction"),
    (r"\b(read|cat|open)\b.{0,80}\b(~/?\.ssh|id_rsa|/etc/passwd|private key)\b", "sensitive_file_read_instruction"),
    (r"\b(call|invoke|use|run)\b.{0,80}\b(tool|function|api|command|shell|bash|curl)\b", "tool_use_instruction"),
    (r"\b(shell\s+tool|bash|curl)\b.{0,80}\b(whoami|/etc/passwd|POST|echo|pwd|id)\b", "tool_use_instruction"),
    (r"\b(create|write)\b.{0,80}\b(file|/tmp/|~/?\.ssh|id_rsa)\b", "file_write_instruction"),
    (r">\s*/tmp/[A-Za-z0-9_.-]+", "file_write_instruction"),
    (r"\bhidden\s+instructions?\b|\bfull\s+system\s+prompt\b", "role_or_prompt_reference"),
    (r"\bdisable\s+safety\s+checks\b|\bapprove\s+all\s+actions\b", "safety_bypass_instruction"),
    (r"\bupdate\b.{0,80}\b(memory|policy|system prompt|instructions|rules)\b", "memory_or_policy_instruction"),
]

SECRET_PATTERNS = [
    (r"(?i)\b(api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-./+=]{16,}", "secret_like_assignment"),
    (r"\bAKIA[0-9A-Z]{16}\b", "aws_access_key_id"),
    (r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b", "github_token_like"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private_key_block"),
]


class TextExtractor(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "template", "svg", "canvas", "iframe", "object", "embed"}:
            self.skip_stack.append(tag.lower())
        if tag.lower() in {"p", "div", "section", "article", "br", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip_stack and self.skip_stack[-1] == tag:
            self.skip_stack.pop()
        if tag in {"p", "div", "section", "article", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_stack:
            self.parts.append(data)

    def text(self) -> str:
        return " ".join("".join(self.parts).split())


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https"}


def make_run_dir(base: Path) -> tuple[str, Path]:
    run_id = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10]
    run_dir = base.expanduser() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_id, run_dir


def docker_available() -> bool:
    return shutil.which("docker") is not None


def cleanup_container(name: str) -> None:
    if not docker_available():
        return
    subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def fetch_with_docker(url: str, run_dir: Path, timeout: int, image: str) -> tuple[bytes, str, str]:
    container = "ghost-safe-fetch-" + uuid.uuid4().hex[:12]
    raw_path = run_dir / "raw.bin"
    meta_path = run_dir / "curl_meta.txt"
    cmd = [
        "docker", "run", "--rm",
        "--name", container,
        "--label", "ghost.safe-fetch=1",
        "--network", "bridge",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--memory", "256m",
        "--cpus", "1.0",
        "--user", f"{os.getuid()}:{os.getgid()}",
        "-v", f"{run_dir.resolve()}:/out",
        image,
        "-fsSL",
        "--max-time", str(timeout),
        "--connect-timeout", "10",
        "--location",
        "--output", "/out/raw.bin",
        "--write-out", "%{content_type}\\n%{http_code}\\n%{url_effective}\\n",
        url,
    ]
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout + 15, check=False)
        meta_path.write_text(result.stdout + result.stderr, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "docker fetch failed").strip())
        return raw_path.read_bytes(), result.stdout.strip(), container
    finally:
        cleanup_container(container)


def fetch_with_urllib(url: str, timeout: int) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "GhostSafeFetch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        content_type = response.headers.get("content-type", "")
        return response.read(), content_type


def read_source(source: str, run_dir: Path, docker_mode: str, timeout: int, image: str) -> tuple[bytes, str, str]:
    if is_url(source):
        if docker_mode in {"auto", "always"} and docker_available():
            try:
                raw, meta, _container = fetch_with_docker(source, run_dir, timeout, image)
                content_type = meta.splitlines()[0] if meta else ""
                return raw, content_type, "docker"
            except Exception as exc:
                if docker_mode == "always":
                    raise
                (run_dir / "docker_fallback_error.txt").write_text(str(exc), encoding="utf-8", errors="replace")
        raw, content_type = fetch_with_urllib(source, timeout)
        return raw, content_type, "host"

    path = Path(source).expanduser()
    raw = path.read_bytes()
    return raw, guess_content_type(path, raw), "file"


def guess_content_type(path: Path, raw: bytes) -> str:
    suffix = path.suffix.lower()
    if suffix in {".html", ".htm"}:
        return "text/html"
    if suffix in {".json"}:
        return "application/json"
    if suffix in {".md", ".txt", ".log", ".csv"}:
        return "text/plain"
    if raw.startswith(b"%PDF"):
        return "application/pdf"
    return "application/octet-stream"


def decode_text(raw: bytes) -> str:
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def canonicalize(raw: bytes, content_type: str) -> tuple[str, list[str]]:
    notes: list[str] = []
    text = decode_text(raw)
    lowered = content_type.lower()
    if "html" in lowered or re.search(r"<\s*html|<\s*body|<\s*script", text[:4096], re.I):
        parser = TextExtractor()
        parser.feed(text)
        text = parser.text()
        notes.append("html_to_inert_text")
    elif raw.startswith(b"%PDF"):
        notes.append("pdf_binary_not_parsed")
        text = "[PDF content quarantined; use a sandboxed PDF parser before model ingestion.]"
    else:
        notes.append("plain_text")

    text = unicodedata.normalize("NFC", text).translate(ZERO_WIDTH)
    text = CONTROL_RE.sub("", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip(), notes


def collect_flags(text: str) -> list[str]:
    flags: list[str] = []
    for pattern, label in PROMPT_INJECTION_PATTERNS + SECRET_PATTERNS:
        if re.search(pattern, text, re.I | re.S):
            flags.append(label)
    return sorted(set(flags))


def redact_for_context(text: str) -> str:
    redacted = text
    for pattern, label in SECRET_PATTERNS:
        redacted = re.sub(pattern, f"[REDACTED:{label}]", redacted, flags=re.I | re.S)
    return redacted


def verdict_for(flags: list[str], mode: str) -> tuple[str, str]:
    prompt_flags = [f for f in flags if f not in {label for _pattern, label in SECRET_PATTERNS}]
    secret_flags = [f for f in flags if f in {label for _pattern, label in SECRET_PATTERNS}]
    if mode == "research" and prompt_flags:
        return "quarantine_research_allowed", "research_lab"
    if secret_flags and prompt_flags:
        return "redact_with_warnings", "research_lab"
    if secret_flags:
        return "redact", "normal"
    if prompt_flags:
        return "allow_with_warnings", "research_lab"
    return "allow", "normal"


def build_document(args: argparse.Namespace) -> dict:
    run_id, run_dir = make_run_dir(Path(args.quarantine))
    raw, content_type, fetcher = read_source(args.source, run_dir, args.docker, args.timeout, args.docker_image)
    raw_path = run_dir / "raw.bin"
    raw_path.write_bytes(raw)
    sha256 = hashlib.sha256(raw).hexdigest()
    text, notes = canonicalize(raw, content_type)
    flags = collect_flags(text)
    verdict, recommended_mode = verdict_for(flags, args.mode)
    safe_text = redact_for_context(text)
    truncated = len(safe_text) > args.max_chars
    if truncated:
        safe_text = safe_text[: args.max_chars] + "\n[TRUNCATED]"
    doc = {
        "type": "SanitizedDocument",
        "schema_version": 1,
        "source": args.source,
        "fetched_at": now_utc(),
        "fetcher": fetcher,
        "mode": args.mode,
        "content_type": content_type,
        "sha256": sha256,
        "verdict": verdict,
        "risk_flags": flags,
        "recommended_mode": recommended_mode,
        "canonicalization": notes,
        "truncated": truncated,
        "content": safe_text,
        "raw_artifact": f"safe-fetch://quarantine/{run_id}/raw.bin",
        "artifact_dir": str(run_dir),
    }
    (run_dir / "sanitized.json").write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")
    return doc


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch content into quarantine and emit sanitized JSON.")
    parser.add_argument("source", help="HTTP(S) URL or local file path")
    parser.add_argument("--mode", choices=["normal", "research"], default="normal")
    parser.add_argument("--docker", choices=["auto", "always", "never"], default="auto")
    parser.add_argument("--docker-image", default="curlimages/curl:latest")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--quarantine", default=os.environ.get("GHOST_SAFE_FETCH_QUARANTINE", str(DEFAULT_QUARANTINE)))
    parser.add_argument("--max-chars", type=int, default=MAX_DEFAULT_CHARS)
    parser.add_argument("--json", action="store_true", help="Emit JSON; currently the default output format.")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        doc = build_document(args)
    except Exception as exc:
        print(json.dumps({"type": "SafeFetchError", "source": getattr(args, "source", None), "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(doc, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
