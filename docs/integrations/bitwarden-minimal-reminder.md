# Minimal Bitwarden reminder

- Owner: Hermes, `t_ded3ad9e`; branch `fix/bitwarden-minimal-reminder`, base `origin/beta` `b9142b6b41c5ed630a7977ad718c7c0cb7275ef1`, target `beta`.
- Ryu's intent: one concise instruction to load the Bitwarden skill before `bw` so agents find the existing unlock instructions. Remove the extra examples, delegation and reference discussion added earlier.
- Scope: `skills/bitwarden/SKILL.md` and a focused wording regression; original account-registry order restored except removing restrictive “only.”
- Evidence: pending tests and independent review.
- Activation: integrate beta, push, verify active skill and fresh load. No stable promotion.
- Next: test, review, integrate and remove this temporary dossier.
