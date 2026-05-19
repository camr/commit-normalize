#!/bin/sh
# commit-normalize.sh: entry point called by the .git/hooks/commit-msg hook.
# Delegates to scripts/commit-msg which contains the full normalizer logic.

set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
exec sh "$REPO_ROOT/scripts/commit-msg" "$@"
