#!/usr/bin/env bash
# normalize-commit-msg.sh
#
# Normalize a git commit message to conventional-commit format.
#
# Usage:
#   normalize-commit-msg.sh <file>        # git commit-msg hook mode (edits file in place)
#   normalize-commit-msg.sh               # reads from stdin, writes to stdout
#   echo "MSG" | normalize-commit-msg.sh  # pipe mode
#
# Normalization rules applied to the subject line (first line):
#   1. Type prefix must be one of: feat fix chore docs refactor test style perf ci build
#   2. Type is lowercased via tr
#   3. Separator must be ": " (colon + space)
#   4. Subject max 72 characters (truncated with warning if exceeded)
#   5. Trailing punctuation (. ! ?) stripped from subject

set -euo pipefail

VALID_TYPES="feat|fix|chore|docs|refactor|test|style|perf|ci|build"
MAX_SUBJECT_LEN=72

normalize_subject() {
    local subject="$1"

    # Extract type, optional scope, breaking-change marker, and description
    # Pattern: type[(scope)][!]: description
    local type scope bang description

    local pattern='^([A-Za-z]+)(\([^)]*\))?(!)?(:[[:space:]]*)(.*)$'
    if [[ "$subject" =~ $pattern ]]; then
        type="${BASH_REMATCH[1]}"
        scope="${BASH_REMATCH[2]}"
        bang="${BASH_REMATCH[3]}"
        description="${BASH_REMATCH[5]}"
    else
        # No recognizable type prefix — return as-is with warning
        echo "WARNING: Could not parse conventional-commit prefix in: $subject" >&2
        echo "$subject"
        return 0
    fi

    # Lowercase type via tr (no awk)
    local lower_type
    lower_type="$(echo "$type" | tr '[:upper:]' '[:lower:]')"

    if [[ ! "$lower_type" =~ ^(${VALID_TYPES})$ ]]; then
        echo "WARNING: Unknown commit type '${lower_type}'. Valid types: ${VALID_TYPES//|/, }" >&2
    fi

    # Strip trailing punctuation from description
    description="${description%[.!?]}"

    # Reassemble with normalized ": " separator
    local normalized="${lower_type}${scope}${bang}: ${description}"

    # Enforce max 72 chars (hard truncate)
    if [[ "${#normalized}" -gt "$MAX_SUBJECT_LEN" ]]; then
        echo "WARNING: Subject line exceeds ${MAX_SUBJECT_LEN} characters and will be truncated." >&2
        normalized="${normalized:0:${MAX_SUBJECT_LEN}}"
    fi

    echo "$normalized"
}

normalize_message() {
    local msg="$1"

    # Split into subject and body
    local subject body_part
    subject="$(echo "$msg" | head -n1)"
    body_part="$(echo "$msg" | tail -n +2)"

    local normalized_subject
    normalized_subject="$(normalize_subject "$subject")"

    if [[ -n "$body_part" ]]; then
        printf '%s\n%s' "$normalized_subject" "$body_part"
    else
        printf '%s' "$normalized_subject"
    fi
}

main() {
    if [[ $# -ge 1 && -f "$1" ]]; then
        # git commit-msg hook mode: file path provided
        local commit_file="$1"
        local original
        original="$(cat "$commit_file")"

        # Skip merge commits and fixup/squash commits
        if echo "$original" | grep -qE '^(Merge |fixup! |squash! )'; then
            exit 0
        fi

        local normalized
        normalized="$(normalize_message "$original")"

        printf '%s' "$normalized" > "$commit_file"
    else
        # stdin/stdout mode
        local input
        input="$(cat)"
        normalize_message "$input"
    fi
}

main "$@"
