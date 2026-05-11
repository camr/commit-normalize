"""Conventional Commits message normalizer."""

import json
import os
import re

VALID_TYPES = {
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "build", "ci", "chore", "revert",
}

TYPE_ALIASES = {
    "feature": "feat",
    "bugfix": "fix",
    "hotfix": "fix",
    "documentation": "docs",
    "refactoring": "refactor",
    "performance": "perf",
    "testing": "test",
    "infrastructure": "ci",
}

HEADER_RE = re.compile(
    r"^(?P<type>[a-zA-Z]+)"
    r"(?:\((?P<scope>[^)]*)\))?"
    r"(?P<breaking>!)?"
    r":\s*(?P<description>.+)$"
)

MAX_SUBJECT_LEN = 72

_CONFIG_DEFAULTS = {
    "capitalize_subject": False,
    "strip_trailing_period": True,
    "max_subject_length": 72,
    "normalize_type": True,
}


def load_config(config_path=None):
    """Load per-repo rule config from commit-normalize.json.

    Searches for commit-normalize.json at config_path, or in the current
    working directory. Missing keys fall back to _CONFIG_DEFAULTS.
    """
    if config_path is None:
        config_path = os.path.join(os.getcwd(), "commit-normalize.json")
    config = dict(_CONFIG_DEFAULTS)
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            user_config = json.load(fh)
        config.update({k: v for k, v in user_config.items() if k in _CONFIG_DEFAULTS})
    except (OSError, ValueError):
        pass
    return config


def normalize(message: str, config=None) -> str:
    """Normalize a commit message to Conventional Commits format."""
    if config is None:
        config = load_config()
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

    normalized_header = _normalize_header(header, config)

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


def _is_trailer_line(line):
    """Return True if the line is a git trailer but NOT a conventional commit subject."""
    # A line that matches the conventional commit header pattern with a known
    # type is a subject line, not a git trailer (e.g. "fix: body prose").
    m = HEADER_RE.match(line)
    if m and m.group("type").lower() in VALID_TYPES:
        return False
    return bool(_TRAILER_RE.match(line))


def _is_footer_paragraph(para):
    """Return True only if every line in para looks like a git trailer."""
    if not para:
        return False
    return all(_is_trailer_line(line) for line in para)


def _normalize_header(header: str, config: dict) -> str:
    max_len = config.get("max_subject_length", MAX_SUBJECT_LEN)

    m = HEADER_RE.match(header)
    if not m:
        # Cannot parse - wrap as chore
        description = header.rstrip(".") if config.get("strip_trailing_period", True) else header
        if config.get("capitalize_subject", False) and description:
            description = description[0].upper() + description[1:]
        description = _truncate(description, max_len)
        return f"chore: {description}"

    commit_type = m.group("type").lower() if config.get("normalize_type", True) else m.group("type")
    scope = m.group("scope")
    breaking = m.group("breaking") or ""
    description = m.group("description").strip()

    if config.get("normalize_type", True):
        commit_type = TYPE_ALIASES.get(commit_type, commit_type)
        if commit_type not in VALID_TYPES:
            commit_type = "chore"

    # Normalize scope whitespace; discard whitespace-only scopes
    if scope is not None:
        scope = scope.strip()
        if not scope:
            scope = None

    # Strip trailing period from description
    if config.get("strip_trailing_period", True):
        description = description.rstrip(".")

    # Capitalize first letter of description
    if config.get("capitalize_subject", False) and description:
        description = description[0].upper() + description[1:]

    # Build subject line and truncate
    scope_str = f"({scope})" if scope else ""
    prefix = f"{commit_type}{scope_str}{breaking}: "
    description = _truncate_description(prefix, description, max_len)

    return f"{prefix}{description}"


def _truncate_description(prefix: str, description: str, max_len: int = MAX_SUBJECT_LEN) -> str:
    """Truncate description so that prefix+description fits within max_len."""
    available = max_len - len(prefix)
    if len(description) <= available:
        return description
    truncated = description[:available].rstrip(".")
    return truncated


def _truncate(text: str, max_len: int = MAX_SUBJECT_LEN) -> str:
    """Truncate text to max_len, stripping trailing period."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip(".")
