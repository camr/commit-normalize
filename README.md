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
| Capitalize subject | First letter of the description is uppercased |
| Trailing period | Not allowed on the subject line |
| Blank line | Required between subject and body |
| Body wrapping | Recommended at 72 characters |
| Breaking change | Mark with `!` after type/scope, e.g. `feat!:` |

### Examples

```
feat(auth): Add OAuth2 login flow

Replaces the username/password form with a redirect-based OAuth2 flow.
Supports Google and GitHub providers.

Closes: #42
```

```
fix: Prevent nil pointer on missing config

Reviewed-by: alice@example.com
```

```
chore!: Drop Python 3.8 support
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
# => fix: Correct typo

# Normalize a file in place (commit-msg hook mode)
python3 cli.py --file .git/COMMIT_EDITMSG

# Check without modifying (CI / pre-receive use)
python3 cli.py --check --file .git/COMMIT_EDITMSG
```

`--check` exits 0 if the message is already normalized, or exits 1 and prints a before/after diff to stderr if any rule would change the message. The file is never modified in check mode.

### Git hook (commit-msg)

The `commit-msg` hook at `.git/hooks/commit-msg` runs automatically on every commit and rewrites the message in place. No manual action required.

### Git hook (pre-push)

The `pre-push` hook at `.git/hooks/pre-push` validates all outgoing commits before they reach the remote. It checks:

- Subject line does not exceed 72 characters
- Subject line does not end with a period
- Body (if present) is separated from subject by a blank line

The push is rejected if any commit fails validation, printing the offending commit SHA and subject.

## Configuration

Add a `commit-normalize.json` file to your repository root to toggle rules.
All rules default to enabled; any omitted key inherits its default.

```json
{
  "rules": {
    "capitalize_subject": true,
    "strip_trailing_period": true,
    "normalize_type": true,
    "max_subject_length": 72
  }
}
```

| Key | Default | Effect |
|-----|---------|--------|
| `capitalize_subject` | `true` | Uppercase the first letter of the description |
| `strip_trailing_period` | `true` | Remove trailing `.` from the subject |
| `normalize_type` | `true` | Lowercase the type; remap unknown types to `chore` |
| `max_subject_length` | `72` | Maximum subject line length before truncation |

## Normalization Behavior

| Input | Output |
|-------|--------|
| `Feat: add thing.` | `feat: Add thing` |
| `FIX: correct typo` | `fix: Correct typo` |
| `random: some change` | `chore: Some change` |
| `feat( auth ): login` | `feat(auth): Login` |
| `feat(   ): login` | `feat: Login` |
| Subject > 72 chars | Truncated at 72, trailing period stripped |
| Plain sentence | Wrapped as `chore: <capitalized sentence>` |

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
  normalizer.py          - Core normalization logic and config loader
  cli.py                 - CLI entry point and commit-msg hook driver
  commit-normalize.json  - Per-repo rule configuration (commit this file)
  install-hooks.sh       - Copies hooks/ into .git/hooks/ for contributors
  pyproject.toml         - Package metadata
  hooks/
    commit-msg           - Template: rewrites each commit message on commit
    pre-push             - Template: validates outgoing commits before push
  tests/
    test_normalizer.py   - Unit tests for normalizer
    test_cli.py          - Integration tests for CLI
```
