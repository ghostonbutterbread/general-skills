#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
  printf 'Usage: %s <item-name> <username> <uri> [notes]\n' "$0" >&2
  exit 2
fi

if [[ -z "${BW_SESSION:-}" ]]; then
  printf 'BW_SESSION is required. Source bw-session.sh or unlock Bitwarden manually first.\n' >&2
  exit 1
fi

item_name="$1"
username="$2"
uri="$3"
notes="${4:-Created by Ghost account setup workflow.}"

version="$(bw --version)"
if [[ "$version" == "2026.4.0" ]]; then
  printf 'Refusing Bitwarden CLI version 2026.4.0.\n' >&2
  exit 1
fi

password="$(bw generate --length 24 --uppercase --lowercase --number --special --session "$BW_SESSION")"
template="$(bw get template item --session "$BW_SESSION")"

item_json="$(TEMPLATE="$template" python3 - "$item_name" "$username" "$password" "$uri" "$notes" <<'PY'
import json
import os
import sys

item = json.loads(os.environ["TEMPLATE"])
name, username, password, uri, notes = sys.argv[1:]
item["type"] = 1
item["name"] = name
item["notes"] = notes
item["login"] = {
    "username": username,
    "password": password,
    "uris": [{"match": None, "uri": uri}],
}
print(json.dumps(item, separators=(",", ":")))
PY
)"

encoded="$(printf '%s' "$item_json" | bw encode)"
created="$(bw create item "$encoded" --session "$BW_SESSION")"
bw sync --quiet --session "$BW_SESSION" >/dev/null

CREATED="$created" python3 - <<'PY'
import json
import os
import sys

item = json.loads(os.environ["CREATED"])
print(f"created_item_id={item.get('id', '')}")
print(f"created_item_name={item.get('name', '')}")
PY
