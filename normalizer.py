"""Conventional Commits message normalizer."""

import re

# The complete set of Conventional Commits type tokens.  Any type not in this
# set is remapped to "chore" during normalization.
VALID_TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
}

# Regex that parses a Conventional Commits header line into its named groups:
# type, optional scope, optional breaking-change marker (!), and description.
HEADER_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)"
    r"(?:\((?P<scope>[^)]*)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<description>.+)$"
)

# Maximum allowed length (characters) for the normalized subject line,
# matching the 72-character convention widely used by git tooling.
MAX_SUBJECT_LEN = 72


def normalize(message: str) -> str:
    """Normalize a commit message to Conventional Commits format."""
    if not message or not message.strip():
        raise ValueError("commit message must not be empty")

    lines = message.splitlines()

    # Split into paragraphs separated by blank lines
    paragraphs = _split_paragraphs(lines)
    if not paragraphs:
        raise ValueError("commit message must not be empty")

    header_lines = paragraphs[0]
    rest_paragraphs = paragraphs[1:]

    header = " ".join(line.strip() for line in header_lines if line.strip())

    normalized_header = _normalize_header(header)

    # Separate body paragraphs from footer paragraphs
    # Footer paragraphs consist entirely of git trailer lines (token: value or token #value)
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
        parts.extend(para)
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


def _is_footer_paragraph(para):
    """Return True only if every line in para looks like a git trailer."""
    if not para:
        return False
    return all(_TRAILER_RE.match(line) for line in para)


def _normalize_header(header: str) -> str:
    """Parse and normalize a single Conventional Commits header line.

    Steps performed:
    1. Attempt to match the header against HEADER_RE.  If the match fails the
       entire header is treated as a plain description and wrapped as
       ``chore: <description>``.
    2. The commit type is lowercased.  If it is not in VALID_TYPES it is
       replaced with ``chore``.
    3. Trailing periods are stripped from the description.
    4. The breaking-change marker (``!``) is preserved when present.
    5. The final subject line is truncated to MAX_SUBJECT_LEN characters.
    """
    m = HEADER_RE.match(header)
    if not m:
        # Cannot parse - wrap as chore
        description = header.rstrip(".")
        description = _truncate(description)
        return f"chore: {description}"

    commit_type = m.group("type").lower()
    scope = m.group("scope")
    breaking = m.group("breaking") or ""
    description = m.group("description").strip()

    if commit_type not in VALID_TYPES:
        commit_type = "chore"

    # Normalize scope whitespace; discard whitespace-only scopes
    if scope is not None:
        scope = scope.strip()
        if not scope:
            scope = None

    # Strip trailing period from description
    description = description.rstrip(".")

    # Build subject line and truncate
    scope_str = f"({scope})" if scope else ""
    prefix = f"{commit_type}{scope_str}{breaking}: "
    description = _truncate_description(prefix, description)

    return f"{prefix}{description}"


def _truncate_description(prefix: str, description: str) -> str:
    """Truncate description so that prefix+description fits within MAX_SUBJECT_LEN."""
    available = MAX_SUBJECT_LEN - len(prefix)
    if len(description) <= available:
        return description
    truncated = description[:available].rstrip(".")
    return truncated


def _truncate(text: str) -> str:
    """Truncate text to MAX_SUBJECT_LEN, stripping trailing period."""
    if len(text) <= MAX_SUBJECT_LEN:
        return text
    return text[:MAX_SUBJECT_LEN].rstrip(".")
