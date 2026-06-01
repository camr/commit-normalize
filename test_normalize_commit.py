"""Tests for normalize_commit.py."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalize_commit import (
    MissingFormatError,
    NormalizationError,
    UnknownTypeError,
    main,
    normalize_message,
    normalize_subject,
)


class TestNormalizeSubject:
    def test_valid_message_unchanged(self):
        assert normalize_subject("feat: Add login page") == "feat: Add login page"

    def test_capitalizes_description(self):
        assert normalize_subject("feat: add login page") == "feat: Add login page"

    def test_strips_trailing_period(self):
        assert normalize_subject("fix: Correct typo.") == "fix: Correct typo"

    def test_strips_multiple_trailing_periods(self):
        assert normalize_subject("fix: Correct typo...") == "fix: Correct typo"

    def test_does_not_strip_trailing_exclamation_in_desc(self):
        # ! in a description is user intent, not conventional-commit syntax
        assert normalize_subject("fix: Important fix!") == "fix: Important fix!"

    def test_breaking_change_marker_preserved(self):
        # Critical: feat!: must not silently become feat:
        result = normalize_subject("feat!: Drop old API")
        assert result == "feat!: Drop old API"

    def test_breaking_change_contains_exclamation(self):
        result = normalize_subject("feat!: Add breaking change")
        assert "!" in result
        assert result.startswith("feat!:")

    def test_breaking_change_with_scope_preserved(self):
        result = normalize_subject("feat(api)!: Drop old endpoint")
        assert result == "feat(api)!: Drop old endpoint"

    def test_scope_preserved(self):
        assert normalize_subject("feat(auth): Add login") == "feat(auth): Add login"

    def test_scope_whitespace_normalized(self):
        assert normalize_subject("feat( auth ): Add login") == "feat(auth): Add login"

    def test_whitespace_only_scope_dropped(self):
        assert normalize_subject("feat(   ): Add login") == "feat: Add login"

    def test_subject_truncated_to_72_chars(self):
        long_desc = "A" * 80
        result = normalize_subject(f"feat: {long_desc}")
        assert len(result) <= 72

    def test_no_trailing_period_after_truncation(self):
        # Period lands exactly at the truncation boundary
        # prefix "feat: " = 6 chars, available = 66; put period at position 65
        desc = "A" * 65 + "." + "B" * 20
        result = normalize_subject(f"feat: {desc}")
        assert len(result) <= 72
        assert not result.endswith(".")

    def test_unknown_type_raises(self):
        with pytest.raises(UnknownTypeError):
            normalize_subject("random: Some change")

    def test_missing_format_raises(self):
        with pytest.raises(MissingFormatError):
            normalize_subject("some random change without type")

    def test_all_valid_types_accepted(self):
        valid_types = [
            "feat", "fix", "docs", "style", "refactor",
            "perf", "test", "build", "ci", "chore", "revert",
        ]
        for t in valid_types:
            result = normalize_subject(f"{t}: Do something")
            assert result.startswith(t)


class TestNormalizeMessage:
    def test_subject_only_message(self):
        assert normalize_message("feat: Add feature") == "feat: Add feature"

    def test_body_preserved(self):
        msg = "feat: Add feature\n\nThis is the body.\nSecond line."
        result = normalize_message(msg)
        assert "This is the body." in result
        assert "Second line." in result

    def test_subject_and_body_separated_by_blank_line(self):
        msg = "feat: Add feature\n\nBody text."
        lines = normalize_message(msg).splitlines()
        assert lines[0].startswith("feat:")
        assert lines[1] == ""
        assert "Body text." in lines[2]

    def test_comment_only_message_passes_through(self):
        # git inserts # comment lines; entirely-comment messages pass unchanged
        msg = "# This is a comment\n# On multiple lines\n"
        assert normalize_message(msg) == msg

    def test_comment_lines_stripped_before_normalization(self):
        msg = "feat: add thing\n# git status comment\n\nBody here."
        result = normalize_message(msg)
        assert result.startswith("feat:")
        assert "# git status comment" not in result

    def test_empty_message_raises(self):
        with pytest.raises(NormalizationError):
            normalize_message("")

    def test_whitespace_only_message_raises(self):
        with pytest.raises(NormalizationError):
            normalize_message("   \n  ")


class TestMain:
    def _write_tmp(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_normalizes_file_in_place(self):
        path = self._write_tmp("feat: add thing\n")
        try:
            sys.argv = ["normalize_commit.py", path]
            assert main() == 0
            with open(path) as f:
                assert f.read() == "feat: Add thing"
        finally:
            os.unlink(path)

    def test_returns_nonzero_on_bad_format(self):
        path = self._write_tmp("this is not conventional\n")
        try:
            sys.argv = ["normalize_commit.py", path]
            assert main() != 0
        finally:
            os.unlink(path)

    def test_returns_nonzero_on_unknown_type(self):
        path = self._write_tmp("random: some change\n")
        try:
            sys.argv = ["normalize_commit.py", path]
            assert main() != 0
        finally:
            os.unlink(path)

    def test_comment_only_file_passes(self):
        path = self._write_tmp("# comment only\n# another comment\n")
        try:
            sys.argv = ["normalize_commit.py", path]
            assert main() == 0
        finally:
            os.unlink(path)

    def test_missing_argv_returns_nonzero(self):
        sys.argv = ["normalize_commit.py"]
        assert main() != 0
