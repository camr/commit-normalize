#!/usr/bin/env python3
"""
CLI entry point for the commit message normalizer.

Usage as a git commit-msg hook:
    python cli.py <path-to-commit-msg-file>

Usage via stdin:
    echo "my commit" | python cli.py
"""

import argparse
import sys

from normalizer import normalize


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize a git commit message to conventional-commit format."
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to commit message file (as passed by git commit-msg hook). "
             "Reads from stdin when omitted.",
    )
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            original = fh.read()
        normalized = normalize(original)
        with open(args.file, "w", encoding="utf-8") as fh:
            fh.write(normalized + "\n")
    else:
        original = sys.stdin.read()
        normalized = normalize(original)
        sys.stdout.write(normalized + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
