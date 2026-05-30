"""Unit tests for normalize_commit.py."""

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from normalize_commit import normalize


# ---------------------------------------------------------------------------
# Valid conventional commit passthrough
# ---------------------------------------------------------------------------

def test_valid_commit_passthrough():
    msg = "feat: Add new login flow"
    assert normalize(msg) == msg


def test_valid_with_scope_passthrough():
    msg = "fix(auth): Resolve null pointer"
    assert normalize(msg) == msg


def test_valid_with_breaking_passthrough():
    msg = "feat!: Remove legacy API"
    assert normalize(msg) == msg


# ---------------------------------------------------------------------------
# Missing type: auto-detection fallback to 'chore'
# ---------------------------------------------------------------------------

def test_missing_type_falls_back_to_chore():
    msg = "Update some configuration"
    result = normalize(msg)
    assert result.startswith("chore: ")


def test_missing_type_fix_inferred():
    msg = "fix the login bug"
    result = normalize(msg)
    assert result.startswith("fix: ")


def test_missing_type_feat_inferred():
    msg = "add new user endpoint"
    result = normalize(msg)
    assert result.startswith("feat: ")


# ---------------------------------------------------------------------------
# Uppercase type normalization
# ---------------------------------------------------------------------------

def test_uppercase_type_lowercased():
    msg = "FEAT: Add new feature"
    result = normalize(msg)
    assert result.startswith("feat: ")


def test_mixedcase_type_lowercased():
    msg = "Fix: resolve issue"
    result = normalize(msg)
    assert result.startswith("fix: ")


def test_uppercase_scope_lowercased():
    msg = "fix(AUTH): Resolve null pointer"
    result = normalize(msg)
    assert result.startswith("fix(auth): ")


# ---------------------------------------------------------------------------
# Trailing period removal
# ---------------------------------------------------------------------------

def test_trailing_period_removed():
    msg = "feat: Add new feature."
    result = normalize(msg)
    assert not result.rstrip().endswith(".")


def test_ellipsis_not_removed():
    msg = "feat: Work in progress..."
    result = normalize(msg)
    assert result.endswith("...")


def test_trailing_period_with_scope():
    msg = "fix(db): Fix connection leak."
    result = normalize(msg)
    assert not result.rstrip().endswith(".")


# ---------------------------------------------------------------------------
# Subject line capitalization
# ---------------------------------------------------------------------------

def test_subject_desc_capitalized():
    msg = "feat: add new feature"
    result = normalize(msg)
    assert result == "feat: Add new feature"


def test_subject_already_capitalized():
    msg = "feat: Add new feature"
    assert normalize(msg) == msg


def test_non_conventional_subject_capitalized():
    msg = "update the readme"
    result = normalize(msg)
    first_alpha = result.lstrip("abcdefghijklmnopqrstuvwxyz:( ")
    assert result[0].isupper() or result.split(": ", 1)[-1][0].isupper()


# ---------------------------------------------------------------------------
# Line length: truncation warning
# ---------------------------------------------------------------------------

def test_long_subject_truncated_to_72(capsys):
    long_desc = "a word " * 20
    msg = "feat: " + long_desc.strip()
    result = normalize(msg)
    subject_line = result.splitlines()[0]
    assert len(subject_line) <= 72


def test_long_subject_prints_warning(capsys):
    long_desc = "a word " * 20
    msg = "feat: " + long_desc.strip()
    normalize(msg)
    captured = capsys.readouterr()
    assert "warning" in captured.err.lower() or len(msg.splitlines()[0]) <= 72


def test_subject_exactly_72_not_truncated():
    prefix = "feat: "
    desc = "A" + "x" * (72 - len(prefix) - 1)
    msg = f"{prefix}{desc}"
    assert len(msg) == 72
    assert normalize(msg) == msg


# ---------------------------------------------------------------------------
# Blank line between subject and body
# ---------------------------------------------------------------------------

def test_blank_line_inserted_when_missing():
    msg = "feat: Add feature\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[0].startswith("feat: ")
    assert lines[1] == ""
    assert "This is the body." in result


def test_blank_line_preserved_when_present():
    msg = "feat: Add feature\n\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[1] == ""
    assert "This is the body." in result


def test_multiple_leading_blanks_collapsed():
    msg = "feat: Add feature\n\n\n\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[1] == ""
    assert lines[2] != ""


# ---------------------------------------------------------------------------
# CLI invocation
# ---------------------------------------------------------------------------

def test_cli_file_mode(tmp_path):
    commit_file = tmp_path / "COMMIT_EDITMSG"
    commit_file.write_text("feat: add widget.\n\nbody text here\n")
    subprocess.check_call(
        [sys.executable, "normalize_commit.py", str(commit_file)],
        cwd=str(Path(__file__).parent),
    )
    result = commit_file.read_text()
    assert result.startswith("feat: Add widget")
    assert "body text here" in result


def test_cli_stdin_mode():
    msg = "feat: add gadget.\n"
    proc = subprocess.run(
        [sys.executable, "normalize_commit.py"],
        input=msg,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent),
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("feat: Add gadget")
