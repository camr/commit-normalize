#!/usr/bin/env bash
# install-hooks.sh - Install the commit-normalize commit-msg hook
#
# Usage:
#   bash tools/install-hooks.sh            # install into .git/hooks for current repo
#   bash tools/install-hooks.sh --global   # install into global git hooks directory
#
# The script symlinks tools/commit-normalize.sh as the commit-msg hook.
# For per-repo installs, the symlink is relative so it works after cloning.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SCRIPT="$SCRIPT_DIR/commit-normalize.sh"
HOOK_NAME="commit-msg"

# Verify the hook script exists
if [[ ! -f "$HOOK_SCRIPT" ]]; then
    printf 'error: hook script not found: %s\n' "$HOOK_SCRIPT" >&2
    exit 1
fi

# Ensure hook script is executable
chmod +x "$HOOK_SCRIPT"

global_install=false
if [[ "${1:-}" == "--global" ]]; then
    global_install=true
fi

if $global_install; then
    # Global install: use git's core.hooksPath
    hooks_dir="${XDG_CONFIG_HOME:-$HOME/.config}/git/hooks"
    mkdir -p "$hooks_dir"
    target="$hooks_dir/$HOOK_NAME"
    ln -sf "$HOOK_SCRIPT" "$target"
    git config --global core.hooksPath "$hooks_dir"
    printf 'installed globally: %s -> %s\n' "$target" "$HOOK_SCRIPT"
    printf 'global core.hooksPath set to: %s\n' "$hooks_dir"
else
    # Per-repo install
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
    if [[ -z "$repo_root" ]]; then
        printf 'error: not inside a git repository\n' >&2
        exit 1
    fi

    hooks_dir="$repo_root/.git/hooks"
    mkdir -p "$hooks_dir"
    target="$hooks_dir/$HOOK_NAME"

    # Check for existing hook
    if [[ -e "$target" && ! -L "$target" ]]; then
        printf 'warning: existing hook found at %s\n' "$target" >&2
        printf 'backing up to %s.bak\n' "$target" >&2
        mv "$target" "${target}.bak"
    fi

    ln -sf "$HOOK_SCRIPT" "$target"
    printf 'installed: %s -> %s\n' "$target" "$HOOK_SCRIPT"
fi
