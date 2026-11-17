# Local egress manager inspection

Resolve the installed `script-manager` skill directory from the active runtime's
skill loader, then follow its `scripts/README.md` entry to this usage guide. Do
not assume the current working directory is the skills source checkout. The
helper is diagnostic only: it does not authorize traffic, IP rotation, or a VPN
manager switch.

For a Hermes runtime where `$HOME/.hermes/synced-skills/script-manager` exists
and is the active installation of this skill, this command works from any
working directory:

```sh
python3 "$HOME/.hermes/synced-skills/script-manager/scripts/egress_inspect.py"
```

For another runtime or installation, replace the placeholder with the actual
absolute directory resolved by that runtime's skill loader (do not guess a
checkout or lane):

```sh
python3 "<resolved-script-manager-skill-dir>/scripts/egress_inspect.py"
```

The command prints one JSON object to stdout and writes no state files. It
executes only `tailscale get exit-node`, `tailscale status --json`, `tailscale
debug prefs`, `mullvad status --json`, and `ip -4 route get 1.1.1.1`. The last
is a local kernel route lookup for a numeric destination, not a packet or DNS
query. Local CLI implementations may communicate with their local daemon or
kernel over sockets; no public probe is performed. Commands have five-second
individual timeouts. A zero exit status means the diagnostic ran, not that the
observations were complete or safe.

The JSON contains `tailscale.selected`, `effective` (`online`, `offline`,
`none`, or `unknown`), effective and saved IDs, `route_all`, Mullvad actual
`state` (`connected`, `disconnected`, or `unknown`), IPv4 route `interface`,
heuristic `manager`, `issues`, and `action` (`none`). A manager of `none`
means only that these two observed managers are not selected/connected; it does
not exclude another VPN, proxy, tunnel, or other network owner. `unknown` is
expected for unavailable CLI, unsupported output, timeout or conflicts.
`not-on-path` is a PATH diagnostic, not evidence of system-wide absence.
A connected tailnet is not an exit. `RouteAll: false` is not absence of an
exit. Interface names `tailscale0` and `wg-mullvad` are classifiers, not proof
of tunnel ownership. Other interfaces may be valid but are left unknown when
they do not match this narrow classifier.

These commands are sequential and non-atomic. Results do not establish public
IP, target availability, DNS or IPv6 path, proxy routing, ISP exposure, or a
kill switch, and do not authorize any traffic or manager switch. Follow the
Mullvad skill and investigate unknown or conflicting results; never infer
permission to refresh or switch a VPN from this diagnostic.

Tests use a sanitized combination observed on a host with an online Tailscale
exit, `RouteAll: false`, a disconnected Mullvad CLI with location metadata, and
an IPv4 route through `tailscale0`. The fixture is not a live-host verification.
