#!/bin/sh
# test_commit_msg.sh: unit tests for the commit-msg normalizer hook.
#
# Run from the repository root:
#   sh tests/test_commit_msg.sh
#
# Exit code 0 = all tests passed; non-zero = one or more failures.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOOK="$SCRIPT_DIR/../scripts/commit-msg"
TMPFILE=$(mktemp)

PASS=0
FAIL=0

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
run_hook() {
    printf '%s' "$1" > "$TMPFILE"
    sh "$HOOK" "$TMPFILE"
    cat "$TMPFILE"
}

assert_eq() {
    label="$1"
    expected="$2"
    actual="$3"
    if [ "$actual" = "$expected" ]; then
        PASS=$((PASS + 1))
        printf 'PASS  %s\n' "$label"
    else
        FAIL=$((FAIL + 1))
        printf 'FAIL  %s\n' "$label"
        printf '      expected: %s\n' "$expected"
        printf '      actual:   %s\n' "$actual"
    fi
}

# ---------------------------------------------------------------------------
# Tests: valid messages pass through correctly
# ---------------------------------------------------------------------------

result=$(run_hook "feat: Add new login flow")
assert_eq "valid feat message unchanged" "feat: Add new login flow" "$result"

result=$(run_hook "fix: Correct null pointer in parser")
assert_eq "valid fix message unchanged" "fix: Correct null pointer in parser" "$result"

result=$(run_hook "chore: Update dependencies")
assert_eq "valid chore message unchanged" "chore: Update dependencies" "$result"

result=$(run_hook "docs: Add API reference section")
assert_eq "valid docs message unchanged" "docs: Add API reference section" "$result"

result=$(run_hook "refactor: Extract helper function")
assert_eq "valid refactor message unchanged" "refactor: Extract helper function" "$result"

result=$(run_hook "test: Add coverage for auth module")
assert_eq "valid test message unchanged" "test: Add coverage for auth module" "$result"

result=$(run_hook "style: Fix indentation")
assert_eq "valid style message unchanged" "style: Fix indentation" "$result"

result=$(run_hook "perf: Cache database queries")
assert_eq "valid perf message unchanged" "perf: Cache database queries" "$result"

result=$(run_hook "ci: Add lint step to pipeline")
assert_eq "valid ci message unchanged" "ci: Add lint step to pipeline" "$result"

# ---------------------------------------------------------------------------
# Tests: type lowercasing
# ---------------------------------------------------------------------------

result=$(run_hook "FEAT: Add feature")
assert_eq "uppercase type is lowercased" "feat: Add feature" "$result"

result=$(run_hook "Fix: Correct bug")
assert_eq "mixed case type is lowercased" "fix: Correct bug" "$result"

# ---------------------------------------------------------------------------
# Tests: subject capitalization
# ---------------------------------------------------------------------------

result=$(run_hook "feat: add new feature")
assert_eq "subject first word is capitalized" "feat: Add new feature" "$result"

result=$(run_hook "fix: correct the issue")
assert_eq "fix subject capitalized" "fix: Correct the issue" "$result"

# ---------------------------------------------------------------------------
# Tests: trailing period removal
# ---------------------------------------------------------------------------

result=$(run_hook "feat: Add new feature.")
assert_eq "trailing period removed" "feat: Add new feature" "$result"

result=$(run_hook "fix: Resolve null pointer.")
assert_eq "trailing period removed from fix" "fix: Resolve null pointer" "$result"

result=$(run_hook "docs: See the changelog...")
assert_eq "ellipsis preserved" "docs: See the changelog..." "$result"

# ---------------------------------------------------------------------------
# Tests: missing type prefix - inferred from description
# ---------------------------------------------------------------------------

result=$(run_hook "add user authentication")
assert_eq "bare add description gets feat type" "feat: Add user authentication" "$result"

result=$(run_hook "fix broken redirect")
assert_eq "bare fix description gets fix type" "fix: Fix broken redirect" "$result"

result=$(run_hook "update readme")
assert_eq "bare docs description gets appropriate type" "docs: Update readme" "$result"

# ---------------------------------------------------------------------------
# Tests: subject line length limit (72 chars)
# ---------------------------------------------------------------------------

long_subject="feat: Add a really long description that goes beyond the seventy-two character limit set by the conventional commits spec"
result=$(run_hook "$long_subject")
result_len=${#result}
assert_eq "long subject truncated to <=72 chars" "72" "$result_len"

# ---------------------------------------------------------------------------
# Tests: scope is preserved
# ---------------------------------------------------------------------------

result=$(run_hook "feat(auth): add oauth support")
assert_eq "scope preserved and description capitalized" "feat(auth): Add oauth support" "$result"

result=$(run_hook "fix(api): correct response code")
assert_eq "fix with scope preserved" "fix(api): Correct response code" "$result"

# ---------------------------------------------------------------------------
# Tests: body preserved with blank line separator
# ---------------------------------------------------------------------------

msg_with_body="feat: Add feature

This is the body of the commit message.
It can span multiple lines."

result=$(run_hook "$msg_with_body")
expected_with_body="feat: Add feature

This is the body of the commit message.
It can span multiple lines."
assert_eq "body preserved with blank separator" "$expected_with_body" "$result"

# ---------------------------------------------------------------------------
# Tests: comment lines stripped (git inserts these)
# ---------------------------------------------------------------------------

msg_with_comments="feat: add login
# Please enter the commit message...
# Changes to be committed:
#   new file: login.py"

result=$(run_hook "$msg_with_comments")
assert_eq "git comment lines stripped" "feat: Add login" "$result"

# ---------------------------------------------------------------------------
# Cleanup and summary
# ---------------------------------------------------------------------------
rm -f "$TMPFILE"

TOTAL=$((PASS + FAIL))
printf '\n%d/%d tests passed\n' "$PASS" "$TOTAL"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
