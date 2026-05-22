#!/usr/bin/env bash
# Install the commit-msg hook into a target git repository.
#
# Usage: ./scripts/install-hook.sh [TARGET_REPO_PATH]
#
# If TARGET_REPO_PATH is omitted, the current directory is used.

set -euo pipefail

TARGET_REPO="${1:-.}"
HOOKS_DIR="${TARGET_REPO}/.git/hooks"
HOOK_FILE="${HOOKS_DIR}/commit-msg"

if [ ! -d "${TARGET_REPO}/.git" ]; then
    echo "error: '${TARGET_REPO}' is not a git repository" >&2
    exit 1
fi

if ! command -v normalize-commit-msg &>/dev/null; then
    echo "error: normalize-commit-msg not found in PATH" >&2
    echo "Install it first: pip install -e /path/to/commit-normalize" >&2
    exit 1
fi

NORMALIZER_PATH="$(command -v normalize-commit-msg)"

cat > "${HOOK_FILE}" <<EOF
#!/usr/bin/env bash
# Installed by commit-normalize/scripts/install-hook.sh
exec "${NORMALIZER_PATH}" "\$1"
EOF

chmod +x "${HOOK_FILE}"
echo "Installed commit-msg hook at ${HOOK_FILE}"
