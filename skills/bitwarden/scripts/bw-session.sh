#!/usr/bin/env bash
set -euo pipefail

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  printf 'Source this script so BW_SESSION is exported in your current shell:\n' >&2
  printf '  source %s /path/to/local/password-file\n' "$0" >&2
  exit 2
fi

password_file="${1:-}"
if [[ -z "$password_file" ]]; then
  printf 'Usage: source %s /path/to/local/password-file\n' "${BASH_SOURCE[0]}" >&2
  return 2
fi

if [[ ! -f "$password_file" ]]; then
  printf 'Bitwarden password file not found.\n' >&2
  return 1
fi

mode="$(stat -c '%a' "$password_file")"
case "$mode" in
  600|400) ;;
  *)
    printf 'Refusing password file with permissions %s. Use chmod 600 or chmod 400.\n' "$mode" >&2
    return 1
    ;;
esac

version="$(bw --version)"
if [[ "$version" == "2026.4.0" ]]; then
  printf 'Refusing Bitwarden CLI version 2026.4.0.\n' >&2
  return 1
fi

BW_SESSION="$(bw unlock --raw --passwordfile "$password_file")"
export BW_SESSION
bw sync --quiet --session "$BW_SESSION" >/dev/null
printf 'Bitwarden session unlocked for this shell.\n' >&2

