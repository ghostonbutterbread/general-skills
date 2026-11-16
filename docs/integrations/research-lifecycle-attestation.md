# Research lifecycle attestation — integration dossier

- **Status:** blocked; no adapter installed or activated
- **Owner:** delegated Hermes integration worker; parent owns coordination/review
- **Owning branch:** `feat/disposable-research-worker`
- **Worktree:** `/home/ryushe/worktrees/general-research-worker-20261115`
- **Base:** `caf64af821f2628d3586b7c14b913f0ee6396681` (transport feature tip); its integration base is `20189521b6aab6997ebde5a353542af2e63848de`
- **Native candidate:** `/home/ryushe/worktrees/hermes-research-tool-confinement` at `12569d07656b8acda918df70c19d706042d37c7f` (read-only)
- **Target:** `beta`, subject to separate review and integration approval
- **Updated:** 2026-11-15
- **Prior transport record:** `docs/integrations/disposable-research-worker.md`

## Intent and decision

Connect `research_container` to exactly one host-lifecycle-owned forced-leaf child, authorize only from server-held identity and effective exact tool names, and revoke/clean up on all completion and cancellation paths. Do not trust model-supplied identity, put credentials in a container, or use prompt instructions as a boundary. Only new integration files were authorized; existing transport and the native candidate remain unchanged.

**Blocked, deliberately no resolver or launcher shipped.** The candidate has real exact-tool selection: `SubagentLifecycleService.launch` requires `force_leaf` with `exact_tools`, and its returned server-created handle records the child's effective names and role. `status()` returns the server-held handle even when the submitted role/names are modified. This is more capable than the older transport dossier's statement about the prior public API; it still does not provide a public, authenticated binding between the *currently executing tool invocation* and that lifecycle record.

Specific seams:

- `agent/subagent_lifecycle.py:319-335` constructs a handle without a child session ID or `force_leaf` field and submits the child before returning it. `:401-412` only resolves handles while the active parent session matches the handle's parent. In a child turn `bind_subagent_parent(self)` binds the child (`agent/turn_facade.py:144`), so the plugin context's ordinary `status(handle)` returns UNKNOWN rather than a usable parent-owned record. Role `leaf` alone does not separately attest the force-leaf flag.
- `agent/tool_executor.py:1743-1764` and `model_tools.py:851-874` pass ordinary `task_id` and `session_id` kwargs to the registry. The child runner commonly sets its task ID to the subagent ID (`tools/delegate_tool_child_run.py:878`), and `subagent_start` emits the child ID and session ID (`tools/delegate_tool.py:400-407`). Those are useful correlation data, but the public resolver receives no runtime-verified lifecycle capability/identity or public method to bind the current dispatch to the server-held record and its forced-leaf/effective-tool state. Registry dispatch itself accepts caller-provided kwargs; our direct-dispatch test demonstrates this host API property, **not** that an unprivileged model can forge those kwargs through its tool schema. We do not infer an exploitable bypass.
- `launch` submits before returning the handle, so a child can call the tool before a parent-side mapping created after `launch()` returns. A resolver that waits indefinitely for this mapping can deadlock if launch or setup fails. The existing default-deny handler remains in place.

## Required native prerequisite

Provide a documented plugin-safe, runtime-issued invocation attestation that identifies the current lifecycle-owned child and resolves to the server-held live record (not an ID from model arguments or an unverified plain kwarg), exposing verified effective **exact** names and whether `force_leaf` was applied. It must be propagated through sequential, concurrent, middleware and thread/context hops without letting unrelated calls borrow it. Provide an atomic pre-run binding/start gate, or equivalent race-safe host hook, so a task container can be bound before the first tool dispatch; revoke authorization before cleanup on terminal, cancel, failed launch, timeout, and unload. The adapter must retain uncertain cleanup receipts and respect transport retry semantics, not report removal solely because the mapping was removed. Another verified public API with equivalent guarantees would also satisfy this requirement; do not rely on private registry internals as a substitute.

## Offline evidence

`integration_tests/test_research_lifecycle_blocker.py` ran **4/4 passed**, using the real candidate `PluginContext`, registry, lifecycle service, and existing default-deny handler, with a fake child/builder/run function and a scheduler wrapper forcing the early-dispatch ordering. Cases: default deny for missing/spoofed IDs; parent-owned server snapshot versus UNKNOWN from child scope; plain registry kwargs are not independently authenticated; and child dispatch before `launch` returns is denied. These do **not** exercise real `AIAgent` creation, an actual model, a real container, host-tool confinement, or adapter cancellation. The wrapper only establishes a possible scheduling order, not a measured frequency.

Reproduce from this worktree with a fresh disposable scratch directory and an empty executable PATH; no inherited environment, credentials, Docker, or provider access:

```sh
d=$(mktemp -d /home/ryushe/.hermes/cache/scratch/research-attest-fixture.XXXXXX)
mkdir -p "$d/bin" "$d/home" "$d/hermes" "$d/config" "$d/cache" "$d/tmp"
env -i HOME="$d/home" HERMES_HOME="$d/hermes" HERMES_RUNTIME_DIR="$d/runtime" \
  XDG_CONFIG_HOME="$d/config" XDG_CACHE_HOME="$d/cache" TMPDIR="$d/tmp" PATH="$d/bin" \
  HERMES_NATIVE_CHECKOUT=/home/ryushe/worktrees/hermes-research-tool-confinement \
  PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -W error::ResourceWarning \
  integration_tests/test_research_lifecycle_blocker.py -v
# Remove only the task-created "$d" afterward.
```

This is an environment-variable/executable fence, not an OS network namespace. Fixtures do not make network calls. No real Docker, live target, model/provider inference, or withdrawn descendant probe was run; no previously blocked container was inspected or retried. No independent review yet.

## Deferred gates and resume

1. Once the native prerequisite exists, implement the smallest new integration adapter and run provider-free fixtures using the actual public API: parent, sibling and forged/absent identity denial; exact-tool and force-leaf mismatch denial; early-call race; cross-task isolation; terminal/failure/cancellation/unload revocation and fake-container cleanup, including cleanup uncertainty and retry. Verify actual native sequential/concurrent dispatch cannot reach normal host tools, not only tool schemas.
2. **Known product gap:** the existing transport uses `--network none`, so it cannot currently fetch public sources; source transfer/fetch policy and bounded untrusted parent handoff are not implemented. Network policy must be separately designed and reviewed; do not silently enable network.
3. No real subagent or end-to-end model run is verified. Such a run and live/real-container descendant behavior remain separately gated by explicit authorization; the withdrawn model/provider and detached-descendant probes must not be repeated by another route. Transport daemon uncertainty and the prior unresolved cleanup gate remain as recorded in the prior dossier.
4. Review the complete branch independently. No push, beta merge, runtime activation, global config change, or promotion is authorized. Parent reconciles Kanban. Resume at the native attestation contract; retain these blocker fixtures until positive integration tests supersede them.
