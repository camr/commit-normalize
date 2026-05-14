"""Unit tests for normalize_commit.py."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from normalize_commit import normalize, NormalizationError


# Already-valid messages pass through unchanged

def test_passthrough_valid_message():
    msg = "feat: Add login page"
    assert normalize(msg) == msg


def test_passthrough_with_scope():
    msg = "fix(auth): Correct token expiry"
    assert normalize(msg) == msg


def test_passthrough_breaking_change():
    msg = "feat!: Drop old API"
    assert normalize(msg) == msg


def test_passthrough_breaking_change_with_scope():
    msg = "feat(api)!: Drop old API"
    assert normalize(msg) == msg


# Type casing is fixed

def test_type_uppercased_is_lowercased():
    assert normalize("Feat: Add login page") == "feat: Add login page"


def test_type_all_caps_lowercased():
    assert normalize("FIX: Correct typo") == "fix: Correct typo"


def test_type_mixed_case_lowercased():
    assert normalize("ChOrE: Update deps") == "chore: Update deps"


# Trailing periods removed

def test_trailing_period_stripped():
    assert normalize("fix: Correct typo.") == "fix: Correct typo"


def test_multiple_trailing_periods_stripped():
    assert normalize("fix: Correct typo...") == "fix: Correct typo"


def test_period_in_middle_preserved():
    assert normalize("fix: Rewrite v1.0 parser") == "fix: Rewrite v1.0 parser"


# Capitalized description enforced

def test_description_capitalized():
    assert normalize("feat: add login page") == "feat: Add login page"


def test_description_already_capitalized():
    assert normalize("fix: Correct the typo") == "fix: Correct the typo"


def test_description_capitalized_after_type_normalization():
    assert normalize("FIX: resolve crash") == "fix: Resolve crash"


# Blank line enforcement between subject and body

def test_missing_blank_line_inserted():
    msg = "feat: Add feature\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[0] == "feat: Add feature"
    assert lines[1] == ""
    assert lines[2] == "This is the body."


def test_blank_line_already_present():
    msg = "feat: Add feature\n\nThis is the body."
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[0] == "feat: Add feature"
    assert lines[1] == ""
    assert "This is the body." in result


# Body wrapping at 72 characters

def test_body_long_line_wrapped():
    body = "a" * 80
    msg = f"feat: Add feature\n\n{body}"
    result = normalize(msg)
    body_lines = result.splitlines()[2:]
    for line in body_lines:
        assert len(line) <= 72


def test_body_wrap_preserves_content():
    body = "word " * 20
    msg = f"feat: Add feature\n\n{body.strip()}"
    result = normalize(msg)
    original_words = body.split()
    result_words = " ".join(result.splitlines()[2:]).split()
    assert original_words == result_words


def test_short_body_lines_unchanged():
    msg = "feat: Add feature\n\nShort body line.\nAnother short line."
    result = normalize(msg)
    assert "Short body line." in result
    assert "Another short line." in result


# Unknown types raise NormalizationError

def test_unknown_type_raises_normalization_error():
    with pytest.raises(NormalizationError):
        normalize("random: some change")


def test_unknown_type_error_message():
    with pytest.raises(NormalizationError, match="unknown commit type"):
        normalize("bogus: do something")


def test_unknown_type_not_remapped_silently():
    # Must raise, not silently produce "chore: ..."
    with pytest.raises(NormalizationError):
        normalize("xyz: something")


# Subject line length enforcement

def test_subject_truncated_to_72_chars():
    description = "a" * 80
    result = normalize(f"feat: {description}")
    assert len(result.splitlines()[0]) <= 72


def test_no_trailing_period_after_truncation():
    # prefix "feat: " = 6 chars, available = 66 chars; put period at position 66
    description = "a" * 65 + "." + "b" * 20
    result = normalize(f"feat: {description}")
    assert not result.splitlines()[0].endswith(".")
    assert len(result.splitlines()[0]) <= 72


# Scope normalization

def test_scope_preserved():
    assert normalize("feat(auth): Add login") == "feat(auth): Add login"


def test_scope_whitespace_normalized():
    assert normalize("feat( auth ): Add login") == "feat(auth): Add login"


def test_whitespace_only_scope_removed():
    assert normalize("feat(   ): Add login") == "feat: Add login"


# Empty message

def test_empty_message_raises():
    with pytest.raises(NormalizationError):
        normalize("")


def test_whitespace_only_message_raises():
    with pytest.raises(NormalizationError):
        normalize("   \n  \n ")


# Footer preservation

def test_footer_separated_from_body():
    msg = "fix: Correct bug\n\nThis is body text.\n\nCloses: #123"
    result = normalize(msg)
    assert "This is body text." in result
    assert "Closes: #123" in result


def test_footer_trailer_not_treated_as_body():
    msg = "fix: Correct bug\n\nCloses: #123"
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[0] == "fix: Correct bug"
    assert lines[1] == ""
    assert "Closes: #123" in result


# NormalizationError is a subclass of ValueError

def test_normalization_error_is_value_error():
    with pytest.raises(ValueError):
        normalize("bogus: something")
