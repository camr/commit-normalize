"""CLI entry point for commit message normalizer."""

import argparse
import sys

from normalizer import normalize


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

    args = parser.parse_args()

    if args.file:
        if args.file == "-":
            raw = sys.stdin.read()
            try:
                result = normalize(raw)
            except ValueError as exc:
                print(f"error: {exc}", file=sys.stderr)
                sys.exit(1)
            print(result)
            return

        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

        try:
            result = normalize(raw)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            sys.exit(1)

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
        result = normalize(args.message)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(result)


if __name__ == "__main__":
    main()
