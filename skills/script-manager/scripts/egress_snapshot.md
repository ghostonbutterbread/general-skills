# Host-direct IPv4 incident snapshot

An agent can record promptly when it suspects an IP-related block, continue its
investigation, then check or request a refresh using the **same opaque run-owned
incident key**. Classification, program rules, rate/ban stops and review remain
the caller's responsibility. Keep the key in the agent's run/incident context;
do not use an IP, secret, or target identifier as the key. From any working directory:

```sh
python3 "$HOME/.hermes/synced-skills/script-manager/scripts/egress_snapshot.py" record "$INCIDENT_KEY"
# Continue independent work; no lease is held.
python3 "$HOME/.hermes/synced-skills/script-manager/scripts/egress_snapshot.py" check "$INCIDENT_KEY"
python3 "$HOME/.hermes/synced-skills/script-manager/scripts/egress_snapshot.py" refresh "$INCIDENT_KEY"
```

For another installation, use the skill directory resolved by that runtime.
`record` first durably stores minimal incident metadata keyed by a hash, then
tries to capture the baseline. It returns `captured` on success, or
`incident_recorded_baseline_unknown` (exit 1, with an actionable reason) when
the incident was saved but capture failed. If the record itself cannot be saved,
the result is `unknown`; no durability is claimed. A later `check`, `refresh`,
`record`, or `capture` cannot turn a new sample into that incident's missing
original baseline: use a new incident key for a new incident. `capture` retains
its original behavior and creates no incident on failed observation; `check` is
the `compare` alias. Check returns `same`, `different`, or `unknown`.
Refresh rechecks under a shared rotation lock and returns `already_refreshed` if
the IP changed. If unchanged, it considers one switch to a distinct, live-listed
same-city West Coast exit of the current manager. It rechecks the manager, route,
baseline, listing and candidate before persisting an uncertainty latch and
invoking the manager. Unknown or conflicting evidence means no switch. Results
include `path: host-direct`; `unknown` exits 1. A verified success reports
`switch`, and an attempted but uncertain switch reports `switch_uncertain`.
The caller must decide whether rotation is appropriate under program rules,
active workloads, and the host's recovery arrangements. **These point-in-time
checks do not prevent ISP fallback or guarantee recovery access**; switching may
interrupt connectivity or remote access. Follow the Mullvad policy, including
stopping ordinary traffic if the route cannot be verified; do not treat this
helper as a kill switch or an automatic recovery mechanism.
After a successful manager command the backend retries at most three **complete**
observations, within a 15-second monotonic observation budget (0.2 seconds
between attempts), while retaining the lock and latch. It never repeats the
switch. Local manager, candidate, city and route checks must pass before each
probe and remain consistent afterward; a stale IP alone is not success. The
budget limits child command timeouts and probe reads; process creation, kernel
scheduling, cleanup and filesystem operations are not hard real-time bounded.
Uncertain receipts add sanitized `stage`, `error_code`, and `attempts` fields:
`manager_command/command_failed`, `local_verification/observation_invalid`,
`host_probe/probe_failed`, `stale_ip/address_unchanged`, or
`latch_storage/storage_failed`; `unexpected_error` can accompany an observation
stage. The stage is the last failed attempt, not proof of the original cause;
zero attempts means the manager command did not complete successfully. No raw
IPs, provider output, or exception text are included. A changed IP alone does
not establish geographic suitability. Duplicate record
never overwrites: check the existing baseline or choose a new incident key. A
missing baseline is `unknown` and sends no probe. A baseline captured *after*
another switch cannot detect that earlier switch and can cause another rotation
on refresh; record at incident detection, not after waiting.

This approved host-direct diagnostic is the narrow exception to task MITM
routing; **all active target traffic stays through the task MITM**. A valid
record or check sends a bounded DNS-free HTTPS request directly to the fixed
Cloudflare `https://1.1.1.1/cdn-cgi/trace` over the locally verified tunnel.
It does not request the target, use a proxy, rotate an exit, or turn off TLS
verification. Curl's configuration, proxy, and custom CA environment overrides
are excluded. The helper uses the canonical local `egress_inspect.py` before
and after, rejects unknown/conflicting manager or route states, and compares
selected Tailscale identity or connected Mullvad status and the exact route.
Standalone Mullvad must expose relay hostname or endpoint address in status.
Unsupported manager/status shapes fail closed. Checks are non-atomic snapshots,
not a VPN kill switch: a transient routing change between checks may go unseen.

The IP is stored **in plaintext**, not printed, in an owner-owned 0700
`$XDG_STATE_HOME/host-egress-snapshot` directory (default `~/.local/state`),
in owner-owned 0600 files named by the SHA-256 of the key. Filenames are not a
confidentiality mechanism: low-entropy keys and IPs can be enumerated. The
script validates file/directory permissions, refuses symlinks in any state
path component or at file boundaries, and does not overwrite a baseline. If the
state path contains a symlink, set `XDG_STATE_HOME` to an absolute path without
symlink components. A symlinked working directory alone is supported. Path
components must remain stable while the script runs; concurrent replacement by
uncooperative processes is not protected. It writes incident
metadata and baselines to private temporary files, fsyncs and publishes them
without replacing an existing path; interrupted temporary files may require
private-state cleanup. Before using an existing valid baseline, the script syncs
the file and its directory under the state lock. Thus a baseline left by an
uncertain publication can be used only after that barrier succeeds; a failed
barrier returns `unknown` without probing. Each state-directory acquisition also
syncs the ancestor directory entries, including existing ones. This requires
permission to open and sync those ancestor directories; failure is `unknown`.
It never changes permissions on pre-existing files.
Baselines and their
lock remain XDG-root-specific. Refresh additionally takes a rotation lock and
checks a persistent uncertainty latch in `<passwd-home>/.host-egress-rotation`,
independent of `HOME` and XDG overrides. This coordinates cooperating processes
of the **same UID with the same passwd home and filesystem view**, not different
users, containers with distinct mounts, or other VPN tools. Do not delete or
replace the lock. After a failed/interrupted switch the latch blocks all refreshes;
an operator must first establish that all switch processes/daemon actions have
finished and independently recover and verify the protected route before manual
removal. A verified-success path unlinks the latch under lock after the CLI exits
and identity, route, city and changed-IP checks pass, then fsyncs the directory;
a crash may conservatively retain a latch. Storage that does not honor fsync or
flock is unsupported. Protect backups and delete old private baselines under your normal
retention policy. A partial/corrupt file is preserved and returns `unknown`;
use a new key rather than guessing its value.

A changed host IP is not proof that the proxy's source changed or that a target
is unblocked, and it is never permission to evade a 429, WAF, program rule,
operator review, or user instruction. No claim is made about DNS, IPv6, proxy
traffic, target reachability, or fail-closed protection. If the local checks,
TLS, or public response fail, pause and inspect; never fall back to ISP egress.

Offline regression suite (Linux, libseccomp, private scratch):

```sh
TMPDIR="<private-scratch>" /usr/bin/python3 tests/egress_offline_runner.py
```

The fixture runner denies socket, socketpair and connect in all descendants;
tests execute the production admission logic with fake manager commands and fake
curl, redirecting the passwd home to private test state. They do not prove live
tunnel routing, real TLS, recovery access, or the standalone Mullvad JSON shape.
The manager command itself has no timeout: interrupting it could leave a switch
in progress, so the durable latch remains until verified operator recovery.
