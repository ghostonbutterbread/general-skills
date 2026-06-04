---
name: tmpmail
description: "Use the tmpmail CLI for disposable terminal inboxes in owned test workflows."
---

# tmpmail

Use when an agent needs a disposable email inbox through the `tmpmail` terminal utility.

This skill is for owned test accounts and verification flows. It does not replace durable researcher email, Gmail, or program-provided accounts.

## Preflight

1. Confirm disposable email is allowed for the target workflow.
2. Use only inboxes created for the current owned test task.
3. Prefer existing `agent-email` / Mail.tm workflows when account tracking, aliases, or repeat reads are needed.
4. Do not paste mailbox passwords, target passwords, tokens, cookies, reset links, verification links, verification codes, or private message bodies into chat, prompts, notes, findings, or reports.

## Install

If `tmpmail` is missing, install it locally:

```bash
mkdir -p ~/.local/bin
curl -L "https://raw.githubusercontent.com/sdushantha/tmpmail/master/tmpmail" > /tmp/tmpmail
sed -n '1,220p' /tmp/tmpmail
chmod +x /tmp/tmpmail
mv /tmp/tmpmail ~/.local/bin/tmpmail
```

Make sure `~/.local/bin` is on `PATH` before using it:

```bash
export PATH="$HOME/.local/bin:$PATH"
command -v tmpmail
```

Dependencies commonly needed by `tmpmail`: `curl`, `jq`, `w3m`, and `xclip`.

If the fetched script looks unexpected, stop and report it instead of installing.

## Workflow

1. Check the tool is available:
   ```bash
   tmpmail --help
   ```
2. Generate an inbox:
   ```bash
   tmpmail --generate
   ```
3. Use the generated address only for the current owned signup or verification flow.
4. List inbox messages:
   ```bash
   tmpmail
   ```
5. Read only the needed message. Prefer text mode for safer extraction:
   ```bash
   tmpmail -t <message-id>
   ```
6. Record only non-secret account metadata:
   ```text
   Account alias:
   Email reference:
   Target/program:
   Purpose:
   Destructible: yes|no
   Cleanup notes:
   Credential store item:
   ```

## Examples

These are examples and things agents can think about trying when they match the task:

- Generate a random inbox for a disposable signup:
  ```bash
  tmpmail --generate
  ```
- Generate a custom inbox when the target accepts 1secmail domains:
  ```bash
  tmpmail --generate my-test-alias@1secmail.com
  ```
- Check whether verification mail arrived:
  ```bash
  tmpmail
  ```
- Open the latest message without dumping it into chat:
  ```bash
  tmpmail -r
  ```
- Read a known message as text and extract only the action needed locally:
  ```bash
  tmpmail -t <message-id>
  ```

## Stop Conditions

- The target blocks disposable email, requires phone/KYC/payment/SSO, or explicitly prohibits temporary inboxes.
- The flow needs a durable account, shared team identity, or program-domain email.
- The output contains secrets, verification codes, magic links, reset links, tokens, cookies, or private user data that would be exposed to chat or notes.
- Cleanup expectations are unclear for an account or public-facing artifact created during testing.
