"""Commit message normalizer enforcing conventional commit standards."""

import re

CONVENTIONAL_TYPES = {
    "feat", "fix", "chore", "docs", "refactor",
    "test", "style", "perf", "ci",
}

SUBJECT_MAX_LEN = 72

TYPE_PATTERN = re.compile(
    r"^(?P<type>[a-z]+)(?P<scope>\([^)]*\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)


def _guess_type(subject: str) -> str:
    """Return the best-guess conventional type for a bare subject line."""
    lower = subject.lower()
    if lower.startswith(("fix", "bug", "patch", "resolve")):
        return "fix"
    if lower.startswith(("add", "new", "feat", "implement", "create")):
        return "feat"
    if lower.startswith(("doc", "readme", "comment")):
        return "docs"
    if lower.startswith(("refactor", "clean", "restructure", "move", "rename")):
        return "refactor"
    if lower.startswith(("test", "spec")):
        return "test"
    if lower.startswith(("style", "format", "lint")):
        return "style"
    if lower.startswith(("perf", "optim", "speed")):
        return "perf"
    if lower.startswith(("ci", "pipeline", "deploy", "workflow")):
        return "ci"
    return "chore"


def _capitalize_first(text: str) -> str:
    """Capitalize the first character of text without changing the rest."""
    if not text:
        return text
    return text[0].upper() + text[1:]


def normalize(message: str) -> str:
    """
    Normalize a git commit message.

    Rules applied:
    1. Strip leading/trailing whitespace from each line.
    2. Enforce conventional-commit type prefix.
    3. Capitalize first word of description.
    4. Trim subject line to SUBJECT_MAX_LEN characters.
    5. Remove trailing period from subject line.
    6. Ensure blank line between subject and body when body is present.
    """
    lines = message.splitlines()

    # Strip whitespace from all lines and drop trailing blank lines.
    lines = [line.rstrip() for line in lines]
    while lines and not lines[-1]:
        lines.pop()

    if not lines:
        return ""

    subject = lines[0].strip()

    # Determine body lines (everything after the subject, skipping leading blanks).
    raw_body = lines[1:]

    # Strip the leading blank line separator if already present.
    while raw_body and not raw_body[0]:
        raw_body = raw_body[1:]

    # --- Enforce type prefix ---
    match = TYPE_PATTERN.match(subject)
    if match:
        typ = match.group("type")
        scope = match.group("scope") or ""
        breaking = match.group("breaking") or ""
        desc = match.group("desc").strip()

        # Replace unknown types with best guess based on description.
        if typ not in CONVENTIONAL_TYPES:
            typ = _guess_type(desc)

        desc = _capitalize_first(desc)

        # Remove trailing period (but not ellipsis).
        if desc.endswith(".") and not desc.endswith("..."):
            desc = desc[:-1]

        subject = f"{typ}{scope}{breaking}: {desc}"
    else:
        # No type prefix found - infer one from the raw subject.
        desc = _capitalize_first(subject.strip())
        if desc.endswith(".") and not desc.endswith("..."):
            desc = desc[:-1]
        typ = _guess_type(desc)
        subject = f"{typ}: {desc}"

    # --- Trim subject to max length ---
    if len(subject) > SUBJECT_MAX_LEN:
        subject = subject[:SUBJECT_MAX_LEN]

    # --- Assemble final message ---
    if raw_body:
        body_text = "\n".join(raw_body)
        return f"{subject}\n\n{body_text}"

    return subject
