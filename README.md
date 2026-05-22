# Commit Message Normalizer

Normalizes git commit messages to the [Conventional Commits v1.0](https://www.conventionalcommits.org/en/v1.0.0/) specification.

## Normalization Rules

Given a commit message header of the form `type(scope)!: description`:

| Rule | Detail |
|------|--------|
| Type lowercased | `FEAT` -> `feat` |
| Unknown type mapped to `chore` | `wip: ...` -> `chore: ...` |
| Scope whitespace trimmed | `( auth )` -> `(auth)` |
| Breaking-change marker preserved | `feat!:` stays `feat!:` |
| Trailing period stripped from description | `fix: resolve bug.` -> `fix: resolve bug` |
| Description first character lowercased | `feat: Add thing` -> `feat: add thing` |
| Subject truncated to 72 characters | long lines are hard-truncated |
| Unparseable headers prefixed with `chore:` | |
| Merge commits pass through unchanged | |
| Body paragraphs preserved unchanged | |
| Git trailer footers preserved unchanged | |

### Allowed Types

`feat` `fix` `docs` `style` `refactor` `perf` `test` `build` `ci` `chore` `revert`

## Installation

```bash
pip install -e .
```

## Usage

### CLI

```bash
normalize-commit-msg <commit-msg-file>
```

### As a Python library

```python
from normalizer import normalize

normalized = normalize("FEAT(Auth): Add OAuth2 Support.")
# -> "feat(auth): add OAuth2 Support"
```

### As a git commit-msg hook

Install the hook into any git repository:

```bash
./scripts/install-hook.sh /path/to/target-repo
```

Or manually:

```bash
cp scripts/install-hook.sh /path/to/repo/.git/hooks/commit-msg
chmod +x /path/to/repo/.git/hooks/commit-msg
```

The hook rewrites the commit message file in place before git records the commit.

## Running Tests

```bash
pytest
```
