#!/usr/bin/env bash
# Install normalize_commit.py as the commit-msg hook in a target git repo.
# Usage: ./install.sh [path-to-repo]  (defaults to current directory)
set -euo pipefail

REPO="${1:-.}"
HOOK_DIR="$REPO/.git/hooks"
HOOK_FILE="$HOOK_DIR/commit-msg"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$HOOK_DIR" ]; then
    echo "error: $REPO does not appear to be a git repository (.git/hooks not found)" >&2
    exit 1
fi

cp "$SCRIPT_DIR/normalize_commit.py" "$HOOK_FILE"
chmod +x "$HOOK_FILE"

echo "installed: $HOOK_FILE"
