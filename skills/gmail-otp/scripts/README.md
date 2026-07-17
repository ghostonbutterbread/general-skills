# Gmail OTP Scripts

### `gmail_otp.py`
- Purpose: narrowly read an OAuth-authorized Gmail inbox for user-initiated login/password-reset OTPs; send only to `ryushe.dev@gmail.com`.
- Inputs: Google Desktop OAuth client JSON during one-time setup; Gmail message IDs, Gmail search queries, or an exact allowlisted recipient for normal use.
- Outputs: JSON message metadata/body, OTP candidates, or a Gmail send result. Never prints OAuth tokens.
- Safe to run on: a dedicated mailbox/account controlled by Ryushe.
- Mutates: creates/refreshes owner-only OAuth state in `$HERMES_HOME/gmail-otp/`; the `send` command delivers one plain-text email only to `ryushe.dev@gmail.com`. Inbox commands do not mutate Gmail state.
- Example:
  ```bash
  python3 ~/.hermes/synced-skills/gmail-otp/scripts/gmail_otp.py otp \
    --query 'is:unread newer_than:2d' --max 10
  ```
- Tests: `python3 -m py_compile skills/gmail-otp/scripts/gmail_otp.py`; mocked send allowlist and read-only static capability checks.
- Owner: general-skills/gmail-otp.
- Last verified: 2026-07-17.
