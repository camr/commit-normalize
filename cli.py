"""CLI entry point for commit message normalizer."""

import argparse
import sys

from normalizer import normalize, load_config


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
        help="report violations without modifying; exits 1 if changes would be made",
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="path to commit-normalize.json (default: ./commit-normalize.json)",
    )

    args = parser.parse_args()

    config = load_config(args.config)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        try:
            result = normalize(raw, config)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        if args.check:
            if raw.rstrip("\n") != result:
                print("commit message requires normalization:", file=sys.stderr)
                print(result, file=sys.stderr)
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
        result = normalize(args.message, config)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.check:
        if args.message.rstrip("\n") != result:
            print("commit message requires normalization:", file=sys.stderr)
            print(result, file=sys.stderr)
            sys.exit(1)
        return

    print(result)


if __name__ == "__main__":
    main()
