"""Pure selection of distinct, live-listed Tailscale Mullvad exits.

Call select_candidates(status, live_entries, current_id=..., requirements=...).
status is a decoded ``tailscale status --json`` object. live_entries is a
separately obtained list of {"hostname": ..., "city": ..., "ip": ...} records parsed
from the exact live exit-node listing; city must be the full observed
"City, ST" label. Each requirements item is a nonempty set of exact state
codes (WA, OR, CA) and/or exact full city labels: alternatives within one item
are OR, and all items are AND. No requirements means the default WA/OR/CA
policy applies alone. No location aliases are inferred. The caller owns data
freshness, parsing, coordination, revalidation and any VPN operation.

Result.candidates is a deterministic tuple of dicts (id, hostname, city,
state); Result.reason is None on success or a human-readable blocking reason.
This function makes no I/O and does not claim the selected route is safe.
"""
from collections import namedtuple
import ipaddress
import re

Result = namedtuple('Result', 'candidates reason')
_STATES = frozenset(('WA', 'OR', 'CA'))
_HOST = re.compile(r'us-[a-z0-9]+-wg-[0-9]+\Z')
_CITY = re.compile(r'([^,]+), (WA|OR|CA)\Z')


def _location(value):
    if not isinstance(value, str):
        return None
    match = _CITY.fullmatch(value)
    if not match or match.group(1) != match.group(1).strip() or not match.group(1).strip():
        return None
    return match.group(2)


def select_candidates(status, live_entries, *, current_id, requirements=(), include_current=False):
    """Return eligible candidates or a blocking reason; never change a VPN."""
    if not isinstance(current_id, str) or not current_id.strip() or current_id != current_id.strip():
        return Result((), 'current stable node ID is missing or invalid')
    if not isinstance(status, dict) or not isinstance(status.get('Peer'), dict):
        return Result((), 'Tailscale peer status is missing or invalid')
    if not isinstance(live_entries, (list, tuple)):
        return Result((), 'live exit-node listing is missing or invalid')
    if not isinstance(requirements, (list, tuple)):
        return Result((), 'region requirements are invalid')
    for group in requirements:
        if not isinstance(group, (list, tuple, set, frozenset)) or not group:
            return Result((), 'region requirements are missing or invalid')
        if any(not isinstance(item, str) or (item not in _STATES and not _location(item)) for item in group):
            return Result((), 'region requirements contain unsupported or ambiguous geography')

    peers = [p for p in status['Peer'].values() if isinstance(p, dict)]
    current = [p for p in peers if p.get('ID') == current_id]
    if not current:
        return Result((), 'current stable node ID is not in peer status')
    if any(p != current[0] for p in current):
        return Result((), 'current stable node ID is ambiguous in peer status')
    # Colliding identities cannot safely establish a distinct node. Exact
    # duplicate entries are harmless, divergent entries poison both identities.
    by_id, by_host, by_ip = {}, {}, {}
    for p in peers:
        ident, host = p.get('ID'), p.get('HostName')
        if isinstance(ident, str) and ident:
            by_id.setdefault(ident, []).append(p)
        if isinstance(host, str) and host:
            by_host.setdefault(host, []).append(p)
        addresses = p.get('TailscaleIPs')
        if isinstance(addresses, list):
            for address in addresses:
                try:
                    value = str(ipaddress.ip_interface(address).ip)
                except (ValueError, TypeError):
                    continue
                by_ip.setdefault(value, []).append(p)
    listing, listed_ips = {}, {}
    for entry in live_entries:
        if isinstance(entry, dict):
            host, city, address = entry.get('hostname'), entry.get('city'), entry.get('ip')
            if isinstance(host, str) and isinstance(city, str):
                try:
                    address = str(ipaddress.ip_address(address)) if isinstance(address, str) else None
                except ValueError:
                    address = None
                listing.setdefault(host, set()).add((city, address))
                listed_ips.setdefault(address, set()).add(host)

    candidates = {}
    for p in peers:
        ident, host = p.get('ID'), p.get('HostName')
        if (not isinstance(ident, str) or not ident or ident != ident.strip()
                or (ident == current_id and not include_current)
                or not isinstance(host, str) or not _HOST.fullmatch(host)):
            continue
        if any(other != p for other in by_id[ident]) or any(other != p for other in by_host[host]):
            continue
        if (p.get('DNSName') != host + '.mullvad.ts.net.' or p.get('Online') is not True
                or p.get('ExitNodeOption') is not True
                or not isinstance(p.get('Tags'), list) or 'tag:mullvad-exit-node' not in p['Tags']):
            continue
        location = p.get('Location')
        if not isinstance(location, dict) or location.get('Country') != 'USA' or location.get('CountryCode') != 'US':
            continue
        city = location.get('City')
        state = _location(city)
        rows = listing.get(host, set())
        if not state or len(rows) != 1:
            continue
        row_city, address = next(iter(rows))
        if (row_city != city or address is None or listed_ips[address] != {host}
                or not by_ip.get(address) or any(other != p for other in by_ip[address])):
            continue
        if any(state not in group and city not in group for group in requirements):
            continue
        candidates[ident] = {'id': ident, 'hostname': host, 'city': city, 'state': state}
    if not candidates:
        return Result((), 'no distinct live-listed eligible exit satisfies geography and identity requirements')
    return Result(tuple(candidates[key] for key in sorted(candidates)), None)
