#!/usr/bin/env bash
# Wire normalize_commit.py into a git repo as the commit-msg hook.
#
# Usage: bash install_hook.sh [repo-dir]
#   repo-dir defaults to the current working directory.

set -euo pipefail

REPO_DIR="${1:-$(pwd)}"
HOOKS_DIR="${REPO_DIR}/.git/hooks"

if [[ ! -d "${HOOKS_DIR}" ]]; then
    echo "error: ${REPO_DIR} is not a git repository (missing .git/hooks)" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NORMALIZER="${SCRIPT_DIR}/normalize_commit.py"

if [[ ! -f "${NORMALIZER}" ]]; then
    echo "error: normalize_commit.py not found at ${NORMALIZER}" >&2
    exit 1
fi

HOOK_FILE="${HOOKS_DIR}/commit-msg"

# printf %q produces a shell-escaped token, so paths with spaces are safe.
{
    echo '#!/usr/bin/env bash'
    printf 'exec python3 %q "$1"\n' "${NORMALIZER}"
} > "${HOOK_FILE}"

chmod +x "${HOOK_FILE}"
echo "installed commit-msg hook -> ${HOOK_FILE}"
