#!/usr/bin/env python3
"""Normalize a git commit message to Conventional Commits format.

Used as a git commit-msg hook: receives the path to the commit message file
as its sole argument, normalizes the message in place, and exits non-zero on
any validation error that should block the commit.
"""

import re
import sys

VALID_TYPES = frozenset({
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
})

# Named group for breaking-change ! so it is always preserved in the rebuild.
CONVENTIONAL_RE = re.compile(
    r"^(?P<type>[a-z]+)"
    r"(?:\((?P<scope>[^)]+)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<desc>.+)$"
)

MAX_SUBJECT_LEN = 72


class NormalizationError(Exception):
    """Base class for commit message normalization errors."""


class UnknownTypeError(NormalizationError):
    """Raised when the commit type is not in VALID_TYPES."""


class MissingFormatError(NormalizationError):
    """Raised when the message subject lacks conventional commit structure."""


def normalize_subject(line: str) -> str:
    """Normalize the subject line, raising NormalizationError on failure."""
    line = line.strip()
    m = CONVENTIONAL_RE.match(line)
    if not m:
        raise MissingFormatError(
            f"subject must follow type(scope): description format; got: {line!r}"
        )

    ctype = m.group("type")
    if ctype not in VALID_TYPES:
        raise UnknownTypeError(
            f"unknown commit type {ctype!r}; valid types: {', '.join(sorted(VALID_TYPES))}"
        )

    scope = m.group("scope")
    breaking = m.group("breaking") or ""
    desc = m.group("desc").strip()

    # Normalize scope whitespace; drop whitespace-only scopes
    if scope is not None:
        scope = scope.strip() or None

    # Capitalize first letter of description
    if desc:
        desc = desc[0].upper() + desc[1:]

    # Strip trailing periods only; ! has semantic meaning in descriptions
    desc = desc.rstrip(".")

    # Build prefix, then truncate description to fit within MAX_SUBJECT_LEN
    scope_part = f"({scope})" if scope else ""
    prefix = f"{ctype}{scope_part}{breaking}: "
    max_desc_len = MAX_SUBJECT_LEN - len(prefix)
    if len(desc) > max_desc_len:
        desc = desc[:max_desc_len].rstrip(".")

    return f"{prefix}{desc}"


def normalize_message(message: str) -> str:
    """Normalize a full commit message and return the result.

    Passes through unchanged when the message contains only git comment lines
    (lines starting with #), since git will abort such commits itself.
    Raises NormalizationError for malformed subjects.
    """
    lines = message.splitlines()

    # Exclude git comment lines inserted by --verbose / --edit
    content_lines = [l for l in lines if not l.startswith("#")]
    has_comments = any(l.startswith("#") for l in lines)
    has_content = any(l.strip() for l in content_lines)

    # Comment-only messages (e.g. git commit --verbose with no edits) pass
    # through unchanged; git will abort the commit itself.
    if not has_content:
        if has_comments:
            return message
        raise NormalizationError("commit message must not be empty")

    subject_line = normalize_subject(content_lines[0])

    # Preserve body: everything after line 0, stripping leading blank lines
    body_lines = content_lines[1:]
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)

    if body_lines:
        return subject_line + "\n\n" + "\n".join(body_lines).rstrip()
    return subject_line


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: normalize_commit.py <commit-msg-file>", file=sys.stderr)
        return 1

    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        original = f.read()

    try:
        normalized = normalize_message(original)
    except NormalizationError as exc:
        print(f"commit-msg: {exc}", file=sys.stderr)
        return 1

    with open(path, "w", encoding="utf-8") as f:
        f.write(normalized)
    return 0


if __name__ == "__main__":
    sys.exit(main())
