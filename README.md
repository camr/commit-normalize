# Commit Message Normalizer

Enforces and normalizes commit messages to [Conventional Commits](https://www.conventionalcommits.org/) format via a git hook and standalone CLI.

## Commit Format Standard

All commits must follow Conventional Commits:

```
<type>[(<scope>)][!]: <description>

[optional body]

[optional footer(s)]
```

### Rules

| Rule | Detail |
|------|--------|
| Subject length | 72 characters maximum |
| Type | Must be lowercase: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert` |
| Trailing period | Not allowed on the subject line |
| Blank line | Required between subject and body |
| Body wrapping | Recommended at 72 characters |
| Breaking change | Mark with `!` after type/scope, e.g. `feat!:` |

### Examples

```
feat(auth): add OAuth2 login flow

Replaces the username/password form with a redirect-based OAuth2 flow.
Supports Google and GitHub providers.

Closes: #42
```

```
fix: prevent nil pointer on missing config

Reviewed-by: alice@example.com
```

```
chore!: drop Python 3.8 support
```

## Installation

Install the commit-msg hook into your repo:

```bash
# From within any git repository
ln -sf /path/to/cli.py .git/hooks/commit-msg
# or copy the hook directly
cp /path/to/commit-normalize/.git/hooks/commit-msg .git/hooks/commit-msg
```

Or install as a Python package and use the entry point:

```bash
pip install -e /path/to/commit-normalize
# Then in your repo
echo '#!/usr/bin/env bash
exec commit-normalize -f "$1"' > .git/hooks/commit-msg
chmod +x .git/hooks/commit-msg
```

## Usage

### Standalone normalization

```bash
# Normalize a message string
python3 cli.py "FIX: correct typo."
# => fix: correct typo

# Normalize a file in place (commit-msg hook mode)
python3 cli.py --file .git/COMMIT_EDITMSG
```

### Git hook (commit-msg)

The `commit-msg` hook at `.git/hooks/commit-msg` runs automatically on every commit and rewrites the message in place. No manual action required.

### Git hook (pre-push)

The `pre-push` hook at `.git/hooks/pre-push` validates all outgoing commits before they reach the remote. It checks:

- Subject line does not exceed 72 characters
- Subject line does not end with a period
- Body (if present) is separated from subject by a blank line

The push is rejected if any commit fails validation, printing the offending commit SHA and subject.

## Normalization Behavior

| Input | Output |
|-------|--------|
| `Feat: add thing.` | `feat: add thing` |
| `FIX: correct typo` | `fix: correct typo` |
| `random: some change` | `chore: some change` |
| `feat( auth ): login` | `feat(auth): login` |
| `feat(   ): login` | `feat: login` |
| Subject > 72 chars | Truncated at 72, trailing period stripped |
| Plain sentence | Wrapped as `chore: <sentence>` |
| `feature: add thing` | `feat: add thing` |
| `bugfix: fix crash` | `fix: fix crash` |
| `hotfix: patch leak` | `fix: patch leak` |
| `documentation: update README` | `docs: update README` |
| `refactoring: extract helper` | `refactor: extract helper` |
| `performance: cache results` | `perf: cache results` |
| `testing: add unit tests` | `test: add unit tests` |
| `infrastructure: add CI` | `ci: add CI` |

## Development

```bash
# Install dev dependencies
pip install pytest

# Run tests
python3 -m pytest tests/ -v
```

## Project structure

```
commit-normalize/
  normalizer.py     - Core normalization logic
  cli.py            - CLI entry point and commit-msg hook driver
  pyproject.toml    - Package metadata
  tests/
    test_normalizer.py  - Unit tests for normalizer
    test_cli.py         - Integration tests for CLI
  .git/hooks/
    commit-msg      - Rewrites each commit message on commit
    pre-push        - Validates outgoing commits before push
```
