#!/usr/bin/env python3
"""Create and read the portable General Skills user configuration."""

from __future__ import annotations

import argparse
import os
import tomllib
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = """# General Skills user configuration.
# This file is created automatically on first use. Environment variables take
# precedence when a one-off override is needed.

[hoster]
# Override with HOSTER_SSH_KEY or --identity-file.
identity_file = "~/.ssh/hoster"

[faq]
# Override with FAQ_CENTRAL or --central.
faq_directory = "~/notes/appsec/faq"
"""


def config_path() -> Path:
    """Return the explicit or XDG-compliant configuration path."""
    configured = os.environ.get("GENERAL_SKILLS_CONFIG")
    if configured:
        return Path(configured).expanduser()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "general-skills" / "config.toml"


def ensure_config() -> Path:
    """Create the default configuration once, without replacing user edits."""
    path = config_path()
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return path
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(DEFAULT_CONFIG)
    return path


def load_config() -> dict[str, Any]:
    """Load the generated configuration, surfacing malformed user edits clearly."""
    path = ensure_config()
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"General Skills config is invalid TOML: {path}: {exc}") from exc


def configured_path(section: str, key: str, *, environment: str, default: str) -> Path:
    """Resolve an env override or configured path without host-specific defaults."""
    value = os.environ.get(environment)
    if value is None:
        section_values = load_config().get(section, {})
        value = section_values.get(key, default)
    return Path(os.path.expandvars(str(value))).expanduser()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "path", "show"), nargs="?", default="show")
    args = parser.parse_args()
    path = ensure_config()
    if args.command == "path":
        print(path)
    elif args.command == "show":
        print(path)
        print(path.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
