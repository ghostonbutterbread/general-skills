# Expected-mail polling cadence

- Owner: Hermes; task `t_2accea6b`.
- Branch/worktree: `docs/mail-polling` at `general-skills-mail-polling`; base `04fb99a1f447ba77fae37fe5adc263bbae962dc7` (`origin/beta`), target `beta` (not stable `master`).
- Intent: Ryu clarified the delivery-window behavior: wait about 10–15 seconds before first lookup, then check on an interval for up to five minutes. A bounded ~20–30-second polling cadence balances responsiveness and query volume; preserve two separate Spam checks while missing and the final deadline check.
- Contract: `mail` remains canonical for Composio provider reads. Track five minutes from send initiation, poll inbox after initial pause and periodically while missing, check Spam early and near deadline, and only call non-arrival after a successful final inbox/Spam check at or after deadline. Early arrival stops polling. Connection/query failures are not evidence of non-delivery.
- Neighbors: `openclaw-imports/gmail` routes to `mail`; `email-access-policy` owns test identities and delegates retrieval to `mail`. No competing delivery rule. No permission or transport change.
- Verification: `python3 -m unittest discover -s tests -q` passed 42 tests; `git diff --check` passed. Independent read-only review found no issues and reran 42 tests. Repository mail contract test asserts cadence and two Spam checks; no separate policy lint command. Integrated checks pending.
- Activation: merge to selected beta, push and verify remote, resolve configured runtime symlink and load current `mail` skill. No stable promotion.
- Next: test, review, commit, integrate into beta, retire this dossier on beta, verify runtime. Implementation commit pending.
