#!/usr/bin/env bash
# test_commit_normalize.sh - Unit tests for tools/commit-normalize.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NORMALIZE="$SCRIPT_DIR/../tools/commit-normalize.sh"

pass=0
fail=0

run_test() {
    local name="$1"
    local input="$2"
    local expected="$3"
    local should_fail="${4:-false}"

    local tmpfile
    tmpfile=$(mktemp)
    printf '%s' "$input" > "$tmpfile"

    if $should_fail; then
        if bash "$NORMALIZE" "$tmpfile" 2>/dev/null; then
            printf 'FAIL [%s]: expected non-zero exit but got 0\n' "$name"
            fail=$((fail + 1))
        else
            printf 'PASS [%s]\n' "$name"
            pass=$((pass + 1))
        fi
    else
        if bash "$NORMALIZE" "$tmpfile" 2>/dev/null; then
            local actual
            actual=$(cat "$tmpfile")
            if [[ "$actual" == "$expected" ]]; then
                printf 'PASS [%s]\n' "$name"
                pass=$((pass + 1))
            else
                printf 'FAIL [%s]: expected "%s" got "%s"\n' "$name" "$expected" "$actual"
                fail=$((fail + 1))
            fi
        else
            printf 'FAIL [%s]: script exited non-zero unexpectedly\n' "$name"
            fail=$((fail + 1))
        fi
    fi

    rm -f "$tmpfile"
}

# --- Normalization tests ---

run_test "lowercase type" \
    "FEAT: add new feature" \
    "feat: add new feature"

run_test "lowercase mixed-case type" \
    "Fix: resolve crash on startup" \
    "fix: resolve crash on startup"

run_test "already lowercase passes through" \
    "feat: add new feature" \
    "feat: add new feature"

run_test "scope preserved" \
    "FEAT(auth): add oauth2 login" \
    "feat(auth): add oauth2 login"

run_test "breaking change marker preserved" \
    "FEAT!: drop old api" \
    "feat!: drop old api"

run_test "scope and breaking change preserved" \
    "FIX(api)!: remove deprecated endpoint" \
    "fix(api)!: remove deprecated endpoint"

run_test "normalize extra spaces after colon" \
    "feat:  add thing with extra space" \
    "feat: add thing with extra space"

run_test "strip trailing period" \
    "feat: add new feature." \
    "feat: add new feature"

run_test "truncate long subject to 72 chars" \
    "feat: $(printf 'a%.0s' {1..80})" \
    "feat: $(printf 'a%.0s' {1..66})"

run_test "preserve body after subject" \
    "feat: add thing

This is the body." \
    "feat: add thing

This is the body."

run_test "skip merge commit" \
    "Merge branch 'main' into feature" \
    "Merge branch 'main' into feature"

run_test "skip fixup commit" \
    "fixup! feat: previous commit" \
    "fixup! feat: previous commit"

run_test "skip squash commit" \
    "squash! fix: something" \
    "squash! fix: something"

# --- All valid type tokens ---
for t in feat fix chore docs refactor test ci style perf build revert; do
    run_test "type ${t} accepted" \
        "${t}: some change" \
        "${t}: some change"
done

# --- Rejection tests ---

run_test "reject unknown type" \
    "unknown: some change" \
    "" \
    true

run_test "reject missing colon" \
    "feat add thing without colon" \
    "" \
    true

run_test "reject empty type" \
    ": missing type" \
    "" \
    true

# --- Summary ---
printf '\n%d passed, %d failed\n' "$pass" "$fail"

if [[ $fail -gt 0 ]]; then
    exit 1
fi
