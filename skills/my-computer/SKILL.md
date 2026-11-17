---
name: my-computer
description: Use when the user refers to my computer or my PC.
---

# My Computer

Use when Ryushe's request refers to the device he is using, such as “my computer”
or “my PC”. An explicitly named device or address
takes precedence over the inferred current controller. “my notes” keeps its normal meaning:
the relevant notes store, not the current device merely because it says “my”.

## Named devices

When Ryushe explicitly names a machine, such as “Nebula”, use that name rather
than the inferred current device. On the machine performing the lookup, resolve
it with its existing hosts file and name-service configuration (for example,
`getent hosts nebula` on Linux). This may use `/etc/hosts` or DNS, including
Tailscale DNS; do not assume every name appears in the file. If a name does not
resolve or points to conflicting candidates, ask instead of guessing. A resolved
address does not establish the proxy port or authorize an unrelated operation.

## Current device

1. For Herdr, seek a fresh lookup of the current controller for the current Herdr pane
   each time the device matters. This per-pane interface was verified in an isolated Hoster trial
   with the candidate client and server and actual OMP; Ryushe confirmed actual use.
   It requires a compatible client and server, not merely this skill: stock older
   or unknown installations may not support it. In a managed Herdr pane (check
   `HERDR_ENV=1`), attempt `herdr pane controller --current --json` using the
   Herdr client on that machine's PATH, without an external verification receipt.
   Do not infer another pane's controller. If outside a managed pane or the client
   or method is unavailable, ask Ryushe; do not install, replace, restart, or
   upgrade a server or disturb existing sessions to make the lookup work.
2. Parse the response as a valid JSON object. The success JSON has an envelope with `result.type` equal to
   `pane_controller`, `result.status`, `result.source_ip`, and `result.reason`.
   Use the SSH source IP directly only when the command exits zero,
   there is no error envelope, `result.type` is `pane_controller`, `result.status`
   is `inferred`, and `result.source_ip` is a valid usable IP for the connection
   context, without maintaining a device table.
   The tested interface derives it from `SSH_CONNECTION` in the local Unix-socket peer's
   environment: it is an untrusted hint that can be spoofed, not an authenticated
   network peer. Call it **inferred**, not proof of who authored a message or which
   physical device it is. NAT, relays and changing connections can make an IP
   misleading or unreachable. An inferred address is not authorization to access a service.
3. If the lookup is unknown, ambiguous, unsupported, unavailable, fails, has a
   missing or malformed response or IP, an unexpected result type, or any
   non-inferred status, ask Ryushe for the device or IP rather than guessing.
   For tmux there is no verified source mechanism: ask instead. Do not read a
   pane process's inherited `SSH_CONNECTION` as the current controller; it may
   be stale. Do not substitute a host's own address, a remembered IP, or
   unqualified latest activity.

## Boundaries

- “my proxy” still means Ryushe's Caido source lane: load `ryushe-proxy` and
  `proxy-routing-policy`. Source history is read-only under those rules; active
  agent traffic uses its task-scoped MITM, with the existing exception only for
  an agent executing on Abommie. The current device does not redefine the known
  Ryushe proxy endpoint. If Ryushe specifically asks for a proxy on a named or
  inferred device, verify its location and port; ask if those are not established.
  An inferred IP does not itself establish a proxy endpoint.
- Do not modify `/etc/hosts` unless Ryushe explicitly requests a named host addition
  and the addition is safe and authorized. A source IP lookup alone never requires it.
