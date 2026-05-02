"""Conventional Commits message normalizer."""

import json
import os
import re
import subprocess

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

DEFAULT_CONFIG = {
    "rules": {
        "capitalize_subject": True,
        "strip_trailing_period": True,
        "normalize_type": True,
        "max_subject_length": MAX_SUBJECT_LEN,
    }
}


def load_config(start_dir=None):
    """Load commit-normalize.json from the repo root or start_dir.

    Returns a config dict with defaults merged with any file overrides.
    """
    config = {
        "rules": dict(DEFAULT_CONFIG["rules"]),
    }

    search_dir = start_dir or _repo_root() or os.getcwd()
    config_path = os.path.join(search_dir, "commit-normalize.json")

    if os.path.isfile(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as fh:
                overrides = json.load(fh)
            if isinstance(overrides.get("rules"), dict):
                config["rules"].update(overrides["rules"])
        except (OSError, json.JSONDecodeError):
            pass

    return config


def _repo_root():
    """Return the git repository root, or None if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except OSError:
        pass
    return None


def normalize(message: str, config=None) -> str:
    """Normalize a commit message to Conventional Commits format."""
    if config is None:
        config = DEFAULT_CONFIG

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


def _is_footer_paragraph(para):
    """Return True only if every line in para looks like a git trailer.

    Single-line paragraphs that match the conventional commit header format
    (e.g. 'fix: some body prose') are treated as body, not footer, because
    they are almost certainly prose rather than git trailers.
    """
    if not para:
        return False
    # A single line matching the conventional commit header pattern is body, not footer.
    if len(para) == 1 and HEADER_RE.match(para[0]):
        return False
    return all(_TRAILER_RE.match(line) for line in para)


def _normalize_header(header: str, config=None) -> str:
    if config is None:
        config = DEFAULT_CONFIG
    rules = config.get("rules", DEFAULT_CONFIG["rules"])
    max_len = rules.get("max_subject_length", MAX_SUBJECT_LEN)

    m = HEADER_RE.match(header)
    if not m:
        # Cannot parse - wrap as chore
        description = header
        if rules.get("strip_trailing_period", True):
            description = description.rstrip(".")
        prefix = "chore: "
        description = _truncate_description(prefix, description, max_len)
        if rules.get("capitalize_subject", True):
            description = _capitalize(description)
        return f"{prefix}{description}"

    if rules.get("normalize_type", True):
        commit_type = m.group("type").lower()
    else:
        commit_type = m.group("type")

    scope = m.group("scope")
    breaking = m.group("breaking") or ""
    description = m.group("description").strip()

    if rules.get("normalize_type", True) and commit_type not in VALID_TYPES:
        commit_type = "chore"

    # Normalize scope whitespace; discard whitespace-only scopes
    if scope is not None:
        scope = scope.strip()
        if not scope:
            scope = None

    if rules.get("strip_trailing_period", True):
        description = description.rstrip(".")

    # Build subject line and truncate
    scope_str = f"({scope})" if scope else ""
    prefix = f"{commit_type}{scope_str}{breaking}: "
    description = _truncate_description(prefix, description, max_len)

    if rules.get("capitalize_subject", True):
        description = _capitalize(description)

    return f"{prefix}{description}"


def _capitalize(text: str) -> str:
    """Capitalize the first character of text, leaving the rest unchanged."""
    if not text:
        return text
    return text[0].upper() + text[1:]


def _truncate_description(prefix: str, description: str, max_len: int = MAX_SUBJECT_LEN) -> str:
    """Truncate description so that prefix+description fits within max_len."""
    available = max_len - len(prefix)
    if len(description) <= available:
        return description
    truncated = description[:available].rstrip(".")
    return truncated


def _truncate(text: str) -> str:
    """Truncate text to MAX_SUBJECT_LEN, stripping trailing period."""
    if len(text) <= MAX_SUBJECT_LEN:
        return text
    return text[:MAX_SUBJECT_LEN].rstrip(".")
