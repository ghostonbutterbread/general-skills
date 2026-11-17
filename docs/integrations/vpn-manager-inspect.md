# Local VPN manager inspection integration dossier

- **Status:** independently reviewed read-only slice; beta integration pending
- **Owner / branch:** delegated inspector task, `feat/vpn-manager-inspect`
- **Base / latest immutable pre-feature checkpoint:** `f17eaa16e90ddfc14bfb9de5f74065900c8e4a04`
- **Intended integration target:** `beta`
- **Implementation checkpoint:** `5dacff753e3924c19e4dc2bbe67c478284c1c247` on `feat/vpn-manager-inspect` contains the cwd correction, regression, and review evidence; this handoff-only update follows it. Resume with independent correction recheck at the branch tip.
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
- Independent reviewer found the usage command was relative to the General Skills
  source root, so it failed from a BBH agent's unrelated working directory.
  The feature now documents resolving the active runtime's installed skill,
  with a conditional Hermes `$HOME/.hermes/synced-skills` example and a portable
  resolved-directory placeholder. It explicitly disclaims traffic and rotation
  authorization. Correction needs independent reviewer recheck.
- Cwd regression RED: the documented command, extracted through the installed
  skill -> index -> usage discovery path, failed with `can't open file` under a
  synthetic BBH cwd. GREEN: the same discovery and shell command passes using a
  scratch HOME symlink to this feature's provider, fake PATH commands, and an
  inherited seccomp socket/socketpair/connect/io_uring ban. The test checks the
  JSON, `action=none`, and exactly the five fake calls; it is not live runtime
  activation or evidence of real VPN routing.
- Exact test launcher for both runs: `/usr/bin/python3`, invoked in a process
  with `env -i HOME=/home/ryushe/.hermes/profiles/bugfix/cache/scratch/egress-offline XDG_CONFIG_HOME=/home/ryushe/.hermes/profiles/bugfix/cache/scratch/egress-offline/config XDG_CACHE_HOME=/home/ryushe/.hermes/profiles/bugfix/cache/scratch/egress-offline/cache XDG_STATE_HOME=/home/ryushe/.hermes/profiles/bugfix/cache/scratch/egress-offline/state TMPDIR=/home/ryushe/.hermes/profiles/bugfix/cache/scratch/egress-offline PATH=/usr/bin:/bin PYTHONNOUSERSITE=1`, followed by `/usr/bin/python3 /home/ryushe/.hermes/profiles/bugfix/cache/scratch/egress-offline/launch.py -B -m unittest discover -s tests -p test_egress_inspect.py -k documented -v` for RED, and the same command without `-k documented` for GREEN (7 passed). The launcher reestablishes scratch-only environment, checks seccomp setup and self-tests socket denial before exec. Same launcher and environment with `-p test_script_manager_policy.py -v` instead: 11 passed.
- Independent review of the complete feature found a cwd-dependent usage command. After correction, independent re-review accepted the bounded checkpoint: 7 provider tests and 1 BBH routing test passed under network denial. The wider refresh feature remains outside this release.
- Fresh beta comparison by parent: `origin/beta` and the clean selected local beta both at `f17eaa16e90ddfc14bfb9de5f74065900c8e4a04` after fetch.

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
- **Review and integration:** bounded feature review completed. Re-fetch and
  verify the exact target tip before integration; preserve unrelated work and
  remove this branch-local dossier from the beta merge. Runtime activation and
  stable promotion remain separate decisions.

## Handoff and gates

- Resume on the owning branch at its committed tip; rerun the fenced inspection
  and script-policy tests after edits and independently review the diff.
- Intended target is `beta`; remove this temporary dossier during accepted
  integration. No push, merge, activation or service change is authorized here.
- Runtime use, live-host evidence, beta merge, and stable promotion are separate
  decisions; none is claimed by this feature commit.
