#!/usr/bin/env bash
# install-commit-hook.sh
#
# Install normalize-commit-msg.sh as a git commit-msg hook.
#
# Usage:
#   install-commit-hook.sh [--global] [--repo-path PATH]
#
# Options:
#   --global         Install into the global git hooks directory (git config core.hooksPath)
#   --repo-path DIR  Target a specific repository (default: current directory)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NORMALIZER="${SCRIPT_DIR}/normalize-commit-msg.sh"

GLOBAL=false
REPO_PATH="."

while [[ $# -gt 0 ]]; do
    case "$1" in
        --global) GLOBAL=true; shift ;;
        --repo-path) REPO_PATH="$2"; shift 2 ;;
        *) echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

if [[ ! -x "$NORMALIZER" ]]; then
    chmod +x "$NORMALIZER" 2>/dev/null || true
    if [[ ! -x "$NORMALIZER" ]]; then
        echo "ERROR: Normalizer script not found or not executable: $NORMALIZER" >&2
        exit 1
    fi
fi

if [[ "$GLOBAL" == true ]]; then
    HOOKS_DIR="$(git config --global core.hooksPath 2>/dev/null || echo "")"
    if [[ -z "$HOOKS_DIR" ]]; then
        HOOKS_DIR="${HOME}/.git-hooks"
        mkdir -p "$HOOKS_DIR"
        git config --global core.hooksPath "$HOOKS_DIR"
        echo "Set global hooks path to: ${HOOKS_DIR}"
    fi
else
    GIT_DIR="$(git -C "$REPO_PATH" rev-parse --git-dir 2>/dev/null)" || {
        echo "ERROR: Not a git repository: ${REPO_PATH}" >&2
        exit 1
    }
    if [[ "$GIT_DIR" != /* ]]; then
        GIT_DIR="${REPO_PATH}/${GIT_DIR}"
    fi
    HOOKS_DIR="${GIT_DIR}/hooks"
    mkdir -p "$HOOKS_DIR"
fi

HOOK_FILE="${HOOKS_DIR}/commit-msg"

cat > "$HOOK_FILE" <<EOF
#!/usr/bin/env bash
# Auto-installed by install-commit-hook.sh
exec "${NORMALIZER}" "\$1"
EOF

chmod +x "$HOOK_FILE"

echo "Installed commit-msg hook at: ${HOOK_FILE}"
echo "Hook normalizes commit messages using: ${NORMALIZER}"
