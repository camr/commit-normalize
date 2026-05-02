"""CLI entry point for commit message normalizer."""

import argparse
import sys

from normalizer import load_config, normalize


def main():
    parser = argparse.ArgumentParser(
        description="Normalize a commit message to Conventional Commits format."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "message",
        nargs="?",
        help="commit message string to normalize",
    )
    group.add_argument(
        "-f",
        "--file",
        metavar="FILE",
        help="path to commit message file (git commit-msg hook usage); rewrites file in place",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="report violations without modifying the file; exits non-zero if the message "
             "would be changed (requires --file)",
    )

    args = parser.parse_args()

    if args.check and not args.file:
        print("error: --check requires --file", file=sys.stderr)
        sys.exit(1)

    config = load_config()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        try:
            result = normalize(raw, config=config)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        if args.check:
            if result.strip() != raw.strip():
                print("commit message requires normalization:", file=sys.stderr)
                _report_diff(raw.strip(), result.strip())
                sys.exit(1)
            return

        try:
            with open(args.file, "w", encoding="utf-8") as fh:
                fh.write(result + "\n")
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        return

    if args.message is None:
        parser.print_usage(sys.stderr)
        sys.exit(1)

    try:
        result = normalize(args.message, config=config)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(result)


def _report_diff(original: str, normalized: str):
    """Print a simple before/after view to stderr."""
    for line in original.splitlines():
        print(f"  - {line}", file=sys.stderr)
    for line in normalized.splitlines():
        print(f"  + {line}", file=sys.stderr)


if __name__ == "__main__":
    main()
