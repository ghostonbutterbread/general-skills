# Expected-mail delivery window

- Owner: Hermes; task `t_b188866c`.
- Branch/worktree: `docs/mail-delivery-window` at `general-skills-mail-delivery`.
- Fetched base: `cc1e19cead81cc93d5804da41e96360708a0598d` (`origin/beta`); target: `beta` (not `master`).
- Intent: Agents prematurely report missing Gmail/Composio verification mail after one inbox/Spam check. Ryu requested about five minutes from send and two Spam checks before non-arrival.
- Contract: Canonical `mail` guidance applies to expected incoming messages on the authorized connection; narrow inbox checks continue within the window, Spam is checked separately early and near the end while missing, and non-arrival requires the elapsed window plus final inbox/Spam check. Success can continue immediately; connection/query failures are not delivery failures. No Gmail transport commands or identity permissions change.
- Neighbors: `openclaw-imports/gmail` routes to `mail`; `email-access-policy` owns test identities and routes Gmail retrieval to `mail`. No competing delivery rule in those routes. `tests/test_mail_skill.py` asserts the owner contract. No router change needed.
- Verification: `python3 -m unittest discover -s tests -v` passed 41 tests; `git diff --check` passed. Independent read-only review found no issues and reran 41 tests. Repository has no separate policy lint command; contract tests cover the mail rule. Integrated checks pending.
- Activation: A beta merge changes the configured General Skills source; confirm focused profile sync dry-run, runtime symlink, and active skill load. No stable promotion requested.
- Next: test, review, commit, integrate into beta, verify projection, retire this dossier from beta and clean feature worktree. Implementation commit pending.
