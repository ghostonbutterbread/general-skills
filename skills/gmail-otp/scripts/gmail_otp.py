#!/usr/bin/env python3
"""Narrow Gmail read/OTP wrapper with a single-recipient send allowlist."""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import sys
import tempfile
from email.mime.text import MIMEText
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ALLOWED_RECIPIENT = "ryushe.dev@gmail.com"
SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
)
# 8765 avoids browser-blocked low-numbered ports while remaining a loopback-only redirect.
REDIRECT_URI = "http://localhost:8765"
MAX_MESSAGE_CHARS = 12_000
OTP_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){4,10}(?!\d)")


def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")).expanduser()


def state_dir() -> Path:
    path = hermes_home() / "gmail-otp"
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)
    return path


def client_path() -> Path:
    return state_dir() / "client_secret.json"


def token_path() -> Path:
    return state_dir() / "token.json"


def pending_path() -> Path:
    return state_dir() / "pending_oauth.json"


def secure_write_json(path: Path, payload: dict) -> None:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
        os.replace(tmp_name, path)
        os.chmod(path, 0o600)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        fail(f"Missing {path.name}. Complete setup first.")
    except json.JSONDecodeError:
        fail(f"Invalid JSON in {path}; remove it and set up again.")


def fail(message: str, code: int = 2) -> None:
    print(json.dumps({"ok": False, "error": message}), file=sys.stderr)
    raise SystemExit(code)


def require_google():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import Flow
        from googleapiclient.discovery import build
    except ImportError:
        fail(
            "Google dependencies are missing. Install only into an isolated venv: "
            "uv venv ~/.hermes/gmail-otp/.venv && "
            "uv pip install --python ~/.hermes/gmail-otp/.venv/bin/python "
            "google-api-python-client google-auth-oauthlib google-auth-httplib2"
        )
    return Request, Credentials, Flow, build


def cmd_setup_client(args: argparse.Namespace) -> None:
    source = Path(args.path).expanduser().resolve()
    if not source.is_file():
        fail(f"Client secret file not found: {source}")
    try:
        payload = json.loads(source.read_text())
    except json.JSONDecodeError:
        fail("Client secret file is not valid JSON.")
    installed = payload.get("installed")
    if not isinstance(installed, dict) or not installed.get("client_id"):
        fail("Expected a Google Desktop OAuth client JSON with an 'installed' object.")
    secure_write_json(client_path(), payload)
    print(json.dumps({"ok": True, "client": str(client_path()), "scopes": list(SCOPES)}))


def cmd_auth_url(_: argparse.Namespace) -> None:
    _, _, Flow, _ = require_google()
    if not client_path().is_file():
        fail("Run setup-client first.")
    flow = Flow.from_client_secrets_file(
        str(client_path()), scopes=SCOPES, redirect_uri=REDIRECT_URI,
        autogenerate_code_verifier=True,
    )
    auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
    secure_write_json(pending_path(), {
        "state": state,
        "code_verifier": flow.code_verifier,
        "redirect_uri": REDIRECT_URI,
        "scope_fingerprint": hashlib.sha256(" ".join(SCOPES).encode()).hexdigest(),
    })
    print(json.dumps({"ok": True, "auth_url": auth_url, "redirect_uri": REDIRECT_URI, "scopes": list(SCOPES)}))


def cmd_auth_code(args: argparse.Namespace) -> None:
    _, _, Flow, _ = require_google()
    pending = load_json(pending_path())
    parsed = urlparse(args.redirect_url)
    params = parse_qs(parsed.query)
    code = (params.get("code") or [None])[0]
    state = (params.get("state") or [None])[0]
    if not code or not state:
        fail("Paste the complete localhost redirect URL containing both code and state.")
    if state != pending.get("state"):
        fail("OAuth state mismatch. Run auth-url again and use only its newest redirect.")
    if pending.get("scope_fingerprint") != hashlib.sha256(" ".join(SCOPES).encode()).hexdigest():
        fail("OAuth scope configuration changed. Run auth-url again.")
    flow = Flow.from_client_secrets_file(
        str(client_path()), scopes=SCOPES,
        redirect_uri=pending["redirect_uri"], state=state,
        code_verifier=pending["code_verifier"],
    )
    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        fail(f"OAuth token exchange failed: {exc}")
    creds = flow.credentials
    granted = set(creds.granted_scopes or SCOPES)
    if granted != set(SCOPES):
        fail("Google did not grant exactly the required read/send scopes; authorization was not saved.")
    secure_write_json(token_path(), json.loads(creds.to_json()))
    pending_path().unlink(missing_ok=True)
    print(json.dumps({"ok": True, "authenticated": True, "scopes": sorted(granted)}))


def credentials():
    Request, Credentials, _, _ = require_google()
    if not token_path().is_file():
        fail("Not authenticated. Run setup-client, auth-url, then auth-code.")
    try:
        creds = Credentials.from_authorized_user_file(str(token_path()), SCOPES)
    except Exception as exc:
        fail(f"Token could not be loaded: {exc}")
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception as exc:
            fail(f"Token refresh failed: {exc}")
        secure_write_json(token_path(), json.loads(creds.to_json()))
    if not creds.valid:
        fail("OAuth token is invalid. Re-authorize this skill.")
    if not creds.has_scopes(SCOPES):
        fail("OAuth token is missing the required Gmail read/send scopes. Re-authorize this skill.")
    return creds


def gmail_service():
    _, _, _, build = require_google()
    return build("gmail", "v1", credentials=credentials(), cache_discovery=False)


def headers_dict(message: dict) -> dict[str, str]:
    return {h.get("name", "").lower(): h.get("value", "") for h in message.get("payload", {}).get("headers", [])}


def decode_part(part: dict) -> str:
    mime = part.get("mimeType", "")
    data = part.get("body", {}).get("data")
    if data and mime in {"text/plain", "text/html"}:
        raw = base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
        if mime == "text/html":
            raw = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        return raw
    for child in part.get("parts", []) or []:
        text = decode_part(child)
        if text:
            return text
    return ""


def summary(message: dict) -> dict:
    headers = headers_dict(message)
    return {
        "id": message["id"], "thread_id": message.get("threadId", ""),
        "from": headers.get("from", ""), "to": headers.get("to", ""),
        "subject": headers.get("subject", ""), "date": headers.get("date", ""),
        "snippet": message.get("snippet", ""), "labels": message.get("labelIds", []),
        "untrusted_content": True,
    }


def list_messages(query: str, maximum: int) -> list[dict]:
    service = gmail_service()
    result = service.users().messages().list(userId="me", q=query, maxResults=maximum).execute()
    items = []
    for metadata in result.get("messages", []):
        message = service.users().messages().get(
            userId="me", id=metadata["id"], format="metadata",
            metadataHeaders=["From", "To", "Subject", "Date"],
        ).execute()
        items.append(summary(message))
    return items


def cmd_inbox(args: argparse.Namespace) -> None:
    print(json.dumps({"ok": True, "read_only": True, "messages": list_messages("in:inbox", args.maximum)}, indent=2))


def cmd_search(args: argparse.Namespace) -> None:
    print(json.dumps({"ok": True, "read_only": True, "query": args.query, "messages": list_messages(args.query, args.maximum)}, indent=2))


def cmd_get(args: argparse.Namespace) -> None:
    message = gmail_service().users().messages().get(userId="me", id=args.message_id, format="full").execute()
    result = summary(message)
    body = decode_part(message.get("payload", {}))[:args.max_chars]
    result.update({"body": body, "body_truncated": len(body) >= args.max_chars})
    print(json.dumps({"ok": True, "read_only": True, "message": result}, indent=2, ensure_ascii=False))


def cmd_otp(args: argparse.Namespace) -> None:
    service = gmail_service()
    candidates = []
    for item in list_messages(args.query, args.maximum):
        message = service.users().messages().get(userId="me", id=item["id"], format="full").execute()
        body = decode_part(message.get("payload", ""))[:MAX_MESSAGE_CHARS]
        codes = []
        for match in OTP_PATTERN.findall(body):
            code = re.sub(r"\D", "", match)
            if code not in codes:
                codes.append(code)
        if codes:
            candidates.append({"id": item["id"], "from": item["from"], "subject": item["subject"], "codes": codes, "untrusted_content": True})
    print(json.dumps({"ok": True, "read_only": True, "query": args.query, "candidates": candidates}, indent=2))


def cmd_send(args: argparse.Namespace) -> None:
    recipient = args.to.strip()
    if recipient.casefold() != ALLOWED_RECIPIENT:
        fail(f"Recipient rejected. The only permitted recipient is {ALLOWED_RECIPIENT}.")
    if "\n" in recipient or "\r" in recipient or "\n" in args.subject or "\r" in args.subject:
        fail("Recipient and subject must not contain newline characters.")
    message = MIMEText(args.body, "plain", "utf-8")
    message["To"] = ALLOWED_RECIPIENT
    message["Subject"] = args.subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = gmail_service().users().messages().send(userId="me", body={"raw": raw}).execute()
    print(json.dumps({"ok": True, "sent": True, "to": ALLOWED_RECIPIENT, "id": result.get("id"), "thread_id": result.get("threadId")}))


def cmd_status(_: argparse.Namespace) -> None:
    credentials()  # validates the token and its exact required capability set
    print(json.dumps({"ok": True, "authenticated": True, "state_dir": str(state_dir()), "scopes": list(SCOPES), "allowed_recipient": ALLOWED_RECIPIENT}))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("setup-client"); p.add_argument("path"); p.set_defaults(func=cmd_setup_client)
    p = commands.add_parser("auth-url"); p.set_defaults(func=cmd_auth_url)
    p = commands.add_parser("auth-code"); p.add_argument("redirect_url"); p.set_defaults(func=cmd_auth_code)
    p = commands.add_parser("status"); p.set_defaults(func=cmd_status)
    p = commands.add_parser("inbox"); p.add_argument("--max", dest="maximum", type=int, default=10, choices=range(1, 51)); p.set_defaults(func=cmd_inbox)
    p = commands.add_parser("search"); p.add_argument("query"); p.add_argument("--max", dest="maximum", type=int, default=10, choices=range(1, 51)); p.set_defaults(func=cmd_search)
    p = commands.add_parser("get"); p.add_argument("message_id"); p.add_argument("--max-chars", type=int, default=MAX_MESSAGE_CHARS, choices=range(1, MAX_MESSAGE_CHARS + 1)); p.set_defaults(func=cmd_get)
    p = commands.add_parser("otp"); p.add_argument("--query", default="is:unread newer_than:2d"); p.add_argument("--max", dest="maximum", type=int, default=10, choices=range(1, 51)); p.set_defaults(func=cmd_otp)
    p = commands.add_parser("send"); p.add_argument("--to", required=True); p.add_argument("--subject", required=True); p.add_argument("--body", required=True); p.set_defaults(func=cmd_send)
    args = parser.parse_args()
    args.func(args)


def run() -> None:
    try:
        main()
    except Exception as exc:
        # Keep API failures actionable without dumping request URLs or OAuth data.
        response = getattr(exc, "resp", None)
        status = getattr(response, "status", None)
        if exc.__class__.__name__ == "HttpError":
            error = "Gmail API request was rejected."
            if status == 403 and "accessNotConfigured" in str(exc):
                error = "Gmail API is disabled for this OAuth project. Enable Gmail API, wait briefly, then retry."
            print(json.dumps({"ok": False, "error": error, "http_status": status}), file=sys.stderr)
            raise SystemExit(1)
        raise


if __name__ == "__main__":
    run()
