#!/usr/bin/env bash
# Wrapper invoked by the commit-msg hook.
# Normalizes the commit message file using normalizer.py.

set -euo pipefail

COMMIT_MSG_FILE="${1:?commit message file argument required}"
REPO_ROOT="$(git rev-parse --show-toplevel)"

python3 "${REPO_ROOT}/normalizer.py" "$COMMIT_MSG_FILE"
