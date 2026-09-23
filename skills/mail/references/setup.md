# Mail setup

Load when Composio CLI is missing, authentication/connection is unavailable, or
the installed CLI's interface needs checking. Provider selection belongs to the
`mail` router; account/email policies own identity mappings.

## Install only when authorized

The exact installation command is:

```sh
curl -fsSL https://composio.dev/install | sh
```

Do not install merely to validate documentation. Installation is not login or
mailbox authorization. Check [current Composio CLI documentation](https://docs.composio.dev/docs/cli)
and the installed CLI's help before execution:

```sh
composio --help
```

## Secure connection handoff

The documented account login command is `composio login`. Tell the user when
login or the requested email connection is missing; let them complete the
provider's browser consent in a secure interactive handoff. Never ask for
passwords, tokens, OAuth codes, or callback URLs in chat. Do not create an
unattended agent account instead of connecting the user's authorized account.

Composio documents `composio link` for connecting apps. Select the provider
identified by the authorized task and inspect its current CLI help. For a
Gmail task, the documentation verifies `composio link gmail`; that is a provider
example, not a default mailbox or authorization to connect one.

## Discover read tools

The current documentation verifies these Gmail discovery/schema examples:

```sh
composio search "search and read gmail messages"
composio execute GMAIL_FETCH_EMAILS --get-schema
```

For another authorized email provider, search for that provider's read/search
tools instead. Inspect the returned tool schema, confirm the account, and supply
the requested query and bounded result count. Inspect any message-detail tool's
schema too. Do not invent slugs, flags, or inputs. CLI/version mismatches are
setup blockers; do not widen scopes, install plugins, or read a sample message
just to validate this skill.

Commands were checked against the linked official documentation; an installed
CLI was not available during authoring. Recheck local help/schema at use time.
