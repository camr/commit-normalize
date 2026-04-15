#!/usr/bin/env bash
# install_hook.sh - Install the commit-msg normalizer as a git hook.
#
# Usage:
#   ./install_hook.sh [TARGET_REPO_PATH]
#
# If TARGET_REPO_PATH is omitted, installs into the current repo's hooks dir.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLI="$SCRIPT_DIR/cli.py"

TARGET_REPO="${1:-$(pwd)}"
HOOKS_DIR="$TARGET_REPO/.git/hooks"

if [ ! -d "$HOOKS_DIR" ]; then
    echo "Error: $HOOKS_DIR does not exist. Is $TARGET_REPO a git repository?"
    exit 1
fi

HOOK_PATH="$HOOKS_DIR/commit-msg"

# Remove existing hook if present.
if [ -e "$HOOK_PATH" ] || [ -L "$HOOK_PATH" ]; then
    rm "$HOOK_PATH"
fi

# Create a small wrapper script so python is resolved at hook runtime.
cat > "$HOOK_PATH" <<HOOK
#!/usr/bin/env bash
exec python3 "$CLI" "\$1"
HOOK

chmod +x "$HOOK_PATH"
echo "Installed commit-msg hook at $HOOK_PATH"
echo "The hook will normalize commit messages using $CLI"
