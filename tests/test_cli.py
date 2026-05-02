"""Integration tests for cli.py using subprocess."""

import subprocess
import sys
import tempfile
import os

import pytest

CLI = [sys.executable, os.path.join(os.path.dirname(__file__), "..", "cli.py")]


def run(*args, input_text=None):
    return subprocess.run(
        CLI + list(args),
        capture_output=True,
        text=True,
        input=input_text,
    )


def test_normalize_string_argument():
    result = run("feat: add new feature")
    assert result.returncode == 0
    assert result.stdout.strip() == "feat: Add new feature"


def test_normalize_fixes_type_case():
    result = run("FIX: correct typo.")
    assert result.returncode == 0
    assert result.stdout.strip() == "fix: Correct typo"


def test_no_args_exits_nonzero():
    result = run()
    assert result.returncode != 0


def test_empty_message_exits_nonzero():
    result = run("")
    assert result.returncode != 0


def test_whitespace_message_exits_nonzero():
    result = run("   ")
    assert result.returncode != 0


def test_file_flag_reads_and_rewrites():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("Feat: add thing.\n")
        path = fh.name

    try:
        result = run("--file", path)
        assert result.returncode == 0
        with open(path, "r") as fh:
            content = fh.read()
        assert content.strip() == "feat: Add thing"
    finally:
        os.unlink(path)


def test_short_file_flag():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("FIX: bug.\n")
        path = fh.name

    try:
        result = run("-f", path)
        assert result.returncode == 0
        with open(path) as fh:
            content = fh.read()
        assert content.strip() == "fix: Bug"
    finally:
        os.unlink(path)


def test_missing_file_exits_nonzero():
    result = run("--file", "/nonexistent/path/commit_msg.txt")
    assert result.returncode != 0


def test_multiline_message_preserved():
    msg = "feat: add feature\n\nThis is the body text."
    result = run(msg)
    assert result.returncode == 0
    assert "This is the body text." in result.stdout


# ---------------------------------------------------------------------------
# --check mode
# ---------------------------------------------------------------------------

def test_check_passes_for_normalized_message():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("feat: Add new feature\n")
        path = fh.name

    try:
        result = run("--check", "--file", path)
        assert result.returncode == 0
        # File must not be modified
        with open(path) as fh:
            content = fh.read()
        assert content == "feat: Add new feature\n"
    finally:
        os.unlink(path)


def test_check_fails_for_non_normalized_message():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("FIX: correct typo.\n")
        path = fh.name

    try:
        result = run("--check", "--file", path)
        assert result.returncode != 0
        # File must NOT be rewritten in check mode
        with open(path) as fh:
            content = fh.read()
        assert content == "FIX: correct typo.\n"
    finally:
        os.unlink(path)


def test_check_without_file_exits_nonzero():
    result = run("--check", "feat: Add thing")
    assert result.returncode != 0
    assert "requires --file" in result.stderr
