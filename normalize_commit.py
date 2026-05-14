"""Conventional Commits message normalizer."""

import re
import textwrap

VALID_TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
}

HEADER_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)"
    r"(?:\((?P<scope>[^)]*)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<description>.+)$"
)

MAX_SUBJECT_LEN = 72
BODY_WRAP_LEN = 72


class NormalizationError(ValueError):
    """Raised when a commit message cannot be normalized."""


def normalize(message: str) -> str:
    """Normalize a commit message to Conventional Commits format.

    Rules applied:
    - Strip leading/trailing whitespace from all lines
    - Enforce type(scope): description subject format via regex
    - Lowercase the type token
    - Capitalize first letter of description
    - Strip trailing period from subject line
    - Ensure blank line between subject and body
    - Wrap body lines at 72 characters
    - Unknown types raise NormalizationError
    """
    if not message or not message.strip():
        raise NormalizationError("commit message must not be empty")

    lines = [line.rstrip() for line in message.splitlines()]

    paragraphs = _split_paragraphs(lines)
    if not paragraphs:
        raise NormalizationError("commit message must not be empty")

    header_lines = paragraphs[0]
    rest_paragraphs = paragraphs[1:]

    # If the first paragraph has multiple lines and the first line parses as a
    # conventional commit subject, treat only that line as the header and the
    # remaining lines as an additional body paragraph (blank line was missing).
    if len(header_lines) > 1 and HEADER_RE.match(header_lines[0].strip()):
        extra_body = header_lines[1:]
        header_lines = [header_lines[0]]
        rest_paragraphs = [extra_body] + rest_paragraphs

    header = " ".join(line.strip() for line in header_lines if line.strip())
    normalized_header = _normalize_header(header)

    body_paragraphs = []
    footer_paragraphs = []
    found_footer = False

    for para in rest_paragraphs:
        if not found_footer and _is_footer_paragraph(para):
            found_footer = True
        if found_footer:
            footer_paragraphs.append(para)
        else:
            body_paragraphs.append(para)

    parts = [normalized_header]
    for para in body_paragraphs:
        parts.append("")
        wrapped = _wrap_paragraph(para)
        parts.extend(wrapped)
    for para in footer_paragraphs:
        parts.append("")
        parts.extend(para)

    return "\n".join(parts)


def _split_paragraphs(lines):
    """Split lines into paragraphs separated by blank lines."""
    paragraphs = []
    current = []
    for line in lines:
        if line.strip() == "":
            if current:
                paragraphs.append(current)
                current = []
        else:
            current.append(line)
    if current:
        paragraphs.append(current)
    return paragraphs


_TRAILER_RE = re.compile(r"^[\w-]+(?:\s[\w-]+)*\s*:(?:\s|$)|^[\w-]+\s#")


def _is_trailer_line(line):
    """Return True if the line is a git trailer but NOT a conventional commit subject."""
    m = HEADER_RE.match(line)
    if m and m.group("type").lower() in VALID_TYPES:
        return False
    return bool(_TRAILER_RE.match(line))


def _is_footer_paragraph(para):
    """Return True only if every line in para looks like a git trailer."""
    if not para:
        return False
    return all(_is_trailer_line(line) for line in para)


def _wrap_paragraph(para):
    """Wrap a list of body lines at BODY_WRAP_LEN characters."""
    joined = " ".join(line.strip() for line in para)
    wrapped = textwrap.wrap(joined, width=BODY_WRAP_LEN)
    return wrapped if wrapped else para


def _normalize_header(header: str) -> str:
    m = HEADER_RE.match(header)
    if not m:
        # Cannot parse as conventional commit
        description = header.rstrip(".")
        description = description[0].upper() + description[1:] if description else description
        description = _truncate(description, MAX_SUBJECT_LEN - len("chore: "))
        return f"chore: {description}"

    commit_type = m.group("type").lower()
    scope = m.group("scope")
    breaking = m.group("breaking") or ""
    description = m.group("description").strip()

    if commit_type not in VALID_TYPES:
        raise NormalizationError(
            f"unknown commit type '{commit_type}': must be one of {sorted(VALID_TYPES)}"
        )

    if scope is not None:
        scope = scope.strip()
        if not scope:
            scope = None

    description = description.rstrip(".")

    if description:
        description = description[0].upper() + description[1:]

    scope_str = f"({scope})" if scope else ""
    prefix = f"{commit_type}{scope_str}{breaking}: "
    available = MAX_SUBJECT_LEN - len(prefix)
    if len(description) > available:
        description = description[:available].rstrip(".")

    return f"{prefix}{description}"


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip(".")


def _main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Normalize a commit message.")
    parser.add_argument("file", nargs="?", help="commit message file to read")
    parser.add_argument(
        "--in-place", "-i", action="store_true",
        help="rewrite the file in place after normalizing"
    )
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            message = fh.read()
    else:
        message = sys.stdin.read()

    try:
        result = normalize(message)
    except NormalizationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.in_place and args.file:
        with open(args.file, "w", encoding="utf-8") as fh:
            fh.write(result + "\n")
    else:
        print(result)


if __name__ == "__main__":
    _main()
