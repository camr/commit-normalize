"""Unit tests for normalizer.py."""

import pytest
from normalizer import normalize


def test_passthrough_valid_message():
    msg = "feat: add login page"
    assert normalize(msg) == msg


def test_type_uppercased_is_lowercased():
    assert normalize("Feat: add login page") == "feat: add login page"


def test_type_all_caps_lowercased():
    assert normalize("FIX: correct typo") == "fix: correct typo"


def test_unknown_type_defaults_to_chore():
    assert normalize("random: some change") == "chore: some change"


def test_missing_type_wrapped_as_chore():
    # Plain sentence with no type
    assert normalize("some random change") == "chore: some random change"


def test_trailing_period_stripped():
    assert normalize("fix: correct typo.") == "fix: correct typo"


def test_multiple_trailing_periods_stripped():
    assert normalize("fix: correct typo...") == "fix: correct typo"


def test_subject_truncated_to_72_chars():
    description = "a" * 80
    result = normalize(f"feat: {description}")
    assert len(result) <= 72


def test_no_trailing_period_after_truncation():
    # Make description such that truncation boundary lands on a period
    # prefix = "feat: " = 6 chars, available = 66 chars
    # put a period at position 66
    description = "a" * 65 + "." + "b" * 20
    result = normalize(f"feat: {description}")
    assert not result.endswith(".")
    assert len(result) <= 72


def test_period_at_exact_truncation_boundary():
    # prefix = "chore: " = 7 chars, available = 65 chars
    description = "x" * 64 + "." + "y" * 20
    result = normalize(f"chore: {description}")
    assert not result.endswith(".")


def test_scope_preserved():
    assert normalize("feat(auth): add login") == "feat(auth): add login"


def test_scope_whitespace_normalized():
    assert normalize("feat( auth ): add login") == "feat(auth): add login"


def test_whitespace_only_scope_removed():
    assert normalize("feat(   ): add login") == "feat: add login"


def test_breaking_change_marker_preserved():
    assert normalize("feat!: drop old API") == "feat!: drop old API"


def test_breaking_change_with_scope():
    assert normalize("feat(api)!: drop old API") == "feat(api)!: drop old API"


def test_multiline_body_preserved():
    msg = "feat: add feature\n\nThis is the body.\nIt spans multiple lines."
    result = normalize(msg)
    assert "This is the body." in result
    assert "It spans multiple lines." in result


def test_empty_message_raises():
    with pytest.raises(ValueError):
        normalize("")


def test_whitespace_only_message_raises():
    with pytest.raises(ValueError):
        normalize("   \n  \n ")


def test_body_not_misclassified_as_footer():
    # Body paragraph that contains a colon should not be treated as footer
    msg = "fix: bug\n\nNote: this is body text\nMore body here."
    result = normalize(msg)
    lines = result.splitlines()
    # Should have blank line after header, then body
    assert lines[1] == ""
    assert any("Note: this is body text" in l for l in lines)


def test_footer_separated_from_body():
    msg = "fix: bug\n\nThis is body text.\n\nCloses: #123"
    result = normalize(msg)
    assert "This is body text." in result
    assert "Closes: #123" in result


def test_last_body_paragraph_type_style_not_footer():
    # A paragraph that looks like "fix: something" should be body, not footer
    msg = "feat: new thing\n\nfix: this is actually body prose"
    result = normalize(msg)
    # Should preserve it as body
    assert "fix: this is actually body prose" in result


def test_body_content_not_lost():
    msg = "chore: update deps\n\nBumped requests from 2.28 to 2.31."
    result = normalize(msg)
    assert "Bumped requests" in result
