#!/usr/bin/env python3
"""Conventional-commits commit message normalizer for use as a git commit-msg hook."""

import re
import sys
import textwrap

MAX_LINE = 72

# Matches: type(scope)!: description  or  type!: description  or  type: description
CONVENTIONAL_SUBJECT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)

VALID_TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
}


def _strip_comments(msg: str) -> str:
    """Remove lines starting with '#' (git verbose/annotated comment lines)."""
    lines = [line for line in msg.splitlines() if not line.startswith("#")]
    return "\n".join(lines)


def _wrap_body(text: str) -> str:
    """Wrap body text at 72 chars, preserving paragraph structure."""
    result_lines = []
    current_block: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current_block:
                wrapped = textwrap.fill(" ".join(current_block), MAX_LINE)
                result_lines.extend(wrapped.splitlines())
                current_block = []
            result_lines.append("")
        else:
            current_block.append(stripped)

    if current_block:
        wrapped = textwrap.fill(" ".join(current_block), MAX_LINE)
        result_lines.extend(wrapped.splitlines())

    # Remove trailing blank lines added by the loop
    while result_lines and not result_lines[-1]:
        result_lines.pop()

    return "\n".join(result_lines)


def _normalize_subject(subject: str) -> str:
    """Apply normalization rules to the subject line."""
    subject = subject.strip()

    m = CONVENTIONAL_SUBJECT_RE.match(subject)
    if m:
        type_ = m.group("type")
        scope = m.group("scope")
        breaking = m.group("breaking") or ""
        desc = m.group("desc").strip()

        if type_ not in VALID_TYPES:
            print(
                f"warning: unrecognized conventional commit type '{type_}'; "
                f"expected one of: {', '.join(sorted(VALID_TYPES))}",
                file=sys.stderr,
            )

        # Capitalize first word of description
        if desc:
            desc = desc[0].upper() + desc[1:]

        # Remove trailing period
        desc = desc.rstrip(".")

        if scope is not None:
            subject = f"{type_}({scope}){breaking}: {desc}"
        else:
            subject = f"{type_}{breaking}: {desc}"
    else:
        # Non-conventional subject: apply capitalization and period removal
        # to the whole subject so behavior is consistent and explicit.
        if subject:
            subject = subject[0].upper() + subject[1:]
        subject = subject.rstrip(".")

    # Trim to 72 chars at a word boundary to avoid mid-word cuts.
    if len(subject) > MAX_LINE:
        truncated = subject[:MAX_LINE]
        last_space = truncated.rfind(" ")
        subject = truncated[:last_space] if last_space > 0 else truncated

    return subject


def normalize(msg: str) -> str:
    """Normalize a commit message to conventional-commits style.

    Rules applied:
    - Git comment lines (starting with '#') are stripped before processing.
    - Subject first word capitalized.
    - No trailing period on subject.
    - Subject trimmed to 72 chars at a word boundary.
    - Blank line between subject and body enforced.
    - Body lines wrapped at 72 chars.
    """
    msg = _strip_comments(msg)
    msg = msg.strip()
    if not msg:
        return msg

    lines = msg.splitlines()
    subject = _normalize_subject(lines[0])

    if len(lines) < 2:
        return subject

    rest = lines[1:]

    # Skip any leading blank lines from the original body.
    start = 0
    while start < len(rest) and not rest[start].strip():
        start += 1

    body_lines = rest[start:]
    if not body_lines:
        return subject

    body_text = "\n".join(body_lines)
    normalized_body = _wrap_body(body_text)

    return subject + "\n\n" + normalized_body


def main() -> None:
    """CLI entry point: reads from a file path arg (git hook) or stdin."""
    import difflib

    args = sys.argv[1:]
    check_mode = "--check" in args
    file_args = [a for a in args if a != "--check"]

    if file_args:
        path = file_args[0]
        with open(path, encoding="utf-8") as fh:
            msg = fh.read()
        normalized = normalize(msg)
        if check_mode:
            # Already normalized means normalize() produces no change to the
            # meaningful content (ignoring a single trailing newline).
            if normalized == msg.rstrip("\n") or normalized + "\n" == msg:
                sys.exit(0)
            diff = difflib.unified_diff(
                msg.splitlines(keepends=True),
                (normalized + "\n").splitlines(keepends=True),
                fromfile="original",
                tofile="normalized",
            )
            sys.stdout.writelines(diff)
            sys.exit(1)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(normalized)
    else:
        msg = sys.stdin.read()
        normalized = normalize(msg)
        if check_mode:
            if normalized == msg.rstrip("\n") or normalized + "\n" == msg:
                sys.exit(0)
            diff = difflib.unified_diff(
                msg.splitlines(keepends=True),
                (normalized + "\n").splitlines(keepends=True),
                fromfile="original",
                tofile="normalized",
            )
            sys.stdout.writelines(diff)
            sys.exit(1)
        sys.stdout.write(normalized)


if __name__ == "__main__":
    main()
