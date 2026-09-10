---
name: dotfile_management
description: Use when managing Ryushe's Stow-backed dotfiles.
---

# Dotfile Management

Use this skill for `ryushe/dotfiles`, whose `ln_dotfiles.sh` wrapper invokes
GNU Stow. A top-level package directory is only Stow's container; the
application reads its configuration from the real path below `$HOME`.

## When to Use

- Migrating an application's existing configuration into a Stow dotfiles repo.
- Adding, changing, or removing a Stow-managed configuration.
- Checking where a tracked configuration will be linked.
- Preparing a clean-machine dotfiles bootstrap.

Do not use this for unrelated manual `ln -s` work.

## Path Rule

Preserve the application's actual destination-relative configuration path under
one top-level Stow package.

Example for Kitty:

- Actual application path: `~/.config/kitty/kitty.conf`
- Stow package container: `kitty/`
- Tracked source path: `kitty/.config/kitty/kitty.conf`
- Linker: `./ln_dotfiles.sh`

The `kitty/` package name does not appear in the installed path. Put every file
or subdirectory from `~/.config/kitty/` that should be backed up and linked
under `kitty/.config/kitty/`, preserving its exact relative path.

For example, `picom/.config/picom/picom.conf` installs at
`~/.config/picom/picom.conf`.

## Procedure

1. Identify the exact live configuration path the application reads.
2. Move or copy selected configuration files into a top-level package while
   preserving the destination-relative path.
3. Inspect `ln_dotfiles.sh`. New non-blacklisted top-level packages are handled
   by its Stow loop automatically; do not create `.ln` files or individual
   `ln -s` links.
4. Run `stow --simulate --verbose <package>` from the repository root. Continue
   only when every target is intended.
5. On a fresh-machine bootstrap, run `./removeoldsymlinks.sh`, then
   `./ln_dotfiles.sh`. If the script installs Stow, rerun the linker because the
   initially skipped package is not retried.
6. Confirm each target is a symlink into the dotfiles checkout and launch the
   application to verify it reads the linked configuration.

## Safety

- `removeoldsymlinks.sh` is a destructive cleanup allowlist, not the inventory
  of every managed dotfile. Add only exact, safe-to-remove conflicting paths.
- Stow does not overwrite a conflicting real file. Preserve or deliberately
  remove the conflict before linking.
- Preserve literal script names: `ln_dotfiles.sh` and `removeoldsymlinks.sh`.
- “Use the .ln dotfiles script” means use `./ln_dotfiles.sh`; it does not mean
  create or symlink `.ln` files.

## Verification

- The Stow simulation reports only intended targets.
- Migrated files appear at their actual application paths, not below a
  package-named directory.
- `readlink <actual-path>` resolves into the dotfiles checkout.
- The application loads the linked configuration.
