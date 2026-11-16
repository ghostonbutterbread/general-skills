# Agent Outreach Scripts

- `send.py`: Python 3.11+ one-way Discord webhook sender. Loads a named destination's `webhook_file` from the local General Skills config; validates that the credential is private and targets Discord; posts concise Markdown with mentions suppressed. Does not automatically retry. Exit `0` means Discord accepted the request, not that a human saw it; nonzero means failure or uncertain delivery. Never logs the webhook URL or response body.
- Focused tests from the source checkout: `python3 -m unittest discover -s tests -p test_agent_outreach.py -v`. Use fake local secrets and mocked HTTP; never put a real webhook into a test. For live verification, use a separately provisioned disposable/approved destination and disclose that a message will be sent.
- The script is self-contained because consumers may project the skill directory without projecting repository-root helpers. Keep config path behavior consistent with `scripts/general_skills_config.py`.
