# Actionable agent-outreach handoffs

- **Status / owner:** in progress / Hermes, General Skills task `t_88c66523`.
- **Base:** beta `cd5f8d05a6e67573a2b0567d404b0cb680af9a22`; feature `feat/actionable-agent-outreach`; target beta.
- **Intent:** when a human is needed, proactively notify and include the specific action and actual safe user-reachable handoff URL, identity/role context, status, relevant expiry, fallback, and monitored completion channel. Never send credentials or bearer links. State missing/unsafe routes and preserve existing workflow safety.
- **Evidence:** documentation regression was red before updating the skill, then green. Sender payload test asserts a safe handoff URL is preserved. Initial 105-test full suite had an unrelated research timing cutoff fail at 3.213 seconds vs 3.2; focused rerun and full rerun passed (one skip), tracked as `PC-20261117-001850-7c044656`. Independent provider re-review accepted corrections in `d5e9c11cfc56af99a85a4df7e7d81a532bbd0649`; caller routing is separately required before overall task completion.
- **Checkpoint:** reviewed provider implementation `d5e9c11cfc56af99a85a4df7e7d81a532bbd0649`; current tip includes the subsequent dossier-only receipt.
- **Boundary:** general skill instructions alone do not enforce runtime triggers; audit existing handoff/blocker owner routes separately. No live notification is necessary for documentation changes. Shared credentials are not touched.
- **Next:** reconcile caller-route audit; validate policy/security and independently review exact change; integrate/push beta, then verify actual local and Hoster projections and a fresh resolver. Do not put this dossier on beta.
