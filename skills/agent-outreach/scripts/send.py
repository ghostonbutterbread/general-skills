#!/usr/bin/env python3
"""Send a concise, one-way agent notification to a configured Discord webhook."""
from __future__ import annotations

import argparse
import http.client
import json
import os
from pathlib import Path
import re
import sys
import tomllib
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def open_webhook(request: urllib.request.Request, timeout: float):
    return urllib.request.build_opener(NoRedirect()).open(request, timeout=timeout)


def config_path() -> Path:
    override = os.environ.get('GENERAL_SKILLS_CONFIG')
    if override:
        return Path(override).expanduser()
    return Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'general-skills' / 'config.toml'


def webhook_for(destination: str) -> str:
    path = config_path()
    try:
        config = tomllib.loads(path.read_text(encoding='utf-8'))
        secret_path = config['agent_outreach']['destinations'][destination]['webhook_file']
    except (OSError, UnicodeError, tomllib.TOMLDecodeError, KeyError, TypeError) as exc:
        raise ValueError('Cannot load the selected destination from General Skills config; configure its webhook_file.') from exc
    if not isinstance(secret_path, str) or not secret_path:
        raise ValueError('webhook_file must be a nonempty path.')
    secret = Path(os.path.expandvars(secret_path)).expanduser()
    try:
        if not hasattr(os, 'getuid'):
            raise ValueError('This sender requires a POSIX host to verify secret-file ownership and permissions.')
        info = secret.stat()
        if info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('Webhook secret file must be owned by the current user and inaccessible to group and others (chmod 600).')
        url = secret.read_text(encoding='utf-8').strip()
    except (OSError, UnicodeError) as exc:
        raise ValueError('Cannot read webhook secret file; check the configured path and permissions.') from exc
    if not re.fullmatch(r'https://(?:discord\.com|discordapp\.com)/api/webhooks/[0-9]+/[A-Za-z0-9._-]+', url):
        raise ValueError('Webhook secret file must contain a Discord HTTPS webhook URL only.')
    return url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', default='default')
    parser.add_argument('--kind', choices=['handoff', 'safety', 'notice'], required=True)
    parser.add_argument('--agent', required=True)
    parser.add_argument('--run', required=True)
    parser.add_argument('--summary', required=True)
    parser.add_argument('--action', required=True)
    parser.add_argument('--status', required=True)
    parser.add_argument('--link', help='Optional safe human handoff URL; never include credentials or session tokens')
    args = parser.parse_args(argv)
    heading = {'handoff': '🔐 **Handoff needed**', 'safety': '🚨 **Safety attention**', 'notice': '📣 **Agent notice**'}[args.kind]
    fields = [heading, '', f'**Agent:** {args.agent} · `{args.run}`', f'**What happened:** {args.summary}', f'**Your action:** {args.action}', f'**Status:** {args.status}']
    if args.link:
        fields.append(f'**Link:** {args.link}')
    content = '\n'.join(fields)
    if len(content) > 2000:
        print('Notification exceeds Discord’s 2000-character limit; shorten it and try again.', file=sys.stderr)
        return 1
    try:
        url = webhook_for(args.destination)
    except ValueError as exc:
        print(f'Notification not sent: {exc}', file=sys.stderr)
        return 1
    payload = json.dumps({'content': content, 'allowed_mentions': {'parse': []}}).encode('utf-8')
    try:
        request = urllib.request.Request(url + '?wait=true', data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        with open_webhook(request, timeout=10) as response:
            status = response.status
            confirmation = json.loads(response.read())
        if status != 200 or not isinstance(confirmation, dict) or not isinstance(confirmation.get('id'), str) or not confirmation['id'].isdigit():
            raise ValueError('Unconfirmed response')
    except urllib.error.HTTPError as exc:
        status = exc.code
        exc.close()
        if status == 408 or status >= 500:
            print(f'Notification delivery uncertain: Discord returned HTTP {status}. Check before retrying to avoid duplicates.', file=sys.stderr)
        else:
            print(f'Notification delivery failed: Discord returned HTTP {status}; check the destination or retry later. No automatic retry was made.', file=sys.stderr)
        return 1
    except (OSError, urllib.error.URLError, http.client.HTTPException, ValueError, UnicodeError):
        print('Notification delivery uncertain: network or response error. Check before retrying to avoid duplicates.', file=sys.stderr)
        return 1
    print('Notification accepted by Discord; this does not confirm a human saw or approved it.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
