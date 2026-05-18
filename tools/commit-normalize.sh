#!/usr/bin/env bash
# commit-normalize.sh - git commit-msg hook
# Normalizes commit messages to conventional-commits format.
#
# Usage:
#   As a git hook:  .git/hooks/commit-msg (called automatically by git)
#   Standalone:     bash tools/commit-normalize.sh <commit-msg-file>
#                   echo "FEAT: add thing" | bash tools/commit-normalize.sh
#
# Normalizations applied:
#   - Skips merge and fixup commits without modification
#   - Lowercases the type token (e.g., FEAT -> feat)
#   - Normalizes separator to ": " (removes extra spaces around colon)
#   - Truncates subject line to 72 characters
#   - Strips trailing punctuation (period) from subject line
#
# Exits non-zero with an error message if the message cannot be
# normalized into conventional-commits format.

set -euo pipefail

CONVENTIONAL_COMMITS_TYPES="feat|fix|chore|docs|refactor|test|ci|style|perf|build|revert"
MAX_SUBJECT_LEN=72

# Read commit message: from file argument or stdin
if [[ $# -ge 1 ]]; then
    MSG_FILE="$1"
    msg=$(cat "$MSG_FILE")
else
    msg=$(cat)
    MSG_FILE=""
fi

# Extract subject line (first non-empty line)
subject=$(printf '%s\n' "$msg" | head -n1)
rest=$(printf '%s\n' "$msg" | tail -n +2)

# Skip merge commits
if printf '%s\n' "$subject" | grep -qiE '^Merge '; then
    exit 0
fi

# Skip fixup/squash commits
if printf '%s\n' "$subject" | grep -qiE '^(fixup|squash)!'; then
    exit 0
fi

# Lowercase the type token before the colon
# Match: optional leading whitespace, type, optional (scope), optional !, colon
# Store pattern in variable to avoid bash parsing issues with ) in [[ =~ ]]
CONV_PATTERN='^([[:space:]]*)([A-Za-z]+)(\([^)]*\))?(!)?(:[[:space:]]*)(.*)$'
if [[ "$subject" =~ $CONV_PATTERN ]]; then
    leading="${BASH_REMATCH[1]}"
    type_token="${BASH_REMATCH[2]}"
    scope="${BASH_REMATCH[3]}"
    breaking="${BASH_REMATCH[4]}"
    sep="${BASH_REMATCH[5]}"
    desc="${BASH_REMATCH[6]}"

    # Lowercase the type
    type_lower=$(printf '%s' "$type_token" | tr '[:upper:]' '[:lower:]')

    # Validate type against known conventional-commits types
    if ! printf '%s' "$type_lower" | grep -qE "^($CONVENTIONAL_COMMITS_TYPES)$"; then
        printf 'error: commit type "%s" is not a recognized conventional-commits type\n' "$type_lower" >&2
        printf 'accepted types: %s\n' "$CONVENTIONAL_COMMITS_TYPES" >&2
        exit 1
    fi

    # Normalize separator to exactly ": "
    subject="${leading}${type_lower}${scope}${breaking}: ${desc}"
else
    printf 'error: commit message does not match conventional-commits format\n' >&2
    printf 'expected: <type>[(<scope>)][!]: <description>\n' >&2
    printf 'example:  feat(auth): add oauth2 login\n' >&2
    exit 1
fi

# Strip trailing period from subject line
subject="${subject%.}"

# Truncate subject line to MAX_SUBJECT_LEN characters
if [[ ${#subject} -gt $MAX_SUBJECT_LEN ]]; then
    subject="${subject:0:$MAX_SUBJECT_LEN}"
fi

# Reconstruct full message
if [[ -n "$rest" ]]; then
    normalized_msg="${subject}
${rest}"
else
    normalized_msg="$subject"
fi

# Write back to file or stdout
if [[ -n "$MSG_FILE" ]]; then
    printf '%s\n' "$normalized_msg" > "$MSG_FILE"
else
    printf '%s\n' "$normalized_msg"
fi
