"""Conventional Commits v1.0 message normalizer."""

import re
import sys

ALLOWED_TYPES = frozenset([
    "feat", "fix", "docs", "style", "refactor",
    "perf", "test", "build", "ci", "chore", "revert",
])

# Matches: type(scope)!: description  or  type!: description  or  type: description
HEADER_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)"
    r"(?:\((?P<scope>[^)]*)\))?"
    r"(?P<breaking>!)?"
    r": (?P<description>.+)$"
)

# Git trailer line: token: value  (RFC 2822-style)
TRAILER_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9-]*|BREAKING CHANGE): .+$")

MERGE_RE = re.compile(r"^Merge ", re.IGNORECASE)


def _is_trailer_block(lines: list[str]) -> bool:
    """Return True if every non-empty line looks like a git trailer."""
    non_empty = [l for l in lines if l.strip()]
    return bool(non_empty) and all(TRAILER_RE.match(l) for l in non_empty)


def _split_body_and_footer(paragraphs: list[list[str]]) -> tuple[list[list[str]], list[list[str]]]:
    """Split paragraphs into body paragraphs and footer/trailer paragraphs."""
    if not paragraphs:
        return [], []
    # The footer is the last paragraph(s) that are all trailers
    footer_start = len(paragraphs)
    for i in range(len(paragraphs) - 1, -1, -1):
        if _is_trailer_block(paragraphs[i]):
            footer_start = i
        else:
            break
    return paragraphs[:footer_start], paragraphs[footer_start:]


def _parse_paragraphs(text: str) -> list[list[str]]:
    """Split text into paragraphs (groups of lines separated by blank lines)."""
    paragraphs = []
    current: list[str] = []
    for line in text.splitlines():
        if line.strip() == "":
            if current:
                paragraphs.append(current)
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(current)
    return paragraphs


def normalize(message: str) -> str:
    """Normalize a commit message to the conventional commits v1.0 spec.

    Rules applied:
    - Merge commits pass through unchanged.
    - Header type is lowercased.
    - Unknown types are mapped to 'chore'.
    - Scope whitespace is trimmed.
    - Breaking-change marker (!) is preserved.
    - Trailing punctuation is stripped from the description.
    - First character of description is lowercased.
    - Subject line is truncated to 72 characters.
    - Unparseable headers are prefixed with 'chore: '.
    - Body paragraphs are preserved unchanged.
    - Git trailer footers are preserved unchanged.
    - Empty messages raise ValueError.
    """
    if not message or not message.strip():
        raise ValueError("commit message must not be empty")

    lines = message.splitlines()

    # Merge commit passthrough
    if MERGE_RE.match(lines[0].strip()):
        return message

    # Multi-line header: join continuation lines until blank line or trailer
    header_lines = [lines[0].rstrip()]
    i = 1
    while i < len(lines) and lines[i].strip() and not TRAILER_RE.match(lines[i]):
        header_lines.append(lines[i].strip())
        i += 1

    raw_header = " ".join(header_lines)
    rest_lines = lines[i:]

    match = HEADER_RE.match(raw_header.strip())
    if match:
        commit_type = match.group("type").lower()
        scope = match.group("scope")
        breaking = match.group("breaking") or ""
        description = match.group("description")

        if commit_type not in ALLOWED_TYPES:
            commit_type = "chore"

        if scope is not None:
            scope = scope.strip()

        # Normalize description
        description = description.strip()
        # Strip trailing punctuation (period only per conventional commits)
        description = description.rstrip(".")
        # Lowercase first char
        if description:
            description = description[0].lower() + description[1:]

        # Build subject
        if scope:
            subject = f"{commit_type}({scope}){breaking}: {description}"
        else:
            subject = f"{commit_type}{breaking}: {description}"

        # Truncate to 72 chars
        if len(subject) > 72:
            subject = subject[:72]
    else:
        # Unparseable header: prefix with chore:
        raw_stripped = raw_header.strip().rstrip(".")
        subject = f"chore: {raw_stripped}"
        if len(subject) > 72:
            subject = subject[:72]

    # Process body/footer from rest_lines
    rest_text = "\n".join(rest_lines)
    paragraphs = _parse_paragraphs(rest_text)
    body_paragraphs, footer_paragraphs = _split_body_and_footer(paragraphs)

    parts = [subject]
    if body_paragraphs or footer_paragraphs:
        parts.append("")  # blank line after subject
    for para in body_paragraphs:
        parts.extend(para)
        parts.append("")
    for para in footer_paragraphs:
        parts.extend(para)
        parts.append("")

    result = "\n".join(parts)
    # Remove trailing blank lines but preserve a single trailing newline if original had one
    result = result.rstrip("\n")
    if message.endswith("\n"):
        result += "\n"
    return result


def main() -> None:
    """CLI entry point for use as a git commit-msg hook."""
    if len(sys.argv) < 2:
        print("usage: normalize-commit-msg <commit-msg-file>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    # Strip comment lines (lines starting with #) for parsing
    content_lines = [l for l in original.splitlines() if not l.startswith("#")]
    content = "\n".join(content_lines).strip()

    if not content:
        # Empty or comment-only message — leave as-is (git will abort the commit)
        sys.exit(0)

    try:
        normalized = normalize(content)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(normalized)


if __name__ == "__main__":
    main()
