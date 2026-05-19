#!/bin/sh
# install-hook.sh: install the commit-msg normalizer as a git hook.
#
# Run from anywhere inside a git repository:
#   ./scripts/install-hook.sh
#
# Options:
#   --copy   Copy the script instead of symlinking (useful for shared repos)
#   --check  Verify the hook is installed without making changes

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK_SRC="$SCRIPT_DIR/commit-msg"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
MODE="symlink"
for arg in "$@"; do
    case "$arg" in
        --copy)  MODE="copy" ;;
        --check) MODE="check" ;;
        *)
            printf 'unknown option: %s\n' "$arg" >&2
            printf 'usage: install-hook.sh [--copy] [--check]\n' >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Locate the git root
# ---------------------------------------------------------------------------
GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    printf 'error: not inside a git repository\n' >&2
    exit 1
}
HOOKS_DIR="$GIT_ROOT/.git/hooks"
HOOK_DEST="$HOOKS_DIR/commit-msg"

# ---------------------------------------------------------------------------
# Validate source
# ---------------------------------------------------------------------------
if [ ! -f "$HOOK_SRC" ]; then
    printf 'error: hook source not found: %s\n' "$HOOK_SRC" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Check mode
# ---------------------------------------------------------------------------
if [ "$MODE" = "check" ]; then
    if [ -f "$HOOK_DEST" ] || [ -L "$HOOK_DEST" ]; then
        printf 'hook is installed: %s\n' "$HOOK_DEST"
        exit 0
    else
        printf 'hook is NOT installed\n'
        exit 1
    fi
fi

# ---------------------------------------------------------------------------
# Back up existing hook if present
# ---------------------------------------------------------------------------
if [ -f "$HOOK_DEST" ] || [ -L "$HOOK_DEST" ]; then
    BACKUP="${HOOK_DEST}.bak.$(date +%Y%m%d%H%M%S)"
    printf 'backing up existing hook to %s\n' "$BACKUP"
    mv "$HOOK_DEST" "$BACKUP"
fi

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
mkdir -p "$HOOKS_DIR"

if [ "$MODE" = "copy" ]; then
    cp "$HOOK_SRC" "$HOOK_DEST"
    printf 'copied hook to %s\n' "$HOOK_DEST"
else
    ln -s "$HOOK_SRC" "$HOOK_DEST"
    printf 'symlinked hook to %s\n' "$HOOK_DEST"
fi

chmod +x "$HOOK_DEST"
printf 'commit-msg hook installed successfully\n'
