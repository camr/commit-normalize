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


def test_stdin_normalizes_message():
    result = run("--file", "-", input_text="Feat: Add something.")
    assert result.returncode == 0
    assert result.stdout.strip() == "feat: add something"


def test_stdin_short_flag():
    result = run("-f", "-", input_text="FIX: Bug fixed.")
    assert result.returncode == 0
    assert result.stdout.strip() == "fix: bug fixed"


def test_stdin_empty_exits_nonzero():
    result = run("--file", "-", input_text="   ")
    assert result.returncode != 0


def test_stdin_multiline():
    msg = "feat: Add feature\n\nBody text here."
    result = run("--file", "-", input_text=msg)
    assert result.returncode == 0
    assert result.stdout.startswith("feat: add feature")
    assert "Body text here." in result.stdout
