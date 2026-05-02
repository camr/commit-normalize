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
    assert result.stdout.strip() == "feat: add new feature"


def test_normalize_fixes_type_case():
    result = run("FIX: correct typo.")
    assert result.returncode == 0
    assert result.stdout.strip() == "fix: correct typo"


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
        assert content.strip() == "feat: add thing"
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
        assert content.strip() == "fix: bug"
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


# --check mode tests

def test_check_mode_clean_message_exits_zero():
    # An already-normalized message should exit 0 with --check
    result = run("--check", "feat: add login page")
    assert result.returncode == 0


def test_check_mode_dirty_message_exits_nonzero():
    # A message that needs normalization should exit 1 with --check
    result = run("--check", "FIX: correct typo.")
    assert result.returncode == 1
    # Should print what the normalized form would be
    assert "fix: correct typo" in result.stderr


def test_check_mode_does_not_modify_file():
    # --check with --file must NOT write back to the file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as fh:
        fh.write("FIX: bad message.\n")
        path = fh.name

    try:
        result = run("--check", "--file", path)
        assert result.returncode == 1
        # File must be unchanged
        with open(path) as fh:
            content = fh.read()
        assert content == "FIX: bad message.\n"
    finally:
        os.unlink(path)
