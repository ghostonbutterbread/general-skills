# Local VPN manager inspection integration dossier

- **Status:** feature; independent review pending
- **Owner / branch:** delegated inspector task, `feat/vpn-manager-inspect`
- **Base / latest immutable pre-feature checkpoint:** `f17eaa16e90ddfc14bfb9de5f74065900c8e4a04`
- **Intended integration target:** `beta`
- **Implementation:** the commit containing this dossier on the owning branch; exact tip is supplied in the handoff.
- **Inspiration:** `feat/shared-egress-recovery` at `9f4705b`, notably `egress_coordinator.py`'s inspection and its tests; that worktree is not modified.

## Intent and contract

Deliver a separately usable, read-only local diagnostic before the wider IP
refresh work is complete. The script gathers Tailscale selected, saved, and
effective exit state, Mullvad actual state and a numeric IPv4 kernel route,
with conservative manager inference and explanatory issues. No DNS, HTTP,
public packet, state file, preference, route or VPN action is initiated by the
script. Normal real CLI implementations may use local daemon/kernel sockets.
Results are non-atomic, incomplete, and never authorize traffic, IP refresh or
manager changes. `RouteAll: false` is not treated as no exit; `not-on-path` is
not system-wide absence; interface names are only heuristics.

## Evidence

- RED: isolated `unittest` CLI fixture failed because the new script did not
  exist. Green: all six inspection tests pass, including cases adapted from the
  sibling branch, the observed RouteAll-false combination, malformed data,
  conflicts, command failure, timeout, and PATH absence. A later invalid-route
  regression failed before the route destination check and passed after it.
- `/usr/bin/python3` under an inherited libseccomp socket, socketpair, connect
  and io_uring-setup denial, with private HOME/XDG/TMPDIR before imports;
  `unittest discover -s tests -p test_egress_inspect.py -v`: 6 passed.
- Same fence, private copied pytest 9.0.3 dependencies, plugin autoload off:
  `pytest -q -p no:cacheprovider --ignore=tests/test_research_engine.py tests`:
  90 passed, 1 skipped, 28 subtests passed. The excluded unrelated research
  engine suite needs Unix sockets; the socket ban was not weakened.
- `strace -f -e trace=%file,%network` on the observed fixture with non-writing
  fake commands: no writable file opens or checked mutation syscalls; the only
  socket call was the fence's intentionally denied self-test. No production
  script/fixture child socket call occurred in that trace. This is a fixture
  receipt, not proof about third-party CLI behavior.
- Parent independently ran the actual CLI on this host: `manager=tailscale`, selected exit online, saved/effective IDs matching, `RouteAll=false`, standalone Mullvad disconnected, IPv4 route interface `tailscale0`, no reported issues, and `action=none`. This was a read-only local snapshot; no DNS/public probe or VPN mutation occurred. It does not prove public egress, DNS, IPv6, kill-switch behavior or readiness for rotation.
- Parent independently ran `/usr/bin/python3 /home/ryushe/.hermes/profiles/bugfix/cache/scratch/egress-offline/launch.py -m unittest discover -s tests -p test_egress_inspect.py -v`: 6 passed with inherited network denial.
- Independent review of this complete feature diff and test evidence is pending.

## Blockers and deferred work

- **Real-host read-only inspection:** completed on the parent host as recorded
  above. Real CLI behavior on other hosts, including a connected standalone
  Mullvad tunnel, remains unverified; recheck locally before relying on a
  different host. No public probes or state changes are implied.
- **Wider coordinated refresh:** incomplete and deliberately excluded. No IP
  sample, lock, rotation, recovery, target unblocking, DNS/IPv6 verification,
  kill switch, or protected-path backend is supplied here. Before integrating
  sibling `feat/shared-egress-recovery`, reconcile its `inspect_host()` with this
  script into one canonical inspector, retaining the conservative PATH/unknown,
  preference, identity, failure, CLI and route regressions. Do not permanently
  maintain two conflicting implementations. Follow that branch's independent
  protection and review gates; this diagnostic cannot clear them.
- **Review and integration:** obtain independent complete-diff review; the
  parent owns review, any beta reconciliation and promotion. No fetch was done
  during this task because live network was prohibited; the supplied fetched
  `origin/beta` base was used. Refresh upstream only when network is permitted.

## Handoff and gates

- Resume on the owning branch at its committed tip; rerun the fenced inspection
  and script-policy tests after edits and independently review the diff.
- Intended target is `beta`; remove this temporary dossier during accepted
  integration. No push, merge, activation or service change is authorized here.
- Runtime use, live-host evidence, beta merge, and stable promotion are separate
  decisions; none is claimed by this feature commit.
