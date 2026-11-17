#!/usr/bin/env python3
"""Inspect local VPN manager state and an IPv4 route; no traffic is authorized."""
import argparse
import ipaddress
import json
import os
import re
import shutil
import subprocess


def run(*args):
    if shutil.which(args[0]) is None:
        # A non-executable PATH entry is a failure, not an absent command.
        found = any(os.path.lexists(os.path.join(p or os.curdir, args[0]))
                    for p in os.get_exec_path())
        return ('failed' if found else 'not-on-path'), None
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=5, check=False)
        if result.returncode == 0:
            return 'ok', result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired, UnicodeError):
        pass
    return 'failed', None


def inspect_host():
    """Read separate, non-atomic local snapshots; never infer protection."""
    commands = {
        'tailscale-selection': ('tailscale', 'get', 'exit-node'),
        'tailscale-status': ('tailscale', 'status', '--json'),
        'tailscale-prefs': ('tailscale', 'debug', 'prefs'),
        'mullvad-status': ('mullvad', 'status', '--json'),
        # ip route get is a local kernel lookup, not a packet or DNS query.
        'ipv4-route': ('ip', '-4', 'route', 'get', '1.1.1.1'),
    }
    results = {key: run(*args) for key, args in commands.items()}
    issues = [key + '-' + result for key, (result, _) in results.items() if result != 'ok']

    def object_result(key):
        result, text = results[key]
        if result != 'ok':
            return None
        try:
            value = json.loads(text or '')
            if not isinstance(value, dict):
                raise ValueError('expected object')
            return value
        except (ValueError, TypeError):
            issues.append(key + '-invalid')
            return None

    selected = 'unknown'
    selected_value = None
    result, text = results['tailscale-selection']
    if result == 'ok':
        if not text:
            selected = 'none'
        elif len(text) <= 253 and re.fullmatch(r'[A-Za-z0-9_.:-]+', text):
            selected, selected_value = 'selected', text
        else:
            issues.append('tailscale-selection-invalid')

    status = object_result('tailscale-status')
    effective, exit_id, matches = 'unknown', None, False
    if status is not None:
        if status.get('BackendState') != 'Running':
            issues.append('tailscale-status-not-running')
        else:
            node = status.get('ExitNodeStatus')
            if node is None:
                effective = 'none'
            elif (isinstance(node, dict) and isinstance(node.get('ID'), str)
                  and node['ID'] and type(node.get('Online')) is bool):
                exit_id = node['ID']
                effective = 'online' if node['Online'] else 'offline'
                if effective == 'offline':
                    issues.append('tailscale-exit-offline')
                aliases = {exit_id.lower()}
                peers = status.get('Peer')
                peers = peers.values() if isinstance(peers, dict) else ()
                for item in (node, *(p for p in peers if isinstance(p, dict) and p.get('ID') == exit_id)):
                    for key in ('HostName', 'DNSName'):
                        if isinstance(item.get(key), str):
                            aliases.add(item[key].lower().rstrip('.'))
                    for addr in item.get('TailscaleIPs', []) if isinstance(item.get('TailscaleIPs', []), list) else []:
                        try:
                            aliases.add(str(ipaddress.ip_interface(addr).ip))
                        except (ValueError, TypeError):
                            pass
                matches = selected == 'selected' and selected_value is not None and selected_value.lower().rstrip('.') in aliases
                if selected == 'selected' and not matches:
                    issues.append('tailscale-selection-mismatch')
            else:
                issues.append('tailscale-status-invalid')
    if (selected == 'none' and effective in ('online', 'offline')
            or selected == 'selected' and effective == 'none'):
        issues.append('tailscale-selection-mismatch')

    prefs = object_result('tailscale-prefs')
    route_all, saved_id = None, None
    if prefs is not None:
        if type(prefs.get('RouteAll')) is not bool or not isinstance(prefs.get('ExitNodeID'), str):
            issues.append('tailscale-prefs-invalid')
        else:
            route_all, saved_id = prefs['RouteAll'], prefs['ExitNodeID']
            # RouteAll is not an exit-selection flag; compare identity instead.
            if (effective in ('online', 'offline') and saved_id != exit_id
                    or selected == 'none' and effective == 'none' and saved_id):
                issues.append('tailscale-prefs-mismatch')

    m = object_result('mullvad-status')
    mullvad = m.get('state') if m else None
    if mullvad not in ('connected', 'disconnected'):
        mullvad = 'unknown'
        if m is not None:
            issues.append('mullvad-status-unknown')

    result, route = results['ipv4-route']
    devices = re.findall(r'(?:^|\s)dev\s+(\S+)', route or '')
    interface = devices[0] if len(devices) == 1 and re.match(r'^1\.1\.1\.1(?:\s|$)', route or '') else None
    if result == 'ok' and interface is None:
        issues.append('ipv4-route-invalid')
    if mullvad == 'connected' and (selected == 'selected' or effective in ('online', 'offline')):
        issues.append('manager-conflict')
    if interface and ((effective == 'online' and interface != 'tailscale0')
                      or (mullvad == 'connected' and selected == 'none' and interface != 'wg-mullvad')
                      or (effective == 'none' and interface == 'tailscale0')
                      or (mullvad == 'disconnected' and 'mullvad' in interface.lower())):
        issues.append('ipv4-route-conflict')
    manager = 'unknown'
    if not issues:
        if selected == 'selected' and matches and effective == 'online' and interface == 'tailscale0' and mullvad == 'disconnected':
            manager = 'tailscale'
        elif selected == effective == 'none' and mullvad == 'connected' and interface == 'wg-mullvad':
            manager = 'mullvad'
        elif selected == effective == 'none' and mullvad == 'disconnected' and interface and interface not in ('tailscale0', 'wg-mullvad'):
            manager = 'none'
    return {'manager': manager,
            'tailscale': {'selected': selected, 'selected_value': selected_value, 'effective': effective,
                          'effective_id': exit_id, 'saved_id': saved_id, 'route_all': route_all},
            'mullvad': {'state': mullvad}, 'route': {'interface': interface},
            'issues': issues, 'action': 'none', 'exhaustive': False,
            'guidance': 'Local non-atomic IPv4 snapshot only; not authorization for traffic or manager changes. Pause external traffic and follow the Mullvad skill.'}


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(inspect_host()))


if __name__ == '__main__':
    main()
