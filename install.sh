#!/usr/bin/env bash
# Install the commit-msg hook locally or globally.
#
# Usage:
#   bash install.sh           install into .git/hooks/ of the current repo
#   bash install.sh --global  install into the global git hooks template dir

set -euo pipefail

GLOBAL=0
for arg in "$@"; do
    case "$arg" in
        --global) GLOBAL=1 ;;
        *) echo "unknown argument: $arg" >&2; exit 1 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOOK_SRC="$SCRIPT_DIR/commit-msg"

if [ ! -f "$HOOK_SRC" ]; then
    echo "error: commit-msg hook not found at $HOOK_SRC" >&2
    exit 1
fi

if [ "$GLOBAL" -eq 1 ]; then
    TEMPLATE_DIR="$(git config --global init.templateDir 2>/dev/null || true)"
    if [ -z "$TEMPLATE_DIR" ]; then
        TEMPLATE_DIR="$HOME/.git-templates"
        git config --global init.templateDir "$TEMPLATE_DIR"
        echo "set global hooks template dir to $TEMPLATE_DIR"
    fi
    HOOKS_DEST="$TEMPLATE_DIR/hooks"
    mkdir -p "$HOOKS_DEST"
else
    REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
    if [ -z "$REPO_ROOT" ]; then
        echo "error: not inside a git repository (use --global to install globally)" >&2
        exit 1
    fi
    HOOKS_DEST="$REPO_ROOT/.git/hooks"
    mkdir -p "$HOOKS_DEST"
fi

DEST="$HOOKS_DEST/commit-msg"
cp "$HOOK_SRC" "$DEST"
chmod +x "$DEST"
echo "installed commit-msg hook -> $DEST"
