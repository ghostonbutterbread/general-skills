"""Same-manager selection and switching; source adapted from 89c27ec.

Caller owns the lock, durable intent and local route observations.
These local non-atomic observations do not establish fail-closed protection.
"""
import ipaddress
import json
import re
import subprocess

from egress_candidates import select_candidates
import egress_inspect


class Invalid(Exception):
    pass


def read(*args):
    result, text = egress_inspect.run(*args)
    if result != 'ok':
        raise Invalid('local manager listing unavailable')
    return text


def tailscale_exits(text):
    entries = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or re.match(r'^IP\s+HOSTNAME\s+COUNTRY\s+CITY\b', line, re.I):
            continue
        m = re.fullmatch(r'(\S+)\s+([a-z0-9-]+)\.mullvad\.ts\.net\s+USA\s+(.+?)\s+(selected|-)', line)
        if not m:
            raise Invalid('unrecognized Tailscale exit list')
        address, hostname, city, selected = m.groups()
        try:
            address = str(ipaddress.ip_address(address))
        except ValueError as exc:
            raise Invalid('invalid exit address') from exc
        entries.append(dict(hostname=hostname, city=city, ip=address, selected=selected == 'selected'))
    return entries


def tailscale_selection(observed):
    try:
        status = json.loads(read('tailscale', 'status', '--json'))
        ident = observed[1]['effective_id']
        if (status['BackendState'] != 'Running' or status['ExitNodeStatus']['ID'] != ident
                or status['ExitNodeStatus']['Online'] is not True
                or not egress_inspect.exit_identity_consistent(status)):
            raise Invalid('effective Tailscale exit changed')
        entries = tailscale_exits(read('tailscale', 'exit-node', 'list', '--filter=USA'))
        if not isinstance(status['Peer'], dict) or not all(isinstance(p, dict) for p in status['Peer'].values()):
            raise Invalid('invalid Tailscale peer state')
        current = select_candidates(status, entries, current_id=ident, include_current=True)
        selected = [e for e in entries if e['selected']]
        choices = [c for c in current.candidates if c['id'] == ident]
        peers = [p for p in status['Peer'].values() if p.get('ID') == ident]
        if len(choices) != 1 or len(selected) != 1 or len(peers) != 1:
            raise Invalid('current exit not uniquely listed')
        old = choices[0]
        addresses = {str(ipaddress.ip_interface(v).ip) for v in peers[0]['TailscaleIPs']}
        if selected[0]['hostname'] != old['hostname'] or selected[0]['city'] != old['city'] or selected[0]['ip'] not in addresses:
            raise Invalid('selected exit listing disagrees')
        alternatives = select_candidates(status, entries, current_id=ident, requirements=[{old['city']}])
        eligible = [candidate for candidate in alternatives.candidates
                    if egress_inspect.exit_identity_consistent({**status, 'ExitNodeStatus':
                                                              {'ID': candidate['id'], 'Online': True}})]
        if not eligible:
            raise Invalid('no distinct live-listed same-city exit')
        return old, eligible[0]
    except (KeyError, TypeError, ValueError) as exc:
        raise Invalid('invalid Tailscale exit state') from exc


def standalone_relays(text):
    rows, seen = [], set()
    country = city = code = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if not line.startswith('\t'):
            m = re.fullmatch(r'(.+) \(([a-z]{2})\)', line)
            if not m:
                raise Invalid('unrecognized relay country')
            country, city, code = m.group(2), None, None
        elif line.startswith('\t\t'):
            m = re.fullmatch(r'\t\t([a-z0-9-]+) \([^\n()]+\) - hosted by .+ \((?:Mullvad-owned|rented)\)', line)
            if not m or not country or not city or not code:
                raise Invalid('unrecognized relay entry')
            hostname = m.group(1)
            if hostname in seen or not hostname.startswith(country + '-' + code + '-'):
                raise Invalid('ambiguous relay identity')
            seen.add(hostname)
            rows.append(dict(country=country, city=city, code=code, hostname=hostname))
        else:
            m = re.fullmatch(r'\t(.+) \(([a-z0-9]+)\) @ .+', line)
            if not m or not country:
                raise Invalid('unrecognized relay city')
            city, code = m.groups()
    if not rows:
        raise Invalid('empty relay listing')
    return rows


def standalone_selection(observed, *, target=None):
    try:
        location = observed[4]['details']['location']
        if (observed[4]['state'] != 'connected' or location['country'] != 'USA'
                or location['entry_hostname'] is not None or location['obfuscator_hostname'] is not None):
            raise Invalid('unsupported connected relay')
        rows = standalone_relays(read('mullvad', 'relay', 'list'))
        matches = [r for r in rows if r['hostname'] == location['hostname'] and r['country'] == 'us'
                   and r['city'] == location['city'] and re.fullmatch(r'[^,]+, (?:WA|OR|CA)', r['city'])]
        if len(matches) != 1:
            raise Invalid('connected relay not uniquely listed')
        old = matches[0]
        alternatives = sorted((r for r in rows if r['country'] == 'us' and r['city'] == old['city']
                               and r['hostname'] != old['hostname']), key=lambda r: r['hostname'])
        if target is not None:
            if old != target:
                raise Invalid('connected relay differs from target')
            return old, None
        if not alternatives:
            raise Invalid('no distinct live-listed same-city relay')
        return old, alternatives[0]
    except (KeyError, TypeError) as exc:
        raise Invalid('unsupported standalone relay state') from exc


def selection(observed):
    return tailscale_selection(observed) if observed[0] == 'tailscale' else standalone_selection(observed)


def switch(manager, candidate):
    # No timeout or kill: a manager may continue applying a request. If this
    # process dies, the pre-existing durable intent blocks later rotations.
    commands = ([['tailscale', 'set', '--exit-node=' + candidate['hostname'] + '.mullvad.ts.net']]
                if manager == 'tailscale' else
                [['mullvad', 'relay', 'set', 'location', candidate['country'], candidate['code'], candidate['hostname']],
                 ['mullvad', 'reconnect', '--wait']])
    for command in commands:
        if subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False).returncode:
            raise Invalid('manager switch failed; outcome uncertain')


def verify(observed, candidate):
    if observed[0] == 'tailscale':
        # Reuse selection validation even if no further alternative remains.
        status = json.loads(read('tailscale', 'status', '--json'))
        node = status.get('ExitNodeStatus') if isinstance(status, dict) else None
        if (not isinstance(node, dict) or status.get('BackendState') != 'Running'
                or node.get('ID') != candidate['id'] or node.get('Online') is not True
                or not egress_inspect.exit_identity_consistent(status)):
            raise Invalid('post-switch effective exit identity mismatch')
        if not isinstance(status.get('Peer'), dict) or not all(isinstance(p, dict) for p in status['Peer'].values()):
            raise Invalid('invalid Tailscale peer state')
        entries = tailscale_exits(read('tailscale', 'exit-node', 'list', '--filter=USA'))
        selected = [e for e in entries if e['selected']]
        result = select_candidates(status, entries, current_id=candidate['id'], include_current=True,
                                   requirements=[{candidate['city']}])
        peers = [p for p in status['Peer'].values() if p.get('ID') == candidate['id']]
        if (observed[1]['effective_id'] != candidate['id'] or candidate not in result.candidates
                or len(selected) != 1 or len(peers) != 1
                or selected[0]['hostname'] != candidate['hostname']
                or selected[0]['city'] != candidate['city']
                or selected[0]['ip'] not in {str(ipaddress.ip_interface(v).ip) for v in peers[0]['TailscaleIPs']}):
            raise Invalid('post-switch exit identity or location mismatch')
    else:
        standalone_selection(observed, target=candidate)
