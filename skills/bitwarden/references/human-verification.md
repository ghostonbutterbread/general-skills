# Human Verification

Human verification is an account setup blocker, not a vulnerability finding.

## Allowed

- Use an approved visible browser profile for the target signup.
- Let Ryushe or the operator complete Cloudflare/CAPTCHA/Turnstile prompts manually.
- Use approved setup-only solving when the target policy and local account-creation workflow allow it.
- Keep the action low-volume and tied to one owned test account.

## Not Allowed

- Do not use CAPTCHA solving for bulk account creation, scraping, rate-limit evasion, spam, denial of service, or noisy automation.
- Do not attempt to bypass or attack the challenge system.
- Do not classify network or challenge configuration as a Canva.cn finding.
- Do not continue account creation if the flow requires phone/KYC/payment unless Ryushe explicitly approves that exact step.

## Practical Flow

1. Try the normal approved visible browser first.
2. If headless hits verification, switch to a visible browser and pause for manual completion.
3. After completion, continue signup with the approved alias.
4. Store credentials in Bitwarden before using the account for testing.
5. Record only account alias and Bitwarden item reference in notes.

