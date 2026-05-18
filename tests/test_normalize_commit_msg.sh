#!/usr/bin/env bash
# test_normalize_commit_msg.sh
#
# Unit tests for normalize-commit-msg.sh
# Run directly: bash tests/test_normalize_commit_msg.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NORMALIZER="${SCRIPT_DIR}/../scripts/normalize-commit-msg.sh"

PASS=0
FAIL=0

run_test() {
    local name="$1"
    local input="$2"
    local expected="$3"

    local actual
    actual="$(echo "$input" | "$NORMALIZER" 2>/dev/null)"

    if [[ "$actual" == "$expected" ]]; then
        echo "  PASS: $name"
        PASS=$(( PASS + 1 ))
    else
        echo "  FAIL: $name"
        echo "        Input:    $input"
        echo "        Expected: $expected"
        echo "        Got:      $actual"
        FAIL=$(( FAIL + 1 ))
    fi
}

echo "=== normalize-commit-msg tests ==="
echo ""

# Test 1: already-valid message passes unchanged
run_test "valid message unchanged" \
    "feat: add login endpoint" \
    "feat: add login endpoint"

# Test 2: uppercase type gets lowercased
run_test "uppercase type lowercased" \
    "FEAT: add login endpoint" \
    "feat: add login endpoint"

# Test 3: mixed case type gets lowercased
run_test "mixed case type lowercased" \
    "Fix: handle null pointer" \
    "fix: handle null pointer"

# Test 4: missing space after colon gets fixed
run_test "missing space after colon fixed" \
    "feat:add login endpoint" \
    "feat: add login endpoint"

# Test 5: extra spaces after colon normalized
run_test "extra spaces after colon normalized" \
    "feat:  add login endpoint" \
    "feat: add login endpoint"

# Test 6: trailing period gets removed
run_test "trailing period removed" \
    "fix: handle null pointer." \
    "fix: handle null pointer"

# Test 7: trailing exclamation mark gets removed
run_test "trailing exclamation mark removed" \
    "chore: update dependencies!" \
    "chore: update dependencies"

# Test 8: trailing question mark gets removed
run_test "trailing question mark removed" \
    "docs: update readme?" \
    "docs: update readme"

# Test 9: subject over 72 chars gets truncated
long_input="feat: $(python3 -c "print('a' * 80)")"
actual_len="$(echo "$long_input" | "$NORMALIZER" 2>/dev/null | wc -c | tr -d ' ')"
if [[ "$actual_len" -le 73 ]]; then  # 72 chars + newline
    echo "  PASS: long subject truncated to <=72 chars (got $((actual_len - 1)) chars)"
    PASS=$(( PASS + 1 ))
else
    echo "  FAIL: long subject not truncated (got $((actual_len - 1)) chars)"
    FAIL=$(( FAIL + 1 ))
fi

# Test 10: scope preserved
run_test "scope preserved" \
    "feat(auth): add login endpoint" \
    "feat(auth): add login endpoint"

# Test 11: breaking change marker preserved
run_test "breaking change marker preserved" \
    "feat!: remove deprecated api" \
    "feat!: remove deprecated api"

# Test 12: scope + breaking change preserved
run_test "scope and breaking change preserved" \
    "feat(api)!: remove v1 endpoints" \
    "feat(api)!: remove v1 endpoints"

# Test 13: body preserved after subject
run_test "body preserved" \
    "$(printf 'feat: add feature\n\nThis is the body.')" \
    "$(printf 'feat: add feature\n\nThis is the body.')"

# Test 14: uppercase type with trailing period (combined normalization)
run_test "uppercase type and trailing period" \
    "FIX: resolve crash on startup." \
    "fix: resolve crash on startup"

# Test 15: merge commit skipped (file mode)
tmpfile="$(mktemp)"
echo "Merge branch 'main' into feature/foo" > "$tmpfile"
"$NORMALIZER" "$tmpfile"
merge_result="$(cat "$tmpfile")"
if [[ "$merge_result" == "Merge branch 'main' into feature/foo" ]]; then
    echo "  PASS: merge commit skipped unchanged"
    PASS=$(( PASS + 1 ))
else
    echo "  FAIL: merge commit was modified (got: $merge_result)"
    FAIL=$(( FAIL + 1 ))
fi
rm -f "$tmpfile"

# Test 16: fixup commit skipped (file mode)
tmpfile="$(mktemp)"
echo "fixup! feat: previous commit" > "$tmpfile"
"$NORMALIZER" "$tmpfile"
fixup_result="$(cat "$tmpfile")"
if [[ "$fixup_result" == "fixup! feat: previous commit" ]]; then
    echo "  PASS: fixup commit skipped unchanged"
    PASS=$(( PASS + 1 ))
else
    echo "  FAIL: fixup commit was modified (got: $fixup_result)"
    FAIL=$(( FAIL + 1 ))
fi
rm -f "$tmpfile"

# Test 17: file mode normalizes in place
tmpfile="$(mktemp)"
echo "FEAT: add something." > "$tmpfile"
"$NORMALIZER" "$tmpfile"
file_result="$(cat "$tmpfile")"
if [[ "$file_result" == "feat: add something" ]]; then
    echo "  PASS: file mode normalizes in place"
    PASS=$(( PASS + 1 ))
else
    echo "  FAIL: file mode did not normalize (got: $file_result)"
    FAIL=$(( FAIL + 1 ))
fi
rm -f "$tmpfile"

# Test 18-27: all valid types accepted
echo ""
echo "--- type validation ---"
for t in feat fix chore docs refactor test style perf ci build; do
    actual="$(echo "${t}: do something" | "$NORMALIZER" 2>/dev/null)"
    expected="${t}: do something"
    if [[ "$actual" == "$expected" ]]; then
        echo "  PASS: type '${t}' accepted"
        PASS=$(( PASS + 1 ))
    else
        echo "  FAIL: type '${t}' rejected (got: $actual)"
        FAIL=$(( FAIL + 1 ))
    fi
done

echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed ==="

[[ "$FAIL" -eq 0 ]]
