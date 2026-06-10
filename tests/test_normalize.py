"""Tests for normalize.py — commit message normalizer."""

import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from normalize import normalize, _normalize_subject, _wrap_body

# ---------------------------------------------------------------------------
# Subject: capitalization
# ---------------------------------------------------------------------------

def test_subject_capitalizes_description():
    assert normalize("feat: add new feature") == "feat: Add new feature"


def test_subject_already_capitalized_unchanged():
    assert normalize("feat: Add new feature") == "feat: Add new feature"


def test_subject_with_scope_capitalizes():
    assert normalize("fix(auth): resolve null pointer") == "fix(auth): Resolve null pointer"


# ---------------------------------------------------------------------------
# Subject: trailing period removal
# ---------------------------------------------------------------------------

def test_trailing_period_removed():
    assert normalize("feat: Add new feature.") == "feat: Add new feature"


def test_no_trailing_period_unchanged():
    assert normalize("feat: Add new feature") == "feat: Add new feature"


def test_trailing_period_with_scope():
    assert normalize("fix(db): Fix connection leak.") == "fix(db): Fix connection leak"


# ---------------------------------------------------------------------------
# Subject: 72-char trimming with word boundary
# ---------------------------------------------------------------------------

def test_subject_trimmed_to_72():
    long_desc = "a " * 40  # well over 72 chars
    msg = "feat: " + long_desc.strip()
    result = normalize(msg)
    assert len(result.splitlines()[0]) <= 72


def test_subject_trim_at_word_boundary():
    # Subject over 72 chars — trim should not cut mid-word
    msg = "feat: Add a feature that has a very long description exceeding seventy-two characters"
    result = normalize(msg)
    line = result.splitlines()[0]
    assert len(line) <= 72
    assert not line.endswith("-")  # no mid-word cut at hyphen boundary
    # The trimmed line should be a valid prefix ending at a space
    assert msg.startswith(line) or line == msg[:72]


def test_subject_exactly_72_unchanged():
    # "feat: " = 6 chars, pad description to make total exactly 72
    desc = "A" + "x" * 65  # 66 chars -> total 72
    msg = f"feat: {desc}"
    assert len(msg) == 72
    assert normalize(msg) == msg


# ---------------------------------------------------------------------------
# Blank line between subject and body
# ---------------------------------------------------------------------------

def test_blank_line_inserted_when_missing():
    msg = "feat: Add feature\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[0] == "feat: Add feature"
    assert lines[1] == ""
    assert "This is the body." in result


def test_blank_line_preserved_when_present():
    msg = "feat: Add feature\n\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[0] == "feat: Add feature"
    assert lines[1] == ""
    assert "This is the body." in result


def test_multiple_leading_blanks_collapsed():
    msg = "feat: Add feature\n\n\n\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[1] == ""
    assert lines[2] != ""


# ---------------------------------------------------------------------------
# Body wrapping at 72 chars
# ---------------------------------------------------------------------------

def test_body_long_line_wrapped():
    long_body = "word " * 20  # 100 chars
    msg = "feat: Add feature\n\n" + long_body.strip()
    result = normalize(msg)
    body_lines = result.splitlines()[2:]
    for line in body_lines:
        assert len(line) <= 72


def test_body_short_line_unchanged():
    msg = "feat: Add feature\n\nShort body."
    result = normalize(msg)
    assert "Short body." in result


def test_body_paragraphs_preserved():
    msg = "feat: Add feature\n\nFirst paragraph.\n\nSecond paragraph."
    result = normalize(msg)
    assert "First paragraph." in result
    assert "Second paragraph." in result


# ---------------------------------------------------------------------------
# Passthrough of already-valid messages
# ---------------------------------------------------------------------------

def test_already_valid_message_unchanged():
    msg = "feat: Add new login flow"
    assert normalize(msg) == msg


def test_valid_with_scope_unchanged():
    msg = "fix(auth): Resolve null pointer"
    assert normalize(msg) == msg


def test_valid_with_breaking_unchanged():
    msg = "feat!: Remove legacy API"
    assert normalize(msg) == msg


# ---------------------------------------------------------------------------
# Non-conventional subjects: documented partial normalization
# ---------------------------------------------------------------------------

def test_non_conventional_subject_capitalizes():
    # Non-conventional messages still get capitalization and period removal.
    msg = "fix the thing."
    result = normalize(msg)
    assert result[0].isupper()
    assert not result.endswith(".")


def test_non_conventional_subject_period_removed():
    msg = "Update the readme."
    result = normalize(msg)
    assert not result.rstrip().endswith(".")


def test_non_conventional_subject_still_trimmed():
    long = "w " * 40
    msg = long.strip()
    result = normalize(msg)
    assert len(result.splitlines()[0]) <= 72


# ---------------------------------------------------------------------------
# CLI invocation
# ---------------------------------------------------------------------------

def test_cli_file_mode(tmp_path):
    commit_file = tmp_path / "COMMIT_EDITMSG"
    commit_file.write_text("feat: add widget.\n\nbody text here\n")
    subprocess.check_call([sys.executable, "normalize.py", str(commit_file)],
                          cwd=str(Path(__file__).parent.parent))
    result = commit_file.read_text()
    assert result.startswith("feat: Add widget")
    assert "body text here" in result


def test_cli_stdin_mode():
    msg = "feat: add gadget.\n"
    proc = subprocess.run(
        [sys.executable, "normalize.py"],
        input=msg,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert proc.returncode == 0
    assert proc.stdout.startswith("feat: Add gadget")


# ---------------------------------------------------------------------------
# Comment stripping
# ---------------------------------------------------------------------------

def test_comment_lines_stripped():
    msg = (
        "feat: add feature\n"
        "\n"
        "# Please enter the commit message for your changes.\n"
        "# Changes to be committed:\n"
        "#   modified: foo.py\n"
    )
    result = normalize(msg)
    assert "#" not in result
    assert result == "feat: Add feature"


def test_comment_lines_stripped_with_body():
    msg = (
        "fix: resolve issue\n"
        "\n"
        "Detailed explanation here.\n"
        "\n"
        "# On branch main\n"
        "# Changes to be committed:\n"
    )
    result = normalize(msg)
    assert "#" not in result
    assert "Detailed explanation here." in result


def test_comment_only_message_returns_empty():
    msg = "# Please enter the commit message\n# Changes:\n#  foo\n"
    result = normalize(msg)
    assert result == ""


def test_inline_hash_in_body_not_stripped():
    # '#' not at line start should be preserved
    msg = "feat: Add feature\n\nSee issue #123 for details."
    result = normalize(msg)
    assert "#123" in result


# ---------------------------------------------------------------------------
# --check mode
# ---------------------------------------------------------------------------

def test_check_mode_exits_zero_when_already_normalized(tmp_path):
    commit_file = tmp_path / "COMMIT_EDITMSG"
    commit_file.write_text("feat: Add widget")
    proc = subprocess.run(
        [sys.executable, "normalize.py", "--check", str(commit_file)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert proc.returncode == 0


def test_check_mode_exits_one_when_changes_needed(tmp_path):
    commit_file = tmp_path / "COMMIT_EDITMSG"
    original = "feat: add widget.\n"
    commit_file.write_text(original)
    proc = subprocess.run(
        [sys.executable, "normalize.py", "--check", str(commit_file)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert proc.returncode == 1
    # File must not be modified
    assert commit_file.read_text() == original


def test_check_mode_does_not_modify_file(tmp_path):
    commit_file = tmp_path / "COMMIT_EDITMSG"
    original = "feat: add widget.\n"
    commit_file.write_text(original)
    subprocess.run(
        [sys.executable, "normalize.py", "--check", str(commit_file)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert commit_file.read_text() == original


def test_check_mode_stdin_exits_zero_when_normalized():
    proc = subprocess.run(
        [sys.executable, "normalize.py", "--check"],
        input="feat: Add widget",
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert proc.returncode == 0


def test_check_mode_stdin_exits_one_when_changes_needed():
    proc = subprocess.run(
        [sys.executable, "normalize.py", "--check"],
        input="feat: add widget.\n",
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )
    assert proc.returncode == 1


# ---------------------------------------------------------------------------
# Git trailer preservation
# ---------------------------------------------------------------------------

def test_trailer_co_authored_by_preserved():
    msg = (
        "feat: Add feature\n"
        "\n"
        "Implement the new thing.\n"
        "\n"
        "Co-authored-by: Jane Doe <jane@example.com>\n"
    )
    result = normalize(msg)
    assert "Co-authored-by: Jane Doe <jane@example.com>" in result


def test_trailer_not_reflowed_into_prose():
    msg = (
        "fix: Resolve bug\n"
        "\n"
        "Long prose body that explains the fix in detail.\n"
        "Co-authored-by: Jane Doe <jane@example.com>\n"
    )
    result = normalize(msg)
    lines = result.splitlines()
    trailer_lines = [l for l in lines if l.startswith("Co-authored-by:")]
    assert len(trailer_lines) == 1
    assert trailer_lines[0] == "Co-authored-by: Jane Doe <jane@example.com>"


def test_trailer_fixes_preserved():
    msg = "fix: Resolve issue\n\nSome explanation.\n\nFixes: #123\n"
    result = normalize(msg)
    assert "Fixes: #123" in result


def test_multiple_trailers_preserved():
    msg = (
        "feat: Add oauth\n"
        "\n"
        "Adds OAuth2 support.\n"
        "\n"
        "Co-authored-by: Alice <alice@example.com>\n"
        "Reviewed-by: Bob <bob@example.com>\n"
        "Fixes: #42\n"
    )
    result = normalize(msg)
    assert "Co-authored-by: Alice <alice@example.com>" in result
    assert "Reviewed-by: Bob <bob@example.com>" in result
    assert "Fixes: #42" in result


def test_breaking_change_trailer_preserved():
    msg = (
        "feat!: Remove legacy endpoint\n"
        "\n"
        "Drops /v1/users entirely.\n"
        "\n"
        "BREAKING CHANGE: /v1/users is removed, use /v2/users\n"
    )
    result = normalize(msg)
    assert "BREAKING CHANGE: /v1/users is removed, use /v2/users" in result
