#!/usr/bin/env bash
# Install git hooks from the hooks/ directory into .git/hooks/.
# Run from the repo root: bash install-hooks.sh

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
HOOKS_SRC="$REPO_ROOT/hooks"
HOOKS_DEST="$REPO_ROOT/.git/hooks"

for hook in "$HOOKS_SRC"/*; do
    name="$(basename "$hook")"
    dest="$HOOKS_DEST/$name"
    cp "$hook" "$dest"
    chmod +x "$dest"
    echo "installed $name -> $dest"
done

echo "hooks installed"
