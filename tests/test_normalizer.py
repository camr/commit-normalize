"""Tests for the conventional commits normalizer."""

import pytest

from normalizer import normalize


# --- Valid types pass through ---

def test_valid_type_feat():
    assert normalize("feat: add new login flow") == "feat: add new login flow"


def test_valid_type_fix():
    assert normalize("fix: resolve null pointer in auth") == "fix: resolve null pointer in auth"


def test_valid_type_docs():
    assert normalize("docs: update contributing guide") == "docs: update contributing guide"


def test_valid_type_chore():
    assert normalize("chore: bump dependencies") == "chore: bump dependencies"


# --- Type uppercasing normalized ---

def test_type_uppercased_to_lower():
    assert normalize("FEAT: add something") == "feat: add something"


def test_type_mixed_case_to_lower():
    assert normalize("Fix: resolve issue") == "fix: resolve issue"


# --- Unknown type mapped to chore ---

def test_unknown_type_mapped_to_chore():
    assert normalize("wip: half-done feature") == "chore: half-done feature"


def test_unknown_type_update_mapped_to_chore():
    assert normalize("update: refresh dashboard") == "chore: refresh dashboard"


# --- Scope preserved and whitespace-trimmed ---

def test_scope_preserved():
    assert normalize("feat(auth): add oauth2 support") == "feat(auth): add oauth2 support"


def test_scope_whitespace_trimmed():
    assert normalize("feat( auth ): add oauth2 support") == "feat(auth): add oauth2 support"


def test_scope_with_unknown_type():
    assert normalize("wip(ui): broken layout") == "chore(ui): broken layout"


# --- Breaking-change marker preserved ---

def test_breaking_change_marker():
    assert normalize("feat!: remove legacy api") == "feat!: remove legacy api"


def test_breaking_change_with_scope():
    assert normalize("fix(api)!: change response format") == "fix(api)!: change response format"


# --- Trailing period stripped ---

def test_trailing_period_stripped():
    assert normalize("feat: add new endpoint.") == "feat: add new endpoint"


def test_trailing_period_stripped_with_scope():
    assert normalize("fix(db): fix connection pool leak.") == "fix(db): fix connection pool leak"


# --- First char of description lowercased ---

def test_description_first_char_lowercased():
    assert normalize("feat: Add new button") == "feat: add new button"


def test_description_first_char_lowercased_uppercase():
    assert normalize("fix: Fix the race condition") == "fix: fix the race condition"


# --- Subject truncated at 72 chars ---

def test_subject_truncated_at_72():
    long_desc = "a" * 80
    msg = f"feat: {long_desc}"
    result = normalize(msg)
    assert len(result.splitlines()[0]) == 72


def test_subject_exactly_72_unchanged():
    # "feat: " = 6 chars, need 66 more
    desc = "x" * 66
    msg = f"feat: {desc}"
    assert len(msg) == 72
    assert normalize(msg) == msg


# --- Body paragraphs preserved ---

def test_body_preserved():
    msg = "feat: add caching\n\nThis improves response time significantly.\n\nAdditional details here."
    result = normalize(msg)
    assert "This improves response time significantly." in result
    assert "Additional details here." in result


def test_body_paragraph_content_unchanged():
    body = "This is a long explanation of why we made this change."
    msg = f"feat: add feature\n\n{body}"
    result = normalize(msg)
    lines = result.splitlines()
    assert lines[0] == "feat: add feature"
    assert lines[1] == ""
    assert body in result


# --- Git trailers preserved in footer ---

def test_git_trailer_preserved():
    msg = "feat: add login\n\nCloses: #42"
    result = normalize(msg)
    assert "Closes: #42" in result


def test_multiple_trailers_preserved():
    msg = "fix: patch auth\n\nFixes: #10\nReviewed-by: Alice"
    result = normalize(msg)
    assert "Fixes: #10" in result
    assert "Reviewed-by: Alice" in result


def test_trailer_not_modified():
    msg = "feat: new api\n\nBREAKING-CHANGE: old endpoints removed\nCo-authored-by: Bob <bob@example.com>"
    result = normalize(msg)
    assert "BREAKING-CHANGE: old endpoints removed" in result
    assert "Co-authored-by: Bob <bob@example.com>" in result


def test_breaking_change_space_token_in_footer():
    msg = "feat!: remove v1 endpoint\n\nBREAKING CHANGE: removes the /v1/users endpoint entirely"
    result = normalize(msg)
    assert "BREAKING CHANGE: removes the /v1/users endpoint entirely" in result


def test_breaking_change_space_token_not_treated_as_body():
    msg = "fix: patch endpoint\n\nBREAKING CHANGE: old param removed"
    result = normalize(msg)
    lines = result.splitlines()
    # The BREAKING CHANGE line should appear after the blank separator line
    assert lines[0] == "fix: patch endpoint"
    assert "BREAKING CHANGE: old param removed" in result


# --- Empty message raises ValueError ---

def test_empty_message_raises():
    with pytest.raises(ValueError):
        normalize("")


def test_whitespace_only_raises():
    with pytest.raises(ValueError):
        normalize("   \n  ")


# --- Merge commit passthrough ---

def test_merge_commit_passthrough():
    msg = "Merge branch 'feature/foo' into main"
    assert normalize(msg) == msg


def test_merge_commit_preserves_body():
    msg = "Merge pull request #42 from user/branch\n\nSome merge details."
    assert normalize(msg) == msg


# --- Multi-line header joining ---

def test_multiline_header_joined():
    msg = "feat: add a very long feature\n    that spans two lines"
    result = normalize(msg)
    assert result.startswith("feat: add a very long feature that spans two lines")


# --- Unparseable header fallback ---

def test_unparseable_header_prefixed():
    msg = "just some random text without a type"
    result = normalize(msg)
    assert result.startswith("chore: ")


def test_unparseable_header_with_body():
    msg = "random commit text\n\nSome body text."
    result = normalize(msg)
    assert result.startswith("chore: ")
    assert "Some body text." in result
