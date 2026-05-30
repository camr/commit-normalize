#!/usr/bin/env python3
"""Standalone git commit-msg hook: normalizes messages to conventional commit format."""

import re
import sys

SUBJECT_MAX_LEN = 72

CONVENTIONAL_TYPES = frozenset({
    "feat", "fix", "chore", "docs", "style",
    "refactor", "test", "build", "ci", "perf",
})

_TYPE_RE = re.compile(
    r"^(?P<type>[A-Za-z]+)(?P<scope>\([^)]*\))?(?P<breaking>!)?:\s*(?P<desc>.+)$"
)


def _guess_type(subject: str) -> str:
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
    if lower.startswith(("build",)):
        return "build"
    return "chore"


def _normalize_subject(subject: str) -> str:
    subject = subject.strip()
    m = _TYPE_RE.match(subject)
    if m:
        typ = m.group("type").lower()
        scope_raw = m.group("scope") or ""
        breaking = m.group("breaking") or ""
        desc = m.group("desc").strip()

        if typ not in CONVENTIONAL_TYPES:
            typ = _guess_type(desc)

        scope = scope_raw.lower() if scope_raw else ""

        if desc:
            desc = desc[0].upper() + desc[1:]
        if desc.endswith(".") and not desc.endswith("..."):
            desc = desc[:-1]

        subject = f"{typ}{scope}{breaking}: {desc}"
    else:
        desc = subject
        if desc:
            desc = desc[0].upper() + desc[1:]
        if desc.endswith(".") and not desc.endswith("..."):
            desc = desc[:-1]
        typ = _guess_type(desc)
        subject = f"{typ}: {desc}"

    if len(subject) > SUBJECT_MAX_LEN:
        truncated = subject[:SUBJECT_MAX_LEN]
        last_space = truncated.rfind(" ")
        subject = truncated[:last_space] if last_space > 0 else truncated
        import sys as _sys
        print(f"warning: subject line truncated to {SUBJECT_MAX_LEN} characters", file=_sys.stderr)

    return subject


def normalize(message: str) -> str:
    lines = [line.rstrip() for line in message.splitlines()]
    while lines and not lines[-1]:
        lines.pop()

    if not lines:
        return ""

    subject = _normalize_subject(lines[0])

    raw_body = lines[1:]
    while raw_body and not raw_body[0]:
        raw_body = raw_body[1:]

    if not raw_body:
        return subject

    return subject + "\n\n" + "\n".join(raw_body)


def main() -> None:
    if len(sys.argv) >= 2:
        path = sys.argv[1]
        with open(path, encoding="utf-8") as fh:
            msg = fh.read()
        normalized = normalize(msg)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(normalized + "\n")
    else:
        msg = sys.stdin.read()
        sys.stdout.write(normalize(msg) + "\n")


if __name__ == "__main__":
    main()
