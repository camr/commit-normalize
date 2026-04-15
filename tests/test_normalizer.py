"""Tests for commit message normalizer."""

import pytest

from normalizer import normalize, SUBJECT_MAX_LEN


# ---------------------------------------------------------------------------
# Subject trimming
# ---------------------------------------------------------------------------

class TestSubjectTrimming:
    def test_subject_within_limit_unchanged(self):
        msg = "feat: short subject"
        result = normalize(msg)
        assert result.startswith("feat: Short subject")

    def test_subject_exactly_at_limit(self):
        # Build a subject that is exactly SUBJECT_MAX_LEN chars after normalization.
        desc = "x" * (SUBJECT_MAX_LEN - len("chore: "))
        msg = f"chore: {desc}"
        result = normalize(msg)
        assert len(result.splitlines()[0]) == SUBJECT_MAX_LEN

    def test_subject_exceeding_limit_is_trimmed(self):
        long_desc = "a" * 100
        msg = f"feat: {long_desc}"
        result = normalize(msg)
        subject_line = result.splitlines()[0]
        assert len(subject_line) <= SUBJECT_MAX_LEN

    def test_leading_trailing_whitespace_stripped(self):
        msg = "  feat: add thing  "
        result = normalize(msg)
        assert not result.startswith(" ")


# ---------------------------------------------------------------------------
# Capitalization
# ---------------------------------------------------------------------------

class TestCapitalization:
    def test_description_capitalized(self):
        result = normalize("feat: add new feature")
        assert result == "feat: Add new feature"

    def test_already_capitalized_unchanged(self):
        result = normalize("fix: Fix the bug")
        assert result == "fix: Fix the bug"

    def test_does_not_uppercase_rest(self):
        result = normalize("docs: update README and changelog")
        assert result == "docs: Update README and changelog"

    def test_bare_subject_gets_capitalized(self):
        result = normalize("add logging to api")
        assert result.split(": ", 1)[1][0].isupper()


# ---------------------------------------------------------------------------
# Type prefix enforcement
# ---------------------------------------------------------------------------

class TestTypePrefixEnforcement:
    def test_valid_type_preserved(self):
        for typ in ("feat", "fix", "chore", "docs", "refactor", "test", "style", "perf", "ci"):
            result = normalize(f"{typ}: do something")
            assert result.startswith(f"{typ}: ")

    def test_unknown_type_replaced_with_guess(self):
        result = normalize("wip: add new feature")
        # wip is unknown; desc starts with 'add' so should become feat
        subject = result.splitlines()[0]
        assert subject.startswith("feat: ")

    def test_bare_subject_gets_inferred_feat(self):
        result = normalize("add new payment gateway")
        assert result.startswith("feat: ")

    def test_bare_fix_subject_gets_fix_type(self):
        result = normalize("fix broken link in readme")
        assert result.startswith("fix: ")

    def test_scope_preserved(self):
        result = normalize("feat(auth): add oauth support")
        assert result.startswith("feat(auth): ")

    def test_breaking_change_marker_preserved(self):
        result = normalize("feat!: remove deprecated api")
        assert result.startswith("feat!: ")


# ---------------------------------------------------------------------------
# Trailing period removal
# ---------------------------------------------------------------------------

class TestTrailingPeriodRemoval:
    def test_trailing_period_stripped(self):
        result = normalize("fix: correct the off-by-one error.")
        assert not result.splitlines()[0].endswith(".")

    def test_no_period_unchanged(self):
        result = normalize("fix: correct the off-by-one error")
        assert result == "fix: Correct the off-by-one error"

    def test_ellipsis_not_stripped(self):
        # Only a single trailing period should be stripped; ellipsis left alone.
        result = normalize("chore: work in progress...")
        assert result.splitlines()[0].endswith("...")


# ---------------------------------------------------------------------------
# Body blank-line insertion
# ---------------------------------------------------------------------------

class TestBodyBlankLine:
    def test_blank_line_inserted_before_body(self):
        msg = "feat: add thing\nThis is the body."
        result = normalize(msg)
        lines = result.splitlines()
        assert lines[1] == "", f"Expected blank line at index 1, got: {lines!r}"
        assert lines[2] == "This is the body."

    def test_existing_blank_line_kept(self):
        msg = "feat: add thing\n\nThis is the body."
        result = normalize(msg)
        lines = result.splitlines()
        assert lines[1] == ""
        assert lines[2] == "This is the body."

    def test_no_body_no_blank_line(self):
        result = normalize("feat: add thing")
        assert "\n" not in result

    def test_multiple_body_lines_preserved(self):
        msg = "fix: patch\n\nLine one.\nLine two.\nLine three."
        result = normalize(msg)
        lines = result.splitlines()
        assert lines[0].startswith("fix: ")
        assert lines[1] == ""
        assert lines[2] == "Line one."
        assert lines[3] == "Line two."
        assert lines[4] == "Line three."

    def test_trailing_blank_lines_in_input_removed(self):
        msg = "feat: add thing\n\n"
        result = normalize(msg)
        assert not result.endswith("\n")
