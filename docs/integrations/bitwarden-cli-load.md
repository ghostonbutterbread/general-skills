# Bitwarden CLI load correction

- Owner: Hermes, task `t_6507b829`; corrected interpretation of `t_d5d8b184`.
- Branch: `fix/bitwarden-cli-load`; base: `origin/beta` `3dff6b2fe90b6936cf1cdc19b342ad679953889c`; integration target: `beta`.
- Intent: load `bitwarden` before the first `bw` command or bw-backed helper, so agents see safe preflight and unlock directions. Merely reading an opaque item reference does not trigger CLI guidance.
- Boundary: account-registry still owns login/recovery order; account-manager routes credential-store work to bitwarden. No other skills changed.
- Evidence: pending tests and independent review.
- Activation: beta integration and live symlink/fresh-agent load needed; stable promotion not requested.
- Next: test, review, merge into beta, retire this temporary dossier, verify remote and runtime.
